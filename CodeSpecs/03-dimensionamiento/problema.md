# Módulo 03 — Dimensionamiento eléctrico

**Estado:** completado

## Alcance de la fase

Módulos, strings, inversores, tensión, corriente, límites eléctricos y compatibilidad.

## Problema a resolver

Los consumidores aguas abajo podían combinar la selección viva de panel/inversor o
de strings por tracker con un número de módulos en serie confirmado para otra
configuración. También debía evitarse que fichas de inversor incompletas produjeran
recomendaciones eléctricas engañosas.

## Contexto

La página `bipv_python/pages/4_📐_Dimensionamiento.py` y la lógica pura de
`bipv_python/calculos/dimensionamiento.py` alimentan Producción, Unifilar, RETIE,
finanzas y reportes. Esta Spec regulariza retrospectivamente cambios ya integrados
y desplegados; no autoriza un refactor adicional.
