"""Offline tests: pipeline quality gates, point-in-time handling, cache safety, inflation and output math."""
import json
import threading
from datetime import date

import numpy as np
import pandas as pd
import pytest

import feature_study as fs
import inflation as inf
import macro
import output_trend as out
import pipeline as pl

SPEC_M = pl.SeriesSpec("X", "monthly idx", "M", "index", 20, "t")
SPEC_D = pl.SeriesSpec("D", "daily", "D", "level", 1, "t", lo=0, hi=10)
SPEC_Q = pl.SeriesSpec("Q", "quarterly", "Q", "level", 30, "t")


def monthly(values, start="2020-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="MS"), dtype=float)


def growing_index(n=48, annual=0.03, start="2020-01-01"):
    return monthly(100 * (1 + annual) ** (np.arange(n) / 12), start)


# ------------------------------------------------------------ point in time
def test_monthly_observation_is_known_only_after_period_end_plus_lag():
    s = monthly([1, 2, 3])                                 # Jan, Feb, Mar 2020
    av = pl.available_dates(s.index, SPEC_M)
    assert av[0] == pd.Timestamp("2020-01-31") + pd.Timedelta(days=20)
    assert len(pl.point_in_time(s, SPEC_M, "2020-02-15")) == 0
    assert len(pl.point_in_time(s, SPEC_M, "2020-02-25")) == 1


def test_align_to_never_reveals_a_value_early():
    s = monthly([10, 20, 30])
    idx = pd.date_range("2020-01-01", "2020-05-31", freq="D")
    a = pl.align_to(s, SPEC_M, idx)
    assert a.loc[:"2020-02-19"].isna().all()               # Jan data not out until Feb 20
    assert a.loc["2020-02-20"] == 10 and a.loc["2020-03-21"] == 20


def test_changing_future_observations_cannot_change_past_aligned_values():
    s = monthly(np.arange(1, 25))
    idx = pd.date_range("2020-06-01", "2021-03-31", freq="W-FRI")
    base = pl.align_to(s, SPEC_M, idx)
    wrecked = s.copy()
    wrecked.iloc[15:] = 9999
    after = pl.align_to(wrecked, SPEC_M, idx)
    cutoff = pl.available_dates(s.index, SPEC_M)[15]
    pd.testing.assert_series_equal(base[base.index < cutoff], after[after.index < cutoff])


# ------------------------------------------------------------ quality gates
def test_stale_series_is_flagged_and_blocking():
    s = pd.Series(1.0, index=pd.date_range("2026-01-01", periods=5, freq="D"))
    issues = pl.quality_issues(s, SPEC_D, date(2026, 3, 1))
    assert pl.worst_status(issues) == "STALE" and "STALE" in pl.BLOCKING


def test_fresh_series_is_ok():
    s = pd.Series(1.0, index=pd.date_range("2026-02-20", "2026-03-01", freq="D"))
    assert pl.quality_issues(s, SPEC_D, date(2026, 3, 2)) == []


def test_out_of_range_latest_value_is_flagged():
    s = pd.Series(1.0, index=pd.date_range("2026-02-20", "2026-03-01", freq="D"))
    s.iloc[-1] = 50.0
    assert pl.worst_status(pl.quality_issues(s, SPEC_D, date(2026, 3, 2))) == "RANGE"


def test_wild_latest_print_is_flagged_as_outlier():
    rng = np.random.default_rng(0)
    s = monthly(100 * np.cumprod(1 + rng.normal(0.002, 0.001, 80)), "2020-01-01")
    s.iloc[-1] = s.iloc[-2] * 1.2
    issues = pl.quality_issues(s, SPEC_M, date(2026, 8, 1))
    assert any(i.startswith("OUTLIER") for i in issues)


def test_missing_month_is_reported_as_a_gap():
    s = growing_index(30).drop(pd.Timestamp("2021-06-01"))
    assert any(i.startswith("GAP") for i in pl.quality_issues(s, SPEC_M, date(2022, 7, 1)))


def test_empty_series_fails():
    assert pl.worst_status(pl.quality_issues(pd.Series(dtype=float), SPEC_M, date(2026, 1, 1))) == "FAILED"


# ------------------------------------------------------------ calendar-aware growth
def test_yoy_uses_calendar_months_across_a_missing_month():
    idx = growing_index(48, annual=0.03)
    with_gap = idx.drop(pd.Timestamp("2022-06-01"))
    y = inf.yoy(with_gap)
    assert y.loc["2022-12-01"] == pytest.approx(3.0, abs=1e-6)       # correct, spans 12 calendar months
    assert np.isnan(y.loc["2023-06-01"])                             # base month never published: NaN, not a 13-month number
    positional = (with_gap / with_gap.shift(12) - 1) * 100
    assert positional.loc["2022-12-01"] > 3.2                        # the old method stretched to 13 months


def test_growth_rates_on_a_clean_index():
    idx = growing_index(36, annual=0.03)
    assert inf.yoy(idx).iloc[-1] == pytest.approx(3.0, abs=1e-6)
    assert inf.ann_growth(idx, 3).iloc[-1] == pytest.approx(3.0, abs=1e-6)
    assert inf.ann_growth(idx, 1).iloc[-1] == pytest.approx(3.0, abs=1e-6)


def test_sticky_cpi_compounds_monthly_percent_changes():
    pct = monthly([0.25] * 24)
    assert inf.compound_from_monthly_pct(pct, 12).iloc[-1] == pytest.approx((1.0025 ** 12 - 1) * 100, abs=1e-9)
    assert inf.compound_from_monthly_pct(pct, 3).iloc[-1] == pytest.approx((1.0025 ** 12 - 1) * 100, abs=1e-9)


def test_direction_labels():
    assert inf.direction(4.0, 3.0) == "accelerating"
    assert inf.direction(2.0, 3.0) == "decelerating"
    assert inf.direction(3.1, 3.0) == "steady"
    assert inf.direction(float("nan"), 3.0) == "n/a"


def test_inflation_table_and_pulse_on_synthetic_data():
    s = {"CPIAUCSL": growing_index(36, 0.04), "CPILFESL": growing_index(36, 0.03),
         "PCEPILFE": growing_index(36, 0.025), "MEDCPIM158SFRBCLE": monthly([3.0] * 36),
         "STICKCPIM157SFRBATL": monthly([0.25] * 36),
         "T5YIFR": pd.Series([2.3] * 300, index=pd.bdate_range("2025-01-01", periods=300))}
    t = inf.inflation_table(s)
    assert t.loc["Headline CPI", "y/y %"] == pytest.approx(4.0, abs=1e-6)
    assert t.loc["Core CPI", "direction"] == "steady"
    assert t.loc["Median CPI", "y/y %"] == pytest.approx(3.0)
    p = inf.inflation_pulse(s)
    assert p["core_cpi_3m_ann"] == pytest.approx(3.0, abs=1e-6) and p["breakeven_5y5y"] == pytest.approx(2.3)
    assert np.isnan(p["mich_1y"]) and np.isnan(p["gas_yoy_pct"])    # missing series never raise


def test_pulse_is_nan_for_a_missing_series():
    assert all(np.isnan(v) for v in inf.inflation_pulse({}).values())
    assert all(np.isnan(v) for v in out.output_pulse({}).values())


# ------------------------------------------------------------ output trends
def test_trailing_trend_is_exact_on_pure_growth():
    g = growing_index(80, 0.05)
    tr = out.trailing_loglinear(g, 40)
    np.testing.assert_allclose(tr.dropna().to_numpy(), g.loc[tr.dropna().index].to_numpy(), rtol=1e-9)


def test_trailing_trend_does_not_move_when_the_future_changes():
    g = growing_index(100, 0.03)
    base = out.trailing_loglinear(g, 40)
    wrecked = g.copy()
    wrecked.iloc[80:] *= 3
    after = out.trailing_loglinear(wrecked, 40)
    pd.testing.assert_series_equal(base.iloc[:80], after.iloc[:80])


def test_gdp_gap_against_potential():
    q = pd.date_range("2018-01-01", periods=30, freq="QS")
    gdp = pd.Series(20000 * 1.005 ** np.arange(30), index=q)
    pot = gdp * 1.02
    blk = out.gdp_block({"GDPC1": gdp, "GDPPOT": pot})
    assert blk["Gap to potential %"].iloc[-1] == pytest.approx((1 / 1.02 - 1) * 100)


def test_sahm_indicator_hits_the_rule_when_unemployment_jumps():
    u = monthly([3.5] * 14 + [3.7, 4.0, 4.3, 4.5])
    sahm = out.activity_block({"UNRATE": u})["Sahm indicator"].dropna()
    assert sahm.iloc[-1] >= 0.5
    flat = out.activity_block({"UNRATE": monthly([4.0] * 20)})["Sahm indicator"].dropna()
    assert flat.iloc[-1] == pytest.approx(0.0)


def test_sahm_survives_one_missing_month():
    u = monthly([3.5] * 14 + [3.7, 4.0, 4.3, 4.5]).drop(pd.Timestamp("2021-04-01"))
    sahm = out.activity_block({"UNRATE": u})["Sahm indicator"].dropna()
    assert len(sahm) and sahm.iloc[-1] >= 0.4


# ------------------------------------------------------------ cache and pipeline
def test_concurrent_cache_writes_keep_the_manifest_valid(tmp_path):
    cache = pl.Cache(tmp_path)
    s = monthly([1, 2, 3])

    def work(i):
        cache.write(f"S{i}", s, {"rows": 3, "i": i})

    threads = [threading.Thread(target=work, args=(i,)) for i in range(40)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert len(manifest) == 40


def test_corrupt_manifest_is_tolerated(tmp_path):
    cache = pl.Cache(tmp_path)
    cache.write("A", monthly([1, 2, 3]), {"rows": 3})
    (tmp_path / "manifest.json").write_text("{not json")
    s, meta = cache.read("A")
    assert len(s) == 3 and meta == {}
    cache.write("B", monthly([1, 2, 3]), {"rows": 3})            # and it heals on the next write
    assert "B" in json.loads((tmp_path / "manifest.json").read_text())


class FakeSource:
    mode = "fake"

    def __init__(self, data, failing=()):
        self.data, self.failing = data, set(failing)

    def series(self, sid, start=None):
        if sid in self.failing:
            raise RuntimeError("network down")
        return self.data[sid]


def test_pipeline_falls_back_to_cache_and_labels_it(tmp_path):
    specs = [SPEC_D, pl.SeriesSpec("E", "other daily", "D", "level", 1, "t")]
    today = date(2026, 3, 2)
    idx = pd.date_range("2026-02-20", "2026-03-01", freq="D")
    data = {"D": pd.Series(1.0, index=idx), "E": pd.Series(2.0, index=idx)}
    first = pl.Pipeline(FakeSource(data), tmp_path, today, specs).run()
    assert first.quality["status"].tolist() == ["OK", "OK"]
    second = pl.Pipeline(FakeSource(data, failing=["E"]), tmp_path, today, specs).run()
    row = second.quality.set_index("series").loc["E"]
    assert row["status"] == "CACHED" and row["usable"] and "E" in second.series


def test_pipeline_marks_a_failed_fetch_without_cache_as_unusable(tmp_path):
    today = date(2026, 3, 2)
    data = {"D": pd.Series(1.0, index=pd.date_range("2026-02-20", "2026-03-01", freq="D"))}
    res = pl.Pipeline(FakeSource(data, failing=["D"]), tmp_path, today, [SPEC_D]).run()
    row = res.quality.iloc[0]
    assert row["status"] == "FAILED" and not row["usable"] and res.usable() == {}


def test_stale_cached_series_is_unusable(tmp_path):
    old = pd.Series(1.0, index=pd.date_range("2025-01-01", "2025-01-10", freq="D"))
    pl.Pipeline(FakeSource({"D": old}), tmp_path, date(2025, 1, 12), [SPEC_D]).run()
    res = pl.Pipeline(FakeSource({}, failing=["D"]), tmp_path, date(2026, 3, 2), [SPEC_D]).run()
    row = res.quality.iloc[0]
    assert "STALE" in row["issues"] and "CACHED" in row["issues"] and not row["usable"]


def test_metrics_leave_out_unusable_series(tmp_path):
    cpi = growing_index(36, 0.03)
    data = {"CPIAUCSL": cpi, "CPILFESL": cpi}
    specs = [pl.SPEC_BY_ID["CPIAUCSL"], pl.SPEC_BY_ID["CPILFESL"]]
    res = pl.Pipeline(FakeSource(data, failing=["CPILFESL"]), tmp_path, date(2022, 12, 20), specs, use_cache=False).run()
    m = macro.metrics(res.usable())
    assert m["cpi_yoy"] == pytest.approx(3.0, abs=1e-6) and np.isnan(m["core_cpi_yoy"])


# ------------------------------------------------------------ feature study timing
def test_macro_features_use_only_published_data():
    cpi = growing_index(60, 0.03)
    specs = {"CPILFESL": pl.SPEC_BY_ID["CPILFESL"]}
    dates = pd.date_range("2022-01-07", "2024-06-28", freq="W-FRI")
    base = fs.macro_features({"CPILFESL": cpi}, specs, dates)["core_cpi_3m_ann"]
    wrecked = cpi.copy()
    wrecked.iloc[40:] *= 5
    after = fs.macro_features({"CPILFESL": wrecked}, specs, dates)["core_cpi_3m_ann"]
    first_hit = pl.available_dates(cpi.index, specs["CPILFESL"])[40]
    early = base.index < first_hit
    pd.testing.assert_series_equal(base[early], after[early])
