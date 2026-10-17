# =============================================================================
#  build_dashboard.R - turn fetched data + analytics into the HTML dashboard
#  (single self-contained file: CSS, JS and data are inlined) plus a PNG
#  snapshot for email / Teams.
# =============================================================================
suppressPackageStartupMessages({
  library(ggplot2)
  library(gridExtra)
})

PAL <- c(blue = "#2a78d6", orange = "#eb6834", aqua = "#1baf7a", yellow = "#eda100",
         magenta = "#e87ba4", green = "#008300", violet = "#4a3aa7", red = "#e34948")
INK <- c(primary = "#0b0b0b", secondary = "#52514e", muted = "#898781", grid = "#e1e0d9", axis = "#c3c2b7")

# ---- HTML helpers -------------------------------------------------------------
esc <- function(x) {
  x <- as.character(x); x[is.na(x)] <- ""
  x <- gsub("&", "&amp;", x, fixed = TRUE); x <- gsub("<", "&lt;", x, fixed = TRUE)
  x <- gsub(">", "&gt;", x, fixed = TRUE); x <- gsub("'", "&#39;", x, fixed = TRUE)
  gsub("\"", "&quot;", x, fixed = TRUE)
}
nz <- function(x) !is.null(x) && length(x) > 0 && !all(is.na(x))
fmt_num <- function(x, d = 2, suffix = "", prefix = "") {
  x <- suppressWarnings(as.numeric(x))
  ifelse(is.na(x), "&ndash;", paste0(prefix, formatC(x, format = "f", digits = d, big.mark = ","), suffix))
}
fmt_chg <- function(x, d = 0, suffix = "", good_up = NA) {
  x <- suppressWarnings(as.numeric(x))
  vapply(x, function(v) {
    if (is.na(v)) return("<span class='flat'>&ndash;</span>")
    sgn <- if (v > 0) "+" else if (v < 0) "&minus;" else ""
    txt <- paste0(sgn, formatC(abs(v), format = "f", digits = d, big.mark = ","), suffix)
    cls <- "flat"
    if (!is.na(good_up) && abs(v) >= (10^-d) / 2) cls <- if ((v > 0) == good_up) "up" else "dn"
    sprintf("<span class='%s'>%s</span>", cls, txt)
  }, "")
}
fmt_money <- function(x, d = 0) fmt_num(x, d, "", "$")
html_table <- function(rows, headers, aligns = NULL, class = "tbl", row_attrs = NULL) {
  if (is.null(aligns)) aligns <- c("l", rep("r", length(headers) - 1))
  th <- paste0(sprintf("<th class='a%s' scope='col'>%s</th>", aligns, headers), collapse = "")
  body <- if (!length(rows)) sprintf("<tr><td colspan='%d' class='al muted'>No data</td></tr>", length(headers)) else
    paste0(vapply(seq_along(rows), function(i) {
      r <- rows[[i]]
      paste0("<tr", if (!is.null(row_attrs)) paste0(" ", row_attrs[i]) else "", ">",
             paste0(sprintf("<td class='a%s'>%s</td>", aligns, r), collapse = ""), "</tr>")
    }, ""), collapse = "\n")
  sprintf("<table class='%s'><thead><tr>%s</tr></thead><tbody>%s</tbody></table>", class, th, body)
}
read_input_csv <- function(path) {
  if (!file.exists(path)) return(NULL)
  x <- tryCatch(utils::read.csv(path, stringsAsFactors = FALSE, check.names = FALSE, strip.white = TRUE,
                                colClasses = "character", na.strings = character(0)),
                error = function(e) NULL)
  if (is.null(x) || !nrow(x)) return(NULL)
  x
}
why_html <- function(w) gsub(" | ", " &middot; ", esc(w), fixed = TRUE)   # "why it moved" lines use | as a locale-safe separator
chip <- function(status, text) sprintf("<span class='chip %s'>%s</span>", status, text)
STATUS_ICON <- c(good = "&#10003;", warn = "&#9650;", bad = "&#10007;", na = "&ndash;")
status_chip <- function(st, label) chip(st, paste(STATUS_ICON[[st]], label))
SEV_ICON <- c(critical = "&#10007;", serious = "&#9650;", warning = "&#9650;", info = "&#9432;")

widget <- function(id, title, body, w, h, sub = "", src = "", cls = "", hidden = FALSE) {
  # titles are written in this file (trusted) and may contain entities such as &amp;
  paste0("<section class='w ", cls, "' id='w-", id, "' data-id='", id, "' data-w='", w, "' data-h='", h,
         "' data-def-hidden='", if (hidden) "1" else "0", "' data-title='", gsub("'", "&#39;", title, fixed = TRUE), "'>",
         "<header class='wh'><span class='grip' title='Drag to move' aria-hidden='true'>&#10303;</span>",
         "<h2>", title, if (nzchar(sub)) paste0(" <span class='sub'>", sub, "</span>") else "", "</h2>",
         if (nzchar(src)) paste0("<span class='src' title='Data source and freshness'>", src, "</span>") else "",
         "<span class='wctl'></span></header><div class='wb'>", body, "</div>",
         "<span class='rz' title='Drag to resize' aria-hidden='true'></span></section>")
}
chart_div <- function(key, extra = "") paste0("<div class='chart ", extra, "' data-chart='", key, "'></div>")

spark_svg <- function(v, w = 84, h = 22, cls = "spark") {
  v <- suppressWarnings(as.numeric(v)); v <- v[!is.na(v)]
  if (length(v) < 2) return("")
  r <- range(v); if (r[2] == r[1]) r <- r + c(-1, 1)
  x <- seq(1, w - 3, length.out = length(v)); y <- (h - 3) - (v - r[1]) / diff(r) * (h - 6)
  sprintf("<svg class='%s' viewBox='0 0 %d %d' width='%d' height='%d' aria-hidden='true'><polyline points='%s'/><circle cx='%.1f' cy='%.1f' r='2.5'/></svg>",
          cls, w, h, w, h, paste(sprintf("%.1f,%.1f", x, y), collapse = " "), x[length(x)], y[length(y)])
}

arr <- function(x) I(as.vector(x))
ser <- function(name, df, digits = 4, from = NULL) {
  if (is.null(df) || !nrow(df)) return(NULL)
  if (!is.null(from)) df <- df[df$date >= from, ]
  list(name = name, dates = arr(format(df$date)), values = arr(round(df$value, digits)))
}
compact <- function(l) Filter(Negate(is.null), l)

# ---- ggplot theme for the PNG snapshot -----------------------------------------
theme_dash <- function(base = 9.5) {
  theme_minimal(base_size = base) +
    theme(panel.grid.minor = element_blank(),
          panel.grid.major = element_line(colour = INK[["grid"]], linewidth = 0.3),
          axis.text = element_text(colour = INK[["muted"]], size = base * 0.85),
          axis.title = element_blank(), axis.ticks = element_blank(),
          legend.position = "top", legend.justification = "left", legend.title = element_blank(),
          strip.text = element_text(colour = INK[["secondary"]], face = "bold", hjust = 0),
          plot.margin = margin(4, 10, 4, 4))
}

