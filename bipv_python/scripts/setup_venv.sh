#!/usr/bin/env bash
# setup_venv.sh — Crea/recrea el venv de Python en el servidor
# Usar tras git reset --hard o primer despliegue.
# Ejecutar desde /var/www/bipv/calculadora-bipv/
set -e
cd "$(dirname "$0")/../.."   # ir a la raíz del repo

echo "[1/4] Desactivando venv anterior (si existe)..."
deactivate 2>/dev/null || true

echo "[2/4] Eliminando venv antiguo..."
rm -rf bipv_python/venv

echo "[3/4] Creando venv limpio con Python del sistema..."
python3 -m venv bipv_python/venv

echo "[4/4] Instalando dependencias (~3-5 min)..."
source bipv_python/venv/bin/activate
pip install --upgrade pip --quiet
pip install -r bipv_python/requirements.txt

echo ""
echo "✓ venv listo. Para activar:"
echo "  source bipv_python/venv/bin/activate"
echo ""
echo "  pm2 restart streamlit-bipv"
