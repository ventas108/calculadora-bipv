# Validación — Vista 3D: string que cruza dos superficies

**Estado:** validación

## Checklist de validación del módulo

- [x] 20 pruebas nuevas en `tests/test_string_cruza_superficies.py`: en
  `main` el archivo no se puede cargar (no existe
  `calculos.cruce_superficies`); con el cambio pasan. Cubren módulos físicos,
  pérdida del string (igual al modelo de la Spec B), factor por superficie,
  cadena con y sin cruce, energía publicada, validación, modo físico,
  sección «🔀 6», firmas, editor, persistencia y manual.
- [x] Punta a punta con la energía publicada: con las mismas superficies y
  módulos, la energía de cada superficie con cruce es exactamente la de sin
  cruce × `f_cruce`.
- [x] Prueba con la página real (AppTest, 🗺️ Vista 3D, Bogotá, SPR-E20-327):
  fachada Este (G1 10 × 2 con 5 módulos de cada string en la Oeste, G2 10 × 1)
  y fachada Oeste (10 × 1). Sin errores de la página; los módulos pasan de
  30/10 a 20/20 y el área los sigue (32.61 m² cada una); columna «String que
  cruza» 6.2 % en las dos; PR 0.796/0.801 → 0.746/0.752; energía publicada
  15,865 → 14,920 kWh.
- [x] Suite completa de `bipv_python`.

## Resultado

Criterios 1 a 9 cumplidos. En espera de la revisión del PR.
