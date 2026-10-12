# =============================================================================
#  Morning Market Dashboard - configuration
#  Edit this file to change what the dashboard tracks. No code changes needed.
#  Desk-maintained lists (holdings, watchlist, pipeline, comps, calendar) live
#  in inputs/*.csv and are read at every build.
# =============================================================================

DASH_TITLE    <- "Morning Market Dashboard"
DASH_SUBTITLE <- "DCM  |  Fixed Income  |  Syndicate"

# An open browser tab reloads itself this often (seconds), so a wall screen
# picks up every rebuild without anyone touching it. Reload is paused while
# someone is customizing the layout.
BROWSER_REFRESH_SECONDS <- 900

# How much daily history to pull for rates / credit (days).
HISTORY_DAYS <- 400
# Macro series need longer history for year-over-year changes.
MACRO_HISTORY_DAYS <- 1900

# Optional: a free FRED API key (https://fred.stlouisfed.org/docs/api/api_key.html)
# enables the automatic economic-release calendar and next-release dates on the
# macro ribbon. Without it the calendar uses inputs/calendar.csv only.
FRED_API_KEY <- Sys.getenv("FRED_API_KEY", unset = "")

# Optional: if this PC has a Bloomberg terminal logged in, set TRUE and the
# comps card is refreshed live via Rblpapi (bbg_ticker column in comps.csv).
# Everything else keeps using the free sources.
USE_BLOOMBERG <- FALSE

# -----------------------------------------------------------------------------
#  FRED series (free, no key). label = FRED series id
# -----------------------------------------------------------------------------
FRED_SERIES <- list(
  ust = c("1M" = "DGS1MO", "3M" = "DGS3MO", "6M" = "DGS6MO", "1Y" = "DGS1",
          "2Y" = "DGS2",   "3Y" = "DGS3",   "5Y" = "DGS5",   "7Y" = "DGS7",
          "10Y" = "DGS10", "20Y" = "DGS20", "30Y" = "DGS30"),
  money = c("SOFR" = "SOFR", "EFFR" = "EFFR",
            "Fed Funds Upper" = "DFEDTARU", "Fed Funds Lower" = "DFEDTARL",
            "10Y Breakeven" = "T10YIE", "5Y Breakeven" = "T5YIE",
            "30Y Mortgage (wkly)" = "MORTGAGE30US"),
  credit_rating = c("US IG (all)" = "BAMLC0A0CM", "IG AAA" = "BAMLC0A1CAAA",
                    "IG AA" = "BAMLC0A2CAA", "IG A" = "BAMLC0A3CA",
                    "IG BBB" = "BAMLC0A4CBBB", "US HY (all)" = "BAMLH0A0HYM2",
                    "HY BB" = "BAMLH0A1HYBB", "HY B" = "BAMLH0A2HYB",
                    "HY CCC & below" = "BAMLH0A3HYC"),
  credit_maturity = c("IG 1-3Y" = "BAMLC1A0C13Y", "IG 3-5Y" = "BAMLC2A0C35Y",
                      "IG 5-7Y" = "BAMLC3A0C57Y", "IG 7-10Y" = "BAMLC4A0C710Y",
                      "IG 10-15Y" = "BAMLC7A0C1015Y", "IG 15Y+" = "BAMLC8A0C15PY"),
  credit_other = c("IG Eff. Yield" = "BAMLC0A0CMEY", "HY Eff. Yield" = "BAMLH0A0HYM2EY",
                   "EM Corp OAS" = "BAMLEMCBPIOAS", "Euro HY OAS" = "BAMLHE00EHYIOAS"),
  macro = c("VIX (close)" = "VIXCLS", "WTI (close)" = "DCOILWTICO")
)

