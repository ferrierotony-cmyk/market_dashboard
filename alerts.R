# =============================================================================
#  alerts.R - rule-based alerts (inputs/alerts.csv) and desktop notifications.
#
#  A rule names a metric, an operator and a value. Three scopes:
#    market     one number from rates / credit / vol / FX / health, e.g. hy_oas.w1
#    portfolio  a portfolio total, e.g. port.day_pnl
#    symbol     a watchlist technical, evaluated for every name the target covers
#  The same evaluation runs in the browser (Rules editor) for instant previews,
#  so keep the two in step when adding metrics or operators.
# =============================================================================

SEV_RANK <- c(critical = 1, serious = 2, warning = 3, info = 4)
ALERT_OPS <- c(">", "<", ">=", "<=", "abs>", "abs<", "crosses_above", "crosses_below")
SYMBOL_METRICS <- c(last = "Last price", d1 = "1-day change (%)", w1 = "1-week change (%)", m1 = "1-month change (%)",
                    ytd = "Year-to-date change (%)", vol_x = "Volume vs 20-day average (x)", rsi = "RSI 14",
                    vs50 = "Distance from 50-day average (%)", vs200 = "Distance from 200-day average (%)",
                    pos52 = "Position in 52-week range (0-100)")
PORTFOLIO_METRICS <- c("port.day_pnl" = "Day P&L ($)", "port.day_pct" = "Day P&L (%)", "port.total_pnl" = "P&L since entry ($)",
                       "port.total_pct" = "P&L since entry (%)", "port.dv01" = "DV01 ($ per bp)", "port.cs01" = "CS01 ($ per bp)",
                       "port.duration" = "Duration (years)", "port.yield" = "Yield (%)",
                       "port.max_issuer_pct" = "Largest non-govt issuer (%)", "port.max_sector_pct" = "Largest non-govt sector (%)",
                       "port.top5_pct" = "Top 5 holdings (%)")

read_alert_rules <- function(path) {
  r <- read_input_csv(path)
  if (is.null(r)) return(NULL)
  for (k in c("id", "enabled", "scope", "target", "metric", "op", "value", "severity", "note")) if (is.null(r[[k]])) r[[k]] <- ""
  r$enabled <- toupper(trimws(r$enabled)) %in% c("Y", "YES", "TRUE", "1")
  r$scope <- tolower(trimws(r$scope)); r$op <- trimws(r$op); r$metric <- trimws(r$metric)
  r$severity <- tolower(trimws(r$severity)); r$severity[!r$severity %in% names(SEV_RANK)] <- "warning"
  r$id[!nzchar(r$id)] <- paste0("rule", seq_len(nrow(r)))[!nzchar(r$id)]
  r[r$scope %in% c("market", "portfolio", "symbol") & r$op %in% ALERT_OPS & nzchar(r$metric), ]
}

# ---- metric tables ------------------------------------------------------------
resolve_market_metrics <- function(cfg, S, Y, yahoo, health) {
  out <- list()
  for (nm in names(cfg$ALERT_MARKET_METRICS)) {
    m <- cfg$ALERT_MARKET_METRICS[[nm]]
    r <- list(label = m$label, unit = m$unit, v = NA_real_, d1 = NA_real_, w1 = NA_real_, m1 = NA_real_, ytd = NA_real_)
    if (m$src %in% c("fred", "derived")) {
      s <- S[[m$key]]
      if (!is.null(s) && !is.na(s$last)) {
        k <- if (m$unit == "yield") 100 else 1          # yield changes are reported in bp
        r$v <- s$last; r$d1 <- s$d1 * k; r$w1 <- s$w1 * k; r$m1 <- s$m1 * k; r$ytd <- s$ytd * k
      }
    } else if (m$src == "yahoo") {
      y <- Y[[m$key]]; q <- yahoo[[m$key]]
      if (!is.null(y) && !is.na(y$last)) {
        r$v <- y$last
        if (m$unit == "level") { r$d1 <- y$d1_abs; r$w1 <- y$w1_abs }
        else { r$d1 <- y$d1; r$w1 <- y$w1 }
        if (isTRUE(q$ok)) {
          h <- q$history; d <- as.Date(q$market_time)
          yr_end <- as.Date(sprintf("%d-12-31", as.integer(format(d, "%Y")) - 1))
          chg <- function(base) if (is.na(base)) NA_real_ else if (m$unit == "level") y$last - base else 100 * (y$last / base - 1)
          r$m1 <- chg(val_at(h, d - 30)); r$ytd <- chg(val_at(h, yr_end))
        }
      }
    } else if (m$src == "health") {
      if (!is.null(health) && !is.na(health$score)) r$v <- health$score
    }
    out[[nm]] <- r
  }
  out
}

