"""Point-in-time backtest of the multi-node regime rules against buy and hold.

What is tested: the nodes in alert_rules.json (each a macro or market trigger with a pre-written
tilt) turn the neutral mix into a target mix every Friday. Would that have beaten simply holding
the neutral mix, or the S&P 500, from 2020 through the latest data?

Design, to keep the test honest
  * Point-in-time. Each metric is used only from its publication date plus a conservative lag.
    Weights set at Friday's close earn the following week; nothing sees the future.
  * Same rules as live. Node state uses alerts.next_triggered and weights use regime.target_weights.
  * Costs. 5 bps on every unit of weight traded, with turnover measured against drifted weights.
  * Benchmarks. (1) buy and hold of the neutral mix, never rebalanced; (2) the neutral mix
    rebalanced weekly, which isolates the rules' effect from rebalancing; (3) 100% S&P 500.
  * Thresholds. Several thresholds in alert_rules.json were set from 2010-2026 percentiles, which
    includes this test window. So the headline run RE-ESTIMATES those thresholds from data before
    2020 only (same percentiles). The shipped thresholds are shown as a second, flattered run.
  * Nodes whose history would leak the future (GDPNow, CBO potential) are excluded.
  * Remaining caveat: revised series (CPI, WEI, CFNAI, unemployment) are the last-revised values.
  * Tilts and the 20-point cap were fixed before any result was seen and are not tuned here.

  python regime_backtest.py
  python regime_backtest.py --start 2020-01-01 --cost-bps 5
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import alerts
import allocator as al
import fedliq
import fredcfg
import macro
import pipeline as pl
import regime

ROOT = Path(__file__).resolve().parent
PCT_NODE_METRICS = {"net_liq_4w_pct", "net_liq_13w_pct", "tga_4w_chg_bn", "vix", "baa_spread", "nfci",
                    "stlfsi", "dgs10_4w_chg_bp", "dollar_4w_pct"}   # thresholds that were percentile-based
STRATS = ["Regime rules", "Buy & hold (neutral)", "Neutral, rebalanced weekly", "S&P 500",
          "Static mix, same average weights"]
SHORT = {"Buy & hold (neutral)": "buy & hold", "Neutral, rebalanced weekly": "rebalanced neutral",
         "S&P 500": "S&P 500", "Static mix, same average weights": "matched static mix"}

# Market series the rules use that are not part of the macro pipeline, with conservative lags.
EXTRA_SPECS = {
    "VIXCLS": pl.SeriesSpec("VIXCLS", "VIX", "D", "level", 1, "mkt"),
    "T10Y2Y": pl.SeriesSpec("T10Y2Y", "10y-2y", "D", "level", 1, "mkt"),
    "BAA10Y": pl.SeriesSpec("BAA10Y", "Baa-10y", "D", "level", 1, "mkt"),
    "DGS10": pl.SeriesSpec("DGS10", "10y", "D", "level", 1, "mkt"),
    "DTWEXBGS": pl.SeriesSpec("DTWEXBGS", "Broad dollar", "D", "level", 7, "mkt"),   # published weekly
    "NFCI": pl.SeriesSpec("NFCI", "NFCI", "W", "level", 5, "mkt"),                   # Friday data, out Wednesday
    "STLFSI4": pl.SeriesSpec("STLFSI4", "STLFSI", "W", "level", 6, "mkt"),           # Friday data, out Thursday
}


# ------------------------------------------------------------------ point-in-time metric history
def known_on(s: pd.Series, release_dates: pd.DatetimeIndex, dates: pd.DatetimeIndex) -> pd.Series:
    """Latest value of s that had been released by each date."""
    rel = pd.Series(s.to_numpy(), index=release_dates).sort_index()
    rel = rel[~rel.index.duplicated(keep="last")]
    return rel.reindex(rel.index.union(dates)).ffill().reindex(dates)


def change_over_days(s: pd.Series, days: int, scale: float = 1.0, pct: bool = False) -> pd.Series:
    """Change versus the last observation at least `days` earlier, per observation date."""
    base = s.asof(s.index - pd.Timedelta(days=days)).to_numpy()
    cur = s.to_numpy()
    return pd.Series((cur / base - 1) * 100 if pct else (cur - base) * scale, index=s.index)


def metric_history(weekly: pd.DataFrame, market: dict, macro_series: dict, dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Every rule metric as it would have been known on each decision date (Fridays)."""
    nl = weekly["net_liq"]
    friday = nl.index + pd.Timedelta(days=2)               # H.4.1 is out Thursday, so usable Friday
    cols = {
        "net_liq_4w_pct": known_on((nl / nl.shift(4) - 1) * 100, friday, dates),
        "net_liq_13w_pct": known_on((nl / nl.shift(13) - 1) * 100, friday, dates),
        "tga_4w_chg_bn": known_on(weekly["tga"].diff(4), friday, dates),
    }

    def aligned(sid, derived=None):
        s = market[sid] if derived is None else derived
        return pl.align_to(s, EXTRA_SPECS[sid], dates)

    cols["vix"] = aligned("VIXCLS")
    cols["curve_10y2y"] = aligned("T10Y2Y")
    cols["baa_spread"] = aligned("BAA10Y")
    cols["nfci"] = aligned("NFCI")
    cols["stlfsi"] = aligned("STLFSI4")
    cols["dgs10_4w_chg_bp"] = aligned("DGS10", change_over_days(market["DGS10"], 28, scale=100))
    cols["dollar_4w_pct"] = aligned("DTWEXBGS", change_over_days(market["DTWEXBGS"], 28, pct=True))
    for name, (base, s) in macro.metric_series(macro_series).items():
        cols[name] = pl.align_to(s, pl.SPEC_BY_ID[base], dates)
    return pd.DataFrame(cols, index=dates)


