# Lantern Review watcher: starts RENDER.cmd when the Blender chats have pushed new or changed specs and nothing is
# rendering, and logs new jobs in docs/pc_requests/. Cheap (one git fetch, no Blender); safe to run every few minutes.
# What actually renders is still decided by lantern_review.py (skips KEEP/DROP and takes that already have clips).
# Log: render-watch.log. Remembered state: render-watch.state (delete it to force one run).

$ErrorActionPreference = "Continue"
$Live  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Site  = Join-Path $Live "review-site"
$State = Join-Path $Live "render-watch.state"
$LogF  = Join-Path $Live "render-watch.log"
$Dev   = "claude/lantern-redesign-pass2"
$Specs = "docs/blender/review/specs"

function Log($msg) { Add-Content $LogF "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg" }

function Test-PidFile($file, $namePattern) {
    $id = Get-Content (Join-Path $Site $file) -ErrorAction SilentlyContinue
    if (-not $id) { return $false }
    return [bool](Get-Process -Id $id -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match $namePattern })
}

# 1. Busy? RENDER.ps1 holds RENDERING; any lantern_review.py run (also ones a chat started by hand) holds BLENDER.lock.
if ((Test-PidFile "RENDERING" "powershell|pwsh") -or (Test-PidFile "BLENDER.lock" "blender")) {
    exit 0
}
if (-not (Test-Path (Join-Path $Site ".git"))) { Log "no review-site clone"; exit 1 }

# 2. What the chats' branch has now (fetch only: touches no files in the clone).
& git -C $Site fetch -q origin "+refs/heads/${Dev}:refs/remotes/origin/dev" 2>$null
if ($LASTEXITCODE -ne 0) { Log "fetch failed"; exit 1 }
# Jobs project threads left for the PC chat (docs/pc_requests/*.md): log each new one once; the chat's loop acts on it.
$ReqState = Join-Path $Live "render-watch.requests"
$known = @(Get-Content $ReqState -ErrorAction SilentlyContinue)
foreach ($r in (& git -C $Site ls-tree --name-only origin/dev "docs/pc_requests/")) {
    if ($r -match '\.md$' -and $r -notmatch 'README\.md$' -and $known -notcontains $r) {
        Log "pc request: $r"; Add-Content $ReqState $r
    }
}

$tree = (& git -C $Site rev-parse "origin/dev:$Specs").Trim()
$lastSpecCommit = [int](& git -C $Site log -1 --format=%ct origin/dev -- $Specs)
$ageMin = ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - $lastSpecCommit) / 60
$seen = (Get-Content $State -ErrorAction SilentlyContinue | Select-Object -First 1)
if ($seen) { $seen = $seen.Trim() }

# 3. Decide.
function Test-ReadyToRender($tree, $seen, $ageMin) {
    if (-not $seen) { Set-Content $State $tree; Log "first check: remembered specs tree"; return $false }
    if ($tree -eq $seen) { return $false }
    if ($ageMin -lt 5) { return $false }     # chats often fix a spec a minute later; also covers clock skew (negative age)
    return $true
}

if (-not (Test-ReadyToRender $tree $seen $ageMin)) { exit 0 }

# 4. Go. RENDER.ps1 has the watchdog, keep-awake, restarts and the end notification.
Set-Content $State $tree
Log ("specs changed (tree {0}, last spec commit {1:N0} min ago): starting RENDER.cmd" -f $tree.Substring(0, 8), $ageMin)
Start-Process -FilePath (Join-Path $Live "RENDER.cmd") -WorkingDirectory $Live
