"""Offline tests for the allocator. Synthetic data only, no network."""
import numpy as np
import pandas as pd
import pytest

import allocator as al
import fedliq

CFG = {**al.CONFIG, "min_train_weeks": 100, "gate_min_obs": 8}


def synth(n_weeks=420, signal=0.0, seed=1):
    """Weekly net liquidity plus daily asset returns. `signal` plants a real liquidity edge in stocks."""
    rng = np.random.default_rng(seed)
    wed = pd.date_range("2016-01-06", periods=n_weeks, freq="W-WED")
    nl = pd.Series(5000 * np.exp(np.cumsum(rng.normal(0, 0.012, n_weeks))), index=wed)
    feats = al.liquidity_features(nl)
    days = pd.bdate_range(wed[0], wed[-1] + pd.Timedelta(weeks=8))
    ret = pd.DataFrame(rng.normal(0, 0.008, (len(days), 4)) + 0.0002, index=days, columns=al.ASSETS)
    ret["Cash"] = 0.00008
    if signal:
        # stocks earn extra over the 4 weeks after a Friday that follows a strong 4w liquidity change
        z = (feats["nl_4w"] / feats["nl_4w"].std()).fillna(0)
        for w, v in z.items():
            start = w + pd.Timedelta(days=2)
            span = ret.index[(ret.index > start) & (ret.index <= start + pd.Timedelta(weeks=4))]
            ret.loc[span, "Stocks"] += signal * v * 0.0015 / max(1, len(span)) * 20
    return nl, ret


# ------------------------------------------------------------ timing
def test_forward_returns_blank_when_window_runs_past_the_data():
    idx = pd.bdate_range("2020-01-01", periods=60)
    tri = pd.DataFrame({"Stocks": np.linspace(1, 2, 60)}, index=idx)
    dates = pd.DatetimeIndex([idx[0], idx[-5]])
    fwd = al.forward_returns(tri, dates, 4)
    assert fwd.iloc[0, 0] == pytest.approx(tri.asof(idx[0] + pd.Timedelta(weeks=4)).iloc[0] / 1 - 1)
    assert np.isnan(fwd.iloc[1, 0])  # would be silently truncated without the explicit blanking


def test_features_are_usable_from_the_friday_after_the_wednesday():
    nl, ret = synth(80)
    ds = al.build_dataset(nl, ret, CFG)
    assert all(d.day_of_week == 4 for d in ds.index)


