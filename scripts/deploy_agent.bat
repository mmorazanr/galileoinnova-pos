@echo off
echo ===================================================
echo 1. Compilando Agente (Creando .exe)
echo ===================================================
call C:\ICOM\Database\scripts\build_agent_exe.bat
if %errorlevel% neq 0 (
    echo Error al compilar. Deteniendo el proceso...
    pause
    exit /b %errorlevel%
)
echo.

echo ===================================================
echo 2. Subiendo al Servidor FTP
echo ===================================================
cd C:\ICOM\Database
python _ftp_agents.py
if %errorlevel% neq 0 (
    echo Error al subir por FTP. Deteniendo el proceso...
    pause
    exit /b %errorlevel%
)
echo.

echo ===================================================
echo 3. Sincronizando GitHub
echo ===================================================
git add .
git commit -m "Compilado agente con fix de idiomas y actualizados scripts"
git push origin main
if %errorlevel% neq 0 (
    echo Error al hacer push a Github.
    pause
    exit /b %errorlevel%
)

echo.
echo ===================================================
echo PROCESO COMPLETADO EXITOSAMENTE
echo ===================================================
pause
