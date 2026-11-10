"""Liquidity-driven asset class allocator. RESEARCH TOOL, NOT INVESTMENT ADVICE.

Idea: Fed net liquidity changes (fedliq.py) might help predict the next four weeks of
returns for stocks, Treasuries and credit. This tool
  1. builds a liquidity-to-returns dataset with strict point-in-time timing,
  2. fits a small ridge model with expanding-window walk-forward (no look-ahead),
  3. measures whether it actually works out of sample,
  4. turns forecasts into bounded tilts around neutral weights, and
  5. feeds the simulated liquidity paths from fedliq.py through the model.

Safeguards, because predicting markets is hard and a model that fits history is cheap:
  * SKILL GATE. A tilt for an asset is only taken if the model's trailing out-of-sample
    rank correlation with realized returns is statistically significant (t-stat of at least
    2), and then only in proportion to its out-of-sample R-squared versus a plain
    historical mean. Otherwise the allocator stays at neutral weights. Automatically.
  * EXTRAPOLATION GUARD. Features are clipped to the 1st-99th percentile of training data,
    so a 2020-sized simulated liquidity shock cannot produce a wild forecast.
  * Costs stay in. Results are compared with the static neutral mix, not with cash.
  * Every forecast carries a one-sigma band so you can see signal against noise.

Timing. The Fed publishes the balance sheet Thursday for the prior Wednesday. A feature
dated Wednesday w is therefore used from Friday w+2, and returns are measured from that
Friday. A training row is only used once its 4-week outcome is complete.

Asset class proxies built from FRED (price return, no dividends, no defaults):
  Stocks      S&P 500 index (FRED carries about 10 years)
  Treasuries  10y yield carry minus duration x yield change (duration 7)
  Credit      Moody's Baa yield, same construction (duration 7). Used because FRED's ICE BofA
              spread series now only go back about three years.
  Cash        3-month Treasury bill
These are rough proxies for real index returns.

Usage:
  python allocator.py
  python allocator.py --horizon 26 --custom "assets=-300,tga=100,rrp=0"
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import fedliq
import fredcfg

ASSETS = ["Stocks", "Treasuries", "Credit", "Cash"]
RISKY = ["Stocks", "Treasuries", "Credit"]
FEATURES = ["nl_4w", "nl_13w"]

# Placeholders. Lock these before looking at results; do not tune them to flatter a backtest.
CONFIG = {
    "neutral": {"Stocks": 0.50, "Treasuries": 0.30, "Credit": 0.10, "Cash": 0.10},
    "horizon_weeks": 4,          # forecast horizon and rebalance interval
    "min_train_weeks": 156,      # about three years before the first decision
    "ridge_alpha": 1.0,
    "max_tilt": 0.15,            # largest move from neutral for any one asset
    "z_cap": 2.0,                # forecast / volatility is capped at this many sigma
    "gate_r2_full": 0.02,        # trailing OOS R-squared at which the gate is fully open
    "gate_min_obs": 12,          # matured out-of-sample forecasts needed before any tilt
    "gate_min_tstat": 2.0,       # trailing rank-correlation t-stat needed before any tilt
    "cost_bps": 5.0,             # per unit of weight traded
    "durations": {"Treasuries": 7.0, "Credit": 7.0},
}


# ------------------------------------------------------------------ returns
def asset_returns(px: pd.DataFrame, durations: dict) -> pd.DataFrame:
    """Daily returns for the four proxies. px columns: spx, y10, baa, bill (yields in percent)."""
    df = px.dropna()
    prev = df.shift(1)
    gap = pd.Series(df.index, index=df.index).diff().dt.days / 365.0
    out = pd.DataFrame({
        "Stocks": df["spx"] / prev["spx"] - 1,
        "Treasuries": prev["y10"] / 100 * gap - durations["Treasuries"] * (df["y10"] - prev["y10"]) / 100,
        "Credit": prev["baa"] / 100 * gap - durations["Credit"] * (df["baa"] - prev["baa"]) / 100,
        "Cash": prev["bill"] / 100 * gap,
    })
    return out.iloc[1:]


def forward_returns(tri: pd.DataFrame, dates: pd.DatetimeIndex, weeks: int) -> pd.DataFrame:
    """Total return from each date to date + weeks. NaN when the window runs past the data.

    asof() would quietly reuse the last row for dates past the end and shrink the window,
    so those rows are blanked explicitly.
    """
    ends = dates + pd.Timedelta(weeks=weeks)
    a, b = tri.asof(dates), tri.asof(ends)
    fwd = pd.DataFrame(b.values / a.values - 1, index=dates, columns=tri.columns)
    fwd.loc[np.asarray(ends > tri.index[-1])] = np.nan
    return fwd


# ------------------------------------------------------------------ dataset
def liquidity_features(net_liq: pd.Series) -> pd.DataFrame:
    """Percent change in net liquidity over 4 and 13 weeks. Index = Wednesday of the data."""
    return pd.DataFrame({
        "nl_4w": net_liq / net_liq.shift(4) - 1,
        "nl_13w": net_liq / net_liq.shift(13) - 1,
    })


def build_dataset(net_liq: pd.Series, daily_ret: pd.DataFrame, cfg: dict = CONFIG) -> pd.DataFrame:
    """One row per decision date (Friday after each Wednesday).

    Columns: features, fwd_<asset> total returns, y_<risky asset> excess over cash.
    Rows whose outcome is not complete yet keep NaN targets (used only for live forecasts).
    """
    tri = (1 + daily_ret).cumprod()
    feats = liquidity_features(net_liq)
    feats.index = feats.index + pd.Timedelta(days=2)  # usable from Friday
    fwd = forward_returns(tri, feats.index, cfg["horizon_weeks"])
    ds = feats.join(fwd.add_prefix("fwd_"))
    for a in RISKY:
        ds[f"y_{a}"] = ds[f"fwd_{a}"] - ds["fwd_Cash"]
    ds.index.name = "decision_date"
    return ds[ds[FEATURES].notna().all(axis=1)]


# ------------------------------------------------------------------ model
def ridge_fit(X: np.ndarray, y: np.ndarray, alpha: float) -> dict:
    mu, sd = X.mean(0), X.std(0)
    sd = np.where(sd == 0, 1.0, sd)
    Z = (X - mu) / sd
    ym = y.mean()
    beta = np.linalg.solve(Z.T @ Z + alpha * np.eye(Z.shape[1]), Z.T @ (y - ym))
    resid = y - ym - Z @ beta
    return {"mu": mu, "sd": sd, "ym": ym, "beta": beta, "y_sd": float(y.std()),
            "resid_sd": float(resid.std()), "lo": np.percentile(X, 1, axis=0),
            "hi": np.percentile(X, 99, axis=0), "r2_in": 1 - float(resid.var() / y.var()) if y.var() > 0 else 0.0}


def ridge_predict(m: dict, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Forecasts plus a flag marking rows that had to be clipped (extrapolation guard)."""
    Xc = np.clip(X, m["lo"], m["hi"])
    clipped = (Xc != X).any(axis=1)
    return m["ym"] + ((Xc - m["mu"]) / m["sd"]) @ m["beta"], clipped


