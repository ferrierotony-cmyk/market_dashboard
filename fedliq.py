"""Fed balance sheet tracker and net liquidity scenarios.

Net liquidity = Fed total assets - Treasury General Account (TGA) - ON reverse repo (RRP).
It is a popular market heuristic for how much Fed-created money is available to the
financial system. It is not an official Fed measure.

Data comes live from FRED (public CSV endpoint, no API key). All figures in $ billions.
  WALCL      Fed total assets, Wednesday level (millions)
  WDTGAL     Treasury General Account, Wednesday level (millions)
  RRPONTSYD  Overnight reverse repo, daily (billions)
  WRBWFRBL   Reserve balances, Wednesday level (millions). Shown as a cross-check.

Scenarios REPLAY what the balance sheet components actually did in past episodes,
applied to today's levels. They are historical analogues, not forecasts. You can also
define your own shock with --custom.

Usage:
  python fedliq.py                       # track + all scenarios, writes ./output
  python fedliq.py --horizon 13
  python fedliq.py --custom "assets=-300,tga=100,rrp=0"   # $B change over the horizon
"""
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import fredcfg

# name: (FRED id, multiplier to convert to $ billions)
SERIES = {
    "assets": ("WALCL", 1e-3),
    "tga": ("WDTGAL", 1e-3),
    "rrp": ("RRPONTSYD", 1.0),
    "reserves": ("WRBWFRBL", 1e-3),
}
COMPONENTS = ["assets", "tga", "rrp"]


# ------------------------------------------------------------------ data
def fetch_all(start: str = "2010-01-01", source=None) -> dict:
    """Return {'weekly': DataFrame, 'rrp_daily': Series}. Weekly index = Wednesdays.

    `source` is a fredcfg.FredSource. Default: official fredapi if a key is configured,
    otherwise the public CSV endpoint.
    """
    source = source or fredcfg.get_source()
    raw = {name: source.series(sid, start) * mult for name, (sid, mult) in SERIES.items()}
    return build_weekly(raw)


def build_weekly(raw: dict) -> dict:
    """Align everything to the Fed's Wednesday dates and compute net liquidity.

    RRP is daily, so take its value on each Wednesday (carry forward over holidays).
    RRP before the facility existed at scale (pre-2013) is filled with 0.
    """
    weekly = pd.DataFrame({"assets": raw["assets"], "tga": raw["tga"]})
    weekly["rrp"] = raw["rrp"].reindex(weekly.index, method="ffill").fillna(0.0)
    if "reserves" in raw:
        weekly["reserves"] = raw["reserves"]
    weekly = weekly.dropna(subset=COMPONENTS)
    weekly["net_liq"] = net_liquidity(weekly)
    return {"weekly": weekly, "rrp_daily": raw["rrp"]}


def net_liquidity(df: pd.DataFrame) -> pd.Series:
    return df["assets"] - df["tga"] - df["rrp"]


# ------------------------------------------------------------------ tracking
def snapshot(weekly: pd.DataFrame, rrp_daily: pd.Series) -> str:
    last, prev = weekly.iloc[-1], weekly.iloc[-2]
    wk4 = weekly.iloc[-5] if len(weekly) > 5 else weekly.iloc[0]
    yr = weekly.iloc[-53] if len(weekly) > 53 else weekly.iloc[0]
    rows = ["Latest Wednesday: " + weekly.index[-1].strftime("%Y-%m-%d")]
    rows.append(f"{'':16}{'Level $B':>12}{'1w chg':>10}{'4w chg':>10}{'1y chg':>10}")
    for name, label in [("assets", "Fed assets"), ("tga", "TGA"), ("rrp", "ON RRP"),
                        ("net_liq", "NET LIQUIDITY"), ("reserves", "Reserves (memo)")]:
        if name not in weekly.columns:
            continue
        rows.append(f"{label:16}{last[name]:12,.0f}{last[name]-prev[name]:+10,.0f}"
                    f"{last[name]-wk4[name]:+10,.0f}{last[name]-yr[name]:+10,.0f}")
    if len(rrp_daily):
        rows.append(f"Memo: latest daily ON RRP {rrp_daily.iloc[-1]:,.1f}B on "
                    f"{rrp_daily.index[-1].strftime('%Y-%m-%d')}")
    return "\n".join(rows)


# ------------------------------------------------------------------ scenarios
@dataclass
class Episode:
    name: str
    start: str      # first Wednesday of the replayed window
    note: str


EPISODES = [
    Episode("Market crash (Mar 2020 replay)", "2020-03-04",
            "Fed emergency lending and QE; Treasury stockpiles cash in the TGA"),
    Episode("High inflation / hawkish Fed (mid 2022 replay)", "2022-06-01",
            "QT ramps to full pace; hikes pull cash into the RRP facility"),
]


def trend_path(weekly: pd.DataFrame, horizon: int, lookback: int = 13) -> pd.DataFrame:
    """Cumulative change if each component keeps its average weekly change of the last `lookback` weeks."""
    step = weekly[COMPONENTS].diff().iloc[-lookback:].mean()
    steps = np.arange(horizon + 1)[:, None] * step.values[None, :]
    return pd.DataFrame(steps, columns=COMPONENTS)


def custom_path(shock: dict, horizon: int) -> pd.DataFrame:
    """Linear ramp to a total change (in $B) over the horizon."""
    ramp = np.linspace(0, 1, horizon + 1)[:, None]
    total = np.array([[shock.get(c, 0.0) for c in COMPONENTS]])
    return pd.DataFrame(ramp * total, columns=COMPONENTS)


