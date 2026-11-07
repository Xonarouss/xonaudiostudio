@echo off
setlocal enabledelayedexpansion
title AI Audio Studio - Installatie Setup
color 0A

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

echo =====================================================================
echo            AI AUDIO STUDIO - INSTALLATIE SETUP WIZARD
echo   Voor Nvidia GeForce RTX 5080 + Ryzen 7800X3D + Windows 11
echo =====================================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [FOUT] Python is niet gevonden. Installeer Python 3.10 of 3.11 en vink 'Add to PATH' aan.
    pause
    exit /b 1
)

:: Create venv
if not exist "venv\Scripts\activate.bat" (
    echo [*] Virtuele omgeving 'venv' aanmaken...
    python -m venv venv
)

echo [*] Venv activeren...
call venv\Scripts\activate.bat

echo [*] Upgraden van pip...
python -m pip install --upgrade pip

echo.
echo [*] PyTorch met CUDA installeren voor RTX 5080...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

echo.
echo [*] AI Audio Studio backend vereisten installeren...
pip install -r backend\requirements.txt

echo.
echo [*] Frontend dependencies controleren...
if not exist "frontend\node_modules" (
    cd /d "%SCRIPT_DIR%\frontend"
    call npm install
    cd /d "%SCRIPT_DIR%"
)

echo.
echo =====================================================================
echo [SUCCES] Installatie is compleet!
echo Je kunt de studio nu opstarten via: Start_AudioStudio.bat
echo =====================================================================
echo.
pause
