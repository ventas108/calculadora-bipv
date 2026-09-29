# Implementación — La app no nombra el software de simulación de referencia

**Estado:** validación

## Cambios realizados

- Nuevo `calculos/texto_referencia.py`.
- Manual del Asistente: 150 menciones reemplazadas (0 quedan).
- 28 líneas de texto en páginas (☀️ Recurso Solar, 🔀 Mismatch, 📊 Producción,
  💰 Financiero) y cálculos (`produccion.py`, `asistente.py`).
- Catálogos filtrados al leerlos; Asistente con regla 6, regla 2 ampliada y
  respuesta filtrada.

## Archivos modificados

- `bipv_python/calculos/texto_referencia.py`
- `bipv_python/calculos/asistente.py`
- `bipv_python/calculos/produccion.py`
- `bipv_python/datos/catalogo_paneles_excel.py`
- `bipv_python/datos/catalogo_inversores_excel.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `bipv_python/pages/2_☀️_Recurso_Solar.py`
- `bipv_python/pages/5_🔀_Mismatch.py`
- `bipv_python/pages/6_📊_Produccion.py`
- `bipv_python/pages/7_💰_Financiero.py`
- `bipv_python/tests/test_sin_nombre_referencia.py`
- `CodeSpecs/00-director/registro-de-decisiones.md`
- `bipv_python/tests/test_consistencia_sdm_entre_modulos.py`
