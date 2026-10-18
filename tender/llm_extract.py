"""Stage 2 (model version): read each cached press release with a model and extract tender and exchange offer fields.

Reads tender/out/meta.json and tender/out/texts from fetch.py. Writes tender/out/llm_events.csv and keeps a per document cache so a
release is only sent to the model once. Every value is then checked against the source text by verify.py.

Auth: uses the Anthropic SDK defaults. In GitHub Actions this is workload identity federation, no stored key.
Set LLM_MOCK_CSV_DIR to a folder of llm_out_*.csv files to test the pipeline without calling the API."""
import csv, glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
import verify

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "out")
CACHE = os.path.join(OUT, "llm_cache")
os.makedirs(CACHE, exist_ok=True)
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
MAX_CHARS = int(os.environ.get("LLM_MAX_CHARS", "40000"))
MOCK = os.environ.get("LLM_MOCK_CSV_DIR", "")

COLS = ["key", "is_offer", "kind", "issuer", "securities", "cap", "cap_basis", "sub_caps", "expiration", "early_date", "notes"]

PROMPT = """You are an extraction analyst reading an SEC press release about bond tender offers and exchange offers. Work only from the text.

Decide and extract:
- is_offer: Y if the document is a lifecycle release about an issuer's cash tender offer or exchange offer for DEBT notes, bonds or debentures (launch, early results, final or expiration results, extension, pricing terms, amendment, termination). Offers by an acquirer for an acquired company's notes count. N for new issue notes offerings, earnings, redemptions, equity or warrant offers, equity buybacks, registered exchange offers under a registration rights agreement for notes already sold privately, consent solicitation only releases, and anything else. When N, give a three word reason in notes and leave the other fields empty.
- kind: launch, early_results, final_results (includes expiration results and settlement), extension, pricing_terms, amendment, or terminated. If a release does two things, choose the primary one and mention the other in notes.
- issuer: short company name.
- securities: the target notes only, as coupon and maturity year like 4.250% 2029, separated by semicolons. Exclude new notes being issued, notes being redeemed, and notes that only appear as reference securities. Zero coupon notes are 0.000%. If a table has class names with no coupon, write the class names.
- cap: the current overall maximum tender amount or cap, as a number with unit, for example 750 million. Empty if the offer is any and all or has no overall cap. If the release upsized or amended it, give the new current amount.
- cap_basis: principal or purchase_price. Purchase price means the cap limits the aggregate consideration paid, excluding accrued interest. Empty if no cap.
- sub_caps: any series, pool or sub caps in one short phrase, else empty.
- expiration: the current expiration date as ISO yyyy-mm-dd, after any extension. Empty if the text has none.
- early_date: the early tender or early participation date as ISO, empty if none or if removed.
- notes: anything ambiguous, short.

Be literal and careful. Do not guess. If unsure leave a field empty and say why in notes.
Reply with one JSON object only, with exactly these keys: is_offer, kind, issuer, securities, cap, cap_basis, sub_caps, expiration, early_date, notes. All values are strings."""


def load_mock():
    rows = {}
    for f in glob.glob(os.path.join(MOCK, "llm_out_*.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            rows[r["key"]] = r
    return rows


def candidates(meta):
    """press release style documents that mention an offer near the top. 8-K cover pages are skipped, the exhibits carry the release."""
    out = []
    for m in meta:
        if m["doc"] == "8-K":
            continue
        t = open(os.path.join(OUT, "texts", m["key"] + ".txt"), encoding="utf-8").read()
        if re.search(r"tender offer|exchange offer|offers? to purchase|offer to exchange|tender results|cash tender", t[:3000], re.I):
            out.append((m, t))
    return out


def call_model(client, text):
    msg = client.messages.create(model=MODEL, max_tokens=1500, system=PROMPT,
                                 messages=[{"role": "user", "content": text[:MAX_CHARS]}])
    raw = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise ValueError("no JSON in model reply")
    return json.loads(m.group(0))


def main():
    meta = json.load(open(os.path.join(OUT, "meta.json")))
    cands = candidates(meta)
    print("candidate documents", len(cands))
    mock = load_mock() if MOCK else None
    client = None
    rows, fails = [], 0
    for m, text in cands:
        cf = os.path.join(CACHE, m["key"] + ".json")
        if os.path.exists(cf):
            r = json.load(open(cf))
        elif mock is not None:
            r = {k: (mock.get(m["key"], {}).get(k) or "") for k in COLS if k != "key"}
        else:
            if client is None:
                import anthropic
                client = anthropic.Anthropic()
            try:
                r = call_model(client, text)
            except Exception as e:  # keep going, the row is retried next run because nothing is cached
                fails += 1
                print("model call failed", m["key"], type(e).__name__, str(e)[:120])
                continue
            json.dump(r, open(cf, "w"))
        r = {k: str(r.get(k, "") or "") for k in COLS if k != "key"}
        r["key"] = m["key"]
        flags = []
        if r["is_offer"].upper().startswith("Y"):
            fixed = re.sub(r"\b(Januar|Februar|Septembe|Octobe|Novembe|Decembe)\s(y|r)\b", r"\1\2", text)
            flags = verify.check({"securities": r["securities"], "cap": r["cap"], "expiration": r["expiration"],
                                  "early_date": r["early_date"]}, fixed)
        r.update({"file_date": m["file_date"], "doc_issuer_sec": m["issuer"], "url": m["url"],
                  "verify_flags": " | ".join(flags), "needs_review": "yes" if flags else ""})
        rows.append(r)
    cols = COLS + ["file_date", "doc_issuer_sec", "url", "verify_flags", "needs_review"]
    with open(os.path.join(OUT, "llm_events.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r["file_date"], reverse=True))
    offers = [r for r in rows if r["is_offer"].upper().startswith("Y")]
    print("rows", len(rows), "offers", len(offers), "needs review", sum(1 for r in offers if r["needs_review"]), "failed calls", fails)
    if fails and not rows:
        sys.exit("every model call failed")


if __name__ == "__main__":
    main()
