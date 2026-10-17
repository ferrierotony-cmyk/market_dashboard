# =============================================================================
#  analytics.R - everything computed from the raw downloads:
#    series stats, macro ribbon, market health composite, correlations,
#    watchlist technicals + alerts, portfolio valuation / allocation /
#    performance vs benchmarks.
# =============================================================================

# ---- basic series helpers ---------------------------------------------------
val_at <- function(df, on_or_before) {
  if (is.null(df) || !nrow(df)) return(NA_real_)
  i <- findInterval(as.numeric(on_or_before), as.numeric(df$date))
  if (i < 1) NA_real_ else df$value[i]
}

locf_on <- function(df, dates) {
  out <- rep(NA_real_, length(dates))
  if (is.null(df) || !nrow(df)) return(out)
  i <- findInterval(as.numeric(dates), as.numeric(df$date))
  ok <- i > 0; out[ok] <- df$value[i[ok]]; out
}

exact_on <- function(df, dates) {
  if (is.null(df) || !nrow(df)) return(rep(NA_real_, length(dates)))
  df$value[match(as.numeric(dates), as.numeric(df$date))]
}

series_stats <- function(df) {
  empty <- list(last = NA_real_, date = as.Date(NA), prev = NA_real_, d1 = NA_real_, w1 = NA_real_,
                m1 = NA_real_, ytd = NA_real_, lo1y = NA_real_, hi1y = NA_real_, pct1y = NA_real_)
  if (is.null(df) || !nrow(df)) return(empty)
  n <- nrow(df); last <- df$value[n]; d <- df$date[n]
  prev <- if (n > 1) df$value[n - 1] else NA_real_
  yr_end <- as.Date(sprintf("%d-12-31", as.integer(format(d, "%Y")) - 1))
  y <- df$value[df$date > d - 365]
  lo <- suppressWarnings(min(y)); hi <- suppressWarnings(max(y))
  list(last = last, date = d, prev = prev, d1 = last - prev,
       w1 = last - val_at(df, d - 7), m1 = last - val_at(df, d - 30),
       ytd = last - val_at(df, yr_end), lo1y = lo, hi1y = hi,
       pct1y = if (is.finite(hi) && is.finite(lo) && hi > lo) (last - lo) / (hi - lo) else NA_real_)
}

diff_series <- function(a, b, scale = 100) {
  if (is.null(a) || is.null(b)) return(NULL)
  m <- merge(a, b, by = "date", suffixes = c(".a", ".b"))
  if (!nrow(m)) return(NULL)
  data.frame(date = m$date, value = (m$value.a - m$value.b) * scale)
}

# FRED publishes ICE BofA OAS in percent (0.85 = 85 bp): convert to bp once.
normalize_fred <- function(fred, cfg) {
  other <- cfg$FRED_SERIES$credit_other
  bp_ids <- c(cfg$FRED_SERIES$credit_rating, cfg$FRED_SERIES$credit_maturity,
              other[!grepl("Yield", names(other))])
  for (id in unname(bp_ids)) if (!is.null(fred[[id]])) fred[[id]]$value <- fred[[id]]$value * 100
  fred
}

derived_series <- function(fred, ust_ids) {
  u <- function(t) fred[[ust_ids[[t]]]]
  list("2s10s" = diff_series(u("10Y"), u("2Y")),
       "5s30s" = diff_series(u("30Y"), u("5Y")),
       "3m10y" = diff_series(u("10Y"), u("3M")))
}

pct_stats <- function(y) {
  if (!isTRUE(y$ok)) return(list(last = NA_real_, d1 = NA_real_, w1 = NA_real_, d1_abs = NA_real_,
                                 w1_abs = NA_real_, date = as.Date(NA), time = NULL))
  h <- y$history; d <- as.Date(y$market_time)
  w1v <- val_at(h, d - 7)
  list(last = y$last, d1 = 100 * (y$last / y$prev - 1), w1 = 100 * (y$last / w1v - 1),
       d1_abs = y$last - y$prev, w1_abs = y$last - w1v, date = d, time = y$market_time)
}

# ---- technical indicators (also mirrored in the browser for candles) ---------
sma <- function(x, n) {
  if (length(x) < n) return(rep(NA_real_, length(x)))
  out <- as.numeric(stats::filter(x, rep(1 / n, n), sides = 1)); out
}
rsi_wilder <- function(x, n = 14) {
  out <- rep(NA_real_, length(x))
  if (length(x) <= n) return(out)
  d <- diff(x); g <- pmax(d, 0); l <- pmax(-d, 0)
  ag <- mean(g[1:n]); al <- mean(l[1:n])
  out[n + 1] <- if (al == 0) 100 else 100 - 100 / (1 + ag / al)
  if (length(d) > n) for (i in (n + 1):length(d)) {
    ag <- (ag * (n - 1) + g[i]) / n; al <- (al * (n - 1) + l[i]) / n
    out[i + 1] <- if (al == 0) 100 else 100 - 100 / (1 + ag / al)
  }
  out
}

grade_rule <- function(v, rule) {
  if (is.null(v) || length(v) == 0 || is.na(v)) return("na")
  if (rule$dir == "below") { if (v <= rule$good) "good" else if (v <= rule$warn) "warn" else "bad" }
  else                     { if (v >= rule$good) "good" else if (v >= rule$warn) "warn" else "bad" }
}
POINTS <- c(good = 2, warn = 1, bad = 0, na = NA)

