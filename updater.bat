@echo off
chcp 65001 >nul
title G.A.M.M.A Bot Updater
echo ========================================
echo    G.A.M.M.A Bot Auto Updater
echo ========================================
echo.

:: Переменные
set GITHUB_REPO=ateistsatanic/GAMMA
set BACKUP_DIR=backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%

echo [*] Проверка обновлений с GitHub...
echo.

:: Создаем временную папку для скачивания
if not exist "temp_update" mkdir "temp_update"

:: Скачиваем архив с GitHub
echo [*] Скачивание последней версии...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/%GITHUB_REPO%/archive/refs/heads/main.zip' -OutFile 'temp_update/latest.zip'"

if exist "temp_update/latest.zip" (
    echo [✓] Архив скачан успешно
) else (
    echo [!] Ошибка скачивания
    goto error
)

:: Распаковываем архив
echo [*] Распаковка архива...
powershell -Command "Expand-Archive -Path 'temp_update/latest.zip' -DestinationPath 'temp_update' -Force"

:: Находим распакованную папку
for /f "delims=" %%i in ('dir /b /ad "temp_update" 2^>nul') do (
    if not "%%i"=="latest.zip" set "EXTRACTED_FOLDER=%%i"
)

if not defined EXTRACTED_FOLDER (
    echo [!] Не удалось найти распакованные файлы
    goto error
)

:: Создаем backup текущих файлов
echo [*] Создание резервной копии...
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

:: Создаем список исключений для backup
echo venv > exclude_list.txt
echo .git >> exclude_list.txt
echo temp_update >> exclude_list.txt
echo backup_* >> exclude_list.txt
echo config >> exclude_list.txt
echo Phrases >> exclude_list.txt

xcopy *.* "%BACKUP_DIR%" /E /I /Y /EXCLUDE:exclude_list.txt >nul 2>&1

:: Копируем новые файлы (кроме конфигов)
echo [*] Обновление файлов...
for %%f in (
    "test.py"
    "install.bat"
    "run.bat"
    "updater.bat"
    "check_update.bat"
    "requirements.txt"
    "README.md"
) do (
    if exist "temp_update\%EXTRACTED_FOLDER%\%%~f" (
        copy "temp_update\%EXTRACTED_FOLDER%\%%~f" . /Y >nul
        echo [✓] Обновлен: %%~f
    )
)

:: Очистка
del exclude_list.txt >nul 2>&1
rmdir /s /q "temp_update" >nul 2>&1

echo.
echo [✓] Обновление завершено!
echo [✓] Резервная копия сохранена в: %BACKUP_DIR%
echo.
echo Запустите run.bat для старта бота
pause
exit /b 0

:error
echo.
echo [!] Ошибка обновления
echo [!] Проверьте подключение к интернету
pause
exit /b 1