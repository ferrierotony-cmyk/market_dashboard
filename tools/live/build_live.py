"""Builds live.json, the feed the portfolio pages read.

Five sections: models, toolkit, tender, lab, window. Each one is built on its own. If one fails, the last good
version of it is kept, with its own date and the error, so the page can say how old it is.

Run: python build_live.py --out live.json [--prev old.json] [--tender-dir dir] [--lab-dir dir] [--window-file file] [--only a,b]
SEC requests need SEC_USER_AGENT, a name and a contact."""
import argparse, csv, json, os, sys, traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SECTIONS = ("models", "toolkit", "tender", "lab", "window")
MODELS = json.loads((HERE / "models.json").read_text(encoding="utf-8"))
# the 8-K items that can make a model stale: deals, results, new debt, defaults
ITEMS = {"1.01": "a material agreement", "2.01": "a closed deal", "2.02": "results", "2.03": "new debt", "2.04": "a debt acceleration", "4.02": "a restatement"}
BIG = ("10-K", "10-Q", "10-K/A", "10-Q/A", "20-F")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def stale_filings(filings, since):
    """Filings after the model date that should make a reader doubt it. Newest first."""
    out = []
    for f in filings:
        if f["filed"] <= since: continue
        if f["form"] in BIG:
            out.append({"form": f["form"], "filed": f["filed"].isoformat(), "what": "quarterly or annual report", "url": f["url"], "big": True})
        elif f["form"].startswith("8-K"):
            hit = [ITEMS[i] for i in f["items"] if i in ITEMS]
            if hit: out.append({"form": f["form"], "filed": f["filed"].isoformat(), "what": ", ".join(hit), "url": f["url"], "big": False})
    return sorted(out, key=lambda x: x["filed"], reverse=True)


def models(a):
    sys.path.insert(0, str(ROOT / "credit_toolkit"))
    from credit_toolkit.edgar import recent_filings
    res = {}
    for name, m in MODELS.items():
        since = date.fromisoformat(m["model_date"])
        res[name] = {"model_date": m["model_date"], "new": stale_filings(recent_filings(m["cik"], since), since)[:6]}
    return res