# =============================================================================
#  Macro ribbon
# =============================================================================
macro_transform <- function(df, m) {
  if (is.null(df) || nrow(df) < 2) return(NULL)
  v <- df$value; n <- length(v)
  lagk <- function(k) c(rep(NA_real_, k), v[seq_len(n - k)])
  out <- switch(m$transform,
                level = v,
                yoy   = if (n > 12) 100 * (v / lagk(12) - 1) else rep(NA_real_, n),
                diff  = v - lagk(1),
                pct   = 100 * (v / lagk(1) - 1),
                avg4  = as.numeric(stats::filter(v, rep(0.25, 4), sides = 1)),
                v)
  out <- out * (m$scale %||% 1)
  r <- data.frame(date = df$date, value = out)
  r[!is.na(r$value), ]
}

period_label <- function(id, d) {
  f <- FRED_LATENCY[id]
  if (is.na(f)) return(format(d, "%d %b"))
  switch(f, Monthly = format(d, "%b %Y"),
         Quarterly = paste0("Q", (as.integer(format(d, "%m")) - 1) %/% 3 + 1, " ", format(d, "%Y")),
         Weekly = paste("wk of", format(d, "%d %b")), format(d, "%d %b"))
}

macro_ribbon <- function(fred, cfg, calendar) {
  lapply(cfg$MACRO_SERIES, function(m) {
    t <- macro_transform(fred[[m$id]], m)
    nxt <- NA_character_
    if (!is.null(calendar) && nrow(calendar)) {
      dd <- calendar$date[calendar$event == m$release & calendar$date >= Sys.Date()]
      if (length(dd)) nxt <- format(min(dd), "%a %d %b")
    }
    if (is.null(t) || !nrow(t)) return(list(id = m$id, label = m$label, ok = FALSE))
    n <- nrow(t)
    list(id = m$id, label = m$label, ok = TRUE, unit = m$unit, dec = m$dec,
         value = t$value[n], prev = if (n > 1) t$value[n - 1] else NA_real_,
         period = period_label(m$id, t$date[n]), date = format(t$date[n]),
         spark = utils::tail(t$value, 24), spark_dates = format(utils::tail(t$date, 24)),
         next_release = nxt, freq = unname(FRED_LATENCY[m$id]) %||% "Daily")
  })
}

# =============================================================================
#  Market health composite
# =============================================================================
health_compute <- function(cfg, S, Y, yahoo, fred) {
  closes <- function(s) if (isTRUE(yahoo[[s]]$ok)) yahoo[[s]]$history$value else numeric(0)
  pct_back <- function(x, k) { n <- length(x); if (n > k) 100 * (x[n] / x[n - k] - 1) else NA_real_ }
  spx <- closes("^GSPC"); n_spx <- length(spx)
  sofr <- fred[["SOFR"]]; effr <- fred[["EFFR"]]
  se <- if (!is.null(sofr) && !is.null(effr)) { m <- merge(sofr, effr, by = "date"); if (nrow(m)) 100 * (m$value.x[nrow(m)] - m$value.y[nrow(m)]) else NA_real_ } else NA_real_
  vix <- Y[["^VIX"]]$last %||% S[["VIXCLS"]]$last
  metrics <- list(
    vix = vix,
    vix_ts = if (!is.na(vix) && isTRUE(yahoo[["^VIX3M"]]$ok)) vix / yahoo[["^VIX3M"]]$last else NA_real_,
    move = Y[["^MOVE"]]$last,
    ig_pct1y = S[["BAMLC0A0CM"]]$pct1y,
    hy_m1 = S[["BAMLH0A0HYM2"]]$m1,
    ust10_absm1 = abs(S[["DGS10"]]$m1 * 100),
    c3m10y = S[["3m10y"]]$last,
    spx_vs200 = if (n_spx >= 200) 100 * (spx[n_spx] / mean(utils::tail(spx, 200)) - 1) else NA_real_,
    spx_dd = if (n_spx >= 20) 100 * (spx[n_spx] / max(utils::tail(spx, 252)) - 1) else NA_real_,
    dxy_absm1 = abs(pct_back(closes("DX-Y.NYB"), 21)),
    wti_absm1 = abs(pct_back(closes("CL=F"), 21)),
    nfci = S[["NFCI"]]$last,
    sofr_effr = se
  )
  fmt_v <- function(v, f) {
    if (is.null(v) || is.na(v)) return("n/a")
    if (f == "pct") sprintf("%d%%", round(100 * v)) else sprintf(f, v)
  }
  items <- lapply(cfg$HEALTH_RULES, function(r) {
    v <- metrics[[r$metric]]; g <- grade_rule(v, r)
    thr <- if (r$dir == "below") sprintf("green <= %s, red > %s", fmt_v(r$good, r$fmt), fmt_v(r$warn, r$fmt))
           else sprintf("green >= %s, red < %s", fmt_v(r$good, r$fmt), fmt_v(r$warn, r$fmt))
    list(domain = r$domain, name = r$name, value = if (is.null(v)) NA else v,
         value_txt = fmt_v(v, r$fmt), status = g, rule = thr)
  })
  pts <- vapply(items, function(i) POINTS[[i$status]], 0)
  ok <- !is.na(pts)
  score <- if (any(ok)) round(100 * sum(pts[ok]) / (2 * sum(ok))) else NA
  status <- if (is.na(score)) "na" else if (score >= 70) "good" else if (score >= 45) "warn" else "bad"
  domains <- unique(vapply(items, function(i) i$domain, ""))
  dom <- lapply(domains, function(d) {
    its <- Filter(function(i) i$domain == d, items)
    p <- vapply(its, function(i) POINTS[[i$status]], 0); p <- p[!is.na(p)]
    st <- if (!length(p)) "na" else { s <- mean(p); if (s >= 1.5) "good" else if (s >= 0.75) "warn" else "bad" }
    list(name = d, status = st, items = its)
  })
  list(score = score, status = status, label = if (status == "na") "UNKNOWN" else cfg$HEALTH_LABELS[[status]],
       n_ok = sum(ok), n_total = length(items), domains = dom)
}

