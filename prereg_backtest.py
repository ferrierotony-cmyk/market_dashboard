"""Run the locked v2 design exactly as registered, and judge it against the pre-declared criteria.

The spec in prereg_v2.json is the only source of parameters. This script refuses to run unless
the spec still matches its lock (prereg.py), prints the verdict mechanically, and changes nothing
when the verdict is FAIL. One run per window; no parameter is tuned here.

  python prereg_backtest.py
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
import pipeline as pl
import prereg
import regime
import regime_backtest as rb

ROOT = Path(__file__).resolve().parent
SPEC_PATH = ROOT / "prereg_v2.json"
V2 = "Regime rules"                       # column name shared with regime_backtest so its statistics are reused


# ------------------------------------------------------------------ nodes with adaptive thresholds
def adaptive_thresholds(x: pd.Series, side: str, a: dict) -> pd.DataFrame:
    """Trigger and clear levels from the trailing window of observations strictly BEFORE each date."""
    past = x.shift(1).rolling(a["window_weeks"], min_periods=a["min_weeks"])
    if side == "high":
        trig, clr = past.quantile(a["high_side_trigger_pct"] / 100), past.quantile(a["high_side_clear_pct"] / 100)
    else:
        trig, clr = past.quantile(a["low_side_trigger_pct"] / 100), past.quantile(a["low_side_clear_pct"] / 100)
    return pd.DataFrame({"trigger": trig, "clear": clr})


def adaptive_state_path(x: pd.Series, side: str, a: dict) -> pd.Series:
    """On/off path of one fast node, with the same hysteresis rule as live alerts. Warm-up weeks stay off."""
    thr = adaptive_thresholds(x, side, a)
    op = ">=" if side == "high" else "<="
    state, out = None, []
    for t, v in x.items():
        tr, cl = thr.at[t, "trigger"], thr.at[t, "clear"]
        if not (pd.isna(v) or pd.isna(tr) or pd.isna(cl)):
            state = alerts.next_triggered(state, float(v), {"op": op, "value": float(tr), "clear": float(cl)})
        out.append(bool(state))
    return pd.Series(out, index=x.index)


def overlay_state_path(x: pd.Series, rule: dict) -> pd.Series:
    state, out = None, []
    for v in x:
        if not pd.isna(v):
            state = alerts.next_triggered(state, float(v), rule)
        out.append(bool(state))
    return pd.Series(out, index=x.index)


def virtual_rules(spec: dict) -> list:
    return [{"id": "tier_2", "tilt": spec["sizing"]["tier_2"]}, {"id": "tier_3", "tilt": spec["sizing"]["tier_3"]},
            {"id": spec["overlay"]["id"], "tilt": spec["overlay"]["tilt"]}]


def build_targets(spec: dict, hist: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Weekly target weights and the node states behind them."""
    a = spec["adaptive_thresholds"]
    nodes = {n["id"]: adaptive_state_path(hist[n["metric"]], n["side"], a) for n in spec["fast_nodes"]}
    states = pd.DataFrame(nodes)
    count = states.sum(axis=1)
    ov = spec["overlay"]
    states[ov["id"]] = overlay_state_path(hist[ov["metric"]], {"op": ov["op"], "value": ov["value"], "clear": ov["clear"]})
    rules = virtual_rules(spec)
    rows = {}
    for t in hist.index:
        active = []
        if count[t] == 2:
            active.append("tier_2")
        elif count[t] >= 3:
            active.append("tier_3")
        if states.at[t, ov["id"]]:
            active.append(ov["id"])
        rows[t] = regime.target_weights(active, rules, spec["max_dev"], spec["neutral"])
    states["n_fast_on"] = count
    return pd.DataFrame(rows).T[al.ASSETS], states


# ------------------------------------------------------------------ data
def metric_history_v2(weekly: pd.DataFrame, market: dict, pce: pd.Series, dates: pd.DatetimeIndex) -> pd.DataFrame:
    nl = weekly["net_liq"]
    friday = nl.index + pd.Timedelta(days=2)                       # H.4.1 is out Thursday
    return pd.DataFrame({
        "net_liq_4w_pct": rb.known_on((nl / nl.shift(4) - 1) * 100, friday, dates),
        "vix": pl.align_to(market["VIXCLS"], rb.EXTRA_SPECS["VIXCLS"], dates),
        "nfci": pl.align_to(market["NFCI"], rb.EXTRA_SPECS["NFCI"], dates),
        "baa_4w_chg": pl.align_to(rb.change_over_days(market["BAA10Y"], 28), rb.EXTRA_SPECS["BAA10Y"], dates),
        "core_pce_3m_ann": pl.align_to(inf.ann_growth(pce, 3).dropna(), pl.SPEC_BY_ID["PCEPILFE"], dates),
    }, index=dates)


