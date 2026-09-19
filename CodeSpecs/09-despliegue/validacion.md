# Validación — Despliegue

**Estado:** en validación

## Checklist de validación del módulo

- [x] Revisión manual: rutas y nombres de proceso en los 4 archivos
      corregidos coinciden con la configuración real confirmada por SSH en
      esta sesión (`/var/www/bipv/calculadora-bipv`, proceso `streamlit-bipv`).
- [x] `ecosystem.config.js` ya no duplica configuración divergente; redirige
      a `ecosystem.config.cjs`.
- [ ] Verificación funcional en el servidor: correr
      `pm2 start bipv_python/ecosystem.config.cjs` (en una próxima sesión,
      con cuidado de no duplicar el proceso ya corriente) para confirmar que
      el archivo corregido reproduce el proceso real sin diferencias.

## Resultado

Corrección aplicada y revisada. No se reinició ningún proceso en
DigitalOcean porque estos archivos son referencia/instalación, no código que
ya esté ejecutándose — el proceso real en producción no cambió. Falta la
verificación funcional de `ecosystem.config.cjs` en una reinstalación o
prueba controlada.

