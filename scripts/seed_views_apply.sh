#!/usr/bin/env bash
# Carga XML de vistas en semillero_demo sin -u: un -u sobre seed_* recarga en cascada
# la demo de toda la suite y pisa estados de órdenes/viajes.
# Todo o nada: si un archivo falla no se commitea ninguno y el script sale con 1.
# Uso: scripts/seed_views_apply.sh seed_plant views/seed_drying_order_views.xml [...]
set -euo pipefail
DB=${DB:-semillero_demo}
ODOO=odoo_semillero-verticalizacion
MODULE=$1
shift
OUT=$(docker exec -i -e MODULE="$MODULE" -e FILES="$*" "$ODOO" sh -c \
    "odoo shell -c /etc/odoo/odoo.conf --db_host=postgres --db_user=\"\$DB_USER\" \
     --db_password=\"\$DB_PASSWORD\" -d $DB --no-http 2>&1" <<'PY'
import os
import traceback
from odoo.tools import convert_file
try:
    for path in os.environ['FILES'].split():
        convert_file(env, os.environ['MODULE'], path, {}, mode='update', noupdate=False)
        print('SEEDAPPLY cargado', os.environ['MODULE'], path)
    env.cr.commit()
    print('SEEDAPPLY commit')
except Exception:
    env.cr.rollback()
    print('SEEDAPPLY ERROR (rollback, nada commiteado)')
    print('SEEDAPPLY ' + traceback.format_exc().replace('\n', '\nSEEDAPPLY '))
PY
)
echo "$OUT" | grep '^SEEDAPPLY' | sed 's/^SEEDAPPLY //'
echo "$OUT" | grep -q '^SEEDAPPLY commit$'