def daily_returns(equity: pd.Series, src, start: str) -> pd.DataFrame:
    px = pd.concat({"spx": equity, "y10": src.series("DGS10", start), "baa": src.series("DBAA", start),
                    "bill": src.series("DTB3", start)}, axis=1, sort=True)
    return al.asset_returns(px, al.CONFIG["durations"])


# ------------------------------------------------------------------ one window
def run_window(spec: dict, targets: pd.DataFrame, daily: pd.DataFrame, dates: pd.DatetimeIndex,
               start: str, end: str) -> dict:
    rets = rb.weekly_asset_returns(daily, dates)
    rets = rets[rets.index >= pd.Timestamp(start)]
    if end != "latest":
        rets = rets[rets.index <= pd.Timestamp(end) - pd.Timedelta(days=7)]
    neutral = pd.Series(spec["neutral"])[al.ASSETS]
    flat = lambda w: pd.DataFrame([w] * len(rets), index=rets.index)          # noqa: E731
    tg = targets.loc[rets.index]
    stocks = pd.DataFrame(0.0, index=rets.index, columns=al.ASSETS).assign(Stocks=1.0)
    c = spec["cost_bps"]
    sims = {
        V2: rb.simulate(tg, rets, c),
        "Buy & hold (neutral)": rb.simulate(flat(neutral), rets, c, rebalance=False),
        "Neutral, rebalanced weekly": rb.simulate(flat(neutral), rets, c),
        "S&P 500": rb.simulate(stocks, rets, 0.0, rebalance=False),
        "Static mix, same average weights": rb.simulate(flat(tg.mean()), rets, c),
    }
    return {"returns": pd.DataFrame({k: v["net"] for k, v in sims.items()})[rb.STRATS],
            "turnover": pd.DataFrame({k: v["turnover"] for k, v in sims.items()})[rb.STRATS],
            "targets": tg, "cash": rets["Cash"], "rets": rets}


# ------------------------------------------------------------------ mechanical judgement
def judge(dev: dict, conf: dict) -> dict:
    """Apply C1-C4 exactly as written in the spec."""
    s_dev = rb.summarize(dev, dev["cash"])
    t_dev = rb.excess_tests(dev).set_index("vs")
    s_conf = rb.summarize(conf, conf["cash"])
    c1_low = float(t_dev.loc["Static mix, same average weights", "90% CI low"]) / 100
    dd_gain = float(s_dev.loc[V2, "max drawdown"] - s_dev.loc["Buy & hold (neutral)", "max drawdown"])
    sh_v2, sh_bh = float(s_dev.loc[V2, "Sharpe (vs cash)"]), float(s_dev.loc["Buy & hold (neutral)", "Sharpe (vs cash)"])
    c4 = float(s_conf.loc[V2, "excess vs matched static mix"])
    crit = {
        "C1": {"test": "dev: 90% CI low of excess vs matched static mix > 0", "value": c1_low, "pass": c1_low > 0},
        "C2": {"test": "dev: max drawdown shallower than buy&hold by >= 2 pts", "value": dd_gain, "pass": dd_gain >= 0.02},
        "C3": {"test": "dev: Sharpe >= buy&hold Sharpe", "value": sh_v2 - sh_bh, "pass": sh_v2 >= sh_bh},
        "C4": {"test": "confirmation: excess vs matched static mix > -0.5%/yr", "value": c4, "pass": c4 > -0.005},
    }
    crit["verdict"] = "PASS" if all(v["pass"] for v in crit.values()) else "FAIL"
    return crit


