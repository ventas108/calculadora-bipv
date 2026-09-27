# Validación — Cadena de pérdidas multi-superficie

**Estado:** validación

## Checklist de validación del módulo

- [x] Seguimiento del código de los tres orígenes hasta Financiero.
- [x] `tests/test_cadena_perdidas_multisup.py`: 12 pruebas; 3 fallan en `main`
  (Vista 3D con 0,78, PR por superficie, físico sin óptica) y todas pasan con
  el cambio.
  - Criterio 2: PR de la cadena = PR de `simular_produccion_anual` (±0,002)
    para fachada ASP 90° y techo SPR 10°.
  - La fachada CdTe ya no se sobreestima (la fórmula lineal daba +11 %).
  - Criterios 3, 4, 5 y 6; sombra de horizonte solo en el simplificado;
    memoria sin recálculo.
- [x] Pruebas de multi-superficie existentes: 475 pasan.
- [x] Humo con AppTest de Vista 3D con el diseño del cliente (fachada 8 × 14,
  techo 4 × 1, TMY sintético): PR fachada 0,682 y techo 0,802 (antes 0,78 las
  dos); desglose visible; publicación con `cadena_perdidas_v1`; energía
  8.910 → 8.284 kWh/año (−7 %) con ese clima de prueba.
- [x] Suite completa y `physics-guard`.

## Resultado

Criterios 1 a 6 y 8 cumplidos. Criterio 7 (caso del cliente con el TMY real)
se completa en producción: al volver a publicar en 🗺️ Vista 3D.
