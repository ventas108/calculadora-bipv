# Implementación — Curva de baja irradiancia de la ficha

**Estado:** validación

## Cambios realizados

- `parsear_curva_baja_irradiancia`.
- Ajuste por mínimos cuadrados con sección áurea, y el resultado por punto.
- `_con_bordes`: malla de 13 puntos más el borde de la zona física (10 pasos
  de bisección), para el ajuste por curva y para el de un solo punto.
  Resultados del 70N y del 90N sin cambio.
- `estimar_sdm_desde_ficha` guarda el resultado en memoria por panel (entrega
  una copia). Antes: ~12 s por panel en cada recarga. Ahora: 2,5 a 6 s la
  primera vez y después inmediato.
- Catálogo: `curva_baja_irradiancia` desde `CurvaBajaIrradiancia`; la columna
  se crea sola al guardar.
- Motor IV: línea de origen «curva» y gráfica «Eficiencia relativa vs G».

## Archivos modificados

- `bipv_python/calculos/modelo_iv.py`
- `bipv_python/datos/catalogo_paneles_excel.py`
- `bipv_python/pages/14_📋_Catálogo_Paneles.py`
- `bipv_python/pages/3_🔬_Motor_IV.py`
- `bipv_python/tests/test_curva_baja_irradiancia.py`
- `bipv_python/tests/test_consistencia_sdm_entre_modulos.py`
- `bipv_python/datos/base_conocimiento_asistente.md` (sección 114)
- `CodeSpecs/00-director/registro-de-decisiones.md`
