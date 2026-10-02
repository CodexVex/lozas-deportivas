#!/usr/bin/env bash
set -euo pipefail
ACTION="$1"
REPO="$2"
REV="$3"
cloud-init status --wait >/dev/null
if ! docker compose version >/dev/null 2>&1; then
  install -d /usr/local/lib/docker/cli-plugins
  curl -fL "https://github.com/docker/compose/releases/download/v2.39.4/docker-compose-linux-x86_64" -o /usr/local/lib/docker/cli-plugins/docker-compose
  chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
fi
cd /opt/lozas
if [ ! -f .env ]; then
  umask 077
  printf 'DB_PASSWORD=%s\n' "$(openssl rand -hex 20)" > .env
fi
docker compose up -d db
for i in $(seq 1 60); do
  if docker compose exec -T db pg_isready -U lozas -d lozas; then break; fi
  sleep 2
done
docker compose exec -T db pg_isready -U lozas -d lozas
if [ "$ACTION" = setup ]; then
  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U lozas -d lozas < bd.sql
  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U lozas -d lozas < feed.sql
else
  docker compose up -d --build web
  for i in $(seq 1 60); do
    if curl -fsS http://localhost/health; then echo LOZAS_SUCCESS; exit 0; fi
    sleep 2
  done
  exit 1
fi

echo LOZAS_SUCCESS
