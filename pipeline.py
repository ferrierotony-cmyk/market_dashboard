"""FRED data pipeline: registry, cache with lineage, quality gates, point-in-time availability.

Every macro series the lab uses is declared once in SPECS with its frequency, units,
publication lag and plausible range. The pipeline then
  1. fetches each series (official fredapi when a key is set, public CSV otherwise),
  2. falls back to the on-disk cache when a fetch fails, and says so,
  3. writes a lineage manifest (when, from where, how many rows, a hash of the values),
  4. runs quality gates: failed fetch, stale, out of range, outlier print, gaps, cached,
  5. exposes a point-in-time view: what was actually published by a given date.

Point-in-time. An observation dated d for a monthly series covers the whole month, so it is
only knowable at period end + publication lag. `available_date` encodes that. Lags here are
deliberately conservative (later than the usual release day) so a backtest cannot see data early.
Series flagged `revised` (GDP, CPI seasonal factors, potential output) are still shown as
last revised, not as first published, so even a lagged view carries some revision look-ahead.
Real vintages need the official API key (fredcfg.FredSource.as_of / first_release).

A series is `usable` unless it failed, is stale, or is out of range. Consumers such as the
alert engine treat unusable series as missing instead of acting on bad data.
"""
import hashlib
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import fredcfg

ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / "data" / "cache"
SEVERITY = ["FAILED", "STALE", "RANGE", "OUTLIER", "GAP", "CACHED"]   # worst first
BLOCKING = {"FAILED", "STALE", "RANGE"}
GRACE_DAYS = {"D": 3, "W": 5, "M": 10, "Q": 20}


@dataclass(frozen=True)
class SeriesSpec:
    id: str
    name: str
    freq: str               # D, W, M, Q
    kind: str               # index, level, pct_yy, pct_mm, ann_rate
    lag_days: int           # publication lag after the end of the observation period
    group: str
    lo: float | None = None  # plausible range for the latest value
    hi: float | None = None
    check_stale: bool = True
    revised: bool = False    # values change after first publication
    start: str = "2000-01-01"


SPECS = [
    # --- consumer inflation
    SeriesSpec("CPIAUCSL", "CPI, all items (SA)", "M", "index", 20, "inflation", revised=True),
    SeriesSpec("CPILFESL", "CPI, core (SA)", "M", "index", 20, "inflation", revised=True),
    SeriesSpec("PCEPI", "PCE price index", "M", "index", 35, "inflation", revised=True),
    SeriesSpec("PCEPILFE", "PCE price index, core", "M", "index", 35, "inflation", revised=True),
    SeriesSpec("MEDCPIM158SFRBCLE", "Median CPI, 1m annualized % (Cleveland Fed)", "M", "ann_rate", 25, "inflation", -20, 40),
    SeriesSpec("TRMMEANCPIM094SFRBCLE", "16% trimmed-mean CPI index (Cleveland Fed)", "M", "index", 25, "inflation"),
    SeriesSpec("STICKCPIM157SFRBATL", "Sticky CPI, 1m % (Atlanta Fed)", "M", "pct_mm", 25, "inflation", -5, 5),
    SeriesSpec("CORESTICKM159SFRBATL", "Sticky core CPI, y/y % (Atlanta Fed)", "M", "pct_yy", 25, "inflation", -5, 25),
    SeriesSpec("MICH", "Michigan 1y inflation expectations, %", "M", "level", 5, "inflation", 0, 25),
    SeriesSpec("T5YIE", "5y breakeven inflation, %", "D", "level", 1, "inflation", -2, 6, start="2003-01-01"),
    SeriesSpec("T10YIE", "10y breakeven inflation, %", "D", "level", 1, "inflation", -2, 6, start="2003-01-01"),
    SeriesSpec("T5YIFR", "5y5y forward inflation expectation, %", "D", "level", 1, "inflation", -2, 6, start="2003-01-01"),
    SeriesSpec("GASREGW", "US regular gasoline, $/gal", "W", "level", 2, "inflation", 0.5, 12),
    # --- economic output
    SeriesSpec("GDPC1", "Real GDP, $B chained", "Q", "level", 30, "output", revised=True),
    SeriesSpec("GDPPOT", "Real potential GDP (CBO), $B", "Q", "level", 0, "output", check_stale=False, revised=True),
    SeriesSpec("GDPNOW", "Atlanta Fed GDPNow, q/q annualized %", "Q", "level", 28, "output", -30, 30, check_stale=False, start="2011-01-01"),
    SeriesSpec("WEI", "Weekly Economic Index (NY Fed), y/y GDP %", "W", "level", 5, "output", -20, 15, start="2008-01-01"),
    SeriesSpec("INDPRO", "Industrial production index", "M", "index", 20, "output", revised=True),
    SeriesSpec("PAYEMS", "Nonfarm payrolls, thousands", "M", "level", 10, "output", revised=True),
    SeriesSpec("UNRATE", "Unemployment rate, %", "M", "level", 10, "output", 0, 30),
    SeriesSpec("CFNAI", "Chicago Fed National Activity Index", "M", "level", 30, "output", -15, 10, revised=True),
]
SPEC_BY_ID = {s.id: s for s in SPECS}


