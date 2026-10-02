#!/usr/bin/env bash
set -euo pipefail
ACTION="$1"
REPO="$2"
REV="$3"
DOMAIN="${4:-}"
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
if [ -n "$DOMAIN" ]; then
  python3 - "$DOMAIN" <<'PYENV'
import sys
from pathlib import Path
p=Path('.env')
lines=[x for x in p.read_text().splitlines() if not x.startswith('APP_DOMAIN=')]
p.write_text('\n'.join(lines)+'\nAPP_DOMAIN='+sys.argv[1]+'\n')
PYENV
fi
DOMAIN=$(sed -n 's/^APP_DOMAIN=//p' .env)
if [ -n "$DOMAIN" ]; then
  export COMPOSE_FILE=compose.yml:compose.https.yml
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
  if [ -n "$DOMAIN" ]; then
    docker compose up -d --build web proxy
  else
    docker compose up -d --build web
  fi
  for i in $(seq 1 60); do
    if docker compose exec -T web python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health').read().decode())"; then echo LOZAS_SUCCESS; exit 0; fi
    sleep 2
  done
  exit 1
fi

echo LOZAS_SUCCESS
