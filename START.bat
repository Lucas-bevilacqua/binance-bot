@echo off
title Binance Futures Agent

echo ============================================
echo   BINANCE FUTURES AGENT
echo ============================================
echo.

REM Verificar se venv existe
if not exist "venv\" (
    echo [!] Ambiente virtual nao encontrado
    echo [*] Execute INSTALL.bat primeiro
    pause
    exit /b
)

REM Ativar ambiente virtual
echo [*] Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Verificar se .env está configurado
findstr /C:"BINANCE_API_KEY=" .env | findstr /V /C:"BINANCE_API_KEY=$" >nul
if errorlevel 1 (
    echo.
    echo [!] ATENCAO: Configure suas API Keys no arquivo .env
    echo [*] Abra o arquivo .env e preencha:
    echo     - BINANCE_API_KEY
    echo     - BINANCE_API_SECRET
    echo.
    pause
    exit /b
)

echo.
echo ============================================
echo   INICIANDO AGENTE...
echo ============================================
echo.

REM Executar bot
python binance_futures_agent.py

REM Se houver erro, pausar para ver mensagem
if errorlevel 1 (
    echo.
    echo [!] Erro ao executar
    pause
)
