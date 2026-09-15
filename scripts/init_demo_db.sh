#!/usr/bin/env bash
# Crea semillero_demo (Odoo 19 EE, es_AR, demo data) en el contenedor que ya corre.
set -euo pipefail

DB=semillero_demo
ODOO_CTR=odoo_semillero-verticalizacion
PG_CTR=postgres_semillero-verticalizacion
DB_HOST=postgres
DB_USER=${POSTGRES_USER:-odoo}
DB_PASSWORD=${POSTGRES_PASSWORD:?exportá POSTGRES_PASSWORD (está en .env)}

ODOO_DB=(odoo --db_host="$DB_HOST" --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD")

MODULES=$(tr '\n' ',' <<'EOF' | sed 's/,$//'
l10n_ar
l10n_ar_edi
l10n_ar_stock
l10n_ar_reports
l10n_ar_withholding
l10n_ar_ux
l10n_ar_tax
l10n_ar_bank
l10n_ar_currency_update
l10n_ar_edi_ux
l10n_ar_account_reports
l10n_ar_edi_payment_pro
account_accountant
account_accountant_ux
account_payment_pro
account_payment_pro_receiptbook
account_ux
accountant
stock_barcode
crm
purchase
mrp
fleet
hr
seed_base
seed_field
seed_weighing
seed_inventory
seed_quality
seed_plant
seed_compliance
seed_logistics
seed_crm
seed_ipr
seed_dashboard
production_dashboard
bom_dashboard
EOF
)

echo "==> [0/3] drop $DB if exists"
docker exec "$PG_CTR" psql -U odoo -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB' AND pid <> pg_backend_pid();" >/dev/null
docker exec "$PG_CTR" psql -U odoo -d postgres -c "DROP DATABASE IF EXISTS $DB;"

echo "==> [1/3] db init $DB (es_AR, country ar, with-demo)"
docker exec "$ODOO_CTR" odoo db \
  --db_host="$DB_HOST" --db_port=5432 -r "$DB_USER" -w "$DB_PASSWORD" \
  init --with-demo --language es_AR --country ar \
  --username admin --password admin \
  "$DB"

echo "==> [2/3] install modules + demo"
docker exec "$ODOO_CTR" "${ODOO_DB[@]}" \
  --database="$DB" \
  --with-demo \
  --load-language=es_AR \
  --no-http \
  --stop-after-init \
  --limit-time-cpu=36000 \
  --limit-time-real=36000 \
  -i "$MODULES"

echo "==> [3/3] post-init (empresa, transportistas)"
docker cp /opt/proyectos/semillero-odoo/docker-odoo-ee/scripts/post_init_demo.py "$ODOO_CTR":/tmp/post_init_demo.py
docker cp /opt/proyectos/semillero-odoo/docker-odoo-ee/scripts/load_demo_transport.py "$ODOO_CTR":/tmp/load_demo_transport.py

docker exec -i "$ODOO_CTR" "${ODOO_DB[@]}" \
  shell --database="$DB" --no-http \
  < /opt/proyectos/semillero-odoo/docker-odoo-ee/scripts/post_init_demo.py

echo "==> OK: database $DB lista"
docker exec "$PG_CTR" psql -U odoo -d "$DB" -c "
SELECT 'expiration' AS k, value FROM ir_config_parameter WHERE key='database.expiration_date'
UNION ALL
SELECT 'tickets', count(*)::text FROM seed_weighing_ticket
UNION ALL
SELECT 'vehicles', count(*)::text FROM fleet_vehicle
UNION ALL
SELECT 'seed_logistics_demo', demo::text FROM ir_module_module WHERE name='seed_logistics';
"
