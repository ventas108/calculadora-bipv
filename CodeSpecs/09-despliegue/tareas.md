# Tareas — Despliegue

**Estado:** en validación

- [x] Comparar `actualizar_en_servidor.sh`, `instalar_servidor.sh` y ambos
      `ecosystem.config.*` contra la configuración real confirmada por SSH.
- [x] Corregir ruta (`calculadora_bipv` → `calculadora-bipv`) y nombre de
      proceso (`calculadora-bipv-python` → `streamlit-bipv`) en los tres
      scripts.
- [x] Consolidar `ecosystem.config.cjs` como fuente de verdad; `.js` ahora
      redirige a `.cjs` en vez de duplicarlo con datos distintos.
- [ ] Confirmar en el servidor (próxima sesión con SSH) que
      `pm2 start bipv_python/ecosystem.config.cjs` reproduce exactamente el
      proceso `streamlit-bipv` ya corriendo, sin crear un proceso duplicado.
