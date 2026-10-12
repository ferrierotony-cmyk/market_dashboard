# Windows toast notification for new dashboard alerts. Called by run_dashboard.R;
# needs nothing installed (uses the WinRT toast API that ships with Windows 10/11).
#   powershell -NoProfile -ExecutionPolicy Bypass -File notify.ps1 -Title "..." -Message "..." -Open "C:\...\market_dashboard.html"
param(
    [string]$Title = "Morning Market Dashboard",
    [string]$Message = "",
    [string]$Open = ""
)
$ErrorActionPreference = "Stop"
try {
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
    # PowerShell's own AppUserModelId: registered on every Windows install, so the toast shows without an app registration
    $appId = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
    $esc = { param($s) [System.Security.SecurityElement]::Escape($s) }
    $launch = ""
    if ($Open -ne "") {
        $uri = (New-Object System.Uri (Resolve-Path $Open).Path).AbsoluteUri
        $launch = " activationType='protocol' launch='" + (& $esc $uri) + "'"
    }
    $xml = "<toast$launch scenario='reminder'><visual><binding template='ToastGeneric'><text>" + (& $esc $Title) + "</text><text>" + (& $esc $Message) + "</text></binding></visual></toast>"
    $doc = New-Object Windows.Data.Xml.Dom.XmlDocument
    $doc.LoadXml($xml)
    $toast = [Windows.UI.Notifications.ToastNotification]::new($doc)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)
    exit 0
} catch {
    Write-Error $_
    exit 1
}
