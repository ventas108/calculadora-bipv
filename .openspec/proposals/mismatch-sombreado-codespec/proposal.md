# Proposal: CodeSpec de Mismatch y Pérdidas de Sombreado

## Objetivo

Formalizar el módulo `bipv_python/pages/5_🔀_Mismatch.py` y sus motores `mismatch_bypass.py`, `mismatch.py`, `agregacion_fs.py` y `metricas_escenarios.py`, porque esta frontera recibe el CSV de la Calculadora de Sombreado y alimenta bypass, cascada de pérdidas, Producción, Financiero, Reportes y escenarios.

## Contrato principal

- `FS_geometrico` es la única capa física autorizada para activar bypass.
- `FS_climatico`, `FS` combinado y nubosidad son diagnóstico; nunca sustituyen `FS_geometrico`.
- El parser rechaza un CSV sin `FS_geometrico`.
- El CSV se normaliza, se agrega por punto/fachada y se alinea con el índice TMY en modo mensual o exacto.
- La agregación puede ponderar por `n_modulos`, `area_activa_m2` o `potencia_instalada_kw`.
- Horizonte y FS 3D se combinan por máximo, nunca por suma.

## Salidas y consumidores

- `p_shade` horario alineado al TMY.
- `bypass_result`: potencia DC con bypass, pérdida adicional, horas y resumen mensual.
- `factor_sombra_anual`, `factor_global_mismatch`, `cascada_mismatch` y métricas solares.
- Producción incorpora la pérdida eléctrica de bypass; Reporte PDF y Financiero consumen los resultados derivados.

## Hallazgo de coherencia resuelto

La validación confirmó que Página 5 usaba `poa_efectiva_df`, con el factor térmico ya aplicado, mientras el bypass recalculaba temperatura dentro del SDM. El commit `95388cd4` corrigió el camino normal: Página 5 selecciona `poa_sin_termico_df`, bypass recibe `k_BIPV` y escenarios Fase 4 lo propagan.

El commit `f7402f70` cerró la vigencia completa del cálculo:

- Página 5 y Producción bloquean el cálculo cuando Motor Óptico está activo y falta `poa_sin_termico_df`; nunca sustituyen esa entrada por `poa_efectiva_df` ni por POA bruta.
- Recalcular Motor Óptico invalida primero Producción, bypass monofacial, pérdida óhmica, Financiero y CO₂ derivados de la POA anterior.
- La producción persistida en disco también se elimina para impedir que Financiero restaure resultados obsoletos en otra pestaña.
- El estado multi-superficie se conserva porque usa una POA independiente; su coherencia interna permanece fuera del alcance validado.

El cambio fue desplegado en `main` como `e6b76069b` y el endpoint de salud de Streamlit respondió `ok`.

## Estado SDD

El alcance de coherencia térmica e invalidación downstream está implementado y validado. La propuesta completa permanece en estado `proposed` porque todavía quedan pendientes las verificaciones del contrato CSV, alineación, ponderación y ciclo de vida multi-superficie.