symbol_metrics <- function(rows) {
  out <- list()
  for (r in rows) {
    if (!isTRUE(r$ok)) next
    out[[r$symbol]] <- list(label = r$label, sector = r$sector, type = r$type, detail = isTRUE(r$detail),
                            last = r$last, prev = r$prev, d1 = r$d1, w1 = r$w1, m1 = r$m1, ytd = r$ytd,
                            vol_x = r$vratio, rsi = r$rsi, vs50 = r$vs50, vs200 = r$vs200,
                            pos52 = if (is.na(r$pos52)) NA_real_ else 100 * r$pos52,
                            cross50 = r$cross50 %||% 0, cross200 = r$cross200 %||% 0, ts = r$ts)
  }
  out
}

portfolio_metrics <- function(port) {
  if (is.null(port)) return(list())
  tt <- port$totals; cc <- port$conc
  list("port.day_pnl" = tt$day, "port.day_pct" = tt$day_pct, "port.total_pnl" = tt$total_pnl, "port.total_pct" = tt$total_pct,
       "port.dv01" = tt$dv01, "port.cs01" = tt$cs01, "port.duration" = tt$duration, "port.yield" = tt$yield,
       "port.max_issuer_pct" = 100 * cc$max_issuer, "port.max_sector_pct" = 100 * cc$max_sector, "port.top5_pct" = 100 * cc$top5)
}

# ---- evaluation ------------------------------------------------------------------
cmp_rule <- function(op, v, x) {
  if (is.null(v) || is.na(v) || is.na(x)) return(FALSE)
  switch(op, ">" = v > x, "<" = v < x, ">=" = v >= x, "<=" = v <= x, "abs>" = abs(v) > x, "abs<" = abs(v) < x, FALSE)
}
fmt_metric <- function(v, unit, change = FALSE) {
  if (is.null(v) || is.na(v)) return("n/a")
  if (change) switch(unit, yield = sprintf("%+.0f bp", v), bp = sprintf("%+.0f bp", v), level = sprintf("%+.1f", v), sprintf("%+.2f%%", v))
  else switch(unit, yield = sprintf("%.2f%%", v), bp = sprintf("%.0f bp", v), level = sprintf("%.1f", v), sprintf("%s", format(round(v, 2), big.mark = ",")))
}
SUFFIX_WORD <- c(d1 = "1-day change", w1 = "1-week change", m1 = "1-month change", ytd = "YTD change")

alerts_compute <- function(rules, mkt, syms, pm) {
  if (is.null(rules) || !nrow(rules)) return(NULL)
  out <- list(); now <- Sys.time()
  add <- function(sev, sym, msg, ts, key) out[[length(out) + 1]] <<- data.frame(severity = sev, category = "Rule", symbol = sym, message = msg,
                                                                               time = format(as.POSIXct(ts, origin = "1970-01-01"), "%d %b %H:%M"),
                                                                               ts = as.numeric(ts), key = key, stringsAsFactors = FALSE)
  for (i in seq_len(nrow(rules))) {
    r <- rules[i, ]; if (!r$enabled) next
    x <- suppressWarnings(as.numeric(r$value))
    note <- if (nzchar(r$note)) r$note else r$id
    if (r$scope == "market") {
      parts <- strsplit(r$metric, ".", fixed = TRUE)[[1]]
      m <- mkt[[parts[1]]]; if (is.null(m)) next
      suf <- if (length(parts) > 1) parts[2] else ""
      v <- if (nzchar(suf)) m[[suf]] else m$v
      if (cmp_rule(r$op, v, x))
        add(r$severity, "Market", sprintf("%s: %s%s %s", note, m$label, if (nzchar(suf)) paste0(" ", SUFFIX_WORD[[suf]]) else "", fmt_metric(v, m$unit, nzchar(suf))),
            now, paste0(r$id, "|market"))
    } else if (r$scope == "portfolio") {
      v <- pm[[r$metric]]
      if (cmp_rule(r$op, v, x)) {
        lab <- PORTFOLIO_METRICS[r$metric]; if (is.na(lab)) lab <- r$metric
        vt <- if (grepl("pnl|dv01|cs01", r$metric)) paste0("$", format(round(v), big.mark = ",")) else sprintf("%.2f", v)
        add(r$severity, "Portfolio", sprintf("%s: %s %s", note, lab, vt), now, paste0(r$id, "|portfolio"))
      }
    } else if (r$scope == "symbol") {
      tg <- trimws(r$target); if (!nzchar(tg)) tg <- "*"
      pick <- if (tg == "*") names(syms) else if (tolower(tg) == "detail") names(syms)[vapply(syms, function(s) isTRUE(s$detail), TRUE)] else
        if (grepl("^sector:", tg, ignore.case = TRUE)) { sc <- tolower(trimws(sub("^sector:", "", tg, ignore.case = TRUE))); names(syms)[vapply(syms, function(s) tolower(s$sector) == sc, TRUE)] } else
          intersect(toupper(trimws(strsplit(tg, ",", fixed = TRUE)[[1]])), names(syms))
      for (s in pick) {
        sm <- syms[[s]]; fired <- FALSE; vt <- ""
        if (r$op %in% c("crosses_above", "crosses_below")) {
          up <- r$op == "crosses_above"; val <- tolower(trimws(r$value))
          if (val %in% c("sma50", "sma200")) { cr <- sm[[if (val == "sma50") "cross50" else "cross200"]]; fired <- !is.na(cr) && cr == (if (up) 1 else -1); vt <- paste("vs", toupper(val)) }
          else if (!is.na(x) && !is.na(sm$prev) && !is.na(sm$last)) { fired <- if (up) sm$prev < x && sm$last >= x else sm$prev > x && sm$last <= x; vt <- paste("through", x) }
        } else {
          v <- sm[[r$metric]]; if (is.null(v)) next
          fired <- cmp_rule(r$op, v, x)
          vt <- if (r$metric == "last") format(round(v, 2), big.mark = ",") else if (r$metric %in% c("vol_x")) sprintf("%.1fx", v) else if (r$metric == "rsi") sprintf("%.0f", v) else sprintf("%+.1f%%", v)
        }
        if (fired) add(r$severity, s, sprintf("%s (%s): %s %s%s", sm$label, s, SYMBOL_METRICS[r$metric] %||% r$metric, vt, if (nzchar(note)) paste0(". ", note) else ""),
                       if (!is.null(sm$ts) && !is.na(sm$ts)) sm$ts else now, paste0(r$id, "|", s))
      }
    }
  }
  if (length(out)) do.call(rbind, out) else NULL
}