# =============================================================================
#  Correlations
# =============================================================================
corr_compute <- function(cfg, fred, yahoo, derived) {
  grid <- fred[["DGS10"]]$date
  if (is.null(grid)) return(NULL)
  grid <- grid[grid > max(grid) - 400]
  get_series <- function(it) switch(it$src,
    yahoo = if (isTRUE(yahoo[[it$key]]$ok)) yahoo[[it$key]]$history else NULL,
    fred = fred[[it$key]], derived = derived[[it$key]])
  labs <- vapply(cfg$CORR_SET, function(it) it$label, "")
  M <- sapply(cfg$CORR_SET, function(it) {
    v <- exact_on(get_series(it), grid)
    ch <- if (it$kind == "ret") c(NA, 100 * (v[-1] / v[-length(v)] - 1)) else c(NA, diff(v))
    ch
  })
  if (is.null(dim(M))) return(NULL)
  colnames(M) <- labs
  cm <- function(rows) {
    X <- M[rows, , drop = FALSE]
    r <- suppressWarnings(stats::cor(X, use = "pairwise.complete.obs"))
    r[!is.finite(r)] <- NA; round(r, 2)
  }
  n <- nrow(M)
  w90 <- max(1, n - 62):n; w1y <- max(1, n - 251):n
  roll <- lapply(cfg$ROLLING_CORR_PAIRS, function(p) {
    a <- M[, p[1]]; b <- M[, p[2]]; W <- cfg$ROLLING_CORR_WINDOW
    idx <- max(W, n - 251):n
    vals <- vapply(idx, function(t) {
      s <- (t - W + 1):t; ok <- stats::complete.cases(a[s], b[s])
      if (sum(ok) < W * 0.6) NA_real_ else suppressWarnings(stats::cor(a[s][ok], b[s][ok]))
    }, 0)
    list(label = paste(p[1], "vs", p[2]), dates = format(grid[idx]), values = round(vals, 3))
  })
  list(labels = labs, kinds = vapply(cfg$CORR_SET, function(it) it$kind, ""),
       m90 = cm(w90), m1y = cm(w1y), asof = format(max(grid)),
       n90 = length(w90), n1y = length(w1y), rolling = roll, window = cfg$ROLLING_CORR_WINDOW)
}

