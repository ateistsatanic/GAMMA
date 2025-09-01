@echo off
chcp 65001 >nul
echo Установка G.A.M.M.A Bot...

:: Простые проверки
python --version >nul 2>&1
if errorlevel 1 (
    echo Установка Python...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe' -OutFile 'python_installer.exe'"
    start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
)

if not exist "venv" python -m venv venv

call venv\Scripts\activate.bat
pip install --upgrade pip
if exist "requirements.txt" pip install -r requirements.txt

if not exist "config" mkdir "config"
if not exist "Phrases" mkdir "Phrases"

echo Установка завершена!