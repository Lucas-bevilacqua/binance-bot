FROM python:3.11-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Criar um usuário comum para rodar o app (melhor prática)
RUN useradd -m myuser && chown -R myuser:myuser /app
USER myuser

# Copiar arquivos
COPY --chown=myuser:myuser . .

# Comando para rodar
CMD ["bash", "start.sh"]
