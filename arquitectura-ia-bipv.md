# Arquitectura de trabajo con IA para calculadora-bipv

## 1. Propósito

Este documento consolida la gobernanza de trabajo para la calculadora BIPV de Colombia y sirve como referencia maestra para cualquier agente de IA o asistente de codificación que trabaje en este repositorio.

La intención no es generar código a la ligera ni improvisar soluciones. La intención es mantener la arquitectura existente, respetar los contratos de cálculo y asegurar que cada cambio esté apoyado por análisis real, especificación y validación.

---

## 2. Contexto del repositorio

- Frontend: `client/`
- Backend: `server/`
- Lógica compartida y contratos: `shared/`
- Documentación de despliegue: `DEPLOY_README.md`
- Stack principal: React 19, Vite, Tailwind 4, Express, tRPC, TypeScript, pnpm

Este repositorio no es un proyecto generalista. Tiene lógica de cálculo, meteorología, sombreado, irradiancia, regionalización colombiana y producción energética. Por tanto, la prioridad está en la integridad de los cálculos y no en la UI como fuente de verdad.

---

## 3. Principios fundamentales

### 3.1. No improvisar

No se debe escribir código sin entender:

- el problema real
- el módulo afectado
- la ruta de cálculo involucrada
- los contratos que debe respetar

### 3.2. Respetar frontera de capas

- `shared/` define contratos y lógica reutilizable
- `server/` orquesta cálculo y validaciones
- `client/` solo presenta datos y entrega entradas

Si un problema afecta sombreado, irradiancia, región colombiana, dimensionamiento, strings, producción o simulación, la revisión debe comenzar en shared/server antes que en UI.

### 3.3. Mantener arquitectura

Se debe preservar la estructura existente y evitar refactors innecesarios. El cambio debe ser mínimo, compatible y reversible.

### 3.4. Priorizar cálculo sobre la presentación

La UI no debe ser la fuente de verdad. Si hay un error de cálculo, no se corrige solo cambiando display, mapeo, textos o props visuales.

---

## 4. Contratos críticos que no deben romperse

Existen dos elementos particularmente sensibles en este repositorio:

- `shared/shading-engine-contract.ts`
- `shared/colombianRegions.ts`

Estos no son detalles auxiliares; son puntos de arquitectura y cálculo. Cualquier cambio en ellos debe revisarse con cuidado por su impacto en el flujo de cálculo completo.

---

## 5. Regla de trabajo obligatoria

Antes de editar código, se debe:

1. revisar el estado del repositorio
2. comprobar rama y git status
3. localizar el flujo real del cálculo afectado
4. revisar los archivos clave de `shared/`, `server/` y solo después `client/`
5. redactar la propuesta del cambio
6. implementar la corrección mínima
7. validar con el comando más pequeño y relevante
8. documentar resultados y riesgos

---

## 6. Flujo SDD / OpenSpec

Para cualquier trabajo significativo, se debe usar un flujo explícito de especificación.

### Flujo esperado

```text
/opsx:propose
/opsx:apply
/opsx:validate
/opsx:archive
```

### Estructura sugerida

```text
.openspec/
  proposals/
    <feature-or-fix>/
      proposal.md
      design.md
      tasks.md
      spec.yaml
```

### Debe incluirse en la propuesta

- objetivo
- estado actual
- módulos afectados
- restricciones
- comportamiento esperado
- ruta de validación
- riesgos de compatibilidad

---

## 7. Estructura recomendada de la propuesta

### `proposal.md`
Debe describir la intención del cambio y su contexto de negocio/técnico.

### `design.md`
Debe describir el diseño técnico, fronteras del sistema y la lógica de decisión.

### `tasks.md`
Debe listar tareas concretas con prioridad y rutas de validación.

### `spec.yaml`
Debe registrar el caso con metadatos y criterios de verificación.

---

## 8. Reglas para agentes de IA

### 8.1. Objeto del agente

El agente debe actuar como puente de implementación, no como refactorizador improvisado.

Debe:

- entender la arquitectura real
- trabajar con evidencia del código
- no inventar supuestos
- priorizar contratos y cálculo
- dejar trazabilidad del trabajo

### 8.2. Lo que no debe hacer

- no crear cambios arbitrarios
- no tocar UI antes de revisar la lógica real
- no modificar contratos compartidos sin inspección del impacto
- no asumir comportamiento sin confirmarlo en el código
- no añadir dependencias sin necesidad clara

### 8.3. Reglas de validación

