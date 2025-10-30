FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Dependências do sistema (inclui netcat para o entrypoint aguardar serviços)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    netcat-openbsd \
    ca-certificates \
    apt-utils \
    bash \
 && rm -rf /var/lib/apt/lists/*

# copia e instala requirements
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# copia código
COPY . /app

# garante entrypoint executável (útil em Linux; no Windows ENTRYPOINT chama bash)
RUN chmod +x /app/entrypoint.sh

# chama o script via bash (evita erro se arquivo perder permissão)
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]