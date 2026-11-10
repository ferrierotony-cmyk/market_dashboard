"""Do inflation and output readings add out-of-sample skill to the liquidity allocator?

Compares three feature sets with the same walk-forward machinery, costs, and 4-week horizon:
  liquidity   net liquidity change over 4 and 13 weeks (the production model)
  macro       core CPI 3m annualized, 5y5y forward inflation, industrial production vs trend, Sahm
  both        all six

Point-in-time handling: each macro value is used only from its publication date plus a
conservative lag (pipeline.SPECS). Revised series (CPI seasonal factors, industrial production)
are still taken as last revised, so some revision look-ahead remains. That bias flatters the
macro features, so a weak result here is believable and a strong one deserves suspicion until
it is re-run on real vintages (official API key, fredcfg.FredSource.as_of).

Multiple testing: 3 feature sets x 3 assets = 9 tests, so a t-stat of 2 is expected by chance
about once. The bar printed below is Bonferroni-adjusted (two-sided, 5% across 9 tests).

  python feature_study.py
"""
import numpy as np
import pandas as pd

import allocator as al
import fredcfg
import inflation as inf
import macro
import output_trend as out
import pipeline

N_TESTS = 9
BONFERRONI_T = 2.8


def macro_features(series: dict, specs: dict, decision_dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Macro features as known at each decision date. Derived on raw series, then released on their lag."""
    derived = {}
    if "CPILFESL" in series:
        derived["core_cpi_3m_ann"] = ("CPILFESL", inf.ann_growth(series["CPILFESL"], 3).dropna())
    if "T5YIFR" in series:
        derived["t5yifr"] = ("T5YIFR", series["T5YIFR"])
    if "INDPRO" in series:
        derived["ip_trend_dev"] = ("INDPRO", out.activity_block({"INDPRO": series["INDPRO"]})["IP dev from trend %"].dropna())
    if "UNRATE" in series:
        derived["sahm"] = ("UNRATE", out.activity_block({"UNRATE": series["UNRATE"]})["Sahm indicator"].dropna())
    return pd.DataFrame({name: pipeline.align_to(s, specs[base], decision_dates)
                         for name, (base, s) in derived.items()}, index=decision_dates)


def run_study(ds: pd.DataFrame, feature_sets: dict, cfg: dict = al.CONFIG) -> tuple[pd.DataFrame, pd.DataFrame]:
    diag_rows, bt_rows = [], []
    for name, cols in feature_sets.items():
        preds = al.walk_forward(ds, cfg, features=cols)
        d = al.diagnostics(preds)
        for asset in al.RISKY:
            diag_rows.append({"features": name, "asset": asset, "decisions": int(d.loc[asset, "decisions"]),
                              "OOS R2": d.loc[asset, "OOS R2 vs mean"], "IC": d.loc[asset, "IC (rank corr)"],
                              "IC t-stat": d.loc[asset, "IC t-stat"]})
        stats, _, extra = al.backtest(preds, cfg)
        bt_rows.append({"features": name, "excess vs neutral %/yr": stats.loc["Allocator", "excess vs neutral"] * 100,
                        "90% CI low": extra["excess_ci90"][0] * 100, "90% CI high": extra["excess_ci90"][1] * 100,
                        "avg turnover/yr": stats.loc["Allocator", "avg turnover / yr"]})
    return pd.DataFrame(diag_rows), pd.DataFrame(bt_rows)


def main():
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", lambda v: f"{v:,.3f}")
    cfg = al.CONFIG
    src = fredcfg.get_source()
    weekly, px = al.load_inputs("2010-01-01", src)
    ds = al.build_dataset(weekly["net_liq"], al.asset_returns(px, cfg["durations"]), cfg)
    data = macro.collect(src)
    mf = macro_features(data.series, data.specs, ds.index)
    ds = ds.join(mf)
    mcols = list(mf.columns)
    sets = {"liquidity": al.FEATURES, "macro": mcols, "both": al.FEATURES + mcols}
    diag, bt = run_study(ds, sets, cfg)
    print(f"Features available at decision dates: {mcols}. Sample: stocks history from "
          f"{px['spx'].dropna().index[0]:%Y-%m-%d}.\n")
    print("OUT-OF-SAMPLE SKILL by feature set")
    print(diag.to_string(index=False))
    print("\nBACKTEST vs neutral (net of costs)")
    print(bt.to_string(index=False))
    winners = diag[(diag["IC t-stat"] >= BONFERRONI_T) & (diag["OOS R2"] > 0)]
    print(f"\nBar for a real finding after correcting for {N_TESTS} tests: IC t-stat >= {BONFERRONI_T} and OOS R2 > 0.")
    if winners.empty:
        print("No feature set clears it. Inflation and output readings add no demonstrated skill over the "
              "historical mean, so they stay out of the allocator and the gate stays closed.")
    else:
        print("Clears the bar (re-test on real vintages before trusting it):")
        print(winners.to_string(index=False))


if __name__ == "__main__":
    main()
