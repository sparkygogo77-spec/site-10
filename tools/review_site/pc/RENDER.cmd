@echo off
rem Renders whatever the review site is missing. Runs minimised; progress is on the review site.
start "Lantern Review render" /min powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RENDER.ps1"
