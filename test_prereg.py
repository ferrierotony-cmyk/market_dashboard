"""Offline tests for the pre-registration lock and the v2 implementation. Synthetic data only.

These run BEFORE the real data is touched, so implementation bugs are caught without ever
seeing a result that could tempt a change to the design.
"""
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import allocator as al
import prereg
import prereg_backtest as pb
import regime_backtest as rb

SPEC_PATH = Path(pb.SPEC_PATH)
SPEC = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
SMALL = {**SPEC["adaptive_thresholds"], "window_weeks": 30, "min_weeks": 20}


def fridays(n, start="2012-01-06"):
    return pd.date_range(start, periods=n, freq="W-FRI")


# ------------------------------------------------------------ lock
def test_shipped_spec_matches_its_lock():
    assert prereg.verify(SPEC_PATH)["sha256"] == prereg.spec_hash(SPEC_PATH)


def test_editing_a_locked_spec_is_detected(tmp_path):
    p = tmp_path / "s.json"
    shutil.copy(SPEC_PATH, p)
    prereg.lock(p)
    prereg.verify(p)
    edited = json.loads(p.read_text())
    edited["max_dev"] = 0.25
    p.write_text(json.dumps(edited))
    with pytest.raises(RuntimeError, match="changed since it was locked"):
        prereg.verify(p)


def test_reformatting_does_not_break_the_lock_but_a_missing_lock_does(tmp_path):
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"a": 1, "b": [1, 2]}))
    with pytest.raises(RuntimeError, match="lock the spec"):
        prereg.verify(p)
    prereg.lock(p)
    p.write_text(json.dumps({"b": [1, 2], "a": 1}, indent=4))       # same content, different layout
    prereg.verify(p)


def test_a_lock_is_never_overwritten(tmp_path):
    p = tmp_path / "s.json"
    p.write_text("{}")
    prereg.lock(p)
    with pytest.raises(FileExistsError):
        prereg.lock(p)


def test_spec_tilts_move_weight_without_adding_any():
    for t in (SPEC["sizing"]["tier_2"], SPEC["sizing"]["tier_3"], SPEC["overlay"]["tilt"]):
        assert abs(sum(t.values())) < 1e-12 and set(t) == set(al.ASSETS)
    assert abs(sum(SPEC["neutral"].values()) - 1) < 1e-12


# ------------------------------------------------------------ adaptive thresholds and node paths
def test_threshold_at_a_date_never_uses_that_dates_own_value():
    x = pd.Series(np.random.default_rng(0).normal(0, 1, 80), index=fridays(80))
    base = pb.adaptive_thresholds(x, "high", SMALL)
    changed = x.copy()
    changed.iloc[60] = 1e6
    after = pb.adaptive_thresholds(changed, "high", SMALL)
    assert base.iloc[60].equals(after.iloc[60])             # current value cannot move its own threshold
    assert not base.iloc[61].equals(after.iloc[61])         # but it does enter later windows


def test_states_ignore_the_future():
    rng = np.random.default_rng(1)
    x = pd.Series(rng.normal(0, 1, 120), index=fridays(120))
    base = pb.adaptive_state_path(x, "high", SMALL)
    wrecked = x.copy()
    wrecked.iloc[80:] = 50.0
    after = pb.adaptive_state_path(wrecked, "high", SMALL)
    pd.testing.assert_series_equal(base.iloc[:80], after.iloc[:80])


def test_nodes_stay_off_during_warm_up():
    x = pd.Series(np.r_[np.full(10, 0.0), np.full(10, 100.0), np.zeros(40)], index=fridays(60))
    st = pb.adaptive_state_path(x, "high", SMALL)
    assert not st.iloc[:20].any()                           # fewer than min_weeks of history


def test_high_node_triggers_on_a_spike_and_clears_with_hysteresis():
    rng = np.random.default_rng(2)
    base = rng.normal(0, 1, 60)
    x = pd.Series(np.r_[base, [6.0, 6.0, 0.9, 0.0, 0.0]], index=fridays(65))
    st = pb.adaptive_state_path(x, "high", SMALL)
    assert st.iloc[60] and st.iloc[61]                      # far above the trailing 90th percentile
    assert not st.iloc[63] and not st.iloc[64]              # back to normal, so cleared


