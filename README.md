# Morning Market Dashboard

Market dashboard for DCM, fixed income and syndicate analysts. It needs no
Bloomberg terminal: data comes from free sources and refreshes automatically.

Open **`output/market_dashboard.html`** in Chrome or Edge. No internet is needed to view it,
and it reloads itself every 15 minutes. The candlestick data for the 500-name watchlist sits
in **`output/market_data.js`** next to the page, so keep the two files together (the page works
without it, except for the Charts tab). `output/market_dashboard.png` is a chart snapshot for
email or Teams.

## What is in it

| Tab | What analysts get |
|---|---|
| **Morning** | One-screen view. KPI tiles, the Treasury curve, 2Y/10Y/30Y, curve slope and IG/HY spread charts. Tables for rates and funding, credit by rating and maturity, and overnight risk assets. Also the new-issue window scorecard with the calendar, plus pipeline, comps and a portfolio snapshot. |
| **Portfolio** | Total market value, day P&L, P&L since entry (price and carry), yield, duration, DV01 and CS01. Holdings table, allocation by asset class, sector and top holdings, DV01 by curve point, and concentration against limits. Performance vs AGG, LQD and SPY with return, volatility, Sharpe, beta, max drawdown and tracking error. |
| **Charts** | Candlesticks for every watchlist symbol over 1D, 5D, 1M, 6M, 1Y and 5Y. Toggle SMA 20/50/200, Bollinger bands, VWAP (intraday), volume, RSI and MACD. Includes a correlation heatmap (90 days, 1 year, change), rolling correlations, and a snapshot panel with headlines. |
| **Macro & health** | Market health score from 13 indicators across six domains, graded green, amber or red. A macro ribbon covers CPI, core CPI, core PCE, unemployment, payrolls, GDP, claims, retail sales, NFCI and the Fed balance sheet. Charts cover inflation, Fed funds vs EFFR and SOFR, labor, and financial conditions. |
| **Watchlist & alerts** | Alerts for price levels, big moves, volume spikes, RSI extremes, unusual options activity, put/call extremes, flagged headlines, concentration breaches and red health indicators (informational ones are collapsed). Top gainers and losers, a sector summary, and the 509-name watchlist table (S&P 500 plus macro), which can be filtered by text or sector and sorted by any column. Also headlines and option activity for the detail names. |
| **Data sources** | Where every number comes from, whether it is real-time, delayed or end of day, its last observation and whether this run fetched it. Also a guide to data sources by budget and latency. |

Every widget header shows its source and freshness. Every chart has a **Table** button.

## Customizing the layout

* Click **Customize**. Drag a widget by its header to move it, or drag its bottom-right corner to resize.
  The arrow buttons resize step by step, and the cross hides a widget. Hidden widgets appear in the yellow bar to restore.
* Layouts save automatically in your browser. Use **Save layout as…** for named layouts.
  Built-in presets are **Default**, **Syndicate desk** and **Rates & credit**.
* **Theme** cycles Auto, Light and Dark.
* On a phone or narrow window the widgets stack into one scrolling column.
* Layouts live in each person's browser, so every analyst can keep their own.

## Data sources

| Source | Supplies | Latency |
|---|---|---|
| FRED | Treasury par curve, SOFR, EFFR, Fed target, breakevens, ICE BofA OAS, macro series | End of day, weekly or monthly |
| Treasury.gov | Same-day par curve | End of day |
| Yahoo Finance | Futures, indices, FX, ETFs, equities (daily and intraday candles), headlines | Delayed up to 15 min |
| Cboe | Option chains for equities and ETFs (volume, open interest, IV30) | Delayed 15 min |
| Bloomberg (optional) | Live comps when `USE_BLOOMBERG = TRUE` in `config.R` and a terminal is logged in | Real-time |

Every download is cached in `data/`. If a source is down, the dashboard builds from the
cache and the header shows a warning that links to the Data sources tab.

**Not available free:** single-bond prices and Z-spreads, CDX and swaps. Comps stay a
desk-maintained CSV unless the Bloomberg option is on. Bond holdings are priced with a model, described under Methodology on the Data sources tab.

