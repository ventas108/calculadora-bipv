# Diseño — Recurso solar

**Estado:** archivado (reemplazado — ver `vision.md` sección 5, `react/diseno.md` y `streamlit/diseno.md`)

## Entradas

- latitud
- longitud
- azimuth
- tilt
- albedo

## Salidas

- POA mensual
- POA anual
- irradiancia horaria
- fuente de datos
- estado de validez

## Unidades

- irradiancia: W/m²
- energía solar: kWh/m²
- ángulos: grados
- albedo: valor entre 0 y 1

## Tipos de datos

- 

## Errores posibles

- 

## Dependencias

- Módulos previos: `01-datos-proyecto`
- Módulos dependientes: `03-dimensionamiento`, `04-produccion-energia`

## Criterios de aceptación

- 

## Pruebas requeridas

- 

## Nota

El módulo de producción no necesita conocer la implementación interna del recurso
solar; solo consume este contrato.
