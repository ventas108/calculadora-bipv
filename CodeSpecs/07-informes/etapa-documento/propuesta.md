# Propuesta — Etapa del documento en el Reporte

**Estado:** validación

## Objetivo

Que el diseñador elija cómo se presenta el reporte y que el cliente reciba un
aviso profesional en lugar de «BORRADOR».

## Alternativa recomendada

Selector «Etapa del documento» con cinco etapas:
- Estudio de prefactibilidad (por defecto);
- Propuesta técnica;
- Diseño conceptual;
- Versión para revisión del cliente;
- Borrador interno.

Los textos están en un módulo puro, `calculos/etapa_documento.py`. Los
avisos de las cuatro primeras etapas están escritos para el cliente y siguen
dejando claro que los valores definitivos salen de la ingeniería de detalle.

## Alternativas descartadas

- Quitar el aviso del todo: el reporte dejaría de advertir que no es la
  ingeniería de detalle.
- Texto libre: cada reporte quedaría distinto y podría prometer de más.

## Fuera de alcance

La 📋 Ficha RETIE y el Diagrama Unifilar, que conservan sus avisos técnicos
propios.