# ------------------------------------------------------------------ reporting
def show(label: str, res: dict, equity_label: str) -> None:
    pd.set_option("display.width", 220)
    r = res["returns"]
    print(f"\n{'=' * 100}\n{label}: {r.index[0]:%Y-%m-%d} to {r.index[-1]:%Y-%m-%d}, {len(r)} weekly periods\n{'=' * 100}")
    s = rb.summarize(res, res["cash"])
    fmt = s.copy()
    for c in ["ann. return", "ann. vol", "max drawdown", "avg turnover/yr"] + [c for c in s.columns if c.startswith("excess")]:
        fmt[c] = (s[c] * 100).map(lambda v: f"{v:,.2f}%")
    fmt["Sharpe (vs cash)"] = s["Sharpe (vs cash)"].map(lambda v: f"{v:,.2f}")
    fmt = fmt.rename(index={"S&P 500": equity_label}, columns={"excess vs S&P 500": f"excess vs {equity_label}"})
    print(fmt.to_string())
    t = rb.excess_tests(res).replace({"S&P 500": equity_label})
    print("\nv2 minus each benchmark (90% block-bootstrap interval, block 8 weeks):")
    print(t.round(3).to_string(index=False))
    yr = (rb.by_year(res) * 100).round(2).rename(columns={"S&P 500": equity_label})
    print("\nCalendar years (total return, %):")
    print(yr.to_string())
    tg = res["targets"]
    print(f"\nAverage target: " + ", ".join(f"{a} {tg[a].mean()*100:.1f}%" for a in al.ASSETS)
          + f"; {int((tg.diff().abs().max(axis=1) >= 0.02).sum())} target changes of 2+ points")


def main() -> int:
    try:
        lock = prereg.verify(SPEC_PATH)
    except Exception as e:
        print(f"REFUSING TO RUN: {e}")
        return 1
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    print(f"Spec {spec['name']} verified against its lock (sha256 {lock['sha256'][:16]}..., locked {lock['locked_utc']}).")

    src = fredcfg.get_source()
    begin = "2000-01-01"
    weekly = fedliq.fetch_all(begin, src)["weekly"]
    market = {sid: src.series(sid, begin) for sid in ("VIXCLS", "NFCI", "BAA10Y")}
    pce = src.series("PCEPILFE", begin)
    dev_eq, conf_eq = spec["windows"]["development"]["equity_series"], spec["windows"]["confirmation"]["equity_series"]
    daily_dev = daily_returns(src.series(dev_eq, begin), src, begin)
    daily_conf = daily_returns(src.series(conf_eq, "2016-01-01"), src, "2016-01-01")
    dates = pd.date_range("2003-01-03", max(daily_dev.index[-1], daily_conf.index[-1]), freq="W-FRI")
    hist = metric_history_v2(weekly, market, pce, dates)
    targets, states = build_targets(spec, hist)
    print(f"Metric history {dates[0]:%Y-%m-%d} to {dates[-1]:%Y-%m-%d}. Equity: development {dev_eq} (proxy), confirmation {conf_eq}.")

    w = spec["windows"]
    dev = run_window(spec, targets, daily_dev, dates, w["development"]["start"], w["development"]["end"])
    conf = run_window(spec, targets, daily_conf, dates, w["confirmation"]["start"], w["confirmation"]["end"])
    show("DEVELOPMENT WINDOW (clean; equity proxy Nasdaq Composite)", dev, "Nasdaq Comp.")
    show("CONFIRMATION WINDOW (NOT clean: v1 results were seen first; equity S&P 500)", conf, "S&P 500")

    node_cols = [n["id"] for n in spec["fast_nodes"]] + [spec["overlay"]["id"]]
    for name, res in (("development", dev), ("confirmation", conf)):
        st = states.loc[res["targets"].index]
        print(f"\nNode time on, {name} window: " + ", ".join(f"{c} {st[c].mean()*100:.0f}%" for c in node_cols)
              + f"; tier 2 {float((st['n_fast_on'] == 2).mean()*100):.0f}%, tier 3 {float((st['n_fast_on'] >= 3).mean()*100):.0f}%")

    crit = judge(dev, conf)
    print(f"\n{'=' * 100}\nPRE-DECLARED CRITERIA\n{'=' * 100}")
    for k in ("C1", "C2", "C3", "C4"):
        c = crit[k]
        print(f"  {k} {'PASS' if c['pass'] else 'FAIL'}  {c['test']}  (value {c['value']:+.4f})")
    print(f"\nVERDICT: {crit['verdict']}")
    print(spec["on_failure"] if crit["verdict"] == "FAIL" else
          "PASS means paper-trade forward from the lock date, not trade. " + spec["on_failure"].split(". ")[-1])

    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    (out / "prereg_v2_result.json").write_text(json.dumps({
        "spec": spec["name"], "spec_sha256": lock["sha256"], "locked_utc": lock["locked_utc"],
        "run_utc": datetime.now(timezone.utc).isoformat(), "criteria": crit}, indent=1, default=float), encoding="utf-8")
    pd.concat({"development": dev["returns"], "confirmation": conf["returns"]}).to_csv(out / "prereg_v2_weekly_returns.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