def skill_gate(preds: pd.DataFrame, asset: str, now: pd.Timestamp, cfg: dict) -> float:
    """0..1 from the trailing out-of-sample R-squared of forecasts whose outcome is known by `now`."""
    h = pd.Timedelta(weeks=cfg["horizon_weeks"])
    done = preds[preds.index + h <= now]
    if len(done) < cfg["gate_min_obs"]:
        return 0.0
    real, p, bench = done[f"real_{asset}"], done[f"pred_{asset}"], done[f"bench_{asset}"]
    denom = float(((real - bench) ** 2).sum())
    if denom <= 0:
        return 0.0
    r2 = 1 - float(((real - p) ** 2).sum()) / denom
    # Significance requirement: a small positive R-squared is easy to get by luck, so the
    # forecasts must also rank outcomes with a rank-correlation t-stat above the minimum.
    if rank_ic_tstat(p, real) < cfg["gate_min_tstat"]:
        return 0.0
    return float(np.clip(r2 / cfg["gate_r2_full"], 0.0, 1.0))


def rank_ic_tstat(pred: pd.Series, real: pd.Series) -> float:
    """t-stat of the Spearman rank correlation. Decisions are one horizon apart, so no overlap."""
    n = len(pred)
    if n < 3:
        return 0.0
    ic = float(pred.rank().corr(real.rank()))
    if not np.isfinite(ic):
        return 0.0
    return ic * np.sqrt((n - 2) / max(1e-9, 1 - ic ** 2))


