# =============================================================================
#  fetch_data.R - pull market data from free sources, with caching + retries
#
#  Sources (no Bloomberg terminal needed):
#    FRED (St. Louis Fed)  Treasury par curve, ICE BofA OAS, SOFR/EFFR, macro.
#    Treasury.gov          same-day par curve XML (tops up FRED).
#    Yahoo Finance         daily + intraday OHLCV, news headlines.
#    Cboe                  delayed option chains (volume, open interest, IV).
#    Bloomberg (optional)  comps refresh when USE_BLOOMBERG = TRUE.
#
#  Every download is cached in data/. If a source is down, the cache is used
#  and the dashboard flags it. In "intraday" mode slow-moving sources (FRED,
#  Treasury, weekly candles) are read from cache by design.
# =============================================================================

`%||%` <- function(a, b) if (is.null(a) || length(a) == 0 || all(is.na(a))) b else a

UA <- "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"

LOG_FILE <- NULL
logmsg <- function(...) {
  msg <- sprintf("[%s] %s", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), paste0(..., collapse = ""))
  cat(msg, "\n")
  if (!is.null(LOG_FILE)) cat(msg, "\n", file = LOG_FILE, append = TRUE)
  invisible(msg)
}

# Download a URL to a file. Retries with back-off; returns TRUE on success.
# Attempt 1 uses R's default identity (FRED rejects a browser-style UA over
# HTTP/2); later attempts switch to a browser-style UA.
http_get_file <- function(url, dest, tries = 3, pause = 2) {
  for (i in seq_len(tries)) {
    old <- options(HTTPUserAgent = if (i == 1) getOption("HTTPUserAgent") else UA)
    ok <- tryCatch({
      status <- suppressWarnings(utils::download.file(url, dest, method = "libcurl",
                                                      quiet = TRUE, mode = "wb"))
      status == 0 && file.exists(dest) && file.size(dest) > 0
    }, error = function(e) FALSE)
    options(old)
    if (ok) return(TRUE)
    Sys.sleep(pause * i)
  }
  FALSE
}

# Fetch -> parse -> cache, falling back to the cached copy.
# mode in result: fetched | cache-fallback | cache-by-design | failed
cached_fetch <- function(url, cache, parse, cache_only = FALSE, tries = 3) {
  if (!cache_only) {
    tmp <- tempfile()
    if (http_get_file(url, tmp, tries = tries)) {
      p <- tryCatch(parse(tmp), error = function(e) NULL)
      if (!is.null(p)) {
        file.copy(tmp, cache, overwrite = TRUE); unlink(tmp)
        return(list(data = p, mode = "fetched"))
      }
    }
  }
  if (file.exists(cache)) {
    p <- tryCatch(parse(cache), error = function(e) NULL)
    if (!is.null(p)) return(list(data = p, mode = if (cache_only) "cache-by-design" else "cache-fallback"))
  }
  list(data = NULL, mode = "failed")
}

safe_name <- function(x) gsub("[^A-Za-z0-9]", "_", x)

# ----------------------------------------------------------------------------
#  FRED
# ----------------------------------------------------------------------------
parse_fred_csv <- function(path) {
  x <- utils::read.csv(path, stringsAsFactors = FALSE, na.strings = c(".", "", "NA"))
  if (ncol(x) < 2) stop("unexpected FRED csv layout")
  names(x)[1:2] <- c("date", "value")
  x$date  <- as.Date(x$date)
  x$value <- suppressWarnings(as.numeric(x$value))
  x <- x[!is.na(x$date) & !is.na(x$value), c("date", "value")]
  if (!nrow(x)) stop("empty series")
  x[order(x$date), ]
}

fred_get_series <- function(id, cache_dir, start_date, cache_only = FALSE) {
  url <- sprintf("https://fred.stlouisfed.org/graph/fredgraph.csv?id=%s&cosd=%s", id, format(start_date))
  cached_fetch(url, file.path(cache_dir, paste0("fred_", id, ".csv")), parse_fred_csv, cache_only)
}

