"""Alert framework: notify when live FRED data crosses allocation triggers.

How it works
  * alert_rules.json lists triggers: a metric, a comparison, a level, and the allocation review
    it prompts. Metrics come live from FRED (net liquidity and its components, VIX, curve,
    credit spreads, financial conditions, inflation) and from the allocator model (does it
    pass its significance test, how far are its target weights from neutral).
  * Alerts fire on a CROSSING, not on every check. Once a rule is triggered it stays quiet
    until the reading clears its `clear` level, then it can fire again after the cooldown.
  * The first run only records the starting state, so existing conditions do not spam you.
  * State is kept in output/alert_state.json and every event in output/alerts.jsonl.

Channels (set in alert_rules.json "channels"):
  toast    desktop notification (Windows, macOS or Linux)
  log      output/alerts.jsonl
  webhook  optional. Set ALERT_WEBHOOK_URL (and ALERT_WEBHOOK_FORMAT=ntfy or json). Off unless
           you set the variable and list "webhook". Only the alert text is sent.

Commands:
  python alerts.py check            # evaluate rules, notify on crossings
  python alerts.py check --dry-run  # evaluate only: no notifications, state not saved
  python alerts.py monitor          # check + calendar reminders + upcoming releases report
  python alerts.py calendar --days 21
  python alerts.py notify-test      # send one test notification through the channels
Add --no-model to skip the allocator model (faster).
"""
import argparse
import json
import math
import operator
import os
import subprocess
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import allocator as al
import fedliq
import fredcfg
import macro
import macro_calendar
import regime
import tracker

ROOT = Path(__file__).resolve().parent
RULES_FILE = ROOT / "alert_rules.json"
OUT_DIR = ROOT / "output"
OPS = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge}
# clearing is the opposite comparison against the `clear` level
CLEAR_OPS = {"<": operator.ge, "<=": operator.gt, ">": operator.le, ">=": operator.lt}

METRICS = {
    "net_liq", "net_liq_4w_pct", "net_liq_13w_pct", "tga_4w_chg_bn", "rrp", "reserves_bn",
    "vix", "curve_10y2y", "baa_spread", "nfci", "stlfsi", "dgs10", "dgs10_4w_chg_bp",
    "dollar_4w_pct", "unrate", "claims",
    # from macro.py (inflation and output pipeline)
    "cpi_yoy", "core_cpi_yoy", "core_cpi_3m_ann", "core_pce_yoy", "core_pce_3m_ann", "median_cpi_3m_ann",
    "trimmed_mean_3m_ann", "breakeven_5y", "breakeven_5y5y", "mich_1y", "gas_yoy_pct",
    "gdp_yoy", "gdp_gap", "gdp_trend_dev", "gdpnow", "wei", "ip_yoy", "ip_trend_dev",
    "payroll_3m_avg_k", "sahm", "cfnai_ma3",
    "alloc_gate_max", "alloc_tilt_max_abs",
    "alloc_w_Stocks", "alloc_w_Treasuries", "alloc_w_Credit", "alloc_w_Cash",
}


# ------------------------------------------------------------------ rules
def load_rules(path: Path = RULES_FILE) -> dict:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    ids = set()
    for r in cfg["rules"]:
        for k in ("id", "metric", "op", "value", "message"):
            if k not in r:
                raise ValueError(f"rule {r.get('id', '?')} is missing {k!r}")
        if r["op"] not in OPS:
            raise ValueError(f"rule {r['id']}: op must be one of {list(OPS)}")
        if r["metric"] not in METRICS:
            raise ValueError(f"rule {r['id']}: unknown metric {r['metric']!r}")
        if r["id"] in ids:
            raise ValueError(f"duplicate rule id {r['id']!r}")
        ids.add(r["id"])
        if r.get("pit", "ok") not in ("ok", "caveat", "exclude"):
            raise ValueError(f"rule {r['id']}: pit must be ok, caveat or exclude")
        tilt = r.get("tilt")
        if tilt is not None:
            if set(tilt) - set(al.ASSETS):
                raise ValueError(f"rule {r['id']}: tilt keys must be from {al.ASSETS}")
            if abs(sum(tilt.values())) > 1e-9:
                raise ValueError(f"rule {r['id']}: tilt must sum to zero (a tilt moves weight, it does not add any)")
    return cfg


# ------------------------------------------------------------------ metrics
def _asof(s: pd.Series, when: pd.Timestamp) -> float:
    prior = s[s.index <= when]
    return float(prior.iloc[-1]) if len(prior) else float("nan")


