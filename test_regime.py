"""Offline tests: regime target weights, shift detection, dispatch, allocation log, and the backtest engine."""
import json
import sqlite3
import urllib.request
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

import alerts
import allocator as al
import dispatch
import macro
import regime
import regime_backtest as rb
import tracker

NOW = datetime(2026, 11, 9, 22, 0, tzinfo=timezone.utc)
NEUTRAL = pd.Series(al.CONFIG["neutral"])[al.ASSETS]


def rule(id_, metric="vix", op=">", value=30, clear=27, tilt=None, pit="ok"):
    return {"id": id_, "metric": metric, "op": op, "value": value, "clear": clear, "message": id_ + " fired",
            "tilt": tilt if tilt is not None else {"Stocks": -0.05, "Treasuries": 0.0, "Credit": 0.0, "Cash": 0.05}, "pit": pit}


RULES = [rule("a"), rule("b", tilt={"Stocks": 0.0, "Treasuries": -0.04, "Credit": 0.0, "Cash": 0.04}),
         rule("c", tilt={"Stocks": -0.08, "Treasuries": 0.07, "Credit": -0.03, "Cash": 0.04})]


# ------------------------------------------------------------ target weights
def test_no_triggered_nodes_means_neutral_weights():
    pd.testing.assert_series_equal(regime.target_weights([], RULES), NEUTRAL, check_names=False)


def test_tilts_add_and_weights_stay_fully_invested():
    w = regime.target_weights(["a", "b"], RULES)
    assert w["Stocks"] == pytest.approx(0.45) and w["Treasuries"] == pytest.approx(0.26)
    assert w["Cash"] == pytest.approx(0.19) and w.sum() == pytest.approx(1.0)


def test_deviation_cap_and_long_only_hold_under_a_pile_up_of_nodes():
    many = [rule(f"n{i}", tilt={"Stocks": -0.08, "Treasuries": 0.0, "Credit": -0.03, "Cash": 0.11}) for i in range(10)]
    w = regime.target_weights([r["id"] for r in many], many, max_dev=0.20)
    assert (w >= 0).all() and w.sum() == pytest.approx(1.0)
    assert w["Stocks"] >= NEUTRAL["Stocks"] - 0.20 - 1e-9 and w["Credit"] >= 0.0


def test_shipped_rules_have_zero_sum_tilts_and_a_pit_flag():
    cfg = alerts.load_rules()
    tilted = [r for r in cfg["rules"] if r.get("tilt")]
    assert len(tilted) >= 15
    assert all(abs(sum(r["tilt"].values())) < 1e-9 for r in tilted)
    assert all(r.get("pit") in ("ok", "caveat", "exclude") for r in tilted)


def test_a_tilt_that_adds_weight_is_rejected(tmp_path):
    bad = {"rules": [{"id": "x", "metric": "vix", "op": ">", "value": 1, "message": "m",
                      "tilt": {"Stocks": 0.05, "Cash": 0.0}}]}
    p = tmp_path / "r.json"
    p.write_text(json.dumps(bad))
    with pytest.raises(ValueError):
        alerts.load_rules(p)


def test_triggered_nodes_reads_state():
    state = {"a": {"triggered": True}, "b": {"triggered": False}, "c": {"triggered": True}, "regime:last": {}}
    assert regime.triggered_nodes(state, RULES) == ["a", "c"]


# ------------------------------------------------------------ shift detection and dispatch
def make_log(tmp_path, sheet=None):
    return tracker.AllocationLog(tmp_path / "a.db", tmp_path / "a.csv", sheet)


def test_first_sight_is_a_logged_baseline_and_never_dispatched(tmp_path):
    sent = []
    info, st = regime.process_regime(RULES, {"a": {"triggered": True}}, {"vix": 31}, {"regime": {"dispatch": True}},
                                     NOW, log=make_log(tmp_path), send=lambda *a: sent.append(a))
    assert info["kind"] == "baseline" and sent == [] and "regime:last" in st
    assert len(make_log(tmp_path).recent()) == 1


def test_shift_is_logged_and_dispatched_only_when_enabled(tmp_path):
    base = {"a": {"triggered": False}, "c": {"triggered": False}}
    log = make_log(tmp_path)
    _, st = regime.process_regime(RULES, base, {}, {}, NOW, log=log)
    moved = {**st, "c": {"triggered": True}}
    sent = []
    send = lambda payload, text: sent.append((payload, text)) or {"sent": True, "host": "h", "detail": "ok"}  # noqa: E731
    off, _ = regime.process_regime(RULES, moved, {}, {"regime": {"dispatch": False}}, NOW, log=log, send=send)
    assert off["kind"] == "shift" and sent == [] and off["dispatched"] is None
    on, st2 = regime.process_regime(RULES, moved, {}, {"regime": {"dispatch": True}}, NOW, log=log, send=send)
    assert len(sent) == 1 and on["dispatched"]["sent"]
    payload = sent[0][0]
    assert payload["targets"]["Stocks"] == pytest.approx(0.42) and payload["trades"]["Stocks"] == pytest.approx(-0.08)
    assert "not investment advice" in payload["note"]
    again, _ = regime.process_regime(RULES, st2, {}, {"regime": {"dispatch": True}}, NOW, log=log, send=send)
    assert again["kind"] == "none"                       # nothing new to say after the target was published


