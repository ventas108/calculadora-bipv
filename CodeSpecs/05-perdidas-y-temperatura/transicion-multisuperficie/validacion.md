# Validación — Integración de la transición transaccional multi-superficie con Streamlit

**Estado:** pendiente (Spec aprobada; implementación aún no iniciada)

## Checklist de validación (a ejecutar cuando exista implementación)

- [ ] Verificar que las 7 páginas consumidoras de `multisup_*` y
  `calculos/invalidacion.py`
  (`7_💰_Financiero.py`, `12_🌿_Impacto_CO2.py`, `11_🔋_Baterias_y_Balance.py`,
  `5_🔀_Mismatch.py`, `10_📄_Reporte_PDF.py`, `20_⚡_Diagrama_Unifilar.py`,
  `4b_⚖️_Comparador_Inversores.py`, `calculos/invalidacion.py`) siguen
  funcionando SIN modificaciones cuando el adaptador físico escribe las
  claves `multisup_*` en vez del modelo simplificado.
- [ ] Verificar que con el toggle `multisup_usar_fisico` apagado (default)
  el comportamiento es idéntico al actual, sin ninguna diferencia
  observable.
- [ ] Verificar que una superficie con datos incompletos bloquea con un
  mensaje que nombra la superficie y el campo faltante, no una excepción
  cruda ni un resultado silenciosamente incompleto.
- [ ] Verificar que un `ok=False` de cualquier transición dentro del
  adaptador deja `session_state` bit a bit idéntico al estado previo
  (comparación de snapshot antes/después).
- [ ] Verificar que la vista de comparación lado a lado no escribe ninguna
  clave `multisup_*` antes de la adopción explícita.
- [ ] Ejecutar `pytest` sobre las pruebas unitarias de ambos adaptadores.
- [ ] Ejecutar las pruebas de página e integración definidas en
  `diseno.md` (punto 8).
- [ ] Ejecutar la suite de regresión de los 11 archivos ya usados en las 4
  rondas de auditoría de `transicion_multisuperficie.py`, y confirmar cero
  fallos nuevos.
- [ ] Prueba manual en al menos un proyecto real con datos completos: el
  modo físico produce un resultado plausible y la comparación contra el
  simplificado es explicable (o queda documentada la diferencia si es
  grande).
- [ ] Revisión de Copilot y revisión final de Claude en modo solo lectura,
  mismo patrón que `conservacion-optica-inversor`.
- [ ] Confirmar que no se modificó el Director, ninguna Spec ajena, ni
  contratos existentes durante la implementación.

## Resultado

No aplica todavía — no hay implementación. Este archivo describe QUÉ se
validará, no un resultado obtenido.
