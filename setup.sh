#!/usr/bin/env bash
# Clona o actualiza los módulos definidos en modules.conf dentro de addons/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULES_CONF="$SCRIPT_DIR/modules.conf"
ADDONS_DIR="$SCRIPT_DIR/addons"

if [ ! -f "$MODULES_CONF" ]; then
    echo "Error: no se encontró modules.conf en $SCRIPT_DIR"
    exit 1
fi

mkdir -p "$ADDONS_DIR"

line_num=0
while IFS= read -r line || [[ -n "$line" ]]; do
    line_num=$((line_num + 1))

    # Ignorar comentarios y líneas vacías
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line//[[:space:]]/}" ]]  && continue

    # Parsear formato: <url> [-b <rama>] <ruta-local>
    read -ra parts <<< "$line"
    url="${parts[0]}"
    branch=""
    local_path=""

    i=1
    while [ $i -lt ${#parts[@]} ]; do
        if [ "${parts[$i]}" = "-b" ]; then
            i=$((i + 1))
            branch="${parts[$i]}"
        else
            local_path="${parts[$i]}"
        fi
        i=$((i + 1))
    done

    if [ -z "$url" ] || [ -z "$local_path" ]; then
        echo "Línea $line_num ignorada (formato inválido): $line"
        continue
    fi

    dest="$ADDONS_DIR/$local_path"

    if [ -d "$dest/.git" ]; then
        echo "↺  Actualizando $local_path ..."
        git -C "$dest" pull --ff-only
    else
        echo "↓  Clonando $url → addons/$local_path ..."
        mkdir -p "$(dirname "$dest")"
        if [ -n "$branch" ]; then
            git clone -b "$branch" --single-branch --depth 1 "$url" "$dest"
        else
            git clone --depth 1 "$url" "$dest"
        fi
    fi
done < "$MODULES_CONF"

echo ""
echo "Listo. Módulos instalados en addons/"
echo "Recuerda clonar Enterprise en ee-addons/enterprise si aún no lo hiciste:"
echo "  git clone git@github.com:odoo/enterprise.git -b 19.0 ee-addons/enterprise"
