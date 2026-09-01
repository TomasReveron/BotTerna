@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
title BotTerna - Lanzador
cd /d "%~dp0"

if not exist "venv" (
    echo [1/2] Creando entorno virtual de Python...
    python -m venv venv
    call venv\Scripts\activate
    echo [2/2] Instalando dependencias necesarias...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

echo Iniciando BotTerna...
python main.py
if %errorlevel% neq 0 (
    pause
)
