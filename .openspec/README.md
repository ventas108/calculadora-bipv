# OpenSpec en este repositorio

Las propuestas de cambios importantes se guardan en `.openspec/proposals/`.

## Cómo iniciar un caso

1. Copie [`plantilla-openspec-bipv.md`](../plantilla-openspec-bipv.md).
2. Cree una carpeta con un nombre corto dentro de `.openspec/proposals/`.
3. Complete `proposal.md`, `design.md`, `tasks.md` y `spec.yaml`.
4. Revise la propuesta antes de editar código.
5. Implemente solo las tareas aprobadas.
6. Registre la validación y archive el caso.

## Caso de referencia

La propuesta de Urabá agrivoltaica se encuentra en:

`.openspec/proposals/uraba-agrivoltaica-case/`

## Regla de seguridad

Cuando el cambio afecta cálculos de sombreado, irradiancia, región, geometría, producción o simulación, revise primero `shared/` y `server/`. La interfaz se revisa después como integración y presentación.
