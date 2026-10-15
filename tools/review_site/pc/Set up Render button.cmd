@echo off
rem One-time setup, asked for by J: lets the "Render on my PC" button on lantern-review-j.vercel.app start "Render Lantern Review.cmd".
rem Adds one entry for your Windows user only (HKEY_CURRENT_USER\Software\Classes\lanternrender). Undo: "Remove Render button.cmd".
rem The link passes nothing to the script: all it can do is start this render.
reg add "HKCU\Software\Classes\lanternrender" /ve /d "URL:Lantern Review render" /f >nul
reg add "HKCU\Software\Classes\lanternrender" /v "URL Protocol" /d "" /f >nul
reg add "HKCU\Software\Classes\lanternrender\shell\open\command" /ve /d "\"%~dp0Render Lantern Review.cmd\"" /f >nul
echo Done. The "Render on my PC" button on the review site now starts your render.
echo The first time, your browser asks to open it: tick "Always allow" and click Open.
pause
