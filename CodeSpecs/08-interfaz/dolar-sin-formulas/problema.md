# Spec — El signo «$» no debe convertirse en fórmula

**Estado:** validación

## Alcance de la fase

Textos con formato (markdown) de `pages/` y el mensaje final de 💰 Financiero
(`calculos/lectura_financiera.mensaje_resumen_financiero`).

## Problema a resolver

Streamlit toma el texto entre dos «$» como una fórmula LaTeX. Tras completar el
mensaje final de Financiero (#74) el recuadro salía «(48.76MCOP)|TIR:∗∗16.8…» en
cursiva matemática. El mismo defecto, de antes, en el cuadro «CAPEX bruto →
neto», la tabla «Detalle Ley 1715», la tabla de mercado de carbono de
🌿 Impacto CO₂ y el resumen de 💼 Presupuesto.

## Contexto

En markdown de Streamlit «\$» muestra un «$» normal. Las métricas (`st.metric`)
y las tablas de datos no usan markdown y no cambian.
