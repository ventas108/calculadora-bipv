# CodeSpecs — Calculadora BIPV

Arquitectura híbrida de trabajo: **director central + Specs modulares**.

## Estructura

```text
CodeSpecs/
├── 00-director/                 # Gobierno del proceso: visión, arquitectura, contratos, dependencias, decisiones
├── 01-datos-proyecto/
├── 02-recurso-solar/
├── 03-dimensionamiento/
├── 04-produccion-energia/
├── 05-perdidas-y-temperatura/
├── 06-analisis-financiero/
├── 07-informes/
├── 08-interfaz/
└── 09-despliegue/
```

Cada módulo sigue el mismo ciclo:

```text
problema.md -> propuesta.md -> diseno.md -> tareas.md -> implementacion.md -> validacion.md -> archivo/
```

## Empezar aquí

1. Lee [00-director/vision.md](00-director/vision.md) para la visión general y el orden de fases.
2. Revisa [00-director/mapa-dependencias.md](00-director/mapa-dependencias.md) antes de abrir un módulo.
3. Toda Spec nueva dentro de un módulo arranca en `problema.md` con estado `idea`.
4. Los contratos aprobados se resumen en [00-director/contratos-entre-modulos.md](00-director/contratos-entre-modulos.md).
5. Toda decisión de arquitectura se anota en [00-director/registro-de-decisiones.md](00-director/registro-de-decisiones.md).

## Regla de Specs verticales

No se crean Specs que abarquen "toda la calculadora". Cada Spec debe ser vertical y
verificable, atravesando: entrada -> cálculo -> API/estado -> interfaz -> validación.