def test_walk_forward_ignores_the_future():
    nl, ret = synth(300)
    ds = al.build_dataset(nl, ret, CFG)
    base = al.walk_forward(ds, CFG)
    cut = base.index[len(base) // 2]
    h = pd.Timedelta(weeks=CFG["horizon_weeks"])
    wrecked = ds.copy()
    future_x = wrecked.index > cut
    future_y = wrecked.index + h > cut                 # outcomes not complete at `cut`
    wrecked.loc[future_x, al.FEATURES] *= 50
    ycols = [c for c in wrecked.columns if c.startswith(("y_", "fwd_"))]
    wrecked.loc[future_y, ycols] = 7.0
    after = al.walk_forward(wrecked, CFG)
    pcols = [c for c in base.columns if c.startswith(("pred_", "bench_", "gate_", "w_"))]
    pd.testing.assert_frame_equal(base.loc[:cut, pcols], after.loc[:cut, pcols])


def test_training_rows_always_have_completed_outcomes():
    nl, ret = synth(260)
    ds = al.build_dataset(nl, ret, CFG)
    preds = al.walk_forward(ds, CFG)
    h = pd.Timedelta(weeks=CFG["horizon_weeks"])
    first = preds.index[0]
    usable = ds.dropna(subset=["y_Stocks"])
    assert (usable.index + h <= first).sum() >= CFG["min_train_weeks"]


# ------------------------------------------------------------ allocation rules
def test_allocation_is_long_only_fully_invested_and_bounded():
    big = {a: 1.0 for a in al.RISKY}
    sig = {a: 0.01 for a in al.RISKY}
    for sign in (+1, -1):
        w = al.allocate({a: sign * 1.0 for a in al.RISKY}, sig, {a: 1.0 for a in al.RISKY}, CFG)
        assert w.sum() == pytest.approx(1.0) and (w >= -1e-12).all()
        if sign < 0:
            for a in al.RISKY:
                assert w[a] >= CFG["neutral"][a] - CFG["max_tilt"] - 1e-12


def _preds_frame(real, pred, h_weeks=4):
    idx = pd.date_range("2020-01-03", periods=len(real), freq=f"{h_weeks}W-FRI")
    return pd.DataFrame({"real_Stocks": real, "pred_Stocks": pred, "bench_Stocks": 0.0}, index=idx)


def test_gate_stays_closed_for_a_positive_r2_that_is_not_significant():
    """The weakness seen on live data: a ~1% R-squared passed the old gate on noise."""
    cfg = {**CFG, "gate_min_obs": 12}
    for seed in range(500):
        rng = np.random.default_rng(seed)
        real = rng.normal(0, 1, 14)
        pred = 0.25 * (0.55 * real + 0.45 * rng.normal(0, 1, 14))
        df = _preds_frame(real, pred)
        r2 = 1 - ((real - pred) ** 2).sum() / (real ** 2).sum()
        if r2 > 0.0 and al.rank_ic_tstat(df["pred_Stocks"], df["real_Stocks"]) < cfg["gate_min_tstat"]:
            now = df.index[-1] + pd.Timedelta(weeks=4)
            assert al.skill_gate(df, "Stocks", now, cfg) == 0.0
            return
    pytest.fail("could not construct a positive-R2, insignificant case")


def test_gate_opens_when_skill_is_significant():
    rng = np.random.default_rng(0)
    real = rng.normal(0, 1, 40)
    pred = 0.6 * real + 0.2 * rng.normal(0, 1, 40)
    df = _preds_frame(real, pred)
    now = df.index[-1] + pd.Timedelta(weeks=4)
    assert al.rank_ic_tstat(df["pred_Stocks"], df["real_Stocks"]) > CFG["gate_min_tstat"]
    assert al.skill_gate(df, "Stocks", now, CFG) > 0.0


def test_closed_gate_returns_neutral_weights():
    w = al.allocate({"Stocks": 0.5, "Treasuries": -0.4, "Credit": 0.1},
                    {a: 0.02 for a in al.RISKY}, {a: 0.0 for a in al.RISKY}, CFG)
    pd.testing.assert_series_equal(w, pd.Series(CFG["neutral"])[al.ASSETS], check_names=False)


# ------------------------------------------------------------ null world and planted edge
def test_null_world_gate_stays_closed_and_no_edge():
    gates, excess = [], []
    for seed in range(6):
        nl, ret = synth(420, signal=0.0, seed=seed)
        ds = al.build_dataset(nl, ret, CFG)
        preds = al.walk_forward(ds, CFG)
        gates.append(preds["gate_Stocks"].mean())
        stats, _, _ = al.backtest(preds, CFG)
        excess.append(stats.loc["Allocator", "excess vs neutral"])
    assert np.mean(gates) < 0.25                      # the gate should mostly refuse to trade noise
    assert abs(np.mean(excess)) < 0.01                # and there is no free edge in a null world


def test_planted_edge_is_found_out_of_sample():
    nl, ret = synth(520, signal=3.0, seed=2)
    ds = al.build_dataset(nl, ret, CFG)
    preds = al.walk_forward(ds, CFG)
    d = al.diagnostics(preds)
    assert d.loc["Stocks", "OOS R2 vs mean"] > 0.0
    assert d.loc["Stocks", "IC (rank corr)"] > 0.1
    assert preds["gate_Stocks"].iloc[-1] > 0.0


def test_costs_reduce_net_returns():
    nl, ret = synth(520, signal=3.0, seed=2)
    preds = al.walk_forward(al.build_dataset(nl, ret, CFG), CFG)
    free, _, _ = al.backtest(preds, {**CFG, "cost_bps": 0.0})
    paid, _, _ = al.backtest(preds, {**CFG, "cost_bps": 50.0})
    assert paid.loc["Allocator", "ann. return"] < free.loc["Allocator", "ann. return"]


# ------------------------------------------------------------ scenarios
def test_scenario_direction_follows_the_fitted_relationship():
    nl, ret = synth(520, signal=3.0, seed=2)
    ds = al.build_dataset(nl, ret, CFG)
    preds = al.walk_forward(ds, CFG)
    fit = al.fit_final(ds, preds, CFG)
    up = pd.Series(np.linspace(nl.iloc[-1], nl.iloc[-1] * 1.03, 14))
    down = pd.Series(np.linspace(nl.iloc[-1], nl.iloc[-1] * 0.97, 14))
    r_up = al.simulate_path(nl, up, fit, CFG)
    r_dn = al.simulate_path(nl, down, fit, CFG)
    assert r_up["cum_excess"]["Stocks"] > r_dn["cum_excess"]["Stocks"]


def test_scenario_table_reports_effect_relative_to_hold():
    nl, ret = synth(520, signal=3.0, seed=2)
    ds = al.build_dataset(nl, ret, CFG)
    fit = al.fit_final(ds, al.walk_forward(ds, CFG), CFG)
    hold = pd.DataFrame({"net_liq": np.full(14, nl.iloc[-1])})
    up = pd.DataFrame({"net_liq": np.linspace(nl.iloc[-1], nl.iloc[-1] * 1.03, 14)})
    weekly = pd.DataFrame({"net_liq": nl})
    t = al.scenario_forecasts(weekly, {"hold": hold, "up": up}, fit, CFG)
    assert t.loc["hold", "Stocks liquidity effect %"] == pytest.approx(0.0)
    assert t.loc["up", "Stocks liquidity effect %"] > 0


def test_extrapolation_guard_clips_extreme_paths():
    nl, ret = synth(520, signal=3.0, seed=2)
    ds = al.build_dataset(nl, ret, CFG)
    fit = al.fit_final(ds, al.walk_forward(ds, CFG), CFG)
    crazy = pd.Series(np.linspace(nl.iloc[-1], nl.iloc[-1] * 3.0, 27))
    r = al.simulate_path(nl, crazy, fit, CFG)
    assert r["clipped_share"] > 0.5
    # a forecast from absurdly large inputs equals the forecast at the edge of the training range
    m = fit["models"]["Stocks"]
    far, flag = al.ridge_predict(m, np.array([[1000.0, 1000.0]]))
    edge, _ = al.ridge_predict(m, m["hi"][None, :])
    assert flag.all() and far[0] == pytest.approx(edge[0])
