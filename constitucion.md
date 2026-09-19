# Constitución técnica de calculadora-bipv

## Propósito

Esta constitución define la arquitectura base del proyecto y las reglas no negociables para cualquier trabajo de desarrollo asistido por IA, incluyendo Claude Code, OpenSpec y agentes de VS Code.

La intención principal no es “programar más rápido”, sino programar con disciplina, reduciendo ambigüedad, evitando improvisación técnica y asegurando estabilidad de arquitectura.

## Principios fundamentales

### 1. No improvisación técnica

Cualquier cambio debe estar respaldado por:
- una intención clara,
- un alcance definido,
- una revisión del estado actual del repositorio,
- una validación del impacto real sobre los módulos implicados.

No se aceptan cambios “a ciegas” ni correcciones por ensayo y error sin entender el flujo de cálculo y la arquitectura existente.

### 2. El contrato define la integridad

El proyecto debe respetar sus contratos y fronteras:
- frontend y backend deben mantenerse separados por responsabilidad,
- la lógica compartida en `shared/` es fuente de verdad para reglas transversales,
- los contratos y API interfaces no deben romperse sin justificación explícita,
- los cambios de lógica no deben ocultarse detrás de ajustes visuales o de presentación.

### 3. SDD como guardián arquitectónico

El desarrollo debe operar bajo una especificación previa que actúe como guardián de calidad.

El flujo correcto es:

```text
/opsx:propose
/opsx:apply
/opsx:validate
/opsx:archive
```

Cada etapa debe dejar evidencia escrita en la especificación:
- objetivo,
- alcance,
- restricciones,
- módulos impactados,
- decisiones técnicas,
- por qué se decidió así,
- riesgos y compatibilidad.

### 4. La especificación es un entregable

La especificación no es documentación opcional. Es parte del producto.

Debe incluir:
- propósito del cambio,
- estado actual del código,
- alcance delimitado,
- reglas de negocio,
- restricciones técnicas,
- mensajes de compatibilidad,
- justificación técnica del diseño,
- plan de validación.

### 5. Reducir ambigüedad antes de escribir código

La IA debe trabajar con el proyecto como si fuera un sistema con reglas de arquitectura predefinidas. No se debe aceptar:
- cambios sin alcance,
- rutas ambiguas,
- decisiones sin justificación,
- correcciones que ignoren módulos de cálculo reales.

La reducción de ambigüedad es un mecanismo de calidad y de ahorro de costo técnico.

### 6. Calidad arquitectónica antes que velocidad

La productividad de la IA se maximiza cuando tiene reglas claras. No se trata de “hacer más cosas”, sino de hacer las cosas correctas con un plan explícito.

Los agentes deben:
- entender primero el estado del repo,
- identificar el objetivo probable,
- definir plan de trabajo lógico,
- respetar los contratos y capas del sistema,
- ejecutar la implementación solo cuando la especificación lo permita.

## Reglas de ejecución para agentes

### Regla 1: obligado revisión del estado actual

Antes de cambiar cualquier archivo, el agente debe revisar:
- rama actual,
- git status,
- módulos implicados,
- código relevante en `shared/`, `server/`, `client/` y demás capas afectadas.

### Regla 2: no romper infraestructura existente

Los agentes deben preservar:
- arquitectura del proyecto,
- nombres y convenciones,
- contratos de datos y API,
- validaciones ya implementadas,
- reglas de negocio previas.

### Regla 3: cálculo y backend tienen prioridad

Si el cambio afecta:
- sombreado,
- irradiancia,
- geometría,
- región colombiana,
- producción,
- baterías,
- dimensionamiento,
- simulación,

entonces deben revisarse primero `shared/` y `server/` antes de cualquier ajuste visual o de frontend.

### Regla 4: la especificación guía la ejecución

Los agentes no deben ejecutar código arbitrario.

Todo cambio debe estar respaldado por:
- objetivo,
- alcance,
- restricciones,
- evidencia técnica,
- validación concreta.

### Regla 5: decisiones y “por qué” quedan escritos

Los agentes deben documentar, dentro de la especificación, no solo lo que se va a hacer, sino por qué:
- qué problema real existe,
- qué módulos lo causan,
- qué compatibilidad se debe preservar,
- qué riesgos existen,
- por qué la solución elegida es la menos invasiva.

### Regla 6: la IA debe actuar como copiloto, no como improvisador

El papel de la IA es:
- estructurar el plan,
- mantener el contexto del proyecto,
- sugerir paths seguros,
- anotar reglas y decisiones,
- implementar solo dentro del marco especificado.

No debe producir cambios que:
- ignoren el backend,
- rompan interfaces,
- salten validaciones,
- oculten errores lógicos detrás de UI.

## Reglas de integración con Claude Code y OpenSpec

### Flujo esperado

```text
1. Revisión del estado actual del repo.
2. Identificación del problema real y del flujo implicado.
3. Definición del alcance, limitaciones y objetivos.
4. /opsx:propose
5. /opsx:apply
6. /opsx:validate
7. /opsx:archive
```

### Output mínimo requerido

Cada propuesta debe contener al menos:
- objetivo
- estado actual
- módulos afectados
- restricciones
- decisiones técnicas
- riesgos y compatibilidad
- estrategia de validación

### Criterio de aceptación

Un cambio es aceptable solo si:
- respeta la arquitectura actual,
- no rompe interfaces o contratos,
- se justifica en la especificación,
- queda validado por una comprobación técnica relevante,
- no introduce ambigüedad ni improvisación.

## Finalidad

El objetivo de esta constitución es asegurar que la IA funcione como copiloto disciplinado y no como generador impulsivo de código. La especificación es la capa que disciplina la ejecución, protege la calidad arquitectónica y favorece la colaboración entre producto y desarrollo.
