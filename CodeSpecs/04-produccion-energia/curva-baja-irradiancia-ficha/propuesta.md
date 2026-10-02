# Propuesta — Curva de baja irradiancia de la ficha

**Estado:** validación

## Objetivo

Que Motor IV se calibre con la gráfica de baja irradiancia de cada fabricante,
muestre qué tan bien la sigue y avise cuando no puede.

## Alternativa recomendada

- **Catálogo:** columna `CurvaBajaIrradiancia` («Curva baja irradiancia (G:η
  %)») con pares `G:η` separados por punto y coma.
- **Modelo:** `parsear_curva_baja_irradiancia` y ajuste del factor de idealidad
  por mínimos cuadrados sobre todos los puntos, con R_s re-anclado. Prioridad:
  curva > dato de 200 W/m² > 97 % por defecto (solo CIGS).
- **Aviso:** `_ajuste_curva` (ficha, modelo y diferencia por punto),
  `_desv_max_curva`, y `_error_ajuste_200` si un punto queda a más de 3 puntos.
- **Motor IV:** línea en «Origen del modelo» y gráfica «Eficiencia relativa vs
  G» con los puntos de la ficha.
- **Velocidad:** malla de 13 puntos más búsqueda del borde físico, y resultado
  guardado en memoria por panel.

## Alternativas descartadas

- Columnas fijas para 200, 400 y 600 W/m²: cada fabricante publica puntos
  distintos (la teja empieza en 300).
- Ajustar también R_sh: en la Spec anterior apenas movía la baja luz.
- Interpolar la curva directamente en la producción, sin modelo: rompería la
  coherencia con la curva I-V y el resto de motores.

## Fuera de alcance

- Extraer la curva automáticamente del PDF; se escribe a mano.
- Paneles con SDM calibrado o manual.
