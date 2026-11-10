"""Regime layer: turn triggered nodes into target weights, detect regime shifts, publish them.

Each rule in alert_rules.json can carry a `tilt`, the way it moves weight between stocks,
Treasuries, credit and cash when it is triggered. The target mix is the neutral mix plus the
tilts of every triggered node, limited to `max_dev` from neutral per asset, long-only, summing
to 100%. A REGIME SHIFT is a change in that target of at least `min_change` for any asset
since the last target that was published.

Publishing is opt-in. A shift is always printed and logged locally (SQLite, CSV). It goes out
by webhook only when regime.dispatch is true in alert_rules.json AND ALERT_WEBHOOK_URL is set.
Targets are model output from a research tool, not investment advice.
"""
from datetime import datetime

import pandas as pd

import allocator as al
import dispatch
import tracker

DEFAULTS = {"max_dev": 0.20, "min_change": 0.02, "dispatch": False}
DISCLAIMER = "Model output of a research tool, not investment advice. Weights are fractions of the portfolio."


def regime_cfg(cfg: dict) -> dict:
    return {**DEFAULTS, **cfg.get("regime", {})}


def target_weights(triggered, rules: list, max_dev: float = DEFAULTS["max_dev"],
                   neutral: dict | None = None) -> pd.Series:
    """Neutral weights plus the tilt of every triggered node, bounded and long-only."""
    neutral = pd.Series(neutral or al.CONFIG["neutral"])[al.ASSETS]
    on = set(triggered)
    tilt = pd.Series(0.0, index=al.ASSETS)
    for r in rules:
        if r["id"] in on and r.get("tilt"):
            tilt = tilt.add(pd.Series(r["tilt"]).reindex(al.ASSETS).fillna(0.0), fill_value=0.0)
    w = (neutral + tilt).clip(lower=neutral - max_dev, upper=neutral + max_dev).clip(lower=0.0)
    return w / w.sum()


def triggered_nodes(state: dict, rules: list) -> list[str]:
    """Rule ids currently on that carry a tilt."""
    return [r["id"] for r in rules if r.get("tilt") and state.get(r["id"], {}).get("triggered")]


def max_change(prev: dict, new: pd.Series) -> float:
    return float(max(abs(new[a] - prev.get(a, 0.0)) for a in al.ASSETS))


def build_payload(kind: str, new: pd.Series, prev: dict | None, nodes: list, metrics: dict,
                  rules: list, now: datetime) -> dict:
    by_id = {r["id"]: r for r in rules}
    trades = {a: round(float(new[a] - (prev or {}).get(a, new[a])), 4) for a in al.ASSETS}
    return {
        "type": f"regime_{kind}",
        "time_utc": now.isoformat(),
        "targets": {a: round(float(new[a]), 4) for a in al.ASSETS},
        "previous_targets": prev,
        "trades": trades,                                   # change in weight, in fractions
        "triggered_nodes": [{"id": n, "metric": by_id[n]["metric"], "value": metrics.get(by_id[n]["metric"]),
                             "why": by_id[n]["message"]} for n in nodes],
        "note": DISCLAIMER,
    }


def payload_text(p: dict) -> str:
    parts = []
    for a in al.ASSETS:
        t = p["targets"][a] * 100
        d = p["trades"][a] * 100
        parts.append(f"{a} {t:.1f}%" + (f" ({d:+.1f} pts)" if p.get("previous_targets") and abs(d) >= 0.05 else ""))
    nodes = ", ".join(n["id"] for n in p["triggered_nodes"]) or "none (neutral)"
    return f"Regime {p['type'].split('_')[1]}: " + "; ".join(parts) + f". Triggered nodes: {nodes}. {DISCLAIMER}"


def process_regime(rules: list, state: dict, metrics: dict, cfg: dict, now: datetime,
                   dry_run: bool = False, log: "tracker.AllocationLog | None" = None,
                   send=dispatch.send_payload) -> tuple[dict, dict]:
    """Detect a shift against the last published target. Returns (info, updated state).

    First sight records a baseline (logged, never dispatched). After that, a shift is logged
    and, only if dispatch is enabled and configured, sent.
    """
    rc = regime_cfg(cfg)
    nodes = triggered_nodes(state, rules)
    new = target_weights(nodes, rules, rc["max_dev"])
    last = state.get("regime:last")
    info = {"nodes": nodes, "target": new, "kind": "none", "dispatched": None}
    new_state = dict(state)
    if last is None:
        kind, prev = "baseline", None
    elif max_change(last["target"], new) >= rc["min_change"]:
        kind, prev = "shift", last["target"]
    else:
        return info, new_state
    payload = build_payload(kind, new, prev, nodes, metrics, rules, now)
    info.update(kind=kind, payload=payload, text=payload_text(payload))
    if dry_run:
        return info, new_state
    log = log or tracker.AllocationLog()
    log.record(kind, payload["targets"], prev, nodes, note=info["text"], sync=True)
    if kind == "shift" and rc["dispatch"]:
        info["dispatched"] = send(payload, info["text"])
    new_state["regime:last"] = {"target": payload["targets"], "nodes": nodes, "time": now.isoformat()}
    return info, new_state