def compute_metrics(source, with_model: bool = True) -> dict:
    """Latest value of every metric a rule can use. Missing data becomes NaN, never an error."""
    m = {}
    data = fedliq.fetch_all("2010-01-01", source)
    w, rrp_daily = data["weekly"], data["rrp_daily"]
    nl = w["net_liq"]
    m["net_liq"] = float(nl.iloc[-1])
    m["net_liq_4w_pct"] = float((nl.iloc[-1] / nl.iloc[-5] - 1) * 100)
    m["net_liq_13w_pct"] = float((nl.iloc[-1] / nl.iloc[-14] - 1) * 100)
    m["tga_4w_chg_bn"] = float(w["tga"].iloc[-1] - w["tga"].iloc[-5])
    m["rrp"] = float(rrp_daily.iloc[-1])
    m["reserves_bn"] = float(w["reserves"].iloc[-1]) if "reserves" in w else float("nan")

    def last(sid, start="2024-01-01"):
        try:
            return source.series(sid, start)
        except Exception:
            return pd.Series(dtype=float)

    def latest(sid):
        s = last(sid)
        return float(s.iloc[-1]) if len(s) else float("nan")

    m["vix"], m["curve_10y2y"], m["baa_spread"] = latest("VIXCLS"), latest("T10Y2Y"), latest("BAA10Y")
    m["nfci"], m["stlfsi"], m["unrate"], m["claims"] = latest("NFCI"), latest("STLFSI4"), latest("UNRATE"), latest("ICSA")
    y10 = last("DGS10")
    if len(y10):
        m["dgs10"] = float(y10.iloc[-1])
        m["dgs10_4w_chg_bp"] = (float(y10.iloc[-1]) - _asof(y10, y10.index[-1] - pd.Timedelta(days=28))) * 100
    usd = last("DTWEXBGS")
    if len(usd):
        m["dollar_4w_pct"] = (float(usd.iloc[-1]) / _asof(usd, usd.index[-1] - pd.Timedelta(days=28)) - 1) * 100
    # Inflation and output come from the vetted pipeline: series that fail the quality gates
    # (stale, out of range, failed fetch) are left out, so their rules report no_data.
    try:
        m.update(macro.metrics(macro.collect(source).usable()))
    except Exception as e:
        print(f"  macro pipeline unavailable: {str(e)[:80]}", file=sys.stderr)
    if with_model:
        m.update(model_metrics(source, w))
    return m


def model_metrics(source, weekly: pd.DataFrame, cfg: dict = al.CONFIG) -> dict:
    """Run the allocator pipeline on live data and report the current target and gate."""
    px = al.load_prices("2010-01-01", source)
    ds = al.build_dataset(weekly["net_liq"], al.asset_returns(px, cfg["durations"]), cfg)
    preds = al.walk_forward(ds, cfg)
    fit = al.fit_final(ds, preds, cfg)
    return model_metrics_from(ds, fit, cfg)


def model_metrics_from(ds: pd.DataFrame, fit: dict, cfg: dict = al.CONFIG) -> dict:
    t = al.current_target(ds, fit, cfg)
    out = {"alloc_gate_max": float(max(t["gate"].values())), "alloc_tilt_max_abs": t["tilt_max_abs"]}
    for a in al.ASSETS:
        out[f"alloc_w_{a}"] = float(t["weights"][a])
    return out


# ------------------------------------------------------------------ evaluation (pure)
def next_triggered(prev_triggered, val: float, rule: dict) -> bool:
    """One step of a node's on/off state with hysteresis. Shared by live alerts and the backtest.

    Off -> on when the value crosses `value`. On -> off only once it passes `clear`.
    `prev_triggered` is None the first time a node is seen.
    """
    crossing_in = bool(OPS[rule["op"]](val, rule["value"]))
    if prev_triggered:
        return not CLEAR_OPS[rule["op"]](val, rule.get("clear", rule["value"]))
    return crossing_in



def evaluate(rules: list, metrics: dict, state: dict, now: datetime,
             cooldown_hours: float = 24, notify_initial: bool = False):
    """Decide which rules fire. Returns (alerts to send, new state, one report row per rule).

    Events: fired, suppressed (re-crossed inside the cooldown), cleared, initial (first sight
    of a rule), unchanged, no_data.
    """
    new_state, alerts, rows = dict(state), [], []
    for r in rules:
        val = metrics.get(r["metric"])
        row = {"id": r["id"], "metric": r["metric"], "value": val, "rule": f"{r['op']} {r['value']}",
               "triggered": None, "event": "no_data"}
        if val is None or (isinstance(val, float) and math.isnan(val)):
            rows.append(row)
            continue
        prev = state.get(r["id"])
        crossing_in = OPS[r["op"]](val, r["value"])
        triggered = next_triggered(None if prev is None else prev["triggered"], val, r)
        if prev is None:
            event = "initial"
            fire = crossing_in and notify_initial
        elif prev["triggered"]:
            event = "unchanged" if triggered else "cleared"
            fire = False
        else:
            event, fire = ("unchanged", False)
            if crossing_in:
                last = prev.get("last_fired")
                recent = last and (now - datetime.fromisoformat(last)) < timedelta(hours=cooldown_hours)
                event, fire = ("suppressed", False) if recent else ("fired", True)
        entry = {"triggered": triggered, "last_value": val,
                 "last_fired": prev.get("last_fired") if prev else None}
        if fire:
            entry["last_fired"] = now.isoformat()
            event = "fired"
            alerts.append({"rule": r, "value": val, "time": now.isoformat()})
        new_state[r["id"]] = entry
        row.update(triggered=triggered, event=event)
        rows.append(row)
    return alerts, new_state, rows


