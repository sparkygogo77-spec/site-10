# Lantern Review: render whatever the site is missing, publish it, tell you when it's done.
# Started by "Render Lantern Review.cmd" (double-click) or the site's "Render on my PC" button.
# You don't need to watch this window: it runs minimised, the review site shows live progress
# ("Rendering on your PC: 12 of 48 takes, about 9 min left"), it uploads every 15 minutes,
# and a Windows notification pops up when it finishes. Stop early: double-click "Stop render.cmd".

$ErrorActionPreference = "Continue"
$Live    = Split-Path -Parent $MyInvocation.MyCommand.Path
$Blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$Site    = Join-Path $Live "review-site"
$Log     = Join-Path $Site "last_render.log"
$Url     = "https://lantern-review-j.vercel.app"
$env:PYTHONWARNINGS = "ignore"
$env:PYTHONUNBUFFERED = "1"     # show each line as it happens (piped output is otherwise held back)

function Notify($title, $text) {
    try {
        Add-Type -AssemblyName System.Windows.Forms, System.Drawing
        $n = New-Object System.Windows.Forms.NotifyIcon
        $n.Icon = [System.Drawing.SystemIcons]::Information
        $n.Visible = $true
        $n.ShowBalloonTip(15000, $title, $text, [System.Windows.Forms.ToolTipIcon]::Info)
        Start-Sleep 8; $n.Dispose()
    } catch {}
}

$Host.UI.RawUI.WindowTitle = "Lantern Review render (progress is on the review site)"
Set-Location $Live
if (-not (Test-Path $Blender)) { Notify "Lantern render" "Blender 5.2 not found"; Write-Host "Blender 5.2 not found at $Blender" -ForegroundColor Red; Read-Host "Press Enter to close"; exit 1 }
if (-not (Test-Path (Join-Path $Site "tools\lantern_review.py"))) { Write-Host "No review-site folder in $Live" -ForegroundColor Red; Read-Host "Press Enter to close"; exit 1 }
Remove-Item (Join-Path $Site "STOP") -ErrorAction SilentlyContinue
$Lock = Join-Path $Site "RENDERING"
$old = Get-Content $Lock -ErrorAction SilentlyContinue
if ($old -and (Get-Process -Id $old -ErrorAction SilentlyContinue)) { Write-Host "A render is already running in another window. Nothing started." -ForegroundColor Yellow; Start-Sleep 6; exit 0 }
Set-Content $Lock $PID

Write-Host "Lantern Review render  $(Get-Date -Format 'ddd HH:mm')" -ForegroundColor Green
Write-Host "You can leave this window: progress shows on $Url and a notification pops up at the end."
Write-Host "Full log: $Log"
Write-Host ""

$start = Get-Date
$done = 0; $failed = 0; $total = 0
& $Blender -b --python "review-site\tools\lantern_review.py" -- --all 2>&1 |
  ForEach-Object { if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.Exception.Message } else { "$_" } } |
  Tee-Object -FilePath $Log | ForEach-Object {
    $l = "$_"
    if     ($l -match "^\s+(\d+) takes to render")      { $total = [int]$Matches[1]; Write-Host $l }
    elseif ($l -match "FAILED")                        { $failed++; $done++; Write-Host "[$done/$total] $l" -ForegroundColor Red }
    elseif ($l -match "^\[[^\]]+\] .* done \(")        { $done++;   Write-Host "[$done/$total] $l" -ForegroundColor Green }
    elseif ($l -match "^\[[^\]]+\] (loaded|scrapped)|^pushed:|^Rendered:|^Stopped|^Renderer updated|^PUSH|^COMMIT") { Write-Host $l }
}
Remove-Item $Lock -ErrorAction SilentlyContinue

$mins = [math]::Round(((Get-Date) - $start).TotalMinutes, 1)
Write-Host ""
if ($done -eq 0)   { $msg = "Nothing new to render." }
elseif ($failed)   { $msg = "$done takes done, $failed failed ($mins min). Failures are listed on the site." }
else               { $msg = "$done takes rendered and uploaded ($mins min)." }
Write-Host $msg -ForegroundColor $(if ($failed) { "Yellow" } else { "Green" })
Notify "Lantern render finished" $msg
if ($done -gt 0) { Start-Process "$Url" }
Write-Host "This window closes in 20 seconds."
Start-Sleep 20
