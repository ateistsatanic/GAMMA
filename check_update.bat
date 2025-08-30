@echo off
chcp 65001 >nul
title Check for Updates
echo ==============================
echo    Проверка обновлений
echo ==============================
echo.

call updater.bat
echo %date:~-4,4%%date:~-10,2%%date:~-7,2% > last_update_check.txt

echo.
echo Обновление проверено!
pause