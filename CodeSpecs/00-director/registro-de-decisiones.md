# Registro de decisiones

| Fecha | Decisión | Motivo | Módulo(s) afectados |
|---|---|---|---|
| 2026-09-14 | Adoptar arquitectura híbrida: director central + Specs modulares en `CodeSpecs/` | Evitar Specs gigantes y descoordinación entre módulos; permitir trabajar con Claude y Copilot sin duplicar esfuerzos; ganar trazabilidad y validación módulo por módulo | Todos |
| 2026-09-15 | Aprobar `problema.md`, `propuesta.md` y `diseno.md` de `01-datos-proyecto`; corregir regla de precedencia de tarifa por ciudad (no sobreescribir un valor editado manualmente al cambiar de ciudad) | Los valores del catálogo son una aproximación regional; el usuario los corrige con su factura real y esa corrección se perdía silenciosamente al cambiar de ciudad | `01-datos-proyecto`, `06-analisis-financiero` |
| 2026-09-15 | Cerrar `01-datos-proyecto` como `completado`: implementación desplegada en producción y verificación funcional confirmada (valor manual conservado, aviso correcto, botón de aplicar sugerencia funcional) | Primera Spec vertical llevada de principio a fin por el ciclo SDD completo (problema → propuesta → diseño → aprobación → tareas → implementación por Claude Code → validación) | `01-datos-proyecto` |
