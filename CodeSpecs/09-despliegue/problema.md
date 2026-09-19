# Módulo 09 — Despliegue

**Estado:** en validación

## Alcance de la fase

Validación, build, GitHub, DigitalOcean y procedimiento de rollback.

## Problema a resolver

Los scripts de infraestructura de la app Streamlit
(`bipv_python/actualizar_en_servidor.sh`, `bipv_python/instalar_servidor.sh`,
`bipv_python/ecosystem.config.js`) usaban una ruta (`/var/www/bipv/calculadora_bipv`,
con guión bajo) y un nombre de proceso PM2 (`calculadora-bipv-python`) que
**nunca coincidieron** con lo que realmente corre en producción
(`/var/www/bipv/calculadora-bipv`, proceso `streamlit-bipv`, confirmado por
SSH en esta misma sesión). Además existían dos archivos
`ecosystem.config.*` distintos para la misma app, y ninguno de los dos
coincidía exactamente con la configuración real (`pm2 describe streamlit-bipv`).
Ejecutar esos scripts tal como estaban habría fallado (ruta inexistente,
proceso no encontrado).

## Contexto

Esto no afectaba la app ya desplegada (el proceso real seguía corriendo
correctamente), pero cualquier reinstalación futura del servidor, o un
intento de seguir estos scripts al pie de la letra, habría fallado o hecho
lo incorrecto. `DEPLOY_README.md` (sección PowerShell) sí tenía la
configuración correcta y sirvió de referencia para la corrección.

