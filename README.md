# Morning Market Dashboard

**Live demo:** https://ferrierotony-cmyk.github.io/market_dashboard/

The hosted page is a public demo. It rebuilds on a schedule from free data only, with the FRED, Treasury.gov, Yahoo and Nasdaq feeds. The pipeline and comps cards are empty on purpose, and the portfolio tab is a hypothetical model book, not real positions. Nothing from a Bloomberg terminal is published here.

Built in R by Anthony Ferriero. The full local version, which also supports a Bloomberg refresh and Windows alerts, is described below.

---

Market dashboard for DCM, fixed income and syndicate analysts. It needs no
Bloomberg terminal: data comes from free sources and refreshes automatically.

Open **`output/market_dashboard.html`** in Chrome or Edge. No internet is needed to view it,
and it reloads itself every 15 minutes. Two data files sit next to the page and must stay
with it: **`market_data.js`** (candles for the watchlist) and **`market_universe.js`** (the
whole-market snapshot). `output/market_dashboard.png` is a chart snapshot for email or Teams.

## What is in it

| Tab | What analysts get |
|---|---|
| **Morning** | One-screen view. KPI tiles, the Treasury curve, 2Y/10Y/30Y, curve slope and IG/HY spread charts. Tables for rates and funding, credit by rating and maturity, and overnight risk assets. The new-issue window scorecard with the calendar, plus pipeline, comps and a portfolio snapshot. |
| **Portfolio** | Total market value, day P&L, P&L since entry (price and carry), yield, duration, DV01 and CS01. Holdings table, allocation by asset class, sector and top holdings, DV01 by curve point, and concentration against limits. Performance vs AGG, LQD and SPY with return, volatility, Sharpe, beta, max drawdown and tracking error. |
| **Charts** | Candlesticks for every watchlist symbol over 1D, 5D, 1M, 6M, 1Y and 5Y. Toggle SMA 20/50/200, Bollinger bands, VWAP (intraday), volume, RSI and MACD. A snapshot panel with a one-line **why it moved** (move, volume, sector context, 52-week position, RSI, put/call, flagged headlines) and matched headlines. Correlation heatmap and rolling correlations. |
| **Market** | **Every US-listed common stock** (about 5,500 names) as a daily snapshot. Breadth tiles (advancers/decliners, median and cap-weighted move, share above the 50/200-day averages, new 52-week highs/lows, up vs down dollar volume), sector and market-cap tables, gainers and losers by size with liquidity floors, unusual volume, 52-week highs and lows, and a screener you can filter by text, sector, size and dollar volume and sort by any column. |
| **Macro & health** | Market health score from 13 indicators across six domains, graded green, amber or red. A macro ribbon covers CPI, core CPI, core PCE, unemployment, payrolls, GDP, claims, retail sales, NFCI and the Fed balance sheet. Charts cover inflation, Fed funds vs EFFR and SOFR, labor, and financial conditions. |
| **Watchlist & alerts** | Alerts from your rules (`inputs/alerts.csv`), the portfolio limits, red health indicators, options activity and market-wide movers, with an in-page **Rules editor**. Top gainers and losers with why-it-moved lines, a sector summary, and the 509-name watchlist table (S&P 500 plus macro) with filter and sort. Headlines matched to their company, with a summary paragraph (click to expand). Option activity for the detail names. |

The **feeds chip** in the header (`✓ 46 feeds`, `▲ 12 from cache`, `✗ 2 feeds down`) opens a
dialog listing every series, its source, freshness and whether this run fetched it, plus the
methodology notes. Every widget header shows its source and freshness; every chart has a
**Table** button.

## Alerts

Rules live in **`inputs/alerts.csv`**, one per row:

| Column | Values |
|---|---|
| `scope` | `market` (one number from rates, credit, vol, FX or the health score), `portfolio` (a portfolio total), `symbol` (a watchlist technical, checked for every name the target covers) |
| `target` | symbol scope only: a ticker (`T`), a list (`T,VZ`), `*` for every name, `detail` for detail names, `sector:Energy` |
| `metric` | market: a name from `ALERT_MARKET_METRICS` in `config.R` (`hy_oas`, `ust10y`, `vix`, `spx_fut`, `health_score`…) with an optional change suffix `.d1` `.w1` `.m1` `.ytd` (bp for yields and spreads, points for VIX/MOVE, % for prices). portfolio: `port.day_pnl`, `port.total_pct`, `port.dv01`, `port.max_issuer_pct`… symbol: `last`, `d1`, `w1`, `m1`, `ytd`, `vol_x`, `rsi`, `vs50`, `vs200`, `pos52` |
| `op` | `>` `<` `>=` `<=` `abs>` `abs<` `crosses_above` `crosses_below` (crosses use `last` against `sma50`, `sma200` or a price) |
| `severity` | `critical`, `serious`, `warning`, `info` |

Click **Edit rules** on the Alerts widget to add, change or delete rules and see what each
one would fire on right now. Edits stay in your browser until you click **Download
alerts.csv** and save it over `inputs/alerts.csv`; the next build uses it.

