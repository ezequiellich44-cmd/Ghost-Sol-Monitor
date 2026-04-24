@echo off
TITLE Solana Alert Bot - Startup Script
:: Change to the project directory
cd /d "D:\DGhostDev"

:: Activate the virtual environment
if exist ".\venv\Scripts\activate.bat" (
    echo [INFO] Activando entorno virtual...
    call .\venv\Scripts\activate.bat
) else (
    echo [ERROR] No se encontro la carpeta 'venv'. Asegurate de haberla creado con 'python -m venv venv'.
    pause
    exit /b
)

:: Check and install dependencies
echo [INFO] Verificando dependencias en requirements.txt...
pip install -r requirements.txt

:: Run the bot
echo [INFO] Iniciando bot.py...
python bot.py

:: Keep the window open if an error occurs or the bot stops
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] El bot se detuvo inesperadamente con el codigo: %ERRORLEVEL%
    pause
) else (
    echo.
    echo [INFO] El bot ha finalizado su ejecucion.
    pause
)
