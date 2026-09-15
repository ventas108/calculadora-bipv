# Estudio del Agente SDD

## Propósito

El Agente SDD es un agente de preparación y control dentro de una arquitectura híbrida. Su función es verificar que una Spec esté suficientemente definida antes de convertirla en tareas y comenzar la implementación.

No es un ejecutor autónomo de cambios.

## Posición en el flujo

```text
problema
  -> propuesta
  -> diseño
  -> aprobación humana
  -> agente SDD
  -> tareas
  -> implementación
  -> validación
  -> completado
  -> archivado
```

La auditoría determinista puede ejecutarse antes de la aprobación para detectar bloqueos. La preparación con Claude solo debe ejecutarse cuando la Spec esté completa y aprobada.

## Funciones del agente

- Verificar que existan los seis documentos SDD:
  - `problema.md`
  - `propuesta.md`
  - `diseno.md`
  - `tareas.md`
  - `implementacion.md`
  - `validacion.md`
- Comprobar entradas, salidas, tipos de datos y errores posibles.
- Revisar dependencias entre módulos.
- Comprobar criterios de aceptación.
- Detectar documentos o secciones incompletas.
- Identificar capas y archivos probablemente afectados.
- Detectar riesgos de integración.
- Revisar posibles contradicciones con el director central.
- Extraer comandos y pruebas de validación.
- Preparar contexto estructurado para Claude, Copilot u otro agente implementador.
- Detener el flujo cuando faltan datos o existe una incompatibilidad.
- Para `09-despliegue`, revisar migraciones, variables de entorno, artefactos y rollback.

## Contrato de estricto cumplimiento

El agente puede:

- leer `CodeSpecs/`;
- auditar documentos y estados;
- analizar contratos y dependencias;
- producir informes;
- proponer tareas;
- señalar riesgos y validaciones faltantes;
- bloquear el avance.

El agente no puede:

- modificar código;
- modificar Specs;
- cambiar contratos entre módulos;
- tomar decisiones arquitectónicas autónomas;
- aprobar una Spec;
- cambiar estados de una Spec;
- ejecutar validaciones reales en sustitución del equipo;
- marcar una Spec como válida o completada.

## Dos niveles de control

### 1. Auditoría determinista

Comando:

```bash
pnpm exec tsx scripts/sdd-agent.ts --spec CodeSpecs/01-datos-proyecto
```

Comprueba hechos objetivos: archivos existentes, secciones, contenido pendiente,
estado de la Spec, requisitos técnicos, capas afectadas, archivos detectables,
riesgos y comandos de validación.

### 2. Preparación con Claude

Solo procede cuando la auditoría indique que la Spec está completa y aprobada:

```bash
ANTHROPIC_API_KEY=... pnpm exec tsx scripts/sdd-agent.ts \
  --spec CodeSpecs/01-datos-proyecto --review
```

Claude recibe la Spec junto con el contexto del director central y devuelve un
informe organizado con hallazgos, contratos, dependencias, tareas propuestas,
archivos afectados, riesgos y validaciones faltantes.

La respuesta de Claude no constituye aprobación ni autorización automática.

## Flujo de responsabilidades

```text
Usuario / equipo
  define y aprueba la Spec

Auditoría determinista
  comprueba condiciones objetivas

Agente SDD + Claude
  prepara el contexto y propone tareas

Claude / Copilot / desarrollador
  implementa los cambios autorizados

Pruebas y comandos reales
  validan el resultado

Usuario / equipo
  revisa y acepta o rechaza
```

## Cuándo es especialmente útil

- Cuando una Spec atraviesa cálculo, API, estado e interfaz.
- Cuando cambia contratos entre módulos.
- Cuando existen dependencias en cadena.
- Cuando participan varias personas o agentes.
- Cuando el cambio puede afectar producción.
- Cuando se necesita trazabilidad antes de modificar código.

## Cuándo puede omitirse

En cambios pequeños, aislados y de bajo riesgo puede bastar una revisión local de
Copilot o del desarrollador. Aun así, no se debe omitir la validación técnica
correspondiente.

## Regla de estudio

El agente SDD no implementa. Su papel es:

```text
preparar + verificar + ordenar + bloquear cuando sea necesario
```

La implementación pertenece al agente o persona autorizada, y la validación real
siempre permanece como paso obligatorio.
