# Registers (or re-registers) the Windows Task Scheduler jobs that keep the
# dashboard fresh. Both run hidden (no console window pops up).
#
#   Morning Market Dashboard            full build, weekdays at -At (default 07:00)
#   Morning Market Dashboard (intraday) quick refresh of quotes, candles, news and
#                                       options every -EveryMinutes during market hours
#
# Run once from PowerShell:
#   powershell -ExecutionPolicy Bypass -File ".\schedule_daily_refresh.ps1"
# Options:
#   -At "07:00"              morning build time
#   -IntradayStart "07:15"   first intraday refresh
#   -IntradayHours 10        how long intraday refreshes continue
#   -EveryMinutes 15         intraday interval
#   -NoIntraday              only register the morning build (removes the intraday task)
#   -Remove                  remove both tasks
param(
    [string]$At = "07:00",
    [string]$IntradayStart = "07:15",
    [int]$IntradayHours = 10,
    [int]$EveryMinutes = 15,
    [switch]$NoIntraday,
    [switch]$Remove
)

$TaskName     = "Morning Market Dashboard"
$IntradayName = "Morning Market Dashboard (intraday)"
$DashDir      = Split-Path -Parent $MyInvocation.MyCommand.Path
$Script       = Join-Path $DashDir "run_dashboard.R"

if ($Remove) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $IntradayName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Removed both dashboard tasks."
    exit 0
}

$Rscript = Get-ChildItem "C:\Program Files\R\R-*\bin\Rscript.exe" -ErrorAction SilentlyContinue |
           Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $Rscript) { throw "Rscript.exe not found under C:\Program Files\R" }

$Days = "Monday","Tuesday","Wednesday","Thursday","Friday"
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 20) `
            -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# conhost --headless runs Rscript without opening a console window
function New-HiddenAction([string]$mode) {
    $argLine = "--headless `"$Rscript`" `"$Script`" $mode".Trim()
    New-ScheduledTaskAction -Execute "conhost.exe" -Argument $argLine -WorkingDirectory $DashDir
}

$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Days -At $At
Register-ScheduledTask -TaskName $TaskName -Action (New-HiddenAction "") -Trigger $Trigger -Settings $Settings `
    -Description "Full morning build of the market dashboard (FRED, Treasury.gov, Yahoo, Cboe)" -Force | Out-Null
Write-Host "Registered '$TaskName': weekdays at $At"

if ($NoIntraday) {
    Unregister-ScheduledTask -TaskName $IntradayName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Intraday refresh not registered."
} else {
    $IT = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Days -At $IntradayStart
    $IT.Repetition = (New-ScheduledTaskTrigger -Once -At $IntradayStart `
        -RepetitionInterval (New-TimeSpan -Minutes $EveryMinutes) `
        -RepetitionDuration (New-TimeSpan -Hours $IntradayHours)).Repetition
    Register-ScheduledTask -TaskName $IntradayName -Action (New-HiddenAction "intraday") -Trigger $IT -Settings $Settings `
        -Description "Intraday refresh of quotes, candles, news and options for the market dashboard" -Force | Out-Null
    Write-Host "Registered '$IntradayName': weekdays every $EveryMinutes min from $IntradayStart for $IntradayHours h"
}
Write-Host "If the PC is asleep at a scheduled time, the run starts as soon as it wakes."