def allocate(mu: dict, sigma: dict, gate: dict, cfg: dict = CONFIG) -> pd.Series:
    """Neutral weights plus bounded, gated tilts. Long-only, fully invested.

    tilt = max_tilt x gate x clip(forecast / volatility, +-z_cap) / z_cap, funded from cash.
    """
    w = dict(cfg["neutral"])
    for a in RISKY:
        z = np.clip(mu[a] / sigma[a], -cfg["z_cap"], cfg["z_cap"]) / cfg["z_cap"]
        w[a] = max(0.0, w[a] + cfg["max_tilt"] * gate[a] * z)
    risky_sum = sum(w[a] for a in RISKY)
    if risky_sum > 1.0:                       # not enough cash to fund the tilts
        for a in RISKY:
            w[a] /= risky_sum
        risky_sum = 1.0
    w["Cash"] = 1.0 - risky_sum
    return pd.Series(w)[ASSETS]


# ------------------------------------------------------------------ walk-forward
def walk_forward(ds: pd.DataFrame, cfg: dict = CONFIG, features: list | None = None) -> pd.DataFrame:
    """Decide every `horizon_weeks` weeks using only rows whose outcome was complete.

    Returns one row per decision: forecasts, expanding-mean benchmark, realized excess
    return, volatility, gate, and the resulting weights. `features` picks the model inputs
    (default: the liquidity features); rows missing any chosen feature are skipped.
    """
    features = list(features or FEATURES)
    h = pd.Timedelta(weeks=cfg["horizon_weeks"])
    target_cols = [f"y_{a}" for a in RISKY]
    labeled = ds.dropna(subset=target_cols + [f"fwd_{a}" for a in ASSETS] + features)
    rows, step = [], cfg["horizon_weeks"]
    first = None
    for i in range(0, len(labeled), 1):
        d = labeled.index[i]
        train = labeled[labeled.index + h <= d]
        if len(train) < cfg["min_train_weeks"]:
            continue
        if first is None:
            first = i
        if (i - first) % step:
            continue
        x = labeled.loc[[d], features].to_numpy()
        rec = {"decision_date": d}
        mu, sig = {}, {}
        for a in RISKY:
            m = ridge_fit(train[features].to_numpy(), train[f"y_{a}"].to_numpy(), cfg["ridge_alpha"])
            p, _ = ridge_predict(m, x)
            mu[a], sig[a] = float(p[0]), m["y_sd"]
            rec[f"pred_{a}"], rec[f"bench_{a}"] = mu[a], m["ym"]
            rec[f"real_{a}"] = float(labeled.loc[d, f"y_{a}"])
            rec[f"sd_{a}"] = m["y_sd"]
        for a in ASSETS:
            rec[f"fwd_{a}"] = float(labeled.loc[d, f"fwd_{a}"])
        done = pd.DataFrame(rows).set_index("decision_date") if rows else pd.DataFrame()
        gate = {a: (skill_gate(done, a, d, cfg) if len(done) else 0.0) for a in RISKY}
        w = allocate(mu, sig, gate, cfg)
        for a in RISKY:
            rec[f"gate_{a}"] = gate[a]
        for a in ASSETS:
            rec[f"w_{a}"] = w[a]
        rows.append(rec)
    return pd.DataFrame(rows).set_index("decision_date")


