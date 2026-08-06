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
#   bash bipv_python/scripts/setup_venv.sh
#   pm2 restart streamlit-bipv
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "→ Directorio de la app: $DIR"

if [ ! -d venv ] || [ ! -x venv/bin/python3 ]; then
    echo "→ Creando venv nuevo..."
    rm -rf venv
    python3 -m venv venv
else
    echo "→ venv existente detectado; se actualizarán los paquetes."
fi

echo "→ Instalando dependencias de requirements.txt..."
venv/bin/pip install --upgrade pip -q
venv/bin/pip install -r requirements.txt

echo "✅ venv listo. Reinicia la app con:  pm2 restart streamlit-bipv"
