# Propuesta — 📊 Producción: recorte del inversor y γ bien presentados

**Estado:** validación

## Objetivo

Que la tabla mensual y la tabla de balance muestren el recorte y el γ con el
mismo formato y dato que el resto de la página, sin cambiar ningún cálculo.

## Alternativa recomendada

Aprobada por el usuario el 29-sep-2026 («si prepara la Spec con su PR»).

- `calculos/formato_produccion.py` (nuevo, sin Streamlit):
  `FORMATO_TABLA_MENSUAL` con el formato de **todas** las columnas de
  `df_mensual`, `gamma_ficha(panel)` y `texto_gamma(valor)`.
- La página 6 usa `FORMATO_TABLA_MENSUAL` (solo con las columnas presentes,
  para resultados guardados antiguos).
- Los dos motores devuelven `Tk_gamma_pct` = γ de la ficha (%/°C) o `None`;
  la nota muestra `texto_gamma` («—» solo si la ficha no lo trae).
- Una prueba falla si una columna nueva de `df_mensual` queda sin formato.
- Manual del Asistente: sección 89, con cómo leer el recorte y qué hacer.

## Alternativas descartadas

- Redondear el recorte dentro del motor: cambiaría los datos que usan otros
  módulos (Reporte, Financiero); el formato es de presentación.
- Mostrar el γ efectivo del modelo SDM: es una cantidad interna distinta del
  dato de ficha que ve el usuario en «Diagnóstico BIPV».

## Fuera de alcance

- Cualquier cambio en el cálculo del recorte, la temperatura o el PR.