# FRED frequency -> latency wording for the provenance table
FRED_LATENCY <- c(CPIAUCSL = "Monthly", CPILFESL = "Monthly", PCEPILFE = "Monthly", UNRATE = "Monthly",
                  PAYEMS = "Monthly", A191RL1Q225SBEA = "Quarterly", ICSA = "Weekly", RSAFS = "Monthly",
                  NFCI = "Weekly", WALCL = "Weekly", MORTGAGE30US = "Weekly")

# ----------------------------------------------------------------------------
#  Treasury.gov daily par yield curve (XML feed, one month per call)
# ----------------------------------------------------------------------------
TREASURY_TENOR_MAP <- c(BC_1MONTH = "DGS1MO", BC_3MONTH = "DGS3MO", BC_6MONTH = "DGS6MO",
                        BC_1YEAR = "DGS1", BC_2YEAR = "DGS2", BC_3YEAR = "DGS3",
                        BC_5YEAR = "DGS5", BC_7YEAR = "DGS7", BC_10YEAR = "DGS10",
                        BC_20YEAR = "DGS20", BC_30YEAR = "DGS30")

parse_treasury_xml <- function(path) {
  doc   <- xml2::read_xml(path)
  props <- xml2::xml_find_all(doc, "//*[local-name()='properties']")
  if (length(props) == 0) stop("no rows")
  rows <- lapply(props, function(p) {
    kids <- xml2::xml_children(p)
    v <- xml2::xml_text(kids); names(v) <- xml2::xml_name(kids); v
  })
  keep <- c("NEW_DATE", names(TREASURY_TENOR_MAP))
  rows <- lapply(rows, function(v) { out <- v[keep]; names(out) <- keep; out })
  df <- as.data.frame(do.call(rbind, rows), stringsAsFactors = FALSE)
  df$date <- as.Date(substr(df$NEW_DATE, 1, 10))
  for (k in names(TREASURY_TENOR_MAP)) df[[k]] <- suppressWarnings(as.numeric(df[[k]]))
  df[!is.na(df$date), c("date", names(TREASURY_TENOR_MAP))]
}

treasury_get_curve <- function(cache_dir, cache_only = FALSE) {
  months <- unique(c(format(Sys.Date() - 28, "%Y%m"), format(Sys.Date(), "%Y%m")))
  out <- NULL; modes <- character(0)
  for (m in months) {
    url <- paste0("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml",
                  "?data=daily_treasury_yield_curve&field_tdr_date_value_month=", m)
    r <- cached_fetch(url, file.path(cache_dir, paste0("treasury_", m, ".xml")), parse_treasury_xml, cache_only)
    modes <- c(modes, r$mode)
    if (!is.null(r$data)) out <- rbind(out, r$data)
  }
  if (!is.null(out)) { out <- out[!duplicated(out$date), ]; out <- out[order(out$date), ] }
  mode <- if (all(modes == "failed")) "failed" else if (any(modes == "fetched")) "fetched" else modes[modes != "failed"][1]
  list(data = out, mode = mode)
}

