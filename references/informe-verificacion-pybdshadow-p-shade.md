# Informe de verificación — pybdshadow como proveedor de `p_shade` eléctrico

**Fecha:** 2026-09-21. **Encargo:** `PROMPT_CLAUDE_PYBDSHADOW_PSHADE.md`. **Copia web:**
https://claude.ai/artifact/7fUXsNfnFGFz9kPRT74nDT (documento vivo, mismo contenido con tablas
formateadas). Esta es la copia local identificable exigida por el encargo. Ningún archivo
productivo fue modificado durante esta verificación.

## Conclusión

**No.** `pybdshadow` no puede producir el `p_shade` eléctrico que necesita el motor BIPV, por
dos razones independientes:

1. **No calcula nada eléctrico.** No tiene modelo de módulo (SDM), de string, de diodo de
   bypass ni de inversor — solo geometría 2D (polígonos de sombra).
2. **Tampoco puede producir, en general, el `p_shade` geométrico que esta app ya define.** Su
   motor de sombra (`bdshadow_sunlight`) solo opera sobre planos horizontales (suelo o techo de
   un edificio extruido verticalmente); no existe en su API pública ningún parámetro de
   inclinación/azimut para una superficie receptora. Las superficies BIPV reales del proyecto
   (`pages/9_🗺️_Vista_3D.py`: Fachada/Techo/Pérgola/Marquesina, tilt/azimuth arbitrarios) son
   exactamente el caso que no modela.

**Hallazgo clave:** el contrato ya vigente de esta app (`docs/contratos/shading-engine-contract.v1.json`,
`calculos/sombras_3d.py`, `calculos/mismatch_bypass.py`) define `p_shade` exactamente como una
fracción **geométrica** (`FS_geometrico`, 0=sin sombra, 1=sombra total), no como una pérdida
eléctrica. La conversión eléctrica (SDM + bypass) ya ocurre río abajo, en
`simular_bypass_horario`, sea cual sea el origen del `p_shade`. La pregunta correcta es si
`pybdshadow` puede alimentar ese `p_shade` geométrico ya existente — y la respuesta es **sí para
techos horizontales**, **no de forma nativa para fachadas verticales ni cubiertas inclinadas**.

**Decisión final:** `pybdshadow` es, como máximo, una referencia algorítmica / proveedor
secundario opcional para cubiertas horizontales sin malla 3D propia — nunca un proveedor
universal, y no reemplaza `sombras_3d.py` ni `mismatch_bypass.py`.

## Qué es pybdshadow (lectura de código, v0.3.5, commit 2025-03-19)

Librería de geometría urbana 2.5D (polígonos + atributo `height`), no un motor de ray-casting 3D.

- `bdshadow_sunlight(buildings, date, roof=False)` (`pybdshadow.py:93-241`): proyección
  analítica exacta de un prisma de paredes verticales sobre el plano `z=0` (`ground`) o sobre la
  azotea horizontal de un edificio más bajo (`roof=True`), vía trigonometría simple
  (`calSunShadow_vector`, `pybdshadow.py:45-90`: `distancia = altura/tan(elevación)`).
- `bdshadow_pointlight`: análogo para una fuente de luz puntual (farola) — no aplica a energía
  solar.
- `cal_sunshine`/`cal_shadowcoverage` (`analysis.py:32-250`): **conteo de horas de sol/sombra por
  celda y por día** (`time = count × precision`, `Hour = horas_luz_día − time/3600`) — no un
  `p_shade` horario por timestamp. Es exactamente lo que el encargo pedía no aceptar sin
  demostración; queda demostrado que es solo eso.
- Toda la geometría es 2D (`shapely.Polygon`, WGS84 o proyección azimutal equidistante local,
  `utils.py:51-102`). Búsqueda exhaustiva en las 1043 líneas de `pybdshadow.py`, `analysis.py`,
  `preprocess.py`, `utils.py`: cero apariciones de `tilt`/`azimuth` de superficie receptora.
- **Evidencia de que el soporte de fachadas fue intentado y abandonado:** `__init__.py:79`
  declara `'cal_sunshine_facade'` en `__all__`, pero la función no existe —
  `pybdshadow.cal_sunshine_facade` → `AttributeError` (confirmado en vivo). Historial de git:
  commit `2024-01-02 "update facade calculation"`, notebook `Example2-facade shadow.ipynb`
  borrado el `2024-03-12`.

## El contrato `p_shade` de esta app

