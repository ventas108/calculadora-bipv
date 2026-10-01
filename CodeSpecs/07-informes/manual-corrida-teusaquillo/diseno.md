# Diseño — Manual: corrida completa de un proyecto BIPV de varias superficies

**Estado:** validación

## Entradas

Hallazgos verificados con `validar_diseno_electrico`,
`evaluar_compatibilidad_string`, `evaluar_relacion_dc_ac` y la ficha
`Ficha_Tec_Vidrios_FV_SolTech_1200x600_T105.pdf`.

## Salidas

Secciones 108 y 109 antes del pie del manual; remisión en la sección 2.

## Tipos de datos

Texto Markdown.

## Errores posibles

Ninguno de cálculo: solo texto.

## Dependencias

Spec `03/tension-maxima-modulo` (el aviso 🔒 y la comprobación «Voc en frío
≤ tensión máx. del módulo» que nombra el manual).

## Criterios de aceptación

1. La 108 tiene el orden completo de las páginas.
2. La 108 explica las trampas con sus números.
3. La 109 explica la regla, dónde aparece y que sin el dato nada cambia.
4. La sección 2 remite a la 108. Sin «PVsyst».