# ------------------------------------------------------------------ calendar logic
def period_end(ts: pd.Timestamp, freq: str) -> pd.Timestamp:
    """Last day of the period an observation dated `ts` covers (FRED dates M and Q at period start)."""
    ts = pd.Timestamp(ts)
    if freq == "M":
        return ts + pd.offsets.MonthEnd(0)
    if freq == "Q":
        return ts + pd.offsets.QuarterEnd(0)
    return ts


def available_dates(index: pd.DatetimeIndex, spec: SeriesSpec) -> pd.DatetimeIndex:
    """When each observation could first be known: period end plus publication lag."""
    ends = [period_end(t, spec.freq) for t in index]
    return pd.DatetimeIndex(ends) + pd.Timedelta(days=spec.lag_days)


def point_in_time(s: pd.Series, spec: SeriesSpec, asof) -> pd.Series:
    """Observations that had been published by `asof`."""
    if s.empty:
        return s
    return s[available_dates(s.index, spec) <= pd.Timestamp(asof)]


def align_to(s: pd.Series, spec: SeriesSpec, idx: pd.DatetimeIndex) -> pd.Series:
    """Carry each value forward onto `idx`, but only from the day it became available."""
    if s.empty:
        return pd.Series(np.nan, index=idx)
    avail = pd.Series(s.values, index=available_dates(s.index, spec)).sort_index()
    avail = avail[~avail.index.duplicated(keep="last")]
    return avail.reindex(avail.index.union(idx)).ffill().reindex(idx)


def regular(s: pd.Series, freq: str = "M") -> pd.Series:
    """Put a monthly or quarterly series on a continuous calendar, with NaN for missing periods.

    Growth rates must count calendar months, not observations. If one month was never published
    (the October 2025 CPI, for example), shifting by 12 rows would silently compare against 13
    months ago and overstate year-over-year inflation.
    """
    if s.empty or freq not in ("M", "Q"):
        return s
    return s.asfreq("MS" if freq == "M" else "QS")


# ------------------------------------------------------------------ quality gates (pure)
def quality_issues(s: pd.Series, spec: SeriesSpec, today: date, from_cache: bool = False) -> list[str]:
    """Return a list of issue codes with short detail, e.g. 'STALE: ...'."""
    if s is None or s.empty:
        return ["FAILED: no data"]
    issues = []
    last = s.index[-1]
    today_ts = pd.Timestamp(today)
    if spec.check_stale and last <= today_ts:
        if spec.freq == "D":
            nxt = last + pd.Timedelta(days=4)
        elif spec.freq == "W":
            nxt = last + pd.Timedelta(days=7)
        else:
            nxt = period_end(last + pd.DateOffset(months=1 if spec.freq == "M" else 3), spec.freq)
        due = nxt + pd.Timedelta(days=spec.lag_days + GRACE_DAYS[spec.freq])
        if today_ts > due:
            issues.append(f"STALE: last obs {last:%Y-%m-%d}, a newer one was due by {due:%Y-%m-%d}")
    v = float(s[s.index <= today_ts].iloc[-1]) if (s.index <= today_ts).any() else float(s.iloc[-1])
    if (spec.lo is not None and v < spec.lo) or (spec.hi is not None and v > spec.hi):
        issues.append(f"RANGE: latest {v:g} outside [{spec.lo}, {spec.hi}]")
    d = s.pct_change() if spec.kind == "index" else s.diff()
    d = d.replace([np.inf, -np.inf], np.nan).dropna()
    if len(d) > 40:
        base, recent = d.iloc[-123:-3], d.iloc[-3:]
        mad = float((base - base.median()).abs().median())
        if mad > 0:
            z = ((recent - base.median()).abs() / (1.4826 * mad)).max()
            if z > 10:
                issues.append(f"OUTLIER: a recent change is {z:.0f} robust sigmas from normal")
    if spec.freq in ("M", "Q"):
        recent = s[s.index >= s.index[-1] - pd.DateOffset(years=10)]
        want = pd.date_range(recent.index[0], recent.index[-1], freq="MS" if spec.freq == "M" else "QS")
        missing = len(want.difference(recent.index))
        if missing:
            issues.append(f"GAP: {missing} missing period(s) in the last 10 years")
    if from_cache:
        issues.append("CACHED: live fetch failed, using saved copy")
    return issues


