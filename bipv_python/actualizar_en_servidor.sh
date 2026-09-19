#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Flujo de actualización diaria — app hermana Streamlit (bipv_python)
# Ruta y proceso PM2 confirmados en producción (ver
# CodeSpecs/00-director/separacion-apps.md): NO mezclar con la app web
# principal (client/server, proceso PM2 `calculadora-bipv`).
# ─────────────────────────────────────────────────────────────────────────────

# OPCIÓN A — Desde el servidor (SSH)
# 1. cd /var/www/bipv/calculadora-bipv
# 2. git pull --ff-only origin main
# 3. source bipv_python/venv/bin/activate && pip install -r bipv_python/requirements.txt
# 4. pm2 restart streamlit-bipv

# OPCIÓN B — Desde tu computador local (push → servidor jala automático)
# Solo si configuras un webhook o GitHub Action (ver sección 6 del documento)

echo "Actualizando calculadora BIPV Python (app hermana Streamlit)..."
cd /var/www/bipv/calculadora-bipv
git pull --ff-only origin main
source bipv_python/venv/bin/activate
pip install -r bipv_python/requirements.txt --quiet
pm2 restart streamlit-bipv
pm2 status

echo "✅ Actualización completa. Revisa: https://bipv.innovacionquimica.com.co"

