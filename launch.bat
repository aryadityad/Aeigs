@echo off
setlocal enabledelayedexpansion
title Aegis Hotspot Vault — Launcher

:: Always run from the folder where launch.bat lives
cd /d "%~dp0"

:: ════════════════════════════════════════════════════════════
::   AEGIS HOTSPOT VAULT — Windows Auto Launcher
::   Author : Aryaditya Deshmukh (23BCE5056) · VIT Chennai
:: ════════════════════════════════════════════════════════════

cls
echo.
echo  =====================================================
echo    AEGIS HOTSPOT VAULT - Auto Launcher
echo    23BCE5056 ^| VIT Chennai
echo  =====================================================
echo.

:: ── Step 1: Check Python ─────────────────────────────────
echo  [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo  [X] Python not found. Please install Python 3.11+
    echo      https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo  [OK] %%i found.

:: ── Step 2: Create venv if missing ───────────────────────
echo.
echo  [2/5] Setting up virtual environment...
if not exist "venv\" (
    echo  [..] Creating venv...
    python -m venv venv
    echo  [OK] Virtual environment created.
) else (
    echo  [OK] Virtual environment already exists.
)

:: ── Step 3: Install dependencies ─────────────────────────
echo.
echo  [3/5] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo  [X] pip install failed. Check requirements.txt and internet connection.
    pause
    exit /b 1
)
echo  [OK] All dependencies installed.

:: ── Step 4: Generate RSA keys if missing ─────────────────
echo.
echo  [4/5] Checking RSA keypair...
if not exist "public.pem" (
    echo  [..] Generating RSA-2048 keypair...
    python crypto_core.py genkeys --dir .
    echo  [OK] Keys generated: public.pem + private.pem
    echo.
    echo  *** IMPORTANT: Copy private.pem to your phone! ***
) else (
    echo  [OK] RSA keypair already exists.
)

:: ── Step 5: Launch everything ────────────────────────────
echo.
echo  [5/5] Launching Aegis components...
echo.

:: Launch FTP Server in new PowerShell window
echo  [..] Starting FTP Server on port 2121...
start "Aegis — FTP Server" powershell -NoExit -Command ^
    "& { cd '%CD%'; .\venv\Scripts\activate.ps1 2>$null; if($LASTEXITCODE -ne 0){.\venv\Scripts\activate.bat}; Write-Host ''; Write-Host '  ================================================' -ForegroundColor Cyan; Write-Host '   AEGIS FTP SERVER' -ForegroundColor Cyan; Write-Host '  ================================================' -ForegroundColor Cyan; Write-Host ''; python server.py }"

:: Wait a moment for server to bind
timeout /t 3 /nobreak >nul

:: Launch Streamlit in new PowerShell window
echo  [..] Starting Streamlit Dashboard...
start "Aegis — Dashboard" powershell -NoExit -Command ^
    "& { cd '%CD%'; .\venv\Scripts\activate.ps1 2>$null; if($LASTEXITCODE -ne 0){.\venv\Scripts\activate.bat}; Write-Host ''; Write-Host '  ================================================' -ForegroundColor Green; Write-Host '   AEGIS DASHBOARD' -ForegroundColor Green; Write-Host '  ================================================' -ForegroundColor Green; Write-Host ''; python -m streamlit run app.py --server.headless true }"

:: Wait for Streamlit to spin up then open browser
echo  [..] Waiting for dashboard to start...
timeout /t 5 /nobreak >nul
echo  [..] Opening browser at http://localhost:8501 ...
start "" "http://localhost:8501"

:: ── Done ─────────────────────────────────────────────────
echo.
echo  =====================================================
echo   ALL SYSTEMS LAUNCHED
echo.
echo   FTP Server  →  Window: "Aegis - FTP Server"
echo   Dashboard   →  Window: "Aegis - Dashboard"
echo   Browser     →  http://localhost:8501
echo.
echo   To stop: close the two PowerShell windows.
echo  =====================================================
echo.
pause