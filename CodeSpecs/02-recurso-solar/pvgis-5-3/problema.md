# Spec — Elegir la versión de PVGIS (5.2 o 5.3) en ☀️ Recurso Solar

**Estado:** validación

## Alcance de la fase

Descarga del año típico (TMY) de PVGIS en ☀️ Recurso Solar
(`calculos/solar.py::obtener_tmy_pvgis`), su caché de disco, la detección de
cambios que invalida el recurso solar y la carga de proyectos guardados.

## Problema a resolver

La app descarga siempre PVGIS 5.2. PVsyst 8 descarga PVGIS 5.3. En la
comparación del proyecto agrivoltaico de Apartadó (29-sep-2026), con las
mismas coordenadas (7.8830 / −76.6259), la app obtuvo GHI 1,606 kWh/m² y
PVsyst 1,683 kWh/m² (−4.6 %). La verificación cruzada con PVWatts (NSRDB)
dio 1,707 kWh/m² de POA frontal contra 1,716 de PVsyst: la diferencia viene
de la base de datos, no del cálculo. Sin poder elegir la versión, ninguna
comparación con PVsyst puede aislar el cálculo del clima.

Además, la app no muestra qué base de radiación ni qué años escogió PVGIS
para cada mes, que es justamente lo que explica por qué dos años típicos del
mismo sitio tienen repartos mensuales distintos.

## Contexto

- Los dos servicios (`/api/v5_2/tmy` y `/api/v5_3/tmy`) reciben los mismos
  parámetros y devuelven el mismo JSON (`outputs.tmy_hourly`,
  `outputs.months_selected`, `inputs.meteo_data`).
- Los proyectos guardados no traen versión: se calcularon con 5.2. Su
  multi-superficie restaurada verifica la huella del TMY, así que deben seguir
  usando 5.2 para no cambiar sus resultados.
