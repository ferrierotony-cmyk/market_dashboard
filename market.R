# =============================================================================
#  market.R - the whole US equity market as a daily snapshot (no candles).
#
#  Universe + day change + sector + market cap: Nasdaq's screener API, one call
#  for every listed stock (NYSE, Nasdaq, AMEX). Fallback: the Nasdaq Trader
#  symbol directories (names only).
#  52-week range, 50/200-day averages, average volume: Yahoo's batch quote
#  endpoint, ~200 symbols per call, which needs a session cookie + crumb.
#  Everything is cached in data/market_universe.json and the build falls back
#  to the cache when a source is down.
# =============================================================================

CAP_BUCKETS <- c(mega = 200e9, large = 10e9, mid = 2e9, small = 300e6, micro = 0)
cap_bucket <- function(mcap) {
  out <- rep(NA_character_, length(mcap))
  for (b in names(CAP_BUCKETS)) out[is.na(out) & !is.na(mcap) & mcap >= CAP_BUCKETS[[b]]] <- b
  out
}
num_clean <- function(x) suppressWarnings(as.numeric(gsub("[$,%\\s]", "", as.character(x))))

# ---- HTTP with headers (curl); falls back to download.file ---------------------------
http_get_headers <- function(url, dest, headers = NULL, handle = NULL, tries = 2, pause = 2) {
  if (!requireNamespace("curl", quietly = TRUE)) return(http_get_file(url, dest, tries = tries, pause = pause))
  for (i in seq_len(tries)) {
    h <- if (is.null(handle)) curl::new_handle(useragent = UA, followlocation = TRUE, timeout = 60) else handle
    if (length(headers)) curl::handle_setheaders(h, .list = as.list(headers))
    ok <- tryCatch({
      r <- curl::curl_fetch_memory(url, handle = h)
      if (r$status_code == 200 && length(r$content) > 0) { writeBin(r$content, dest); TRUE } else { logmsg("  HTTP ", r$status_code, " for ", sub("\\?.*", "", url)); FALSE }
    }, error = function(e) { logmsg("  ", conditionMessage(e), " for ", sub("\\?.*", "", url)); FALSE })
    if (ok) return(TRUE)
    Sys.sleep(pause * i)
  }
  FALSE
}

# ---- Nasdaq screener: the whole listed universe in one call ---------------------------
parse_nasdaq_screener <- function(path) {
  j <- jsonlite::fromJSON(path)
  rows <- j$data$rows
  if (is.null(rows)) rows <- j$data$table$rows
  if (!is.data.frame(rows) || !nrow(rows)) stop("no rows")
  col <- function(nm) if (!is.null(rows[[nm]])) as.character(rows[[nm]]) else rep("", nrow(rows))
  data.frame(symbol = trimws(col("symbol")), name = trimws(col("name")), last = num_clean(col("lastsale")),
             chg_pct = num_clean(col("pctchange")), volume = num_clean(col("volume")), mcap = num_clean(col("marketCap")),
             sector = trimws(col("sector")), industry = trimws(col("industry")), country = trimws(col("country")),
             stringsAsFactors = FALSE)[nzchar(trimws(col("symbol"))), ]
}
nasdaq_screener <- function(cache_dir, cache_only = FALSE) {
  url <- "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=10000&offset=0&download=true"
  cache <- file.path(cache_dir, "nasdaq_screener.json")
  if (!cache_only) {
    tmp <- tempfile(fileext = ".json")
    if (http_get_headers(url, tmp, headers = c(Accept = "application/json, text/plain, */*", "Accept-Language" = "en-US,en;q=0.9",
                                                Origin = "https://www.nasdaq.com", Referer = "https://www.nasdaq.com/market-activity/stocks/screener"))) {
      p <- tryCatch(parse_nasdaq_screener(tmp), error = function(e) { logmsg("  Nasdaq screener parse: ", conditionMessage(e)); NULL })
      if (!is.null(p)) { file.copy(tmp, cache, overwrite = TRUE); return(list(data = p, mode = "fetched")) }
    }
  }
  if (file.exists(cache)) { p <- tryCatch(parse_nasdaq_screener(cache), error = function(e) NULL); if (!is.null(p)) return(list(data = p, mode = if (cache_only) "cache-by-design" else "cache-fallback")) }
  list(data = NULL, mode = "failed")
}

