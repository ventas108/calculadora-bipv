# Validación — 🌾 Granja FV, fase 5: eléctrico por bloques — strings, inversores y cables que alimentan Unifilar y RETIE

**Estado:** validación

## Checklist de validación del módulo

- [x] 17 pruebas nuevas en `tests/test_granja_electrico.py`: en `main` el
  archivo no se puede cargar (no existe `calculos.granja_electrico`); con el
  motor y sin el manual falla 1; con el cambio completo pasan.
- [x] La resistencia DC efectiva es igual a la de `calcular_perdida_ohmica`
  con un tramo por string (27,7 mΩ con 6 mm², 41,6 mΩ con 4 mm²).
- [x] Prueba con las páginas reales (AppTest, Apartadó, JAM66D46-720/LB del
  catálogo, 28 en serie, reparto 6 + 5, 2 × 100 kW):
  - 🌾 Granja FV, sección 8: 🟢 11 strings = 308 módulos (6 + 5), 🟠 4
    strings cruzan filas, 🟢 caída DC 0,68 %, 🟢 caída AC 0,51 %; cable DC
    1.065 m, AC 136 m, 27,7 mΩ, pérdida DC a STC 0,46 %. Con el inversor
    en el centro del bloque el DC baja a 760 m.
  - ⚡ Diagrama Unifilar: casilla «🌾 Usar los cables de 🌾 Granja FV»
    marcada; `perdida_ohmica_unifilar` con 11 tramos DC.
  - 📋 Ficha RETIE: cuatro validaciones «Granja: …» (✅ strings y bloques,
    ⚠️ cruces, ✅ caída DC, ✅ caída AC) con el mismo diseño.
- [x] Guardia de física: sin cambios en fórmulas del SDM.
- [x] Suite completa de `bipv_python`: 2255 pruebas pasan.

## Resultado

Criterios 1 a 7 cumplidos. En espera de la revisión del PR.
