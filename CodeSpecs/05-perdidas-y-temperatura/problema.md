# Módulo 05 — Pérdidas y temperatura

**Estado:** completado

## Alcance de la fase

Temperatura de célula, sombreado, suciedad, IAM, mismatch y degradación.

## Problema a resolver

El Motor Óptico y el bypass podían usar una POA con el término térmico ya
aplicado, mientras Producción volvía a calcular la temperatura de célula. Esto
generaba doble conteo térmico y podía conservar resultados derivados de una POA
óptica anterior.

## Contexto

`pages/5b_🔆_Motor_Optico.py`, `calculos/mismatch_bypass.py` y
`calculos/invalidacion.py` publican e invalidan el estado que consume
Producción. Esta Spec regulariza cambios ya implementados; no autoriza nuevas
fórmulas ni cambios de interfaz.
