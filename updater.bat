@echo off
chcp 65001 >nul
title G.A.M.M.A Bot Updater

echo [*] Быстрая проверка обновлений...
echo.

:: Временная папка для обновлений
set TEMP_UPDATE=_temp_update
if exist "%TEMP_UPDATE%" rmdir /s /q "%TEMP_UPDATE%"
mkdir "%TEMP_UPDATE%"

echo [✓] Скачивание обновлений...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/ateistsatanic/GAMMA/archive/refs/heads/main.zip' -OutFile '%TEMP_UPDATE%\update.zip'"

if not exist "%TEMP_UPDATE%\update.zip" (
    echo [!] Ошибка скачивания
    pause
    exit /b 1
)

echo [✓] Распаковка...
powershell -Command "Expand-Archive -Path '%TEMP_UPDATE%\update.zip' -DestinationPath '%TEMP_UPDATE%' -Force"

:: Копируем только основные файлы
echo [✓] Обновление файлов...
if exist "%TEMP_UPDATE%\GAMMA-main\test.py" copy /y "%TEMP_UPDATE%\GAMMA-main\test.py" .
if exist "%TEMP_UPDATE%\GAMMA-main\requirements.txt" copy /y "%TEMP_UPDATE%\GAMMA-main\requirements.txt" .
if exist "%TEMP_UPDATE%\GAMMA-main\run.bat" copy /y "%TEMP_UPDATE%\GAMMA-main\run.bat" .
if exist "%TEMP_UPDATE%\GAMMA-main\install.bat" copy /y "%TEMP_UPDATE%\GAMMA-main\install.bat" .

:: Очистка
rmdir /s /q "%TEMP_UPDATE%"

echo [✓] Обновление завершено!
echo.
exit /b 0