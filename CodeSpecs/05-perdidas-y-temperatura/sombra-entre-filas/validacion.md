# Validación — Sombra entre filas y cara trasera según la geometría del campo (🌾 Granja FV, fase 2)

**Estado:** validación

## Checklist de validación del módulo

- [x] 21 pruebas nuevas en `tests/test_sombra_entre_filas.py`: en `main` el
  archivo no se puede cargar (no existen `aplicar_sombra_filas` ni las
  funciones de geometría → energía); con el cambio pasan.
- [x] Las 22 pruebas de la fase 1 (`tests/test_granja_fv.py`) siguen verdes.
- [x] Prueba con las páginas reales (AppTest, Apartadó, JAM66D46-720/LB del
  catálogo, monofacial, TMY sintético sin red):
  - ☀️ Recurso Solar sin filas: POA 2,423 kWh/m².
  - 🌾 Granja FV: 🟠 «La POA vigente no incluye la sombra entre filas…»;
    «📏 Estimar» da 2,423 → 2,418 kWh/m², pérdida **0,19 %** (referencia
    0,20 %); «⚡ Usar la geometría» guarda GCR 0,3979, altura 2,628 m,
    mesa 2,626 m.
  - ☀️ Recurso Solar con esa geometría: POA 2,418 kWh/m² (−0,19 %).
  - 🌾 Granja FV de nuevo: 🟢 «La energía usa la geometría del campo».
- [x] Guardia de física (`verificar_fisica_tiene_test.py`): sin cambios en
  fórmulas del SDM.
- [x] Suite completa de `bipv_python`: 2206 pruebas pasan.

## Resultado

Criterios 1 a 8 cumplidos. En espera de la revisión del PR.
