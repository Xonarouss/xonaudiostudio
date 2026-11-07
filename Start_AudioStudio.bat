@echo off
setlocal enabledelayedexpansion
title AI Audio Studio Launcher - Xonarous Inc
color 0B

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

echo =====================================================================
echo               AI AUDIO STUDIO - XONAROUS INC
echo   Hardware: Nvidia RTX 5080 (16GB) + AMD Ryzen 7 7800X3D (64GB RAM)
echo =====================================================================
echo.

:: 1. Controleer of Python beschikbaar is
python --version >nul 2>&1
if errorlevel 1 (
    echo [FOUT] Python is niet gevonden in Windows PATH!
    echo Zorg dat Python 3.10 of 3.11 is geinstalleerd en 'Add to PATH' is aangevinkt.
    echo.
    pause
    exit /b 1
)

:: 2. Controleer of venv bestaat
if not exist "venv\Scripts\activate.bat" (
    echo [*] Virtuele Python omgeving [venv] aanmaken...
    python -m venv venv
    if errorlevel 1 (
        echo [FOUT] Kon virtuele omgeving niet aanmaken.
        pause
        exit /b 1
    )
    echo [+] Virtuele omgeving succesvol aangemaakt.
)

:: Activeer venv
call venv\Scripts\activate.bat

:: 3. Controleer of benodigde pakketten geinstalleerd zijn in venv
python -c "import fastapi" >nul 2>&1
if errorlevel 1 goto INSTALL_DEPS
goto CHECK_FRONTEND

:INSTALL_DEPS
echo =====================================================================
echo   EERSTE KEER: AI AUDIO STUDIO PAKKETTEN EN CUDA INSTALLEREN
echo =====================================================================
echo.
echo [*] Stap 1/3: Pip upgraden...
python -m pip install --upgrade pip

echo.
echo [*] Stap 2/3: PyTorch met CUDA 12.4 installeren voor RTX 5080...
echo     (Dit duurt een paar minuten bij de allereerste start...)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

echo.
echo [*] Stap 3/3: Backend vereisten (FastAPI, Transformers, Diffusers, F5-TTS) installeren...
pip install -r backend\requirements.txt
echo.
echo [+] Installatie van pakketten voltooid!
echo.

:CHECK_FRONTEND
:: 4. Frontend controle
if not exist "frontend\node_modules" (
    echo [*] Frontend dependencies installeren via npm...
    cd /d "%SCRIPT_DIR%\frontend"
    call npm install
    cd /d "%SCRIPT_DIR%"
)

echo.
:: 5. Modelverificatie en automatische download
echo [*] Modellen in /models controleren...
python backend\download_models.py

echo.
:: 6. Start Backend en Frontend
echo [*] AI Audio Studio servers starten...
echo.

:: Start FastAPI backend
start "AI Audio Studio - Backend (FastAPI)" cmd /k "cd /d "%SCRIPT_DIR%" && call venv\Scripts\activate.bat && python backend\main.py"

:: Start React Frontend via Vite
start "AI Audio Studio - Frontend (Vite)" cmd /k "cd /d "%SCRIPT_DIR%\frontend" && npm run dev"

:: 7. Wacht 3 seconden en open standaardbrowser
echo [*] De studio wordt geopend in je browser...
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo =====================================================================
echo    AI Audio Studio is gelanceerd!
echo    - Web UI: http://localhost:5173 (of http://localhost:8000)
echo    - FastAPI Docs: http://127.0.0.1:8000/docs
echo.
echo    Laat de twee zwarte terminalvensters openstaan tijdens gebruik.
echo    Sluit ze om de servers te stoppen.
echo =====================================================================
echo.
pause