# -----------------------------------------------------------------------------
#  Macro ribbon (FRED). transform: level | yoy (% vs 12 obs ago) | diff (vs prior)
#  | avg4 (4-obs average) ; scale multiplies the result; release = FRED release
#  name used for "next release" when an API key is set.
# -----------------------------------------------------------------------------
MACRO_SERIES <- list(
  list(id = "CPIAUCSL",        label = "CPI YoY",            transform = "yoy",  unit = "%",   dec = 1, release = "Consumer Price Index"),
  list(id = "CPILFESL",        label = "Core CPI YoY",       transform = "yoy",  unit = "%",   dec = 1, release = "Consumer Price Index"),
  list(id = "PCEPILFE",        label = "Core PCE YoY",       transform = "yoy",  unit = "%",   dec = 1, release = "Personal Income and Outlays"),
  list(id = "UNRATE",          label = "Unemployment",       transform = "level",unit = "%",   dec = 1, release = "Employment Situation"),
  list(id = "PAYEMS",          label = "Payrolls m/m",       transform = "diff", unit = "k",   dec = 0, release = "Employment Situation"),
  list(id = "A191RL1Q225SBEA", label = "Real GDP q/q (SAAR)",transform = "level",unit = "%",   dec = 1, release = "Gross Domestic Product"),
  list(id = "ICSA",            label = "Jobless claims (4wk)",transform = "avg4",unit = "k",   dec = 0, scale = 0.001, release = "Unemployment Insurance Weekly Claims Report"),
  list(id = "RSAFS",           label = "Retail sales m/m",   transform = "pct",  unit = "%",   dec = 1, release = "Advance Monthly Sales for Retail and Food Services"),
  list(id = "NFCI",            label = "Chicago Fed NFCI",   transform = "level",unit = "",    dec = 2, release = "Chicago Fed National Financial Conditions Index"),
  list(id = "WALCL",           label = "Fed balance sheet",  transform = "level",unit = "$tn", dec = 2, scale = 1e-6, release = "Factors Affecting Reserve Balances")
)

# -----------------------------------------------------------------------------
#  Yahoo Finance symbols for the morning "Overnight & risk" table.
#  issuer_friendly_up: TRUE -> a rise is green; FALSE -> a rise is red; NA -> neutral
# -----------------------------------------------------------------------------
YAHOO_SYMBOLS <- data.frame(
  symbol = c("ES=F", "NQ=F", "^STOXX50E", "^FTSE", "^N225", "^HSI",
             "^VIX", "^MOVE",
             "ZT=F", "ZN=F", "ZB=F",
             "DX-Y.NYB", "EURUSD=X", "USDJPY=X", "GBPUSD=X",
             "CL=F", "BZ=F", "GC=F",
             "LQD", "HYG", "TLT", "IEF"),
  label  = c("S&P 500 fut", "Nasdaq 100 fut", "Euro Stoxx 50", "FTSE 100", "Nikkei 225", "Hang Seng",
             "VIX", "MOVE",
             "UST 2Y fut", "UST 10Y fut", "UST 30Y fut",
             "DXY", "EUR/USD", "USD/JPY", "GBP/USD",
             "WTI crude", "Brent crude", "Gold",
             "LQD (IG ETF)", "HYG (HY ETF)", "TLT (20Y+ UST)", "IEF (7-10Y UST)"),
  group  = c(rep("Equities", 6), rep("Volatility", 2), rep("Rates futures", 3),
             rep("FX", 4), rep("Commodities", 3), rep("Credit / rates ETFs", 4)),
  issuer_friendly_up = c(rep(TRUE, 6), FALSE, FALSE, TRUE, TRUE, TRUE,
                         NA, NA, NA, NA, NA, NA, NA, TRUE, TRUE, TRUE, TRUE),
  stringsAsFactors = FALSE
)

# Extra Yahoo symbols needed by analytics (health score, correlations, benchmarks)
EXTRA_YAHOO <- c("^GSPC", "^VIX3M", "^VIX9D", "^SKEW")