def episode_path(weekly: pd.DataFrame, start: str, horizon: int) -> pd.DataFrame:
    """Cumulative change of each component from `start`, over `horizon` weeks."""
    i = weekly.index.get_indexer([pd.Timestamp(start)], method="nearest")[0]
    seg = weekly[COMPONENTS].iloc[i:i + horizon + 1]
    if len(seg) < horizon + 1:
        raise ValueError(f"Not enough data after {start} for a {horizon}-week replay")
    return (seg - seg.iloc[0]).reset_index(drop=True)


def apply_path(latest: pd.Series, delta: pd.DataFrame, scale: float = 1.0) -> pd.DataFrame:
    """Add a cumulative change path to today's levels.

    Levels are floored at zero: a replayed fall in RRP cannot take it below nothing.
    This is what keeps a replay honest when today's RRP is already near zero.
    """
    levels = pd.DataFrame(
        latest[COMPONENTS].values[None, :] + scale * delta[COMPONENTS].values,
        columns=COMPONENTS,
    ).clip(lower=0.0)
    levels["net_liq"] = net_liquidity(levels)
    levels.index.name = "weeks_ahead"
    return levels


def scenario_table(weekly: pd.DataFrame, horizon: int, custom: dict | None = None,
                   scale: float = 1.0) -> tuple[dict, pd.DataFrame]:
    latest = weekly.iloc[-1]
    paths = {"Baseline: hold today's levels": apply_path(latest, custom_path({}, horizon))}
    paths["Baseline: last-13-week trend continues"] = apply_path(latest, trend_path(weekly, horizon))
    for ep in EPISODES:
        paths[ep.name] = apply_path(latest, episode_path(weekly, ep.start, horizon), scale)
    if custom:
        paths["Custom shock"] = apply_path(latest, custom_path(custom, horizon))

    start_net = float(latest[COMPONENTS[0]] - latest["tga"] - latest["rrp"])
    rows = []
    for name, p in paths.items():
        end = p.iloc[-1]
        rows.append({
            "scenario": name,
            "net_liq_start": start_net,
            "net_liq_end": end["net_liq"],
            "change": end["net_liq"] - start_net,
            "change_pct": end["net_liq"] / start_net - 1,
            "from_assets": end["assets"] - latest["assets"],
            "from_tga": -(end["tga"] - latest["tga"]),
            "from_rrp": -(end["rrp"] - latest["rrp"]),
        })
    return paths, pd.DataFrame(rows).set_index("scenario")


# ------------------------------------------------------------------ output
def plot(weekly: pd.DataFrame, paths: dict, horizon: int, outfile: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (a, b) = plt.subplots(1, 2, figsize=(14, 5))
    hist = weekly.iloc[-156:]
    a.plot(hist.index, hist["net_liq"], label="Net liquidity", lw=2, color="black")
    a.plot(hist.index, hist["assets"], label="Fed assets", lw=1, alpha=.7)
    a.plot(hist.index, hist["tga"], label="TGA", lw=1, alpha=.7)
    a.plot(hist.index, hist["rrp"], label="ON RRP", lw=1, alpha=.7)
    a.set_title("Last 3 years ($B)")
    a.legend()
    a.grid(alpha=.3)
    for name, p in paths.items():
        b.plot(p.index, p["net_liq"], label=name, lw=2 if "Baseline: hold" not in name else 1.2,
               ls="--" if "Baseline" in name else "-")
    b.set_title(f"Net liquidity over next {horizon} weeks ($B), historical-replay scenarios")
    b.set_xlabel("weeks ahead")
    b.legend(fontsize=8)
    b.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(outfile, dpi=130)
    plt.close(fig)


def parse_custom(s: str) -> dict:
    out = {}
    for part in s.split(","):
        k, v = part.split("=")
        k = k.strip()
        if k not in COMPONENTS:
            raise SystemExit(f"--custom keys must be from {COMPONENTS}, got {k!r}")
        out[k] = float(v)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default="2010-01-01", help="first date to download")
    ap.add_argument("--horizon", type=int, default=26, help="weeks to project")
    ap.add_argument("--scale", type=float, default=1.0, help="multiply replayed episode flows (1 = same dollars)")
    ap.add_argument("--custom", help='e.g. "assets=-300,tga=100,rrp=0" ($B change over horizon)')
    ap.add_argument("--out", default="output")
    args = ap.parse_args(argv)

    data = fetch_all(args.start)
    weekly, rrp_daily = data["weekly"], data["rrp_daily"]
    print(f"Retrieved from FRED at {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC "
          f"(mode: {fredcfg.get_source().mode})\n")
    print(snapshot(weekly, rrp_daily))

    paths, table = scenario_table(weekly, args.horizon, parse_custom(args.custom) if args.custom else None,
                                  args.scale)
    pd.set_option("display.width", 200)
    print(f"\nScenarios over {args.horizon} weeks ($B). 'from_*' columns add up to 'change'.")
    show = table.copy()
    show["change_pct"] = (show["change_pct"] * 100).round(1)
    print(show.round(0).astype({"change_pct": float}).to_string())
    for ep in EPISODES:
        print(f"  - {ep.name}: {ep.note}")

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    weekly.to_csv(out / "net_liquidity_weekly.csv")
    table.to_csv(out / "scenarios.csv")
    plot(weekly, paths, args.horizon, out / "net_liquidity.png")
    print(f"\nWrote {out}/net_liquidity_weekly.csv, scenarios.csv, net_liquidity.png")
    print("Scenarios replay past dollar flows onto today's levels. They are analogues, not forecasts.")


if __name__ == "__main__":
    main()
