"""Grounding checks: a value a model extracted is accepted only if it can be found in the source text.
Used after any model based extraction. Returns a list of problems, empty means every value was found in the release."""
import re
from datetime import datetime

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def date_forms(iso):
    try:
        d = datetime.strptime(iso, "%Y-%m-%d")
    except (ValueError, TypeError):
        return []
    m = MONTHS[d.month - 1]
    return [f"{m} {d.day}, {d.year}", f"{m[:3]}. {d.day}, {d.year}", f"{m[:3]} {d.day}, {d.year}", f"Sept. {d.day}, {d.year}" if d.month == 9 else f"{m} {d.day}, {d.year}"]


def amount_to_number(s):
    m = re.match(r"\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|mm|bn|m|b)?", (s or "").lower())
    if not m:
        return None
    v = float(m.group(1).replace(",", ""))
    u = (m.group(2) or "")
    return v * (1e9 if u in ("billion", "bn", "b") else 1e6 if u in ("million", "mm", "m") else 1)


def amounts_in_text(text):
    out = set()
    for m in re.finditer(r"[$€£]\s?([\d,]+(?:\.\d+)?)\s*(million|billion)?", text, re.I):
        try:
            v = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        u = (m.group(2) or "").lower()
        out.add(round(v * (1e9 if u == "billion" else 1e6 if u == "million" else 1), 0))
    return out


def check(row, text):
    """row has keys securities, cap, expiration, early_date. Returns list of problem strings."""
    problems = []
    for sec in [x.strip() for x in (row.get("securities") or "").split(";") if x.strip()]:
        m = re.match(r"(\d+\.\d+)%\s+(\d{4})", sec)
        if not m:
            continue
        coupon, year = m.groups()
        coupon_alt = coupon.rstrip("0").rstrip(".") if "." in coupon else coupon
        pat = rf"(?:{re.escape(coupon)}|{re.escape(coupon_alt)})\s*%[^.]{{0,120}}?{year}|Zero[- ]Coupon[^.]{{0,100}}{year}"
        if coupon == "0.000":
            if not (re.search(pat, text, re.I) or re.search(rf"0%[^.]{{0,100}}{year}", text)):
                problems.append(f"security not found: {sec}")
        elif not re.search(pat, text):
            problems.append(f"security not found: {sec}")
    cap = row.get("cap")
    if cap:
        v = amount_to_number(cap)
        if v is not None and round(v, 0) not in amounts_in_text(text):
            problems.append(f"cap amount not found in text: {cap}")
    for field in ("expiration", "early_date"):
        iso = row.get(field)
        if iso:
            if not any(f in text for f in date_forms(iso)):
                problems.append(f"{field} not found in text: {iso}")
    return problems
