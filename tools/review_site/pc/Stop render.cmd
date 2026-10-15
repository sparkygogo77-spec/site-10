@echo off
type nul > "%~dp0review-site\STOP"
echo Stop requested: the render finishes the take it is on, uploads what is done, and closes.
timeout /t 5
