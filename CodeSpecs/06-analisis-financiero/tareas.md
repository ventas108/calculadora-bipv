# Tareas — Análisis financiero

**Estado:** aprobado

- [x] Aprobación humana explícita del diseño (payload canónico persistido +
      verificación de integridad) antes de tocar código — confirmada 19-sep-2026.
- [ ] Confirmar en `guardar_resultados_produccion()` el punto exacto donde
      añadir el payload canónico sin romper el formato JSON existente.
- [ ] Encargo a Claude: persistir el payload y verificar su consistencia en
      `restaurar_resultados_produccion()`, reutilizando
      `calculos/produccion_vigencia.py` (sin duplicar normalización/serialización).
- [ ] Pruebas nuevas: payload consistente restaura; payload ausente (legacy)
      no restaura; payload alterado no restaura; huella distinta bloquea antes
      del payload.
- [ ] Revisión de diff (Copilot): confirmar que Producción y su firma no
      cambiaron, solo el payload adicional persistido.
- [ ] Actualizar `implementacion.md`/`validacion.md` de este módulo y el
      director (`contratos-entre-modulos.md`, `registro-de-decisiones.md`).
- [ ] Commit en rama propia, merge `--ff-only` a `main`, push y despliegue de
      `streamlit-bipv`.
- [ ] Validación manual: simular Producción, abrir Finanzas/Presupuesto en
      pestaña nueva y confirmar restauración; luego alterar el JSON persistido
      a mano y confirmar que se rechaza.