# ---- Nasdaq Trader symbol directories (fallback universe, names only) --------------------
parse_symdir <- function(path, sym_col, etf_col = "ETF", test_col = "Test Issue") {
  x <- utils::read.delim(path, sep = "|", stringsAsFactors = FALSE, quote = "", check.names = FALSE)
  x <- x[!grepl("^File Creation Time", x[[1]]), ]
  if (is.null(x[[sym_col]])) stop("unexpected layout")
  data.frame(symbol = trimws(x[[sym_col]]), name = trimws(x[["Security Name"]]),
             etf = toupper(trimws(x[[etf_col]] %||% "N")) == "Y", test = toupper(trimws(x[[test_col]] %||% "N")) == "Y", stringsAsFactors = FALSE)
}
nasdaq_symdir <- function(cache_dir, cache_only = FALSE) {
  out <- NULL; modes <- character(0)
  for (f in c("nasdaqlisted", "otherlisted")) {
    url <- sprintf("https://www.nasdaqtrader.com/dynamic/symdir/%s.txt", f)
    sc <- if (f == "nasdaqlisted") "Symbol" else "ACT Symbol"
    r <- cached_fetch(url, file.path(cache_dir, paste0("symdir_", f, ".txt")), function(p) parse_symdir(p, sc), cache_only)
    modes <- c(modes, r$mode); if (!is.null(r$data)) out <- rbind(out, r$data)
  }
  list(data = out, mode = if (all(modes == "failed")) "failed" else if (any(modes == "fetched")) "fetched" else modes[modes != "failed"][1])
}

# ---- Yahoo batch quotes (cookie + crumb) ------------------------------------------------
yahoo_symbol <- function(s) gsub("[./]", "-", s)      # BRK.A / BRK/A -> BRK-A
yahoo_quote_batch <- function(symbols, batch = 200, pause = 0.5) {
  if (!requireNamespace("curl", quietly = TRUE)) { logmsg("  Yahoo quotes need the curl package"); return(NULL) }
  h <- curl::new_handle(useragent = UA, followlocation = TRUE, timeout = 60, cookiefile = "")   # in-memory cookie jar
  curl::handle_setheaders(h, Accept = "*/*", "Accept-Language" = "en-US,en;q=0.9")
  crumb <- tryCatch({
    curl::curl_fetch_memory("https://fc.yahoo.com/", handle = h)   # 404, but it sets the session cookie
    r <- curl::curl_fetch_memory("https://query2.finance.yahoo.com/v1/test/getcrumb", handle = h)
    if (r$status_code != 200) stop("crumb HTTP ", r$status_code)
    trimws(rawToChar(r$content))
  }, error = function(e) { logmsg("  Yahoo crumb failed: ", conditionMessage(e)); "" })
  if (!nzchar(crumb) || grepl("[<{]", crumb)) { logmsg("  Yahoo quotes: no crumb (consent wall or block); 52-week data will be missing"); return(NULL) }
  fields <- paste(c("symbol", "shortName", "regularMarketPrice", "regularMarketChangePercent", "regularMarketPreviousClose",
                    "regularMarketVolume", "averageDailyVolume3Month", "fiftyTwoWeekHigh", "fiftyTwoWeekLow", "fiftyDayAverage",
                    "twoHundredDayAverage", "marketCap", "fullExchangeName", "quoteType", "regularMarketTime"), collapse = ",")
  out <- list(); n_fail <- 0
  chunks <- split(symbols, ceiling(seq_along(symbols) / batch))
  for (ch in chunks) {
    url <- sprintf("https://query2.finance.yahoo.com/v7/finance/quote?symbols=%s&fields=%s&formatted=false&crumb=%s",
                   paste(vapply(ch, utils::URLencode, "", reserved = TRUE), collapse = ","), fields, utils::URLencode(crumb, reserved = TRUE))
    r <- tryCatch(curl::curl_fetch_memory(url, handle = h), error = function(e) NULL)
    if (is.null(r) || r$status_code != 200) { n_fail <- n_fail + 1; if (!is.null(r) && r$status_code %in% c(401, 403, 429)) { logmsg("  Yahoo quotes HTTP ", r$status_code, ", stopping"); break }; Sys.sleep(pause * 4); next }
    j <- tryCatch(jsonlite::fromJSON(rawToChar(r$content)), error = function(e) NULL)
    q <- j$quoteResponse$result
    if (is.data.frame(q) && nrow(q)) {
      g <- function(nm) if (!is.null(q[[nm]])) q[[nm]] else rep(NA, nrow(q))
      out[[length(out) + 1]] <- data.frame(ysymbol = as.character(g("symbol")), yname = as.character(g("shortName")),
                                           last = as.numeric(g("regularMarketPrice")), chg_pct = as.numeric(g("regularMarketChangePercent")),
                                           prev = as.numeric(g("regularMarketPreviousClose")), volume = as.numeric(g("regularMarketVolume")),
                                           avg_vol = as.numeric(g("averageDailyVolume3Month")), hi52 = as.numeric(g("fiftyTwoWeekHigh")),
                                           lo52 = as.numeric(g("fiftyTwoWeekLow")), sma50 = as.numeric(g("fiftyDayAverage")),
                                           sma200 = as.numeric(g("twoHundredDayAverage")), mcap = as.numeric(g("marketCap")),
                                           exchange = as.character(g("fullExchangeName")), qtype = as.character(g("quoteType")),
                                           qtime = as.numeric(g("regularMarketTime")), stringsAsFactors = FALSE)
    }
    Sys.sleep(pause)
  }
  if (n_fail) logmsg("  Yahoo quotes: ", n_fail, " of ", length(chunks), " batches failed")
  if (length(out)) do.call(rbind, out) else NULL
}

