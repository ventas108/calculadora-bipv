# Diseño — Tensión máxima de sistema del módulo en el límite del Voc

**Estado:** validación

## Entradas

- Panel: `V_sistema_max` (V). En el Excel, columna `VsistemaMaxV`; sin dato,
  el de `datos/tecnologias_bipv.py` para el mismo modelo.
- Inversor: `Vdc_max` (V).

## Salidas

`limite_voc(panel, inversor)` → `{limite_v, origen, vdc_inversor_v,
v_sistema_modulo_v}`; `origen` = `"modulo"` si el módulo es menor,
`"inversor"` si no (empate = inversor), `None` sin datos.

- `evaluar_compatibilidad_string`: compara con `limite_v`; agrega
  `limite_voc_V` y `limite_voc_origen`; mensaje «Voc en frío X V > tensión
  máxima del módulo Y V».
- `optimizar_n_serie`: el semáforo 1 usa `limite_v`.
- `curva_electrica_temperatura`: `vdc_max` = `limite_v` y
  `limite_voc_origen`; la interpretación nombra el límite que manda.
- Comparador: filtro y margen con `limite_v`; motivo «máx. del módulo».
- Vista 3D: `rango_n_serie` y la comprobación por grupo («Voc en frío ≤
  tensión máx. del módulo» cuando manda el módulo).
- `margen_voc(voc, inv, panel=None)`: margen frente a `limite_v`, con origen.
- RETIE: `construir_config_retie(v_sistema_modulo_v=…)`; la validación usa
  el menor.

## Tipos de datos

`float | None`, `dict`.

## Errores posibles

- Panel sin el dato: todo queda como antes (límite del inversor).
- Inversor sin Vdc: sigue siendo ficha incompleta (no se evalúa solo con el
  módulo).

## Dependencias

Ninguna nueva.

## Criterios de aceptación

1. ASP-ST1-T40 + SG8.0RT: con T mín 0 °C, 8 en serie es incompatible por el
   módulo (1.002,5 V > 1.000 V); con T mín 5 °C, 8 en serie queda en alerta
   (987,6 V, margen 1,2 % < 7,5 %) y 7 en serie (864,1 V) queda OK.
2. Panel sin dato: resultados idénticos a los de antes.
3. Comparador, Vista 3D, RETIE y margen del reporte usan el mismo límite.
4. El catálogo lee `VsistemaMaxV` y, sin ella, el respaldo de la familia ASP.
5. El manual del Asistente explica la regla y la corrida de Teusaquillo.
