"""Offline checks for the feed and the health check. Run: python test_live.py"""
import json, os, sys, tempfile
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_live as bl
import health as h
sys.path.insert(0, str(HERE.parent / "dashboard_backtest"))
import fetch_data as fd

N = 0


def check(name, ok):
    global N
    N += 1; print(("pass " if ok else "FAIL ") + name)
    if not ok: raise SystemExit(1)


f = lambda form, d, items=(): {"form": form, "filed": date.fromisoformat(d), "accession": "a", "items": list(items), "url": "https://www.sec.gov/x"}
got = bl.stale_filings([f("8-K", "2026-11-06", ["2.01", "9.01"]), f("10-Q", "2026-11-02"), f("8-K", "2026-10-30", ["5.02"]), f("10-Q", "2026-08-01"), f("4", "2026-11-03")], date(2026, 10, 24))
check("a closed deal after the model is flagged, the way Roku would have been", got[0]["form"] == "8-K" and "closed deal" in got[0]["what"])
check("a new 10-Q is flagged as big", any(x["form"] == "10-Q" and x["big"] for x in got))
check("an officer leaving, an old filing and a Form 4 are not", len(got) == 2)
check("a filing on the model date is not flagged", bl.stale_filings([f("10-Q", "2026-10-24")], date(2026, 10, 24)) == [])

ev = lambda d, kind, url, exp="", early="": {"file_date": d, "kind": kind, "url": url, "expiration_date": exp, "early_date": early}
t = bl.tender_stats([ev("2026-11-02", "launch", "https://www.sec.gov/a", "2026-11-06"), ev("2026-11-03", "launch", "https://www.sec.gov/b", "2026-12-02", "2026-11-17"), ev("2026-11-04", "launch", "https://wire", "2026-11-10"), ev("2026-11-04", "other", "https://www.sec.gov/c")],
                    [{"status": "closed", "event_kinds": "launch>extension"}, {"status": "open_or_unknown", "event_kinds": "launch"}])
check("fast and slow kinds", (t["dated"], t["fast"], t["slow"]) == (2, 1, 1))
check("open and changed offers", (t["open"], t["changed"]) == (1, 1))
check("chart has one row per weekday", [r[0] for r in t["chart"]] == ["2026-11-02", "2026-11-03", "2026-11-04"] and t["chart"][2][1:] == [1, 1])
check("weekdays skip the weekend", bl.weekdays(date(2026, 11, 6), date(2026, 11, 9)) == 1)

d = tempfile.mkdtemp(); prev, out = os.path.join(d, "p.json"), os.path.join(d, "o.json")
json.dump({"sections": {"window": {"ok": True, "built": "2026-11-01T00:00Z", "data": {"end": "x"}}, "lab": {"ok": True, "built": "2026-11-01T00:00Z", "data": {"as_of": "y"}}}}, open(prev, "w"))
bad = os.path.join(d, "bad.json"); open(bad, "w").write("{}")
code = bl.main(["--out", out, "--prev", prev, "--window-file", bad, "--only", "window"])
s = json.load(open(out))["sections"]
check("a failed section keeps the last good data and says so", code == 1 and s["window"]["ok"] is False and s["window"]["data"] == {"end": "x"} and s["window"]["built"] == "2026-11-01T00:00Z")
check("a section that was not asked for is carried over", s["lab"]["data"] == {"as_of": "y"})
check("a section with no input is skipped, not failed", bl.main(["--out", out, "--prev", prev, "--only", "tender"]) == 0)
open(prev, "w").write("not json")
check("a broken old feed does not stop the run", bl.main(["--out", out, "--prev", prev, "--only", "tender"]) == 0)

now = datetime(2026, 11, 25, 16, 0, tzinfo=timezone.utc)
good = {"quotes": {k: {"price": 1.0, "time": "2026-11-25T15:00:00.000Z"} for k in h.WANT}}
check("good quotes pass", h.check_quotes(good, now) == [])
check("a missing quote is a problem", h.check_quotes(dict(good, quotes={}), now)[0].startswith("no quote"))
old = json.loads(json.dumps(good)); old["quotes"]["SKYD"]["time"] = "2026-11-10T15:00:00.000Z"
check("an old quote is a problem", any("SKYD" in x for x in h.check_quotes(old, now)))
snap = {"built_at": "2026-11-25 15:28:47", "fred": {k: {"last": 1, "date": "2026-11-24"} for k in ("DGS10", "BAMLC0A0CM", "BAMLH0A0HYM2")}}
check("a fresh snapshot passes", h.check_snapshot(snap, now) == [])
snap["built_at"] = "2026-11-20 15:28:47"; snap["fred"]["DGS10"]["last"] = None
check("an old snapshot with a missing print is two problems", len(h.check_snapshot(snap, now)) == 2)
feed = {"sections": {k: {"ok": True, "built": "2026-11-25T10:00Z", "data": {"a": 1}} for k in h.MAX_AGE}}
check("a fresh feed passes", h.check_feed(feed, now) == [])
feed["sections"]["toolkit"]["built"] = "2026-11-10T10:00Z"; feed["sections"]["lab"]["ok"] = False
check("an old section and a failed one are problems", len(h.check_feed(feed, now)) == 2)
check("an inline style is a problem", h.check_page("a.html", '<h1>x</h1><p style="x">') == ["a.html has an inline style"])
check("the FRED API answer reads like the CSV download, with a blank for no print", fd.fred_csv({"observations": [{"date": "2026-11-23", "value": "4.1"}, {"date": "2026-11-24", "value": "."}]}) == "observation_date,value\n2026-11-23,4.1\n2026-11-24,\n")
print(N, "checks passed")
