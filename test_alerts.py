"""Offline tests for the alert framework and macro calendar. No network, no real notifications."""
import json
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

import alerts
import macro_calendar as mc
import allocator as al
from test_allocator import CFG, synth

T0 = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


def rule(**kw):
    base = {"id": "r", "metric": "vix", "op": ">", "value": 30, "clear": 27, "message": "VIX high"}
    return {**base, **kw}


def step(rules, metrics, state, now=T0, **kw):
    alerts_, new_state, rows = alerts.evaluate(rules, metrics, state, now, **kw)
    return alerts_, new_state, rows


# ------------------------------------------------------------ crossing logic
def test_first_run_records_state_and_stays_silent():
    a, st, rows = step([rule()], {"vix": 35}, {})
    assert a == [] and st["r"]["triggered"] is True and rows[0]["event"] == "initial"


def test_first_run_can_notify_when_asked():
    a, _, _ = step([rule()], {"vix": 35}, {}, notify_initial=True)
    assert len(a) == 1


def test_fires_once_on_the_crossing_then_stays_quiet():
    _, st, _ = step([rule()], {"vix": 20}, {})
    a1, st, _ = step([rule()], {"vix": 31}, st, T0 + timedelta(hours=1))
    a2, st, _ = step([rule()], {"vix": 33}, st, T0 + timedelta(hours=2))
    assert len(a1) == 1 and a2 == []


def test_hysteresis_keeps_rule_on_until_the_clear_level():
    _, st, _ = step([rule()], {"vix": 20}, {})
    _, st, _ = step([rule()], {"vix": 31}, st, T0 + timedelta(hours=1))
    _, st, rows = step([rule()], {"vix": 28.5}, st, T0 + timedelta(hours=2))   # below 30, above clear 27
    assert st["r"]["triggered"] is True and rows[0]["event"] == "unchanged"
    _, st, rows = step([rule()], {"vix": 26}, st, T0 + timedelta(hours=3))
    assert st["r"]["triggered"] is False and rows[0]["event"] == "cleared"


def test_recross_inside_cooldown_is_suppressed_then_fires_after_it():
    _, st, _ = step([rule(clear=29)], {"vix": 20}, {})
    a, st, _ = step([rule(clear=29)], {"vix": 31}, st, T0)
    assert len(a) == 1
    _, st, _ = step([rule(clear=29)], {"vix": 25}, st, T0 + timedelta(hours=2))
    a, st, rows = step([rule(clear=29)], {"vix": 32}, st, T0 + timedelta(hours=5))
    assert a == [] and rows[0]["event"] == "suppressed"
    _, st, _ = step([rule(clear=29)], {"vix": 25}, st, T0 + timedelta(hours=6))
    a, st, _ = step([rule(clear=29)], {"vix": 32}, st, T0 + timedelta(hours=30))
    assert len(a) == 1


@pytest.mark.parametrize("op,value,clear,low,high", [
    ("<", 0.0, 0.1, -0.5, 0.5), ("<=", 0.0, 0.1, -0.5, 0.5),
    (">", 30, 27, 20, 35), (">=", 30, 27, 20, 35)])
def test_every_operator_fires_on_the_right_side(op, value, clear, low, high):
    r = rule(op=op, value=value, clear=clear)
    below_side_triggers = op in ("<", "<=")
    safe, trig = (high, low) if below_side_triggers else (low, high)
    _, st, _ = step([r], {"vix": safe}, {})
    a, _, _ = step([r], {"vix": trig}, st, T0 + timedelta(hours=1))
    assert len(a) == 1


def test_missing_or_nan_metric_changes_nothing():
    _, st, _ = step([rule()], {"vix": 35}, {})
    for m in ({}, {"vix": float("nan")}):
        a, st2, rows = step([rule()], m, st, T0 + timedelta(hours=1))
        assert a == [] and st2 == st and rows[0]["event"] == "no_data"


# ------------------------------------------------------------ rules file
def test_shipped_rules_file_is_valid():
    cfg = alerts.load_rules()
    assert len(cfg["rules"]) >= 10
    assert all(r["metric"] in alerts.METRICS for r in cfg["rules"])


def test_bad_rules_are_rejected(tmp_path):
    for bad in ({"id": "x", "metric": "vix", "op": "=>", "value": 1, "message": "m"},
                {"id": "x", "metric": "not_a_metric", "op": ">", "value": 1, "message": "m"},
                {"id": "x", "metric": "vix", "op": ">", "message": "m"}):
        p = tmp_path / "r.json"
        p.write_text(json.dumps({"rules": [bad]}))
        with pytest.raises(ValueError):
            alerts.load_rules(p)


# ------------------------------------------------------------ notifications
def test_toast_passes_text_by_environment_not_by_code(monkeypatch):
    seen = {}

    def fake_run(cmd, env=None, **kw):
        seen["cmd"], seen["env"] = cmd, env

    monkeypatch.setattr(alerts.subprocess, "run", fake_run)
    nasty = "'; Remove-Item -Recurse C:\\ ; '"
    assert alerts.toast("title", nasty)
    assert nasty not in " ".join(seen["cmd"]) and seen["env"]["ALERT_BODY"] == nasty