# =============================================================================
#  Watchlist technicals + alerts
# =============================================================================
watch_compute <- function(cfg, wl, yahoo, news, options_data) {
  rows <- list(); alerts <- list()
  add_alert <- function(sev, cat, sym, msg, when = NA, ts = NA) {
    alerts[[length(alerts) + 1]] <<- data.frame(severity = sev, category = cat, symbol = sym,
                                                message = msg, time = as.character(when),
                                                ts = as.numeric(ts), key = paste0(cat, "|", sym), stringsAsFactors = FALSE)
  }
  now_et <- as.POSIXlt(Sys.time(), tz = "America/New_York")
  col <- function(nm, default = "") { v <- wl[[nm]]; if (is.null(v)) return(rep(default, nrow(wl))); v[is.na(v) | !nzchar(v)] <- default; v }
  wl_type <- col("type", "Other"); wl_sector <- col("sector", "Unclassified")
  for (i in seq_len(nrow(wl))) {
    s <- wl$symbol[i]; y <- yahoo[[s]]; lab <- wl$label[i]
    if (!isTRUE(y$ok)) { rows[[length(rows) + 1]] <- list(symbol = s, label = lab, type = wl_type[i], sector = wl_sector[i], ok = FALSE); next }
    b <- y$daily; n <- nrow(b); cl <- b$c
    pctk <- function(k) if (n > k) 100 * (cl[n] / cl[n - k] - 1) else NA_real_
    yr_end <- as.Date(sprintf("%d-12-31", as.integer(format(Sys.Date(), "%Y")) - 1))
    ytd_base <- val_at(y$history, yr_end)
    # volume: use the last complete session (today's bar is partial before the close)
    partial <- b$date[n] == as.Date(now_et) && (now_et$hour * 60 + now_et$min) < 16 * 60 + 30
    vi <- if (partial) n - 1 else n
    vol <- if (vi >= 21) b$v[vi] else NA_real_
    avg20 <- if (vi >= 21) mean(b$v[(vi - 20):(vi - 1)]) else NA_real_
    vratio <- if (!is.na(vol) && !is.na(avg20) && avg20 > 0) vol / avg20 else NA_real_
    r <- rsi_wilder(cl)[n]
    sma50 <- sma(cl, 50); sma200 <- sma(cl, 200); s50 <- sma50[n]; s200 <- sma200[n]
    # +1 when the close crossed above the average since the prior session, -1 below, 0 otherwise
    crossed <- function(a) if (n < 2 || is.na(a[n]) || is.na(a[n - 1])) 0 else (cl[n] > a[n]) - (cl[n - 1] > a[n - 1])
    w52 <- utils::tail(cl, 252)
    d1 <- 100 * (y$last / y$prev - 1)
    rows[[length(rows) + 1]] <- list(
      symbol = s, label = lab, type = wl_type[i], sector = wl_sector[i], ok = TRUE,
      detail = toupper(wl$detail[i] %||% "N") == "Y", prev = y$prev, cross50 = crossed(sma50), cross200 = crossed(sma200),
      last = y$last, d1 = d1, w1 = pctk(5), m1 = pctk(21),
      ytd = if (!is.na(ytd_base)) 100 * (y$last / ytd_base - 1) else NA_real_,
      vratio = vratio, rsi = r,
      vs50 = if (!is.na(s50)) 100 * (cl[n] / s50 - 1) else NA_real_,
      vs200 = if (!is.na(s200)) 100 * (cl[n] / s200 - 1) else NA_real_,
      pos52 = if (max(w52) > min(w52)) (cl[n] - min(w52)) / (max(w52) - min(w52)) else NA_real_,
      spark = round(utils::tail(cl, 60), 6), time = format(y$market_time, "%d %b %H:%M"),
      ts = as.numeric(y$market_time), stale = identical(y$mode, "cache-fallback"),
      delay = if (!is.na(y$delay_min) && y$delay_min > 0) sprintf("%d min", round(y$delay_min)) else "<=15 min")
    # per-row alert columns: only for the rows WATCHLIST_ROW_ALERTS selects (rules cover the rest)
    row_mode <- tolower(cfg$WATCHLIST_ROW_ALERTS %||% "all")
    if (row_mode == "none" || (row_mode == "detail" && !isTRUE(toupper(wl$detail[i] %||% "N") == "Y"))) next
    num <- function(x) suppressWarnings(as.numeric(x))
    above <- num(wl$alert_above[i]); below <- num(wl$alert_below[i])
    mv <- num(wl$alert_move_pct[i]); vx <- num(wl$alert_volume_x[i])
    when <- format(y$market_time, "%d %b %H:%M"); ts <- y$market_time
    if (!is.na(above) && y$last >= above) add_alert("serious", "Price", s, sprintf("%s at %s, above alert level %s", lab, format(y$last, big.mark = ","), format(above, big.mark = ",")), when, ts)
    if (!is.na(below) && y$last <= below) add_alert("serious", "Price", s, sprintf("%s at %s, below alert level %s", lab, format(y$last, big.mark = ","), format(below, big.mark = ",")), when, ts)
    if (!is.na(mv) && !is.na(d1) && abs(d1) >= mv) add_alert(if (abs(d1) >= 2 * mv) "serious" else "warning", "Move", s, sprintf("%s %+.2f%% on the day (alert at +/-%.1f%%)", lab, d1, mv), when, ts)
    if (!is.na(vx) && !is.na(vratio) && vratio >= vx) add_alert("warning", "Volume", s, sprintf("%s volume %.1fx its 20-day average (last full session)", lab, vratio), format(b$date[vi], "%d %b"), as.POSIXct(b$date[vi]) + 21 * 3600)
    if (!is.na(r) && (r >= cfg$RSI_ALERTS[["high"]] || r <= cfg$RSI_ALERTS[["low"]])) add_alert("info", "Technical", s, sprintf("%s RSI(14) %.0f, %s", lab, r, if (r >= cfg$RSI_ALERTS[["high"]]) "overbought" else "oversold"), when, ts)
  }
  # news: keyword flags, summaries, one copy of each story ----------------------------
  news_rows <- list(); seen_links <- character(0); flagged_24h <- list()
  kw <- paste0("(", paste(cfg$NEWS_KEYWORDS, collapse = "|"), ")")
  max_sum <- cfg$NEWS_SUMMARY_CHARS %||% 320
  for (s in names(news)) {
    nd <- news[[s]]; if (is.null(nd) || !nrow(nd)) next
    nd <- nd[!is.na(nd$time) & nd$time >= Sys.time() - cfg$NEWS_MAX_AGE_HOURS * 3600, ]
    if (!nrow(nd)) next
    nd <- nd[order(nd$time, decreasing = TRUE), ]
    if (is.null(nd$summary)) nd$summary <- ""
    lab <- wl$label[match(s, wl$symbol)]
    for (k in seq_len(nrow(nd))) {
      if (nd$link[k] %in% seen_links) next
      seen_links <- c(seen_links, nd$link[k])
      hit <- regmatches(tolower(nd$title[k]), regexpr(kw, tolower(nd$title[k])))
      sm <- nd$summary[k]; if (is.na(sm)) sm <- ""
      if (nchar(sm) > max_sum) sm <- paste0(substr(sm, 1, max_sum - 3), "...")
      if (tolower(sm) == tolower(nd$title[k])) sm <- ""
      news_rows[[length(news_rows) + 1]] <- list(symbol = s, label = lab, title = nd$title[k], publisher = nd$publisher[k],
                                                 link = nd$link[k], time = format(nd$time[k], "%Y-%m-%dT%H:%M:%SZ"),
                                                 summary = sm, flag = if (length(hit)) hit else "")
      if (length(hit) && nd$time[k] >= Sys.time() - 24 * 3600) {
        flagged_24h[[s]] <- c(flagged_24h[[s]], hit)
        add_alert("info", "News", s, sprintf("%s headline mentions '%s': %s", lab, hit, nd$title[k]),
                  format(nd$time[k], "%d %b %H:%M UTC"), nd$time[k])
      }
    }
  }
  # options activity
  opt_rows <- list()
  orl <- cfg$OPTIONS_RULES
  for (s in names(options_data)) {
    o <- options_data[[s]]; lab <- wl$label[match(s, wl$symbol)]
    pc <- if (o$call_vol > 0) o$put_vol / o$call_vol else NA_real_
    # contracts expiring within two days always trade far above open interest: ignore them
    asof <- suppressWarnings(as.Date(substr(o$timestamp, 1, 10))); if (is.na(asof)) asof <- Sys.Date()
    tp <- o$top[as.Date(o$top$expiry) > asof + 2, ]
    tp <- utils::head(tp[order(-tp$volume), ], 8)
    unusual <- tp[tp$volume >= orl$min_contract_volume & tp$volume >= orl$vol_oi_ratio * pmax(tp$oi, 1), ]
    opt_rows[[length(opt_rows) + 1]] <- list(symbol = s, label = lab, timestamp = o$timestamp,
      call_vol = o$call_vol, put_vol = o$put_vol, pc = pc, oi = o$call_oi + o$put_oi,
      iv30 = o$iv30, iv30_change = o$iv30_change, top = tp, n_unusual = nrow(unusual))
    o_ts <- suppressWarnings(as.POSIXct(substr(o$timestamp, 1, 19), tz = "UTC")); if (is.na(o_ts)) o_ts <- Sys.time()
    if (!is.na(pc) && (pc >= orl$pc_high || pc <= orl$pc_low) && (o$call_vol + o$put_vol) >= 5 * orl$min_contract_volume)
      add_alert(if (nzchar(Sys.getenv("DASH_PUBLIC", unset = ""))) "info" else "warning", "Options", s, sprintf("%s put/call volume ratio %.2f (%s calls, %s puts)", lab, pc,
                format(o$call_vol, big.mark = ","), format(o$put_vol, big.mark = ",")), o$timestamp, o_ts)
    if (nrow(unusual)) {
      u <- unusual[1, ]
      add_alert("warning", "Options", s, sprintf("%s unusual activity: %s %s %g %s traded %s vs open interest %s",
                lab, if (u$type == "C") "call" else "put", format(as.Date(u$expiry), "%d %b %y"), u$strike,
                "strike", format(u$volume, big.mark = ","), format(u$oi, big.mark = ",")), o$timestamp, o_ts)
    }
  }
  # equity movers and sector summary ------------------------------------------------
  is_eq <- vapply(rows, function(r) isTRUE(r$ok) && r$type == "Equity" && !is.na(r$d1), TRUE)
  eq <- rows[is_eq]
  movers <- NULL; sectors <- NULL
  if (length(eq)) {
    secs <- vapply(eq, function(r) r$sector, "")
    sectors <- lapply(unique(secs), function(sct) {
      rs <- eq[secs == sct]; dd <- vapply(rs, function(r) r$d1, 0)
      g <- function(f) mean(vapply(rs, function(r) { v <- r[[f]]; if (is.null(v)) NA_real_ else v }, 0), na.rm = TRUE)
      list(sector = sct, n = length(rs), d1 = g("d1"), w1 = g("w1"), m1 = g("m1"), ytd = g("ytd"),
           up = sum(dd > 0), down = sum(dd < 0), best = rs[[which.max(dd)]], worst = rs[[which.min(dd)]])
    })
    sectors <- sectors[order(-vapply(sectors, function(s) s$d1, 0))]
  }
  # "why it moved": one line per name built from the numbers already on the page ----
  sec_d1 <- if (length(sectors)) setNames(vapply(sectors, function(s) s$d1, 0), vapply(sectors, function(s) s$sector, "")) else numeric(0)
  pc_of <- setNames(vapply(opt_rows, function(o) o$pc, 0), vapply(opt_rows, function(o) o$symbol, ""))
  for (k in seq_along(rows)) {
    r <- rows[[k]]; if (!isTRUE(r$ok) || is.na(r$d1)) next
    p <- sprintf("%+.1f%% today", r$d1)
    if (!is.na(r$vratio)) p <- c(p, if (r$vratio >= 1.5) sprintf("on %.1fx normal volume", r$vratio) else if (r$vratio <= 0.5) "on light volume" else NULL)
    sd <- sec_d1[r$sector]
    if (length(sd) && !is.na(sd) && r$type == "Equity")
      p <- c(p, sprintf("sector %+.1f%% (%s)", sd, if (abs(r$d1 - sd) >= 3) "stock-specific" else if (abs(r$d1) >= 1) "sector-wide" else "in line"))
    if (!is.na(r$pos52)) p <- c(p, if (r$pos52 >= 0.98) "at a 52-week high" else if (r$pos52 <= 0.02) "at a 52-week low" else NULL)
    if (!is.na(r$rsi)) p <- c(p, if (r$rsi >= cfg$RSI_ALERTS[["high"]]) sprintf("RSI %.0f overbought", r$rsi) else if (r$rsi <= cfg$RSI_ALERTS[["low"]]) sprintf("RSI %.0f oversold", r$rsi) else NULL)
    pc <- pc_of[r$symbol]
    if (length(pc) && !is.na(pc)) p <- c(p, if (pc >= cfg$OPTIONS_RULES$pc_high) sprintf("put/call %.2f, heavy put buying", pc) else if (pc <= cfg$OPTIONS_RULES$pc_low) sprintf("put/call %.2f, call-heavy", pc) else NULL)
    fl <- unique(flagged_24h[[r$symbol]])
    if (length(fl)) p <- c(p, paste0("headlines: ", paste(fl, collapse = ", ")))
    rows[[k]]$why <- paste(p, collapse = " | ")   # the build renders | as a middle dot (locale-safe)
  }
  # movers come last so each row carries its "why" line
  if (length(eq)) {
    eq <- rows[is_eq]; d1 <- vapply(eq, function(r) r$d1, 0)
    ord <- order(d1, decreasing = TRUE)
    movers <- list(up = eq[utils::head(ord[d1[ord] > 0], 8)], down = eq[utils::head(rev(ord)[d1[rev(ord)] < 0], 8)],
                   n_up = sum(d1 > 0), n_down = sum(d1 < 0), n = length(eq))
  }
  list(rows = rows, news = news_rows, options = opt_rows, movers = movers, sectors = sectors,
       alerts = if (length(alerts)) do.call(rbind, alerts) else NULL)
}