1. `docs/contratos/shading-engine-contract.v1.json`: `fs_geometrico` =
   `"0_no_geometric_shadow_1_total_geometric_shadow"`, distinto de `fs_climatico`/`fs_combinado`.
2. `calculos/sombras_3d.py:343-420` (`calcular_fs_horario`): `FS_geometrico` = choque
   rayo-obstáculo, pura geometría.
3. `calculos/mismatch_bypass.py:242-268` (`simular_bypass_horario`, docstring): `p_shade` =
   "fracción de módulos sombreados [0–1] por hora" — es la ENTRADA del modelo eléctrico.

La conversión eléctrica ocurre íntegramente dentro de `simular_bypass_horario`
(`mismatch_bypass.py:300-362`): separa el string en módulos "sombreados"/"claros", corre el SDM
para ambos grupos, decide si el diodo de bypass activa y calcula la potencia DC — idéntico sea
cual sea el origen de `p_shade`.

## Las cinco magnitudes

| # | Magnitud | ¿La produce pybdshadow? | ¿Quién la produce hoy? |
| --- | --- | --- | --- |
| 1 | Fracción de área geométrica sombreada | Solo plano horizontal | `sombras_3d.calcular_fs_horario` |
| 2 | Fracción de irradiancia directa bloqueada | No (no maneja irradiancia) | `sombras_3d.py` (`transparencia`) |
| 3 | Fracción de irradiancia global perdida | No | `calculos/solar.py` + `calcular_svf_difuso` |
| 4 | Potencia DC perdida (bypass) | No | `mismatch_bypass.simular_bypass_horario` |
| 5 | Energía AC perdida (agregado) | No | `transicion_multisuperficie.recalcular_etapa_inversor_bus` |

## Prototipo experimental A — pybdshadow vs. referencia ray-casting analítica

Montaje desechable en `/tmp/.../scratchpad/pyshade_proto/run_a_geometria.py`: obstáculo
10×10×12 m, Madrid (40.45,-3.74, mismo punto que `references/east2-*`). Referencia: rejilla de
puntos + intersección rayo-caja (slabs, NumPy puro, independiente de trimesh/pybdshadow).
Candidato: polígono `bdshadow_sunlight` intersecado con footprint en planta.

**Superficie horizontal** (caso que pybdshadow sí modela): coincide con la referencia dentro de
±0.008 en todos los casos (sombra total, parcial, cero, obstáculo norte/sur/más bajo, techo
vecino) — el motor geométrico de pybdshadow es correcto para planos horizontales.

**Superficie inclinada/vertical** (forzando su uso fuera de diseño):

| Caso | Tilt | Referencia real | pybdshadow (proxy forzado) | Diferencia |
| --- | --- | --- | --- | --- |
| Inclinada 30°, sombra total | 30° | 1.000 | 1.000 | 0.000 (binario, no revela error) |
| Vertical 90°, sol bajo, casi-total | 90° | 1.000 | 0.955 | 0.045 |
| Pared vertical 2×6m, borde de sombra | 90° | 0.707 | 1.000 | **0.293** |
| Pared vertical 2×6m, más cerca del borde | 90° | 0.537 | 1.000 | **0.463** |
| Pared vertical 2×8m, centrada en el borde exacto | 90° | 0.488 | 1.000 | **0.512** |

Error de hasta 51 puntos porcentuales en el caso realista (fachada parcialmente sombreada por
altura) — falla estructural: `bdshadow_sunlight` no tiene forma de representar que una pared
vertical cambia de sombreada a no sombreada según `z`.

## Prototipo experimental B — fracción geométrica vs. pérdida eléctrica DC

Uso de solo lectura de `calculos.mismatch_bypass.simular_bypass_horario` (sin modificar nada).
Panel `SPR-E20-327`, N_series=7, N_paralelo=2, G_eff=800 W/m², T_amb=20°C constantes.

| p_shade | P_dc uniforme (kW) | P_dc con bypass (kW) | Pérdida DC (%) | Pérdida%/área% |
| ---: | ---: | ---: | ---: | ---: |
| 0.05 | 3.376 | 3.376 | 0.00 | 0.00 (bajo umbral) |
| 0.10 | 3.376 | 3.039 | 10.00 | 1.00 |
| 0.14 | 3.376 | 2.904 | 14.00 | 1.00 |
| 0.30 | 3.376 | 2.363 | 30.00 | 1.00 |
| 0.70 | 3.376 | 1.013 | 70.00 | 1.00 |
| 1.00 | 3.376 | 0.000 | 100.00 | 1.00 |

