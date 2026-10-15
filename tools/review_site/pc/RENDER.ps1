# Lantern Review: render whatever the site is missing, publish it, tell you when it's done.
# Started by RENDER.cmd (double-click) or the site's "Render on my PC" button.
# You don't need to watch this window: it runs minimised, the review site shows live progress, it uploads every
# 15 minutes, and a Windows notification pops up when it finishes.
# Watchdog: if Blender goes quiet for 12 minutes (hung or crashed), it is closed, the take it was on is skipped,
# and the run carries on from there (up to 3 times). Stop early: double-click "Stop render.cmd".

$ErrorActionPreference = "Continue"
$Live    = Split-Path -Parent $MyInvocation.MyCommand.Path
$Blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$Site    = Join-Path $Live "review-site"
$Log     = Join-Path $Site "last_render.log"
$ErrLog  = Join-Path $Site "last_render.err"
$Url     = "https://lantern-review-j.vercel.app"
$QuietMin = 12
$env:PYTHONWARNINGS = "ignore"
$env:PYTHONUNBUFFERED = "1"

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
Remove-Item (Join-Path $Site "STOP"), (Join-Path $Site "SKIPPED"), (Join-Path $Site "CURRENT") -ErrorAction SilentlyContinue
$Lock = Join-Path $Site "RENDERING"
$old = Get-Content $Lock -ErrorAction SilentlyContinue
if ($old -and (Get-Process -Id $old -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match "powershell|pwsh" })) {
    Write-Host "A render is already running in another window. Nothing started." -ForegroundColor Yellow; Start-Sleep 6; exit 0 }
Set-Content $Lock $PID
# Line this folder's copy of the site up with the one online before Blender starts (never a rebase: a stuck rebase
# once left it off its branch so nothing could upload). Keeps every render made here.
function SiteGit { & git -C $Site @args 2>&1 | Out-Null }
if (Get-Command git -ErrorAction SilentlyContinue) {
    if ((Test-Path "$Site\.git\rebase-merge") -or (Test-Path "$Site\.git\rebase-apply")) { SiteGit rebase --quit }
    if (Test-Path "$Site\.git\MERGE_HEAD") { SiteGit merge --quit }
    SiteGit checkout -q -B review-site
    SiteGit fetch -q origin review-site
    if ($LASTEXITCODE -eq 0) {
        SiteGit reset -q --mixed origin/review-site
        SiteGit checkout origin/review-site -- . ":(exclude)media" ":(exclude)data"
        SiteGit branch -q --set-upstream-to=origin/review-site
        SiteGit add -A
        SiteGit commit -q -m "Review renders from J's PC (carried over)"
    }
}

# Clicking in a console window starts "Select" mode, which freezes everything printing to it until Enter is pressed
# (that paused a run for 7 hours). Turn that click-to-select mode off for this window.
try {
    Add-Type -Namespace LR -Name Con -MemberDefinition @'
[DllImport("kernel32.dll")] public static extern System.IntPtr GetStdHandle(int h);
[DllImport("kernel32.dll")] public static extern bool GetConsoleMode(System.IntPtr h, out uint m);
[DllImport("kernel32.dll")] public static extern bool SetConsoleMode(System.IntPtr h, uint m);
'@
    $h = [LR.Con]::GetStdHandle(-10); $m = 0
    if ([LR.Con]::GetConsoleMode($h, [ref]$m)) { [void][LR.Con]::SetConsoleMode($h, (($m -band (-bnot 0x40)) -bor 0x80)) }
} catch {}
# keep the PC awake while rendering (a sleeping PC paused a run for 7 hours); released when this window closes
try {
    Add-Type -Namespace LR -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
    [void][LR.Power]::SetThreadExecutionState([uint32]"0x80000001")
} catch {}

Write-Host "Lantern Review render  $(Get-Date -Format 'ddd HH:mm')" -ForegroundColor Green
Write-Host "You can leave this window: progress shows on $Url and a notification pops up at the end."
Write-Host ""

$start = Get-Date
$done = 0; $failed = 0; $total = 0; $restarts = 0; $hung = @()
while ($true) {
    Remove-Item $Log, $ErrLog -ErrorAction SilentlyContinue
    $p = Start-Process -FilePath $Blender -ArgumentList "-b", "--python", "review-site\tools\lantern_review.py", "--", "--all" `
         -WorkingDirectory $Live -RedirectStandardOutput $Log -RedirectStandardError $ErrLog -WindowStyle Hidden -PassThru
    $read = 0; $lastChange = Get-Date; $lastSize = -1
    while (-not $p.HasExited) {
        Start-Sleep 2
        $size = (Get-Item $Log -ErrorAction SilentlyContinue).Length
        if ($size -ne $lastSize) { $lastChange = Get-Date; $lastSize = $size }
        $lines = @(Get-Content $Log -ErrorAction SilentlyContinue)
        for ($i = $read; $i -lt $lines.Count; $i++) {
            $l = $lines[$i]
            if     ($l -match "^\s+(\d+) takes to render")      { $total = [int]$Matches[1]; Write-Host $l }
            elseif ($l -match "FAILED")                        { $failed++; $done++; Write-Host "[$done/$total] $l" -ForegroundColor Red }
            elseif ($l -match "^\[[^\]]+\] .* done \(")        { $done++;   Write-Host "[$done/$total] $l" -ForegroundColor Green }
            elseif ($l -match "^\[[^\]]+\] (loaded|scrapped)|^pushed:|^Rendered:|^Stopped|^Renderer updated|^PUSH|^COMMIT|bakes on") { Write-Host $l }
        }
        $read = $lines.Count
        if (((Get-Date) - $lastChange).TotalMinutes -gt $QuietMin) {
            $cur = Get-Content (Join-Path $Site "CURRENT") -ErrorAction SilentlyContinue
            Write-Host "Blender has been silent for $QuietMin minutes on '$cur': closing it and carrying on without that take." -ForegroundColor Yellow
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            Get-Process -Name "WerFault" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
            if ($cur) { Add-Content (Join-Path $Site "SKIPPED") $cur; $hung += $cur; $failed++; $done++ }
            break
        }
    }
    if ($p.HasExited -and ($hung.Count -eq $restarts)) { break }     # finished normally
    $restarts++
    if ($restarts -gt 3) { Write-Host "Stopped after 3 restarts." -ForegroundColor Red; break }
    Start-Sleep 3
}
Remove-Item $Lock, (Join-Path $Site "CURRENT") -ErrorAction SilentlyContinue

$mins = [math]::Round(((Get-Date) - $start).TotalMinutes, 1)
Write-Host ""
if ($done -eq 0)   { $msg = "Nothing new to render." }
elseif ($failed)   { $msg = "$done takes done, $failed failed or skipped ($mins min). Details on the site." }
else               { $msg = "$done takes rendered and uploaded ($mins min)." }
if ($hung.Count)   { Write-Host ("Skipped because Blender hung: " + ($hung -join ", ")) -ForegroundColor Yellow }
Write-Host $msg -ForegroundColor $(if ($failed) { "Yellow" } else { "Green" })
Notify "Lantern render finished" $msg
if ($done -gt 0) { Start-Process "$Url" }
Write-Host "This window closes in 20 seconds."
Start-Sleep 20