def test_low_side_node_fires_on_a_collapse():
    rng = np.random.default_rng(3)
    x = pd.Series(np.r_[rng.normal(0, 1, 60), [-6.0, -6.0]], index=fridays(62))
    assert pb.adaptive_state_path(x, "low", SMALL).iloc[60]


# ------------------------------------------------------------ sizing
def hist_with(n_fast_on: int, overlay_on: bool, n=70):
    """Metric history where exactly `n_fast_on` of the four fast metrics spike at the end."""
    rng = np.random.default_rng(5)
    idx = fridays(n)
    cols = {"net_liq_4w_pct": rng.normal(0, 1, n), "vix": rng.normal(0, 1, n),
            "baa_4w_chg": rng.normal(0, 1, n), "nfci": rng.normal(0, 1, n), "core_pce_3m_ann": np.full(n, 2.0)}
    sign = {"net_liq_4w_pct": -8.0, "vix": 8.0, "baa_4w_chg": 8.0, "nfci": 8.0}
    for k in list(sign)[:n_fast_on]:
        cols[k][-1] = sign[k]
    if overlay_on:
        cols["core_pce_3m_ann"][-3:] = 4.0
    return pd.DataFrame(cols, index=idx)


def tweak(spec):
    s = json.loads(json.dumps(spec))
    s["adaptive_thresholds"] = SMALL
    return s


@pytest.mark.parametrize("k,expected", [(0, None), (1, None), (2, "tier_2"), (3, "tier_3"), (4, "tier_3")])
def test_count_based_sizing(k, expected):
    spec = tweak(SPEC)
    targets, states = pb.build_targets(spec, hist_with(k, False))
    last = targets.iloc[-1]
    neutral = pd.Series(spec["neutral"])[al.ASSETS]
    if expected is None:
        pd.testing.assert_series_equal(last, neutral, check_names=False)
    else:
        tilt = pd.Series(spec["sizing"][expected]).reindex(al.ASSETS)
        pd.testing.assert_series_equal(last, (neutral + tilt) / (neutral + tilt).sum(), check_names=False)
    assert states["n_fast_on"].iloc[-1] == k


def test_overlay_adds_to_the_tier_and_weights_stay_valid():
    spec = tweak(SPEC)
    targets, states = pb.build_targets(spec, hist_with(3, True))
    last = targets.iloc[-1]
    assert states["inflation_hot"].iloc[-1]
    assert last.sum() == pytest.approx(1.0) and (last >= 0).all()
    neutral = pd.Series(spec["neutral"])[al.ASSETS]
    assert last["Treasuries"] == pytest.approx(neutral["Treasuries"] + 0.10 - 0.05)
    assert last["Stocks"] >= neutral["Stocks"] - spec["max_dev"] - 1e-9


def test_a_single_node_alone_changes_nothing():
    targets, _ = pb.build_targets(tweak(SPEC), hist_with(1, False))
    neutral = pd.Series(SPEC["neutral"])[al.ASSETS]
    pd.testing.assert_series_equal(targets.iloc[-1], neutral, check_names=False)


