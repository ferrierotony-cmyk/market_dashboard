"""Collect every result of the lab into one JSON snapshot for the dashboard page.

  python build_dashboard.py          # writes output/dashboard/fed_liquidity_lab.json

Pulls live FRED data, reruns the rule check (read-only: no alerts, state not saved), the allocator
diagnostics and the macro pipeline, and reads the saved backtest outputs. Numbers are plain
numbers (percent values are in percent), dates are ISO strings, missing values are null.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import alerts
import allocator as al
import fedliq
import fredcfg
import inflation as inf
import macro
import macro_calendar
import output_trend as out
import regime

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"


def clean(v):
    if isinstance(v, (np.floating, float)):
        return None if not np.isfinite(v) else round(float(v), 4)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, (pd.Timestamp, datetime)):
        return v.strftime("%Y-%m-%d")
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v


def records(df: pd.DataFrame) -> list:
    return [{k: clean(v) for k, v in row.items()} for row in df.to_dict("records")]


def monthly(df: pd.DataFrame, start: str) -> pd.DataFrame:
    d = df[df.index >= start].copy()
    d.index.name = "date"
    return d.reset_index()


def main():
    src = fredcfg.get_source()
    now = datetime.now(timezone.utc)
    data = {}

    # ---- liquidity
    fl = fedliq.fetch_all("2010-01-01", src)
    w, rrp_daily = fl["weekly"], fl["rrp_daily"]
    liq = w.loc["2021-01-01":, ["assets", "tga", "rrp", "net_liq", "reserves"]].copy()
    liq.index.name = "date"
    data["liquidity"] = records(liq.reset_index())
    last, prev, wk4, yr = w.iloc[-1], w.iloc[-2], w.iloc[-5], w.iloc[-53]
    snap = []
    for key, label in [("net_liq", "Net liquidity"), ("assets", "Fed assets"), ("tga", "Treasury General Account"),
                       ("rrp", "ON reverse repo"), ("reserves", "Reserve balances")]:
        snap.append({"item": label, "as_of": w.index[-1], "level": last[key], "chg_1w": last[key] - prev[key],
                     "chg_4w": last[key] - wk4[key], "chg_1y": last[key] - yr[key]})
    data["liquidity_snapshot"] = records(pd.DataFrame(snap))
    paths, table = fedliq.scenario_table(w, 26)
    sc = table.reset_index()[["scenario", "net_liq_end", "change", "change_pct", "from_assets", "from_tga", "from_rrp"]]
    sc["change_pct"] = sc["change_pct"] * 100
    data["scenarios"] = records(sc)
    data["scenario_paths"] = [{"week": int(k), "scenario": name, "net_liq": clean(v)}
                              for name, p in paths.items() for k, v in p["net_liq"].items()]

    # ---- inflation and output
    md = macro.collect(src)
    s = md.usable()
    it = inf.inflation_table(s).reset_index().rename(columns={
        "1m ann %": "m1", "3m ann %": "m3", "6m ann %": "m6", "y/y %": "yoy", "y/y vs 2% target": "vs_target"})
    data["inflation_table"] = records(it)
    ex = inf.expectations_table(s).reset_index().rename(columns={
        "latest %": "latest", "chg vs 1 period/month back": "chg_1m", "chg vs 3 months back": "chg_3m"})
    data["expectations"] = records(ex)
    tr = inf.inflation_trends(s)
    tr = tr.rename(columns={"Headline CPI y/y": "headline_cpi_yoy", "Core CPI y/y": "core_cpi_yoy",
                            "Core PCE y/y": "core_pce_yoy", "Trimmed-mean CPI y/y": "trimmed_yoy",
                            "Median CPI 12m avg": "median_12m", "Core CPI 3m ann": "core_cpi_3m",
                            "Core PCE 3m ann": "core_pce_3m", "Trimmed-mean CPI 3m ann": "trimmed_3m",
                            "Median CPI 3m avg": "median_3m"})
    data["inflation_trends"] = records(monthly(tr, "2015-01-01"))
    ot = out.output_table(s).reset_index()
    data["output_table"] = records(ot)
    g = out.gdp_block(s)[["Real GDP", "Potential (CBO)", "Trailing 10y trend"]]
    g = g.rename(columns={"Real GDP": "real_gdp", "Potential (CBO)": "potential", "Trailing 10y trend": "trend"})
    data["gdp_trend"] = records(monthly(g, "2011-01-01"))
    a = out.activity_block(s)[["IP y/y %", "Sahm indicator", "CFNAI 3m avg"]]
    a = a.rename(columns={"IP y/y %": "ip_yoy", "Sahm indicator": "sahm", "CFNAI 3m avg": "cfnai_ma3"})
    data["activity"] = records(monthly(a, "2015-01-01"))
    q = md.quality[["series", "name", "freq", "last_obs", "status", "usable", "issues"]]
    data["quality"] = records(q)

    # ---- rules, regime target, calendar (read-only evaluation: nothing sent or saved)
    cfg = alerts.load_rules()
    metrics = alerts.compute_metrics(src, with_model=True)
    state = alerts.load_state()
    _, _, rows = alerts.evaluate(cfg["rules"], metrics, state, now, cfg.get("cooldown_hours", 24))
    attr = pd.read_csv(OUT / "regime_node_attribution.csv").set_index("node")
    by_id = {r["id"]: r for r in cfg["rules"]}
    rule_rows, on = [], []
    for r in rows:
        rule = by_id[r["id"]]
        st = "no data" if r["triggered"] is None else ("TRIGGERED" if r["triggered"] else "ok")
        if st == "TRIGGERED" and rule.get("tilt"):
            on.append(r["id"])
        rule_rows.append({"id": r["id"], "metric": r["metric"], "value": r["value"], "threshold": r["rule"],
                          "status": st, "message": rule["message"], "action": rule.get("action", ""),
                          "pit": rule.get("pit", "ok"),
                          "v1_contribution": clean(attr.loc[r["id"], "contribution (pts, summed)"]) if r["id"] in attr.index else None})
    data["rules"] = records(pd.DataFrame(rule_rows))
    tgt = regime.target_weights(on, cfg["rules"], regime.regime_cfg(cfg)["max_dev"])
    neutral = pd.Series(al.CONFIG["neutral"])[al.ASSETS]
    data["target"] = [{"asset": k, "neutral": round(float(neutral[k]) * 100, 2), "target": round(float(tgt[k]) * 100, 2)}
                      for k in al.ASSETS]
    cal, problems = macro_calendar.upcoming(days=21, source=src)
    cal = cal.drop(columns="rid").rename(columns={"time (CT)": "time_ct", "days away": "days_away"})
    data["calendar"] = records(cal)

    # ---- allocator diagnostics and scenarios
    weekly2, px = al.load_inputs("2010-01-01", src)
    ds = al.build_dataset(weekly2["net_liq"], al.asset_returns(px, al.CONFIG["durations"]))
    preds = al.walk_forward(ds)
    diag = al.diagnostics(preds)
    fit = al.fit_final(ds, preds)
    data["allocator"] = [{"asset": a, "decisions": int(diag.loc[a, "decisions"]), "oos_r2": clean(diag.loc[a, "OOS R2 vs mean"]) * 100,
                          "ic": clean(diag.loc[a, "IC (rank corr)"]), "ic_t": clean(diag.loc[a, "IC t-stat"]),
                          "gate": clean(fit["gate"][a])} for a in al.RISKY]
    asc = pd.read_csv(OUT / "allocator_scenarios.csv")
    data["allocator_scenarios"] = records(asc[["scenario", "net liq change %", "Stocks liquidity effect %", "Stocks 1-sigma %",
                                              "Treasuries liquidity effect %", "Credit liquidity effect %"]].rename(columns={
        "net liq change %": "net_liq_change", "Stocks liquidity effect %": "stocks_effect", "Stocks 1-sigma %": "stocks_sigma",
        "Treasuries liquidity effect %": "tsy_effect", "Credit liquidity effect %": "credit_effect"}))

    # ---- backtests (saved outputs)
    v1 = pd.read_csv(OUT / "regime_backtest_summary.csv", index_col=0)
    v1 = v1[["ann. return", "ann. vol", "Sharpe (vs cash)", "max drawdown", "excess vs buy & hold",
             "excess vs matched static mix"]] * [100, 100, 1, 100, 100, 100]
    v1.columns = ["ann_return", "vol", "sharpe", "max_drawdown", "excess_vs_bh", "excess_vs_matched"]
    data["v1_summary"] = records(v1.rename_axis("strategy").reset_index())
    wk = pd.read_csv(OUT / "regime_backtest_weekly.csv", header=[0, 1], index_col=0)
    ret = wk["returns"]
    gr = (1 + ret).cumprod() * 100
    gr.columns = ["rules", "buy_hold", "rebalanced", "sp500", "matched"]
    gr.index = pd.to_datetime(gr.index)
    gr.index.name = "date"
    data["v1_growth"] = records(gr.reset_index())

    p2 = pd.read_csv(OUT / "prereg_v2_weekly_returns.csv", index_col=[0, 1])
    res2 = json.loads((OUT / "prereg_v2_result.json").read_text(encoding="utf-8"))
    summ, growth = [], []
    for win in ("development", "confirmation"):
        r = p2.loc[win]
        r.index = pd.to_datetime(r.index)
        g2 = (1 + r).cumprod() * 100
        for dt, row in g2.iterrows():
            growth.append({"window": win, "date": dt.strftime("%Y-%m-%d"), "rules": clean(row.iloc[0]), "buy_hold": clean(row.iloc[1]),
                           "rebalanced": clean(row.iloc[2]), "equity": clean(row.iloc[3]), "matched": clean(row.iloc[4])})
        for name, col in zip(["v2 rules", "Buy & hold (neutral)", "Neutral, rebalanced weekly", "Equity index", "Matched static mix"], r.columns):
            x = r[col]
            wealth = (1 + x).cumprod()
            summ.append({"window": win, "strategy": name, "ann_return": clean(((1 + x).prod() ** (52 / len(x)) - 1) * 100),
                         "vol": clean(x.std(ddof=1) * np.sqrt(52) * 100), "max_drawdown": clean((wealth / wealth.cummax() - 1).min() * 100)})
    data["v2_summary"], data["v2_growth"] = summ, growth
    crit = res2["criteria"]
    units = {"C1": "% a year", "C2": "points", "C3": "Sharpe", "C4": "% a year"}
    scale = {"C1": 100, "C2": 100, "C3": 1, "C4": 100}
    data["v2_criteria"] = [{"id": k, "test": crit[k]["test"], "value": clean(crit[k]["value"] * scale[k]), "unit": units[k],
                            "passed": "PASS" if crit[k]["pass"] else "FAIL"} for k in ("C1", "C2", "C3", "C4")]
    data["v2_criteria"].append({"id": "Verdict", "test": "All four must pass", "value": None, "unit": "",
                                "passed": crit["verdict"]})

    data["about"] = [{"built_utc": now.strftime("%Y-%m-%d %H:%M"), "fred_mode": src.mode, "latest_wednesday": w.index[-1],
                      "v2_locked_utc": res2["locked_utc"][:16], "v2_sha": res2["spec_sha256"][:12],
                      "nodes_on": len(on), "nodes_total": sum(1 for r in cfg["rules"] if r.get("tilt"))}]
    d = OUT / "dashboard"
    d.mkdir(exist_ok=True)
    path = d / "fed_liquidity_lab.json"
    path.write_text(json.dumps(data, separators=(",", ":"), allow_nan=False, default=clean), encoding="utf-8")
    print(f"Wrote {path} ({path.stat().st_size/1024:.0f} KB). Tables: " + ", ".join(f"{k}={len(v)}" for k, v in data.items()))
    for p in problems:
        print("  calendar source unavailable:", p)


if __name__ == "__main__":
    sys.exit(main())