# ----------------------------------------------------------------------------
#  Yahoo Finance chart endpoint: OHLCV for any range / interval
# ----------------------------------------------------------------------------
parse_yahoo_chart <- function(path) {
  j <- jsonlite::fromJSON(path, simplifyVector = FALSE)
  r <- j$chart$result[[1]]
  if (is.null(r)) stop("no result")
  meta <- r$meta
  num <- function(x) if (is.null(x) || !length(x)) numeric(0) else
    vapply(x, function(v) if (is.null(v)) NA_real_ else as.numeric(v), numeric(1))
  ts <- num(r$timestamp)
  q  <- r$indicators$quote[[1]]
  n  <- length(ts)
  pad <- function(x) { x <- num(x); if (length(x) != n) rep(NA_real_, n) else x }
  df <- data.frame(t = ts, o = pad(q$open), h = pad(q$high), l = pad(q$low), c = pad(q$close), v = pad(q$volume))
  adj <- r$indicators$adjclose
  df$a <- if (!is.null(adj) && length(adj)) pad(adj[[1]]$adjclose) else df$c
  df$a[is.na(df$a)] <- df$c[is.na(df$a)]
  df <- df[!is.na(df$c) & !is.na(df$t), ]
  if (!nrow(df)) stop("no bars")
  for (k in c("o", "h", "l")) df[[k]][is.na(df[[k]])] <- df$c[is.na(df[[k]])]
  df$v[is.na(df$v)] <- 0
  tz <- meta$exchangeTimezoneName %||% "America/New_York"
  list(symbol = meta$symbol %||% "", name = meta$shortName %||% meta$longName %||% meta$symbol %||% "",
       currency = meta$currency %||% "", exchange = meta$fullExchangeName %||% meta$exchangeName %||% "",
       instrument = meta$instrumentType %||% "", tz = tz, gmtoffset = as.numeric(meta$gmtoffset %||% 0),
       delay_min = as.numeric(meta$exchangeDataDelayedBy %||% NA),
       last = as.numeric(meta$regularMarketPrice %||% df$c[nrow(df)]),
       market_time = as.POSIXct(as.numeric(meta$regularMarketTime %||% df$t[nrow(df)]),
                                origin = "1970-01-01", tz = tz),
       bars = df)
}

yahoo_chart <- function(symbol, range, interval, cache_dir, cache_only = FALSE) {
  url <- sprintf("https://query1.finance.yahoo.com/v8/finance/chart/%s?range=%s&interval=%s",
                 utils::URLencode(symbol, reserved = TRUE), range, interval)
  cache <- file.path(cache_dir, sprintf("yahoo_%s_%s_%s.json", safe_name(symbol), range, interval))
  cached_fetch(url, cache, parse_yahoo_chart, cache_only)
}

# Daily quote object: daily bars aligned so the last bar is the live print
yahoo_daily <- function(symbol, cache_dir, cache_only = FALSE) {
  r <- yahoo_chart(symbol, "2y", "1d", cache_dir, cache_only)
  yahoo_daily_from(symbol, r$data, r$mode)
}

# Download many daily charts at once (6 connections, via the curl package).
# Anything that fails falls back to the sequential path with retries + cache.
yahoo_daily_batch <- function(symbols, cache_dir, cache_only = FALSE) {
  out <- list()
  if (cache_only || !requireNamespace("curl", quietly = TRUE)) {
    for (s in symbols) { out[[s]] <- yahoo_daily(s, cache_dir, cache_only); Sys.sleep(0.12) }
    return(out)
  }
  urls <- sprintf("https://query1.finance.yahoo.com/v8/finance/chart/%s?range=2y&interval=1d",
                  vapply(symbols, utils::URLencode, "", reserved = TRUE))
  tmp <- vapply(symbols, function(s) tempfile(fileext = ".json"), "")
  res <- tryCatch(curl::multi_download(urls, tmp, progress = FALSE, multiplex = TRUE, multi_timeout = 900,
                                       useragent = UA, timeout = 60),
                  error = function(e) { logmsg("  parallel download failed (", conditionMessage(e), "), using sequential"); NULL })
  n_retry <- 0
  for (i in seq_along(symbols)) {
    s <- symbols[i]
    ok <- !is.null(res) && isTRUE(res$success[i]) && isTRUE(res$status_code[i] == 200)
    p <- if (ok) tryCatch(parse_yahoo_chart(tmp[i]), error = function(e) NULL) else NULL
    if (!is.null(p)) {
      file.copy(tmp[i], file.path(cache_dir, sprintf("yahoo_%s_2y_1d.json", safe_name(s))), overwrite = TRUE)
      out[[s]] <- yahoo_daily_from(s, p, "fetched")
    } else {
      n_retry <- n_retry + 1
      out[[s]] <- yahoo_daily(s, cache_dir)
    }
    unlink(tmp[i])
  }
  if (n_retry) logmsg("  ", n_retry, " symbols retried sequentially")
  out
}

