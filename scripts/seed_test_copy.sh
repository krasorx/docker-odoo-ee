#!/usr/bin/env bash
# Corre tests de SeedSuite contra una copia descartable de semillero_demo.
# Uso: scripts/seed_test_copy.sh seed_base,seed_field /seed_base:TestSeedBaseFormStyle
set -euo pipefail
MODULES=$1
TAGS=$2
PG=postgres_semillero-verticalizacion
ODOO=odoo_semillero-verticalizacion
DB=seed_test_copy
SRC=${SRC_DB:-semillero_demo}
LOG=${LOG:-/tmp/seed_test_copy.log}

drop_copy() {
    docker exec "$PG" psql -U odoo -d postgres -q \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$DB'" \
        -c "DROP DATABASE IF EXISTS $DB" >/dev/null
}

drop_copy
trap drop_copy EXIT
docker exec "$PG" psql -U odoo -d postgres -q -c "CREATE DATABASE $DB"
# pg_dump en vez de TEMPLATE: funciona aunque haya sesiones abiertas en la base origen
docker exec "$PG" sh -c "pg_dump -U odoo -Fc $SRC | pg_restore -U odoo -d $DB --no-owner" || true

docker exec "$ODOO" sh -c "odoo -c /etc/odoo/odoo.conf --db_host=postgres \
    --db_user=\"\$DB_USER\" --db_password=\"\$DB_PASSWORD\" -d $DB \
    --http-port=8099 --gevent-port=8098 --stop-after-init --db-filter='^$DB\$' \
    -u $MODULES --test-enable --test-tags '$TAGS'" > "$LOG" 2>&1 || true

grep -E "FAIL:|ERROR: |ParseError|tests when loading" "$LOG" | tail -20 || true
grep -q "0 failed, 0 error(s)" "$LOG"
