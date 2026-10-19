# Lantern Review commands (run through lr.cmd: "lr <command>" in cmd, ".\lr <command>" in PowerShell).
param([string]$Cmd = "help", [string]$Arg = "", [string]$Extra = "")

$Live    = Split-Path -Parent $MyInvocation.MyCommand.Path
$Site    = Join-Path $Live "review-site"
$Repo    = Join-Path $Live "site-10"
$Blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$Url     = "https://lantern-review-j.vercel.app"
Set-Location $Live

function Busy {
    foreach ($f in @(@("RENDERING", "powershell|pwsh"), @("BLENDER.lock", "blender"))) {
        $id = Get-Content (Join-Path $Site $f[0]) -ErrorAction SilentlyContinue
        if ($id -and (Get-Process -Id $id -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match $f[1] })) { return "$($f[0]) (process $id)" }
    }
    return ""
}

function Spec($n) {
    $p = Join-Path $Site "specs\$n.json"
    if (-not (Test-Path $p)) { git -C $Site fetch -q origin "+refs/heads/claude/lantern-redesign-pass2:refs/remotes/origin/dev" 2>$null
        $j = git -C $Site show "origin/dev:docs/blender/review/specs/$n.json" 2>$null
        if ($j) { return ($j -join "`n" | ConvertFrom-Json) } ; return $null }
    return (Get-Content $p -Raw | ConvertFrom-Json)
}

switch ($Cmd.ToLower()) {
    "status" {
        $b = Busy
        if ($b) { Write-Host "Rendering now: $b, on $(Get-Content (Join-Path $Site 'CURRENT') -ErrorAction SilentlyContinue)" -ForegroundColor Yellow }
        else { Write-Host "Nothing rendering." -ForegroundColor Green }
        Write-Host "Last run: $((Get-Content (Join-Path $Site 'last_render_summary.txt') -ErrorAction SilentlyContinue) -join ' | ')"
        Write-Host "Last upload: $(git -C $Site log -1 --format='%cr: %s')"
        Write-Host "Watcher log:"; Get-Content (Join-Path $Live "render-watch.log") -Tail 3 -ErrorAction SilentlyContinue | ForEach-Object { "  $_" }
    }
    "render" {
        $b = Busy; if ($b) { Write-Host "Already rendering ($b). 'lr status' to see it." -ForegroundColor Yellow; break }
        Start-Process -FilePath (Join-Path $Live "RENDER.cmd") -WorkingDirectory $Live
        Write-Host "Started RENDER.cmd (everything the site is missing). Progress: $Url, or 'lr status'."
    }
    "pass" {
        if (-not $Arg) { Write-Host "Usage: lr pass 864   (add 'force' to re-render clips that exist)"; break }
        $b = Busy; if ($b) { Write-Host "Already rendering ($b). Try again when 'lr status' says nothing is rendering." -ForegroundColor Yellow; break }
        $a = @("-b", "--python", "review-site\tools\lantern_review.py", "--", $Arg)
        if ($Extra -eq "force") { $a += "--force" }
        & $Blender @a 2>&1 | Where-Object { $_ -match "takes to render|done \(|FAILED|saved |pushed:|Rendered:|skipped|scrapped" }
        Get-Content (Join-Path $Site "last_render_summary.txt") -ErrorAction SilentlyContinue
    }
    "stop" {
        New-Item -ItemType File -Force (Join-Path $Site "STOP") | Out-Null
        Write-Host "Stop requested: the render finishes its current take, uploads what's done, and quits."
    }
    "open" {
        if (-not $Arg) { Write-Host "Usage: lr open 864"; break }
        $s = Spec $Arg; if (-not $s) { Write-Host "No spec for pass $Arg." -ForegroundColor Red; break }
        $f = Join-Path $Live ($s.blend -replace "/", "\")
        if (-not (Test-Path $f)) { Write-Host "$f isn't built yet: 'lr pass $Arg' builds and renders it." -ForegroundColor Yellow; break }
        $c0 = if ($s.takes[0].camfp) { $s.takes[0].camfp } else { $s.takes[0].cam3p }
        Write-Host "Opening $f (start camera: $c0)"
        Start-Process -FilePath $Blender -ArgumentList "`"$f`""
    }
    "watch"   { & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Live "render-watch.ps1"); Get-Content (Join-Path $Live "render-watch.log") -Tail 3 }
    "ratings" { git -C $Repo pull -q; python (Join-Path $Repo "tools\review_site\pull_reviews.py") }
    "library" { git -C $Repo pull -q; python (Join-Path $Repo "tools\gen_asset_library.py"); Write-Host "Menu: $Repo\docs\library\LIBRARY.md" }
    "waiting" { Select-String -Path (Join-Path $Repo "docs\blender\review\INBOX.md") -Pattern "^## \d{4}.*status: WAITING" | Select-Object -First 15 | ForEach-Object { $_.Line -replace "^## ", "  " -replace "\s+\[status: WAITING\]", "" } }
    "site"    { Start-Process $Url }
    default {
        Write-Host "Lantern Review commands (in LanternLive: 'lr <command>' in cmd, '.\lr <command>' in PowerShell)" -ForegroundColor Green
        Write-Host "  lr status          is anything rendering, last run, last upload, watcher log"
        Write-Host "  lr render          render everything the review site is missing (RENDER.cmd, minimised)"
        Write-Host "  lr pass 864        build + render one pass here and upload it   (lr pass 864 force: redo its clips)"
        Write-Host "  lr stop            stop a render after its current take (uploads what's done)"
        Write-Host "  lr open 864        open that pass's .blend in Blender"
        Write-Host "  lr waiting         passes waiting on your rating"
        Write-Host "  lr ratings         pull your ratings into the repo"
        Write-Host "  lr library         rebuild the asset menu (docs\library\LIBRARY.md)"
        Write-Host "  lr watch           run the new-spec check once"
        Write-Host "  lr site            open the review site"
    }
}
