#!/bin/bash
set -e

: "${DB_HOST:=postgres}"
: "${DB_PORT:=5432}"
: "${DB_USER:=odoo}"
: "${DB_PASSWORD:=odoo}"
: "${DB_NAME:=odoo}"
: "${ODOO_ADMIN_PASSWORD:=admin}"

ODOO_RC="/etc/odoo/odoo.conf"
ADDONS_BASE="/mnt/extra-addons"

# ── Construir addons_path dinámicamente ───────────────────────────────────────
# Escanea dos niveles: ORG/repo  (excluye enterprise del nivel raíz)
addons_list=()

for org_dir in "$ADDONS_BASE"/*/; do
    [ ! -d "$org_dir" ] && continue
    org_name=$(basename "$org_dir")
    [ "$org_name" = "enterprise" ] && continue

    for repo_dir in "$org_dir"*/; do
        [ -d "$repo_dir" ] && addons_list+=("${repo_dir%/}")
    done
done

# Enterprise siempre al final si existe
if [ -d "$ADDONS_BASE/enterprise" ]; then
    addons_list+=("$ADDONS_BASE/enterprise")
fi

if [ ${#addons_list[@]} -eq 0 ]; then
    ADDONS_PATH="$ADDONS_BASE"
else
    ADDONS_PATH=$(IFS=,; echo "${addons_list[*]}")
fi

echo "addons_path: $ADDONS_PATH"

# ── Generar odoo.conf desde template ─────────────────────────────────────────
sed \
    -e "s|{{ODOO_ADMIN_PASSWORD}}|${ODOO_ADMIN_PASSWORD}|g" \
    -e "s|{{ADDONS_PATH}}|${ADDONS_PATH}|g" \
    -e "s|{{DB_NAME}}|${DB_NAME}|g" \
    /etc/odoo/odoo.conf.template > "$ODOO_RC"

# ── Detectar si la BD ya fue inicializada ────────────────────────────────────
echo "Comprobando estado de la base de datos '$DB_NAME'..."

DB_INITIALIZED=$(python3 - <<EOF
import sys
try:
    import psycopg2
    conn = psycopg2.connect(
        host="$DB_HOST", port=$DB_PORT,
        user="$DB_USER", password="$DB_PASSWORD",
        dbname="$DB_NAME"
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'ir_module_module'
        )
    """)
    print("yes" if cur.fetchone()[0] else "no")
    conn.close()
except psycopg2.OperationalError:
    print("no")
except Exception as e:
    print("no", file=sys.stderr)
    print("no")
EOF
)

if [ "$DB_INITIALIZED" = "no" ]; then
    echo "Base de datos nueva — inicializando módulo base (esto puede tardar unos minutos)..."
    odoo -i base \
        --db_host="$DB_HOST" \
        --db_port="$DB_PORT" \
        --db_user="$DB_USER" \
        --db_password="$DB_PASSWORD" \
        --database="$DB_NAME" \
        --without-demo=all \
        --stop-after-init
    echo "Inicialización completada."
else
    echo "Base de datos ya inicializada, arrancando directamente."
fi

# ── Arrancar Odoo ─────────────────────────────────────────────────────────────
echo "Iniciando Odoo 19 Enterprise..."
exec odoo \
    --db_host="$DB_HOST" \
    --db_port="$DB_PORT" \
    --db_user="$DB_USER" \
    --db_password="$DB_PASSWORD" \
    --database="$DB_NAME" \
    --http-interface=0.0.0.0 \
    --http-port=8069 \
    --gevent-port=8072 \
    --proxy-mode
