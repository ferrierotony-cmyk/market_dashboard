"""FRED access configuration.

Uses the official `fredapi` wrapper when an API key is configured, and falls back to
FRED's public CSV download when it is not, so everything still runs without a key.

Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html, then EITHER
  set the environment variable   FRED_API_KEY=<your 32-character key>
  OR put one line in a file named .env next to this script:   FRED_API_KEY=<your key>
Never paste the key into code or commit it. .env is in .gitignore.

What the official API adds over the CSV fallback:
  - series metadata (title, units, frequency, last updated)
  - search across all FRED series
  - ALFRED vintages: what a series looked like on a past date (first releases, as-of
    dates). Use these when you need point-in-time data free of later revisions.

Commands:
  python fredcfg.py --check       # which mode am I in, does the key work
  python fredcfg.py --dashboard   # granular macro and balance sheet metrics
  python fredcfg.py --search "treasury general account"   # needs a key
"""
import argparse
import io
import os
import re
import urllib.request
from functools import lru_cache
from pathlib import Path

import pandas as pd

KEY_ENV = "FRED_API_KEY"
ENV_FILE = Path(__file__).resolve().parent / ".env"
CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={start}"
KEY_PATTERN = re.compile(r"^[a-z0-9]{32}$")


class NeedsApiKey(RuntimeError):
    """Raised when a feature needs the official API and no key is configured."""


