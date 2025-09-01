@echo off
chcp 65001 >nul
title G.A.M.M.A Bot - Запуск

echo ==============================
echo    Запуск G.A.M.M.A Bot
echo ==============================
echo.

:: Проверки
if not exist "venv\" (
    echo [!] Виртуальное окружение не найдено
    pause
    exit /b 1
)

if not exist "test.py" (
    echo [!] Файл test.py не найден
    pause
    exit /b 1
)

if not exist "config\TOKEN.txt" (
    echo [!] Файл config\TOKEN.txt не найден
    pause
    exit /b 1
)

echo [✓] Все проверки пройдены
echo [*] Запуск бота...
echo.

:: Непосредственный запуск бота
call venv\Scripts\activate.bat
python test.py

echo.
echo [*] Бот завершил работу
echo [*] Нажмите любую клавишу...
pause >nul