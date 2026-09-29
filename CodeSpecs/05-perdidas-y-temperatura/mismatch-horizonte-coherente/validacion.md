# Validación — 🔀 Mismatch: horizonte hora a hora y cascada coherente

**Estado:** validación

## Checklist de validación del módulo

- [x] 30 pruebas nuevas en `tests/test_mismatch_horizonte_coherente.py`: en
  `main` el archivo no se puede cargar (no existen las funciones nuevas); con
  el cambio pasan. Incluyen dos pruebas de punta a punta contra el motor de
  Producción (`simular_produccion_anual`): con horizonte la energía es la de
  la POA con la luz directa quitada a mano en las horas bloqueadas; sin
  horizonte, el mismo factor y la misma energía que antes.
- [x] Verificación de punta a punta con las páginas reales (AppTest:
  🔆 Motor Óptico → 🔀 Mismatch → 📊 Producción, Apartadó, JAM66D46-720/LB
  × 308, Growatt MAX 100KTL3 LV). En los cinco casos la irradiancia que entra
  al motor (`G_eff_Wm2`) coincide hora a hora con la calculada a mano:
  - Monofacial sin horizonte, suciedad 2 %: diferencia 0 W/m²; factor 0.98
    como antes; E_ac 456,849 kWh.
  - Monofacial con horizonte de 15°: diferencia 1e-14 W/m²; horizonte 0.93 %
    de la luz (838 h), −0.99 % de energía (452,349 kWh), una sola vez.
  - Bifacial con horizonte de 15°: diferencia 3e-13 W/m² (la primera corrida
    mostró 0.185 W/m²: la suciedad se calculaba sobre la cara frontal antes
    del horizonte; se corrigió y quedó una prueba permanente).
  - Bifacial con 🔆 Motor Óptico y horizonte: control de suciedad
    deshabilitado («La aplica Motor Óptico, 3.4 %»), cascada con suciedad 0,
    factor 1.0, diferencia 0 W/m² (sin segunda suciedad); aporte trasero en
    Producción 217 kWh/m² = 216.6 del Motor Óptico.
  - Estado de versión anterior: POA × 0.9709 sin factor horario (sin doble
    conteo), con el aviso de recalcular.
- [x] Pruebas de páginas actualizadas (`test_produccion_pagina_vigencia.py`,
  `test_pagina_perdida_ohmica.py`) y pruebas existentes de bypass, horizonte,
  cadena multi-superficie, vigencia y pipeline: pasan.
- [x] Suite completa de `bipv_python`.

## Resultado

Criterios 1 a 11 cumplidos. En espera de la revisión del PR.
