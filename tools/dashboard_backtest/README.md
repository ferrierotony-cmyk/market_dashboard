# Dashboard window score backtest

Rebuilds the seven rules in the Morning Market Dashboard's config.R from public history, labels every morning open, selective or challenging, then looks at what spreads and deal flow did next.

Run: `python3 -I backtest.py <data dir>`

The data dir needs these files:
- fred_BAMLC0A0CM.csv, fred_BAMLH0A0HYM2.csv, fred_DGS10.csv, fred_VIXCLS.csv from FRED
- yahoo_MOVE.csv, yahoo_GSPC.csv with date and close columns
- edgar_daily.csv, daily counts of Form FWP pricing term sheets from SEC EDGAR full text search

backtest_summary.json is the output of the first run. Its outcomes start at the close of the same day, so they skip the first move after each reading. Its b5_all column is zero on every day, which means that pull failed. Neither is used for the findings on the page. backtest.py was corrected on November 25, 2026. It now measures from the last close the morning knew and no longer reads that column. The saved summary is still the first run. Pricing term sheets are a proxy for supply and catch about 3 filings a day against roughly 10 real deals.

## Long test

long_test.py runs six of the seven rules from December 2003 on Moody's Baa spread, and rebuilds the two year window on current data.

Run: `python3 -I long_test.py <data dir> [chart.png]`

It also needs fred_BAA10Y.csv, and full history in yahoo_MOVE.csv and yahoo_GSPC.csv. FRED has carried only three years of the ICE indexes since April 2026, and that is what limits the two year test. long_test_summary.json holds the numbers on the dashboard page. The data files are not in the repo.
