@echo off
setlocal enabledelayedexpansion
title XonAudio Studio Launcher - Xonarous Inc
color 0B

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

echo =====================================================================
echo                  XONAUDIO STUDIO - XONAROUS INC
echo   Next-Gen Local AI Audio Workstation (Voice Cloning ^& Foley FX)
echo =====================================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in your system PATH!
    echo Please install Python 3.10 or 3.11 from python.org and check 'Add to PATH'.
    echo.
    pause
    exit /b 1
)

:: 2. Check Virtual Environment
if not exist "venv\Scripts\activate.bat" (
    echo [*] Creating isolated virtual Python environment [venv]...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Could not create virtual environment.
        pause
        exit /b 1
    )
    echo [+] Virtual environment created successfully.
)

:: Activate venv
call venv\Scripts\activate.bat

:: 3. Check Python dependencies
python -c "import fastapi" >nul 2>&1
if errorlevel 1 goto INSTALL_DEPS
goto CHECK_FRONTEND

:INSTALL_DEPS
echo =====================================================================
echo   FIRST-TIME SETUP: INSTALLING NEURAL PACKAGES ^& CUDA RUNTIME
echo =====================================================================
echo.
echo [*] Step 1/3: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [*] Step 2/3: Installing PyTorch with CUDA 12.4 acceleration...
echo     (This takes a few minutes on initial startup...)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

echo.
echo [*] Step 3/3: Installing neural studio dependencies (F5-TTS, Diffusers, etc.)...
pip install -r backend\requirements.txt
echo.
echo [+] Core dependencies installed successfully!
echo.

:CHECK_FRONTEND
:: 4. Check Frontend modules
if not exist "frontend\node_modules" (
    echo [*] Installing frontend web dependencies...
    cd /d "%SCRIPT_DIR%\frontend"
    call npm install
    cd /d "%SCRIPT_DIR%"
)

:: 5. Desktop Shortcut Prompt (if shortcut doesn't exist on Desktop)
set "DESKTOP_LNK=%USERPROFILE%\Desktop\XonAudio Studio.lnk"
if not exist "!DESKTOP_LNK!" (
    echo.
    echo ---------------------------------------------------------------------
    set /p "MK_SHORTCUT=[?] Would you like to create a Desktop shortcut with the XonAudio logo? [Y/N]: "
    if /i "!MK_SHORTCUT!"=="Y" (
        powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%\scripts\create_desktop_shortcut.ps1"
    )
    echo ---------------------------------------------------------------------
)

echo.
:: 6. Model Verification & Auto-Update Check
echo [*] Checking neural model weights and Hugging Face updates...
python backend\download_models.py

echo.
:: 7. Start Backend and Frontend Servers
echo [*] Starting XonAudio Studio servers...
echo.

:: Start FastAPI backend in dedicated window
start "XonAudio Studio - Backend (FastAPI)" cmd /k "cd /d "%SCRIPT_DIR%" && call venv\Scripts\activate.bat && python backend\main.py"

:: Start React Frontend in dedicated window
start "XonAudio Studio - Frontend (Vite)" cmd /k "cd /d "%SCRIPT_DIR%\frontend" && npm run dev"

:: 8. Wait 3 seconds and open default browser
echo [*] Launching XonAudio Studio in your browser...
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo =====================================================================
echo    XonAudio Studio is now running!
echo    - Web UI: http://localhost:5173 (or http://localhost:8000)
echo    - API Docs: http://127.0.0.1:8000/docs
echo.
echo    Keep the server terminal windows open during your session.
echo    Close them anytime to stop the studio.
echo =====================================================================
echo.
pause
