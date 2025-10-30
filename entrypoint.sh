#!/usr/bin/env bash
set -e

host_check() {
  local host=$1; local port=$2; local tries=0
  until nc -z "$host" "$port" >/dev/null 2>&1 || [ $tries -gt 30 ]; do
    tries=$((tries+1))
    echo "Aguardando $host:$port..."
    sleep 1
  done
}

host_check "${POSTGRES_HOST:-postgres}" "${POSTGRES_PORT:-5432}"
host_check "${RABBITMQ_HOST:-rabbitmq}" "${RABBITMQ_PORT:-5672}"

# opcional: rodar migrations se variável ativada
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  echo "Rodando migrations..."
  alembic upgrade head || true
fi

# executa comando passado ao container (ex.: uvicorn ou python -m app.src.services.queue_consumer_service)
exec "$@"