def due_reminders(events: pd.DataFrame, state: dict, today: date, lead_days: int = 1,
                  importance=("high",)) -> tuple[list, dict]:
    """Calendar heads-ups for important events happening within `lead_days`, once per event."""
    new_state, due = dict(state), []
    for _, e in events.iterrows():
        if e["importance"] not in importance or not (0 <= (e["date"] - today).days <= lead_days):
            continue
        key = f"cal:{e['rid']}:{e['date'].isoformat()}"
        if key in new_state:
            continue
        new_state[key] = {"reminded": today.isoformat()}
        due.append(e.to_dict())
    return due, new_state


# ------------------------------------------------------------------ notification
def format_alert(a: dict) -> tuple[str, str]:
    r = a["rule"]
    body = f"{r['message']} ({r['metric']} = {a['value']:.2f}, trigger {r['op']} {r['value']})."
    if r.get("action"):
        body += f" Review: {r['action']}."
    return f"Fed liquidity alert [{r.get('severity', 'info')}]: {r['id']}", body


def format_reminder(e: dict) -> tuple[str, str]:
    when = "today" if e["days away"] == 0 else "tomorrow"
    body = f"{e['event']} {when} {e['time (CT)']} CT ({e['date']:%a %b %d})."
    if e.get("latest"):
        body += f" Latest: {e['latest']}."
    return f"Macro calendar: {e['event']}", body


def toast(title: str, body: str) -> bool:
    """Desktop notification. Text goes in through environment variables, never into code."""
    env = {**os.environ, "ALERT_TITLE": title, "ALERT_BODY": body}
    try:
        if sys.platform == "win32":
            ps = (
                "$ErrorActionPreference='Stop';"
                "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;"
                "$x=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
                "$t=$x.GetElementsByTagName('text');"
                "$t.Item(0).AppendChild($x.CreateTextNode($env:ALERT_TITLE)) | Out-Null;"
                "$t.Item(1).AppendChild($x.CreateTextNode($env:ALERT_BODY)) | Out-Null;"
                "$n=[Windows.UI.Notifications.ToastNotification]::new($x);"
                "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
                "'{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe').Show($n)"
            )
            cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps]
        elif sys.platform == "darwin":
            cmd = ["osascript", "-e",
                   'display notification (system attribute "ALERT_BODY") with title (system attribute "ALERT_TITLE")']
        else:
            cmd = ["notify-send", title, body]
        subprocess.run(cmd, env=env, check=True, timeout=30, capture_output=True)
        return True
    except Exception as e:
        print(f"  toast failed: {str(e)[:80]}", file=sys.stderr)
        return False


def webhook(title: str, body: str) -> bool:
    url = os.environ.get("ALERT_WEBHOOK_URL")
    if not url:
        return False
    try:
        if os.environ.get("ALERT_WEBHOOK_FORMAT", "ntfy") == "json":
            data, headers = json.dumps({"text": f"{title}\n{body}"}).encode(), {"Content-Type": "application/json"}
        else:
            data, headers = body.encode(), {"Title": title.encode("ascii", "replace").decode()}
        urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers, method="POST"), timeout=15)
        return True
    except Exception as e:
        print(f"  webhook failed: {str(e)[:80]}", file=sys.stderr)
        return False


def log_event(kind: str, title: str, body: str, extra: dict | None = None) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    rec = {"time": datetime.now(timezone.utc).isoformat(), "kind": kind, "title": title, "body": body, **(extra or {})}
    with open(OUT_DIR / "alerts.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")


def send(kind: str, title: str, body: str, channels: list, extra: dict | None = None) -> None:
    print(f"  >> {title}\n     {body}")
    if "toast" in channels:
        toast(title, body)
    if "webhook" in channels:
        webhook(title, body)
    if "log" in channels:
        log_event(kind, title, body, extra)


# ------------------------------------------------------------------ state
def load_state() -> dict:
    p = OUT_DIR / "alert_state.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_state(state: dict) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "alert_state.json").write_text(json.dumps(state, indent=1, default=str), encoding="utf-8")


