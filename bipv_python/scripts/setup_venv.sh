#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Reconstruye el entorno Python (venv) de la Calculadora BIPV en el servidor.
#
# CUÁNDO USARLO:
#   - Primer despliegue en un servidor nuevo.
#   - Si el venv se dañó o borró (ej. "python3: No such file or directory").
#   - Si cambió requirements.txt (agrega paquetes nuevos).
#
# NO es necesario en cada actualización de código: un `git pull` normal NO
# toca el venv (está en .gitignore).
#
# USO (desde la raíz del repo en el servidor):
#   bash bipv_python/scripts/setup_venv.sh              # instala/actualiza
#   bash bipv_python/scripts/setup_venv.sh --rebuild    # borra y recrea desde cero
#   pm2 restart streamlit-bipv
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "→ Directorio de la app: $DIR"

# python3-venv es requisito en Ubuntu (sale un error críptico si falta)
if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "❌ Falta el módulo venv de Python. Instálalo con:"
    echo "   sudo apt-get install -y python3-venv"
    exit 1
fi

REBUILD="${1:-}"
# Reconstruir si: se pidió --rebuild, no existe, falta python3 o pip está dañado
if [ "$REBUILD" = "--rebuild" ] || [ ! -x venv/bin/python3 ] || \
   ! venv/bin/python3 -m pip --version >/dev/null 2>&1; then
    echo "→ Recreando venv desde cero..."
    rm -rf venv
    python3 -m venv venv
else
    echo "→ venv existente y sano; se actualizarán los paquetes."
    echo "  (usa '--rebuild' si quieres recrearlo desde cero)"
fi

echo "→ Instalando dependencias de requirements.txt..."
venv/bin/pip install --upgrade pip -q
venv/bin/pip install -r requirements.txt

echo "✅ venv listo. Reinicia la app con:  pm2 restart streamlit-bipv"