def diagnostics(preds: pd.DataFrame) -> pd.DataFrame:
    """Out-of-sample skill per asset. Decisions are 4 weeks apart so outcomes do not overlap."""
    out = {}
    for a in RISKY:
        real, p, b = preds[f"real_{a}"], preds[f"pred_{a}"], preds[f"bench_{a}"]
        n = len(preds)
        ic = float(p.rank().corr(real.rank()))  # Spearman, without needing scipy
        out[a] = {
            "decisions": n,
            "OOS R2 vs mean": 1 - float(((real - p) ** 2).sum() / ((real - b) ** 2).sum()),
            "IC (rank corr)": ic,
            "IC t-stat": rank_ic_tstat(p, real),
            "hit rate": float((np.sign(p - b) == np.sign(real - b)).mean()),
        }
    return pd.DataFrame(out).T


# ------------------------------------------------------------------ backtest
def _stats(r: pd.Series, per_year: float) -> dict:
    n = len(r)
    wealth = (1 + r).cumprod()
    return {
        "ann. return": float(wealth.iloc[-1] ** (per_year / n) - 1),
        "ann. vol": float(r.std(ddof=1) * np.sqrt(per_year)),
        "max drawdown": float((wealth / wealth.cummax() - 1).min()),
    }


def backtest(preds: pd.DataFrame, cfg: dict = CONFIG, seed: int = 0) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Net returns of the allocator vs the static neutral mix, one row per 4-week period."""
    per_year = 52 / cfg["horizon_weeks"]
    fwd = preds[[f"fwd_{a}" for a in ASSETS]].set_axis(ASSETS, axis=1)
    w = preds[[f"w_{a}" for a in ASSETS]].set_axis(ASSETS, axis=1)
    neutral = pd.Series(cfg["neutral"])[ASSETS]
    turnover = w.diff().abs().sum(axis=1).fillna(0.0)
    alloc = (w * fwd).sum(axis=1) - turnover * cfg["cost_bps"] / 1e4
    base = (fwd * neutral).sum(axis=1)
    rets = pd.DataFrame({"Allocator": alloc, "Neutral": base})
    rets["Excess"] = rets["Allocator"] - rets["Neutral"]

    rows = {k: _stats(rets[k], per_year) for k in ("Allocator", "Neutral")}
    te = float(rets["Excess"].std(ddof=1) * np.sqrt(per_year))
    rows["Allocator"]["excess vs neutral"] = float(rets["Excess"].mean() * per_year)
    rows["Allocator"]["tracking error"] = te
    rows["Allocator"]["info ratio"] = rows["Allocator"]["excess vs neutral"] / te if te > 1e-12 else np.nan
    rows["Allocator"]["avg turnover / yr"] = float(turnover.mean() * per_year)
    rows["Neutral"]["excess vs neutral"] = 0.0

    rng = np.random.default_rng(seed)
    ex = rets["Excess"].to_numpy()
    boot = np.array([rng.choice(ex, len(ex)).mean() * per_year for _ in range(2000)])
    ci = (float(np.percentile(boot, 5)), float(np.percentile(boot, 95)))
    by_year = rets["Excess"].groupby(rets.index.year).sum().rename("excess (sum of 4w periods)")
    return pd.DataFrame(rows).T, by_year.to_frame(), {"excess_ci90": ci, "rets": rets, "weights": w}


# ------------------------------------------------------------------ scenarios
def fit_final(ds: pd.DataFrame, preds: pd.DataFrame, cfg: dict = CONFIG) -> dict:
    """Models on all completed outcomes, plus the skill gate as of the latest data."""
    h = pd.Timedelta(weeks=cfg["horizon_weeks"])
    labeled = ds.dropna(subset=[f"y_{a}" for a in RISKY])
    models = {a: ridge_fit(labeled[FEATURES].to_numpy(), labeled[f"y_{a}"].to_numpy(), cfg["ridge_alpha"])
              for a in RISKY}
    now = labeled.index[-1] + h
    gate = {a: skill_gate(preds, a, now, cfg) for a in RISKY}
    return {"models": models, "gate": gate}


def simulate_path(net_liq_hist: pd.Series, path_net_liq: pd.Series, fit: dict, cfg: dict = CONFIG) -> dict:
    """Run one simulated net liquidity path through the models.

    path_net_liq: values for weeks 0..H ahead (week 0 = latest actual). Forecast for week k+1
    uses only features known at week k. Each 4-week forecast is spread evenly over its 4 weeks.
    """
    H = len(path_net_liq) - 1
    idx = [net_liq_hist.index[-1] + pd.Timedelta(weeks=k) for k in range(1, H + 1)]
    full = pd.concat([net_liq_hist, pd.Series(path_net_liq.iloc[1:].to_numpy(), index=idx)])
    feats = liquidity_features(full).iloc[-(H + 1):-1]       # weeks 0..H-1
    X = feats.to_numpy()
    cum, band, clip_share, mus = {}, {}, 0.0, {}
    for a in RISKY:
        mu, clipped = ridge_predict(fit["models"][a], X)
        mus[a] = mu
        cum[a] = float(mu.sum() / cfg["horizon_weeks"])
        band[a] = fit["models"][a]["resid_sd"] * np.sqrt(H / cfg["horizon_weeks"])
        clip_share = float(clipped.mean())
    weights = []
    for k in range(0, H, cfg["horizon_weeks"]):
        w = allocate({a: mus[a][k] for a in RISKY}, {a: fit["models"][a]["y_sd"] for a in RISKY},
                     fit["gate"], cfg)
        weights.append(w)
    return {"cum_excess": cum, "band": band, "clipped_share": clip_share,
            "avg_weights": pd.concat(weights, axis=1).mean(axis=1)}


def scenario_forecasts(weekly: pd.DataFrame, paths: dict, fit: dict, cfg: dict = CONFIG) -> pd.DataFrame:
    rows = []
    for name, p in paths.items():
        r = simulate_path(weekly["net_liq"], p["net_liq"], fit, cfg)
        row = {"scenario": name, "net liq change %": (p["net_liq"].iloc[-1] / p["net_liq"].iloc[0] - 1) * 100}
        for a in RISKY:
            row[f"{a} exp. excess %"] = r["cum_excess"][a] * 100
            row[f"{a} 1-sigma %"] = r["band"][a] * 100
        row["features clipped %"] = r["clipped_share"] * 100
        for a in ASSETS:
            row[f"avg w {a}"] = r["avg_weights"][a]
        rows.append(row)
    df = pd.DataFrame(rows).set_index("scenario")
    # The first path is "hold today's levels". Its forecast is mostly the historical average
    # premium, so the liquidity effect is the difference from it.
    for a in RISKY:
        df.insert(df.columns.get_loc(f"{a} exp. excess %") + 1, f"{a} liquidity effect %",
                  df[f"{a} exp. excess %"] - df[f"{a} exp. excess %"].iloc[0])
    return df


# ------------------------------------------------------------------ plumbing
def load_prices(start: str, source=None) -> pd.DataFrame:
    source = source or fredcfg.get_source()
    return pd.concat({
        "spx": source.series("SP500", start), "y10": source.series("DGS10", start),
        "baa": source.series("DBAA", start), "bill": source.series("DTB3", start),
    }, axis=1, sort=True)


def load_inputs(start: str, source=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    source = source or fredcfg.get_source()
    return fedliq.fetch_all(start, source)["weekly"], load_prices(start, source)


def current_target(ds: pd.DataFrame, fit: dict, cfg: dict = CONFIG) -> dict:
    """Model target weights for the latest liquidity reading, with forecasts and gates."""
    x = ds[FEATURES].iloc[[-1]].to_numpy()
    mu = {a: float(ridge_predict(fit["models"][a], x)[0][0]) for a in RISKY}
    sigma = {a: fit["models"][a]["y_sd"] for a in RISKY}
    w = allocate(mu, sigma, fit["gate"], cfg)
    neutral = pd.Series(cfg["neutral"])[ASSETS]
    return {"weights": w, "forecast": mu, "gate": fit["gate"],
            "tilt_max_abs": float((w - neutral).abs().max()), "as_of": ds.index[-1]}


def plot(bt: dict, table: pd.DataFrame, outfile: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (a, b) = plt.subplots(1, 2, figsize=(14, 5))
    rets = bt["rets"]
    (1 + rets[["Allocator", "Neutral"]]).cumprod().mul(100).plot(ax=a, lw=2)
    a.set_title("Walk-forward backtest, net of costs (growth of 100)")
    a.grid(alpha=.3)
    names = list(table.index)
    y = table["Stocks liquidity effect %"]
    err = table["Stocks 1-sigma %"]
    b.barh(range(len(names)), y, xerr=err, color="tab:blue", alpha=.7, capsize=4)
    b.set_yticks(range(len(names)), names, fontsize=8)
    b.axvline(0, color="black", lw=.8)
    b.set_title("Stocks: liquidity effect vs 'hold' (bar) against 1-sigma noise (whisker)", fontsize=10)
    b.set_xlabel("% over the horizon")
    fig.tight_layout()
    fig.savefig(outfile, dpi=130)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default="2010-01-01")
    ap.add_argument("--horizon", type=int, default=26, help="scenario length in weeks")
    ap.add_argument("--custom", help='e.g. "assets=-300,tga=100,rrp=0"')
    ap.add_argument("--out", default="output")
    args = ap.parse_args(argv)
    cfg = CONFIG
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    src = fredcfg.get_source()
    weekly, px = load_inputs(args.start, src)
    print(f"FRED mode: {src.mode}. Stocks history starts {px['spx'].dropna().index[0]:%Y-%m-%d}.")
    ds = build_dataset(weekly["net_liq"], asset_returns(px, cfg["durations"]), cfg)
    preds = walk_forward(ds, cfg)
    print(f"\nWalk-forward: {len(preds)} decisions, {preds.index[0]:%Y-%m} to {preds.index[-1]:%Y-%m}, "
          f"every {cfg['horizon_weeks']} weeks.")

    print("\nOUT-OF-SAMPLE SKILL (does liquidity predict returns better than the historical mean?)")
    diag = diagnostics(preds)
    print(diag.round(3).to_string())

    stats, by_year, extra = backtest(preds, cfg)
    print("\nBACKTEST vs static neutral mix (net of costs)")
    print(stats.round(4).to_string())
    lo, hi = extra["excess_ci90"]
    print(f"Excess vs neutral, 90% bootstrap interval: {lo:+.2%} to {hi:+.2%} per year")
    print("\nAllocator excess vs neutral by calendar year")
    print(by_year.round(4).to_string())

    fit = fit_final(ds, preds, cfg)
    print("\nSkill gate today (0 = stay at neutral, 1 = full tilts):",
          {a: round(g, 2) for a, g in fit["gate"].items()})
    print("Standardized model coefficients [nl_4w, nl_13w]:",
          {a: fit["models"][a]["beta"].round(4).tolist() for a in RISKY},
          "| in-sample R2:", {a: round(fit["models"][a]["r2_in"], 3) for a in RISKY})

    paths, _ = fedliq.scenario_table(weekly, args.horizon, fedliq.parse_custom(args.custom) if args.custom else None)
    table = scenario_forecasts(weekly, paths, fit, cfg)
    print(f"\nSCENARIOS over {args.horizon} weeks: model-implied excess return over cash, with 1-sigma noise")
    print(table.round(2).T.to_string())
    if all(g == 0 for g in fit["gate"].values()):
        print("\nGate is closed for every asset: the model has not beaten the historical mean out of "
              "sample, so the allocator holds neutral weights in every scenario.")
    print("Forecasts are small next to their noise bands. Treat them as sensitivity, not predictions.")

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    preds.to_csv(out / "allocator_walk_forward.csv")
    table.to_csv(out / "allocator_scenarios.csv")
    plot(extra, table, out / "allocator.png")
    print(f"\nWrote {out}/allocator_walk_forward.csv, allocator_scenarios.csv, allocator.png")


if __name__ == "__main__":
    main()
