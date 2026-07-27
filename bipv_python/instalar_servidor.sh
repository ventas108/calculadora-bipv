#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Script de instalación: Calculadora BIPV Python en Digital Ocean
# Servidor: Ubuntu 22.04 LTS
# Ejecutar como root: bash instalar_servidor.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e  # Salir si cualquier comando falla

echo "━━━ [1/8] Actualizando sistema ━━━"
apt update && apt upgrade -y

echo "━━━ [2/8] Instalando Python 3.11 y pip ━━━"
apt install -y python3.11 python3.11-venv python3-pip git curl

# Verificar versión
python3.11 --version
pip3 --version

echo "━━━ [3/8] Creando directorio de la aplicación ━━━"
mkdir -p /var/www/bipv/calculadora_bipv
cd /var/www/bipv

echo "━━━ [4/8] Clonando repositorio desde GitHub ━━━"
# REEMPLAZA <TOKEN> con tu nuevo token de GitHub (ya debes haber revocado el anterior)
# git clone https://ventas108:<TOKEN>@github.com/ventas108/calculadora-bipv.git temp_repo
# cp -r temp_repo/bipv_python/* /var/www/bipv/calculadora_bipv/
# rm -rf temp_repo

# O si ya tienes el repo clonado:
# cd /var/www/bipv/calculadora-bipv && git pull
echo "NOTA: Clona el repositorio manualmente con tu nuevo token (ver instrucciones)"

echo "━━━ [5/8] Creando entorno virtual Python ━━━"
cd /var/www/bipv/calculadora_bipv
python3.11 -m venv venv
source venv/bin/activate

echo "━━━ [6/8] Instalando dependencias Python ━━━"
pip install --upgrade pip
pip install -r requirements.txt

echo "Verificando pvlib..."
python3 -c "import pvlib; print('pvlib OK:', pvlib.__version__)"
echo "Verificando streamlit..."
python3 -c "import streamlit; print('streamlit OK:', streamlit.__version__)"

echo "━━━ [7/8] Configurando PM2 ━━━"
# PM2 ya debe estar instalado del proyecto Node.js
# Si no: npm install -g pm2

# Registrar proceso Streamlit en PM2
pm2 start ecosystem.config.js
pm2 save
pm2 status

echo "━━━ [8/8] Configurando Nginx ━━━"
cp nginx_bipv_python.conf /etc/nginx/sites-available/bipv-python
ln -sf /etc/nginx/sites-available/bipv-python /etc/nginx/sites-enabled/bipv-python
nginx -t && systemctl reload nginx

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Instalación completa."
echo "   Streamlit: http://127.0.0.1:8501 (local)"
echo "   Web: https://calc.innovacionquimica.com.co"
echo ""
echo "⚠️  Falta: agregar subdominio DNS en tu panel de dominio:"
echo "   TIPO: A  |  NOMBRE: calc  |  VALOR: IP_de_tu_servidor"
echo ""
echo "⚠️  Falta: certificado SSL para el subdominio:"
echo "   certbot --nginx -d calc.innovacionquimica.com.co"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