## Refresh schedule

Two Windows Task Scheduler jobs run hidden, with no console window:

* **Morning Market Dashboard** runs a full build every weekday at 07:00 (about 3.5 minutes).
* **Morning Market Dashboard (intraday)** runs every 15 minutes from 07:15 for 10 hours (about 2 minutes).
  It refreshes quotes, candles, news and options. Rates, credit and macro come from the morning cache.

Change or remove the schedule:

```
powershell -ExecutionPolicy Bypass -File ".\schedule_daily_refresh.ps1" -At "06:30" -EveryMinutes 30
powershell -ExecutionPolicy Bypass -File ".\schedule_daily_refresh.ps1" -NoIntraday
powershell -ExecutionPolicy Bypass -File ".\schedule_daily_refresh.ps1" -Remove
```

Manual run (add `intraday` for the quick refresh):

```
"C:\Program Files\R\R-4.6.0\bin\Rscript.exe" "C:\Users\ferri\OneDrive\Documents\R Folder\market_dashboard\run_dashboard.R"
```

## Desk inputs (`inputs/`)

| File | Columns | Notes |
|---|---|---|
| `holdings.csv` | id, name, issuer, asset_class, sector, rating, pricing, symbol, spread_index, quantity, cost_price, mark_price, mark_date, entry_date, duration, coupon, price_per_100 | `pricing` is `model` (bonds), `yahoo` (ETFs and stocks, `symbol` = ticker, `quantity` = shares) or `manual` (fixed `mark_price`). For `model`, `symbol` is the UST tenor (2Y, 10Y…) and `spread_index` is an ICE BofA OAS series id (blank for Treasuries). |
| `watchlist.csv` | symbol, label, type, sector, industry, detail, alert_above, alert_below, alert_move_pct, alert_volume_x, news, news_query, options_symbol | 509 names: 9 macro instruments plus the 500 S&P 500 companies with their GICS sector and sub-industry (one share class per company). `detail` = Y adds intraday candles (1D, 5D, 1M), 5-year weekly bars, headlines and options for that name; other names get 6M and 1Y daily charts only. Blank alert cells mean no alert. `options_symbol` = Cboe ticker (blank for futures and indices). Add or remove rows freely; quotes download in parallel, so 500 names take about 30 seconds. |
| `pipeline.csv` | issuer, rating, size_mm, tenor, ipt, status, pricing_date, notes | Example rows; replace with the live book. |
| `comps.csv` | issuer, bond, rating, yield, z_spread, duration, as_of, source, bbg_ticker | `bbg_ticker` is used only when the Bloomberg option is on. |
| `calendar.csv` | date, time_et, event, importance, notes | Set `FRED_API_KEY` (free) to add CPI, payrolls, PCE, GDP and other releases automatically. |

## Changing what is tracked

Everything is in `config.R`: FRED series, Yahoo symbols, KPI tiles, the issuance scorecard,
the health-score thresholds, benchmarks and risk-free rate, concentration limits,
candle timeframes, the correlation set, news keywords and option-alert rules.

## Files

```
run_dashboard.R             entry point (morning or intraday mode)
config.R                    settings
fetch_data.R                FRED / Treasury / Yahoo / Cboe / Bloomberg fetchers, caching, retries
analytics.R                 portfolio, performance, correlations, health score, macro, alerts
build_dashboard.R           HTML assembly, PNG snapshot
assets/dashboard.css, .js   page styling, charts, layout editor (inlined into the HTML at build)
schedule_daily_refresh.ps1  Task Scheduler setup
inputs/  output/  data/ (cache)  logs/
```

## Troubleshooting

* Check `logs/run_YYYYMMDD.log` and the Data sources tab (or `output/data_status.csv`).
* A FRED "Stream error in the HTTP/2 framing layer" is transient. The fetcher retries and then uses the cache.
* Missing packages: `install.packages(c("ggplot2","gridExtra","jsonlite","xml2","svglite"))`.
* Free sources are for internal analysis. Yahoo, Cboe and ICE index data are not licensed for redistribution.
