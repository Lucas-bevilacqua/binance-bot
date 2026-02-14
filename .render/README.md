# Render Deployment - Binance Bot

## Arquivos de Configuração

Este diretório contém arquivos para deploy no Render.com.

### Estrutura

```
.render/
├── README.md           # Este arquivo
├── apps.yaml          # Configuração completa (bot + dashboard)
├── bot.yaml           # Configuração do Worker isolado
├── dashboard.yaml      # Configuração do Dashboard isolado
└── deploy_checklist.md # Checklist de deploy
```

## Uso Rápido

### Deploy Completo (Blueprint)

1. Fazer push para GitHub
2. No Render: New → Blueprint
3. Selecionar repositório
4. Confirmar recursos a criar

### Deploy por Componente

**Apenas Banco:**
- New → PostgreSQL
- Nome: `binance-bot-db`

**Apenas Bot:**
- New → Worker Service
- Usar `.render/bot.yaml`

**Apenas Dashboard:**
- New → Web Service
- Usar `.render/dashboard.yaml`

## Checklist

Antes do deploy, verificar:
- [ ] render.yaml validado
- [ ] .env configurado (não commitar!)
- [ ] requirements.txt completo
- [ ] schema.sql pronto
- [ ] Scripts auxiliares funcionam localmente

Após deploy, verificar:
- [ ] Serviços "Live"
- [ ] Schema aplicado
- [ ] Bot logando normalmente
- [ ] Dashboard acessível

## Scripts Auxiliares

```
scripts/
├── init_render_env.py   # Inicialização automática
├── apply_schema.py       # Aplicar schema SQL
├── health_check.py       # Health check do bot
└── setup_render.sh      # Setup automatizado (Linux/Mac)
```

## Links Úteis

- [Render Blueprint Spec](https://render.com/docs/blueprint-spec)
- [Deploy Checklist](.render/deploy_checklist.md)
- [Troubleshooting](../docs/RENDER_TROUBLESHOOTING.md)
- [Guia Completo](../DEPLOY_RENDER_COMPLETE.md)
