# Tareas — Proveedor de sombra opcional `pybdshadow`

**Estado:** propuesta — NO aprobada. Esta lista es orientativa; no debe ejecutarse sin
aprobación explícita del Director sobre `problema.md`, `propuesta.md` y `diseno.md`.

1. Validar con el Director si esta Spec tiene prioridad frente al bloqueo real de
   `transicion-multisuperficie` (sombra por superficie inclinada) — si la respuesta es no,
   archivar esta Spec sin implementar.
2. Si se aprueba: crear `calculos/proveedores_sombra/` con
   `pybdshadow_horizontal.py` y pruebas unitarias propias (rechazo de superficies no
   horizontales, comparación contra un caso de `sombras_3d.py` con malla 3D real, manejo de
   `pybdshadow` ausente).
3. Documentar `pybdshadow` como dependencia opcional (no en `requirements.txt` base) y resolver
   de antemano el conflicto con `keplergl`/Python 3.14 documentado en el informe de
   verificación (pin de versión, dependencia alternativa, o parche upstream).
4. Prueba de integración: un proyecto real con superficie horizontal sin malla 3D, comparando el
   resultado de este proveedor contra una malla 3D de referencia del mismo sitio si existe.
5. Solo entonces: diseñar la UI de selección de proveedor (fuera de alcance de esta Spec hasta
   que los puntos 1-4 estén resueltos).