The per-row alert columns in `watchlist.csv` (`alert_above`, `alert_move_pct`…) apply to
detail names only (`WATCHLIST_ROW_ALERTS` in `config.R`). Market-wide movers outside the
watchlist use `MARKET_ALERT_RULES`, which carry market-cap and dollar-volume floors.

**Desktop notifications.** Every run toasts new alerts at or above `TOAST_MIN_SEVERITY`
(Windows 10/11, nothing to install; `notify.ps1`). An alert is not repeated within
`TOAST_REPEAT_HOURS`. Set `TOAST_ALERTS <- FALSE` to turn it off. Clicking the toast opens the
dashboard.

## Customizing the layout

* Click **Customize**. Drag a widget by its header to any cell; whatever it lands on moves
  down and the grid closes up. Drag the bottom-right corner to resize. Arrow keys move a
  focused widget, Shift+arrows resize it. The cross hides a widget; hidden widgets appear in
  the yellow bar to restore.
* Layouts save automatically in your browser. **Save layout as…** names one. Built-in presets
  are **Default**, **Syndicate desk** and **Rates & credit**.
* **Export** downloads your layouts as `layouts.json`. Save it as **`inputs/layouts.json`** and
  every machine that runs the build gets them as presets; **Import** loads one into a browser.
* **Theme** cycles Auto, Light and Dark. On a phone the widgets stack into one column in grid order.

## Data sources

| Source | Supplies | Latency |
|---|---|---|
| FRED | Treasury par curve, SOFR, EFFR, Fed target, breakevens, ICE BofA OAS, macro series | End of day, weekly or monthly |
| Treasury.gov | Same-day par curve | End of day |
| Yahoo Finance | Futures, indices, FX, ETFs, equities (daily and intraday candles), per-ticker headline feeds | Delayed up to 15 min |
| Nasdaq screener + Yahoo batch quotes | The whole-market snapshot: every listed common stock with sector, market cap, day change, 52-week range, 50/200-day averages and average volume | Delayed up to 15 min, once a day |
| Cboe | Option chains for equities and ETFs (volume, open interest, IV30) | Delayed 15 min |
| Bloomberg (optional) | Live comps when `USE_BLOOMBERG = TRUE` in `config.R` and a terminal is logged in | Real-time |

Every download is cached in `data/`. If a source is down, the dashboard builds from the
cache and the feeds chip in the header turns amber or red.

**Freshness rules** (`STALE_DAYS` in `config.R`): comps older than 30 days are hidden with a
note, pipeline rows priced more than 21 days ago are tagged, bond marks older than 10 days
are tagged, placeholder `EXAMPLE` pipeline rows never show, and alerts stamped before the
latest live quote are dropped.

**Not available free:** single-bond prices and Z-spreads, CDX and swaps. Comps stay a
desk-maintained CSV unless the Bloomberg option is on. Bond holdings are priced with a model,
described under Methodology in the feeds dialog. The Market tab's sector names come from
Nasdaq's taxonomy and differ from the GICS names on the watchlist.

### Choosing data sources by budget and latency

| Tier | Examples | Cost | Latency | What it adds |
|---|---|---|---|---|
| Free (this dashboard) | FRED, Treasury.gov, Yahoo Finance, Nasdaq, Cboe delayed quotes | Free | End of day for rates and credit; quotes delayed 10 to 15 min | UST curve, index spreads, macro, futures, FX, every listed stock, option chains. No single-bond prices, CDX or swaps. |
| Low-cost APIs | Polygon, Tiingo, Twelve Data, Financial Modeling Prep, Alpha Vantage | Paid monthly; free tiers are rate-limited | Real-time to 15 min for equities, ETFs and FX | Better intraday data, fundamentals and news. Little or no OTC credit. |
| Public fixed income | FINRA TRACE, MSRB EMMA | Free to low cost | Post-trade, delayed | Corporate and municipal trade prints for spot checks on comps. |
| Professional | Bloomberg, LSEG Workspace, ICE Data Services, Tradeweb, MarketAxess | Enterprise contracts | Real-time | Bond-level prices and spreads, CDX and iTraxx, swaps, new-issue monitors, ratings. |

Free sources are for internal analysis. Yahoo, Nasdaq, Cboe and ICE index data are subject
to their providers' terms and are not licensed for redistribution outside the desk.

## Refresh schedule

Two Windows Task Scheduler jobs run hidden, with no console window:

* **Morning Market Dashboard** runs a full build every weekday at 07:00 (about 5 minutes with
  the whole-market snapshot; `MARKET_UNIVERSE$enabled <- FALSE` saves about 90 seconds).
* **Morning Market Dashboard (intraday)** runs every 15 minutes from 07:15 for 10 hours (about 2 minutes).
  It refreshes quotes, candles, news and options. Rates, credit, macro and the market snapshot
  come from the morning cache (`MARKET_UNIVERSE$intraday <- TRUE` refreshes the snapshot too).

Change or remove the schedule:

```
powershell -ExecutionPolicy Bypass -File ".\schedule_daily_refresh.ps1" -At "06:30" -EveryMinutes 30
powershell -ExecutionPolicy Bypass -File ".\schedule_daily_refresh.ps1" -NoIntraday
powershell -ExecutionPolicy Bypass -File ".\schedule_daily_refresh.ps1" -Remove
```