def toolkit(a):
    sys.path.insert(0, str(ROOT / "credit_toolkit"))
    import surveillance as sv
    prev = ((a.prev_json.get("toolkit") or {}).get("data") or {}).get("state", {})
    rows, state = [], dict(prev)
    with open(ROOT / "credit_toolkit" / "watchlist.csv", newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            r = sv.check_issuer(row, state, 14, 30, 0.15)
            state[r["ticker"]] = r["state"]
            why = next((x[1] + ". " + x[2].split(" http")[0] for x in r["alerts"] if x[0] != "LOW"), "")
            rows.append({"ticker": r["ticker"], "issuer": r["name"], "route": r["route"].split(" - ")[0], "why": why,
                         "period": r["metrics"].get("period"), "leverage": r["metrics"].get("gross_leverage"), "coverage": r["metrics"].get("interest_coverage"),
                         "gaps": [x[2] for x in r["alerts"] if x[1] == "Data gap"]})
    if not any(r["leverage"] for r in rows): raise RuntimeError("no issuer could be spread")
    return {"run": date.today().isoformat(), "rows": rows, "state": state}


def weekdays(a, b):
    n, d = 0, a
    while d < b:
        d += timedelta(days=1); n += d.weekday() < 5
    return n


OFFER = {"launch", "early_results", "final_results", "extension", "pricing_terms", "amendment"}


def tender_stats(events, offers):
    dates = sorted(e["file_date"] for e in events)
    first, last = date.fromisoformat(dates[0]), date.fromisoformat(dates[-1])
    sec = [e for e in events if e["kind"] == "launch" and "sec.gov" in e["url"]]
    dated = [(weekdays(date.fromisoformat(e["file_date"]), date.fromisoformat(e["expiration_date"])), bool(e["early_date"])) for e in sec if e["expiration_date"]]
    day = {}
    for e in events:
        d = day.setdefault(e["file_date"], [0, 0]); d[0 if e["kind"] in OFFER else 1] += 1
    chart, d = [], first
    while d <= last:
        if d.weekday() < 5: chart.append([d.isoformat()] + day.get(d.isoformat(), [0, 0]))
        d += timedelta(days=1)
    return {"from": first.isoformat(), "through": last.isoformat(), "launches": sum(e["kind"] == "launch" for e in events), "sec_launches": len(sec), "dated": len(dated),
            "fast": sum(n <= 10 and not early for n, early in dated), "slow": sum(n > 10 and early for n, early in dated),
            "open": sum(o["status"] == "open_or_unknown" for o in offers), "offers": len(offers),
            "changed": sum("extension" in o["event_kinds"] or "amendment" in o["event_kinds"] for o in offers), "chart": chart}


def tender(a):
    d = Path(a.tender_dir)
    read = lambda n: list(csv.DictReader(open(d / n, encoding="utf-8")))
    out = tender_stats(read("events.csv"), read("offers.csv"))
    if out["launches"] < 5: raise RuntimeError("too few launches, %d" % out["launches"])
    return out


def lab(a):
    sys.path.insert(0, str(Path(a.lab_dir).resolve()))
    import fedliq, fredcfg, macro
    import inflation as inf
    src = fredcfg.get_source()
    w = fedliq.fetch_all("2010-01-01", src)["weekly"]
    last, wk4, yr = w.iloc[-1], w.iloc[-5], w.iloc[-53]
    out = {"as_of": w.index[-1].strftime("%Y-%m-%d"), "net_liq": round(float(last["net_liq"]), 1), "chg_4w": round(float(last["net_liq"] - wk4["net_liq"]), 1), "chg_1y": round(float(last["net_liq"] - yr["net_liq"]), 1),
           "assets": round(float(last["assets"]), 1), "tga": round(float(last["tga"]), 1), "rrp": round(float(last["rrp"]), 1),
           "series": [[i.strftime("%Y-%m-%d"), round(float(v), 1)] for i, v in w.loc["2021-01-01":, "net_liq"].items()]}
    t = inf.inflation_table(macro.collect(src).usable()).reset_index()
    out["inflation"] = [{"name": str(r.iloc[0]), "yoy": None if r["y/y %"] != r["y/y %"] else round(float(r["y/y %"]), 2), "m3": None if r["3m ann %"] != r["3m ann %"] else round(float(r["3m ann %"]), 2), "period": str(r.get("latest month", r.get("as of", "")))[:10]} for _, r in t.iterrows()]
    return out


def window(a):
    j = json.loads(Path(a.window_file).read_text(encoding="utf-8")); L = j["long"]
    return {"start": L["start"], "end": L["end"], "mornings": L["mornings"], "challenging": L["challenging"], "tighter": L["tighter"][1:], "abs_bp": L["abs_bp"], "wider_10": L["wider_10"], "before_20bp": L["before_20bp"]}


def main(argv=None):
    p = argparse.ArgumentParser()
    for k in ("out", "prev", "tender-dir", "lab-dir", "window-file", "only"): p.add_argument("--" + k)
    a = p.parse_args(argv)
    try: a.prev_json = json.loads(Path(a.prev).read_text(encoding="utf-8"))["sections"] if a.prev and Path(a.prev).exists() else {}
    except (ValueError, KeyError): a.prev_json = {}
    want = a.only.split(",") if a.only else SECTIONS
    need = {"tender": a.tender_dir, "lab": a.lab_dir, "window": a.window_file}
    out, failed = {}, []
    for s in SECTIONS:
        old = a.prev_json.get(s)
        if s not in want or (s in need and not (need[s] and Path(need[s]).exists())):
            if old: out[s] = old
            continue
        try:
            out[s] = {"ok": True, "built": now(), "data": globals()[s](a)}
        except Exception as e:
            traceback.print_exc(); failed.append(s)
            msg = "%s: %s" % (type(e).__name__, str(e)[:160])
            out[s] = dict(old, ok=False, error=msg, tried=now()) if old and old.get("data") else {"ok": False, "built": None, "error": msg, "tried": now(), "data": None}
        print(s, "ok" if out[s]["ok"] else "FAILED " + out[s]["error"])
    Path(a.out).write_text(json.dumps({"built": now(), "sections": out}, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    print("wrote", a.out, Path(a.out).stat().st_size, "bytes")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