def load_api_key(env_file: Path = ENV_FILE) -> str | None:
    """Key from the environment first, then from a .env file. None when absent."""
    key = os.environ.get(KEY_ENV)
    if not key and Path(env_file).exists():
        for line in Path(env_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(KEY_ENV + "="):
                key = line.split("=", 1)[1].strip().strip("\"'")
    key = (key or "").strip()
    return key or None


class FredSource:
    """One object for all FRED reads. `mode` is 'fredapi' or 'csv'."""

    def __init__(self, api_key: str | None = None, client=None):
        if client is None and api_key:
            if not KEY_PATTERN.match(api_key):
                raise ValueError(f"{KEY_ENV} must be 32 lowercase letters and digits")
            from fredapi import Fred
            client = Fred(api_key=api_key)
        self.client = client
        self.mode = "fredapi" if client is not None else "csv"

    # -- plain series, same call in both modes
    def series(self, sid: str, start: str | None = "2010-01-01") -> pd.Series:
        if self.client is not None:
            s = self.client.get_series(sid, observation_start=start)
        else:
            url = CSV_URL.format(sid=sid, start=start or "1900-01-01")
            req = urllib.request.Request(url, headers={"User-Agent": "fedliq/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                text = r.read().decode("utf-8")
            s = pd.read_csv(io.StringIO(text), na_values=["."], parse_dates=[0], index_col=0)[sid]
        s = s.astype(float).dropna()
        s.index = pd.to_datetime(s.index)
        s.name = sid
        return s

    # -- official-API-only features
    def _need_api(self):
        if self.client is None:
            raise NeedsApiKey(f"This needs the official API. Set {KEY_ENV} (see fredcfg.py docstring).")

    def info(self, sid: str) -> dict:
        self._need_api()
        i = self.client.get_series_info(sid)
        return {k: i.get(k) for k in ("title", "units", "frequency", "seasonal_adjustment", "last_updated")}

    def search(self, text: str, limit: int = 10) -> pd.DataFrame:
        self._need_api()
        df = self.client.search(text, limit=limit, order_by="popularity", sort_order="desc")
        return df[["title", "frequency_short", "units_short", "last_updated"]]

    def as_of(self, sid: str, date: str) -> pd.Series:
        """The series as it was published on `date` (ALFRED). Free of later revisions."""
        self._need_api()
        df = self.client.get_series_as_of_date(sid, date)
        # one row per observation, keep the latest vintage known on `date`
        df = df.sort_values(["date", "realtime_start"]).groupby("date").tail(1)
        s = df.set_index("date")["value"].astype(float).dropna()
        s.index = pd.to_datetime(s.index)
        return s

    def first_release(self, sid: str) -> pd.Series:
        """Each observation as first published, never revised."""
        self._need_api()
        return self.client.get_series_first_release(sid).astype(float).dropna()


@lru_cache(maxsize=1)
def get_source() -> FredSource:
    return FredSource(api_key=load_api_key())


# ---------------------------------------------------------------- granular metrics
# group -> list of (series id, label, transform). transform: 'level' or 'yoy' (12 or 52 periods).
CATALOG = {
    "Fed balance sheet ($B, H.4.1)": [
        ("WALCL", "Total assets", "bn_from_mn"),
        ("WSHOTSL", "Treasury securities held", "bn_from_mn"),
        ("WSHOMCB", "MBS held", "bn_from_mn"),
        ("WDTGAL", "Treasury General Account", "bn_from_mn"),
        ("RRPONTSYD", "Overnight reverse repo", "level"),
        ("WRBWFRBL", "Reserve balances", "bn_from_mn"),
    ],
    "Rates and curve (%)": [
        ("DFF", "Fed funds effective", "level"),
        ("DGS2", "2y Treasury", "level"),
        ("DGS10", "10y Treasury", "level"),
        ("T10Y2Y", "10y minus 2y", "level"),
        ("DFII10", "10y real yield (TIPS)", "level"),
        ("T10YIE", "10y breakeven inflation", "level"),
    ],
    "Credit, stress and dollar": [
        ("BAA10Y", "Baa minus 10y spread (%)", "level"),
        ("NFCI", "Chicago Fed financial conditions", "level"),
        ("STLFSI4", "St. Louis financial stress", "level"),
        ("VIXCLS", "VIX", "level"),
        ("DTWEXBGS", "Broad dollar index", "level"),
    ],
    "Inflation, labor ($)": [
        ("CPIAUCSL", "CPI, year over year %", "yoy12"),
        ("PCEPILFE", "Core PCE, year over year %", "yoy12"),
        ("UNRATE", "Unemployment rate %", "level"),
        ("ICSA", "Initial jobless claims", "level"),
    ],
}


def _transform(s: pd.Series, kind: str) -> pd.Series:
    if kind == "bn_from_mn":
        return s / 1e3
    if kind == "yoy12":
        # calendar months, not rows: a missing month must not stretch the window to 13 months
        return (s.asfreq("MS").pct_change(12) * 100).dropna()
    return s


def macro_dashboard(src: FredSource | None = None) -> pd.DataFrame:
    """Latest value of each catalog series, plus its change over about one year."""
    src = src or get_source()
    rows = []
    for group, items in CATALOG.items():
        for sid, label, kind in items:
            try:
                s = _transform(src.series(sid, "2024-01-01"), kind)
            except Exception as e:  # keep the dashboard alive if one series fails
                rows.append({"group": group, "series": sid, "label": label, "error": str(e)[:50]})
                continue
            last_date = s.index[-1]
            year_ago = s[s.index <= last_date - pd.Timedelta(days=365)]
            rows.append({
                "group": group, "series": sid, "label": label,
                "latest": float(s.iloc[-1]), "as_of": last_date.date(),
                "chg_1y": float(s.iloc[-1] - year_ago.iloc[-1]) if len(year_ago) else float("nan"),
            })
    return pd.DataFrame(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dashboard", action="store_true")
    ap.add_argument("--search")
    args = ap.parse_args(argv)
    src = get_source()
    pd.set_option("display.width", 180)

    if args.check or not (args.dashboard or args.search):
        print(f"Mode: {src.mode}")
        if src.mode == "csv":
            print(f"No API key found. Using the public CSV fallback. To use the official API set {KEY_ENV}.")
        else:
            print("API key found. Test call:", src.info("WALCL")["title"])
    if args.dashboard:
        d = macro_dashboard(src)
        print(d.round(3).to_string(index=False))
    if args.search:
        print(src.search(args.search).to_string())


if __name__ == "__main__":
    main()
