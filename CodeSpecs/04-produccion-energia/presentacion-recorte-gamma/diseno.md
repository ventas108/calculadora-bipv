# Diseño — 📊 Producción: recorte del inversor y γ bien presentados

**Estado:** validación

## Entradas

- `res["df_mensual"]` de `simular_produccion_anual` / `simular_produccion_iv`.
- `panel["Tk_gamma"]` (%/°C), puede ser `None`.

## Salidas

- `FORMATO_TABLA_MENSUAL: dict[str, str]` (columna → formato).
- `gamma_ficha(panel) -> float | None`.
- `texto_gamma(valor) -> str` («—» si `None`; 4 cifras significativas).
- Resultado de los dos motores con la clave `Tk_gamma_pct`.

## Tipos de datos

`dict`, `str`, `float | None`, `pandas.DataFrame`.

## Errores posibles

- Resultado guardado sin alguna columna: la página formatea solo las
  columnas presentes (sin `KeyError`).
- Ficha sin γ: la nota muestra «—».

## Dependencias

`calculos.produccion`, `calculos.produccion_iv`, `pages/6_📊_Produccion.py`.

## Criterios de aceptación

1. Toda columna de `df_mensual` (los dos motores) tiene formato en
   `FORMATO_TABLA_MENSUAL`.
2. `4927.475563` se muestra como `4,927`.
3. Los dos motores devuelven `Tk_gamma_pct` igual al γ de la ficha.
4. La nota de «↳ Solo horas calientes» muestra el γ (p. ej. `-0.214%/°C`).
5. Sin γ en la ficha: `Tk_gamma_pct` es `None` y la nota muestra «—».
6. Ningún kWh cambia (las pruebas de producción existentes siguen verdes).
7. El manual del Asistente lo explica con el ejemplo de Apartadó.