def worst_status(issues: list[str]) -> str:
    codes = {i.split(":")[0] for i in issues}
    for c in SEVERITY:
        if c in codes:
            return c
    return "OK"


# ------------------------------------------------------------------ cache and lineage
def _atomic_write(path: Path, write) -> None:
    """Write to a temp file then rename, so a crash or a reader never sees a half-written file."""
    tmp = path.with_name(f".{path.name}.{threading.get_ident()}.tmp")
    write(tmp)
    os.replace(tmp, path)


class Cache:
    """On-disk copy of each series plus a lineage manifest. Safe for concurrent writers."""

    def __init__(self, directory: Path = CACHE_DIR):
        self.dir = Path(directory)
        self._lock = threading.Lock()

    def read(self, sid: str) -> tuple[pd.Series | None, dict]:
        p = self.dir / f"{sid}.csv"
        if not p.exists():
            return None, {}
        try:
            s = pd.read_csv(p, parse_dates=[0], index_col=0)["value"].astype(float)
        except Exception:
            return None, {}                      # unreadable cache entry counts as no cache
        with self._lock:
            return s, self._manifest().get(sid, {})

    def write(self, sid: str, s: pd.Series, meta: dict) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        _atomic_write(self.dir / f"{sid}.csv",
                      lambda p: s.to_csv(p, header=["value"], index_label="date"))
        with self._lock:                         # the manifest is shared, so update it one writer at a time
            m = self._manifest()
            m[sid] = meta
            _atomic_write(self.dir / "manifest.json",
                          lambda p: p.write_text(json.dumps(m, indent=1), encoding="utf-8"))

    def _manifest(self) -> dict:
        p = self.dir / "manifest.json"
        try:
            return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        except (json.JSONDecodeError, OSError):
            return {}                            # a damaged manifest is rebuilt as series are re-fetched


def fingerprint(s: pd.Series) -> str:
    return hashlib.sha256(s.round(8).to_csv().encode()).hexdigest()[:16]


# ------------------------------------------------------------------ pipeline
@dataclass
class MacroData:
    series: dict            # id -> raw Series, as last revised
    quality: pd.DataFrame   # one row per series
    specs: dict
    retrieved_at: datetime
    mode: str

    def usable_ids(self) -> list[str]:
        return list(self.quality.loc[self.quality["usable"], "series"])

    def usable(self) -> dict:
        ids = set(self.usable_ids())
        return {k: v for k, v in self.series.items() if k in ids}

    def pit(self, asof, only_usable: bool = False) -> dict:
        """Every series cut to what had been published by `asof`."""
        src = self.usable() if only_usable else self.series
        return {k: point_in_time(v, self.specs[k], asof) for k, v in src.items()}


class Pipeline:
    def __init__(self, source=None, cache_dir: Path = CACHE_DIR, today: date | None = None,
                 specs=SPECS, use_cache: bool = True, workers: int = 8):
        self.source = source or fredcfg.get_source()
        self.cache = Cache(cache_dir)
        self.today = today or date.today()
        self.specs = list(specs)
        self.use_cache = use_cache
        self.workers = workers

    def _fetch_one(self, spec: SeriesSpec):
        now = datetime.now(timezone.utc)
        try:
            s = self.source.series(spec.id, spec.start)
            if s.empty:
                raise ValueError("empty response")
            if self.use_cache:
                self.cache.write(spec.id, s, {
                    "retrieved_at": now.isoformat(), "source": self.source.mode, "rows": int(len(s)),
                    "last_obs": s.index[-1].strftime("%Y-%m-%d"), "sha": fingerprint(s), "name": spec.name})
            return spec, s, False, ""
        except Exception as e:
            err = str(e)[:80]
            if self.use_cache:
                s, meta = self.cache.read(spec.id)
                if s is not None and not s.empty:
                    return spec, s, True, err
            return spec, pd.Series(dtype=float), False, err

    def run(self) -> MacroData:
        with ThreadPoolExecutor(self.workers) as ex:
            results = list(ex.map(self._fetch_one, self.specs))
        series, rows = {}, []
        for spec, s, cached, err in results:
            issues = quality_issues(s, spec, self.today, from_cache=cached)
            if s.empty and err:
                issues = [f"FAILED: {err}"]
            status = worst_status(issues)
            if not s.empty:
                series[spec.id] = s
            rows.append({
                "series": spec.id, "name": spec.name, "group": spec.group, "freq": spec.freq,
                "last_obs": s.index[-1].date() if len(s) else None, "rows": len(s),
                "status": status, "usable": not (set(i.split(":")[0] for i in issues) & BLOCKING),
                "issues": "; ".join(issues), "revised": spec.revised,
            })
        return MacroData(series, pd.DataFrame(rows), {s.id: s for s in self.specs},
                         datetime.now(timezone.utc), self.source.mode)