# ------------------------------------------------------------------ nodes, thresholds, weights
def eligible_rules(rules: list, hist: pd.DataFrame) -> list:
    """Rules with a tilt, usable point in time, and with history available."""
    return [r for r in rules if r.get("tilt") and r.get("pit", "ok") != "exclude" and r["metric"] in hist.columns]


def calibrate_pre_cutoff(rules: list, hist: pd.DataFrame, cutoff: str = "2020-01-01",
                         hi: float = 95, lo: float = 5, clear_hi: float = 90, clear_lo: float = 10):
    """Re-estimate percentile-based thresholds from data before `cutoff` only. Returns (rules, table)."""
    pre = hist[hist.index < pd.Timestamp(cutoff)]
    new, rows = [], []
    for r in rules:
        r2 = dict(r)
        if r["metric"] in PCT_NODE_METRICS and pre[r["metric"]].notna().sum() > 100:
            x = pre[r["metric"]].dropna()
            up = r["op"] in (">", ">=")
            r2["value"] = float(np.percentile(x, hi if up else lo))
            r2["clear"] = float(np.percentile(x, clear_hi if up else clear_lo))
            rows.append({"node": r["id"], "metric": r["metric"], "op": r["op"], "shipped": r["value"],
                         "pre-2020": r2["value"]})
        new.append(r2)
    return new, pd.DataFrame(rows)


def node_states(rules: list, hist: pd.DataFrame) -> pd.DataFrame:
    """On/off state of each node on each date, stepped forward with hysteresis. NaN keeps the last state."""
    state = {r["id"]: None for r in rules}
    out = []
    for t, row in hist.iterrows():
        for r in rules:
            v = row[r["metric"]]
            if pd.isna(v):
                continue
            state[r["id"]] = alerts.next_triggered(state[r["id"]], float(v), r)
        out.append({k: bool(s) for k, s in state.items()})
    return pd.DataFrame(out, index=hist.index)


def target_path(rules: list, states: pd.DataFrame, max_dev: float) -> pd.DataFrame:
    rows = {t: regime.target_weights([k for k, on in s.items() if on], rules, max_dev) for t, s in states.iterrows()}
    return pd.DataFrame(rows).T[al.ASSETS]


