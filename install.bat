@echo off
chcp 65001 >nul
title G.A.M.M.A Bot Installer
echo ========================================
echo    G.A.M.M.A Bot Installer
echo ========================================
echo.

:: Переходим в папку скрипта
cd /d "%~dp0"
echo [*] Рабочая папка: %CD%
echo.

:: Проверка прав администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Требуются права администратора
    echo [!] Запустите от имени администратора
    pause
    exit /b 1
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

:: СОЗДАНИЕ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ
echo.
echo [*] Создание виртуального окружения...
if exist "venv" (
    echo [*] Удаление старого venv...
    rmdir /s /q "venv" 2>nul
)

python -m venv venv

if exist "venv\Scripts\python.exe" (
    echo [✓] Виртуальное окружение создано
) else (
    echo [!] Ошибка создания виртуального окружения
    echo [!] Попробуйте вручную: python -m venv venv
    pause
    exit /b 1
)

:: УСТАНОВКА ЗАВИСИМОСТЕЙ
echo [*] Установка зависимостей...
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [!] Ошибка активации виртуального окружения
    pause
    exit /b 1
)

pip install --upgrade pip
pip install pyrogram==2.0.106 requests aiofiles

echo [✓] Зависимости установлены

:: СОЗДАНИЕ ПАПОК
echo [*] Создание необходимых папок...
if not exist "config" mkdir "config"
if not exist "Phrases" mkdir "Phrases"

:: СКАЧИВАНИЕ ФАЙЛОВ С GITHUB
echo [*] Скачивание файлов с GitHub...
if not exist "test.py" (
    echo [*] Скачивание test.py...
    powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/ateistsatanic/GAMMA/main/test.py' -OutFile 'test.py'"
)

if not exist "requirements.txt" (
    echo [*] Скачивание requirements.txt...
    powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/ateistsatanic/GAMMA/main/requirements.txt' -OutFile 'requirements.txt'"
)

if not exist "run.bat" (
    echo [*] Скачивание run.bat...
    powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/ateistsatanic/GAMMA/main/run.bat' -OutFile 'run.bat'"
)

echo.
echo [✓] Установка завершена!
echo.
echo Следующие шаги:
echo 1. В папке config создайте файл TOKEN.txt
echo 2. В файл TOKEN.txt вставьте токен вашего бота
echo 3. В папке Phrases создайте файл messages.txt
echo 4. Запустите run.bat
echo.
echo Папки созданы:
if exist "venv" echo ✓ venv
if exist "config" echo ✓ config  
if exist "Phrases" echo ✓ Phrases
echo.
pause