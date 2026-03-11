@echo off
rem Build the agent executable using PyInstaller
rem Ensure pyinstaller is installed: pip install pyinstaller

set SCRIPT_PATH=%~dp0..\agente_sync_tray.pyw
set OUTPUT_NAME=agente_sync_tray.exe

if not exist "%SCRIPT_PATH%" (
    echo Error: agente_sync_tray.pyw not found at %SCRIPT_PATH%
    exit /b 1
)

echo Building %OUTPUT_NAME% from %SCRIPT_PATH% ...
echo Using the existing spec file: agente_sync_tray.spec
python -m PyInstaller --noconfirm C:\ICOM\Database\agente_sync_tray.spec

if %errorlevel% neq 0 (
    echo Build failed.
    exit /b %errorlevel%
) else (
    echo Build succeeded. Executable is in the "dist" folder.
)
