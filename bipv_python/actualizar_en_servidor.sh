#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Flujo de actualización diaria (equivalente a los 4 comandos del Node.js)
# Desde tu computador local o desde el servidor
# ─────────────────────────────────────────────────────────────────────────────

# OPCIÓN A — Desde el servidor (SSH)
# 1. cd /var/www/bipv/calculadora_bipv
# 2. git pull
# 3. source venv/bin/activate && pip install -r requirements.txt
# 4. pm2 restart calculadora-bipv-python

# OPCIÓN B — Desde tu computador local (push → servidor jala automático)
# Solo si configuras un webhook o GitHub Action (ver sección 6 del documento)

echo "Actualizando calculadora BIPV Python..."
cd /var/www/bipv/calculadora_bipv
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --quiet
pm2 restart calculadora-bipv-python
pm2 status

echo "✅ Actualización completa. Revisa: https://calc.innovacionquimica.com.co"
