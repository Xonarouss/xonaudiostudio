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
echo   Official Repository: https://github.com/Xonarouss/xonaudiostudio
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
goto CHECK_UPDATES

:INSTALL_DEPS
echo =====================================================================
echo   FIRST-TIME SETUP: INSTALLING NEURAL PACKAGES ^& CUDA RUNTIME
echo =====================================================================
echo.
echo [*] Step 1/4: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [*] Step 2/4: Installing PyTorch with CUDA 12.8 (RTX 50-series / sm_120 support)...
pip install torch torchvision torchaudio --pre --index-url https://download.pytorch.org/whl/nightly/cu128

echo.
echo [*] Step 3/4: Installing neural studio dependencies (F5-TTS, Diffusers, XTTS, torchsde)...
pip install -r backend\requirements.txt
pip install torchsde einops encodec pydub phonemizer imageio-ffmpeg

echo.
echo [*] Step 4/4: Setting up FFmpeg audio processing binaries...
python -c "import shutil, os, sys, imageio_ffmpeg; dst=os.path.join(os.path.dirname(sys.executable),'ffmpeg.exe'); os.path.exists(dst) or shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(), dst)" >nul 2>&1
echo.
echo [+] Core dependencies and FFmpeg installed successfully!
echo.

:CHECK_UPDATES
:: 3.5 Verify critical dependencies (torchsde, FFmpeg, TTS, Fish Speech deps, audio-separator, yt-dlp)
python -c "import torchsde, einops, TTS, coqpit, tiktoken, yt_dlp, faiss" >nul 2>&1
if errorlevel 1 (
    echo [*] Verifying and installing voice, SFX and song cover processing libraries...
    pip install torchsde einops encodec pydub phonemizer imageio-ffmpeg coqpit trainer anyascii pysbd num2words tiktoken vector-quantize-pytorch pytorch-lightning lightning loralib natsort pyrootutils yt-dlp faiss-cpu audio-separator
    python -c "import TTS" >nul 2>&1 || pip install TTS==0.22.0
)

:: 3.6 Check Song Cover Lab checkpoints (BS-RoFormer and RMVPE)
if not exist "models\bs_roformer\*.ckpt" (
    echo [*] [Song Cover Lab] On-demand downloading BS-RoFormer vocal separator (~640 MB)...
    python -c "from backend.models_manager import download_model; download_model('bs_roformer')"
)
if not exist "models\rvc\rmvpe.pt" (
    echo [*] [Song Cover Lab] On-demand downloading RMVPE pitch extractor (~150 MB)...
    python -c "from backend.models_manager import download_model; download_model('rmvpe')"
)

if not exist "venv\Scripts\ffmpeg.exe" (
    echo [*] Ensuring FFmpeg audio binaries are linked...
    python -c "import shutil, os, sys, imageio_ffmpeg; shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(), os.path.join(os.path.dirname(sys.executable), 'ffmpeg.exe'))" >nul 2>&1
)

:: 4. Check GitHub Repository for Updates (Auto-Pull)
python backend\check_github_update.py

:: 5. Check Frontend web dependencies
if not exist "frontend\node_modules" (
    echo [*] Installing frontend web dependencies...
    cd /d "%SCRIPT_DIR%\frontend"
    call npm install
    cd /d "%SCRIPT_DIR%"
)

:: 6. Desktop Shortcut Prompt (if shortcut doesn't exist on Desktop)
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
:: 7. Model Verification & Auto-Update Check
echo [*] Checking neural model weights and Hugging Face updates...
python backend\download_models.py

echo.
:: 8. Start Backend Server
echo [*] Starting FastAPI Backend on http://127.0.0.1:8000...
start "XonAudio Studio - Backend (FastAPI)" /d "%SCRIPT_DIR%" cmd /k "call venv\Scripts\activate.bat && python backend\main.py"

:: 9. Wait for Backend to be online (Eliminates ECONNREFUSED in Vite proxy)
echo [*] Waiting for FastAPI backend to initialize...
:WAIT_BACKEND
timeout /t 1 /nobreak >nul
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/health' -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 goto WAIT_BACKEND
echo [+] Backend is online and ready!

:: 10. Start Frontend & Open Browser
echo [*] Starting React Frontend on http://localhost:5173...
start "XonAudio Studio - Frontend (Vite)" /d "%SCRIPT_DIR%\frontend" cmd /k "npm run dev"

timeout /t 2 /nobreak >nul
echo [*] Launching XonAudio Studio in your web browser...
start http://localhost:5173

echo.
echo =====================================================================
echo    XonAudio Studio is now running!
echo    - Web UI: http://localhost:5173 (or http://localhost:8000)
echo    - API Docs: http://127.0.0.1:8000/docs
echo    - GitHub: https://github.com/Xonarouss/xonaudiostudio
echo.
echo    Keep the server terminal windows open during your session.
echo    Close them anytime to stop the studio.
echo =====================================================================
echo.
pause
