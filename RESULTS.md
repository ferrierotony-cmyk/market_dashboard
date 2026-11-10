# Results

Snapshot from November 10, 2026. Research only, not investment advice. All figures are net of 5 bps trading costs and use
only data that had been published at the time, with conservative publication lags.

## Do the 18 rules beat buy and hold? (v1, 2020 to October 2026)

No. Thresholds that were first set from 2010 to 2026 percentiles were re-estimated from pre-2020 data only.

| Strategy | Return / yr | Volatility | Max drawdown |
|---|---|---|---|
| 18 rules | 5.99% | 8.5% | -15.6% |
| Buy and hold, 50/30/10/10 | 8.09% | 10.7% | -19.5% |
| Same mix, rebalanced weekly | 7.34% | 10.0% | -18.2% |
| Static mix at the rules' average weights | 6.95% | 9.1% | -16.5% |

The rules trailed buy and hold by 2.2% a year (90% block-bootstrap interval -3.7% to -0.9%). Part of that is holding less stock.
The matched static mix isolates timing, and the rules trailed it by 1.0% a year (-2.0% to -0.1%). The Sahm node cost the most, 4.3
points of return summed over the period, because it switched on after the 2020 crash and stayed on through the rebound.

## A pre-registered redesign (v2)

`prereg_v2.json` was written and hashed (`prereg_v2.lock`) before it was tested. Four criteria were fixed in advance and the
runner refuses to run if the spec has changed.

| Window | v2 | Buy and hold | Max drawdown, v2 | Max drawdown, buy and hold |
|---|---|---|---|---|
| 2006 to 2019, equity proxy Nasdaq Composite | 7.91% | 7.74% | -17.9% | -24.2% |
| 2020 to 2026, S&P 500 (not clean, v1 results were seen first) | 6.69% | 7.77% | -17.1% | -19.5% |

C2 (drawdown), C3 (Sharpe) and C4 (confirmation window) passed. C1 failed: the 90% interval for excess return over a matched
static mix on the clean window was -0.3% to +1.5% a year, so it includes zero. Verdict: FAIL. Nothing was tuned afterwards.
The gain is concentrated in 2008 (6.6 points over the rebalanced mix). In the other 13 years v2 was about a third of a point a year behind.

## Liquidity allocator

A ridge model on 4 and 13 week changes in net liquidity, walk-forward with an embargo and a skill gate. A tilt is only taken
when the out-of-sample rank correlation has a t-stat of at least 2. Over 90 four-week decisions the best was 1.2 (stocks), so the
allocator holds the neutral mix.

## Caveats

- Stocks are price-only. Treasuries and credit are duration-based proxies with no defaults.
- FRED carries the S&P 500 only from late 2016, so the clean window uses the Nasdaq Composite as a proxy.
- Revised series (CPI, GDP, CFNAI and others) are used as last revised, so some revision look-ahead remains. Real vintages need a
  FRED API key (`fredcfg.FredSource.as_of`), which this run did not use.
- One bull market and one drawdown in 2020 to 2026 cannot prove much either way.