Después de cualquier cambio relevante, se debe ejecutar la comprobación más pequeña y razonable:

- TypeScript check si cambió tipado
- pruebas específicas si existen
- build si se afecta compilación
- validación del proyecto si no existe comando más específico

No se debe afirmar éxito sin evidencia de ejecución.

---

## 9. Caso de referencia: Urabá agrivoltaica

El caso de la granja agrivoltaica de Urabá es una referencia de trabajo útil porque conecta:

- clima
- temperatura real
- zona geográfica
- producción estimada
- generación solar
- lógica regional colombiana
- validación del comportamiento del simulador

Documentos relacionados que deben consultarse cuando se trabaje ese caso:

- `informe_granja_fv_uraba_2026.md`
- `DIAGNOSTICO_NSERIE_URABA_TEMPERATURA_REAL.md`
- `DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md`

Este caso debe abordarse con especificación y revisión de los módulos implicados antes de cualquier modificación.

---

## 10. Orden correcto de trabajo

La secuencia recomendada es:

1. entender el problema real
2. revisar `shared/` y `server/`
3. validar el modelo de cálculo
4. proponer y documentar un ajuste
5. implementar mínimo cambio
6. validar en el entorno real
7. revisar si la UI necesita ajustes secundarios

Esta secuencia evita soluciones de pantalla que no resuelven la causa raíz.

---

## 11. Workflow recomendado para cada sesión

### Paso 1: inspección inicial

- revisar rama
- comprobar estado git
- identificar el alcance del trabajo

### Paso 2: análisis de impacto

- localizar los módulos implicados
- revisar contratos y modelos de datos
- confirmar la ruta de cálculo

### Paso 3: especificación

- preparar la propuesta OpenSpec
- dejar claro qué se va a cambiar y por qué

### Paso 4: implementación

- aplicar la corrección mínima
- mantener compatibilidad
- no introducir cambios colaterales

### Paso 5: validación

- ejecutar el comando más específico posible
- registrar resultados

### Paso 6: cierre

- archivar la evidencia
- documentar riesgos pendientes

---

## 12. Reglas de branch y operación

- usar rama específica para cada trabajo importante
- mantener nombres descriptivos
- confirmar estado antes de iniciar cambio significativo
- no mezclar cambios no relacionados

---

## 13. Qué se espera del trabajo con IA

El buen uso de IA en este repositorio no consiste en pedir “hazlo todo” ni generar código sin contexto. Consiste en:

- aclarar objetivos reales
- guiar al agente con contexto del código
- pedir análisis en capas
- exigir especificación antes de implementación
- conservar la arquitectura del proyecto
- validar antes de cerrar

---

## 14. Resumen operativo

Si se trabaja en este repositorio, la regla maestra es:

> Primero se entiende la lógica real del cálculo, luego se especifica, luego se implementa, y finalmente se valida con evidencia.

Esto aplica a cualquier caso, desde un ajuste pequeño hasta un caso complejo de simulación agrivoltaica.

---

## 15. Archivos base de referencia en este repo

- [guia-sdd-openspec-bipv.md](guia-sdd-openspec-bipv.md)
- [plantilla-openspec-bipv.md](plantilla-openspec-bipv.md)
- [.openspec/README.md](.openspec/README.md)
- [AGENTS.md](AGENTS.md)
- [.github/copilot-instructions.md](.github/copilot-instructions.md)
- [constitucion.md](constitucion.md)
- [prompt-maestro.md](prompt-maestro.md)
- [prompt-strict-mode.md](prompt-strict-mode.md)
- [.openspec/proposals/uraba-agrivoltaica-case/proposal.md](.openspec/proposals/uraba-agrivoltaica-case/proposal.md)
- [.openspec/proposals/uraba-agrivoltaica-case/design.md](.openspec/proposals/uraba-agrivoltaica-case/design.md)
- [.openspec/proposals/uraba-agrivoltaica-case/tasks.md](.openspec/proposals/uraba-agrivoltaica-case/tasks.md)
- [.openspec/proposals/uraba-agrivoltaica-case/spec.yaml](.openspec/proposals/uraba-agrivoltaica-case/spec.yaml)

---

## 16. Conclusión

Este documento sirve como referencia maestra para que el trabajo con IA se mantenga disciplinado, compatible con la lógica de cálculo del proyecto y alineado con la disciplina de especificación y validación.

Su valor radica en que convierte la IA de un generador de código sin contexto en un copiloto técnico que opera dentro de los límites correctos del repositorio.