# -----------------------------------------------------------------------------
#  KPI tiles across the top of the morning view
# -----------------------------------------------------------------------------
KPI_TILES <- list(
  list(label = "UST 2Y",        key = "DGS2",         kind = "yield"),
  list(label = "UST 10Y",       key = "DGS10",        kind = "yield"),
  list(label = "UST 30Y",       key = "DGS30",        kind = "yield"),
  list(label = "2s10s",         key = "2s10s",        kind = "bp"),
  list(label = "IG OAS",        key = "BAMLC0A0CM",   kind = "bp"),
  list(label = "HY OAS",        key = "BAMLH0A0HYM2", kind = "bp"),
  list(label = "SOFR",          key = "SOFR",         kind = "yield"),
  list(label = "10Y Breakeven", key = "T10YIE",       kind = "yield"),
  list(label = "S&P 500 fut",   key = "ES=F",         kind = "px"),
  list(label = "VIX",           key = "^VIX",         kind = "level"),
  list(label = "MOVE",          key = "^MOVE",        kind = "level"),
  list(label = "DXY",           key = "DX-Y.NYB",     kind = "px")
)

# -----------------------------------------------------------------------------
#  New-issue window scorecard (syndicate). dir = "below": lower is better.
# -----------------------------------------------------------------------------
ISSUANCE_RULES <- list(
  list(name = "VIX",                      metric = "vix",         good = 18,   warn = 25,   dir = "below"),
  list(name = "MOVE",                     metric = "move",        good = 100,  warn = 120,  dir = "below"),
  list(name = "IG OAS 1-wk change (bp)",  metric = "ig_w1",       good = 3,    warn = 8,    dir = "below"),
  list(name = "HY OAS 1-wk change (bp)",  metric = "hy_w1",       good = 10,   warn = 25,   dir = "below"),
  list(name = "S&P futures overnight (%)",metric = "spx_d1",      good = -0.5, warn = -1.5, dir = "above"),
  list(name = "UST 10Y 1-day move (bp)",  metric = "ust10_absd1", good = 5,    warn = 10,   dir = "below"),
  list(name = "IG OAS vs 1-yr range",     metric = "ig_pct1y",    good = 0.5,  warn = 0.8,  dir = "below")
)
WINDOW_LABELS <- c(open = "OPEN", selective = "SELECTIVE", closed = "CHALLENGING")

# -----------------------------------------------------------------------------
#  Market health composite: ~12 indicators across six domains.
#  Each graded green / yellow / red; composite = share of available points.
# -----------------------------------------------------------------------------
HEALTH_RULES <- list(
  list(domain = "Volatility", name = "VIX",                         metric = "vix",          good = 18,   warn = 25,   dir = "below", fmt = "%.1f"),
  list(domain = "Volatility", name = "VIX / VIX3M (term structure)",metric = "vix_ts",       good = 0.92, warn = 1.00, dir = "below", fmt = "%.2f"),
  list(domain = "Volatility", name = "MOVE (rates vol)",            metric = "move",         good = 100,  warn = 120,  dir = "below", fmt = "%.0f"),
  list(domain = "Credit",     name = "IG OAS, position in 1-yr range", metric = "ig_pct1y",  good = 0.60, warn = 0.85, dir = "below", fmt = "pct"),
  list(domain = "Credit",     name = "HY OAS 1-month change (bp)",  metric = "hy_m1",        good = 15,   warn = 40,   dir = "below", fmt = "%+.0f"),
  list(domain = "Rates",      name = "UST 10Y 1-month move (bp, abs)", metric = "ust10_absm1", good = 25, warn = 50,   dir = "below", fmt = "%.0f"),
  list(domain = "Rates",      name = "3m10y curve (bp)",            metric = "c3m10y",       good = 25,   warn = -25,  dir = "above", fmt = "%+.0f"),
  list(domain = "Equity",     name = "S&P 500 vs 200-day avg (%)",  metric = "spx_vs200",    good = 2,    warn = -3,   dir = "above", fmt = "%+.1f"),
  list(domain = "Equity",     name = "S&P 500 drawdown from 52w high (%)", metric = "spx_dd", good = -5,  warn = -10,  dir = "above", fmt = "%.1f"),
  list(domain = "Dollar & commodities", name = "DXY 1-month move (%, abs)", metric = "dxy_absm1", good = 2, warn = 4, dir = "below", fmt = "%.1f"),
  list(domain = "Dollar & commodities", name = "WTI 1-month move (%, abs)", metric = "wti_absm1", good = 10, warn = 20, dir = "below", fmt = "%.1f"),
  list(domain = "Funding & conditions", name = "Chicago Fed NFCI",  metric = "nfci",         good = -0.30,warn = 0,    dir = "below", fmt = "%.2f"),
  list(domain = "Funding & conditions", name = "SOFR minus EFFR (bp)", metric = "sofr_effr",  good = 3,    warn = 8,    dir = "below", fmt = "%+.0f")
)
HEALTH_LABELS <- c(good = "STABLE", warn = "CAUTION", bad = "STRESS")