def test_small_moves_below_min_change_are_not_shifts(tmp_path):
    log = make_log(tmp_path)
    tiny = [rule("t", tilt={"Stocks": -0.01, "Treasuries": 0.0, "Credit": 0.0, "Cash": 0.01})]
    _, st = regime.process_regime(tiny, {"t": {"triggered": False}}, {}, {}, NOW, log=log)
    info, _ = regime.process_regime(tiny, {**st, "t": {"triggered": True}}, {}, {}, NOW, log=log)
    assert info["kind"] == "none"


def test_dry_run_writes_nothing(tmp_path):
    log = make_log(tmp_path)
    info, st = regime.process_regime(RULES, {"a": {"triggered": True}}, {}, {}, NOW, dry_run=True, log=log)
    assert info["kind"] == "baseline" and "regime:last" not in st and log.recent() == []


def test_payload_text_names_trades_nodes_and_disclaimer():
    p = regime.build_payload("shift", regime.target_weights(["a"], RULES), dict(NEUTRAL), ["a"], {"vix": 31.0}, RULES, NOW)
    t = regime.payload_text(p)
    assert "Stocks 45.0% (-5.0 pts)" in t and "a" in t and "not investment advice" in t


# ------------------------------------------------------------ webhook
class Resp:
    def __init__(self, status=200):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_no_url_means_no_network(monkeypatch):
    monkeypatch.delenv("ALERT_WEBHOOK_URL", raising=False)
    res = dispatch.send_payload({"x": 1}, "t", opener=lambda *a, **k: pytest.fail("network call"))
    assert res["sent"] is False and "not set" in res["detail"]


@pytest.mark.parametrize("url,ok", [("https://hooks.example.com/x", True), ("http://example.com/x", False),
                                    ("http://localhost:8080/x", True), ("ftp://x/y", False), ("nonsense", False)])
def test_url_validation(url, ok):
    assert (dispatch.validate_url(url) is None) is ok


@pytest.mark.parametrize("fmt,key", [("json", "data"), ("slack", "text"), ("discord", "content")])
def test_body_formats(fmt, key):
    req = dispatch.build_request("https://h/x", {"targets": {"Stocks": 0.4}}, "summary", fmt)
    body = json.loads(req.data)
    assert key in body and (fmt != "json" or body["text"] == "summary")
    assert fmt != "slack" or set(body) == {"text"}


def test_ntfy_body_is_plain_text():
    req = dispatch.build_request("https://h/x", {}, "summary text", "ntfy")
    assert req.data == b"summary text" and req.get_header("Title")


def test_retries_then_succeeds_and_reports_host_not_url():
    calls = []

    def opener(req, timeout):
        calls.append(1)
        if len(calls) < 3:
            raise OSError("boom")
        return Resp(200)

    res = dispatch.send_payload({}, "t", url="https://secret.example.com/abc123", opener=opener, sleep=lambda s: None)
    assert res["sent"] and len(calls) == 3 and res["host"] == "secret.example.com"


def test_failure_never_leaks_the_url():
    def opener(req, timeout):
        raise OSError("cannot reach https://secret.example.com/abc123")

    res = dispatch.send_payload({}, "t", url="https://secret.example.com/abc123", opener=opener, sleep=lambda s: None)
    assert not res["sent"] and "abc123" not in res["detail"]


# ------------------------------------------------------------ allocation log and sheet
class FakeSheet:
    def __init__(self, fail=False):
        self.rows, self.fail = [], fail

    def append(self, rows):
        if self.fail:
            raise ConnectionError("sheet down")
        self.rows += rows


TARGET = {"Stocks": 0.45, "Treasuries": 0.28, "Credit": 0.09, "Cash": 0.18}
PREV = dict(NEUTRAL)


def test_record_writes_database_and_csv_with_changes(tmp_path):
    log = make_log(tmp_path)
    rid = log.record("shift", TARGET, PREV, ["a", "b"], note="n", now=NOW)
    row = log.row(rid)
    assert row["weights"] == TARGET and row["changes"]["Stocks"] == pytest.approx(-0.05) and not row["synced"]
    assert (tmp_path / "a.csv").read_text().count("\n") == 2          # header + one row
    assert sqlite3.connect(tmp_path / "a.db").execute("select count(*) from allocations").fetchone()[0] == 1


