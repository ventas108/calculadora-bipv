# Validación — Mismatch por orientación hora a hora

**Estado:** validación

## Checklist de validación del módulo

- [x] 16 pruebas nuevas en `tests/test_mismatch_orientacion_horario.py`: en
  `main` + Spec A el archivo no se puede cargar (no existen
  `perdida_string_bypass` ni `firma_orientacion`); con el cambio pasan.
  Incluyen los casos a mano (800/100 → 400 de 450; 1000/900 → 900 de 950;
  tres grupos → 420 de 560), Este/Oeste en Apartadó (≈ 14.9 %, antes 0.00 %),
  albedo y bifacial del proyecto, firma y una prueba de punta a punta contra
  el motor de Producción.
- [x] Verificación de punta a punta con las páginas reales (AppTest,
  🔀 Mismatch con Este/Oeste en el mismo string, horizonte de 15° y suciedad
  2 % → 📊 Producción, JAM66D46-720/LB × 308):
  - Sin Motor Óptico: pérdida hora a hora 10.74 % (inclinación 10°; el cálculo
    anterior daba 0.00 %); la irradiancia que entra al motor es
    POA × horizonte × orientación × 0.98 hora a hora (diferencia 1e-14 W/m²).
  - Con 🔆 Motor Óptico: POA del Motor Óptico × horizonte × orientación
    (diferencia 7e-15 W/m²), factor escalar 1.0 (sin segunda suciedad).
  - Los cinco casos de la Spec A siguen exactos.
- [x] Suite completa de `bipv_python`.

## Resultado

Criterios 1 a 8 cumplidos. En espera de la revisión del PR.
