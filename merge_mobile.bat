@echo off
rem ============================================
rem  Merge mobile markdown files into one
rem  (kept ASCII-only so it works on any codepage)
rem ============================================
chcp 65001 > nul
cd /d "%~dp0"

echo.
echo ============================================
echo   Merging mobile version files...
echo   (Chinese text above will be garbled here;
echo    the output file is UTF-8 and fine)
echo ============================================
echo.

where pwsh >nul 2>nul
if %errorlevel%==0 (
    pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0merge_mobile.ps1"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0merge_mobile.ps1"
)

echo.
echo Press any key to close...
pause > nul
