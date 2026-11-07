@echo off
setlocal enabledelayedexpansion
title XonAudio Studio - Setup Wizard
color 0A

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

echo =====================================================================
echo               XONAUDIO STUDIO - INSTALLATION WIZARD
echo          By Xonarous Inc (https://xonarous.nl)
echo =====================================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found. Please install Python 3.10 or 3.11 with 'Add to PATH' checked.
    pause
    exit /b 1
)

:: Create venv
if not exist "venv\Scripts\activate.bat" (
    echo [*] Creating virtual environment 'venv'...
    python -m venv venv
)

echo [*] Activating venv...
call venv\Scripts\activate.bat

echo [*] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [*] Installing PyTorch with CUDA 12.4 acceleration...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

echo.
echo [*] Installing XonAudio Studio backend dependencies...
pip install -r backend\requirements.txt

echo.
echo [*] Verifying frontend web dependencies...
if not exist "frontend\node_modules" (
    cd /d "%SCRIPT_DIR%\frontend"
    call npm install
    cd /d "%SCRIPT_DIR%"
)

echo.
echo =====================================================================
echo [SUCCESS] Installation complete!
echo You can now launch the studio anytime via: Start_AudioStudio.bat
echo =====================================================================
echo.
pause