def test_webhook_is_off_without_the_environment_variable(monkeypatch):
    monkeypatch.delenv("ALERT_WEBHOOK_URL", raising=False)
    monkeypatch.setattr(alerts.urllib.request, "urlopen", lambda *a, **k: pytest.fail("network call"))
    assert alerts.webhook("t", "b") is False


def test_send_only_uses_listed_channels(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(alerts, "toast", lambda *a: calls.append("toast"))
    monkeypatch.setattr(alerts, "webhook", lambda *a: calls.append("webhook"))
    monkeypatch.setattr(alerts, "log_event", lambda *a, **k: calls.append("log"))
    alerts.send("alert", "t", "b", ["log"])
    assert calls == ["log"]


def test_alert_text_names_the_trigger_and_the_review():
    title, body = alerts.format_alert({"rule": rule(action="Review risk"), "value": 31.2, "time": "x"})
    assert "r" in title and "31.20" in body and "Review risk" in body


# ------------------------------------------------------------ model metrics
def test_model_metrics_are_neutral_when_the_gate_is_closed():
    nl, ret = synth(420, signal=0.0, seed=3)
    ds = al.build_dataset(nl, ret, CFG)
    fit = al.fit_final(ds, al.walk_forward(ds, CFG), CFG)
    fit["gate"] = {a: 0.0 for a in al.RISKY}
    m = alerts.model_metrics_from(ds, fit, CFG)
    assert m["alloc_gate_max"] == 0.0 and m["alloc_tilt_max_abs"] == pytest.approx(0.0)
    assert m["alloc_w_Stocks"] == pytest.approx(CFG["neutral"]["Stocks"])


# ------------------------------------------------------------ calendar parsing
CAL_HTML = """<table><tbody>
<tr class="odd"><td colspan="2"><span style="font-weight: bold;">Monday November 09, 2026</span></td></tr>
<tr><td nowrap style="width:5%"> 7:30 am </td><td> <a href="/release?rid=10">Consumer Price Index</a>
  <i class="fa fa-check fa-lg"></i> </td></tr>
<tr class="odd"><td colspan="2"><span style="font-weight: bold;">Thursday November 12, 2026</span></td></tr>
<tr><td nowrap style="width:5%"> 3:30 pm </td><td> <a href="/release?rid=20">H.4.1 Factors Affecting Reserve Balances</a> </td></tr>
<tr><td nowrap style="width:5%"> N/A </td><td> <a href="/release?rid=50">Employment Situation</a> </td></tr>
</tbody></table>"""


def test_parse_calendar_reads_dates_times_and_released_flag():
    ev = mc.parse_calendar(CAL_HTML)
    assert [e["rid"] for e in ev] == [10, 20, 50]
    assert ev[0]["date"] == date(2026, 11, 9) and ev[0]["released"] is True
    assert ev[1]["date"] == date(2026, 11, 12) and ev[1]["time"] == "3:30 pm" and ev[1]["released"] is False
    assert ev[2]["time"] == "N/A"


def test_parse_calendar_returns_nothing_for_an_unrecognized_page():
    assert mc.parse_calendar("<html>layout changed</html>") == []


FOMC_HTML = """
<div>2026 FOMC Meetings</div>
<div class="fomc-meeting__month"><strong>January</strong></div><div class="fomc-meeting__date">27-28</div>
<div class="fomc-meeting__month"><strong>March</strong></div><div class="fomc-meeting__date">17-18*</div>
<div class="fomc-meeting__month"><strong>Oct/Nov</strong></div><div class="fomc-meeting__date">31-1</div>
<div>2025 FOMC Meetings</div>
<div class="fomc-meeting__month"><strong>December</strong></div><div class="fomc-meeting__date">9-10*</div>
"""


def test_parse_fomc_uses_the_decision_day_and_flags_projections():
    ev = mc.parse_fomc(FOMC_HTML)
    got = {e["date"]: e["projections"] for e in ev}
    assert got[date(2026, 1, 28)] is False and got[date(2026, 3, 18)] is True
    assert date(2026, 11, 1) in got            # meeting spanning two months
    assert date(2025, 12, 10) in got
    assert [e["date"] for e in mc.parse_fomc(FOMC_HTML, {2025})] == [date(2025, 12, 10)]


# ------------------------------------------------------------ reminders
def _events():
    return pd.DataFrame([
        {"date": date(2026, 11, 10), "time (CT)": "7:30 am", "event": "CPI inflation", "importance": "high",
         "rid": 10, "days away": 1, "latest": "CPI y/y %: 4.02"},
        {"date": date(2026, 11, 12), "time (CT)": "3:30 pm", "event": "Fed balance sheet", "importance": "medium",
         "rid": 20, "days away": 3, "latest": ""},
        {"date": date(2026, 11, 20), "time (CT)": "7:30 am", "event": "Jobs report", "importance": "high",
         "rid": 50, "days away": 11, "latest": ""},
    ])


def test_reminders_only_for_important_events_inside_the_window_and_only_once():
    today = date(2026, 11, 9)
    due, st = alerts.due_reminders(_events(), {}, today)
    assert [e["event"] for e in due] == ["CPI inflation"]
    again, _ = alerts.due_reminders(_events(), st, today)
    assert again == []


def test_reminder_text_mentions_timing_and_latest_value():
    title, body = alerts.format_reminder({**_events().iloc[0].to_dict()})
    assert "tomorrow" in body and "CPI y/y %: 4.02" in body