# =============================================================================
build_dashboard <- function(cfg, raw, inputs, dash_dir) {
  today <- Sys.Date()
  output_dir <- file.path(dash_dir, "output"); dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)
  fred <- normalize_fred(raw$fred, cfg)
  yahoo <- raw$yahoo
  ust_ids <- cfg$FRED_SERIES$ust
  ust_df <- function(t) fred[[ust_ids[[t]]]]
  derived <- derived_series(fred, ust_ids)

  S <- list()
  for (id in names(fred)) S[[id]] <- series_stats(fred[[id]])
  for (k in names(derived)) S[[k]] <- series_stats(derived[[k]])
  Y <- lapply(yahoo, pct_stats)

  st <- raw$status
  fallback <- st[st$mode == "cache-fallback", ]; failed <- st[st$mode == "failed", ]
  rates_asof <- S[["DGS10"]]$date; credit_asof <- S[["BAMLC0A0CM"]]$date
  live_time <- Y[["ES=F"]]$time
  live_asof <- if (nz(live_time)) format(live_time, "%d %b %H:%M %Z") else "n/a"
  rates_src  <- sprintf("FRED + Treasury.gov &middot; EOD &middot; %s", format(rates_asof, "%d %b"))
  credit_src <- sprintf("ICE BofA via FRED &middot; EOD &middot; %s", format(credit_asof, "%d %b"))
  live_src   <- sprintf("Yahoo &middot; delayed &le;15m &middot; %s", if (nz(live_time)) format(live_time, "%H:%M %Z") else "n/a")
  desk_src <- function(f) {
    p <- file.path(dash_dir, "inputs", f)
    if (file.exists(p)) sprintf("Desk CSV &middot; edited %s", format(file.mtime(p), "%d %b %H:%M")) else "Desk CSV (missing)"
  }
  charts <- list()

  # ===========================================================================
  #  MORNING VIEW
  # ===========================================================================
  tile_html <- vapply(cfg$KPI_TILES, function(t) {
    key <- t$key; kind <- t$kind
    if (key %in% names(Y)) {
      y <- Y[[key]]
      val <- if (kind == "px") fmt_num(y$last, if (!is.na(y$last) && y$last < 10) 4 else 2) else fmt_num(y$last, 2)
      gu <- kind == "px"
      c1 <- paste0("1d ", fmt_chg(y$d1, 2, "%", gu)); c2 <- paste0("1w ", fmt_chg(y$w1, 2, "%", gu))
      if (kind == "level") { c1 <- paste0("1d ", fmt_chg(y$d1_abs, 2, "", FALSE)); c2 <- paste0("1w ", fmt_chg(y$w1_abs, 2, "", FALSE)) }
    } else {
      s <- S[[key]] %||% series_stats(NULL)
      if (kind == "yield") {
        val <- fmt_num(s$last, 2, "%")
        c1 <- paste0("1d ", fmt_chg(s$d1 * 100, 0, "bp", FALSE)); c2 <- paste0("1w ", fmt_chg(s$w1 * 100, 0, "bp", FALSE))
      } else {
        val <- fmt_num(s$last, 0, " bp")
        c1 <- paste0("1d ", fmt_chg(s$d1, 0, "", FALSE)); c2 <- paste0("1w ", fmt_chg(s$w1, 0, "", FALSE))
      }
    }
    sprintf("<div class='tile'><div class='lbl'>%s</div><div class='val'>%s</div><div class='chg'>%s &nbsp; %s</div></div>",
            esc(t$label), val, c1, c2)
  }, "")

  tenors <- names(ust_ids)
  curve_rows <- lapply(tenors, function(tn) {
    s <- S[[ust_ids[[tn]]]] %||% series_stats(NULL)
    c(esc(tn), fmt_num(s$last, 2, "%"), fmt_chg(s$d1 * 100, 0, "", FALSE), fmt_chg(s$w1 * 100, 0, "", FALSE),
      fmt_chg(s$m1 * 100, 0, "", FALSE), fmt_chg(s$ytd * 100, 0, "", FALSE))
  })
  spread_rows <- lapply(c("2s10s", "5s30s", "3m10y"), function(k) {
    s <- S[[k]] %||% series_stats(NULL)
    c(esc(k), fmt_num(s$last, 0, " bp"), fmt_chg(s$d1, 0, "", NA), fmt_chg(s$w1, 0, "", NA),
      fmt_chg(s$m1, 0, "", NA), fmt_chg(s$ytd, 0, "", NA))
  })
  money_keys <- cfg$FRED_SERIES$money
  money_rows <- lapply(names(money_keys), function(lbl) {
    s <- S[[money_keys[[lbl]]]] %||% series_stats(NULL)
    d1 <- if (grepl("wkly", lbl, ignore.case = TRUE)) NA_real_ else s$d1 * 100
    c(esc(lbl), fmt_num(s$last, 2, "%"), fmt_chg(d1, 0, "", NA), fmt_chg(s$w1 * 100, 0, "", NA),
      fmt_chg(s$m1 * 100, 0, "", NA), esc(format(s$date, "%d %b")))
  })
  rates_html <- paste0(html_table(c(curve_rows, spread_rows), c("Tenor", "Yield", "1D bp", "1W bp", "1M bp", "YTD bp")),
                       "<div class='gap'></div>",
                       html_table(money_rows, c("Funding / inflation", "Level", "1D bp", "1W bp", "1M bp", "As of")))

  # curve / history / slope / OAS chart specs ---------------------------------------
  d10 <- S[["DGS10"]]$date
  curve_vals <- function(back) round(vapply(tenors, function(tn) val_at(ust_df(tn), d10 - back), 0), 3)
  charts[["m-curve"]] <- list(type = "line", x = "cat", cats = arr(tenors), fmt = "pct2",
                              series = list(list(name = "Latest", values = arr(curve_vals(0))),
                                            list(name = "1 week ago", values = arr(curve_vals(7))),
                                            list(name = "1 month ago", values = arr(curve_vals(30)))))
  yr <- today - 365
  charts[["m-hist"]] <- list(type = "line", x = "date", fmt = "pct2", endLabels = TRUE,
                             series = compact(list(ser("UST 2Y", ust_df("2Y"), from = yr), ser("UST 10Y", ust_df("10Y"), from = yr),
                                                   ser("UST 30Y", ust_df("30Y"), from = yr))))
  charts[["m-slope"]] <- list(type = "line", x = "date", fmt = "bp0", endLabels = TRUE, zero = TRUE,
                              series = compact(list(ser("2s10s", derived[["2s10s"]], 1, yr), ser("5s30s", derived[["5s30s"]], 1, yr))))
  charts[["m-oas-ig"]] <- list(type = "line", x = "date", fmt = "bp0", endLabels = TRUE, title = "US IG OAS (bp)",
                               series = compact(list(ser("US IG OAS", fred[["BAMLC0A0CM"]], 1, yr))))
  charts[["m-oas-hy"]] <- list(type = "line", x = "date", fmt = "bp0", endLabels = TRUE, title = "US HY OAS (bp)",
                               series = compact(list(ser("US HY OAS", fred[["BAMLH0A0HYM2"]], 1, yr))))
  charts[["m-oas-hy"]]$series[[1]]$color <- "--s2"

  # credit table ----------------------------------------------------------------------
  credit_row <- function(lbl, id, unit = "bp") {
    s <- S[[id]] %||% series_stats(NULL)
    rng <- if (is.na(s$pct1y)) "&ndash;" else sprintf("%s&ndash;%s <span class='muted'>(%d%%)</span>",
                                                       formatC(s$lo1y, format = "f", digits = 0), formatC(s$hi1y, format = "f", digits = 0), round(100 * s$pct1y))
    if (unit == "bp") c(esc(lbl), fmt_num(s$last, 0), fmt_chg(s$d1, 0, "", FALSE), fmt_chg(s$w1, 0, "", FALSE),
                        fmt_chg(s$m1, 0, "", FALSE), fmt_chg(s$ytd, 0, "", FALSE), rng)
    else c(esc(lbl), fmt_num(s$last, 2, "%"), fmt_chg(s$d1 * 100, 0, "", FALSE), fmt_chg(s$w1 * 100, 0, "", FALSE),
           fmt_chg(s$m1 * 100, 0, "", FALSE), fmt_chg(s$ytd * 100, 0, "", FALSE), "")
  }
  section_row <- function(lbl, n = 7) c(sprintf("<span class='sect'>%s</span>", lbl), rep("", n - 1))
  cr <- cfg$FRED_SERIES$credit_rating; cm <- cfg$FRED_SERIES$credit_maturity; co <- cfg$FRED_SERIES$credit_other
  credit_html <- html_table(c(list(section_row("By rating (OAS, bp)")), lapply(names(cr), function(l) credit_row(l, cr[[l]])),
                              list(section_row("IG by maturity (OAS, bp)")), lapply(names(cm), function(l) credit_row(l, cm[[l]])),
                              list(section_row("Other")), lapply(names(co), function(l) credit_row(l, co[[l]], if (grepl("Yield", l)) "pct" else "bp"))),
                            c("Index", "Level", "1D", "1W", "1M", "YTD", "1Y range (pos.)"))

  # overnight & risk table ----------------------------------------------------------
  ys <- cfg$YAHOO_SYMBOLS; risk_rows <- list(); last_group <- ""
  for (i in seq_len(nrow(ys))) {
    if (ys$group[i] != last_group) { risk_rows[[length(risk_rows) + 1]] <- section_row(esc(ys$group[i]), 5); last_group <- ys$group[i] }
    y <- Y[[ys$symbol[i]]] %||% pct_stats(list(ok = FALSE)); gu <- ys$issuer_friendly_up[i]
    dec <- if (is.na(y$last)) 2 else if (abs(y$last) < 10) 4 else if (abs(y$last) < 1000) 2 else 0
    if (ys$group[i] == "Volatility") { d1 <- fmt_chg(y$d1_abs, 2, "", gu); w1 <- fmt_chg(y$w1_abs, 2, "", gu) }
    else { d1 <- fmt_chg(y$d1, 2, "%", gu); w1 <- fmt_chg(y$w1, 1, "%", gu) }
    risk_rows[[length(risk_rows) + 1]] <- c(esc(ys$label[i]), fmt_num(y$last, dec), d1, w1,
                                            esc(if (nz(y$time)) format(y$time, "%d %b %H:%M") else "n/a"))
  }
  risk_html <- html_table(risk_rows, c("Instrument", "Last", "1D", "1W", "Last trade"))

  # issuance window -----------------------------------------------------------------
  metrics <- list(vix = Y[["^VIX"]]$last %||% S[["VIXCLS"]]$last, move = Y[["^MOVE"]]$last,
                  ig_w1 = S[["BAMLC0A0CM"]]$w1, hy_w1 = S[["BAMLH0A0HYM2"]]$w1, spx_d1 = Y[["ES=F"]]$d1,
                  ust10_absd1 = abs(S[["DGS10"]]$d1 * 100), ig_pct1y = S[["BAMLC0A0CM"]]$pct1y)
  grade_label <- c(good = "Supportive", warn = "Watch", bad = "Headwind", na = "n/a")
  score_rows <- character(0); pts <- numeric(0)
  for (r in cfg$ISSUANCE_RULES) {
    v <- metrics[[r$metric]]; g <- grade_rule(v, r); pts <- c(pts, POINTS[[g]])
    vtxt <- if (is.null(v) || is.na(v)) "&ndash;" else if (r$metric == "ig_pct1y") sprintf("%d%% of range", round(100 * v)) else
      if (r$metric == "spx_d1") sprintf("%+.2f%%", v) else formatC(v, format = "f", digits = if (abs(v) < 50) 1 else 0)
    score_rows <- c(score_rows, sprintf("<div class='score'><span>%s</span><span class='num'>%s</span>%s</div>",
                                        esc(r$name), vtxt, status_chip(g, grade_label[[g]])))
  }
  valid <- !is.na(pts)
  window <- if (!any(valid)) "na" else { ratio <- sum(pts[valid]) / (2 * sum(valid)); if (ratio >= 0.8) "good" else if (ratio >= 0.5) "warn" else "bad" }
  window_txt <- c(good = cfg$WINDOW_LABELS[["open"]], warn = cfg$WINDOW_LABELS[["selective"]],
                  bad = cfg$WINDOW_LABELS[["closed"]], na = "UNKNOWN")[[window]]

  # calendar --------------------------------------------------------------------------
  cal <- inputs$calendar
  if (!is.null(cal)) {
    cal$date <- suppressWarnings(as.Date(cal$date))
    for (col in c("time_et", "event", "importance", "notes")) if (is.null(cal[[col]])) cal[[col]] <- ""
    cal <- cal[!is.na(cal$date) & cal$date >= today, c("date", "time_et", "event", "importance", "notes")]
  }
  if (!is.null(raw$calendar)) {
    rc <- raw$calendar[raw$calendar$event %in% cfg$CALENDAR_RELEASES & raw$calendar$date >= today, ]
    if (nrow(rc)) {
      # FRED gives dates only. 08:30 ET is right for most of these releases and Consumer Confidence is 10:00.
      rc_time <- ifelse(rc$event == "Consumer Confidence", "10:00", "08:30")
      rc_imp  <- ifelse(rc$event %in% c("Producer Price Index", "Employment Cost Index", "Consumer Confidence"), "Med", "High")
      cal <- rbind(cal, data.frame(date = rc$date, time_et = rc_time, event = rc$event, importance = rc_imp,
                                   notes = "FRED release calendar", stringsAsFactors = FALSE))
    }
  }
  event_today <- FALSE; cal_rows <- list()
  if (!is.null(cal) && nrow(cal)) {
    cal <- cal[order(cal$date, cal$time_et), ]; cal <- cal[!duplicated(paste(cal$date, cal$event)), ]
    cal <- utils::head(cal, 10)
    event_today <- any(cal$date == today & tolower(cal$importance) == "high")
    cal_rows <- lapply(seq_len(nrow(cal)), function(i) {
      dlab <- if (cal$date[i] == today) "<b>Today</b>" else if (cal$date[i] == today + 1) "Tomorrow" else format(cal$date[i], "%a %d %b")
      imp <- tolower(cal$importance[i])
      c(dlab, esc(cal$time_et[i]), esc(cal$event[i]),
        chip(if (imp == "high") "bad" else if (imp == "med") "warn" else "na", esc(cal$importance[i])))
    })
  }
  cal_table <- html_table(cal_rows, c("When", "ET", "Event", "Imp."), aligns = c("l", "l", "l", "r"))
  window_html <- paste0("<div class='window'><span>Window:</span><span class='big ", window, "'>", STATUS_ICON[[window]], " ", window_txt, "</span>",
                        if (event_today) chip("bad", "High-impact event today") else "", "</div>",
                        paste(score_rows, collapse = "\n"), "<div class='gap'></div>", cal_table)

  # pipeline / comps ------------------------------------------------------------------
  stale <- cfg$STALE_DAYS %||% list(comps = 30, pipeline = 21, holdings_mark = 10)
  age_days <- function(d) as.numeric(today - suppressWarnings(as.Date(d)))
  pipe <- inputs$pipeline
  if (!is.null(pipe)) pipe <- pipe[!grepl("^\\s*example", pipe$issuer, ignore.case = TRUE), ]   # placeholder rows never show
  pipe_rows <- if (is.null(pipe) || !nrow(pipe)) list() else lapply(seq_len(nrow(pipe)), function(i) {
    ag <- age_days(pipe$pricing_date[i])
    st <- esc(pipe$status[i])
    if (!is.na(ag) && ag > stale$pipeline) st <- paste(st, chip("warn", sprintf("priced %dd ago", ag)))
    c(esc(pipe$issuer[i]), esc(pipe$rating[i]), fmt_num(pipe$size_mm[i], 0), esc(pipe$tenor[i]), esc(pipe$ipt[i]),
      st, esc(pipe$pricing_date[i]), esc(pipe$notes[i]))
  })
  pipe_html <- html_table(pipe_rows, c("Issuer", "Rating", "Size ($mm)", "Tenor", "IPT", "Status", "Pricing", "Notes"),
                          aligns = c("l", "l", "r", "l", "l", "l", "l", "l"))
  if (!length(pipe_rows)) pipe_html <- "<div class='muted pad'>No live deals. Add rows to inputs/pipeline.csv (issuer, rating, size_mm, tenor, ipt, status, pricing_date, notes).</div>"
  comps <- inputs$comps; comps_src <- desk_src("comps.csv"); comps_note <- ""
  if (!is.null(comps) && !is.null(raw$bbg_comps) && !is.null(comps$bbg_ticker)) {
    b <- raw$bbg_comps; m <- match(comps$bbg_ticker, b$bbg_ticker); hit <- !is.na(m)
    comps$yield[hit] <- b$yield[m[hit]]; comps$z_spread[hit] <- b$z_spread[m[hit]]
    comps$duration[hit] <- b$duration[m[hit]]; comps$rating[hit] <- b$rating[m[hit]]
    comps$as_of[hit] <- format(today); comps$source[hit] <- "Bloomberg (live)"
    if (any(hit)) comps_src <- sprintf("Bloomberg &middot; live &middot; %s", format(Sys.time(), "%H:%M"))
  }
  if (!is.null(comps) && nrow(comps)) {
    ag <- age_days(comps$as_of); old <- !is.na(ag) & ag > stale$comps
    if (any(old)) comps_note <- sprintf("<div class='note'>%s %d of %d comps are older than %d days and are hidden. Re-mark them in inputs/comps.csv (as_of column).</div>",
                                        status_chip("warn", "Stale"), sum(old), nrow(comps), stale$comps)
    comps <- comps[!old, ]
  }
  comps_rows <- if (is.null(comps) || !nrow(comps)) list() else lapply(order(-suppressWarnings(as.numeric(comps$z_spread))), function(i) {
    c(esc(comps$issuer[i]), esc(comps$bond[i]), esc(comps$rating[i]), fmt_num(comps$yield[i], 2, "%"),
      fmt_num(comps$z_spread[i], 0), fmt_num(comps$duration[i], 1), esc(comps$as_of[i]))
  })
  comps_html <- paste0(html_table(comps_rows, c("Issuer", "Bond", "Rtg", "Yield", "Z (bp)", "Dur", "As of"),
                                  aligns = c("l", "l", "l", "r", "r", "r", "r")), comps_note)
  comps_asof <- if (is.null(comps) || !nrow(comps)) "none current" else paste(unique(comps$as_of), collapse = ", ")

  # ===========================================================================
  #  ANALYTICS
  # ===========================================================================
  port   <- tryCatch(portfolio_compute(cfg, inputs$holdings, fred, yahoo, ust_ids),
                     error = function(e) { logmsg("portfolio failed: ", conditionMessage(e)); NULL })
  watch  <- if (!is.null(inputs$watchlist)) tryCatch(watch_compute(cfg, inputs$watchlist, yahoo, raw$news, raw$options),
                                                     error = function(e) { logmsg("watchlist failed: ", conditionMessage(e)); NULL }) else NULL
  health <- tryCatch(health_compute(cfg, S, Y, yahoo, fred), error = function(e) { logmsg("health failed: ", conditionMessage(e)); NULL })
  macro  <- tryCatch(macro_ribbon(fred, cfg, raw$calendar), error = function(e) { logmsg("macro failed: ", conditionMessage(e)); NULL })
  corr   <- tryCatch(corr_compute(cfg, fred, yahoo, derived), error = function(e) { logmsg("correlation failed: ", conditionMessage(e)); NULL })
  mk     <- tryCatch(market_compute(cfg, raw$market$data, if (!is.null(inputs$watchlist)) inputs$watchlist$symbol else character(0)),
                     error = function(e) { logmsg("market universe failed: ", conditionMessage(e)); NULL })

  # alerts: watchlist + portfolio concentration + red health indicators --------------
  alerts <- if (!is.null(watch)) watch$alerts else NULL
  add_alert <- function(sev, cat, sym, msg) alerts <<- rbind(alerts, data.frame(severity = sev, category = cat, symbol = sym,
                                                                                   message = msg, time = format(Sys.time(), "%d %b %H:%M"),
                                                                                   ts = as.numeric(Sys.time()), key = paste0(cat, "|", sym, "|", substr(msg, 1, 24)),
                                                                                   stringsAsFactors = FALSE))
  if (!is.null(port)) for (f in port$conc$flags) add_alert("serious", "Concentration", "Portfolio", f)
  if (!is.null(health)) for (d in health$domains) for (it in d$items) if (it$status == "bad")
    add_alert("warning", "Market health", d$name, sprintf("%s at %s (%s)", it$name, it$value_txt, it$rule))
  # rule-based alerts (inputs/alerts.csv) ------------------------------------------------
  rules <- read_alert_rules(file.path(dash_dir, "inputs", "alerts.csv"))
  mkt_metrics <- resolve_market_metrics(cfg, S, Y, yahoo, health)
  sym_metrics <- if (!is.null(watch)) symbol_metrics(watch$rows) else list()
  port_metrics <- portfolio_metrics(port)
  rule_alerts <- tryCatch(alerts_compute(rules, mkt_metrics, sym_metrics, port_metrics),
                          error = function(e) { logmsg("alert rules failed: ", conditionMessage(e)); NULL })
  if (!is.null(rule_alerts)) alerts <- rbind(alerts, rule_alerts)
  if (!is.null(mk) && !is.null(mk$alerts)) alerts <- rbind(alerts, mk$alerts)
  n_rules <- if (is.null(rules)) 0 else sum(rules$enabled)
  logmsg("Alert rules: ", n_rules, " enabled, ", if (is.null(rule_alerts)) 0 else nrow(rule_alerts), " fired")
  # an alert stamped long before the latest live quote comes from a stale cache: drop it
  n_stale_alerts <- 0
  if (!is.null(alerts) && nz(live_time)) {
    cut <- as.numeric(live_time) - (cfg$ALERT_MAX_AGE_HOURS %||% 36) * 3600
    old <- !is.na(alerts$ts) & alerts$ts < cut
    n_stale_alerts <- sum(old); alerts <- alerts[!old, ]
  }
  sev_rank <- c(critical = 1, serious = 2, warning = 3, info = 4)
  if (!is.null(alerts) && nrow(alerts)) alerts <- alerts[order(sev_rank[alerts$severity], -alerts$ts), ] else alerts <- NULL
  n_alerts <- if (is.null(alerts)) 0 else sum(alerts$severity != "info")

  # ---- portfolio snapshot for the morning view -------------------------------------
  port_snap <- if (is.null(port)) "<div class='muted pad'>No holdings (inputs/holdings.csv)</div>" else {
    tt <- port$totals
    rows <- list(c("Market value", fmt_money(tt$mv)),
                 c("Day P&amp;L", fmt_chg(tt$day, 0, "", TRUE)),
                 c("P&amp;L since entry", paste0(fmt_chg(tt$total_pnl, 0, "", TRUE), " <span class='muted'>(", fmt_chg(tt$total_pct, 2, "%", NA), ")</span>")),
                 c("DV01 / CS01", paste0(fmt_money(tt$dv01), " / ", fmt_money(tt$cs01))),
                 c("Yield / duration", paste0(fmt_num(tt$yield, 2, "%"), " / ", fmt_num(tt$duration, 1), "y")))
    paste0(html_table(rows, c("Portfolio", "")),
           if (length(port$conc$flags)) paste0("<div class='flagline'>", status_chip("bad", "Limit"), " ", esc(port$conc$flags[1]), "</div>") else "")
  }

  # ===========================================================================
  #  PORTFOLIO VIEW
  # ===========================================================================
  port_views <- ""
  if (!is.null(port)) {
    tt <- port$totals
    stat <- function(lbl, val, sub = "", hero = FALSE) sprintf("<div class='stat%s'><div class='lbl'>%s</div><div class='val'>%s</div><div class='chg'>%s</div></div>",
                                                              if (hero) " hero" else "", lbl, val, sub)
    summary_html <- paste0("<div class='stats'>",
      stat("Total market value", fmt_money(tt$mv), sprintf("%d holdings &middot; cost %s", tt$n, fmt_money(tt$cost_mv)), TRUE),
      stat("Day P&amp;L", fmt_chg(tt$day, 0, "", TRUE), fmt_chg(tt$day_pct, 2, "%", TRUE)),
      stat("P&amp;L since entry", fmt_chg(tt$total_pnl, 0, "", TRUE), paste0(fmt_chg(tt$total_pct, 2, "%", TRUE), " incl. carry")),
      stat("Price / carry P&amp;L", paste0(fmt_chg(tt$price_pnl, 0, "", TRUE)), paste0("carry ", fmt_chg(tt$carry_pnl, 0, "", TRUE))),
      stat("Yield (MV-wtd)", fmt_num(tt$yield, 2, "%"), "modeled"),
      stat("Duration", fmt_num(tt$duration, 2, "y"), "MV-weighted"),
      stat("DV01", fmt_money(tt$dv01), "per 1bp parallel"),
      stat("CS01", fmt_money(tt$cs01), "per 1bp spread"),
      "</div>")
    hold_rows <- lapply(Filter(function(r) isTRUE(r$ok), port$rows), function(r) {
      c(esc(r$name), esc(r$asset_class), esc(r$sector),
        if (r$per100) paste0(fmt_money(r$quantity / 1e6, 1), "mm") else fmt_num(r$quantity, 0),
        fmt_num(r$price, if (r$per100) 3 else 2), paste0("<span class='muted'>", esc(r$method), " &middot; ", esc(r$asof), "</span>",
                                                         if (!is.na(r$mark_age) && r$mark_age > stale$holdings_mark) paste0(" ", chip("warn", sprintf("mark %dd old", r$mark_age))) else ""),
        fmt_money(r$mv), fmt_num(100 * r$weight, 1, "%"), fmt_chg(r$day, 0, "", TRUE), fmt_chg(r$price_pnl, 0, "", TRUE),
        fmt_chg(r$carry_pnl, 0, "", TRUE), fmt_chg(r$total_pnl, 0, "", TRUE), fmt_num(r$duration, 2), fmt_money(r$dv01))
    })
    hold_rows <- c(hold_rows, list(c("<b>Total</b>", "", "", "", "", "", paste0("<b>", fmt_money(tt$mv), "</b>"), "100.0%",
                                     fmt_chg(tt$day, 0, "", TRUE), fmt_chg(tt$price_pnl, 0, "", TRUE), fmt_chg(tt$carry_pnl, 0, "", TRUE),
                                     fmt_chg(tt$total_pnl, 0, "", TRUE), fmt_num(tt$duration, 2), fmt_money(tt$dv01))))
    hold_html <- html_table(hold_rows, c("Holding", "Class", "Sector", "Qty / face", "Price", "Pricing &middot; as of", "Market value",
                                         "Weight", "Day P&amp;L", "Price P&amp;L", "Carry", "Total P&amp;L", "Dur", "DV01"),
                            aligns = c("l", "l", "l", "r", "r", "l", rep("r", 8)))
    for (k in names(port$alloc)) {
      a <- port$alloc[[k]]
      charts[[paste0("p-", k)]] <- list(type = "bar", labels = arr(a$labels), values = arr(a$values),
                                        fmt = if (k == "dv01") "money0" else "pct1")
    }
    cc <- port$conc; lim <- cfg$CONCENTRATION_LIMITS
    lim_row <- function(lbl, v, limit, name = "") {
      st <- if (is.na(v)) "na" else if (v > limit) "bad" else if (v > 0.8 * limit) "warn" else "good"
      c(lbl, paste0(fmt_num(100 * v, 1, "%"), if (nzchar(name)) paste0(" <span class='muted'>", esc(name), "</span>") else ""),
        fmt_num(100 * limit, 0, "%"), status_chip(st, c(good = "Within", warn = "Near", bad = "Breach", na = "n/a")[[st]]))
    }
    conc_html <- paste0(html_table(list(
      lim_row("Largest non-govt issuer", cc$max_issuer, lim$single_issuer_ex_govt, cc$max_issuer_name),
      lim_row("Largest non-govt sector", cc$max_sector, lim$sector_ex_govt, cc$max_sector_name),
      lim_row("Top 5 holdings", cc$top5, lim$top5)), c("Measure", "Current", "Limit", "Status"), aligns = c("l", "r", "r", "r")),
      "<div class='kv'><span>Herfindahl index</span><b>", fmt_num(cc$hhi, 3), "</b><span>Effective number of holdings</span><b>",
      fmt_num(cc$eff_n, 1), "</b></div>")
    perf_html <- "<div class='muted pad'>Not enough history</div>"
    if (!is.null(port$perf)) {
      bcols <- names(cfg$BENCHMARKS)
      prow <- lapply(port$perf, function(p) c(esc(p$label), fmt_chg(p$r1m, 2, "%", TRUE), fmt_chg(p$r3m, 2, "%", TRUE),
                                              fmt_chg(p$ytd, 2, "%", TRUE), fmt_chg(p$r1y, 2, "%", TRUE), fmt_num(p$vol, 2, "%"),
                                              fmt_num(p$sharpe, 2), fmt_num(p$mdd, 2, "%"),
                                              fmt_num(p[[paste0("beta_", cfg$PRIMARY_BENCHMARK)]], 2), fmt_num(p$beta_SPY, 2),
                                              fmt_num(p[[paste0("corr_", cfg$PRIMARY_BENCHMARK)]], 2), fmt_num(p$te, 2, "%")))
      perf_html <- html_table(prow, c("Series", "1M", "3M", "YTD", "1Y", "Ann. vol", "Sharpe", "Max DD",
                                      paste("Beta", cfg$PRIMARY_BENCHMARK), "Beta SPY", paste("Corr", cfg$PRIMARY_BENCHMARK),
                                      paste("TE vs", cfg$PRIMARY_BENCHMARK)))
      perf_html <- paste0(perf_html, "<div class='note'>Total return, current holdings held constant over the window (bonds: modeled price + carry; benchmarks: dividend-adjusted ETF prices). Sharpe uses ",
                          esc(cfg$RISK_FREE_SERIES), " as the risk-free rate.</div>")
      ic <- port$index_chart
      charts[["p-perf"]] <- list(type = "line", x = "date", fmt = "idx", endLabels = TRUE,
                                 series = lapply(ic$series, function(s) list(name = s$name, dates = arr(ic$dates), values = arr(s$values))))
    }
    port_src <- sprintf("Model (EOD %s) + Yahoo &middot; %s", format(rates_asof, "%d %b"), desk_src("holdings.csv"))
    port_views <- paste0(
      widget("p-summary", "Portfolio summary", summary_html, 12, 2, src = port_src),
      widget("p-holdings", "Holdings", paste0("<div class='scroll'>", hold_html, "</div>"), 8, 6, sub = "inputs/holdings.csv"),
      widget("p-asset_class", "Allocation by asset class", chart_div("p-asset_class"), 4, 3, sub = "% of market value"),
      widget("p-sector", "Allocation by sector", chart_div("p-sector"), 4, 3, sub = "% of market value"),
      widget("p-perf", "Performance vs benchmarks", chart_div("p-perf"), 8, 5, sub = "indexed to 100, 1 year", src = "Holdings-based backtest"),
      widget("p-top", "Top holdings", chart_div("p-top"), 4, 5, sub = "% of market value"),
      widget("p-stats", "Return &amp; risk statistics", paste0("<div class='scroll'>", perf_html, "</div>"), 8, 4, sub = "trailing, daily data"),
      widget("p-dv01", "DV01 by curve point", chart_div("p-dv01"), 4, 4, sub = "$ per 1bp"),
      widget("p-conc", "Concentration", conc_html, 4, 4, sub = "limits in config.R"),
      if (!is.null(port$alloc$rating)) widget("p-rating", "Allocation by rating", chart_div("p-rating"), 4, 4) else "")
  }

  # ===========================================================================
  #  WATCHLIST & ALERTS VIEW
  # ===========================================================================
  sev_word <- c(critical = "Critical", serious = "Serious", warning = "Warning", info = "Info")
  alert_items <- function(a) paste0(sprintf("<li class='sev-%s'><span class='sev'>%s %s</span><span class='cat'>%s</span><span class='sym'>%s</span><span class='msg'>%s</span><span class='when'>%s</span></li>",
                                            a$severity, SEV_ICON[a$severity], sev_word[a$severity], esc(a$category),
                                            esc(a$symbol), esc(a$message), esc(a$time)), collapse = "")
  rules_tool <- paste0("<div class='ctool'><button type='button' id='rulesBtn' aria-expanded='false'>Edit rules</button>",
                       sprintf("<span class='muted'>%d rule%s enabled &middot; %d fired &middot; rules live in inputs/alerts.csv</span></div>",
                               n_rules, if (n_rules == 1) "" else "s", if (is.null(rule_alerts)) 0 else nrow(rule_alerts)),
                       "<div id='rulesPanel' class='rules' hidden></div>")
  stale_note <- if (n_stale_alerts > 0) sprintf("<div class='note'>%d alert%s from stale (cached) quotes hidden.</div>", n_stale_alerts, if (n_stale_alerts > 1) "s" else "") else ""
  alerts_html <- if (is.null(alerts) || !nrow(alerts)) paste0("<div class='muted pad'>No alerts triggered</div>", stale_note) else {
    main <- alerts[alerts$severity != "info", ]; info <- alerts[alerts$severity == "info", ]
    paste0(if (nrow(main)) paste0("<ul class='alerts'>", alert_items(main), "</ul>") else "<div class='muted pad'>No warnings</div>",
           if (nrow(info)) paste0("<details class='infoalerts'><summary>", nrow(info), " informational (RSI extremes, headline keywords)</summary><ul class='alerts'>",
                                  alert_items(info), "</ul></details>") else "", stale_note)
  }
  watch_html <- "<div class='muted pad'>No watchlist (inputs/watchlist.csv)</div>"; watch_tool <- ""
  news_html <- "<div class='muted pad'>No headlines</div>"; opts_html <- "<div class='muted pad'>No option chains</div>"
  movers_html <- "<div class='muted pad'>No watchlist</div>"; sectors_html <- movers_html
  side_html <- ""
  if (!is.null(watch)) {
    wrows <- lapply(watch$rows, function(r) {
      if (!isTRUE(r$ok)) return(c(esc(r$label), esc(r$symbol), esc(r$sector), rep("&ndash;", 11)))
      dec <- if (abs(r$last) < 10) 4 else if (abs(r$last) < 1000) 2 else 0
      c(paste0("<b>", esc(r$label), "</b>"), esc(r$symbol), esc(r$sector), fmt_num(r$last, dec), fmt_chg(r$d1, 2, "%", TRUE), fmt_chg(r$w1, 1, "%", TRUE),
        fmt_chg(r$m1, 1, "%", TRUE), fmt_chg(r$ytd, 1, "%", TRUE), spark_svg(r$spark),
        if (is.na(r$vratio)) "&ndash;" else paste0(if (r$vratio >= 2) "<b>" else "", sprintf("%.1fx", r$vratio), if (r$vratio >= 2) "</b>" else ""),
        fmt_num(r$rsi, 0), fmt_chg(r$vs50, 1, "%", NA), fmt_chg(r$vs200, 1, "%", NA),
        paste0(esc(r$time), " <span class='muted'>(", esc(r$delay), ")</span>", if (isTRUE(r$stale)) paste0(" ", chip("warn", "cached")) else ""))
    })
    row_link <- function(r) sprintf("class='rowlink' tabindex='0' data-sym='%s' data-name='%s' data-sector='%s' title='%s'",
                                    esc(r$symbol), esc(r$label), esc(r$sector), why_html(r$why %||% "Open chart"))
    wattrs <- vapply(watch$rows, row_link, "")
    watch_html <- html_table(wrows, c("Name", "Symbol", "Sector", "Last", "1D", "1W", "1M", "YTD", "60D trend", "Vol vs 20D", "RSI 14",
                                      "vs 50D", "vs 200D", "Last trade (delay)"),
                             aligns = c("l", "l", "l", rep("r", 5), "c", rep("r", 4), "r"), row_attrs = wattrs, class = "tbl sort")
    sect_opts <- paste0(vapply(sort(unique(vapply(watch$rows, function(r) r$sector, ""))), function(s) sprintf("<option value='%s'>%s</option>", esc(s), esc(s)), ""), collapse = "")
    watch_tool <- paste0("<div class='ctool'><input type='search' id='wfilter' placeholder='Filter by name, symbol or sector' aria-label='Filter watchlist'>",
                         "<select id='wsector' aria-label='Sector'><option value=''>All sectors</option>", sect_opts, "</select>",
                         "<span class='muted' id='wcount'></span><span class='muted'>Click a column header to sort</span></div>")
    # movers and sector summary (equities only)
    mover_rows <- function(lst) lapply(lst, function(r) c(sprintf("<b>%s</b> <span class='muted'>%s</span>%s", esc(r$label), esc(r$symbol),
                                                                   if (nzchar(r$why %||% "")) paste0("<span class='why'>", why_html(r$why), "</span>") else ""), esc(r$sector),
                                                           fmt_num(r$last, if (abs(r$last) < 10) 4 else 2), fmt_chg(r$d1, 2, "%", TRUE),
                                                           if (is.na(r$vratio)) "&ndash;" else sprintf("%.1fx", r$vratio)))
    mover_table <- function(lst) html_table(mover_rows(lst), c("Name", "Sector", "Last", "1D", "Vol/20D"), aligns = c("l", "l", "r", "r", "r"),
                                            row_attrs = vapply(lst, row_link, ""))
    movers_html <- if (is.null(watch$movers)) "<div class='muted pad'>No equities in the watchlist</div>" else paste0(
      "<div class='movers'><div><h3>Gainers <span class='muted'>", watch$movers$n_up, " of ", watch$movers$n, " up</span></h3>", mover_table(watch$movers$up), "</div>",
      "<div><h3>Losers <span class='muted'>", watch$movers$n_down, " of ", watch$movers$n, " down</span></h3>", mover_table(watch$movers$down), "</div></div>")
    sectors_html <- if (is.null(watch$sectors)) "<div class='muted pad'>No equities in the watchlist</div>" else html_table(
      lapply(watch$sectors, function(s) c(esc(s$sector), s$n, fmt_chg(s$d1, 2, "%", TRUE), fmt_chg(s$w1, 1, "%", TRUE), fmt_chg(s$m1, 1, "%", TRUE),
                                          fmt_chg(s$ytd, 1, "%", TRUE), sprintf("<span class='up'>%d</span> / <span class='dn'>%d</span>", s$up, s$down),
                                          sprintf("%s %s", esc(s$best$label), fmt_chg(s$best$d1, 1, "%", TRUE)),
                                          sprintf("%s %s", esc(s$worst$label), fmt_chg(s$worst$d1, 1, "%", TRUE)))),
      c("Sector", "#", "Avg 1D", "Avg 1W", "Avg 1M", "Avg YTD", "Up / down", "Best today", "Worst today"),
      aligns = c("l", "r", "r", "r", "r", "r", "r", "l", "l"), class = "tbl sort")
    safe_link <- function(u) if (grepl("^https://", u)) esc(u) else ""
    news_item <- function(n) sprintf("<li%s><a href='%s' target='_blank' rel='noopener noreferrer'>%s</a>%s<span class='meta'>%s &middot; %s &middot; <time data-iso='%s'>%s</time>%s</span></li>",
                                     if (nzchar(n$summary %||% "")) " class='hassum' tabindex='0' title='Click to expand the summary'" else "",
                                     safe_link(n$link), esc(n$title),
                                     if (nzchar(n$summary %||% "")) paste0("<p class='sum'>", esc(n$summary), "</p>") else "",
                                     esc(n$label), esc(n$publisher), esc(n$time), esc(substr(n$time, 1, 16)),
                                     if (nzchar(n$flag)) paste0(" ", chip("warn", paste("flag:", esc(n$flag)))) else "")
    if (length(watch$news)) {
      ord <- order(vapply(watch$news, function(n) n$time, ""), decreasing = TRUE)
      news_html <- paste0("<ul class='news'>", paste0(vapply(watch$news[ord], news_item, ""), collapse = ""), "</ul>")
    }
    if (length(watch$options)) {
      orows <- lapply(watch$options, function(o) {
        u <- o$top[1, ]
        c(paste0("<b>", esc(o$label), "</b>"), fmt_num(o$call_vol, 0), fmt_num(o$put_vol, 0),
          if (is.na(o$pc)) "&ndash;" else sprintf("%.2f", o$pc), fmt_num(o$oi, 0), fmt_num(o$iv30, 1, "%"),
          fmt_chg(o$iv30_change, 2, "", NA),
          if (!nrow(o$top)) "&ndash;" else sprintf("%s %s %g &middot; %s vol / %s OI", if (u$type == "C") "Call" else "Put",
                                                                format(as.Date(u$expiry), "%d %b %y"), u$strike, format(u$volume, big.mark = ","), format(u$oi, big.mark = ",")),
          if (o$n_unusual > 0) status_chip("warn", paste(o$n_unusual, "unusual")) else "")
      })
      opts_html <- paste0(html_table(orows, c("Underlying", "Call vol", "Put vol", "P/C", "Open int.", "IV30", "IV30 chg (pts)", "Most active contract", ""),
                                     aligns = c("l", rep("r", 6), "l", "r")),
                          sprintf("<div class='note'>Most active and unusual exclude contracts expiring within 2 days. Unusual = contract volume &ge; %s and &ge; %.1fx open interest. P/C flagged above %.2f or below %.2f.</div>",
                                  format(cfg$OPTIONS_RULES$min_contract_volume, big.mark = ","), cfg$OPTIONS_RULES$vol_oi_ratio,
                                  cfg$OPTIONS_RULES$pc_high, cfg$OPTIONS_RULES$pc_low))
    }
    # per-symbol side panels for the chart view
    side_html <- paste0(vapply(watch$rows, function(r) {
      if (!isTRUE(r$ok)) return("")
      y <- yahoo[[r$symbol]]; b <- y$daily; nb <- nrow(b)
      w52 <- utils::tail(b$c, 252); pos <- if (!is.na(r$pos52)) round(100 * r$pos52) else NA
      o <- if (!is.null(watch$options)) Filter(function(x) x$symbol == r$symbol, watch$options) else list()
      nn <- Filter(function(n) n$symbol == r$symbol, watch$news)
      dec <- if (abs(r$last) < 10) 4 else if (abs(r$last) < 1000) 2 else 0
      kv <- function(k, v) sprintf("<span>%s</span><b>%s</b>", k, v)
      paste0("<div class='symside' data-sym='", esc(r$symbol), "' hidden>",
             "<div class='symhead'><div class='lbl'>", esc(r$label), " &middot; ", esc(y$exchange), "</div><div class='val'>", fmt_num(r$last, dec),
             " <small>", fmt_chg(r$d1, 2, "%", TRUE), "</small></div><div class='muted'>", esc(r$time), " &middot; delay ", esc(r$delay), " &middot; ", esc(y$currency), "</div>",
             if (nzchar(r$why %||% "")) paste0("<div class='why'>", why_html(r$why), "</div>") else "", "</div>",
             "<div class='kv'>", kv("Day range", paste(fmt_num(b$l[nb], dec), "&ndash;", fmt_num(b$h[nb], dec))),
             kv("52w range", paste(fmt_num(min(w52), dec), "&ndash;", fmt_num(max(w52), dec))),
             kv("Position in 52w range", if (is.na(pos)) "&ndash;" else paste0(pos, "%")),
             kv("1W / 1M / YTD", paste(fmt_chg(r$w1, 1, "%", TRUE), fmt_chg(r$m1, 1, "%", TRUE), fmt_chg(r$ytd, 1, "%", TRUE))),
             kv("RSI(14)", fmt_num(r$rsi, 0)), kv("vs 50D / 200D", paste(fmt_chg(r$vs50, 1, "%", NA), "/", fmt_chg(r$vs200, 1, "%", NA))),
             kv("Volume vs 20D avg", if (is.na(r$vratio)) "&ndash;" else sprintf("%.1fx", r$vratio)),
             if (length(o)) paste0(kv("Options P/C (vol)", if (is.na(o[[1]]$pc)) "&ndash;" else sprintf("%.2f", o[[1]]$pc)),
                                   kv("IV30", fmt_num(o[[1]]$iv30, 1, "%"))) else "",
             "</div>",
             if (length(nn)) paste0("<h3>Headlines</h3><ul class='news'>", paste0(vapply(utils::head(nn, 4), news_item, ""), collapse = ""), "</ul>") else "",
             "</div>")
    }, ""), collapse = "")
  }

  # ===========================================================================
  #  MARKET VIEW (whole-market snapshot)
  # ===========================================================================
  market_views <- ""; market_src <- "Nasdaq + Yahoo"; universe_js <- "window.MMD_UNIVERSE=null;"
  if (!is.null(mk)) {
    b <- mk$breadth; mm <- raw$market
    market_src <- sprintf("%s &middot; delayed &le;15m &middot; %s", esc(mm$source %||% "Nasdaq + Yahoo"), esc(mm$asof %||% ""))
    mtile <- function(lbl, val, sub = "", cls = "") sprintf("<div class='tile'><div class='lbl'>%s</div><div class='val %s'>%s</div><div class='chg'>%s</div></div>", lbl, cls, val, sub)
    ad_cls <- if (b$up > b$down) "up" else if (b$up < b$down) "dn" else ""
    breadth_html <- paste0("<div class='tiles mtiles'>",
      mtile("Advancers / decliners", sprintf("<span class='up'>%s</span> / <span class='dn'>%s</span>", format(b$up, big.mark = ","), format(b$down, big.mark = ",")), sprintf("%s names &middot; %s unchanged", format(b$n, big.mark = ","), b$unch)),
      mtile("Median move", fmt_chg(b$median, 2, "%", TRUE), paste0("cap-weighted ", fmt_chg(b$cap_wtd, 2, "%", TRUE))),
      mtile("Above 200-day avg", fmt_num(b$above200, 0, "%"), paste0("above 50-day ", fmt_num(b$above50, 0, "%"))),
      mtile("New 52w highs / lows", sprintf("<span class='up'>%d</span> / <span class='dn'>%d</span>", b$new_highs, b$new_lows), "closing within 0.1% of the range edge"),
      mtile("Up vs down $ volume", sprintf("<span class='up'>$%s</span> / <span class='dn'>$%s</span>", fmt_cap(b$up_dollar), fmt_cap(b$down_dollar)),
            sprintf("%.0f%% of dollars in rising names", 100 * b$up_dollar / max(1, b$up_dollar + b$down_dollar))),
      mtile("Moves of 10%+", sprintf("<span class='up'>%d</span> up / <span class='dn'>%d</span> down", b$big_up, b$big_down), "any size, before liquidity floors"),
      "</div>")
    sec_rows <- lapply(mk$sectors, function(s) c(esc(s$sector), s$n, fmt_chg(s$cap_wtd, 2, "%", TRUE), fmt_chg(s$avg, 2, "%", TRUE), fmt_chg(s$median, 2, "%", TRUE),
                                                   sprintf("<span class='up'>%d</span> / <span class='dn'>%d</span>", s$up, s$down), fmt_num(s$above200, 0, "%"),
                                                   sprintf("%s <span class='muted'>%s</span> %s", esc(s$best$name), esc(s$best$symbol), fmt_chg(s$best$chg_pct, 1, "%", TRUE)),
                                                   sprintf("%s <span class='muted'>%s</span> %s", esc(s$worst$name), esc(s$worst$symbol), fmt_chg(s$worst$chg_pct, 1, "%", TRUE))))
    sectors_mk <- html_table(sec_rows, c("Sector", "#", "Cap-wtd 1D", "Avg 1D", "Median 1D", "Up / down", "&gt; 200D", "Best today (liquid)", "Worst today (liquid)"),
                             aligns = c("l", "r", "r", "r", "r", "r", "r", "l", "l"), class = "tbl sort")
    cap_word <- c(mega = "Mega ($200B+)", large = "Large ($10-200B)", mid = "Mid ($2-10B)", small = "Small ($300M-2B)", micro = "Micro (&lt;$300M)")
    cap_rows <- lapply(mk$caps, function(cp) c(cap_word[[cp$bucket]], cp$n, fmt_chg(cp$avg, 2, "%", TRUE), fmt_chg(cp$median, 2, "%", TRUE),
                                               sprintf("<span class='up'>%d</span> / <span class='dn'>%d</span>", cp$up, cp$down), fmt_num(cp$above200, 0, "%"),
                                               sprintf("<span class='up'>%d</span> / <span class='dn'>%d</span>", cp$new_highs, cp$new_lows)))
    caps_html <- html_table(cap_rows, c("Size", "#", "Avg 1D", "Median 1D", "Up / down", "&gt; 200D", "52w hi / lo"), aligns = c("l", rep("r", 6)))
    mrow <- function(df) lapply(seq_len(nrow(df)), function(i) { h <- df[i, ]
      c(sprintf("<b>%s</b> <span class='muted'>%s</span>%s", esc(h$name), esc(h$symbol), if (isTRUE(h$in_watch)) " <span class='chip na'>watchlist</span>" else ""),
        esc(h$sector), fmt_num(h$last, if (!is.na(h$last) && h$last < 10) 3 else 2), fmt_chg(h$chg_pct, 2, "%", TRUE),
        if (is.na(h$vol_x)) "&ndash;" else sprintf("%.1fx", h$vol_x), paste0("$", fmt_cap(h$mcap))) })
    mtable <- function(df) html_table(mrow(df), c("Name", "Sector", "Last", "1D", "Vol/3M", "Mkt cap"), aligns = c("l", "l", "r", "r", "r", "r"),
                                      row_attrs = vapply(seq_len(nrow(df)), function(i) sprintf("class='mrow' data-sym='%s'", esc(df$symbol[i])), ""))
    movers_block <- function(m, lbl) paste0("<div class='movers'><div><h3>", lbl, " gainers</h3>", mtable(m$up), "</div><div><h3>", lbl, " losers</h3>", mtable(m$down), "</div></div>")
    vol_rows <- lapply(seq_len(nrow(mk$volume)), function(i) { h <- mk$volume[i, ]
      c(sprintf("<b>%s</b> <span class='muted'>%s</span>", esc(h$name), esc(h$symbol)), esc(h$sector), sprintf("<b>%.1fx</b>", h$vol_x), fmt_chg(h$chg_pct, 2, "%", TRUE), paste0("$", fmt_cap(h$dollar_vol)), paste0("$", fmt_cap(h$mcap))) })
    vol_html <- html_table(vol_rows, c("Name", "Sector", "Vol/3M", "1D", "$ traded", "Mkt cap"), aligns = c("l", "l", "r", "r", "r", "r"))
    hl_rows <- function(df) lapply(seq_len(nrow(df)), function(i) { h <- df[i, ]
      c(sprintf("<b>%s</b> <span class='muted'>%s</span>", esc(h$name), esc(h$symbol)), esc(h$sector), fmt_num(h$last, 2), fmt_chg(h$chg_pct, 2, "%", TRUE), paste0("$", fmt_cap(h$mcap))) })
    hl_html <- paste0("<div class='movers'><div><h3>New 52-week highs <span class='muted'>$2B+</span></h3>", html_table(hl_rows(mk$highs), c("Name", "Sector", "Last", "1D", "Mkt cap"), aligns = c("l", "l", "r", "r", "r")),
                      "</div><div><h3>New 52-week lows <span class='muted'>$2B+</span></h3>", html_table(hl_rows(mk$lows), c("Name", "Sector", "Last", "1D", "Mkt cap"), aligns = c("l", "l", "r", "r", "r")), "</div></div>")
    sec_opts <- paste0(vapply(vapply(mk$sectors, function(s) s$sector, ""), function(x) sprintf("<option value='%s'>%s</option>", esc(x), esc(x)), ""), collapse = "")
    screener_html <- paste0("<div class='ctool'><input type='search' id='sfilter' placeholder='Symbol or name' aria-label='Filter'>",
                            "<select id='ssector' aria-label='Sector'><option value=''>All sectors</option>", sec_opts, "</select>",
                            "<select id='sbucket' aria-label='Size'><option value=''>All sizes</option><option value='mega'>Mega $200B+</option><option value='large'>Large $10-200B</option><option value='mid'>Mid $2-10B</option><option value='small'>Small $300M-2B</option><option value='micro'>Micro</option></select>",
                            "<select id='smin' aria-label='Minimum dollar volume'><option value='0'>Any $ volume</option><option value='1e6'>$1M+ traded</option><option value='1e7' selected>$10M+ traded</option><option value='1e8'>$100M+ traded</option></select>",
                            "<label class='tog'><input type='checkbox' id='swatch'><span>Watchlist only</span></label>",
                            "<span class='muted' id='scount'></span><span class='muted'>Click a header to sort</span></div>",
                            "<div class='screener' id='screener'></div>")
    market_views <- paste0(
      widget("k-breadth", "Market breadth", breadth_html, 12, 2, src = market_src, cls = "bare"),
      widget("k-sectors", "Sectors", paste0("<div class='scroll'>", sectors_mk, "</div>"), 7, 5, sub = sprintf("%s common stocks, every listed name", format(mk$n_kept, big.mark = ",")), src = market_src),
      widget("k-caps", "By size", paste0("<div class='scroll'>", caps_html, "</div>"), 5, 5, sub = "market-cap buckets", src = market_src),
      widget("k-large", "Large caps", paste0("<div class='scroll'>", movers_block(mk$movers$large, "Large-cap"), "</div>"), 6, 6, sub = "$10B+, $5M+ traded", src = market_src),
      widget("k-small", "Mid &amp; small caps", paste0("<div class='scroll'>", movers_block(mk$movers$mid, "Mid-cap"), movers_block(mk$movers$small, "Small-cap"), "</div>"), 6, 6, sub = "$5M+ traded", src = market_src),
      widget("k-volume", "Unusual volume", paste0("<div class='scroll'>", vol_html, "</div>"), 5, 5, sub = "vs 3-month average, $300M+ cap", src = market_src),
      widget("k-highlow", "52-week highs &amp; lows", paste0("<div class='scroll'>", hl_html, "</div>"), 7, 5, src = market_src),
      widget("k-screener", "Screener", screener_html, 12, 8, sub = "every name, filter and sort", src = market_src))
    ucols <- c("symbol", "name", "sector", "industry", "exchange", "last", "chg_pct", "volume", "vol_x", "dollar_vol", "mcap", "bucket", "pos52", "vs50", "vs200", "hi52", "lo52", "new_high", "new_low", "in_watch")
    ur <- mk$rows[, ucols]
    for (k in c("last", "chg_pct", "vol_x", "pos52", "vs50", "vs200", "hi52", "lo52")) ur[[k]] <- round(ur[[k]], 3)
    for (k in c("volume", "dollar_vol", "mcap")) ur[[k]] <- round(ur[[k]])
    universe_js <- paste0("window.MMD_UNIVERSE=", jsonlite::toJSON(list(asof = mm$asof %||% "", source = mm$source %||% "", cols = ucols, rows = ur),
                                                                   auto_unbox = TRUE, na = "null", null = "null", digits = 6, dataframe = "values"), ";")
  }

  # ===========================================================================
  #  MACRO & HEALTH VIEW
  # ===========================================================================
  health_html <- "<div class='muted pad'>Unavailable</div>"; domains_html <- ""
  if (!is.null(health)) {
    health_html <- paste0("<div class='health'><div class='hscore ", health$status, "'><div class='num'>", health$score %||% "&ndash;",
                          "</div><div class='of'>/ 100</div></div><div class='hlabel'>", status_chip(health$status, health$label),
                          "<div class='muted'>", health$n_ok, " of ", health$n_total, " indicators available</div></div>",
                          "<div class='domchips'>", paste0(vapply(health$domains, function(d) status_chip(d$status, esc(d$name)), ""), collapse = ""), "</div>",
                          "<div class='note'>Green = 2 points, amber = 1, red = 0. Score = points as a share of the maximum. Thresholds in config.R (HEALTH_RULES).</div></div>")
    domains_html <- paste0("<div class='domains'>", paste0(vapply(health$domains, function(d) {
      paste0("<div class='dom'><h3>", status_chip(d$status, ""), " ", esc(d$name), "</h3>",
             paste0(vapply(d$items, function(it) sprintf("<div class='score' title='%s'><span>%s</span><span class='num'>%s</span>%s</div>",
                                                         esc(it$rule), esc(it$name), esc(it$value_txt),
                                                         status_chip(it$status, c(good = "OK", warn = "Watch", bad = "Stress", na = "n/a")[[it$status]])), ""), collapse = ""),
             "</div>")
    }, ""), collapse = ""), "</div>")
  }
  ribbon_html <- if (is.null(macro)) "" else paste0("<div class='ribbon'>", paste0(vapply(macro, function(m) {
    if (!isTRUE(m$ok)) return(sprintf("<div class='tile'><div class='lbl'>%s</div><div class='val'>&ndash;</div></div>", esc(m$label)))
    u <- m$unit; pre <- if (u == "$tn") "$" else ""; suf <- if (u == "$tn") "tn" else if (u == "k") "k" else u
    ch <- m$value - m$prev
    sprintf("<div class='tile'><div class='lbl'>%s</div><div class='val'>%s</div><div class='chg'>prior %s &middot; %s</div>%s<div class='chg muted'>%s%s</div></div>",
            esc(m$label), fmt_num(m$value, m$dec, suf, pre), fmt_num(m$prev, m$dec, suf, pre), fmt_chg(ch, m$dec, "", NA),
            spark_svg(m$spark, 120, 20), esc(m$period), if (!is.na(m$next_release)) paste0(" &middot; next ", esc(m$next_release)) else "")
  }, ""), collapse = ""), "</div>")
  mac <- function(id) { m <- Filter(function(x) x$id == id, cfg$MACRO_SERIES)[[1]]; macro_transform(fred[[id]], m) }
  y3 <- today - 3 * 365; y5 <- today - 5 * 365
  charts[["x-infl"]] <- list(type = "line", x = "date", fmt = "pct1", endLabels = TRUE,
                             series = compact(list(ser("CPI YoY", mac("CPIAUCSL"), 2, y3), ser("Core CPI YoY", mac("CPILFESL"), 2, y3),
                                                   ser("Core PCE YoY", mac("PCEPILFE"), 2, y3), ser("5Y breakeven", fred[["T5YIE"]], 2, y3))))
  charts[["x-fed"]] <- list(type = "line", x = "date", fmt = "pct2", endLabels = TRUE,
                            series = compact(list(ser("Fed funds upper", fred[["DFEDTARU"]], 2, yr), ser("Fed funds lower", fred[["DFEDTARL"]], 2, yr),
                                                  ser("EFFR", fred[["EFFR"]], 2, yr), ser("SOFR", fred[["SOFR"]], 2, yr))))
  charts[["x-labor"]] <- list(type = "line", x = "date", fmt = "pct1", endLabels = TRUE, title = "Unemployment rate",
                              series = compact(list(ser("Unemployment rate", fred[["UNRATE"]], 2, y5))))
  charts[["x-cond"]] <- list(type = "line", x = "date", fmt = "num2", endLabels = TRUE, zero = TRUE, title = "NFCI (negative = looser than average)",
                             series = compact(list(ser("NFCI", fred[["NFCI"]], 3, y5))))
  macro_src <- "FRED &middot; monthly / weekly releases"

  # ===========================================================================
  #  CHARTS VIEW (candles, correlation)
  # ===========================================================================
  candles <- list()
  wl <- inputs$watchlist
  if (!is.null(wl)) for (i in seq_len(nrow(wl))) {
    s <- wl$symbol[i]; y <- yahoo[[s]]; if (!isTRUE(y$ok)) next
    tfs <- list()
    pack <- function(b, interval) {
      rd <- if (isTRUE(stats::median(b$c, na.rm = TRUE) < 10)) 4 else 2
      list(interval = interval, t = arr(b$t), o = arr(round(b$o, rd)), h = arr(round(b$h, rd)),
           l = arr(round(b$l, rd)), c = arr(round(b$c, rd)), v = arr(round(b$v)))
    }
    detail <- toupper(wl$detail[i] %||% "N") == "Y"
    dbars <- if (isTRUE(detail)) y$daily else utils::tail(y$daily, 280)   # non-detail names: 6M / 1Y daily charts only
    daily_key <- NULL
    for (tf in names(cfg$CANDLE_TIMEFRAMES)) {
      spec <- cfg$CANDLE_TIMEFRAMES[[tf]]
      if (spec$interval == "1d") {
        # daily bars are stored once; later daily timeframes just point at them
        if (is.null(daily_key)) { p <- pack(dbars, "1d"); p$show <- spec$show; tfs[[tf]] <- p; daily_key <- tf }
        else tfs[[tf]] <- list(interval = "1d", ref = daily_key, show = spec$show)
      }
      else if (!is.null(raw$candles[[s]][[tf]])) tfs[[tf]] <- pack(raw$candles[[s]][[tf]]$bars, spec$interval)
    }
    candles[[s]] <- list(label = wl$label[i], exchange = y$exchange, currency = y$currency, tz = y$tz, gmtoffset = y$gmtoffset,
                         delay = if (!is.na(y$delay_min) && y$delay_min > 0) sprintf("delayed %d min", round(y$delay_min)) else "delayed up to 15 min",
                         last = y$last, prev = y$prev, time = format(y$market_time, "%d %b %H:%M %Z"), tf = tfs)
  }
  corr_note <- if (is.null(corr)) "" else sprintf("Daily changes for yields, spreads, VIX and MOVE; daily %% returns for the rest. 90D = last %d sessions, 1Y = %d sessions, as of %s.",
                                                   corr$n90, corr$n1y, format(as.Date(corr$asof), "%d %b"))
  if (!is.null(corr)) {
    charts[["c-roll"]] <- list(type = "line", x = "date", fmt = "corr", endLabels = TRUE, zero = TRUE, ymin = -1, ymax = 1,
                               series = lapply(corr$rolling, function(r) list(name = r$label, dates = arr(r$dates), values = arr(r$values))))
  }
  sym_opts <- ""
  if (length(candles)) {
    sec_of <- vapply(names(candles), function(s) { v <- wl$sector[match(s, wl$symbol)] %||% ""; if (is.na(v) || !nzchar(v)) "Other" else v }, "")
    sym_opts <- paste0(vapply(unique(sec_of), function(g) {
      opts <- vapply(names(candles)[sec_of == g], function(s) sprintf("<option value='%s'>%s (%s)</option>", esc(s), esc(candles[[s]]$label), esc(s)), "")
      paste0("<optgroup label='", esc(g), "'>", paste0(opts, collapse = ""), "</optgroup>")
    }, ""), collapse = "")
  }
  tf_btns <- paste0(vapply(names(cfg$CANDLE_TIMEFRAMES), function(tf) sprintf("<button type='button' data-tf='%s'>%s</button>", tf, tf), ""), collapse = "")
  ind_defs <- c(sma20 = "SMA 20", sma50 = "SMA 50", sma200 = "SMA 200", bb = "Bollinger 20,2", vwap = "VWAP", vol = "Volume", rsi = "RSI 14", macd = "MACD 12,26,9")
  ind_btns <- paste0(sprintf("<label class='tog'><input type='checkbox' data-ind='%s'><span>%s</span></label>", names(ind_defs), ind_defs), collapse = "")
  candle_body <- paste0("<div class='ctool'><select id='csym' aria-label='Symbol'>", sym_opts, "</select><div class='seg' id='ctf' role='group' aria-label='Timeframe'>",
                        tf_btns, "</div><div class='inds'>", ind_btns, "</div></div><div class='chart candle' id='candle'></div>")

  # ===========================================================================
  #  FEEDS (header chip + dialog; the old Data sources tab)
  # ===========================================================================
  mode_word <- c(fetched = "&#10003; Fetched this run", "cache-by-design" = "&#9679; Cached (intraday run)",
                 "cache-fallback" = "&#9650; Source down, using cache", failed = "&#10007; Failed")
  mode_cls <- c(fetched = "good", "cache-by-design" = "na", "cache-fallback" = "warn", failed = "bad")
  prov <- st[order(match(st$mode, c("failed", "cache-fallback", "fetched", "cache-by-design")), st$source), ]
  prov_rows <- lapply(seq_len(nrow(prov)), function(i) c(esc(prov$label[i]), esc(prov$source[i]), esc(prov$key[i]), esc(prov$latency[i]),
                                                       esc(prov$last_obs[i]), chip(mode_cls[[prov$mode[i]]], mode_word[[prov$mode[i]]])))
  for (f in c("holdings.csv", "watchlist.csv", "pipeline.csv", "comps.csv", "calendar.csv")) {
    p <- file.path(dash_dir, "inputs", f)
    prov_rows[[length(prov_rows) + 1]] <- c(esc(f), "Desk-maintained CSV", esc(paste0("inputs/", f)), "Manual",
                                            if (file.exists(p)) format(file.mtime(p), "%Y-%m-%d %H:%M") else "missing",
                                            chip(if (file.exists(p)) "good" else "bad", if (file.exists(p)) "&#10003; Read" else "&#10007; Missing"))
  }
  prov_html <- html_table(prov_rows, c("Dataset", "Source", "Key", "Type / latency", "Last observation", "Status"), aligns = rep("l", 6))
  notes_html <- paste0("<ul class='notes'>",
    "<li><b>Bond prices are modeled.</b> Price = last mark &minus; duration &times; change in yield since the mark. Yield = UST par yield at the bond's tenor, plus the ICE BofA OAS index named in holdings.csv for corporates. Convexity, roll-down and issuer-specific spread moves are ignored. Re-mark a bond by updating mark_price and mark_date.</li>",
    "<li><b>Carry</b> accrues the coupon, or the yield at the mark date when coupon is blank.</li>",
    "<li><b>Performance</b> holds today's holdings constant over the past year and uses daily total return. Benchmarks use dividend-adjusted ETF prices.</li>",
    "<li><b>Whole-market snapshot</b> (Market tab) covers every US-listed common stock from Nasdaq's screener with Yahoo batch quotes, once a day, delayed up to 15 minutes. Warrants, units, rights and preferreds are excluded; names under $1 or $50M are dropped. Market cap and sector come from the exchange feed and can lag corporate actions.</li>",
    "<li><b>Correlations</b> use daily changes for yields, spreads, VIX and MOVE, and daily % returns otherwise.</li>",
    "<li><b>Market health</b> grades ", if (!is.null(health)) health$n_total else "", " indicators across six domains against thresholds in config.R.</li>",
    "<li><b>Live vs delayed.</b> Futures, FX, ETFs and equities come from Yahoo, delayed up to 15 minutes, and refresh every 15 minutes in market hours when the intraday task is on. Rates, credit indices and macro update once a day.</li></ul>")

  # ===========================================================================
  #  ASSEMBLE
  # ===========================================================================
  status_bits <- c(sprintf("Rates <b>%s</b>", esc(format(rates_asof, "%d %b"))),
                   sprintf("Credit <b>%s</b>", esc(format(credit_asof, "%d %b"))),
                   sprintf("Live <b>%s</b>", esc(live_asof)),
                   sprintf("Built <b>%s</b> (%s)", esc(format(raw$fetched_at, "%d %b %H:%M")), esc(raw$run_mode)))
  n_ok <- sum(st$mode %in% c("fetched", "cache-by-design")); n_fb <- nrow(fallback); n_fail <- nrow(failed)
  feeds_cls <- if (n_fail) "bad" else if (n_fb) "warn" else "good"
  feeds_txt <- if (n_fail) sprintf("&#10007; %d feed%s down", n_fail, if (n_fail > 1) "s" else "") else if (n_fb) sprintf("&#9650; %d from cache", n_fb) else sprintf("&#10003; %d feeds", n_ok)
  warn_html <- sprintf("<button type='button' class='feeds %s' id='feedsBtn' title='%d fetched, %d from cache, %d failed. Click for every feed.' aria-haspopup='dialog'>%s</button>",
                       feeds_cls, n_ok, n_fb, n_fail, feeds_txt)
  feeds_dialog <- paste0("<dialog id='feedsDlg' class='feeds' aria-labelledby='feedsTitle'><div class='dhead'><h2 id='feedsTitle'>Data feeds</h2>",
                         sprintf("<span class='muted'>%d fetched this run &middot; %d from cache &middot; %d failed &middot; built %s (%s)</span>",
                                 n_ok, n_fb, n_fail, esc(format(raw$fetched_at, "%d %b %H:%M")), esc(raw$run_mode)),
                         "<button type='button' id='feedsClose' aria-label='Close'>&#10005;</button></div>",
                         "<div class='dbody'><div class='scroll'>", prov_html, "</div><h3>Methodology</h3>", notes_html, "</div></dialog>")
  views <- list(
    morning = paste0(
      widget("m-kpis", "Key levels", paste0("<div class='tiles'>", paste(tile_html, collapse = ""), "</div>"), 12, 2, src = paste(rates_src, "&middot;", live_src), cls = "bare"),
      widget("m-curve", "US Treasury curve", chart_div("m-curve"), 3, 4, sub = "latest vs 1w / 1m ago", src = rates_src),
      widget("m-hist", "UST 2Y / 10Y / 30Y", chart_div("m-hist"), 3, 4, sub = "1 year", src = rates_src),
      widget("m-slope", "Curve slope", chart_div("m-slope"), 3, 4, sub = "2s10s, 5s30s (bp)", src = rates_src),
      widget("m-oas", "Credit spreads", paste0("<div class='stack'>", chart_div("m-oas-ig"), chart_div("m-oas-hy"), "</div>"), 3, 4, sub = "ICE BofA OAS, 1 year", src = credit_src),
      widget("m-rates", "Rates &amp; funding", paste0("<div class='scroll'>", rates_html, "</div>"), 3, 5, sub = "bp changes", src = rates_src),
      widget("m-credit", "Credit", paste0("<div class='scroll'>", credit_html, "</div>"), 3, 5, sub = "OAS bp", src = credit_src),
      widget("m-risk", "Overnight &amp; risk", paste0("<div class='scroll'>", risk_html, "</div>"), 3, 5, src = live_src),
      widget("m-window", "New-issue window", paste0("<div class='scroll'>", window_html, "</div>"), 3, 5, sub = "scorecard &amp; calendar", src = paste0("Derived &middot; ", desk_src("calendar.csv"))),
      widget("m-pipe", "Pipeline", paste0("<div class='scroll'>", pipe_html, "</div>"), 5, 3, src = desk_src("pipeline.csv")),
      widget("m-comps", "Comps", paste0("<div class='scroll'>", comps_html, "</div>"), 4, 3, sub = paste("as of", esc(comps_asof)), src = comps_src),
      widget("m-port", "Portfolio", paste0("<div class='scroll'>", port_snap, "</div>"), 3, 3, src = "Model + Yahoo &middot; holdings.csv"),
      widget("m-movers", "Equity movers", paste0("<div class='scroll'>", movers_html, "</div>"), 6, 3, sub = "watchlist, today", src = live_src, hidden = TRUE)),
    portfolio = port_views,
    market = market_views,
    charts = paste0(
      widget("c-candle", "Price chart", candle_body, 9, 9, sub = "candles with technicals", src = "<span id='csrc'>Yahoo</span>"),
      widget("c-side", "Snapshot", paste0("<div class='scroll'>", side_html, "</div>"), 3, 9, sub = "selected symbol", src = "Yahoo &middot; Cboe"),
      widget("c-heat", "Correlation heatmap", paste0("<div class='ctool'><div class='seg' id='cwin' role='group' aria-label='Window'><button type='button' data-win='90'>90D</button><button type='button' data-win='1y'>1Y</button><button type='button' data-win='chg'>90D minus 1Y</button></div></div><div class='chart heat' id='heat'></div><div class='note'>", esc(corr_note), "</div>"),
             7, 8, src = "FRED + Yahoo &middot; daily"),
      widget("c-roll", "Rolling correlation", chart_div("c-roll"), 5, 8, sub = sprintf("%d-session window", cfg$ROLLING_CORR_WINDOW), src = "FRED + Yahoo &middot; daily")),
    health = paste0(
      widget("h-score", "Market health", health_html, 4, 5, sub = "composite", src = "Derived &middot; FRED + Yahoo"),
      widget("h-domains", "Health by domain", paste0("<div class='scroll'>", domains_html, "</div>"), 8, 5, sub = "hover a row for its thresholds"),
      widget("x-ribbon", "Macro ribbon", ribbon_html, 12, 3, src = macro_src, cls = "bare"),
      widget("x-infl", "Inflation", chart_div("x-infl"), 3, 5, sub = "% YoY, 3 years", src = macro_src),
      widget("x-fed", "Fed &amp; funding", chart_div("x-fed"), 3, 5, sub = "1 year", src = "FRED &middot; daily"),
      widget("x-labor", "Labor", chart_div("x-labor"), 3, 5, sub = "5 years", src = macro_src),
      widget("x-cond", "Financial conditions", chart_div("x-cond"), 3, 5, sub = "Chicago Fed NFCI, 5 years", src = "FRED &middot; weekly"),
      widget("x-cal", "Calendar", paste0("<div class='scroll'>", cal_table, "</div>"), 12, 3,
             sub = if (nzchar(cfg$FRED_API_KEY)) "desk + FRED releases" else "desk calendar (set FRED_API_KEY for releases)", src = desk_src("calendar.csv"))),
    watch = paste0(
      widget("w-alerts", "Alerts", paste0(rules_tool, "<div class='scroll'>", alerts_html, "</div>"), 12, 4, sub = sprintf("%d active", n_alerts), src = "Derived &middot; inputs/alerts.csv"),
      widget("w-movers", "Equity movers", paste0("<div class='scroll'>", movers_html, "</div>"), 6, 5, sub = "today, click a row to chart it", src = live_src),
      widget("w-sectors", "Sector summary", paste0("<div class='scroll'>", sectors_html, "</div>"), 6, 5, sub = "equal-weighted averages of watchlist names", src = live_src),
      widget("w-table", "Watchlist", paste0(watch_tool, "<div class='scroll'>", watch_html, "</div>"), 12, 7, sub = "click a row to chart it", src = "Yahoo &middot; delayed &le;15m &middot; watchlist.csv"),
      widget("w-news", "Headlines", paste0("<div class='scroll'>", news_html, "</div>"), 7, 7, sub = "flagged words in config.R", src = "Yahoo Finance news"),
      widget("w-opts", "Options activity", paste0("<div class='scroll'>", opts_html, "</div>"), 5, 7, sub = "equities &amp; ETFs", src = "Cboe &middot; delayed 15m"))
  )
  tabs <- c(morning = "Morning", portfolio = "Portfolio", charts = "Charts", market = "Market", health = "Macro &amp; health", watch = "Watchlist &amp; alerts")
  if (!nzchar(market_views)) tabs <- tabs[names(tabs) != "market"]
  tab_html <- paste0(vapply(names(tabs), function(v) sprintf("<button type='button' role='tab' data-view='%s'>%s%s</button>", v, tabs[[v]],
                                                             if (v == "watch" && n_alerts > 0) sprintf(" <span class='badge'>%d</span>", n_alerts) else ""), ""), collapse = "")
  views <- views[vapply(views, nzchar, TRUE)]
  views_html <- paste0(vapply(names(views), function(v) sprintf("<div class='view%s' data-view='%s' role='tabpanel' hidden>%s</div>",
                                                                 if (v == "morning") " fit" else "", v, views[[v]]), ""), collapse = "\n")

  # shared layout presets: inputs/layouts.json is what the page's Export button writes
  layouts_path <- file.path(dash_dir, "inputs", "layouts.json")
  layouts <- if (file.exists(layouts_path)) tryCatch(jsonlite::fromJSON(layouts_path, simplifyVector = FALSE),
                                                     error = function(e) { logmsg("inputs/layouts.json ignored: ", conditionMessage(e)); NULL }) else NULL
  D <- list(meta = list(title = cfg$DASH_TITLE, built_at = format(raw$fetched_at, "%Y-%m-%dT%H:%M:%S"), run_mode = raw$run_mode,
                        refresh_s = cfg$BROWSER_REFRESH_SECONDS, n_alerts = n_alerts),
            layouts = layouts,
            alert_rules = if (is.null(rules)) list() else lapply(seq_len(nrow(rules)), function(i) as.list(rules[i, ])),
            alert_fired = if (is.null(rule_alerts)) character(0) else arr(rule_alerts$key),
            metrics = mkt_metrics, symmetrics = sym_metrics, portmetrics = port_metrics,
            metric_labels = list(symbol = as.list(SYMBOL_METRICS), portfolio = as.list(PORTFOLIO_METRICS)),
            charts = charts,
            corr = if (is.null(corr)) NULL else list(labels = arr(corr$labels), m90 = corr$m90, m1y = corr$m1y))
  json <- jsonlite::toJSON(D, auto_unbox = TRUE, na = "null", null = "null", digits = 7, matrix = "rowmajor")
  json <- gsub("<", "\\u003c", json, fixed = TRUE)
  # candle data for every watchlist name lives in a companion file next to the page,
  # so the page itself stays small; the Charts tab reads it when present.
  cjson <- if (length(candles)) jsonlite::toJSON(candles, auto_unbox = TRUE, na = "null", null = "null", digits = 7) else "{}"
  cjson <- gsub("<", "\\u003c", cjson, fixed = TRUE)
  con <- file(file.path(output_dir, "market_data.js"), open = "wb")
  writeLines(enc2utf8(paste0("window.MMD_CANDLES=", cjson, ";")), con, useBytes = TRUE); close(con)

  con <- file(file.path(output_dir, "market_universe.js"), open = "wb")
  writeLines(enc2utf8(gsub("<", "\\u003c", universe_js, fixed = TRUE)), con, useBytes = TRUE); close(con)

  read_asset <- function(f) paste(readLines(file.path(dash_dir, "assets", f), warn = FALSE, encoding = "UTF-8"), collapse = "\n")
  html <- paste0("<!doctype html>\n<html lang='en'><head><meta charset='utf-8'>\n",
                 "<meta name='viewport' content='width=device-width, initial-scale=1'>\n",
                 "<title>", esc(cfg$DASH_TITLE), "</title>\n<style>\n", read_asset("dashboard.css"), "\n</style></head>\n<body>\n",
                 "<header class='top' id='top'><div class='brand'><h1>", esc(cfg$DASH_TITLE), "</h1><span class='sub'>", esc(cfg$DASH_SUBTITLE),
                 "</span><span class='date'>", esc(format(today, "%a %d %b %Y")), "</span></div>",
                 "<nav class='tabs' role='tablist' aria-label='Views'>", tab_html, "</nav>",
                 "<div class='status'>", paste(status_bits, collapse = "<i>&middot;</i>"), warn_html,
                 if (n_alerts > 0) sprintf("<button type='button' class='alertbtn' data-goto='watch'>&#9650; %d alert%s</button>", n_alerts, if (n_alerts > 1) "s" else "") else "",
                 "<span id='countdown' class='muted' title='Time until the page reloads with the latest build'></span></div>",
                 "<div class='controls'><select id='layoutSel' aria-label='Layout'></select>",
                 "<button type='button' id='editBtn' aria-pressed='false'>Customize</button>",
                 "<button type='button' id='themeBtn' title='Theme: system / light / dark'>Theme</button></div></header>\n",
                 "<div id='tray' class='tray' hidden><span class='hint'>Drag a header to any cell, drag the corner to resize (arrow keys / Shift+arrows work too).</span><span>Hidden:</span><span id='trayItems'></span>",
                 "<button type='button' id='saveAsBtn'>Save layout as&hellip;</button><button type='button' id='delLayoutBtn'>Delete layout</button>",
                 "<button type='button' id='resetBtn'>Reset view</button><button type='button' id='exportBtn' title='Download your layouts as layouts.json; drop it in inputs/ to share them as presets'>Export</button>",
                 "<label class='btn' title='Load a layouts.json'>Import<input type='file' id='importFile' accept='.json,application/json' hidden></label>",
                 "<button type='button' id='doneBtn'>Done</button></div>\n",
                 "<main id='main'>", views_html, "</main>\n", feeds_dialog, "\n",
                 "<script type='application/json' id='dash-data'>", json, "</script>\n",
                 "<script src='market_data.js'></script>\n<script src='market_universe.js'></script>\n<script>\n", read_asset("dashboard.js"), "\n</script>\n</body></html>")
  html_path <- file.path(output_dir, "market_dashboard.html")
  # binary connection + useBytes: the assets hold UTF-8 glyphs that a non-UTF-8 locale
  # would otherwise write as <U+XXXX> (or truncate through a text connection)
  con <- file(html_path, open = "wb"); writeLines(enc2utf8(html), con, useBytes = TRUE); close(con)

  # ---- PNG snapshot (email / Teams) --------------------------------------------
  png_path <- file.path(output_dir, "market_dashboard.png")
  tryCatch({
    lines_df <- function(spec) do.call(rbind, lapply(spec$series, function(s) data.frame(date = as.Date(as.character(unclass(s$dates))), value = as.numeric(unclass(s$values)), series = s$name)))
    in_order <- function(df, lv) { df$series <- factor(df$series, levels = lv); df }
    hist_df <- in_order(lines_df(charts[["m-hist"]]), c("UST 2Y", "UST 10Y", "UST 30Y"))
    slope_df <- in_order(lines_df(charts[["m-slope"]]), c("2s10s", "5s30s"))
    oas_df <- in_order(rbind(lines_df(charts[["m-oas-ig"]]), lines_df(charts[["m-oas-hy"]])), c("US IG OAS", "US HY OAS"))
    cv <- charts[["m-curve"]]
    curve_df <- do.call(rbind, lapply(cv$series, function(s) data.frame(tenor = factor(unclass(cv$cats), levels = unclass(cv$cats)), value = as.numeric(unclass(s$values)), series = s$name)))
    curve_df$series <- factor(curve_df$series, levels = c("Latest", "1 week ago", "1 month ago"))
    cols <- unname(PAL[c("blue", "orange", "aqua")])
    g1 <- ggplot(curve_df, aes(tenor, value, colour = series, group = series)) + geom_line(linewidth = 0.7) + geom_point(size = 1.3) +
      scale_colour_manual(values = setNames(cols, c("Latest", "1 week ago", "1 month ago"))) + labs(title = "US Treasury curve (%)") + theme_dash()
    g2 <- ggplot(hist_df, aes(date, value, colour = series)) + geom_line(linewidth = 0.6) + scale_colour_manual(values = cols) +
      labs(title = "UST 2Y / 10Y / 30Y (%)") + theme_dash()
    g3 <- ggplot(slope_df, aes(date, value, colour = series)) + geom_hline(yintercept = 0, colour = INK[["axis"]]) + geom_line(linewidth = 0.6) +
      scale_colour_manual(values = cols[1:2]) + labs(title = "Curve slope (bp)") + theme_dash()
    g4 <- ggplot(oas_df, aes(date, value, colour = series)) + geom_line(linewidth = 0.6, show.legend = FALSE) + facet_wrap(~series, ncol = 1, scales = "free_y") +
      scale_colour_manual(values = cols[1:2]) + labs(title = "Credit spreads (OAS, bp)") + theme_dash()
    grDevices::png(png_path, width = 1800, height = 900, res = 140, bg = "white")
    gridExtra::grid.arrange(g1, g2, g3, g4, ncol = 2,
                            top = grid::textGrob(sprintf("%s  -  %s", cfg$DASH_TITLE, format(today, "%d %b %Y")), gp = grid::gpar(fontface = "bold", fontsize = 13)))
    grDevices::dev.off()
  }, error = function(e) { logmsg("PNG snapshot failed: ", conditionMessage(e)); try(grDevices::dev.off(), silent = TRUE) })

  # ---- machine-readable snapshot ---------------------------------------------------
  snap <- list(built_at = format(raw$fetched_at), run_mode = raw$run_mode, rates_asof = format(rates_asof), credit_asof = format(credit_asof),
               window = window_txt, health = if (!is.null(health)) list(score = health$score, label = health$label) else NULL,
               portfolio = if (!is.null(port)) port$totals else NULL, alerts = alerts,
               fred = lapply(S, function(s) list(last = s$last, date = format(s$date), d1 = s$d1, w1 = s$w1, m1 = s$m1, ytd = s$ytd)),
               yahoo = lapply(Y, function(y) list(last = y$last, d1_pct = y$d1, w1_pct = y$w1)))
  jsonlite::write_json(snap, file.path(output_dir, "market_snapshot.json"), auto_unbox = TRUE, pretty = TRUE, digits = 6, na = "null")
  utils::write.csv(raw$status, file.path(output_dir, "data_status.csv"), row.names = FALSE)

  invisible(list(html = html_path, png = png_path, window = window_txt, n_alerts = n_alerts, alerts = alerts,
                 health = if (!is.null(health)) paste(health$score, health$label) else "n/a"))
}
