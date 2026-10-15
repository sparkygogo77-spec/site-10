@echo off
rem Runs minimised; progress shows on the review site and a notification pops up at the end.
start "Lantern Review render" /min powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Render Lantern Review.ps1"
