@echo off
chcp 65001 >nul
title G.A.M.M.A Bot Installer
echo ========================================
echo    G.A.M.M.A Bot Installer
echo ========================================
echo.

:: Проверка прав администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Требуются права администратора
    echo [!] Запустите от имени администратора
    pause
    exit /b 1
)

:: Скачиваем основные файлы с GitHub если их нет
echo [*] Проверка файлов...
if not exist "test.py" (
    echo [*] Скачивание test.py с GitHub...
    powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/ateistsatanic/GAMMA/main/test.py' -OutFile 'test.py'"
)

if not exist "requirements.txt" (
    echo [*] Скачивание requirements.txt...
    powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/ateistsatanic/GAMMA/main/requirements.txt' -OutFile 'requirements.txt'"
)

:: Проверка Python
echo [*] Проверка установленного Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Python не установлен
    echo [*] Скачивание Python 3.10...
    
    :: Скачиваем Python 3.10
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe' -OutFile 'python_installer.exe'"
    
    echo [*] Установка Python 3.10...
    echo [!] В установщике ОБЯЗАТЕЛЬНО отметьте "Add Python to PATH"
    echo [!] Нажмите OK для продолжения...
    pause
    
    start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
    
    echo [*] Проверка установки...
    python --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo [!] Ошибка установки Python
        echo [!] Установите Python вручную с python.org
        pause
        exit /b 1
    )
)

echo [✓] Python установлен
python --version

:: Создание виртуального окружения
echo.
echo [*] Создание виртуального окружения...
python -m venv venv

:: Активация и установка зависимостей
echo [*] Установка зависимостей...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

:: Создаем необходимые папки
if not exist "config" mkdir "config"
if not exist "Phrases" mkdir "Phrases"

echo.
echo [✓] Установка завершена!
echo.
echo Следующие шаги:
echo 1. В папке config создайте файл TOKEN.txt
echo 2. В файл TOKEN.txt вставьте токен вашего бота
echo 3. В папке Phrases создайте файл messages.txt
echo 4. Запустите run.bat
echo.
pause