# -----------------------------------------------------------------------------
#  Portfolio analytics
# -----------------------------------------------------------------------------
BENCHMARKS <- c("AGG" = "US Aggregate (AGG)", "LQD" = "IG Corporate (LQD)", "SPY" = "S&P 500 (SPY)")
PRIMARY_BENCHMARK <- "AGG"
RISK_FREE_SERIES  <- "SOFR"     # FRED id used for Sharpe ratio
CONCENTRATION_LIMITS <- list(
  single_issuer_ex_govt = 0.15,   # max weight of any one non-government issuer
  sector_ex_govt        = 0.30,   # max weight of any one non-government sector
  top5                  = 0.80    # max combined weight of the five largest holdings
)

# -----------------------------------------------------------------------------
#  Charts: candlestick timeframes (Yahoo range / interval)
# -----------------------------------------------------------------------------
CANDLE_TIMEFRAMES <- list(
  "1D" = list(range = "1d",  interval = "5m",  intraday = TRUE),
  "5D" = list(range = "5d",  interval = "15m", intraday = TRUE),
  "1M" = list(range = "1mo", interval = "60m", intraday = TRUE),
  "6M" = list(range = "2y",  interval = "1d",  show = 126),
  "1Y" = list(range = "2y",  interval = "1d",  show = 252),
  "5Y" = list(range = "5y",  interval = "1wk")
)

# Correlation heatmap set. kind: ret = % return, diff = level change (yields/spreads/vol)
CORR_SET <- list(
  list(label = "S&P 500",   src = "yahoo", key = "^GSPC",        kind = "ret"),
  list(label = "Nasdaq fut",src = "yahoo", key = "NQ=F",         kind = "ret"),
  list(label = "UST 10Y",   src = "fred",  key = "DGS10",        kind = "diff"),
  list(label = "2s10s",     src = "derived", key = "2s10s",      kind = "diff"),
  list(label = "IG OAS",    src = "fred",  key = "BAMLC0A0CM",   kind = "diff"),
  list(label = "HY OAS",    src = "fred",  key = "BAMLH0A0HYM2", kind = "diff"),
  list(label = "VIX",       src = "yahoo", key = "^VIX",         kind = "diff"),
  list(label = "MOVE",      src = "yahoo", key = "^MOVE",        kind = "diff"),
  list(label = "DXY",       src = "yahoo", key = "DX-Y.NYB",     kind = "ret"),
  list(label = "WTI",       src = "yahoo", key = "CL=F",         kind = "ret"),
  list(label = "Gold",      src = "yahoo", key = "GC=F",         kind = "ret"),
  list(label = "LQD",       src = "yahoo", key = "LQD",          kind = "ret")
)
ROLLING_CORR_PAIRS <- list(
  c("S&P 500", "UST 10Y"),   # stock-bond: positive = yields up when stocks up
  c("S&P 500", "HY OAS"),
  c("UST 10Y", "DXY")
)
ROLLING_CORR_WINDOW <- 60

# -----------------------------------------------------------------------------
#  Watchlist alerts, news and options
# -----------------------------------------------------------------------------
# Headlines containing these words are flagged (case-insensitive)
NEWS_KEYWORDS <- c("downgrade", "upgrade", "offering", "notes", "bond", "debt", "refinanc",
                   "tender", "acquire", "acquisition", "merger", "buyback", "guidance",
                   "rating", "default", "lawsuit", "investigation", "ceo")
