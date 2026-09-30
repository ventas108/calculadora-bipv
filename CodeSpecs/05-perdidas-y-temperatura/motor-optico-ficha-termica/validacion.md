# Validación — Motor Óptico: NOCT y γ coherentes con la ficha del panel

**Estado:** validación

## Checklist de validación del módulo

- [x] 12 pruebas nuevas en `tests/test_motor_optico_ficha_termica.py`: en
  `main` el archivo no se puede cargar (no existe
  `calculos.motor_optico_ficha`); con el cambio pasan.
- [x] Prueba con las páginas reales (AppTest, JA Solar JAM66D46-720/LB del
  catálogo: NOCT 45, γ −0,29):
  - 🔆 Motor Óptico con NOCT 35 y γ −0,70 guardados: aviso 🟠 «… NOCT 35 °C
    (la ficha dice 45 °C): con 1000 W/m² la celda sale 12.5 °C más fría …» y
    botón «↩️ Usar los de la ficha»; tras el clic, NOCT 45, γ −0,29 y sin
    aviso.
  - 📊 Producción con el Motor Óptico en 35 °C: aviso 🟠 antes de simular; en
    45 °C, sin aviso.
- [x] Pruebas existentes del Motor Óptico y del Asistente siguen verdes.
- [x] Suite completa de `bipv_python`: 2163 pruebas pasan.

## Resultado

Criterios 1 a 7 cumplidos. En espera de la revisión del PR.
