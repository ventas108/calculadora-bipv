# Tareas — Conservación óptica al adoptar inversor

**Estado:** completado

- [x] Confirmar con Claude y Copilot la clasificación completa de claves ópticas
   y downstream contra los escritores/consumidores reales.
- [x] Definir el conjunto central del Motor Óptico en
   `calculos/invalidacion.py` sin cambiar la invalidación general por
   POA/geometría.
- [x] Implementar la función idempotente de invalidación por cambio de inversor.
- [x] Sustituir la limpieza local en el comparador por la función central.
- [x] Añadir pruebas unitarias de conjuntos, conservación, eliminación e
   idempotencia.
- [x] Añadir pruebas de página e integración con la selección de POA en
   Producción.
- [x] Ejecutar suites focalizadas y vecinas: `103 passed`.
- [x] Revisar el diff final con Claude en modo solo lectura: veredicto
   `APROBADA PARA INTEGRAR`, sin hallazgos bloqueantes.
- [x] Actualizar Director, asistente y documentos de auditoría después de
   validar el comportamiento real.
