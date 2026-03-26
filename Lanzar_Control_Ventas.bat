@echo off
title Lanzador AlexSolutions Ultra
:: Cambia al directorio donde está el script
cd /d "%~dp0"

:: Intenta activar el entorno virtual e iniciar el programa
if exist .venv (
    echo Iniciando sistema con entorno virtual...
    start "" ".\.venv\Scripts\pythonw.exe" "control_ventas_pro.py"
) else (
    echo ERROR: No se encontro la carpeta .venv. 
    echo Por favor, crea el entorno virtual primero.
    pause
)
exit