@echo off
chcp 65001 >nul
title G.A.M.M.A Bot
echo ==============================
echo    Запуск G.A.M.M.A Bot
echo ==============================
echo.

:: Проверка обновлений (раз в неделю)
if exist "last_update_check.txt" (
    for /f "usebackq" %%i in ("last_update_check.txt") do set LAST_CHECK=%%i
) else (
    set LAST_CHECK=0
)

set /a DAYS_DIFF=(%date:~-4,4%%date:~-10,2%%date:~-7,2% - %LAST_CHECK%) / 10000

if %DAYS_DIFF% gtr 7 (
    echo [*] Проверяем обновления...
    call updater.bat
    echo %date:~-4,4%%date:~-10,2%%date:~-7,2% > last_update_check.txt
)

:: Проверка виртуального окружения
if not exist "venv\" (
    echo [!] Виртуальное окружение не найдено
    echo [!] Запустите install.bat сначала
    pause
    exit /b 1
)

:: Проверка файла бота
if not exist "test.py" (
    echo [!] Файл test.py не найден
    echo [!] Запустите updater.bat для скачивания
    pause
    exit /b 1
)

:: Проверка токена
if not exist "config\TOKEN.txt" (
    echo [!] Файл config\TOKEN.txt не найден
    echo [!] Создайте файл config\TOKEN.txt с токеном бота
    pause
    exit /b 1
)

:: Запуск бота
call venv\Scripts\activate.bat
python test.py

pause