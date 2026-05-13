#!/bin/bash
set -e

: "${DB_HOST:=postgres}"
: "${DB_PORT:=5432}"
: "${DB_USER:=odoo}"
: "${DB_PASSWORD:=odoo}"
: "${ODOO_ADMIN_PASSWORD:=admin}"

ODOO_RC="/etc/odoo/odoo.conf"
ADDONS_BASE="/mnt/extra-addons"

# ── Construir addons_path dinámicamente ────────────────────────────────────────
# Escanea dos niveles: ORG/repo  (excluye el directorio enterprise del nivel raíz)
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
    ADDONS_PATH="/mnt/extra-addons"
else
    ADDONS_PATH=$(IFS=,; echo "${addons_list[*]}")
fi

echo "addons_path detectado: $ADDONS_PATH"

# ── Generar odoo.conf desde template ──────────────────────────────────────────
sed \
    -e "s|{{ODOO_ADMIN_PASSWORD}}|${ODOO_ADMIN_PASSWORD}|g" \
    -e "s|{{ADDONS_PATH}}|${ADDONS_PATH}|g" \
    /etc/odoo/odoo.conf.template > "$ODOO_RC"

# ── Leer parámetros DB desde el conf generado ─────────────────────────────────
DB_ARGS=()
function check_config() {
    local param="$1" value="$2"
    if grep -qE "^\s*\b${param}\b\s*=" "$ODOO_RC"; then
        value=$(grep -E "^\s*\b${param}\b\s*=" "$ODOO_RC" | cut -d' ' -f3 | tr -d '"\r\n')
    fi
    DB_ARGS+=("--${param}" "${value}")
}

check_config "db_host" "$DB_HOST"
check_config "db_port" "$DB_PORT"
check_config "db_user" "$DB_USER"
check_config "db_password" "$DB_PASSWORD"

# ── Arrancar Odoo ──────────────────────────────────────────────────────────────
echo "Iniciando Odoo 19 Enterprise..."
exec odoo \
    "${DB_ARGS[@]}" \
    --http-interface=0.0.0.0 \
    --http-port=8069 \
    --gevent-port=8072 \
    --proxy-mode
