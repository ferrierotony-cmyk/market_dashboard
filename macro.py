"""Macro layer: runs the FRED pipeline and turns it into inflation and output readings.

  python macro.py                       # quality report, inflation and output tables, chart
  python macro.py --asof 2022-06-30     # what was published by that date (conservative lags)
  python macro.py --no-cache            # do not read or write the on-disk cache

Outputs go to ./output: macro_quality.csv, inflation_trends.csv, output_trends_*.csv,
macro_metrics.json and macro_dashboard.png. Series that fail the quality gates (stale, out of
range, failed fetch) are left out of every reading and listed in the quality table.
"""
import argparse
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

import fredcfg
import inflation as inf
import output_trend as out
import pipeline

ROOT = Path(__file__).resolve().parent


def collect(source=None, today: date | None = None, use_cache: bool = True,
            cache_dir: Path = pipeline.CACHE_DIR) -> pipeline.MacroData:
    return pipeline.Pipeline(source, cache_dir, today, use_cache=use_cache).run()


def metrics(series: dict) -> dict:
    """Inflation and output headline metrics from already-vetted series (see MacroData.usable)."""
    return {**inf.inflation_pulse(series), **out.output_pulse(series)}


def metric_series(series: dict) -> dict:
    """Full history of the metrics used by rules, as {metric: (FRED id it is released with, Series)}.

    The Series is indexed by observation date; release it on the base series' publication lag
    (pipeline.align_to) to get what was known on any past date. The last value of each equals the
    matching entry of metrics(), a property the tests check so live and backtest cannot drift apart.
    """
    out_ = {}
    if "CPIAUCSL" in series:
        out_["cpi_yoy"] = ("CPIAUCSL", inf.yoy(series["CPIAUCSL"]).dropna())
    if "CPILFESL" in series:
        out_["core_cpi_3m_ann"] = ("CPILFESL", inf.ann_growth(series["CPILFESL"], 3).dropna())
    if "PCEPILFE" in series:
        out_["core_pce_3m_ann"] = ("PCEPILFE", inf.ann_growth(series["PCEPILFE"], 3).dropna())
    if "T5YIFR" in series:
        out_["breakeven_5y5y"] = ("T5YIFR", series["T5YIFR"])
    if "WEI" in series:
        out_["wei"] = ("WEI", series["WEI"])
    if "UNRATE" in series:
        out_["sahm"] = ("UNRATE", out.activity_block({"UNRATE": series["UNRATE"]})["Sahm indicator"].dropna())
    if "CFNAI" in series:
        out_["cfnai_ma3"] = ("CFNAI", out.activity_block({"CFNAI": series["CFNAI"]})["CFNAI 3m avg"].dropna())
    return out_


def _line(ax, s: pd.Series, years: int, label: str, **kw) -> None:
    """Plot the last `years` of a series on plain matplotlib date axes (no pandas period axes)."""
    s = s.dropna()
    if s.empty:
        return
    s = s[s.index >= s.index[-1] - pd.DateOffset(years=years)]
    ax.plot(s.index, s.to_numpy(), label=label, **kw)