def test_sheet_sync_is_idempotent_and_marks_rows(tmp_path):
    sheet = FakeSheet()
    log = make_log(tmp_path, sheet)
    log.record("baseline", TARGET, None, [], sync=True)
    log.record("shift", TARGET, PREV, ["a"], sync=True)
    assert len(sheet.rows) == 2 and log.unsynced() == []
    assert log.sync_sheet() == 0 and len(sheet.rows) == 2             # nothing new, nothing duplicated


def test_failed_sheet_sync_keeps_rows_local_then_retries_without_duplicates(tmp_path):
    sheet = FakeSheet(fail=True)
    log = make_log(tmp_path, sheet)
    log.record("shift", TARGET, PREV, ["a"], sync=True)              # must not raise
    assert len(log.unsynced()) == 1 and sheet.rows == []
    sheet.fail = False
    assert log.sync_sheet() == 1 and len(sheet.rows) == 1 and log.unsynced() == []


def test_sheet_from_env_needs_both_settings_and_creates_the_tab():
    assert tracker.SheetSink.from_env(env={}) is None
    assert tracker.SheetSink.from_env(env={"GOOGLE_SHEET_ID": "x"}) is None

    class WS:
        pass

    class Book:
        def __init__(self):
            self.added = None

        def worksheet(self, tab):
            raise KeyError(tab)

        def add_worksheet(self, title, rows, cols):
            self.added = title
            return WS()

    book = Book()

    class FakeGspread:
        @staticmethod
        def service_account(filename):
            assert filename == "/k.json"
            return type("C", (), {"open_by_key": staticmethod(lambda sid: book)})()

    sink = tracker.SheetSink.from_env(env={"GOOGLE_SERVICE_ACCOUNT_JSON": "/k.json", "GOOGLE_SHEET_ID": "id"},
                                      gspread_module=FakeGspread)
    assert isinstance(sink.ws, WS) and book.added == "Allocations"


def test_sheet_header_written_once():
    class WS:
        def __init__(self):
            self.values = []

        def row_values(self, n):
            return self.values[0] if self.values else []

        def append_rows(self, rows, value_input_option=None):
            self.values += rows

    ws = WS()
    s = tracker.SheetSink(ws)
    s.append([["r1"]])
    s.append([["r2"]])
    assert ws.values[0] == tracker.SHEET_HEADER and ws.values.count(tracker.SHEET_HEADER) == 1 and len(ws.values) == 3


# ------------------------------------------------------------ backtest engine
def fridays(n=120, start="2018-01-05"):
    return pd.date_range(start, periods=n, freq="W-FRI")


def test_known_on_never_reveals_a_value_before_its_release():
    s = pd.Series([1.0, 2.0, 3.0], index=pd.to_datetime(["2020-01-01", "2020-02-01", "2020-03-01"]))
    rel = s.index + pd.Timedelta(days=20)
    dates = pd.date_range("2020-01-10", "2020-04-30", freq="W-FRI")
    k = rb.known_on(s, rel, dates)
    assert k.loc[:"2020-01-17"].isna().all() and k.loc["2020-01-24"] == 1.0 and k.loc["2020-02-21"] == 2.0


def test_change_over_days_uses_the_value_a_month_earlier():
    s = pd.Series(np.arange(100.0), index=pd.date_range("2020-01-01", periods=100, freq="D"))
    c = rb.change_over_days(s, 28)
    assert c.iloc[50] == pytest.approx(28.0) and np.isnan(c.iloc[10])


