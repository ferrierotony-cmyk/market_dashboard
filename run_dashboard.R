# =============================================================================
#  run_dashboard.R - entry point. Run from Task Scheduler, RStudio, or:
#     Rscript run_dashboard.R             full morning build (all sources)
#     Rscript run_dashboard.R intraday    quick refresh: live quotes, candles,
#                                         news, options; rates/credit/macro
#                                         from the morning cache
#  Output: output/market_dashboard.html (+ .png, market_snapshot.json)
# =============================================================================

.find_dash_dir <- function() {
  a <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", grep("^--file=", a, value = TRUE))
  if (length(f)) return(dirname(normalizePath(f[1], winslash = "/")))
  if (file.exists("config.R") && file.exists("build_dashboard.R")) return(normalizePath(getwd(), winslash = "/"))
  "C:/Users/ferri/OneDrive/Documents/R Folder/market_dashboard"
}
DASH_DIR <- .find_dash_dir()
setwd(DASH_DIR)
RUN_MODE <- if ("intraday" %in% tolower(commandArgs(trailingOnly = TRUE))) "intraday" else "morning"

dir.create("logs", showWarnings = FALSE)
source("fetch_data.R")
LOG_FILE <- file.path("logs", paste0("run_", format(Sys.Date(), "%Y%m%d"), ".log"))
logmsg("==== dashboard build (", RUN_MODE, ") started in ", DASH_DIR, " ====")

ok <- tryCatch({
  for (p in c("ggplot2", "gridExtra", "jsonlite", "xml2", "svglite")) {
    if (!requireNamespace(p, quietly = TRUE)) stop("missing package: ", p, "  -> install.packages('", p, "')")
  }
  cfg_env <- new.env()
  sys.source("config.R", envir = cfg_env)
  cfg <- as.list(cfg_env)
  source("analytics.R")
  source("alerts.R")
  source("build_dashboard.R")

  inputs <- lapply(c(holdings = "holdings.csv", watchlist = "watchlist.csv", pipeline = "pipeline.csv",
                     comps = "comps.csv", calendar = "calendar.csv"),
                   function(f) read_input_csv(file.path("inputs", f)))

  raw <- fetch_all(cfg, inputs, cache_dir = "data", run_mode = RUN_MODE)
  res <- build_dashboard(cfg, raw, inputs, DASH_DIR)
  logmsg("Built ", res$html, "  (window: ", res$window, ", health: ", res$health, ", alerts: ", res$n_alerts, ")")
  tryCatch(notify_new_alerts(cfg, res$alerts, DASH_DIR, res$html), error = function(e) logmsg("Toast failed: ", conditionMessage(e)))
  TRUE
}, error = function(e) {
  logmsg("BUILD FAILED: ", conditionMessage(e))
  FALSE
})

logmsg("==== finished ", if (ok) "OK" else "WITH ERRORS", " ====")
if (!ok && !interactive()) quit(status = 1)