def plot(series: dict, outfile: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    trends = inf.inflation_trends(series)
    gdp = out.gdp_block(series) if "GDPC1" in series else None
    act = out.activity_block(series)
    fig, ax = plt.subplots(3, 2, figsize=(15, 13))

    a = ax[0, 0]
    for c in ["Headline CPI y/y", "Core CPI y/y", "Core PCE y/y", "Trimmed-mean CPI y/y", "Median CPI 12m avg"]:
        if c in trends:
            _line(a, trends[c], 12, c, lw=1.8)
    a.axhline(2, color="black", ls=":", lw=1, label="2% target")
    a.set_title("Consumer inflation, year over year (%)")
    a.legend(fontsize=8)

    a = ax[0, 1]
    for c in ["Core CPI 3m ann", "Core PCE 3m ann", "Trimmed-mean CPI 3m ann", "Median CPI 3m avg"]:
        if c in trends:
            _line(a, trends[c], 5, c, lw=1.6)
    a.axhline(2, color="black", ls=":", lw=1, label="2% target")
    a.set_title("Momentum: 3-month annualized (%)")
    a.legend(fontsize=8)

    a = ax[1, 0]
    for sid, lab in [("T5YIFR", "5y5y forward"), ("T5YIE", "5y breakeven"), ("T10YIE", "10y breakeven"), ("MICH", "Michigan 1y")]:
        if sid in series:
            _line(a, series[sid], 5, lab, lw=1.4)
    a.axhline(2, color="black", ls=":", lw=1, label="2% target")
    a.set_title("Inflation expectations (%)")
    a.legend(fontsize=8)

    a = ax[1, 1]
    if gdp is not None:
        _line(a, gdp["Real GDP"], 15, "Real GDP", lw=2)
        if "Potential (CBO)" in gdp:
            _line(a, gdp["Potential (CBO)"][gdp.index <= gdp["Real GDP"].dropna().index[-1]], 15, "CBO potential", lw=1.5, ls="--")
        _line(a, gdp["Trailing 10y trend"], 15, "Trailing 10y trend", lw=1.2, ls=":")
        a.set_title("Real GDP vs potential and trailing trend ($B)")
        a.legend(fontsize=8)

    a = ax[2, 0]
    if "IP y/y %" in act:
        _line(a, act["IP y/y %"], 12, "Industrial production y/y %", lw=1.6)
    if "WEI" in series:
        _line(a, series["WEI"], 12, "Weekly Economic Index", lw=1, alpha=.8)
    a.axhline(0, color="black", lw=.8)
    a.set_title("Real-time output: industrial production and WEI (%)")
    a.legend(fontsize=8)

    a = ax[2, 1]
    if "Sahm indicator" in act:
        _line(a, act["Sahm indicator"], 12, "Sahm indicator", lw=1.8)
    if "CFNAI 3m avg" in act:
        _line(a, act["CFNAI 3m avg"], 12, "CFNAI 3m avg", lw=1.4)
    a.axhline(0.5, color="red", ls="--", lw=1, label="Sahm 0.5 trigger")
    a.axhline(-0.7, color="orange", ls="--", lw=1, label="CFNAI -0.7 risk line")
    a.set_title("Recession gauges")
    a.legend(fontsize=8)

    for x in ax.flat:
        x.grid(alpha=.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outfile, dpi=120)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--asof", help="point-in-time view, YYYY-MM-DD")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--out", default="output")
    args = ap.parse_args(argv)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 70)
    pd.set_option("display.float_format", lambda v: f"{v:,.2f}")

    data = collect(use_cache=not args.no_cache)
    print(f"FRED mode: {data.mode}. Retrieved {data.retrieved_at:%Y-%m-%d %H:%M} UTC.")
    q = data.quality
    print("\nDATA QUALITY")
    print(q[["series", "freq", "last_obs", "status", "usable", "issues"]].to_string(index=False))
    bad = q[~q["usable"]]
    if len(bad):
        print(f"\n{len(bad)} series excluded from every reading below: {', '.join(bad['series'])}")

    if args.asof:
        series = {k: v for k, v in data.pit(args.asof, only_usable=False).items() if len(v)}
        print(f"\nPOINT-IN-TIME VIEW as of {args.asof} (conservative publication lags; revised series still "
              "carry revision look-ahead). Quality gates use today's date, so ignore staleness here.")
    else:
        series = data.usable()

    print("\nCONSUMER INFLATION")
    print(inf.inflation_table(series).to_string())
    print("\nEXPECTATIONS AND GASOLINE")
    print(inf.expectations_table(series).to_string())
    print("\nECONOMIC OUTPUT")
    print(out.output_table(series).to_string())

    outdir = Path(args.out)
    outdir.mkdir(exist_ok=True)
    q.to_csv(outdir / "macro_quality.csv", index=False)
    inf.inflation_trends(series).to_csv(outdir / "inflation_trends.csv")
    if "GDPC1" in series:
        out.gdp_block(series).to_csv(outdir / "output_trends_gdp.csv")
    out.activity_block(series).to_csv(outdir / "output_trends_activity.csv")
    (outdir / "macro_metrics.json").write_text(json.dumps(
        {k: (None if np.isnan(v) else round(v, 4)) for k, v in metrics(series).items()}, indent=1), encoding="utf-8")
    plot(series, outdir / "macro_dashboard.png")
    print(f"\nWrote macro_quality.csv, inflation_trends.csv, output_trends_*.csv, macro_metrics.json, "
          f"macro_dashboard.png to {outdir}/")


if __name__ == "__main__":
    main()