Con bypass activo, la pérdida DC% coincide casi exactamente con `p_shade` — pero es una
propiedad del modelo de dos grupos de esta app, no una ley universal: se rompe en el umbral
(salto de 0% a 10% entre p_shade=0.05 y 0.10, `umbral_shade=0.05`) y depende de N_series,
N_paralelo, G_eff, T_amb y el SDM del panel. `pybdshadow` no conoce ninguno de esos parámetros.

## Casos de aceptación

Ver tabla completa en la copia web. Resumen: geometría horizontal (sur/norte/más
bajo/cero/total/parcial) — error ≤0.008 en ambos motores. Geometría vertical en el borde de la
sombra — error hasta 0.512. Nocturno — ambos motores rechazan sin inventar sombra. TMY con tz —
responsabilidad del llamador en ambos casos. Dos superficies con orientaciones distintas y año
bisiesto — cubiertos por pruebas ya existentes del repositorio
(`test_sombras_por_superficie.py`, `test_transicion_multisuperficie.py`), no repetidos aquí.

## Contrato universal `ShadowProvider`/`ShadowResult`

Ver la copia web para el esquema completo. Decisión de diseño clave: `p_shade` en `ShadowResult`
es y debe seguir siendo geométrico; ningún proveedor escribe ahí una magnitud eléctrica. Campos
mínimos: `surface_id`, `timestamps_utc`+`timezone`, `p_shade` (definición explícita),
`fraccion_area_geometrica`, `componentes_directa_difusa` (opcional), `geometria_sombra`
(opcional), `cobertura_temporal`+`resolucion`, `crs`/`unidades`, `firma_reproducible`,
`version_proveedor`, `capacidades_declaradas` (`soporta_vertical`, `soporta_inclinada`, ...),
`calidad_confianza`, `advertencias`/`datos_faltantes`, distinción explícita
`sombra_cero_calculada` vs. `no_calculado`.

## Qué debe ser pybdshadow y qué debe seguir siendo propio

Candidato legítimo: sombra urbana entre edificios vecinos sobre cubiertas horizontales sin
malla 3D propia; fuente de `geometria_sombra` auditable para mapas. Debe seguir siendo propio,
siempre: cualquier superficie inclinada/vertical, sombra parcial módulo a módulo, toda la
cadena eléctrica, la firma de vigencia y la invalidación transaccional.

## Riesgos y límites

- **Incompatible con Python 3.14 tal como se distribuye**: `pip install pybdshadow` arrastra
  `keplergl`, que falla al compilar en 3.14 (pyarrow/pkg_resources). Requirió un stub manual
  para poder probarlo — inaceptable en producción sin el mismo parche. `bipv_python/.venv`
  corre Python 3.14.2.
- **Mantenimiento estancado**: último commit de código real `2024-01-03`; commit posterior
  (`2025-03-19`) solo toca `CITATION.cff`.
- **API rota publicada**: `cal_sunshine_facade` en `__all__` sin implementación.
- **Stack de dependencias pesado y ajeno**: geopandas/shapely/rtree/pyproj/suncalc/transbigdata/
  keplergl/tqdm/retrying/vt2geojson/requests, ninguna usada hoy por `bipv_python`.
- **Rendimiento**: una llamada por timestamp (sin vectorización horaria), vs. el ray-casting
  vectorizado propio.
- **Licencia**: BSD-3-Clause — sin restricciones, no es un riesgo.
- **Recomendación**: si se integra alguna vez, estrictamente opcional (import perezoso, nunca en
  `requirements.txt` base).

## Decisión final y cambios en la CodeSpec

No modificar el contrato vigente `p_shade`/`FS_geometrico`. Propuesta de Spec vertical nueva
(pendiente de aprobación humana) en
`CodeSpecs/05-perdidas-y-temperatura/proveedor-sombra-pybdshadow/`.

## Reproducibilidad

- Clon: `git clone --depth 1 https://github.com/ni1o1/pybdshadow.git` (commit `2025-03-19`).
- Entorno aislado en el scratchpad de la sesión (Python 3.14.2), dependencias instaladas una por
  una para sortear el fallo de keplergl/pyarrow.
- Prototipo A: `run_a_geometria.py`. Prototipo B: `run_b_electrico.py` (lectura de
  `bipv_python/.venv` real, sin modificar código productivo).
