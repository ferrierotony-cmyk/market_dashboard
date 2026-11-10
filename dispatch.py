"""Webhook dispatch for regime shifts. Opt-in, and quiet unless you configure it.

Nothing is sent unless BOTH are true:
  * regime.dispatch is true in alert_rules.json
  * the environment variable ALERT_WEBHOOK_URL is set (it is a secret, so it never lives in a file)

ALERT_WEBHOOK_FORMAT picks the body:
  json     {"text": summary, "data": payload}     generic receivers, Zapier, n8n   (default)
  slack    {"text": summary}                       Slack incoming webhook
  discord  {"content": summary}                    Discord webhook
  ntfy     plain-text body with a Title header     ntfy.sh topics

Only https URLs are allowed (plain http only for localhost). Failures are retried with backoff and
reported, never raised. The URL is never printed or logged; only its host is.
"""
import json
import os
import time
import urllib.request
from urllib.parse import urlparse


def configured_url() -> str | None:
    url = (os.environ.get("ALERT_WEBHOOK_URL") or "").strip()
    return url or None


def validate_url(url: str) -> str | None:
    """None when fine, otherwise the reason it is refused."""
    u = urlparse(url)
    if u.scheme == "https" and u.netloc:
        return None
    if u.scheme == "http" and u.hostname in ("localhost", "127.0.0.1", "::1"):
        return None
    return "webhook URL must be https (http is allowed only for localhost)"


def build_request(url: str, payload: dict, text: str, fmt: str) -> urllib.request.Request:
    if fmt == "ntfy":
        return urllib.request.Request(url, data=text.encode("utf-8"), method="POST",
                                      headers={"Title": "Regime shift", "Content-Type": "text/plain; charset=utf-8"})
    body = {"slack": {"text": text}, "discord": {"content": text}}.get(fmt, {"text": text, "data": payload})
    return urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                  headers={"Content-Type": "application/json"})


def send_payload(payload: dict, text: str, url: str | None = None, fmt: str | None = None,
                 opener=urllib.request.urlopen, retries: int = 3, sleep=time.sleep) -> dict:
    """Send one payload. Returns {'sent': bool, 'host': str, 'detail': str}."""
    url = url or configured_url()
    if not url:
        return {"sent": False, "host": None, "detail": "ALERT_WEBHOOK_URL not set; nothing sent"}
    bad = validate_url(url)
    host = urlparse(url).hostname
    if bad:
        return {"sent": False, "host": host, "detail": bad}
    fmt = (fmt or os.environ.get("ALERT_WEBHOOK_FORMAT") or "json").lower()
    last = ""
    for attempt in range(retries):
        try:
            with opener(build_request(url, payload, text, fmt), timeout=15) as r:
                code = getattr(r, "status", 200)
            if 200 <= code < 300:
                return {"sent": True, "host": host, "detail": f"HTTP {code}"}
            last = f"HTTP {code}"
        except Exception as e:
            last = type(e).__name__ + ": " + str(e).replace(url, "<url>")[:60]   # scrub the secret before truncating
        if attempt < retries - 1:
            sleep(2 ** attempt)
    return {"sent": False, "host": host, "detail": f"failed after {retries} tries ({last})"}
