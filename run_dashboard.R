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
  normalizePath(getwd(), winslash = "/")
}
DASH_DIR <- .find_dash_dir()
setwd(DASH_DIR)
RUN_MODE <- if ("intraday" %in% tolower(commandArgs(trailingOnly = TRUE))) "intraday" else "morning"

dir.create("logs", showWarnings = FALSE)
source("fetch_data.R")
source("market.R")      # market_fetch() is called from fetch_all()
LOG_FILE <- file.path("logs", paste0("run_", format(Sys.Date(), "%Y%m%d"), ".log"))
logmsg("==== dashboard build (", RUN_MODE, ") started in ", DASH_DIR, " ====")

# ---- one run at a time ---------------------------------------------------------------
# After a sleep the morning and intraday tasks can both fire in the same second (seen on
# Oct 16, 2026), and two runs then write the same cache, HTML and alert state together.
# dir.create() is atomic: it returns TRUE only for the process that made the lock folder.
# The morning build waits for a running refresh to finish. An intraday refresh just skips.
# The lock lives in the Windows temp folder, not in this OneDrive folder. OneDrive can hold a
# new folder open and block its deletion, which left a stale lock on the first test run.
LOCK_DIR <- file.path(Sys.getenv("TEMP", unset = ""), "market_dashboard_run.lock")
if (!nzchar(Sys.getenv("TEMP", unset = ""))) LOCK_DIR <- file.path("logs", "run.lock")
.release_lock <- function() {
  for (i in 1:5) { unlink(LOCK_DIR, recursive = TRUE, force = TRUE); if (!dir.exists(LOCK_DIR)) return(invisible(TRUE)); Sys.sleep(1) }
  logmsg("Could not remove the run lock ", LOCK_DIR, ". It clears by itself after 22 minutes.")
  invisible(FALSE)
}
.acquire_lock <- function() {
  if (dir.exists(LOCK_DIR) && difftime(Sys.time(), file.mtime(LOCK_DIR), units = "mins") > 22) {
    unlink(LOCK_DIR, recursive = TRUE)   # older than the 20 minute task limit, so a dead run left it
    logmsg("Removed a stale run lock")
  }
  isTRUE(dir.create(LOCK_DIR, showWarnings = FALSE))
}
got_lock <- .acquire_lock()
if (!got_lock && RUN_MODE == "morning") {
  logmsg("Another run is in progress, the morning build is waiting for it")
  waited <- 0
  while (!got_lock && waited < 600) { Sys.sleep(15); waited <- waited + 15; got_lock <- .acquire_lock() }
}
if (!got_lock) {
  logmsg("Skipped: another dashboard run is in progress")
  if (!interactive()) quit(status = 0) else stop("another dashboard run is in progress")
}

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

.release_lock()
logmsg("==== finished ", if (ok) "OK" else "WITH ERRORS", " ====")
if (!ok && !interactive()) quit(status = 1)
