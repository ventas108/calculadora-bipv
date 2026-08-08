---
name: BIPV - ejecutor de escenarios Fase 4
description: Reglas del ejecutor reproducible de escenarios (referencia/actual/optimizada) y trampa de clipping silencioso en la agregación FS.
---

# Ejecutor de escenarios (calculos/ejecutor_escenarios.py)

- Regla: `ejecutar_escenarios()` no confía en los inputs vivos aunque el `base_id` coincida — verifica panel, N_serie, N_strings_tracker y eta_inversor contra los valores congelados en `base["componentes"]` y aborta si difieren.
- **Why:** la revisión de arquitectura detectó que comparar solo bases recapturadas permite simular con inputs eléctricos distintos etiquetados con la base vieja (viola reproducibilidad).
- **How to apply:** cualquier nueva entrada de simulación en la Fase 4 debe o derivarse de la base congelada o verificarse por huella contra ella antes de simular.

# Clipping silencioso en agregación FS

- `promedio_fs_por_claves` (agregacion_fs.py) y otros pasos hacen `.clip(0.0, 1.0)`: un FS_geometrico fuera de rango (>1 o <0) NO llega a validadores aguas abajo — se recorta en silencio.
- **How to apply:** validar el rango de `FS_geometrico` en el DataFrame crudo, ANTES de `alinear_fs_con_tmy`, si se quiere fallar explícito.

# Otros
- Método de decisión: E_AC por escenario = sum(P_dc_kW de `simular_bypass_horario`) × eta_inversor; mismo método en los tres escenarios, solo cambia p_shade.
- `obtener_constantes_tecnologia` exige tecnología con mayúscula exacta ("Mono-Si", no "mono-Si").
- `tests/test_carga_proyecto_127.py` es un script con `sys.exit` al importar: rompe pytest si se recoge; ignorarlo (`--ignore`). `tests/test_validacion_vba.py` tiene 10 fallos pre-existentes no relacionados.
