"""Offline tests. No network needed."""
import numpy as np
import pandas as pd
import pytest

import fedliq


def make_weekly(n=200, start="2019-01-02"):
    idx = pd.date_range(start, periods=n, freq="W-WED")
    raw = {
        "assets": pd.Series(4000.0 + np.arange(n) * 10, index=idx),
        "tga": pd.Series(300.0 + np.arange(n) * 1, index=idx),
        "rrp": pd.Series(np.r_[np.zeros(n // 2), np.full(n - n // 2, 100.0)], index=idx),
    }
    return fedliq.build_weekly(raw)["weekly"]


def test_net_liquidity_formula():
    w = make_weekly()
    row = w.iloc[-1]
    assert row["net_liq"] == pytest.approx(row["assets"] - row["tga"] - row["rrp"])


def test_rrp_daily_aligned_to_wednesday_with_ffill():
    idx = pd.date_range("2024-01-03", periods=3, freq="W-WED")
    daily = pd.Series([5.0, 7.0], index=pd.to_datetime(["2024-01-02", "2024-01-09"]))  # nothing on the 10th/17th
    raw = {"assets": pd.Series([100.0] * 3, index=idx), "tga": pd.Series([10.0] * 3, index=idx), "rrp": daily}
    w = fedliq.build_weekly(raw)["weekly"]
    assert list(w["rrp"]) == [5.0, 7.0, 7.0]


def test_hold_scenario_changes_nothing():
    w = make_weekly()
    paths, table = fedliq.scenario_table(w, 13)
    assert table.loc["Baseline: hold today's levels", "change"] == pytest.approx(0.0)


def test_contributions_add_to_change():
    w = make_weekly()
    _, table = fedliq.scenario_table(w, 13, custom={"assets": -300, "tga": 100, "rrp": 20})
    parts = table[["from_assets", "from_tga", "from_rrp"]].sum(axis=1)
    np.testing.assert_allclose(parts, table["change"], atol=1e-9)


def test_custom_shock_sign_and_size():
    w = make_weekly()
    _, table = fedliq.scenario_table(w, 10, custom={"assets": -300, "tga": 100})
    # assets down 300 and TGA up 100 drains 400 from net liquidity
    assert table.loc["Custom shock", "change"] == pytest.approx(-400.0)


def test_floor_stops_rrp_going_negative():
    latest = pd.Series({"assets": 1000.0, "tga": 100.0, "rrp": 5.0})
    delta = fedliq.custom_path({"rrp": -500.0}, 4)
    out = fedliq.apply_path(latest, delta)
    assert (out["rrp"] >= 0).all() and out["rrp"].iloc[-1] == 0.0
    assert out["net_liq"].iloc[-1] == pytest.approx(900.0)


def test_episode_replay_uses_only_the_window_after_start():
    w = make_weekly()
    d = fedliq.episode_path(w, "2020-03-04", 13)
    assert len(d) == 14 and (d.iloc[0] == 0).all()
    # assets rise 10 per week in the fake data
    assert d["assets"].iloc[-1] == pytest.approx(130.0)


def test_episode_replay_errors_when_window_runs_off_the_end():
    w = make_weekly(n=40)
    with pytest.raises(ValueError):
        fedliq.episode_path(w, w.index[-3].strftime("%Y-%m-%d"), 13)
