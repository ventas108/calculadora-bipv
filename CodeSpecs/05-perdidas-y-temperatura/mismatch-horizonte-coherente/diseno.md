# Diseño — 🔀 Mismatch: horizonte hora a hora y cascada coherente

**Estado:** validación

## Entradas

- `res_sombra["mascara_sombra"]` (bool horario), `poa_df` (con `poa_direct`;
  en bifacial `poa_front`/`poa_rear`), `factor_mismatch_or_pct`,
  `pct_soiling`, `motor_optico_ok`.

## Salidas

- `calculos/mismatch.py`:
  - `DEFAULTS_MISMATCH`, `VERSION_MISMATCH = 2`,
    `CLAVE_VERSION_MISMATCH = "mismatch_version"`.
  - `factor_horizonte_horario(mascara, poa_df) -> np.ndarray`:
    1 − (luz directa frontal en horas bloqueadas) ÷ POA global.
  - `calcular_sombreado_horizonte` agrega `factor_horario`, `solo_directa` y
    `firma`; `factor_sombra_anual` = 1 − Σ(POA × f) ÷ Σ POA.
  - `firma_horizonte(puntos, poa_df) -> str`.
  - `factores_mismatch_produccion(estado, poa_df, motor_ok) -> dict` con
    `factor_escalar`, `factor_horario` (o `None`), `legado`, `avisos`.
  - `aplicar_factor_horario(poa_df, f) -> DataFrame`: `poa_global × f` y, en
    bifacial, `poa_front` baja lo mismo (el aporte trasero no cambia).
- `calculos/mismatch_bypass.excluir_horas_horizonte(p_shade, mascara)`:
  FS = 0 en horas de horizonte; `info` con las horas excluidas.
- 🔀 Mismatch publica `factor_global_mismatch` y
  `factor_mismatch_sin_soiling` **sin horizonte**, `mismatch_version = 2` y
  `pct_soiling_cascada`.
- 📊 Producción: POA base × factor horario antes de la firma y de la
  simulación; `factor_mismatch_aplicado` en sesión; avisos.

## Tipos de datos

`numpy.ndarray` (8760), `pandas.Series`/`DataFrame`, `dict`, `str`.

## Errores posibles

- Máscara con otras horas que la POA: no se aplica el horizonte y se avisa
  «recalcula el horizonte en 🔀 Mismatch».
- POA sin `poa_direct` (multi-superficie): se quita toda la POA en las horas
  bloqueadas, como antes, con `solo_directa = False`.
- Estado de una versión anterior (sin `mismatch_version`): factor escalar
  como antes, sin factor horario, con aviso si había horizonte.

## Dependencias

Ninguna nueva.

## Criterios de aceptación

1. Horizonte de 15°: la pérdida es la luz directa de las horas bloqueadas
   (0.93 %, no 1.85 %); difusa y trasera intactas.
2. Producción aplica el horizonte hora a hora: horas sin sombra con factor 1;
   el escalar no incluye el horizonte; energía = simulación con la POA × f.
3. Bypass: FS 0 en horas de horizonte; el horizonte se cuenta una vez.
4. Estado legado: mismo factor que antes y ningún factor horario.
5. Con Motor Óptico, el control de suciedad está deshabilitado y la cascada
   no resta suciedad.
6. La cascada no muestra filas de pérdidas eléctricas en 0; tabla aparte.
7. Cambiar el horizonte, las orientaciones o la POA recalcula solo.
8. Sin abrir 🔀 Mismatch, Producción avisa que aplica 0 %.
9. Bifacial sin Motor Óptico: la suciedad no toca el aporte trasero.
10. Sin horizonte, una sola orientación y monofacial, Producción da
    exactamente lo mismo que antes (misma firma).
11. El manual del Asistente lo explica con números.
