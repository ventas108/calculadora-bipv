# Spec — Manual: corrida completa de un proyecto BIPV de varias superficies

**Estado:** validación

## Alcance de la fase

Manual del Asistente (`datos/base_conocimiento_asistente.md`), secciones 2,
108 y 109.

## Problema a resolver

El usuario (1-oct-2026): «haz también lo mismo para la corrida para la
simulación de Teusaquillo, verifica que no hayan incoherencias». La revisión
con las funciones de la app y la ficha oficial del ASP-ST1-T40 encontró:

- inversor de 15 kW para 8,36 kWp (DC/AC 0,56);
- techo bajo el MPPT activo;
- falta de MPPT para el techo;
- 8 en serie por encima de los 1.000 V del módulo;
- fusible de string máximo de 2 A;
- NOCT ausente de la ficha;
- área de 80,6 m² que la app bloquea.

El Asistente no tenía el orden de un proyecto de varias superficies ni estas
trampas.

## Contexto

La sección 107 cubre la granja de Urabá. La sección 75 tiene los valores de
energía de Teusaquillo. La regla del límite del módulo es la Spec
`03/tension-maxima-modulo`.
