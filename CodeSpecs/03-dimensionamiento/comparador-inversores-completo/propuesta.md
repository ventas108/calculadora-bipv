# Propuesta — Comparador de Inversores completo

**Estado:** validación

## Objetivo

Que el comparador diga, para cada inversor del catálogo, cuál es su mejor
configuración para el proyecto y que adoptarla deje 📐 Dimensionamiento
idéntico.

## Alternativa recomendada

Aprobada por el usuario el 1-oct-2026 («Estoy de acuerdo, prepárala»).

- `filtrar_inversores_compatibles(..., T_extremo)`: Vmp a la temperatura
  extrema, margen de Voc y columna `ficha`; una ficha 🔴 descarta.
- `mejor_n_por_inversor`: para cada inversor el N con reparto exacto, margen
  de Voc ≥ 3 % y string más largo; unidades por entradas o por DC/AC ≤ 1,3.
- `comparar_mejores`: energía con recorte por configuración (escalada por los
  módulos usados) y financiero solo con precio (cotizado en la página o del
  catálogo).
- `estado_adopcion`: inversor, N, strings por MPPT, total de cadenas (con la
  firma de `resolver_n_strings_tracker`), unidades y reparto.
- Página: T. de celda extrema, sección «🎯 Mejor configuración para cada
  inversor» con precios editables y adopción completa en las dos secciones.
- Manual del Asistente, sección 104.

## Alternativas descartadas

- Escribir los precios en el Excel del catálogo desde el comparador: el
  catálogo vive en el servidor y se edita en 🔌 Catálogo Inversores.
- Optimizar también el panel: lo hace 🧩 Comparador de Paneles.

## Fuera de alcance

- Lado AC del punto de conexión (`verificar_compatibilidad_ac`).
- Cable y bloques de granja por inversor (los calcula 🌾 Granja FV).
