# Propuesta — Elegir la versión de PVGIS (5.2 o 5.3) en ☀️ Recurso Solar

**Estado:** validación

## Objetivo

Que el usuario elija la versión de PVGIS, que la app diga qué base de datos y
qué años usó, y que los proyectos ya guardados den exactamente lo mismo que
antes.

## Alternativa recomendada

Aprobada por el usuario el 29-sep-2026 («si prepara la Spec con su PR para
PVGIS 5.3»).

- Selector «🛰️ Versión de PVGIS» en ☀️ Recurso Solar: 5.3 (la que descarga
  PVsyst 8) o 5.2.
- Proyecto nuevo: 5.3. Proyecto guardado sin versión: 5.2 (con el que se
  calculó). La versión se guarda con el proyecto.
- Caché de disco separada por versión; los archivos de 5.2 conservan su
  nombre actual, así que los proyectos guardados no vuelven a descargar.
- Cambiar la versión invalida el recurso solar y todo lo derivado, igual que
  cambiar las coordenadas.
- Recuadro «🛰️ Qué descargó PVGIS»: versión, base de radiación, periodo y el
  año escogido para cada mes.
- Sección del manual del Asistente con la explicación y el caso Apartadó.

## Alternativas descartadas

- Cambiar a 5.3 para todos: cambia los resultados de los proyectos guardados
  y rechaza su multi-superficie (la huella del TMY ya no coincide).
- Dejar solo 5.2: impide comparar con PVsyst 8.

## Fuera de alcance

- La incertidumbre P90 (`calculos/incertidumbre_p90.py`) usa la serie
  horaria de varios años, otro servicio de PVGIS; no cambia.
- Los scripts de `scripts/` y la simulación por lotes
  (`simulation/bipv_simulator.py`) siguen usando 5.2 cuando no reciben TMY;
  desde las páginas siempre reciben el TMY de la sesión.
