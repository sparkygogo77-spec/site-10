# Old name: the render script is RENDER.ps1 now (double-click RENDER.cmd).
& (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "RENDER.ps1")
