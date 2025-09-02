@echo off
chcp 65001 >nul
title G.A.M.M.A Bot
echo ==============================
echo    G.A.M.M.A Bot - Auto Setup
echo ==============================
echo.

:: Сохраняем текущую директорию
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: Проверяем установлен ли Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python не установлен!
    echo [!] Скачиваем установщик...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile 'python_installer.exe'"
    if exist "python_installer.exe" (
        echo [*] Запускаем установку Python...
        echo [*] НЕ ЗАБУДЬТЕ ПОСТАВИТЬ ГАЛКУ "Add Python to PATH"!
        echo [*] После установки закройте установщик и запустите этот файл снова
        start python_installer.exe
        pause
        exit /b 0
    ) else (
        echo [!] Не удалось скачать Python
        echo [!] Установите вручную с python.org
        pause
        exit /b 1
    )
)

:: Возвращаемся в корневую директорию
cd /d "%ROOT_DIR%"

:: Проверяем токен
if not exist "config\TOKEN.txt" (
    echo [!] Файл config\TOKEN.txt не найден
    echo [!] Создайте файл и впишите токен бота
    echo [!] Затем запустите этот файл снова
    pause
    exit /b 1
)

:: Скачиваем обновления с GitHub
echo [*] Проверяем обновления с GitHub...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/ateistsatanic/GAMMA/archive/refs/heads/main.zip' -OutFile 'gamma_update.zip'"

if exist "gamma_update.zip" (
    echo [+] Файлы скачаны, обновляем...
    
    :: Создаем временную папку
    if not exist "temp_update" mkdir temp_update
    
    :: Распаковываем архив
    powershell -Command "Expand-Archive -Path 'gamma_update.zip' -DestinationPath 'temp_update' -Force"
    
    :: Копируем файлы (кроме config и важных данных)
    if exist "temp_update\GAMMA-main" (
        xcopy "temp_update\GAMMA-main\*" "." /E /Y /I /EXCLUDE:exclude_list.txt
        echo [+] Файлы обновлены
    ) else (
        echo [!] Неправильная структура архива
    )
    
    :: Чистим временные файлы
    del "gamma_update.zip" 2>nul
    rmdir /s /q "temp_update" 2>nul
) else (
    echo [!] Не удалось скачать обновления
    echo [!] Продолжаем с текущими файлами
)

:: Создаем файл исключений чтобы не перезаписать конфиги
echo config\TOKEN.txt > exclude_list.txt
echo config\admins.json >> exclude_list.txt
echo config\tokens.json >> exclude_list.txt
echo config\multi.json >> exclude_list.txt
echo config\flooder.json >> exclude_list.txt
echo config\chats.json >> exclude_list.txt
echo config\resp.json >> exclude_list.txt
echo config\*.png >> exclude_list.txt
echo config\*.jpg >> exclude_list.txt
echo config\*.jpeg >> exclude_list.txt
echo config\*.mp4 >> exclude_list.txt
echo Phrases\ >> exclude_list.txt

:: Устанавливаем/проверяем зависимости
echo [*] Проверяем зависимости...
python -m pip install --upgrade pip

:: Проверяем каждую зависимость отдельно
for %%i in (pyrogram aiohttp aiofiles psutil tgcrypto) do (
    python -c "import %%i" 2>nul
    if errorlevel 1 (
        echo [*] Устанавливаем %%i...
        python -m pip install %%i
    ) else (
        echo [+] %%i уже установлен
    )
)

echo [+] Все зависимости проверены

:: Проверяем основной файл бота
if not exist "test.py" (
    echo [!] Файл test.py не найден!
    echo [!] Скачайте его с GitHub
    pause
    exit /b 1
)

:: Запускаем бота
echo [*] Запускаем бота...
python test.py

:: Удаляем временный файл исключений
del exclude_list.txt 2>nul

pause