Manual run (add `intraday` for the quick refresh):

```
"C:\Program Files\R\R-4.6.0\bin\Rscript.exe" "C:\path\to\market_dashboard\run_dashboard.R"
```

## Setup checklist

1. R packages: `install.packages(c("ggplot2","gridExtra","jsonlite","xml2","svglite","curl"))`.
2. A free FRED API key turns on the economic-release calendar. Put `FRED_API_KEY=your_key` in
   `.Renviron` in your home folder (never in the repo) and restart R.
3. Run `run_dashboard.R` once by hand and read `logs/run_YYYYMMDD.log`: it says how many feeds
   fetched, how many names the market snapshot covered and whether the Yahoo crumb worked.
4. Register the schedule with `schedule_daily_refresh.ps1`.

## Desk inputs (`inputs/`)

| File | Columns | Notes |
|---|---|---|
| `holdings.csv` | id, name, issuer, asset_class, sector, rating, pricing, symbol, spread_index, quantity, cost_price, mark_price, mark_date, entry_date, duration, coupon, price_per_100 | `pricing` is `model` (bonds), `yahoo` (ETFs and stocks, `symbol` = ticker, `quantity` = shares) or `manual` (fixed `mark_price`). For `model`, `symbol` is the UST tenor (2Y, 10Y…) and `spread_index` is an ICE BofA OAS series id (blank for Treasuries). |
| `watchlist.csv` | symbol, label, type, sector, industry, detail, alert_above, alert_below, alert_move_pct, alert_volume_x, news, news_query, options_symbol | 509 names: 9 macro instruments plus the 500 S&P 500 companies with their GICS sector and sub-industry. `detail` = Y adds intraday candles, 5-year weekly bars, headlines and options for that name. Add or remove rows freely. |
| `alerts.csv` | id, enabled, scope, target, metric, op, value, severity, note | See **Alerts** above. |
| `layouts.json` | written by the page's **Export** button | Shared layout presets. Optional. |
| `pipeline.csv` | issuer, rating, size_mm, tenor, ipt, status, pricing_date, notes | The live book. Rows whose issuer starts with `EXAMPLE` are ignored. |
| `comps.csv` | issuer, bond, rating, yield, z_spread, duration, as_of, source, bbg_ticker | Rows older than `STALE_DAYS$comps` are hidden until re-marked. |
| `calendar.csv` | date, time_et, event, importance, notes | Desk events; FRED releases are added when the API key is set. |

## Changing what is tracked

Everything is in `config.R`: FRED series, Yahoo symbols, KPI tiles, the issuance scorecard,
the health-score thresholds, benchmarks and risk-free rate, concentration limits, candle
timeframes, the correlation set, news keywords, the alert metric registry, market-universe
filters and market-wide alert rules, freshness limits and toast settings.

## Files

```
run_dashboard.R             entry point (morning or intraday mode), toasts new alerts
config.R                    settings
fetch_data.R                FRED / Treasury / Yahoo / Cboe / Bloomberg fetchers, caching, retries
market.R                    whole-market universe fetch and analytics
analytics.R                 portfolio, performance, correlations, health score, macro, watchlist
alerts.R                    rule engine for inputs/alerts.csv, desktop notifications
build_dashboard.R           HTML assembly, data files, PNG snapshot
notify.ps1                  Windows toast (called by run_dashboard.R)
assets/dashboard.css, .js   page styling, charts, layout engine, screener, rules editor
schedule_daily_refresh.ps1  Task Scheduler setup
inputs/  output/            desk inputs, built dashboard
data/  logs/                download cache and run logs (not in git; rebuilt by every run)
```

## Troubleshooting

* Run lock (added Oct 17, 2026). A folder named `market_dashboard_run.lock` in the Windows temp folder exists only while a build is running. After a sleep
  the morning and intraday tasks can fire together. The intraday run then logs "Skipped" and the
  morning build waits up to 10 minutes. A lock left by a killed run is ignored after 22 minutes.
* A log that jumps by hours between two lines usually means the laptop slept mid-run, not a hang.
* A failed toast now logs the PowerShell error text, and `logs/notify_error.txt` holds the last one.
* To make the 07:00 build wake the PC, re-run `schedule_daily_refresh.ps1` once. The PC needs mains
  power and "Allow wake timers" turned on in Windows power options.

* Check `logs/run_YYYYMMDD.log` and the feeds chip in the header (or `output/data_status.csv`).
* A FRED "Stream error in the HTTP/2 framing layer" is transient. The fetcher retries and then uses the cache.
* "Yahoo quotes: no crumb" in the log means Yahoo answered with a consent page or blocked the
  session; the Market tab then builds from the Nasdaq data alone (no 52-week columns) or the
  previous day's cache. It usually clears on the next run.
* Missing packages: `install.packages(c("ggplot2","gridExtra","jsonlite","xml2","svglite","curl"))`.
* Toasts need Windows 10 or 11 and a PowerShell that can run scripts (`run_dashboard.R` passes
  `-ExecutionPolicy Bypass` for that one call).