# ------------------------------------------------------------------ portfolio simulation
def weekly_asset_returns(daily: pd.DataFrame, dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Return of each asset from each date to the next, row-labelled by the start date."""
    tri = (1 + daily).cumprod().asof(dates)
    r = tri.shift(-1) / tri - 1
    return r.iloc[:-1].dropna()


def simulate(weights: pd.DataFrame, rets: pd.DataFrame, cost_bps: float, rebalance: bool = True) -> pd.DataFrame:
    """Weekly net returns. Turnover is measured against weights drifted by the week's returns.

    The first purchase is free for every strategy so the comparison is not tilted by entry cost.
    With rebalance=False the initial weights are held and simply drift (buy and hold).
    """
    held, net, turn = None, [], []
    for t in rets.index:
        target = weights.loc[t] if (rebalance or held is None) else held
        traded = 0.0 if held is None else float((target - held).abs().sum())
        r = rets.loc[t, al.ASSETS]
        gross = float((target * r).sum())
        net.append(gross - traded * cost_bps / 1e4)
        turn.append(traded)
        held = target * (1 + r) / (1 + gross)
    return pd.DataFrame({"net": net, "turnover": turn}, index=rets.index)


def run(hist: pd.DataFrame, rules: list, daily: pd.DataFrame, start: str, cost_bps: float, max_dev: float) -> dict:
    rules = eligible_rules(rules, hist)
    states = node_states(rules, hist)
    targets = target_path(rules, states, max_dev)
    dates = hist.index
    rets = weekly_asset_returns(daily, dates)
    rets = rets[rets.index >= pd.Timestamp(start)]
    neutral = pd.DataFrame([pd.Series(al.CONFIG["neutral"])[al.ASSETS]] * len(rets), index=rets.index)
    stocks = pd.DataFrame(0.0, index=rets.index, columns=al.ASSETS).assign(Stocks=1.0)
    # Control for "it just held less stock": a static mix at the rules' own average weights. This
    # uses the average over the test window, so it is a diagnostic control, not a tradable strategy.
    avg = targets.loc[rets.index].mean()
    matched = pd.DataFrame([avg] * len(rets), index=rets.index)
    sims = {
        "Static mix, same average weights": simulate(matched, rets, cost_bps),
        "Regime rules": simulate(targets.loc[rets.index], rets, cost_bps),
        "Buy & hold (neutral)": simulate(neutral, rets, cost_bps, rebalance=False),
        "Neutral, rebalanced weekly": simulate(neutral, rets, cost_bps),
        "S&P 500": simulate(stocks, rets, 0.0, rebalance=False),
    }
    return {"rules": rules, "states": states.loc[rets.index], "targets": targets.loc[rets.index], "rets": rets,
            "returns": pd.DataFrame({k: v["net"] for k, v in sims.items()})[STRATS],
            "turnover": pd.DataFrame({k: v["turnover"] for k, v in sims.items()})[STRATS]}


# ------------------------------------------------------------------ statistics
def ann_return(r: pd.Series) -> float:
    return float((1 + r).prod() ** (52 / len(r)) - 1)


def block_bootstrap_ci(x: np.ndarray, block: int = 8, draws: int = 2000, seed: int = 0, per_year: int = 52):
    """90% interval for the mean of x (annualized), resampling blocks to respect autocorrelation."""
    rng = np.random.default_rng(seed)
    n = len(x)
    nb = int(np.ceil(n / block))
    means = []
    for _ in range(draws):
        starts = rng.integers(0, n - block + 1, nb)
        means.append(np.concatenate([x[s:s + block] for s in starts])[:n].mean() * per_year)
    return float(np.percentile(means, 5)), float(np.percentile(means, 95))


def summarize(res: dict, cash_weekly: pd.Series) -> pd.DataFrame:
    r = res["returns"]
    cash = cash_weekly.reindex(r.index)
    rows = {}
    for s in STRATS:
        x = r[s]
        wealth = (1 + x).cumprod()
        excess_cash = x - cash
        row = {"ann. return": ann_return(x), "ann. vol": float(x.std(ddof=1) * np.sqrt(52)),
               "Sharpe (vs cash)": float(excess_cash.mean() / excess_cash.std(ddof=1) * np.sqrt(52)),
               "max drawdown": float((wealth / wealth.cummax() - 1).min()),
               "avg turnover/yr": float(res["turnover"][s].mean() * 52)}
        for b in STRATS[1:]:
            row[f"excess vs {SHORT[b]}"] = float((x - r[b]).mean() * 52) if s != b else 0.0
        rows[s] = row
    return pd.DataFrame(rows).T


def excess_tests(res: dict) -> pd.DataFrame:
    r = res["returns"]["Regime rules"]
    rows = []
    for b in STRATS[1:]:
        d = (r - res["returns"][b]).to_numpy()
        lo, hi = block_bootstrap_ci(d)
        rows.append({"vs": b, "excess %/yr": d.mean() * 52 * 100, "90% CI low": lo * 100, "90% CI high": hi * 100,
                     "weeks outperformed %": float((d > 0).mean() * 100),
                     "t-stat (naive)": d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))})
    return pd.DataFrame(rows)


def by_year(res: dict) -> pd.DataFrame:
    r = res["returns"]
    yearly = r.groupby(r.index.year).apply(lambda g: (1 + g).prod() - 1)
    yearly["Rules minus rebalanced neutral"] = yearly["Regime rules"] - yearly["Neutral, rebalanced weekly"]
    return yearly


def node_attribution(res: dict) -> pd.DataFrame:
    """Approximate contribution of each node: sum over weeks of tilt . asset returns while it was on.

    Ignores the deviation cap, normalization, costs and compounding, so it is a guide to which
    nodes helped or hurt, not an exact decomposition.
    """
    rets, states = res["rets"], res["states"]
    rows = []
    for r in res["rules"]:
        tilt = pd.Series(r["tilt"]).reindex(al.ASSETS).fillna(0.0)
        week = rets[al.ASSETS] @ tilt
        on = states[r["id"]]
        rows.append({"node": r["id"], "weeks on": int(on.sum()), "% of time on": float(on.mean() * 100),
                     "contribution (pts, summed)": float(week[on].sum() * 100)})
    return pd.DataFrame(rows).sort_values("contribution (pts, summed)", ascending=False).set_index("node")


def exposure(res: dict) -> pd.DataFrame:
    t = res["targets"]
    neutral = pd.Series(al.CONFIG["neutral"])[al.ASSETS]
    shifts = int((t.diff().abs().max(axis=1) >= regime.DEFAULTS["min_change"]).sum())
    out = pd.DataFrame({"average weight": t.mean(), "neutral": neutral, "min": t.min(), "max": t.max()})
    out.attrs["shifts"] = shifts
    out.attrs["weeks_any_node"] = float((res["states"].any(axis=1)).mean() * 100)
    return out


# ------------------------------------------------------------------ plotting
def plot(res: dict, outfile: Path, title: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    r = res["returns"]
    wealth = (1 + r).cumprod() * 100
    fig, ax = plt.subplots(3, 1, figsize=(12, 12), sharex=True, gridspec_kw={"height_ratios": [3, 2, 2]})
    for s in STRATS:
        ax[0].plot(wealth.index, wealth[s], label=s, lw=2.2 if s == "Regime rules" else 1.4)
    ax[0].set_title(title)
    ax[0].set_ylabel("growth of 100")
    ax[0].legend(fontsize=9)
    dd = wealth / wealth.cummax() - 1
    for s in STRATS:
        ax[1].plot(dd.index, dd[s] * 100, label=s, lw=1.6 if s == "Regime rules" else 1.1)
    ax[1].set_ylabel("drawdown %")
    t = res["targets"]
    ax[2].plot(t.index, t["Stocks"] * 100, label="Stocks target %", lw=1.6)
    ax[2].plot(t.index, t["Cash"] * 100, label="Cash target %", lw=1.2)
    ax[2].axhline(al.CONFIG["neutral"]["Stocks"] * 100, color="gray", ls=":", lw=1)
    n_on = res["states"].sum(axis=1)
    ax2 = ax[2].twinx()
    ax2.fill_between(n_on.index, n_on, step="mid", alpha=.15, color="red", label="nodes on")
    ax2.set_ylabel("nodes on")
    ax[2].set_ylabel("target weight %")
    ax[2].legend(loc="upper left", fontsize=9)
    for a in ax:
        a.grid(alpha=.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outfile, dpi=120)
    plt.close(fig)


# ------------------------------------------------------------------ driver
def load_everything(start_hist: str = "2010-01-01"):
    src = fredcfg.get_source()
    weekly = fedliq.fetch_all(start_hist, src)["weekly"]
    prices = al.load_prices(start_hist, src)
    market = {sid: src.series(sid, start_hist) for sid in EXTRA_SPECS}
    data = macro.collect(src)
    return weekly, prices, market, data.series


def report(label: str, res: dict, cash_weekly: pd.Series) -> None:
    pd.set_option("display.width", 220)
    pd.set_option("display.float_format", lambda v: f"{v:,.3f}")
    print(f"\n{'=' * 100}\n{label}\n{'=' * 100}")
    r = res["returns"]
    print(f"Window: {r.index[0]:%Y-%m-%d} to {r.index[-1]:%Y-%m-%d}, {len(r)} weekly periods. "
          f"Nodes used: {len(res['rules'])}.")
    s = summarize(res, cash_weekly)
    fmt = s.copy()
    for c in ["ann. return", "ann. vol", "max drawdown", "avg turnover/yr"] + [c for c in s.columns if c.startswith("excess")]:
        fmt[c] = (s[c] * 100).map(lambda v: f"{v:,.2f}%")
    fmt["Sharpe (vs cash)"] = s["Sharpe (vs cash)"].map(lambda v: f"{v:,.2f}")
    print("\nPERFORMANCE (net of 5bps costs; excess columns are annualized, simple average)")
    print(fmt.to_string())
    print("\nSTATISTICAL TEST of Regime rules minus each benchmark")
    print(excess_tests(res).to_string(index=False))
    print("\nCALENDAR YEARS (total return)")
    print((by_year(res) * 100).round(2).to_string())
    e = exposure(res)
    print(f"\nEXPOSURE: any node on {e.attrs['weeks_any_node']:.0f}% of weeks; {e.attrs['shifts']} regime shifts "
          f"(target moved 2+ points)")
    print((e * 100).round(1).to_string())
    print("\nNODE ATTRIBUTION (approximate, points of return summed over weeks)")
    print(node_attribution(res).round(2).to_string())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default="2020-01-01")
    ap.add_argument("--cost-bps", type=float, default=5.0)
    ap.add_argument("--out", default="output")
    args = ap.parse_args(argv)

    cfg = alerts.load_rules()
    max_dev = regime.regime_cfg(cfg)["max_dev"]
    weekly, prices, market, macro_series = load_everything()
    daily = al.asset_returns(prices, al.CONFIG["durations"])
    dates = pd.date_range("2010-06-04", daily.index[-1], freq="W-FRI")
    hist = metric_history(weekly, market, macro_series, dates)
    print(f"Metric history: {len(dates)} Fridays, {dates[0]:%Y-%m-%d} to {dates[-1]:%Y-%m-%d}. "
          f"Asset returns start {daily.index[0]:%Y-%m-%d}.")
    excluded = [r["id"] for r in cfg["rules"] if r.get("tilt") and r.get("pit") == "exclude"]
    print(f"Excluded for point-in-time leakage: {', '.join(excluded)}")
    caveat = [r["id"] for r in cfg["rules"] if r.get("tilt") and r.get("pit") == "caveat"]
    print(f"Included with a revision caveat: {', '.join(caveat)}")

    cash_weekly = weekly_asset_returns(daily, dates)["Cash"]
    cal_rules, table = calibrate_pre_cutoff(cfg["rules"], hist, args.start)
    print("\nTHRESHOLDS re-estimated from pre-2020 data only (same percentiles as shipped):")
    print(table.round(3).to_string(index=False))

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    res_clean = run(hist, cal_rules, daily, args.start, args.cost_bps, max_dev)
    report("HEADLINE: thresholds calibrated on pre-2020 data only", res_clean, cash_weekly)
    res_ship = run(hist, cfg["rules"], daily, args.start, args.cost_bps, max_dev)
    report("FLATTERED REFERENCE: shipped thresholds (calibrated on 2010-2026, includes the test window)",
           res_ship, cash_weekly)

    pd.concat({"returns": res_clean["returns"], "targets": res_clean["targets"].add_prefix("w_"),
               "nodes_on": res_clean["states"].sum(axis=1).rename("n")}, axis=1).to_csv(out / "regime_backtest_weekly.csv")
    summarize(res_clean, cash_weekly).to_csv(out / "regime_backtest_summary.csv")
    node_attribution(res_clean).to_csv(out / "regime_node_attribution.csv")
    plot(res_clean, out / "regime_backtest.png", "Regime rules vs buy and hold (pre-2020 thresholds, net of costs)")
    print(f"\nWrote regime_backtest_weekly.csv, regime_backtest_summary.csv, regime_node_attribution.csv, "
          f"regime_backtest.png to {out}/")


if __name__ == "__main__":
    main()
