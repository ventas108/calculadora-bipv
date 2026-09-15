# Agente de preparación y control SDD

## Contrato de estricto cumplimiento

El agente es un **gatekeeper de preparación y control**, no un ejecutor autónomo.
Su posición en el flujo es:

```text
problema -> propuesta -> diseño -> aprobación -> agente de preparación -> tareas -> implementación -> validación -> completado -> archivado
```

Puede verificar Specs, revisar entradas, salidas, contratos, criterios de
aceptación, dependencias, decisiones del director, capas y archivos afectados;
proponer tareas, riesgos y validaciones; y detener el flujo si faltan datos o
existe una incompatibilidad. Para `09-despliegue` también identifica migraciones,
variables de entorno, artefactos y rollback.

No puede modificar código o Specs, cambiar contratos, aprobar estados, decidir
arquitectura, ejecutar validaciones reales ni marcar una Spec como válida. Claude
solo interpreta y organiza el contexto; las comprobaciones objetivas son
deterministas y la aprobación humana permanece obligatoria.

## Disparador VS Code

La intervención se solicita mediante las tareas de `.vscode/tasks.json`; el
agente no observa archivos ni se activa silenciosamente al guardar. En VS Code,
abre **Tasks: Run Task** y selecciona:

- **SDD: auditar Spec (alertas tempranas)** para ejecutar la auditoría y mostrar
  bloqueos o riesgos. Devuelve código `2` si la Spec no está preparada para
  revisión.
- **SDD: preparar revisión Claude (solo aprobada)** para solicitar la preparación
  con Claude. Solo continúa con una Spec completa y en estado `aprobado`, y
  requiere `ANTHROPIC_API_KEY`.

Las alertas usan los prefijos `SDD ALERTA [BLOQUEO]`, `SDD ALERTA [AVANCE]` y
`SDD ALERTA [RIESGO]`. Ninguna tarea modifica archivos, cambia estados o aprueba
la Spec.

El agente se ejecuta con:

```bash
pnpm exec tsx scripts/sdd-agent.ts --spec CodeSpecs/01-datos-proyecto
```

La auditoría determinista comprueba los seis documentos, sus secciones requeridas,
entradas/salidas/contratos, dependencias, criterios, archivos afectados y
validaciones. Una Spec incompleta queda bloqueada y el informe incluye motivos,
capas afectadas, riesgos y comandos de validación para conservar trazabilidad.

Cuando la Spec está completa y en estado `aprobado`, la preparación de Claude se
solicita explícitamente:

```bash
ANTHROPIC_API_KEY=... pnpm exec tsx scripts/sdd-agent.ts \
  --spec CodeSpecs/01-datos-proyecto --review
```

El agente solo devuelve observaciones, preguntas y comprobaciones faltantes. No
modifica archivos, no cambia estados y no aprueba Specs. La aprobación humana se
mantiene como condición independiente para avanzar a implementación.