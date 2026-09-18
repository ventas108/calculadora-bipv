# Revisión final del diff — Fase 4 (k_bipv / poa_sin_termico)

**Alcance:** solo 3 archivos modificados (`ejecutor_escenarios.py`, `mismatch_bypass.py`,
`5_🔀_Mismatch.py`) + 1 archivo de test nuevo (`test_mismatch_bypass_termico.py`, sin
trackear). El resto de `??` en `git status` son archivos preexistentes no relacionados
con esta tarea (`.openspec/`, `AGENTS.md`, `.venv/`, etc.) — ninguno tocado.

## Verificación punto por punto

| Check | Estado |
|---|---|
| `simular_bypass_horario()` usa `temperatura_celda_noct()` | ✅ Reemplaza el cálculo inline `T_amb + (NOCT-20)/800*G_eff` por `temperatura_celda_noct(G_eff, T_amb, NOCT=NOCT_val, k_bipv=k_bipv)` |
| `k_bipv` se propaga Mismatch → 3 escenarios | ✅ La página fija `_k_bipv_bp` y lo pasa a `simular_bypass_horario()` y a `ejecutar_escenarios(k_bipv=...)`. Dentro de `ejecutor_escenarios.py`, `k_bipv` entra al dict `comunes` y los 3 llamados a `_simular_escenario` (`referencia`, `actual`, `optimizada`) lo reciben vía `**comunes` |
| Motor Óptico usa `poa_sin_termico_df` | ✅ La página ahora lee `st.session_state.get("poa_sin_termico_df")` en vez de `poa_efectiva_df` cuando el motor está activo |
| Fallback a `poa_efectiva_df` explícito | ✅ Si `poa_sin_termico_df` es `None`, cae a `poa_efectiva_df` y el `poa_src` lo etiqueta explícitamente como *"sin poa_sin_termico_df disponible"* — no es un fallback silencioso |
| Compatibilidad `k_bipv=1.0` por defecto | ✅ Default `1.0` en `simular_bypass_horario()` y en `ejecutar_escenarios()`; el test `test_comportamiento_legado_sin_motor_optico_k_bipv_uno_es_compatible` y `test_ejecutar_escenarios_sin_k_bipv_usa_default_uno_compatibilidad` lo cubren explícitamente |
| Sin refactors/cambios no relacionados | ✅ Los diffs son quirúrgicos: import nuevo, parámetro nuevo, docstrings actualizados, una línea de cálculo reemplazada, propagación del parámetro. No hay renombrados, reordenamientos ni limpieza colateral |

## Estado final

Working tree limpio de sorpresas — los 3 archivos modificados están dentro del alcance
declarado, y el test nuevo cubre las 4 aristas (NOCT vía `temperatura_celda_noct`,
diferencia flujo correcto vs. doble-conteo con `poa_efectiva`, compatibilidad legada
`k_bipv=1.0`, y propagación end-to-end en `ejecutar_escenarios`). No se hizo ningún
commit ni push.
