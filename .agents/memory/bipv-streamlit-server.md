---
name: BIPV Streamlit — servidor y paths
description: Datos de conexión y rutas del servidor de producción en Digital Ocean
---

## Servidor
- IP: 198.199.75.160
- Dominio: calc.innovacionquimica.com.co
- OS: Linux (bipv-colombia)

## Paths
- **Path actual del repo:** `/var/www/bipv/calculadora-bipv` (confirmado agosto 2026)
- Path anterior (obsoleto): `/root/BIPV_Streamlit` — ya NO existe
- venv Python: verificar dentro del nuevo path, probablemente `bipv_python/venv/`

## Git
- Rama activa: `main`
- Remote: https://github.com/ventas108/calculadora-bipv.git
- Cambios locales frecuentes en archivos de catálogo → siempre `git stash` antes de `git pull`

## PM2
- Nombre del proceso: desconocido en el nuevo path (antes era "bipv")
- `pm2 list` para encontrar el nombre real
- Si no existe: `pm2 start "bipv_python/venv/bin/streamlit run bipv_python/app.py --server.port 8501 --server.address 0.0.0.0" --name bipv-calc && pm2 save`

**Why:** El servidor fue migrado de /root/BIPV_Streamlit a /var/www/bipv/calculadora-bipv. El proceso PM2 "bipv" no existe en el nuevo path.
