#!/usr/bin/env bash
# Pasa el servicio Odoo de la BD vencida (`odoo`) a `semillero_demo` renombrándola a `odoo`.
# Requiere que semillero_demo exista y esté inicializada.
set -euo pipefail

ODOO_CTR=odoo_semillero-verticalizacion
PG_CTR=postgres_semillero-verticalizacion
COMPOSE_DIR=/opt/proyectos/semillero-odoo/docker-odoo-ee

echo "==> stop odoo (libera conexiones)"
docker stop "$ODOO_CTR"

echo "==> rename odoo -> odoo_expired, semillero_demo -> odoo"
docker exec "$PG_CTR" psql -U odoo -d postgres -v ON_ERROR_STOP=1 <<'SQL'
SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
 WHERE datname IN ('odoo', 'semillero_demo', 'odoo_expired')
   AND pid <> pg_backend_pid();
-- si quedó un intento previo
DROP DATABASE IF EXISTS odoo_expired;
ALTER DATABASE odoo RENAME TO odoo_expired;
ALTER DATABASE semillero_demo RENAME TO odoo;
SQL

echo "==> start odoo"
docker start "$ODOO_CTR"

echo "==> wait http"
for i in $(seq 1 60); do
  if curl -fsS -o /dev/null --max-time 3 http://127.0.0.1:8076/web/login; then
    echo "OK: http://127.0.0.1:8076  (admin / admin)"
    exit 0
  fi
  sleep 2
done
echo "WARN: odoo no respondió en /web/login todavía"
exit 1