# ---- desktop notification (Windows toast) ----------------------------------------
notify_new_alerts <- function(cfg, alerts, dash_dir, html_path) {
  if (!isTRUE(cfg$TOAST_ALERTS) || is.null(alerts) || !nrow(alerts)) return(invisible(0))
  min_sev <- SEV_RANK[[cfg$TOAST_MIN_SEVERITY %||% "warning"]]
  a <- alerts[SEV_RANK[alerts$severity] <= min_sev, ]
  if (!nrow(a)) return(invisible(0))
  state_path <- file.path(dash_dir, "logs", "alerts_state.json")
  state <- if (file.exists(state_path)) tryCatch(jsonlite::fromJSON(state_path, simplifyVector = FALSE), error = function(e) NULL) else NULL
  seen <- if (!is.null(state) && length(state$seen)) state$seen else list()
  now <- as.numeric(Sys.time()); window <- (cfg$TOAST_REPEAT_HOURS %||% 12) * 3600
  keys <- a$key
  fresh <- vapply(keys, function(k) is.null(seen[[k]]) || now - as.numeric(seen[[k]]) > window, TRUE)
  n <- sum(fresh)
  if (n > 0) {
    msgs <- a$message[fresh]
    body <- paste(utils::head(msgs, 3), collapse = "\n"); if (n > 3) body <- paste0(body, "\n+", n - 3, " more")
    title <- sprintf("%d new alert%s", n, if (n > 1) "s" else "")
    if (.Platform$OS.type == "windows") {
      ps1 <- file.path(dash_dir, "notify.ps1")
      args <- c("-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", shQuote(ps1),
                "-Title", shQuote(title), "-Message", shQuote(gsub("\"", "'", body)), "-Open", shQuote(html_path))
      # stderr goes to a file so a failed toast says why. One retry, since the first call right
      # after the PC wakes can fail while the notification service is still starting.
      err_file <- file.path(dash_dir, "logs", "notify_error.txt")
      run_toast <- function() tryCatch(system2("powershell.exe", args, stdout = FALSE, stderr = err_file, timeout = 30), error = function(e) 1L)
      rc <- run_toast()
      if (!identical(rc, 0L)) { Sys.sleep(5); rc <- run_toast() }
      detail <- if (!identical(rc, 0L)) {
        msg <- if (file.exists(err_file)) substr(paste(readLines(err_file, warn = FALSE), collapse = " "), 1, 200) else ""
        paste0(" (powershell returned an error, code ", rc, if (nzchar(msg)) paste0(": ", msg) else "", ")")
      } else ""
      logmsg("Toast: ", title, detail)
    } else logmsg("Toast skipped (not Windows): ", title, " - ", gsub("\n", " / ", body))
    for (k in keys[fresh]) seen[[k]] <- now
  }
  seen <- seen[vapply(seen, function(t) now - as.numeric(t) < 7 * 86400, TRUE)]
  dir.create(dirname(state_path), showWarnings = FALSE)
  jsonlite::write_json(list(seen = seen, updated = format(Sys.time())), state_path, auto_unbox = TRUE)
  invisible(n)
}