# ------------------------------------------------------------------ commands
def print_rows(rows: list) -> None:
    df = pd.DataFrame(rows)
    df["value"] = df["value"].map(lambda v: "n/a" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:,.2f}")
    df["triggered"] = df["triggered"].map({True: "TRIGGERED", False: "ok", None: "-"})
    pd.set_option("display.width", 200)
    print(df.to_string(index=False))


def run_check(args, channels=None, source=None) -> dict:
    cfg = load_rules()
    channels = channels or cfg.get("channels", ["log"])
    source = source or fredcfg.get_source()
    now = datetime.now(timezone.utc)
    metrics = compute_metrics(source, with_model=not args.no_model)
    state = load_state()
    first_run = not state
    alerts, new_state, rows = evaluate(cfg["rules"], metrics, state, now, cfg.get("cooldown_hours", 24),
                                       notify_initial=getattr(args, "notify_initial", False))
    print(f"Rule check at {now:%Y-%m-%d %H:%M} UTC (FRED mode: {source.mode})")
    print_rows(rows)
    if first_run:
        n = sum(1 for r in rows if r["triggered"])
        saved = "recorded" if not args.dry_run else "not saved (dry run)"
        print(f"\nFirst run: starting state {saved}, {n} rule(s) already triggered, none notified. "
              "Use --notify-initial to be told about those too.")
    # Regime layer: triggered nodes -> target mix; a shift is logged and, only if enabled, dispatched.
    sheet = None
    try:
        sheet = tracker.SheetSink.from_env()
    except Exception as e:
        print(f"  spreadsheet unavailable: {type(e).__name__}: {str(e)[:80]}", file=sys.stderr)
    info, new_state = regime.process_regime(cfg["rules"], new_state, metrics, cfg, now, dry_run=args.dry_run,
                                            log=None if args.dry_run else tracker.AllocationLog(sheet=sheet))
    tgt = ", ".join(f"{a} {info['target'][a]*100:.1f}%" for a in al.ASSETS)
    print(f"\nREGIME target mix: {tgt}\n  triggered nodes: {', '.join(info['nodes']) or 'none (neutral)'}")
    if info["kind"] == "shift":
        print(f"  REGIME SHIFT detected: {info['text']}")
        if not args.dry_run:
            send("regime", "Regime shift: new target mix", info["text"], channels, {"targets": info["payload"]["targets"]})
            if info["dispatched"] is not None:
                d = info["dispatched"]
                print(f"  webhook: {'sent to ' + str(d['host']) if d['sent'] else 'not sent (' + d['detail'] + ')'}")
            elif not regime.regime_cfg(cfg)["dispatch"]:
                print("  webhook dispatch is off (regime.dispatch is false in alert_rules.json); shift logged locally.")
    elif info["kind"] == "baseline":
        print("  baseline target recorded" + (" (dry run: not saved)" if args.dry_run else " and logged"))
    if args.dry_run:
        print(f"\nDry run: {len(alerts)} alert(s) would fire; nothing sent, state not saved.")
        for a in alerts:
            print("  would send:", *format_alert(a), sep="\n     ")
    else:
        for a in alerts:
            send("alert", *format_alert(a), channels, {"rule": a["rule"]["id"], "value": a["value"]})
        save_state(new_state)
        print(f"\n{len(alerts)} alert(s) sent.")
    return {"metrics": metrics, "rows": rows, "alerts": alerts, "state": new_state, "regime": info}


def run_monitor(args) -> None:
    cfg = load_rules()
    channels = cfg.get("channels", ["log"])
    result = run_check(args, channels)
    cal, problems = macro_calendar.upcoming(days=args.days)
    print(f"\nUPCOMING MACRO INDICATORS, next {args.days} days (times US Central, as shown by FRED)")
    print(cal.drop(columns="rid").to_string(index=False) if len(cal) else "  none found")
    for p in problems:
        print("  unavailable:", p)
    if args.dry_run:
        return
    rem = cfg.get("reminders", {})
    due, state = due_reminders(cal, load_state(), date.today(), rem.get("lead_days", 1),
                               tuple(rem.get("importance", ["high"])))
    for e in due:
        send("reminder", *format_reminder(e), channels, {"event": e["event"], "date": str(e["date"])})
    save_state(state)
    print(f"\n{len(due)} calendar reminder(s) sent.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["check", "monitor", "calendar", "notify-test"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-model", action="store_true")
    ap.add_argument("--notify-initial", action="store_true")
    ap.add_argument("--days", type=int, default=14)
    args = ap.parse_args(argv)
    if args.command == "check":
        run_check(args)
    elif args.command == "monitor":
        run_monitor(args)
    elif args.command == "calendar":
        macro_calendar.main(["--days", str(args.days)])
    else:
        channels = load_rules().get("channels", ["log"])
        send("test", "Fed liquidity alerts: test", "If you can read this, notifications work.", channels)


if __name__ == "__main__":
    main()
