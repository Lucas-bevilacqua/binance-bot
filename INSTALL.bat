@echo off
echo ============================================
echo   BINANCE FUTURES AGENT - Instalacao
echo ============================================
echo.

echo [1/4] Criando ambiente virtual...
python -m venv venv

echo [2/4] Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo [3/4] Instalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt

echo [4/4] Instalando TA-Lib (opcional, para indicadores avancados)...
echo Se der erro, o bot funcionara sem TA-Lib
pip install ta-lib

echo.
echo ============================================
echo   INSTALACAO CONCLUIDA!
echo ============================================
echo.
echo IMPORTANTISSIMO:
echo 1. Edite o arquivo .env
echo 2. Adicione suas credenciais da Binance
echo 3. Execute: python binance_futures_agent.py
echo.
echo OBS: Para trading real, use API Keys de futuras
echo      Configure permissao apenas de trading na Binance
echo.
pause