yahoo_daily_from <- function(symbol, p, mode) {
  if (is.null(p)) return(list(symbol = symbol, ok = FALSE, mode = mode))
  b <- p$bars
  b$date <- as.Date(as.POSIXct(b$t, origin = "1970-01-01", tz = p$tz), tz = p$tz)
  b <- b[!duplicated(b$date, fromLast = TRUE), ]
  mkt_date <- as.Date(p$market_time, tz = p$tz)
  n <- nrow(b)
  if (b$date[n] < mkt_date) {
    b <- rbind(b, data.frame(t = as.numeric(p$market_time), o = p$last, h = p$last, l = p$last,
                             c = p$last, v = 0, a = p$last, date = mkt_date))
  } else {
    b$a[n] <- b$a[n] * p$last / b$c[n]; b$c[n] <- p$last
    b$h[n] <- max(b$h[n], p$last); b$l[n] <- min(b$l[n], p$last)
  }
  n <- nrow(b)
  c(list(symbol = symbol, ok = TRUE, mode = mode,
         prev = if (n >= 2) b$c[n - 1] else NA_real_,
         history = data.frame(date = b$date, value = b$c),
         adj = data.frame(date = b$date, value = b$a),
         daily = b),
    p[c("name", "currency", "exchange", "instrument", "tz", "gmtoffset", "delay_min", "last", "market_time")])
}

# ----------------------------------------------------------------------------
#  Yahoo news headlines
# ----------------------------------------------------------------------------
empty_news <- function() data.frame(title = character(0), publisher = character(0), link = character(0),
                                    time = as.POSIXct(character(0), tz = "UTC"), summary = character(0),
                                    tickers = character(0), stringsAsFactors = FALSE)

# Search endpoint: titles only, but every story lists the tickers it is about.
parse_yahoo_news <- function(path) {
  j <- jsonlite::fromJSON(path, simplifyVector = FALSE)
  n <- j$news
  if (is.null(n)) stop("no news field")
  if (!length(n)) return(empty_news())
  data.frame(title = vapply(n, function(x) x$title %||% "", ""),
             publisher = vapply(n, function(x) x$publisher %||% "", ""),
             link = vapply(n, function(x) x$link %||% "", ""),
             time = as.POSIXct(vapply(n, function(x) as.numeric(x$providerPublishTime %||% NA), 0),
                               origin = "1970-01-01", tz = "UTC"),
             summary = "",
             tickers = vapply(n, function(x) paste(toupper(unlist(x$relatedTickers)), collapse = ","), ""),
             stringsAsFactors = FALSE)
}

# Per-ticker RSS feed: same stories with a summary paragraph.
parse_yahoo_rss <- function(path) {
  doc <- xml2::read_xml(path)
  items <- xml2::xml_find_all(doc, "//item")
  if (!length(items)) return(empty_news())
  txt <- function(tag) vapply(items, function(it) {
    n <- xml2::xml_find_first(it, tag); if (inherits(n, "xml_missing")) "" else trimws(xml2::xml_text(n))
  }, "")
  strip_html <- function(x) trimws(gsub("\\s+", " ", gsub("<[^>]+>", " ", x)))
  old <- Sys.getlocale("LC_TIME"); Sys.setlocale("LC_TIME", "C"); on.exit(Sys.setlocale("LC_TIME", old), add = TRUE)
  pub <- sub("\\s+[+-]\\d{4}$|\\s+GMT$|\\s+UTC$", "", txt("pubDate"))
  tm <- as.POSIXct(strptime(pub, "%a, %d %b %Y %H:%M:%S", tz = "UTC"))
  d <- data.frame(title = strip_html(txt("title")), publisher = txt("source"), link = txt("link"), time = tm,
                  summary = strip_html(txt("description")), tickers = "", stringsAsFactors = FALSE)
  d$publisher[!nzchar(d$publisher)] <- "Yahoo Finance"
  d[nzchar(d$title) & nzchar(d$link), ]
}

