# Credit research toolkit

Two scripts for the parts of credit work that are the same every time. Research tool, not investment advice.

- `credit_spread.py` spreads an issuer from SEC XBRL data: five fiscal years and the last twelve months, with an audit sheet that names the tag and the filing behind every number.
- `surveillance.py` checks `watchlist.csv` against limits and new filings, and routes each name to broken, re-underwrite or intact.
- `test_toolkit.py` holds the offline checks.

The limits in `watchlist.csv` are samples. There are no spreads in it, because there is no free feed.

SEC asks for a contact with every request. Set `SEC_USER_AGENT` to a name and an email before running.

Limits: reported EBITDA with nothing added back, US GAAP filers only, some issuers use their own debt tags, finance arms are consolidated, ratings and spreads are not read.

The results feed the portfolio page through `tools/live/build_live.py`.