NEWS_PER_SYMBOL <- 6
NEWS_MAX_AGE_HOURS <- 72
# Per-ticker RSS feeds carry a summary paragraph; the search endpoint only has
# titles. "rss" tries the feed first and falls back to search for queries that
# are not a ticker (e.g. "S&P 500").
NEWS_SOURCE <- "rss"
NEWS_SUMMARY_CHARS <- 320

# -----------------------------------------------------------------------------
#  Freshness. Desk CSV rows older than these limits (days) are hidden and the
#  widget says how many were dropped, so nobody prices off stale comps.
# -----------------------------------------------------------------------------
STALE_DAYS <- list(comps = 30, pipeline = 21, holdings_mark = 10)
# Alerts stamped more than this many hours before the latest live quote are
# dropped (a stale cache for one symbol must not keep an old alert alive).
ALERT_MAX_AGE_HOURS <- 36

OPTIONS_RULES <- list(
  min_contract_volume = 2000,  # a contract needs at least this volume to count as unusual
  vol_oi_ratio        = 1.5,   # ...and volume at least this multiple of open interest
  pc_high             = 1.5,   # put/call volume ratio above this is flagged
  pc_low              = 0.35   # ...or below this
)
RSI_ALERTS <- c(low = 30, high = 70)

# -----------------------------------------------------------------------------
#  Alert rules live in inputs/alerts.csv (edit them there or with the Rules
#  editor on the Watchlist tab, which downloads a new alerts.csv).
#  Columns: id, enabled (Y/N), scope (symbol | market | portfolio), target
#  (symbol scope only: a ticker, * for every equity, detail for detail names,
#  sector:<name>), metric, op (> < >= <= abs> crosses_above crosses_below),
#  value (a number, or sma50 / sma200 for crosses), severity (critical |
#  serious | warning | info), note (shown in the alert).
# -----------------------------------------------------------------------------
# The per-row alert columns in watchlist.csv (alert_above, alert_move_pct, ...)
# apply to: "detail" (only detail = Y rows), "all", or "none". The rules file
# covers the broad watchlist with sane thresholds; +/-4% on 500 names is noise.
WATCHLIST_ROW_ALERTS <- "detail"
# Market metrics a rule can name. Suffix .d1 / .w1 / .m1 / .ytd for the change
# (bp for yields and spreads, points for VIX / MOVE, % for prices).
ALERT_MARKET_METRICS <- list(
  ust2y   = list(src = "fred", key = "DGS2",   unit = "yield", label = "UST 2Y yield (%)"),
  ust5y   = list(src = "fred", key = "DGS5",   unit = "yield", label = "UST 5Y yield (%)"),
  ust10y  = list(src = "fred", key = "DGS10",  unit = "yield", label = "UST 10Y yield (%)"),
  ust30y  = list(src = "fred", key = "DGS30",  unit = "yield", label = "UST 30Y yield (%)"),
  "2s10s" = list(src = "derived", key = "2s10s", unit = "bp", label = "2s10s curve (bp)"),
  "5s30s" = list(src = "derived", key = "5s30s", unit = "bp", label = "5s30s curve (bp)"),
  "3m10y" = list(src = "derived", key = "3m10y", unit = "bp", label = "3m10y curve (bp)"),
  ig_oas  = list(src = "fred", key = "BAMLC0A0CM",   unit = "bp", label = "US IG OAS (bp)"),
  ig_bbb  = list(src = "fred", key = "BAMLC0A4CBBB", unit = "bp", label = "IG BBB OAS (bp)"),
  hy_oas  = list(src = "fred", key = "BAMLH0A0HYM2", unit = "bp", label = "US HY OAS (bp)"),
  hy_bb   = list(src = "fred", key = "BAMLH0A1HYBB", unit = "bp", label = "HY BB OAS (bp)"),
  hy_ccc  = list(src = "fred", key = "BAMLH0A3HYC",  unit = "bp", label = "HY CCC OAS (bp)"),
  sofr    = list(src = "fred", key = "SOFR",   unit = "yield", label = "SOFR (%)"),
  effr    = list(src = "fred", key = "EFFR",   unit = "yield", label = "EFFR (%)"),
  bkeven10 = list(src = "fred", key = "T10YIE", unit = "yield", label = "10Y breakeven (%)"),
  vix     = list(src = "yahoo", key = "^VIX",  unit = "level", label = "VIX"),
  move    = list(src = "yahoo", key = "^MOVE", unit = "level", label = "MOVE"),
  spx_fut = list(src = "yahoo", key = "ES=F",  unit = "px", label = "S&P 500 futures"),
  nq_fut  = list(src = "yahoo", key = "NQ=F",  unit = "px", label = "Nasdaq 100 futures"),
  dxy     = list(src = "yahoo", key = "DX-Y.NYB", unit = "px", label = "US dollar index"),
  eurusd  = list(src = "yahoo", key = "EURUSD=X", unit = "px", label = "EUR/USD"),
  usdjpy  = list(src = "yahoo", key = "USDJPY=X", unit = "px", label = "USD/JPY"),
  wti     = list(src = "yahoo", key = "CL=F",  unit = "px", label = "WTI crude"),
  gold    = list(src = "yahoo", key = "GC=F",  unit = "px", label = "Gold"),
  tlt     = list(src = "yahoo", key = "TLT",   unit = "px", label = "TLT (20Y+ UST ETF)"),
  lqd     = list(src = "yahoo", key = "LQD",   unit = "px", label = "LQD (IG ETF)"),
  hyg     = list(src = "yahoo", key = "HYG",   unit = "px", label = "HYG (HY ETF)"),
  health_score = list(src = "health", key = "score", unit = "level", label = "Market health score (0-100)")
)
# -----------------------------------------------------------------------------
#  Whole-market snapshot (Market tab): every US-listed common stock, once a day,
#  from Nasdaq's screener plus Yahoo batch quotes. No candles for these; the
#  watchlist keeps the charts. Set enabled = FALSE to skip it.
# -----------------------------------------------------------------------------
MARKET_UNIVERSE <- list(
  enabled = TRUE,
  intraday = FALSE,              # TRUE also refreshes the snapshot on intraday runs (~30 Yahoo calls)
  include_etfs = FALSE,
  min_price = 1,                 # drop sub-$1 names
  min_market_cap = 50e6,         # drop sub-$50M names
  mover_min_dollar_volume = 5e6, # a mover needs at least this much traded today
  volume_min_market_cap = 300e6,
  highlow_min_market_cap = 2e9,
  movers_n = 10,
  quote_batch = 200, quote_pause = 0.5
)
# Market-wide alerts. kind: move | volume | high | low; the cap and dollar-volume
# floors keep penny-stock noise out. max_n caps how many fire per rule.
MARKET_ALERT_RULES <- list(
  list(kind = "move",   threshold = 15, min_market_cap = 1e9,  min_dollar_volume = 20e6, severity = "serious", max_n = 10, note = "Large move outside the watchlist"),
  list(kind = "move",   threshold = 8,  min_market_cap = 20e9, min_dollar_volume = 50e6, severity = "warning", max_n = 10),
  list(kind = "volume", threshold = 5,  min_market_cap = 2e9,  min_dollar_volume = 20e6, severity = "warning", max_n = 8),
  list(kind = "high",   min_market_cap = 50e9, severity = "info", max_n = 8),
  list(kind = "low",    min_market_cap = 50e9, severity = "info", max_n = 8)
)

# Desktop notification when a new alert appears (Windows toast, no setup).
TOAST_ALERTS <- TRUE
TOAST_MIN_SEVERITY <- "warning"     # critical | serious | warning | info
TOAST_REPEAT_HOURS <- 12            # the same alert is not toasted again within this window

# Economic releases shown on the calendar when a FRED API key is configured
CALENDAR_RELEASES <- c("Consumer Price Index", "Employment Situation",
                       "Personal Income and Outlays", "Gross Domestic Product",
                       "Advance Monthly Sales for Retail and Food Services",
                       "Producer Price Index", "FOMC Press Release",
                       "Employment Cost Index", "Consumer Confidence")