# query: ticker or free text; sym: the watchlist symbol the stories are shown under.
# Stories from the search endpoint that name other tickers but not this one are dropped,
# which is what used to put Gilead headlines under Pfizer.
yahoo_news <- function(query, cache_dir, n = 6, cache_only = FALSE, sym = query, source = "rss", label = "") {
  is_ticker <- identical(query, sym) && grepl("^[A-Z0-9.=^-]{1,12}$", query)
  r <- NULL
  if (identical(source, "rss") && is_ticker) {
    url <- sprintf("https://feeds.finance.yahoo.com/rss/2.0/headline?s=%s&region=US&lang=en-US",
                   utils::URLencode(query, reserved = TRUE))
    r <- cached_fetch(url, file.path(cache_dir, paste0("rss_", safe_name(query), ".xml")), parse_yahoo_rss, cache_only)
    if (!is.null(r$data) && nrow(r$data)) { r$data <- utils::head(r$data[order(r$data$time, decreasing = TRUE), ], max(n, 8)); return(r) }
  }
  url <- sprintf("https://query1.finance.yahoo.com/v1/finance/search?q=%s&newsCount=%d&quotesCount=0",
                 utils::URLencode(query, reserved = TRUE), n)
  r <- cached_fetch(url, file.path(cache_dir, paste0("news_", safe_name(query), ".json")), parse_yahoo_news, cache_only)
  if (!is.null(r$data) && nrow(r$data) && is_ticker) {
    # Yahoo tags a story with every ticker it mentions. Keep it only when this symbol is
    # the story's primary ticker, or the title names the company.
    words <- setdiff(tolower(unlist(strsplit(gsub("[^A-Za-z ]", " ", label), "\\s+"))),
                     c("", "inc", "corp", "corporation", "company", "group", "holdings", "the", "plc", "class", "ltd", "co"))
    words <- words[nchar(words) >= 4]
    tk <- strsplit(r$data$tickers, ",", fixed = TRUE)
    keep <- vapply(seq_len(nrow(r$data)), function(k) {
      t <- tk[[k]]; if (!length(t) || !any(nzchar(t))) return(TRUE)
      if (identical(t[1], toupper(sym))) return(TRUE)
      ttl <- tolower(r$data$title[k])
      grepl(paste0("\\b", tolower(sym), "\\b"), ttl) || (length(words) && any(vapply(words, function(w) grepl(paste0("\\b", w), ttl, fixed = FALSE), TRUE)))
    }, TRUE)
    r$data <- r$data[keep, ]
  }
  r
}

# ----------------------------------------------------------------------------
#  Cboe delayed option chain -> activity summary
# ----------------------------------------------------------------------------
parse_cboe_options <- function(path) {
  j <- jsonlite::fromJSON(path)
  d <- j[["data"]]
  o <- d[["options"]]
  if (!is.data.frame(o) || !nrow(o)) stop("empty chain")
  m <- regmatches(o$option, regexec("^(.*?)(\\d{6})([CP])(\\d{8})$", o$option))
  ok <- lengths(m) == 5
  o <- o[ok, ]; m <- m[ok]
  o$expiry <- as.Date(vapply(m, `[`, "", 3), "%y%m%d")
  o$type   <- vapply(m, `[`, "", 4)
  o$strike <- as.numeric(vapply(m, `[`, "", 5)) / 1000
  o$volume[is.na(o$volume)] <- 0; o$open_interest[is.na(o$open_interest)] <- 0
  calls <- o$type == "C"; puts <- o$type == "P"
  top <- o[order(-o$volume), ][seq_len(min(80, nrow(o))), ]
  list(timestamp = paste(j[["timestamp"]] %||% "", "UTC"),
       underlying = as.numeric(d[["current_price"]] %||% NA),
       iv30 = as.numeric(d[["iv30"]] %||% NA), iv30_change = as.numeric(d[["iv30_change"]] %||% NA),
       call_vol = sum(o$volume[calls]), put_vol = sum(o$volume[puts]),
       call_oi = sum(o$open_interest[calls]), put_oi = sum(o$open_interest[puts]),
       top = data.frame(type = top$type, expiry = format(top$expiry), strike = top$strike,
                        volume = top$volume, oi = top$open_interest, iv = top$iv,
                        last = top$last_trade_price, stringsAsFactors = FALSE))
}

