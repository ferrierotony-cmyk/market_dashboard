# Live layer

| File | What it does |
|---|---|
| `site_extra/portfolio/api/quotes.js` | Vercel function. Delayed quotes and FRED prints when a page asks, cached five minutes. Fixed symbol list. |
| `build_live.py` | Builds live.json: filing flags, toolkit run, tender counts, Fed lab reading, long test rerun. A failed section keeps its last good data. |
| `models.json` | The date each DCF was last updated. **Change it when a model changes**, or the flag will be wrong. |
| `health.py` | Checks every page, file, quote and feed age. Exits 1 with a list, so the GitHub job fails and emails the owner. |
| `test_live.py`, `test_quotes.js` | Offline checks. |
| `tools/portfolio_builder/psky/live.js` | The page side. Hidden until a feed answers. |

Numbers are live. Conclusions are dated and change only by hand.
