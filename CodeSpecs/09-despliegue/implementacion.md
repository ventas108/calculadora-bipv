# Implementación — Despliegue

**Estado:** implementado

## Cambios realizados

- `actualizar_en_servidor.sh`: ruta corregida a `/var/www/bipv/calculadora-bipv`,
  venv referenciado en `bipv_python/venv/`, `pm2 restart streamlit-bipv`.
- `instalar_servidor.sh`: mismas correcciones de ruta; crea el venv dentro de
  `bipv_python/`; usa `pm2 start bipv_python/ecosystem.config.cjs`.
- `ecosystem.config.cjs`: corregido para coincidir exactamente con
  `pm2 describe streamlit-bipv` (nombre `streamlit-bipv`, `cwd` en la raíz
  del repo, script/args relativos con prefijo `bipv_python/`).
- `ecosystem.config.js`: convertido en redirección explícita a `.cjs`
  (`module.exports = require("./ecosystem.config.cjs")`), ya no es un
  segundo archivo divergente.

## Archivos modificados

- `bipv_python/actualizar_en_servidor.sh`
- `bipv_python/instalar_servidor.sh`
- `bipv_python/ecosystem.config.cjs`
- `bipv_python/ecosystem.config.js`


_(Pendiente)_