# ---- universe assembly -----------------------------------------------------------------
# Common stock only: no warrants, rights, units, preferreds, notes or test issues.
is_common <- function(symbol, name) {
  bad_sym <- grepl("[\\^]|\\.(U|W|WS|R|RT|UN|P[A-Z]?)$|[-/](W|WS|U|R|P[A-Z]?)$", symbol)
  bad_name <- grepl("warrant|\\bright(s)?\\b|\\bunit(s)?\\b|preferred|depositary|\\bnotes?\\b|debenture|% |trust preferred|subordinated|perpetual",
                    name, ignore.case = TRUE)
  !bad_sym & !bad_name
}

market_fetch <- function(cfg, cache_dir, run_mode = "morning") {
  u <- cfg$MARKET_UNIVERSE
  if (!isTRUE(u$enabled)) return(list(data = NULL, mode = "disabled", source = "", asof = NA))
  cache <- file.path(cache_dir, "market_universe.json")
  read_cache <- function(mode) {
    if (!file.exists(cache)) return(list(data = NULL, mode = "failed", source = "", asof = NA))
    j <- tryCatch(jsonlite::fromJSON(cache), error = function(e) NULL)
    if (is.null(j) || !is.data.frame(j$rows) || !nrow(j$rows)) return(list(data = NULL, mode = "failed", source = "", asof = NA))
    list(data = j$rows, mode = mode, source = j$source %||% "cache", asof = j$asof %||% NA)
  }
  intraday <- identical(run_mode, "intraday")
  if (intraday && !isTRUE(u$intraday)) return(read_cache("cache-by-design"))

  logmsg("Market universe: Nasdaq screener")
  sc <- nasdaq_screener(cache_dir)
  uni <- sc$data; source <- "Nasdaq screener"
  if (is.null(uni)) {
    logmsg("  screener unavailable, trying the symbol directory")
    sd <- nasdaq_symdir(cache_dir)
    if (!is.null(sd$data)) {
      d <- sd$data[!sd$data$test & (isTRUE(u$include_etfs) | !sd$data$etf), ]
      uni <- data.frame(symbol = d$symbol, name = d$name, last = NA_real_, chg_pct = NA_real_, volume = NA_real_, mcap = NA_real_,
                        sector = "", industry = "", country = "", stringsAsFactors = FALSE)
      source <- "Nasdaq symbol directory"
    }
  }
  if (is.null(uni)) { logmsg("  no universe source reachable, using cache"); return(read_cache("cache-fallback")) }
  uni <- uni[!duplicated(uni$symbol) & is_common(uni$symbol, uni$name), ]
  n_raw <- nrow(uni)
  logmsg("  ", n_raw, " common stocks from ", source)

  syms <- yahoo_symbol(uni$symbol)
  logmsg("Market universe: Yahoo quotes for ", length(syms), " symbols in batches of ", u$quote_batch %||% 200)
  q <- yahoo_quote_batch(syms, batch = u$quote_batch %||% 200, pause = u$quote_pause %||% 0.5)
  if (!is.null(q)) {
    m <- match(syms, q$ysymbol); hit <- !is.na(m)
    logmsg("  ", sum(hit), " of ", length(syms), " quoted")
    fill <- function(a, b) { a[is.na(a) & !is.na(b)] <- b[is.na(a) & !is.na(b)]; a }
    uni$last <- fill(q$last[m], uni$last); uni$last[hit] <- ifelse(is.na(q$last[m[hit]]), uni$last[hit], q$last[m[hit]])
    uni$chg_pct[hit] <- ifelse(is.na(q$chg_pct[m[hit]]), uni$chg_pct[hit], q$chg_pct[m[hit]])
    uni$volume[hit] <- ifelse(is.na(q$volume[m[hit]]), uni$volume[hit], q$volume[m[hit]])
    uni$mcap[hit] <- ifelse(is.na(q$mcap[m[hit]]), uni$mcap[hit], q$mcap[m[hit]])
    for (k in c("prev", "avg_vol", "hi52", "lo52", "sma50", "sma200", "exchange", "qtype")) uni[[k]] <- q[[k]][m]
    uni$qtime <- q$qtime[m]
    uni$name[hit & !nzchar(uni$name)] <- q$yname[m[hit & !nzchar(uni$name)]]
    if (!isTRUE(u$include_etfs)) uni <- uni[is.na(uni$qtype) | uni$qtype %in% c("EQUITY", ""), ]
  } else {
    for (k in c("prev", "avg_vol", "hi52", "lo52", "sma50", "sma200")) uni[[k]] <- NA_real_
    uni$exchange <- ""; uni$qtype <- ""; uni$qtime <- NA_real_
  }
  asof <- if (any(!is.na(uni$qtime))) format(as.POSIXct(max(uni$qtime, na.rm = TRUE), origin = "1970-01-01", tz = "America/New_York"), "%Y-%m-%d %H:%M %Z") else format(Sys.time(), "%Y-%m-%d %H:%M")
  jsonlite::write_json(list(asof = asof, source = source, rows = uni), cache, na = "null", digits = 6)
  list(data = uni, mode = "fetched", source = source, asof = asof)
}