# =============================================================================
#  Portfolio
# =============================================================================
portfolio_compute <- function(cfg, h, fred, yahoo, ust_ids) {
  if (is.null(h) || !nrow(h)) return(NULL)
  num <- function(x) suppressWarnings(as.numeric(x))
  for (k in c("quantity", "cost_price", "mark_price", "duration", "coupon")) h[[k]] <- num(h[[k]] %||% NA)
  for (k in c("mark_date", "entry_date")) h[[k]] <- suppressWarnings(as.Date(h[[k]]))
  for (k in c("issuer", "asset_class", "sector", "rating", "spread_index", "price_per_100", "name")) {
    if (is.null(h[[k]])) h[[k]] <- ""; h[[k]][is.na(h[[k]])] <- ""
  }
  h$per100 <- h$pricing == "model" | toupper(h$price_per_100) == "Y"
  scale_of <- function(i) if (h$per100[i]) 0.01 else 1

  # price history per holding --------------------------------------------------
  P <- vector("list", nrow(h))
  for (i in seq_len(nrow(h))) {
    if (h$pricing[i] == "model") {
      u <- fred[[ust_ids[[h$symbol[i]]]]]
      if (is.null(u)) next
      y <- u
      if (nzchar(h$spread_index[i]) && !is.null(fred[[h$spread_index[i]]]))
        y$value <- u$value + locf_on(fred[[h$spread_index[i]]], u$date) / 100
      y <- y[!is.na(y$value), ]
      md <- if (is.na(h$mark_date[i])) y$date[1] else h$mark_date[i]
      y_mark <- val_at(y, md); if (is.na(y_mark)) y_mark <- y$value[1]
      px <- data.frame(date = y$date, value = h$mark_price[i] - h$duration[i] * (y$value - y_mark))
      carry <- if (!is.na(h$coupon[i])) h$coupon[i] else y_mark
      sprd_asof <- if (nzchar(h$spread_index[i]) && !is.null(fred[[h$spread_index[i]]])) max(fred[[h$spread_index[i]]]$date) else NA
      P[[i]] <- list(px = px, adj = px, carry = carry,
                     asof = max(y$date), method = sprintf("Model: UST %s%s", h$symbol[i],
                                                          if (nzchar(h$spread_index[i])) " + OAS index" else ""),
                     spread_asof = sprd_asof, yld = y$value[nrow(y)])
    } else if (h$pricing[i] == "yahoo") {
      q <- yahoo[[h$symbol[i]]]
      if (!isTRUE(q$ok)) next
      P[[i]] <- list(px = q$history, adj = q$adj, carry = 0, asof = q$market_time,
                     method = "Yahoo (delayed)", spread_asof = NA, yld = NA)
    } else {
      md <- if (is.na(h$mark_date[i])) Sys.Date() else h$mark_date[i]
      P[[i]] <- list(px = data.frame(date = md, value = h$mark_price[i]), adj = NULL,
                     carry = if (!is.na(h$coupon[i])) h$coupon[i] else 0, asof = md,
                     method = "Manual mark", spread_asof = NA, yld = NA)
    }
  }
  okh <- !vapply(P, is.null, TRUE)

  # holdings table -------------------------------------------------------------------
  tab <- lapply(seq_len(nrow(h)), function(i) {
    if (!okh[i]) return(list(id = h$id[i], name = h$name[i], ok = FALSE))
    p <- P[[i]]; px <- p$px; n <- nrow(px); sc <- scale_of(i)
    last <- px$value[n]; prev <- if (n > 1) px$value[n - 1] else last
    gap <- if (n > 1) as.numeric(px$date[n] - px$date[n - 1]) else 0
    face <- h$quantity[i]
    carry_rate <- p$carry / 100 * (if (h$per100[i]) face else 0)
    mv <- face * last * sc
    day <- face * (last - prev) * sc + carry_rate * gap / 365
    entry <- if (is.na(h$entry_date[i])) px$date[1] else h$entry_date[i]
    price_pnl <- if (!is.na(h$cost_price[i])) face * (last - h$cost_price[i]) * sc else NA_real_
    carry_pnl <- carry_rate * max(0, as.numeric(px$date[n] - entry)) / 365
    dur <- h$duration[i]
    list(id = h$id[i], name = h$name[i], issuer = h$issuer[i], asset_class = h$asset_class[i],
         sector = h$sector[i], rating = h$rating[i], symbol = h$symbol[i], ok = TRUE,
         quantity = face, per100 = h$per100[i], price = last, cost = h$cost_price[i],
         asof = if (inherits(p$asof, "POSIXct")) format(p$asof, "%d %b %H:%M") else format(as.Date(p$asof), "%d %b"),
         method = p$method, mv = mv, day = day, price_pnl = price_pnl, carry_pnl = carry_pnl,
         mark_age = if (h$pricing[i] == "yahoo" || is.na(h$mark_date[i])) NA_real_ else as.numeric(Sys.Date() - h$mark_date[i]),
         total_pnl = (price_pnl %||% 0) + carry_pnl, duration = dur,
         dv01 = if (!is.na(dur)) mv * dur * 1e-4 else NA_real_,
         cs01 = if (!is.na(dur) && nzchar(h$spread_index[i])) mv * dur * 1e-4 else NA_real_,
         yld = p$yld, tenor = if (h$pricing[i] == "model") h$symbol[i] else "Other")
  })
  okt <- Filter(function(r) isTRUE(r$ok), tab)
  tot_mv <- sum(vapply(okt, function(r) r$mv, 0))
  for (k in seq_along(tab)) if (isTRUE(tab[[k]]$ok)) tab[[k]]$weight <- tab[[k]]$mv / tot_mv
  okt <- Filter(function(r) isTRUE(r$ok), tab)
  sumf <- function(f) sum(vapply(okt, function(r) r[[f]] %||% 0, 0), na.rm = TRUE)
  totals <- list(mv = tot_mv, day = sumf("day"), price_pnl = sumf("price_pnl"), carry_pnl = sumf("carry_pnl"),
                 total_pnl = sumf("total_pnl"), dv01 = sumf("dv01"), cs01 = sumf("cs01"),
                 cost_mv = sum(vapply(okt, function(r) r$quantity * (r$cost %||% r$price) * (if (r$per100) 0.01 else 1), 0)),
                 n = length(okt))
  totals$day_pct <- if (tot_mv > 0) 100 * totals$day / (tot_mv - totals$day) else NA_real_
  totals$total_pct <- if (totals$cost_mv > 0) 100 * totals$total_pnl / totals$cost_mv else NA_real_
  totals$duration <- if (tot_mv > 0) sum(vapply(okt, function(r) (r$duration %||% 0) * r$weight, 0), na.rm = TRUE) else NA_real_
  ylds <- vapply(okt, function(r) if (is.na(r$yld)) NA_real_ else r$yld * r$weight, 0)
  totals$yield <- if (any(!is.na(ylds))) sum(ylds, na.rm = TRUE) / sum(vapply(okt, function(r) if (is.na(r$yld)) 0 else r$weight, 0)) else NA_real_

  # allocation ---------------------------------------------------------------------------
  group_w <- function(field) {
    k <- vapply(okt, function(r) if (nzchar(r[[field]] %||% "")) r[[field]] else "Unclassified", "")
    w <- tapply(vapply(okt, function(r) r$weight, 0), k, sum)
    w <- sort(w, decreasing = TRUE)
    list(labels = names(w), values = round(100 * unname(w), 2))
  }
  alloc <- list(asset_class = group_w("asset_class"), sector = group_w("sector"))
  if (any(vapply(okt, function(r) nzchar(r$rating %||% ""), TRUE))) alloc$rating <- group_w("rating")
  ordw <- okt[order(-vapply(okt, function(r) r$weight, 0))]
  topn <- utils::head(ordw, 10)
  alloc$top <- list(labels = vapply(topn, function(r) r$name, ""), values = round(100 * vapply(topn, function(r) r$weight, 0), 2))
  dvt <- tapply(vapply(okt, function(r) r$dv01 %||% 0, 0), vapply(okt, function(r) r$tenor, ""), sum, na.rm = TRUE)
  tord <- c("1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y", "Other")
  dvt <- dvt[order(match(names(dvt), tord))]
  alloc$dv01 <- list(labels = names(dvt), values = round(unname(dvt), 0))

  # concentration --------------------------------------------------------------------------
  w <- vapply(okt, function(r) r$weight, 0)
  ng <- vapply(okt, function(r) !grepl("^gov", tolower(r$sector)), TRUE)
  iss <- if (any(ng)) tapply(w[ng], vapply(okt[ng], function(r) if (nzchar(r$issuer)) r$issuer else r$name, ""), sum) else numeric(0)
  sec <- if (any(ng)) tapply(w[ng], vapply(okt[ng], function(r) r$sector, ""), sum) else numeric(0)
  lim <- cfg$CONCENTRATION_LIMITS
  conc <- list(top5 = sum(utils::head(sort(w, decreasing = TRUE), 5)), hhi = sum(w^2), eff_n = 1 / sum(w^2),
               max_issuer = if (length(iss)) max(iss) else NA_real_, max_issuer_name = if (length(iss)) names(iss)[which.max(iss)] else "",
               max_sector = if (length(sec)) max(sec) else NA_real_, max_sector_name = if (length(sec)) names(sec)[which.max(sec)] else "")
  flags <- list()
  if (!is.na(conc$max_issuer) && conc$max_issuer > lim$single_issuer_ex_govt)
    flags[[length(flags) + 1]] <- sprintf("%s is %.1f%% of the portfolio (limit %.0f%% per non-government issuer)", conc$max_issuer_name, 100 * conc$max_issuer, 100 * lim$single_issuer_ex_govt)
  if (!is.na(conc$max_sector) && conc$max_sector > lim$sector_ex_govt)
    flags[[length(flags) + 1]] <- sprintf("%s sector is %.1f%% (limit %.0f%% per non-government sector)", conc$max_sector_name, 100 * conc$max_sector, 100 * lim$sector_ex_govt)
  if (conc$top5 > lim$top5 && length(w) >= 10)
    flags[[length(flags) + 1]] <- sprintf("Top 5 holdings are %.1f%% (limit %.0f%%)", 100 * conc$top5, 100 * lim$top5)
  conc$flags <- unlist(flags)

  # performance: current holdings held constant over the last year ---------------------
  dates <- sort(unique(do.call(c, lapply(P[okh], function(p) p$px$date))))
  dates <- dates[dates >= max(dates) - 380 & !(format(dates, "%u") %in% c("6", "7"))]
  perf <- NULL; index_chart <- NULL
  if (length(dates) > 30) {
    nd <- length(dates); pnl <- numeric(nd - 1); base <- numeric(nd - 1)
    for (i in which(okh)) {
      p <- P[[i]]; sc <- scale_of(i); face <- h$quantity[i]
      v <- face * locf_on(p$px, dates) * sc
      if (h$pricing[i] == "yahoo") {
        a <- locf_on(p$adj, dates)
        d_pnl <- v[-nd] * (a[-1] / a[-nd] - 1)
      } else {
        d_pnl <- diff(v) + (p$carry / 100) * (if (h$per100[i]) face else 0) * as.numeric(diff(dates)) / 365
      }
      d_pnl[is.na(d_pnl)] <- 0; vv <- v[-nd]; vv[is.na(vv)] <- 0
      pnl <- pnl + d_pnl; base <- base + vv
    }
    r_port <- ifelse(base > 0, pnl / base, 0)
    rdates <- dates[-1]
    bench_r <- lapply(names(cfg$BENCHMARKS), function(b) {
      q <- yahoo[[b]]; if (!isTRUE(q$ok)) return(NULL)
      a <- locf_on(q$adj, dates); r <- a[-1] / a[-nd] - 1; r[is.na(r)] <- 0; r
    })
    names(bench_r) <- names(cfg$BENCHMARKS)
    rf <- locf_on(fred[[cfg$RISK_FREE_SERIES]], rdates); rf[is.na(rf)] <- mean(rf, na.rm = TRUE)
    rf_d <- rf / 100 / 252
    keep <- utils::tail(seq_along(rdates), 252)
    stats_of <- function(r, label) {
      r <- r[keep]; dts <- rdates[keep]; rfd <- rf_d[keep]
      idx <- cumprod(1 + r)
      cumret <- function(k) if (length(r) >= k) 100 * (prod(1 + utils::tail(r, k)) - 1) else NA_real_
      yr_end <- as.Date(sprintf("%d-12-31", as.integer(format(max(dts), "%Y")) - 1))
      ytd <- 100 * (prod(1 + r[dts > yr_end]) - 1)
      vol <- stats::sd(r) * sqrt(252)
      out <- list(label = label, r1m = cumret(21), r3m = cumret(63), ytd = ytd, r1y = cumret(length(r)),
                  vol = 100 * vol, sharpe = if (vol > 0) mean(r - rfd) / stats::sd(r) * sqrt(252) else NA_real_,
                  mdd = 100 * min(idx / cummax(idx) - 1))
      for (b in names(bench_r)) {
        br <- bench_r[[b]]; if (is.null(br)) next; br <- br[keep]
        out[[paste0("beta_", b)]] <- if (stats::var(br) > 0) stats::cov(r, br) / stats::var(br) else NA_real_
        out[[paste0("corr_", b)]] <- suppressWarnings(stats::cor(r, br))
      }
      pb <- bench_r[[cfg$PRIMARY_BENCHMARK]]
      out$te <- if (!is.null(pb)) 100 * stats::sd(r - pb[keep]) * sqrt(252) else NA_real_
      out
    }
    perf <- c(list(stats_of(r_port, "Portfolio")),
              lapply(names(bench_r)[!vapply(bench_r, is.null, TRUE)], function(b) stats_of(bench_r[[b]], cfg$BENCHMARKS[[b]])))
    idx_series <- c(list(list(name = "Portfolio", values = round(100 * cumprod(1 + r_port[keep]), 3))),
                    lapply(names(bench_r)[!vapply(bench_r, is.null, TRUE)], function(b)
                      list(name = cfg$BENCHMARKS[[b]], values = round(100 * cumprod(1 + bench_r[[b]][keep]), 3))))
    index_chart <- list(dates = format(rdates[keep]), series = idx_series)
  }
  list(rows = tab, totals = totals, alloc = alloc, conc = conc, perf = perf, index_chart = index_chart,
       rf_label = cfg$RISK_FREE_SERIES, bench_primary = cfg$PRIMARY_BENCHMARK)
}
