# Validación — Unifilar y RETIE coherentes con Motor Óptico, Mismatch y Vista 3D

**Estado:** validación

## Checklist de validación del módulo

- [x] 14 pruebas nuevas en `tests/test_unifilar_retie_bifacial_cruce.py`: en
  `main` + Spec C el archivo no se puede cargar (no existe
  `calculos.corriente_bifacial`); con el cambio pasan. Cubren la cuenta del
  JAM66D46-720/LB (20.60 A; Isc de diseño 25.7 A; fusible 32.18 A), φ según
  modelo, fachada adosada, modelo apagado (lado seguro) y monofacial;
  Unifilar (corriente con factor, resistencia sin cambio); ⚡ Diseño
  eléctrico (`isc_total` × 1.108); topología con cruce y módulos físicos;
  ficha RETIE multi-superficie; avisos de cableado y manual.
- [x] Prueba con las páginas reales (AppTest, JAM66D46-720/LB, Growatt MAX
  100KTL3 LV, modelo bifacial 0.80):
  - 📋 Ficha RETIE de superficie única: «🔄 Isc BNPI (bifacial) = 18.59 A ×
    1.108 = 20.60 A», sin errores.
  - ⚡ Diagrama Unifilar de superficie única: aviso de corriente DC con Isc
    BNPI (× 1.108), sin errores.
  - Multi-superficie (Techo Este con G1 28 × 2 que cruza 10 módulos a Techo
    Oeste): la tabla del sistema, en las dos páginas, muestra Isc de diseño
    20.6 A por módulo y «10 de 28 módulos en «Techo Oeste»», sin errores.
- [x] Suite completa de `bipv_python`: 2099 pruebas pasan.

## Resultado

Criterios 1 a 8 cumplidos. En espera de la revisión del PR.
