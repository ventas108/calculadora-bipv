# Visión técnica — Calculadora BIPV

## Propósito

Coordinar la evolución de la Calculadora BIPV mediante una arquitectura híbrida:
un **director central** que gobierna contratos, dependencias y validación global,
y **módulos SDD independientes** que conservan su propio ciclo:

```text
Problema -> Propuesta -> Diseño -> Aprobación -> Agente de preparación -> Tareas -> Implementación -> Validación -> Completado -> Archivo
```

## Principios

1. El director no calcula energía ni modifica módulos directamente; gobierna el proceso.
2. Cada módulo es probable de forma aislada, pero declara un contrato explícito
   (entradas, salidas, unidades, tipos de datos, errores posibles, dependencias).
3. No se crean Specs gigantes (p. ej. "rediseñar toda la calculadora"). Se crean
   **Specs verticales y verificables** que atraviesan: entrada -> cálculo -> API/estado
   -> interfaz -> validación.
4. Toda decisión de arquitectura se registra en [registro-de-decisiones.md](registro-de-decisiones.md).
5. Una Spec no se marca `completado` sin validación del módulo y validación de integración.
6. El agente de preparación verifica y ordena el trabajo, pero no modifica código,
   contratos o estados; la aprobación humana y las validaciones reales son obligatorias.

## Estados de una Spec

```text
idea -> propuesta -> diseño -> aprobado -> en implementación -> validación -> completado -> archivado
```

## Orden de ejecución de fases

1. `01-datos-proyecto`
2. `02-recurso-solar`
3. `03-dimensionamiento`
4. `04-produccion-energia`
5. `05-perdidas-y-temperatura`
6. `06-analisis-financiero`
7. `07-informes`
8. `08-interfaz`
9. `09-despliegue`

## Roles

- **Claude (terminal)**: exploración profunda, especificación amplia, implementación
  multi-capa, validación con comandos, revisión de diffs.
- **Copilot (VS Code)**: cambios locales, explicación de código, tareas pequeñas,
  revisión rápida.
- Regla: una herramienta debe terminar su edición antes de que la otra edite el mismo archivo.
