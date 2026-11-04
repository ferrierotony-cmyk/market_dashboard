# Dashboard window score backtest

Rebuilds the seven rules in the Morning Market Dashboard's config.R from public history, labels every morning open, selective or challenging, then looks at what spreads and deal flow did next.

Run: `python3 -I backtest.py <data dir>`

The data dir needs these files:
- fred_BAMLC0A0CM.csv, fred_BAMLH0A0HYM2.csv, fred_DGS10.csv, fred_VIXCLS.csv from FRED
- yahoo_MOVE.csv, yahoo_GSPC.csv with date and close columns
- edgar_daily.csv, daily counts of Form FWP pricing term sheets from SEC EDGAR full text search

backtest_summary.json is the output behind the numbers on the dashboard page. MOVE and S&P data only go back to October 2024, which limits those two rules. Pricing term sheets are a proxy for supply and catch about 3 filings a day against roughly 10 real deals.
