# How far back does each input to the new issue window score go?
# Writes backtest/history_check.txt. Uses free public endpoints only.
out <- character()
say <- function(...) { s <- paste0(...); cat(s, "\n"); out <<- c(out, s) }
fred <- c("BAMLC0A0CM", "BAMLH0A0HYM2", "VIXCLS", "DGS10")
for (id in fred) {
  r <- tryCatch(read.csv(sprintf("https://fred.stlouisfed.org/graph/fredgraph.csv?id=%s&cosd=1990-01-01", id), stringsAsFactors = FALSE),
                error = function(e) NULL)
  if (is.null(r)) { say("FRED ", id, ": FAILED"); next }
  r <- r[!is.na(suppressWarnings(as.numeric(r[[2]]))), ]
  say("FRED ", id, ": ", nrow(r), " rows, first ", r[[1]][1], ", last ", r[[1]][nrow(r)])
}
if (requireNamespace("jsonlite", quietly = TRUE)) {
  for (s in c("^MOVE", "ES=F", "^VIX")) {
    u <- sprintf("https://query1.finance.yahoo.com/v8/finance/chart/%s?range=15y&interval=1d", utils::URLencode(s, reserved = TRUE))
    j <- tryCatch(jsonlite::fromJSON(u), error = function(e) NULL)
    if (is.null(j) || is.null(j$chart$result)) { say("Yahoo ", s, ": FAILED"); next }
    ts <- as.Date(as.POSIXct(j$chart$result$timestamp[[1]], origin = "1970-01-01", tz = "UTC"))
    say("Yahoo ", s, ": ", length(ts), " rows, first ", min(ts), ", last ", max(ts))
  }
} else say("jsonlite not installed, Yahoo check skipped")
ca <- grep("--file=", commandArgs(FALSE), value = TRUE)
here <- if (length(ca)) dirname(normalizePath(sub("--file=", "", ca[1]))) else getwd()
writeLines(out, file.path(here, "history_check.txt"))
