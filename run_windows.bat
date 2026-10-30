@echo off
title Scrcpy & ADB Wi-Fi Controller
cd /d "%~dp0"

:: Cek apakah Python terpasang
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak ditemukan di PATH Windows!
    echo Silakan install Python dari https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Buat virtual environment jika belum ada
if not exist ".venv\Scripts\activate.bat" (
    echo Membuat virtual environment (.venv)...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Menginstal dependensi...
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

:: Jalankan aplikasi GUI tanpa jendela konsol (menggunakan pythonw jika tersedia)
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" main.py
) else (
    python main.py
)
