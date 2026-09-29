# Diseño — Unifilar y RETIE coherentes con Motor Óptico, Mismatch y Vista 3D

**Estado:** validación

## Entradas

- Panel (`Isc_stc`, `bifacialidad_pct`), `bifacial_activo`, `bifacial_cfg`,
  `ms_bifacial_on`, superficies con `montaje_fachada`, grupos con `cruce`,
  `perdida_ohmica_unifilar`, `pct_cableado_dc`.

## Salidas

- `calculos/corriente_bifacial.py`:
  - `BNPI_TRASERA_W_M2 = 135.0`, `factor_isc_bifacial(phi) -> float`.
  - `phi_proyecto(estado, panel) -> (phi, origen)` y
    `phi_superficie(sup, estado, panel) -> (phi, origen)`;
    origen ∈ {`modelo`, `panel`, `monofacial`}.
  - `panel_para_corriente(panel, phi) -> dict` (copia con `Isc_stc` BNPI,
    `Isc_stc_frontal` y `factor_bifacial`).
- `calcular_perdida_ohmica(..., factor_bifacial=1.0)`.
- `construir_config_retie(..., factor_bifacial=1.0)`; `calcular_retie`
  devuelve `isc_bnpi_a` e `isc_diseno_string_a` = Isc × factor × 1.25.
- `validar_diseno_electrico(..., bifacial=None)`: grupos con
  `factor_bifacial`; `isc_total` y compatibilidad con el Isc BNPI.
- `topologia_desde_estado`: grupos con `isc_stc_A` BNPI, `isc_frontal_A`,
  `factor_bifacial`, `cruce_texto`; superficies con `modulos_fisicos`.
- Fusible gPV de la ficha multi-superficie con el Isc BNPI.

## Tipos de datos

`float`, `dict`, `str`.

## Errores posibles

- Sin Isc: sin corriente de diseño (como antes).
- Bifacialidad fuera de 0–100 %: se recorta a 0–1.

## Dependencias

`calculos.multi_superficie.parametros_poa_estado` y
`config_bifacial_superficie`; `calculos.cruce_superficies` (Spec C).

## Criterios de aceptación

1. JAM66D46-720/LB con φ 0.80: Isc_BNPI = 18.59 × 1.108 = 20.60 A; Isc de
   diseño RETIE 25.74 A; fusible ≥ 32.18 A.
2. Monofacial o fachada adosada: sin cambio.
3. Modelo apagado con panel bifacial: se usa la bifacialidad del panel y se
   avisa.
4. Unifilar: corriente DC de diseño y semáforo de ampacidad con el factor.
5. ⚡ Diseño eléctrico: `isc_total` del MPPT con el factor por grupo.
6. String que cruza: marcado en la topología; módulos físicos por superficie.
7. 🔀 Mismatch avisa cuando Producción usa el cableado del Unifilar; el
   Unifilar multi-superficie muestra el % real.
8. Manual del Asistente con la cuenta.
