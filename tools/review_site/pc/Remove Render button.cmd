@echo off
reg delete "HKCU\Software\Classes\lanternrender" /f
echo The site button no longer starts anything on this PC.
pause