cboe_options <- function(symbol, cache_dir, cache_only = FALSE) {
  url <- sprintf("https://cdn.cboe.com/api/global/delayed_quotes/options/%s.json", symbol)
  cached_fetch(url, file.path(cache_dir, paste0("cboe_", safe_name(symbol), ".json")), parse_cboe_options,
               cache_only, tries = 2)
}

# ----------------------------------------------------------------------------
#  FRED release calendar (optional, needs API key)
# ----------------------------------------------------------------------------
fred_release_calendar <- function(api_key, from = Sys.Date(), to = Sys.Date() + 45) {
  if (!nzchar(api_key)) return(NULL)
  url <- sprintf(paste0("https://api.stlouisfed.org/fred/releases/dates?realtime_start=%s&realtime_end=%s",
                        "&include_release_dates_with_no_data=true&api_key=%s&file_type=json&limit=1000"),
                 format(from), format(to), api_key)
  tmp <- tempfile(fileext = ".json")
  if (!http_get_file(url, tmp)) return(NULL)
  j <- tryCatch(jsonlite::fromJSON(tmp), error = function(e) NULL)
  if (is.null(j) || is.null(j$release_dates)) return(NULL)
  d <- j$release_dates
  data.frame(date = as.Date(d$date), event = d$release_name, stringsAsFactors = FALSE)
}

# ----------------------------------------------------------------------------
#  Optional Bloomberg comps refresh (only when USE_BLOOMBERG = TRUE)
# ----------------------------------------------------------------------------
bloomberg_comps <- function(comps) {
  if (is.null(comps) || is.null(comps$bbg_ticker)) return(NULL)
  tk <- comps$bbg_ticker[nzchar(comps$bbg_ticker %||% "")]
  if (!length(tk) || !requireNamespace("Rblpapi", quietly = TRUE)) return(NULL)
  tryCatch({
    con <- Rblpapi::blpConnect()
    x <- Rblpapi::bdp(tk, c("YLD_YTM_MID", "Z_SPRD_MID", "DUR_ADJ_MID", "RTG_SP"), con = con)
    data.frame(bbg_ticker = rownames(x), yield = x$YLD_YTM_MID, z_spread = x$Z_SPRD_MID,
               duration = x$DUR_ADJ_MID, rating = x$RTG_SP, stringsAsFactors = FALSE)
  }, error = function(e) { logmsg("Bloomberg comps unavailable: ", conditionMessage(e)); NULL })
}

