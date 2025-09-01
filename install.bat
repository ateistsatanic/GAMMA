@echo off
chcp 65001 >nul
title G.A.M.M.A Bot Installer

echo [*] Быстрая установка G.A.M.M.A Bot...
echo.

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python не найден
    echo [*] Скачивание Python 3.10...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe' -OutFile 'python_installer.exe'"
    echo [✓] Запуск установки Python...
    start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
    echo [✓] Python установлен
)

:: Виртуальное окружение
if not exist "venv" (
    echo [*] Создание виртуального окружения...
    python -m venv venv
    echo [✓] Виртуальное окружение создано
)

:: Зависимости
echo [*] Установка зависимостей...
call venv\Scripts\activate.bat
pip install --upgrade pip

if exist "requirements.txt" (
    pip install -r requirements.txt
    echo [✓] Зависимости установлены
)

:: Папки
if not exist "config" mkdir "config"
if not exist "Phrases" mkdir "Phrases"

echo [✓] Установка завершена!
echo.
exit /b 0