def rets_frame(n=60, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame(rng.normal(0.002, 0.01, (n, 4)), index=fridays(n), columns=al.ASSETS)


def test_buy_and_hold_never_trades_and_rebalancing_does():
    r = rets_frame()
    w = pd.DataFrame([NEUTRAL] * len(r), index=r.index)
    bh = rb.simulate(w, r, 5.0, rebalance=False)
    rebal = rb.simulate(w, r, 5.0)
    assert bh["turnover"].sum() == 0.0 and rebal["turnover"].iloc[1:].gt(0).all() and rebal["turnover"].iloc[0] == 0.0


def test_costs_lower_net_returns():
    r = rets_frame()
    w = pd.DataFrame([NEUTRAL] * len(r), index=r.index)
    assert rb.simulate(w, r, 50.0)["net"].sum() < rb.simulate(w, r, 0.0)["net"].sum()


def test_buy_and_hold_matches_direct_wealth_calculation():
    r = rets_frame()
    w = pd.DataFrame([NEUTRAL] * len(r), index=r.index)
    net = rb.simulate(w, r, 0.0, rebalance=False)["net"]
    direct = sum(NEUTRAL[a] * (1 + r[a]).prod() for a in al.ASSETS)
    assert (1 + net).prod() == pytest.approx(direct)


def test_calibration_uses_only_data_before_the_cutoff():
    idx = fridays(400, "2012-01-06")
    rng = np.random.default_rng(1)
    hist = pd.DataFrame({"vix": rng.normal(18, 4, 400)}, index=idx)
    rules = [rule("vix_spike")]
    new, table = rb.calibrate_pre_cutoff(rules, hist, "2018-01-01")
    wrecked = hist.copy()
    wrecked.loc[wrecked.index >= "2018-01-01", "vix"] = 999.0
    new2, _ = rb.calibrate_pre_cutoff(rules, wrecked, "2018-01-01")
    assert new[0]["value"] == new2[0]["value"] and new[0]["value"] < 40
    assert new[0]["clear"] < new[0]["value"]


def test_node_states_follow_the_shared_hysteresis_rule_and_hold_through_gaps():
    idx = fridays(6)
    hist = pd.DataFrame({"vix": [20, 31, 28.5, np.nan, 26, 20.0]}, index=idx)
    st = rb.node_states([rule("v")], hist)["v"].tolist()
    assert st == [False, True, True, True, False, False]


def test_targets_do_not_change_when_the_future_of_a_metric_changes():
    idx = fridays(80)
    rng = np.random.default_rng(2)
    hist = pd.DataFrame({"vix": rng.normal(25, 8, 80)}, index=idx)
    rules = [rule("v")]
    base = rb.target_path(rules, rb.node_states(rules, hist), 0.2)
    wrecked = hist.copy()
    wrecked.iloc[50:] = 99.0
    after = rb.target_path(rules, rb.node_states(rules, wrecked), 0.2)
    pd.testing.assert_frame_equal(base.iloc[:50], after.iloc[:50])


def test_excluded_and_untilted_rules_are_not_backtested():
    hist = pd.DataFrame({"vix": [1.0], "gdpnow": [1.0], "nfci": [1.0]}, index=fridays(1))
    rules = [rule("ok"), rule("leaky", metric="gdpnow", pit="exclude"),
             {"id": "notilt", "metric": "nfci", "op": ">", "value": 0, "message": "m"}]
    assert [r["id"] for r in rb.eligible_rules(rules, hist)] == ["ok"]


def test_node_attribution_adds_up_to_the_active_return_when_the_cap_does_not_bind():
    r = rets_frame(80, seed=3)
    idx = r.index
    rules = [rule("a", metric="m1"), rule("b", metric="m2", tilt={"Stocks": 0.0, "Treasuries": -0.04, "Credit": 0.0, "Cash": 0.04})]
    rng = np.random.default_rng(4)
    states = pd.DataFrame({"a": rng.random(80) > .6, "b": rng.random(80) > .5}, index=idx)
    targets = rb.target_path(rules, states, 0.2)
    rules_ret = rb.simulate(targets, r, 0.0)["net"]
    neutral = rb.simulate(pd.DataFrame([NEUTRAL] * 80, index=idx), r, 0.0)["net"]
    res = {"rules": rules, "states": states, "rets": r}
    contrib = rb.node_attribution(res)["contribution (pts, summed)"].sum()
    assert contrib == pytest.approx((rules_ret - neutral).sum() * 100)


def test_metric_series_last_values_match_live_metrics():
    n = 40
    idx = pd.date_range("2020-01-01", periods=n, freq="MS")
    series = {"CPIAUCSL": pd.Series(100 * 1.003 ** np.arange(n), index=idx),
              "CPILFESL": pd.Series(100 * 1.002 ** np.arange(n), index=idx),
              "PCEPILFE": pd.Series(100 * 1.0025 ** np.arange(n), index=idx),
              "UNRATE": pd.Series(np.r_[np.full(30, 3.8), np.linspace(3.9, 4.6, 10)], index=idx),
              "CFNAI": pd.Series(np.linspace(0.2, -0.5, n), index=idx),
              "T5YIFR": pd.Series(np.linspace(2.0, 2.4, 200), index=pd.bdate_range("2025-01-01", periods=200)),
              "WEI": pd.Series(np.linspace(1.0, 2.0, 100), index=pd.date_range("2025-01-04", periods=100, freq="W-SAT"))}
    live = macro.metrics(series)
    for name, (_, s) in macro.metric_series(series).items():
        assert s.iloc[-1] == pytest.approx(live[name]), name
