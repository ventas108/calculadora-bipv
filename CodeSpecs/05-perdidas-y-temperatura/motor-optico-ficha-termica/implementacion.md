# Implementación — Motor Óptico: NOCT y γ coherentes con la ficha del panel

**Estado:** validación

## Cambios realizados

- `calculos/motor_optico_ficha.py` (nuevo): `ficha_termica`,
  `diferencias_ficha`, `texto_aviso_ficha`.
- `pages/5b_🔆_Motor_Optico.py`: auto-llenado con `ficha_termica` (γ dentro
  del rango del campo); aviso 🟠 y botón «↩️ Usar los de la ficha» con
  `on_click`.
- `pages/6_📊_Produccion.py`: aviso 🟠 antes de simular cuando el NOCT o el γ
  del Motor Óptico no son los de la ficha.
- Manual del Asistente, sección 92; contratos y registro de decisiones.

## Archivos modificados

- `bipv_python/calculos/motor_optico_ficha.py`
- `bipv_python/pages/5b_🔆_Motor_Optico.py`
- `bipv_python/pages/6_📊_Produccion.py`
- `bipv_python/tests/test_motor_optico_ficha_termica.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
