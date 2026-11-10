# Fed liquidity lab

A research project, not investment advice. It tracks the Fed's balance sheet, consumer inflation and economic output from
FRED, and tests whether rules built on them would have beaten buy and hold. They did not. See [RESULTS.md](RESULTS.md).
Data: FRED, Federal Reserve Bank of St. Louis, including series from the Cleveland Fed, Atlanta Fed, NY Fed, S&P and Nasdaq,
each under its own terms. No data files are included. Everything is fetched at run time.

Tracks the Fed balance sheet and net liquidity (assets minus TGA minus ON RRP) from FRED, replays crash and
high-inflation episodes onto today's levels, and tests whether liquidity changes help allocate across asset classes.
Research tool, not investment advice.

## Quick start
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest
python fedliq.py          # live snapshot + scenarios
python allocator.py       # walk-forward test, backtest, scenario forecasts
python fredcfg.py --dashboard
```

## FRED API key (optional but recommended)
Everything runs without a key using FRED's public CSV download. With a free key from
https://fred.stlouisfed.org/docs/api/api_key.html the official `fredapi` wrapper is used instead, which also unlocks
series metadata, search, and ALFRED vintages (`FredSource.as_of`, `first_release`) for revision-free point-in-time data.

Set `FRED_API_KEY` in your environment, or copy `.env.example` to `.env` and fill it in. `.env` is git-ignored.
`python fredcfg.py --check` shows which mode is active.

## Macro pipeline: inflation and output
```
python macro.py                     # quality report, inflation + output tables, output/macro_dashboard.png
python macro.py --asof 2022-06-30   # what had been published by that date
python feature_study.py             # do inflation/output features add out-of-sample skill? (so far: no)
```
`pipeline.py` declares every series once (frequency, units, publication lag, plausible range), caches it on disk with a
lineage manifest, and runs quality gates (failed, stale, out of range, outlier print, gap, cached). Series that fail a
blocking gate are excluded from every reading and from alerts. Growth rates count calendar months, so a month that was
never published (October 2025 CPI and unemployment) cannot stretch a year-over-year figure to 13 months.
`inflation.py`: headline/core CPI and PCE, median, trimmed-mean and sticky CPI, breakevens, 5y5y, Michigan, gasoline,
each with 1m/3m/6m annualized and y/y. `output_trend.py`: real GDP vs CBO potential and a trailing (causal) log-linear
trend, GDPNow, Weekly Economic Index, industrial production, payrolls, Sahm rule, CFNAI.
Point-in-time caveat: publication lags are applied, but revised series (CPI seasonal factors, GDP) are still taken as last
revised. Real vintages need the official API key (`fredcfg.FredSource.as_of`).

## Regime rules, backtest, webhook, allocation log
```
python regime_backtest.py     # would the rules have beaten buy and hold since 2020? (so far: no)
python tracker.py check       # database and spreadsheet connection status
python tracker.py show        # recent logged allocations
python tracker.py sync        # push unsynced rows to the Google Sheet
```
Each node in `alert_rules.json` has a `tilt` (moves weight between stocks, Treasuries, credit, cash; sums to zero) and a
`pit` flag. The target mix is neutral plus the tilts of triggered nodes, capped at 20 points from neutral. A regime shift
is a target move of 2+ points since the last published target. Shifts are always logged to `data/allocations.db` and
`output/allocation_log.csv`.
`regime_backtest.py` replays the nodes point in time (publication lags, 5 bps costs, drift-aware turnover) against buy and
hold, weekly-rebalanced neutral, the S&P 500, and a static mix with the rules' own average weights. Thresholds that were set
from 2010-2026 percentiles are re-estimated from pre-2020 data for the headline run; the shipped thresholds are shown as a
flattered reference. Nodes whose history would leak the future (GDPNow, CBO potential) are excluded.
Webhook dispatch is off. To enable: set `"dispatch": true` under `regime` in `alert_rules.json` and set `ALERT_WEBHOOK_URL`
(https only; `ALERT_WEBHOOK_FORMAT` = json, slack, discord or ntfy). The payload carries the exact target weights, the trades
versus the last published target, and the triggered nodes. Google Sheet sync: see the setup notes at the top of `tracker.py`.

## Dashboard
`python build_dashboard.py` pulls live FRED data, re-evaluates the rules (read-only) and the allocator, reads the saved
backtests, and writes `output/dashboard/fed_liquidity_lab.json`. The dashboard page (`output/dashboard/index.html`) draws
everything from that one file. It is a snapshot: to refresh, rebuild the JSON and upload it again (or ask Claude to).

## Pre-registered design test (v2)
```
python prereg.py lock prereg_v2.json   # fixes a spec before it is tested (done; never re-locked)
python prereg_backtest.py              # runs it once per window and applies the registered criteria
```
`prereg_v2.json` is a locked spec: four fast nodes with trailing-percentile thresholds, count-based sizing, one inflation
overlay, a clean development window (2006-2019, Nasdaq Composite as the equity proxy) and a confirmation window
(2020-2026, not clean because v1 results were seen first). The runner refuses to run if the spec's hash no longer matches
its lock. **Result: FAIL** (criterion C1: the 90% interval for excess return versus a matched static mix, -0.3% to +1.5% a
year, includes zero). Per the registration nothing was tuned afterwards; a new design needs a new name and a new lock.
Details in `output/prereg_v2_result.json`.

## Alerts and monitoring
```
python alerts.py check --dry-run     # evaluate every rule, send nothing
python alerts.py monitor             # check + calendar reminders + upcoming releases
python alerts.py calendar --days 21
python alerts.py notify-test         # one test notification
```
Triggers live in `alert_rules.json` (metric, comparison, level, `clear` level for hysteresis, the review it prompts).
Alerts fire on a crossing, not on every check, with a 24h cooldown. The first run only records the starting state.
Channels: desktop toast and `output/alerts.jsonl` by default; an optional webhook (set `ALERT_WEBHOOK_URL`, and
`ALERT_WEBHOOK_FORMAT=ntfy|json`, then add `"webhook"` to `channels`). Nothing is sent externally unless you do that.
The Claude scheduled task `macro-liquidity-monitor` runs `monitor` on weekdays at 18:00 local time while the app is open.
To run it without the app, schedule `python alerts.py monitor` with Windows Task Scheduler (or cron) instead.

## Files
- `fredcfg.py` key handling, `FredSource` (fredapi or CSV), granular metric catalog, dashboard
- `fedliq.py` net liquidity tracker and scenario engine (historical replays and custom shocks)
- `pipeline.py` series registry, cache and lineage, quality gates, point-in-time availability
- `inflation.py`, `output_trend.py`, `macro.py` the inflation and output layer; `feature_study.py` tests it out of sample
- `prereg.py` design lock; `prereg_v2.json` + `prereg_v2.lock` the locked spec; `prereg_backtest.py` runs it and judges it
- `regime.py` node tilts to target weights, shift detection; `regime_backtest.py` the point-in-time backtest
- `dispatch.py` opt-in webhook; `tracker.py` SQLite allocation log with Google Sheet sync
- `alerts.py` rule engine, state, notifications; `alert_rules.json` the triggers
- `macro_calendar.py` upcoming releases (FRED calendar) and FOMC dates (Fed page)
- `allocator.py` features, walk-forward ridge model, skill gate, allocation rules, backtest, scenario forecasts

## Known limits
- FRED carries about 10 years of S&P 500 and about 3 years of ICE BofA spreads, so the test sample is small.
- Asset returns are proxies (price-only stocks, duration-based Treasuries and Baa credit, no defaults).
- Scenarios replay past dollar flows; they are analogues, not forecasts.
- `fredapi` paths (metadata, search, vintages) are covered by tests with a fake client, not run live without a key.