# ----------------------------------------------------------------------------
#  Fetch everything
# ----------------------------------------------------------------------------
fetch_all <- function(cfg, inputs, cache_dir, run_mode = "morning") {
  dir.create(cache_dir, showWarnings = FALSE, recursive = TRUE)
  intraday <- identical(run_mode, "intraday")
  status <- list()
  add_status <- function(source, key, label, mode, last_obs, latency) {
    status[[length(status) + 1]] <<- data.frame(
      source = source, key = key, label = label, mode = mode,
      last_obs = if (length(last_obs) && !all(is.na(last_obs))) as.character(last_obs) else NA_character_,
      latency = latency, stringsAsFactors = FALSE)
  }

  # FRED ---------------------------------------------------------------------
  fred <- list()
  daily_ids <- unique(unname(unlist(cfg$FRED_SERIES)))
  macro_ids <- unique(vapply(cfg$MACRO_SERIES, function(m) m$id, ""))
  ids <- unique(c(daily_ids, macro_ids))
  label_of <- function(id) {
    for (g in cfg$FRED_SERIES) if (id %in% g) return(names(g)[match(id, g)])
    for (m in cfg$MACRO_SERIES) if (m$id == id) return(m$label)
    id
  }
  logmsg("FRED: ", length(ids), " series", if (intraday) " (cache, intraday run)" else "")
  for (id in ids) {
    start <- Sys.Date() - if (id %in% macro_ids) cfg$MACRO_HISTORY_DAYS else cfg$HISTORY_DAYS
    r <- fred_get_series(id, cache_dir, start, cache_only = intraday)
    fred[[id]] <- r$data
    add_status("FRED", id, label_of(id), r$mode, if (!is.null(r$data)) max(r$data$date) else NA,
               if (id %in% names(FRED_LATENCY)) FRED_LATENCY[[id]] else "Daily, prior close")
    if (r$mode %in% c("failed", "cache-fallback")) logmsg("  FRED ", id, ": ", r$mode)
    if (!intraday) Sys.sleep(0.15)
  }

  # Treasury.gov top-up -------------------------------------------------------
  tr <- treasury_get_curve(cache_dir, cache_only = intraday)
  if (!is.null(tr$data)) {
    for (k in names(TREASURY_TENOR_MAP)) {
      id <- TREASURY_TENOR_MAP[[k]]
      extra <- tr$data[, c("date", k)]; names(extra) <- c("date", "value")
      extra <- extra[!is.na(extra$value), ]
      if (is.null(fred[[id]])) fred[[id]] <- extra
      else {
        extra <- extra[extra$date > max(fred[[id]]$date), ]
        if (nrow(extra)) fred[[id]] <- rbind(fred[[id]], extra)
      }
    }
  }
  add_status("Treasury.gov", "par curve", "Daily par yield curve", tr$mode,
             if (!is.null(tr$data)) max(tr$data$date) else NA, "Daily, published after close")
  logmsg("Treasury.gov: ", tr$mode, if (!is.null(tr$data)) paste0(", curve through ", max(tr$data$date)) else "")

  # Yahoo daily quotes ----------------------------------------------------------
  wl <- inputs$watchlist; hold <- inputs$holdings
  yahoo_syms <- unique(c(cfg$YAHOO_SYMBOLS$symbol, cfg$EXTRA_YAHOO, names(cfg$BENCHMARKS),
                         if (!is.null(wl)) wl$symbol,
                         if (!is.null(hold)) hold$symbol[hold$pricing == "yahoo"],
                         vapply(Filter(function(x) x$src == "yahoo", cfg$CORR_SET), function(x) x$key, "")))
  yahoo_syms <- yahoo_syms[nzchar(yahoo_syms)]
  logmsg("Yahoo daily: ", length(yahoo_syms), " symbols", if (requireNamespace("curl", quietly = TRUE)) " (parallel)" else "")
  yahoo <- yahoo_daily_batch(yahoo_syms, cache_dir)
  for (s in yahoo_syms) {
    r <- yahoo[[s]]
    delay <- if (isTRUE(r$ok) && !is.na(r$delay_min) && r$delay_min > 0) sprintf("Delayed %d min", round(r$delay_min)) else "Delayed up to 15 min"
    add_status("Yahoo Finance", s, if (isTRUE(r$ok)) r$name else s, r$mode,
               if (isTRUE(r$ok)) format(r$market_time, "%Y-%m-%d %H:%M %Z") else NA, delay)
    if (r$mode %in% c("failed", "cache-fallback")) logmsg("  Yahoo ", s, ": ", r$mode)
  }
  modes <- vapply(yahoo, function(r) r$mode, "")
  logmsg("Yahoo daily: ", sum(modes == "fetched"), " fetched, ", sum(modes == "cache-fallback"), " from cache, ", sum(modes == "failed"), " failed")

  # Intraday / weekly candles for the watchlist ---------------------------------
  candles <- list()
  if (!is.null(wl) && nrow(wl)) {
    det <- toupper(wl$detail %||% rep("N", nrow(wl))) == "Y"
    logmsg("Yahoo candles: ", sum(det), " detail symbols (intraday + weekly bars)")
    for (s in wl$symbol[det]) {
      tfs <- list()
      for (tf in names(cfg$CANDLE_TIMEFRAMES)) {
        spec <- cfg$CANDLE_TIMEFRAMES[[tf]]
        if (spec$interval == "1d") next            # daily frames come from the quote fetch
        r <- yahoo_chart(s, spec$range, spec$interval, cache_dir,
                         cache_only = intraday && !isTRUE(spec$intraday))
        if (!is.null(r$data)) tfs[[tf]] <- r$data
        Sys.sleep(0.12)
      }
      candles[[s]] <- tfs
    }
  }

  # News -------------------------------------------------------------------------
  news <- list()
  if (!is.null(wl) && nrow(wl)) {
    for (i in seq_len(nrow(wl))) {
      if (!isTRUE(toupper(wl$news[i]) == "Y")) next
      q <- if (nzchar(wl$news_query[i] %||% "")) wl$news_query[i] else wl$symbol[i]
      r <- yahoo_news(q, cache_dir, cfg$NEWS_PER_SYMBOL, sym = wl$symbol[i], source = cfg$NEWS_SOURCE %||% "rss", label = wl$label[i])
      if (!is.null(r$data)) news[[wl$symbol[i]]] <- r$data
      add_status("Yahoo Finance news", wl$symbol[i], paste("Headlines:", wl$label[i]), r$mode,
                 if (!is.null(r$data) && nrow(r$data)) format(max(r$data$time), "%Y-%m-%d %H:%M UTC") else NA,
                 "Near real-time feed")
      Sys.sleep(0.12)
    }
  }

  # Options -----------------------------------------------------------------------
  options_data <- list()
  if (!is.null(wl) && nrow(wl)) {
    for (i in seq_len(nrow(wl))) {
      os <- wl$options_symbol[i] %||% ""
      if (!nzchar(os)) next
      r <- cboe_options(os, cache_dir)
      if (!is.null(r$data)) options_data[[wl$symbol[i]]] <- r$data
      add_status("Cboe delayed quotes", os, paste("Option chain:", wl$label[i]), r$mode,
                 if (!is.null(r$data)) r$data$timestamp else NA, "Delayed 15 min")
      if (r$mode == "failed") logmsg("  Cboe ", os, ": failed")
      Sys.sleep(0.12)
    }
  }

  # Calendar (optional) ------------------------------------------------------
  cal <- NULL
  if (nzchar(cfg$FRED_API_KEY) && !intraday) {
    cal <- fred_release_calendar(cfg$FRED_API_KEY)
    logmsg("FRED calendar: ", if (is.null(cal)) "unavailable" else paste(nrow(cal), "release dates"))
  }

  # Bloomberg comps (optional) ----------------------------------------------
  bbg <- NULL
  if (isTRUE(cfg$USE_BLOOMBERG)) {
    bbg <- bloomberg_comps(inputs$comps)
    add_status("Bloomberg", "comps", "New-issue comps", if (is.null(bbg)) "failed" else "fetched",
               if (is.null(bbg)) NA else format(Sys.time(), "%Y-%m-%d %H:%M"), "Real-time (terminal)")
  }

  list(fred = fred, yahoo = yahoo, candles = candles, news = news, options = options_data,
       calendar = cal, bbg_comps = bbg, status = do.call(rbind, status),
       fetched_at = Sys.time(), run_mode = run_mode)
}
