"""Automation #2 - surveillance triggers (diagram steps M1 -> D7).

Reads watchlist.csv, checks every covered credit against rule-based triggers, and routes
each name to the diagram's D7 outcomes:

    BROKEN        -> escalate to PM: reduce / exit review   (HIGH severity trigger)
    RE-UNDERWRITE -> open re-underwrite task, back to R3    (MEDIUM severity trigger)
    INTACT        -> no action                              (none, or LOW only)

Triggers
  * New 10-K / 10-Q filed                 -> earnings re-underwrite
  * Credit-relevant 8-K items             -> e.g. 2.04 debt acceleration, 1.03 bankruptcy, 4.02 non-reliance
  * Gross leverage above your max         -> from LTM XBRL spread
  * Interest coverage below your min
  * Covenant headroom below X%            -> if you enter a covenant max leverage
  * Spread move vs. last check / vs. peers (you supply current spreads, e.g. a Bloomberg/TRACE export)
  * Annual review due within N days

Usage:
    python surveillance.py                         # uses watchlist.csv, writes alerts_YYYYMMDD.md/.csv
    python surveillance.py --watchlist my.csv --lookback-days 30
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from credit_toolkit.edgar import CREDIT_8K_ITEMS, recent_filings, resolve_cik, spread_issuer

STATE_FILE = Path("surveillance_state.json")
SEV_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
ROUTE = {3: "BROKEN - escalate to PM (reduce/exit review)", 2: "RE-UNDERWRITE - back to R3", 1: "INTACT", 0: "INTACT"}


def _f(row: dict, key: str) -> float | None:
    v = (row.get(key) or "").strip()
    return float(v) if v else None


def load_state() -> dict:
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}


def check_issuer(row: dict, state: dict, lookback_days: int, review_window: int, headroom_pct: float) -> dict:
    ticker = row["ticker"].strip().upper()
    prev = state.get(ticker, {})
    alerts: list[tuple[str, str, str]] = []  # (severity, trigger, detail)
    today = date.today()

    cik, name = resolve_cik(ticker)

    # 1) Filings since last run (first run: lookback window)
    # Look back one extra day and de-dupe by accession number so same-day filings are never missed.
    since = datetime.strptime(prev["last_checked"], "%Y-%m-%d").date() - timedelta(days=1) \
        if "last_checked" in prev else today - timedelta(days=lookback_days)
    seen = set(prev.get("seen_accessions", []))
    filings = [f for f in recent_filings(cik, since) if f["accession"] not in seen]
    seen_now = (prev.get("seen_accessions", []) + [f["accession"] for f in filings])[-200:]
    for f in filings:
        if f["form"] in ("10-K", "10-Q", "10-K/A", "10-Q/A"):
            alerts.append(("MEDIUM", f"New {f['form']}", f"Filed {f['filed']} - refresh model & memo. {f['url']}"))
        elif f["form"] in ("8-K", "8-K/A"):
            for item in f["items"]:
                if item in CREDIT_8K_ITEMS:
                    desc, sev = CREDIT_8K_ITEMS[item]
                    alerts.append((sev, f"8-K Item {item}: {desc}", f"Filed {f['filed']}. {f['url']}"))
        elif f["form"] in ("NT 10-K", "NT 10-Q"):
            alerts.append(("HIGH", f"Late filing notice ({f['form']})", f"Filed {f['filed']}. {f['url']}"))

    # 2) Fundamentals from the LTM spread
    metrics = {}
    try:
        spread = spread_issuer(ticker, years=2)
        latest = spread["periods"][-1]
        lev = latest.values.get("gross_leverage")
        cov = latest.values.get("interest_coverage")
        metrics = {"period": latest.label, "gross_leverage": lev, "interest_coverage": cov}
        max_lev, min_cov, cov_max = _f(row, "max_gross_leverage"), _f(row, "min_interest_coverage"), \
            _f(row, "covenant_max_leverage")
        if lev is not None and max_lev is not None and lev > max_lev:
            alerts.append(("MEDIUM", "Leverage above threshold", f"{lev:.2f}x vs max {max_lev:.2f}x ({latest.label})"))
        if cov is not None and min_cov is not None and cov < min_cov:
            alerts.append(("MEDIUM", "Coverage below threshold", f"{cov:.2f}x vs min {min_cov:.2f}x ({latest.label})"))
        if lev is not None and cov_max:
            headroom = (cov_max - lev) / cov_max
            metrics["covenant_headroom"] = headroom
            if headroom < 0:
                alerts.append(("HIGH", "Covenant breach (on reported basis)",
                               f"{lev:.2f}x vs covenant {cov_max:.2f}x - check covenant EBITDA definition"))
            elif headroom < headroom_pct:
                alerts.append(("MEDIUM", "Covenant headroom tight", f"{headroom:.0%} headroom ({lev:.2f}x vs {cov_max:.2f}x)"))
        prev_lev = prev.get("gross_leverage")
        if lev is not None and prev_lev is not None and lev - prev_lev >= 0.5:
            alerts.append(("MEDIUM", "Leverage step-up", f"{prev_lev:.2f}x -> {lev:.2f}x since last check"))
        for g in spread.get("gaps", []):
            alerts.append(("LOW", "Data gap", g))
    except Exception as e:
        alerts.append(("LOW", "Spread unavailable", str(e)))

    # 3) Spreads (user-supplied)
    cur, peer, trig = _f(row, "current_spread_bp"), _f(row, "peer_spread_bp"), _f(row, "spread_move_trigger_bp") or 50
    prev_spread = prev.get("current_spread_bp")
    if cur is not None and prev_spread is not None and abs(cur - prev_spread) >= trig:
        sev = "HIGH" if cur - prev_spread >= 2 * trig else "MEDIUM"
        alerts.append((sev, "Spread move", f"{prev_spread:.0f}bp -> {cur:.0f}bp ({cur - prev_spread:+.0f}bp, trigger {trig:.0f}bp)"))
    if cur is not None and peer is not None and abs(cur - peer) >= trig:
        direction = "wide" if cur > peer else "tight"
        alerts.append(("LOW" if direction == "wide" else "MEDIUM", f"Trading {direction} to peers",
                       f"{cur:.0f}bp vs peers {peer:.0f}bp ({cur - peer:+.0f}bp) - relative value check"))

    # 4) Annual review calendar
    lr = (row.get("last_review_date") or "").strip()
    if lr:
        due = datetime.strptime(lr, "%Y-%m-%d").date() + timedelta(days=365)
        if due <= today:
            alerts.append(("MEDIUM", "Annual review overdue", f"Was due {due}"))
        elif (due - today).days <= review_window:
            alerts.append(("LOW", "Annual review coming up", f"Due {due} ({(due - today).days} days)"))

    top = max((SEV_RANK[a[0]] for a in alerts), default=0)
    new_state = {"last_checked": today.isoformat(), "seen_accessions": seen_now,
                 **{k: v for k, v in metrics.items() if k == "gross_leverage"}}
    if cur is not None:
        new_state["current_spread_bp"] = cur
    return {"ticker": ticker, "name": name, "analyst": row.get("analyst", ""), "route": ROUTE[top],
            "rank": top, "alerts": sorted(alerts, key=lambda a: -SEV_RANK[a[0]]), "metrics": metrics,
            "state": {**prev, **new_state}}


def write_reports(results: list[dict], md_path: Path, csv_path: Path) -> None:
    results = sorted(results, key=lambda r: -r["rank"])
    lines = [f"# Credit Surveillance - {date.today()}", "",
             "| Ticker | Issuer | Route | Gross lev | Int cov | Alerts |", "|---|---|---|---|---|---|"]
    for r in results:
        m = r["metrics"]
        lev = f"{m['gross_leverage']:.2f}x" if m.get("gross_leverage") is not None else "n/a"
        cov = f"{m['interest_coverage']:.1f}x" if m.get("interest_coverage") is not None else "n/a"
        n = sum(1 for a in r["alerts"] if a[0] != "LOW")
        lines.append(f"| {r['ticker']} | {r['name']} | **{r['route']}** | {lev} | {cov} | {n} actionable |")
    for r in results:
        lines += ["", f"## {r['ticker']} - {r['name']}" + (f" (analyst: {r['analyst']})" if r["analyst"] else ""),
                  f"**Route:** {r['route']}", ""]
        lines += [f"- `{sev}` **{trig}** - {detail}" for sev, trig, detail in r["alerts"]] or ["- No triggers."]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "ticker", "issuer", "analyst", "route", "severity", "trigger", "detail"])
        for r in results:
            for sev, trig, detail in r["alerts"] or [("", "none", "")]:
                w.writerow([date.today(), r["ticker"], r["name"], r["analyst"], r["route"], sev, trig, detail])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--watchlist", default="watchlist.csv")
    ap.add_argument("--lookback-days", type=int, default=14, help="Filing window on first run (default 14)")
    ap.add_argument("--review-window", type=int, default=30, help="Warn N days before annual review (default 30)")
    ap.add_argument("--headroom", type=float, default=0.15, help="Covenant headroom alert level (default 0.15 = 15%%)")
    ap.add_argument("--no-save-state", action="store_true", help="Don't update surveillance_state.json")
    args = ap.parse_args(argv)

    with open(args.watchlist, newline="", encoding="utf-8-sig") as fh:
        rows = [r for r in csv.DictReader(fh) if (r.get("ticker") or "").strip()]
    state = load_state()
    results = []
    for row in rows:
        t = row["ticker"].strip().upper()
        print(f"Checking {t} ...", end=" ", flush=True)
        try:
            r = check_issuer(row, state, args.lookback_days, args.review_window, args.headroom)
            results.append(r)
            state[t] = r["state"]
            print(r["route"])
        except Exception as e:
            print(f"FAILED: {e}")

    stamp = f"{date.today():%Y%m%d}"
    md, cs = Path(f"alerts_{stamp}.md"), Path(f"alerts_{stamp}.csv")
    write_reports(results, md, cs)
    if not args.no_save_state:
        STATE_FILE.write_text(json.dumps(state, indent=2))
    print(f"\nWrote {md.resolve()}\n      {cs.resolve()}")
    return 2 if any(r["rank"] == 3 for r in results) else 0  # non-zero exit = something needs escalation


if __name__ == "__main__":
    sys.exit(main())