# ---- analytics ---------------------------------------------------------------------------
market_compute <- function(cfg, uni, watch_syms = character(0)) {
  if (is.null(uni) || !nrow(uni)) return(NULL)
  u <- cfg$MARKET_UNIVERSE
  d <- uni
  d$dollar_vol <- d$last * d$volume
  keep <- !is.na(d$last) & d$last >= (u$min_price %||% 1) & (is.na(d$mcap) | d$mcap >= (u$min_market_cap %||% 0))
  d <- d[keep, ]
  if (!nrow(d)) return(NULL)
  d$vol_x <- ifelse(!is.na(d$avg_vol) & d$avg_vol > 0, d$volume / d$avg_vol, NA_real_)
  d$pos52 <- ifelse(!is.na(d$hi52) & !is.na(d$lo52) & d$hi52 > d$lo52, 100 * (d$last - d$lo52) / (d$hi52 - d$lo52), NA_real_)
  d$vs50 <- ifelse(!is.na(d$sma50) & d$sma50 > 0, 100 * (d$last / d$sma50 - 1), NA_real_)
  d$vs200 <- ifelse(!is.na(d$sma200) & d$sma200 > 0, 100 * (d$last / d$sma200 - 1), NA_real_)
  d$new_high <- !is.na(d$hi52) & d$last >= d$hi52 * 0.999
  d$new_low <- !is.na(d$lo52) & d$last <= d$lo52 * 1.001
  d$bucket <- cap_bucket(d$mcap)
  d$sector[is.na(d$sector) | !nzchar(d$sector)] <- "Unclassified"
  d$in_watch <- d$symbol %in% watch_syms | yahoo_symbol(d$symbol) %in% watch_syms
  liquid <- !is.na(d$dollar_vol) & d$dollar_vol >= (u$mover_min_dollar_volume %||% 5e6)
  ok_chg <- !is.na(d$chg_pct)

  # breadth ---------------------------------------------------------------------------------
  pct <- function(x) if (any(!is.na(x))) 100 * mean(x, na.rm = TRUE) else NA_real_
  breadth <- list(n = nrow(d), up = sum(d$chg_pct > 0, na.rm = TRUE), down = sum(d$chg_pct < 0, na.rm = TRUE),
                  unch = sum(d$chg_pct == 0, na.rm = TRUE), median = stats::median(d$chg_pct, na.rm = TRUE),
                  cap_wtd = if (any(!is.na(d$mcap) & ok_chg)) sum((d$mcap * d$chg_pct)[!is.na(d$mcap) & ok_chg]) / sum(d$mcap[!is.na(d$mcap) & ok_chg]) else NA_real_,
                  above50 = pct(d$vs50 > 0), above200 = pct(d$vs200 > 0),
                  new_highs = sum(d$new_high), new_lows = sum(d$new_low),
                  up_dollar = sum(d$dollar_vol[ok_chg & d$chg_pct > 0], na.rm = TRUE), down_dollar = sum(d$dollar_vol[ok_chg & d$chg_pct < 0], na.rm = TRUE),
                  big_up = sum(d$chg_pct >= 10, na.rm = TRUE), big_down = sum(d$chg_pct <= -10, na.rm = TRUE))
  caps <- lapply(names(CAP_BUCKETS), function(b) {
    s <- d[!is.na(d$bucket) & d$bucket == b, ]; if (!nrow(s)) return(NULL)
    list(bucket = b, n = nrow(s), up = sum(s$chg_pct > 0, na.rm = TRUE), down = sum(s$chg_pct < 0, na.rm = TRUE),
         avg = mean(s$chg_pct, na.rm = TRUE), median = stats::median(s$chg_pct, na.rm = TRUE), above200 = pct(s$vs200 > 0),
         new_highs = sum(s$new_high), new_lows = sum(s$new_low))
  })
  caps <- Filter(Negate(is.null), caps)
  sectors <- lapply(sort(unique(d$sector)), function(sc) {
    s <- d[d$sector == sc & ok_chg, ]; if (!nrow(s)) return(NULL)
    sl <- s[liquid[d$sector == sc & ok_chg], ]; if (!nrow(sl)) sl <- s
    cw <- if (any(!is.na(s$mcap))) sum((s$mcap * s$chg_pct)[!is.na(s$mcap)]) / sum(s$mcap[!is.na(s$mcap)]) else NA_real_
    list(sector = sc, n = nrow(s), avg = mean(s$chg_pct), cap_wtd = cw, median = stats::median(s$chg_pct),
         up = sum(s$chg_pct > 0), down = sum(s$chg_pct < 0), above200 = pct(s$vs200 > 0),
         best = sl[which.max(sl$chg_pct), c("symbol", "name", "chg_pct")], worst = sl[which.min(sl$chg_pct), c("symbol", "name", "chg_pct")],
         mcap = sum(s$mcap, na.rm = TRUE))
  })
  sectors <- Filter(Negate(is.null), sectors)
  sectors <- sectors[order(-vapply(sectors, function(s) if (is.na(s$cap_wtd)) s$avg else s$cap_wtd, 0))]

  # movers by size, unusual volume, 52-week lists ------------------------------------------
  top <- function(rows, n, decreasing = TRUE) { rows <- rows[!is.na(rows$chg_pct), ]; rows[utils::head(order(rows$chg_pct, decreasing = decreasing), n), ] }
  big <- d[liquid & !is.na(d$bucket) & d$bucket %in% c("mega", "large"), ]
  mid <- d[liquid & !is.na(d$bucket) & d$bucket == "mid", ]
  small <- d[liquid & !is.na(d$bucket) & d$bucket %in% c("small", "micro"), ]
  nmov <- u$movers_n %||% 10
  movers <- list(large = list(up = top(big, nmov), down = top(big, nmov, FALSE)),
                 mid = list(up = top(mid, nmov), down = top(mid, nmov, FALSE)),
                 small = list(up = top(small, nmov), down = top(small, nmov, FALSE)))
  vol <- d[liquid & !is.na(d$vol_x) & !is.na(d$mcap) & d$mcap >= (u$volume_min_market_cap %||% 300e6), ]
  vol <- vol[utils::head(order(-vol$vol_x), 15), ]
  hl_min <- u$highlow_min_market_cap %||% 2e9
  highs <- d[d$new_high & !is.na(d$mcap) & d$mcap >= hl_min, ]; highs <- highs[utils::head(order(-highs$mcap), 15), ]
  lows <- d[d$new_low & !is.na(d$mcap) & d$mcap >= hl_min, ]; lows <- lows[utils::head(order(-lows$mcap), 15), ]

  # market-wide alerts ------------------------------------------------------------------------
  alerts <- list(); now <- Sys.time()
  add <- function(sev, sym, msg, key) alerts[[length(alerts) + 1]] <<- data.frame(severity = sev, category = "Market", symbol = sym, message = msg,
                                                                                   time = format(now, "%d %b %H:%M"), ts = as.numeric(now), key = key, stringsAsFactors = FALSE)
  for (r in cfg$MARKET_ALERT_RULES) {
    s <- d[ok_chg & !is.na(d$mcap) & d$mcap >= (r$min_market_cap %||% 0) & !is.na(d$dollar_vol) & d$dollar_vol >= (r$min_dollar_volume %||% 0), ]
    hit <- switch(r$kind,
                  move = s[abs(s$chg_pct) >= r$threshold, ],
                  volume = s[!is.na(s$vol_x) & s$vol_x >= r$threshold, ],
                  high = s[s$new_high, ], low = s[s$new_low, ], s[0, ])
    if (!nrow(hit)) next
    hit <- hit[utils::head(order(-abs(hit$chg_pct)), r$max_n %||% 10), ]
    for (i in seq_len(nrow(hit))) {
      h <- hit[i, ]
      msg <- switch(r$kind,
                    move = sprintf("%s (%s) %+.1f%% today, $%s cap, $%sM traded%s", h$name, h$symbol, h$chg_pct, fmt_cap(h$mcap), format(round(h$dollar_vol / 1e6), big.mark = ","),
                                   if (!is.na(h$vol_x)) sprintf(", %.1fx volume", h$vol_x) else ""),
                    volume = sprintf("%s (%s) volume %.1fx its 3-month average (%+.1f%% today)", h$name, h$symbol, h$vol_x, h$chg_pct),
                    high = sprintf("%s (%s) at a 52-week high (%+.1f%% today)", h$name, h$symbol, h$chg_pct),
                    low = sprintf("%s (%s) at a 52-week low (%+.1f%% today)", h$name, h$symbol, h$chg_pct))
      add(r$severity, h$symbol, paste0(msg, if (nzchar(r$note %||% "")) paste0(". ", r$note) else ""), paste0("mkt_", r$kind, "|", h$symbol))
    }
  }
  list(rows = d, breadth = breadth, caps = caps, sectors = sectors, movers = movers, volume = vol, highs = highs, lows = lows,
       alerts = if (length(alerts)) do.call(rbind, alerts) else NULL, n_raw = nrow(uni), n_kept = nrow(d))
}
fmt_cap <- function(x) ifelse(is.na(x), "n/a", ifelse(x >= 1e12, sprintf("%.2fT", x / 1e12), ifelse(x >= 1e9, sprintf("%.1fB", x / 1e9), sprintf("%.0fM", x / 1e6))))