# ------------------------------------------------------------ window run
def synth_daily(n_days=1500, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2012-01-02", periods=n_days)
    return pd.DataFrame(rng.normal(0.0003, 0.006, (n_days, 4)), index=idx, columns=al.ASSETS)


def test_neutral_targets_reproduce_the_rebalanced_neutral_benchmark():
    daily = synth_daily()
    dates = pd.date_range("2012-01-06", daily.index[-1], freq="W-FRI")
    neutral = pd.Series(SPEC["neutral"])[al.ASSETS]
    targets = pd.DataFrame([neutral] * len(dates), index=dates)
    res = pb.run_window(SPEC, targets, daily, dates, "2012-03-02", "latest")
    r = res["returns"]
    pd.testing.assert_series_equal(r[pb.V2], r["Neutral, rebalanced weekly"], check_names=False)
    pd.testing.assert_series_equal(r[pb.V2], r["Static mix, same average weights"], check_names=False)
    assert res["turnover"]["Buy & hold (neutral)"].sum() == 0.0


def test_window_end_excludes_weeks_that_run_past_it():
    daily = synth_daily()
    dates = pd.date_range("2012-01-06", daily.index[-1], freq="W-FRI")
    neutral = pd.Series(SPEC["neutral"])[al.ASSETS]
    targets = pd.DataFrame([neutral] * len(dates), index=dates)
    res = pb.run_window(SPEC, targets, daily, dates, "2012-03-02", "2013-06-30")
    assert res["returns"].index[-1] + pd.Timedelta(days=7) <= pd.Timestamp("2013-06-30")


# ------------------------------------------------------------ mechanical judgement
def fake_stats(monkeypatch, c1_low, dd_v2, dd_bh, sh_v2, sh_bh, conf_excess):
    calls = {"n": 0}

    def summarize(res, cash):
        calls["n"] += 1
        if res is fake_stats.dev:
            return pd.DataFrame({"max drawdown": {pb.V2: dd_v2, "Buy & hold (neutral)": dd_bh},
                                 "Sharpe (vs cash)": {pb.V2: sh_v2, "Buy & hold (neutral)": sh_bh}})
        return pd.DataFrame({"excess vs matched static mix": {pb.V2: conf_excess}})

    monkeypatch.setattr(rb, "summarize", summarize)
    monkeypatch.setattr(rb, "excess_tests", lambda res: pd.DataFrame(
        {"vs": ["Static mix, same average weights"], "90% CI low": [c1_low * 100]}))


fake_stats.dev = {"cash": None}
CONF = {"cash": None}


@pytest.mark.parametrize("kw,verdict,failed", [
    (dict(c1_low=0.004, dd_v2=-0.10, dd_bh=-0.15, sh_v2=0.6, sh_bh=0.5, conf_excess=0.0), "PASS", []),
    (dict(c1_low=-0.001, dd_v2=-0.10, dd_bh=-0.15, sh_v2=0.6, sh_bh=0.5, conf_excess=0.0), "FAIL", ["C1"]),
    (dict(c1_low=0.004, dd_v2=-0.14, dd_bh=-0.15, sh_v2=0.6, sh_bh=0.5, conf_excess=0.0), "FAIL", ["C2"]),
    (dict(c1_low=0.004, dd_v2=-0.10, dd_bh=-0.15, sh_v2=0.4, sh_bh=0.5, conf_excess=0.0), "FAIL", ["C3"]),
    (dict(c1_low=0.004, dd_v2=-0.10, dd_bh=-0.15, sh_v2=0.6, sh_bh=0.5, conf_excess=-0.006), "FAIL", ["C4"]),
    (dict(c1_low=-1.0, dd_v2=-0.20, dd_bh=-0.15, sh_v2=0.1, sh_bh=0.5, conf_excess=-0.05), "FAIL", ["C1", "C2", "C3", "C4"]),
])
def test_verdict_follows_the_registered_criteria(monkeypatch, kw, verdict, failed):
    fake_stats(monkeypatch, **kw)
    out = pb.judge(fake_stats.dev, CONF)
    assert out["verdict"] == verdict
    assert [k for k in ("C1", "C2", "C3", "C4") if not out[k]["pass"]] == failed


def test_runner_refuses_to_run_when_the_spec_has_changed(tmp_path, monkeypatch, capsys):
    p = tmp_path / "prereg_v2.json"
    shutil.copy(SPEC_PATH, p)
    prereg.lock(p)
    edited = json.loads(p.read_text())
    edited["cost_bps"] = 0.0
    p.write_text(json.dumps(edited))
    monkeypatch.setattr(pb, "SPEC_PATH", p)
    assert pb.main() == 1 and "REFUSING TO RUN" in capsys.readouterr().out
