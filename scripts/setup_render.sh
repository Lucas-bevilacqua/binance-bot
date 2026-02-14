#!/bin/bash
# ============================================================================
# DEPLOY AUTOMATIZADO PARA RENDER.COM
# ============================================================================
# Script para setup completo do Binance Bot no Render com PostgreSQL
#
# Uso: bash scripts/setup_render.sh
#
# Pré-requisitos:
#   - Conta no Render.com
#   - Render CLI instalado (pip install render-cli)
#   - Git configurado
# ============================================================================

set -e  # Parar em erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# FUNÇÕES
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Verificando pré-requisitos..."

    # Verificar Render CLI
    if ! command -v render &> /dev/null; then
        log_warning "Render CLI não encontrado. Instalando..."
        pip install render-cli
    fi

    # Verificar se está logado
    if ! render whoami &> /dev/null; then
        log_error "Você precisa fazer login no Render primeiro:"
        log_info "  render login"
        exit 1
    fi

    log_success "Pré-requisitos OK"
}

check_git_repo() {
    log_info "Verificando repositório Git..."

    if [ ! -d .git ]; then
        log_error "Este não é um repositório Git"
        log_info "Execute: git init"
        exit 1
    fi

    log_success "Repositório Git OK"
}

check_env_file() {
    log_info "Verificando arquivo .env..."

    if [ ! -f .env ]; then
        log_warning ".env não encontrado. Copiando de .env.example..."
        cp .env.example .env
        log_warning "Edite .env com suas credenciais antes de continuar!"
    fi

    log_success "Arquivo de ambiente OK"
}

# ============================================================================
# SETUP DO BANCO DE DADOS
# ============================================================================

setup_database() {
    log_info "Configurando banco PostgreSQL..."

    # Criar banco PostgreSQL
    log_info "Criando banco de dados no Render..."
    render create-database binance-bot-db \
        --database-name binance_bot \
        --user binance_bot_user \
        --region oregon \
        --plan free

    log_success "Banco de dados criado"

    # Aguardar banco estar pronto
    log_info "Aguardando banco ficar pronto..."
    sleep 30

    # Rodar schema SQL
    log_info "Aplicando schema SQL..."

    # Obter connection string
    DB_URL=$(render get-database-connection binance-bot-db --internal)

    # Usar psql ou Python para rodar schema
    if command -v psql &> /dev/null; then
        psql "$DB_URL" -f database/schema.sql
    else
        log_warning "psql não encontrado. Usando Python..."
        python -c "
import asyncio
import asyncpg
import sys

async def run_schema():
    with open('database/schema.sql', 'r') as f:
        schema = f.read()
    conn = await asyncpg.connect('$DB_URL')
    try:
        await conn.execute(schema)
        print('Schema aplicado com sucesso!')
    finally:
        await conn.close()

asyncio.run(run_schema())
"
    fi

    log_success "Schema aplicado"
}

# ============================================================================
# SETUP DOS SERVIÇOS
# ============================================================================

setup_worker_service() {
    log_info "Configurando Worker Service (Bot)..."

    render create-service \
        --type worker \
        --name binance-bot-worker \
        --runtime python \
        --region oregon \
        --plan free \
        --env "PYTHON_VERSION=3.11" \
        --env "SCAN_INTERVAL=60" \
        --env "MONITOR_INTERVAL=15" \
        --env "MAX_POSITIONS=3" \
        --build-command "pip install -r requirements.txt" \
        --start-command "python bot_master.py" \
        --repo $(git remote get-url origin)

    log_success "Worker Service criado"
}

setup_dashboard_service() {
    log_info "Configurando Web Service (Dashboard)..."

    render create-service \
        --type web \
        --name binance-dashboard \
        --runtime python \
        --region oregon \
        --plan free \
        --env "PYTHON_VERSION=3.11" \
        --build-command "pip install -r requirements.txt" \
        --start-command "streamlit run dashboard.py --server.port=\$PORT --server.address=0.0.0.0 --server.headless=true" \
        --repo $(git remote get-url origin)

    log_success "Dashboard Service criado"
}

# ============================================================================
# CONFIGURAÇÃO DE VARIÁVEIS DE AMBIENTE
# ============================================================================

setup_env_vars() {
    local service_name=$1

    log_info "Configurando variáveis de ambiente para $service_name..."

    # Variáveis sensíveis (lê do .env)
    if [ -f .env ]; then
        # Ler API Key
        BINANCE_API_KEY=$(grep BINANCE_API_KEY .env | cut -d= -f2)
        if [ -n "$BINANCE_API_KEY" ]; then
            render env set "$service_name" BINANCE_API_KEY "$BINANCE_API_KEY"
        fi

        # Ler API Secret
        BINANCE_API_SECRET=$(grep BINANCE_API_SECRET .env | cut -d= -f2)
        if [ -n "$BINANCE_API_SECRET" ]; then
            render env set "$service_name" BINANCE_API_SECRET "$BINANCE_API_SECRET"
        fi

        # OpenAI (opcional)
        OPENAI_KEY=$(grep OPENAI_API_KEY .env | cut -d= -f2)
        if [ -n "$OPENAI_KEY" ]; then
            render env set "$service_name" OPENAI_API_KEY "$OPENAI_KEY"
        fi

        # Telegram (opcional)
        TELEGRAM_TOKEN=$(grep TELEGRAM_BOT_TOKEN .env | cut -d= -f2)
        if [ -n "$TELEGRAM_TOKEN" ]; then
            render env set "$service_name" TELEGRAM_BOT_TOKEN "$TELEGRAM_TOKEN"
        fi
    fi

    # DATABASE_URL (do banco criado)
    DB_URL=$(render get-database-connection binance-bot-db --internal)
    render env set "$service_name" DATABASE_URL "$DB_URL"

    log_success "Variáveis de ambiente configuradas"
}

# ============================================================================
# HEALTH CHECK
# ============================================================================

run_health_check() {
    local service_name=$1

    log_info "Verificando status do serviço..."

    local status=$(render get-service "$service_name" --json | jq -r '.status')

    if [ "$status" = "live" ]; then
        log_success "Serviço $service_name está rodando!"
    else
        log_warning "Status do $service_name: $status"
        log_info "Acompanhe os logs: render logs -f $service_name"
    fi
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    log_info "=== Iniciando Setup do Binance Bot no Render ==="

    check_prerequisites
    check_git_repo
    check_env_file

    # Perguntar qual setup
    echo ""
    echo "Escolha o tipo de setup:"
    echo "1) Completo (Banco + Worker + Dashboard)"
    echo "2) Apenas Banco de Dados"
    echo "3) Apenas Worker Service"
    echo "4) Apenas Dashboard"
    echo ""
    read -p "Opção [1-4]: " choice

    case $choice in
        1)
            setup_database
            setup_worker_service
            setup_dashboard_service
            setup_env_vars "binance-bot-worker"
            run_health_check "binance-bot-worker"
            ;;
        2)
            setup_database
            ;;
        3)
            setup_worker_service
            setup_env_vars "binance-bot-worker"
            ;;
        4)
            setup_dashboard_service
            ;;
        *)
            log_error "Opção inválida"
            exit 1
            ;;
    esac

    log_success "=== Setup concluído! ==="
    log_info "Próximos passos:"
    log_info "  1. Configure variáveis de ambiente sensíveis no Dashboard Render"
    log_info "  2. Acompanhe os logs: render logs -f <nome-do-serviço>"
    log_info "  3. Acesse o dashboard pela URL gerada"
}

# Executar
main "$@"
