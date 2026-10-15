# Lantern Review: render whatever the site is missing, publish it, open the site.
# Double-click "Render Lantern Review.cmd" (next to this file) to run it.
# It renders only what's needed: takes with no clips yet, or takes a chat changed (rev bumped).
# Skips anything you rated KEEP or DROP, scrapped passes, and replaced rounds. One upload (one deploy) at the end.
# Stop early: double-click "Stop render.cmd"; it finishes the current take and uploads what is done.

$ErrorActionPreference = "Continue"
$Live    = Split-Path -Parent $MyInvocation.MyCommand.Path
$Blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$Site    = Join-Path $Live "review-site"
$Log     = Join-Path $Site "last_render.log"
$Url     = "https://lantern-review-j.vercel.app"

$Host.UI.RawUI.WindowTitle = "Lantern Review render"
Set-Location $Live
if (-not (Test-Path $Blender)) { Write-Host "Blender 5.2 not found at $Blender" -ForegroundColor Red; Read-Host "Press Enter to close"; exit 1 }
if (-not (Test-Path (Join-Path $Site "tools\lantern_review.py"))) { Write-Host "No review-site folder in $Live" -ForegroundColor Red; Read-Host "Press Enter to close"; exit 1 }
Remove-Item (Join-Path $Site "STOP") -ErrorAction SilentlyContinue
$Lock = Join-Path $Site "RENDERING"
$old = Get-Content $Lock -ErrorAction SilentlyContinue
if ($old -and (Get-Process -Id $old -ErrorAction SilentlyContinue)) { Write-Host "A render is already running in another window. Nothing started." -ForegroundColor Yellow; Start-Sleep 6; exit 0 }
Set-Content $Lock $PID

Write-Host "Lantern Review render  $(Get-Date -Format 'ddd HH:mm')" -ForegroundColor Green
Write-Host "Checking what the site is missing, then rendering only that. Full log: $Log"
Write-Host ""

$start = Get-Date
$done = 0; $failed = 0
& $Blender -b --python "review-site\tools\lantern_review.py" -- --all 2>&1 | Tee-Object -FilePath $Log | ForEach-Object {
    $l = "$_"
    if     ($l -match "FAILED")                         { $failed++; Write-Host $l -ForegroundColor Red }
    elseif ($l -match "^\[[^\]]+\] .* done \(")         { $done++;   Write-Host $l -ForegroundColor Green }
    elseif ($l -match "^\[[^\]]+\]|^pushed:|^Rendered:|^status:|^no spec|^Stopped|^Renderer updated|^PUSH|^COMMIT|passes, .* takes") { Write-Host $l }
}

$mins = [math]::Round(((Get-Date) - $start).TotalMinutes, 1)
Write-Host ""
if ($failed) { Write-Host "$done takes rendered, $failed failed ($mins min). The failures are in $Log" -ForegroundColor Yellow }
else         { Write-Host "$done takes rendered ($mins min)." -ForegroundColor Green }
if ($done)   { Write-Host "Uploaded. The site shows them in about a minute; opening it now." ; Start-Sleep 60; Start-Process $Url }
else         { Write-Host "Nothing new to render: the site already has everything." }
Remove-Item $Lock -ErrorAction SilentlyContinue
Read-Host "Press Enter to close"
