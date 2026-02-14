# ============================================================================
# PROCFILE - Render.com Deployment
# ============================================================================
# Define como os serviços são executados no Render
#
# Documentação: https://render.com/docs/procfile
# ============================================================================

# Worker Service - Bot autônomo que executa 24/7
# Usa "worker" porque o bot não precisa receber HTTP requests
worker: python bot_master.py

# ============================================================================
# NOTAS
# ============================================================================
#
# WEB SERVICE (DASHBOARD):
#   O dashboard usa configuração separada no render.yaml
#   Não definido aqui pois requer argumentos de linha de comando específicos
#
# WORKER VS CRON:
#   - "worker": Processo de longa duração (bot 24/7)
#   - "cron": Tarefas agendadas (não é nosso caso)
#
# COMANDOS ALTERNATIVOS:
#   Se precisar rodar com parâmetros especiais, modifique render.yaml
#   em vez de usar Procfile
