# Spec — Sombra falsa con el sol detrás del plano del módulo

**Estado:** diseño

## Alcance de la fase

Motor de sombreado 3D de la app hermana Streamlit (`bipv_python/`):
`calculos/sombras_3d.calcular_fs_horario`, su envoltura por superficie
`calcular_fs_horario_por_superficie`, el contrato de la app web
`scripts/run_shading_contract.py` (solo aceptar el dato nuevo) y la
invalidación de sombras persistidas (`calculos/vinculador_sombra_multisuperficie`).
No cambia fórmulas eléctricas, el modelo de bypass ni la interfaz React.

## Problema a resolver

`calcular_fs_horario` lanza, para cada punto de análisis, un rayo hacia el sol
en **todas** las horas con altura solar > `ALTURA_SOLAR_MIN_DEG`, sin mirar la
orientación del módulo. Cuando el sol está **detrás del plano del módulo**
(`sol · normal ≤ 0`), el rayo sale hacia la parte trasera y choca contra el
propio edificio al que pertenece la fachada, o contra cualquier obstáculo
situado detrás. Esa hora queda como `FS_geometrico = 1`.

Esa sombra es físicamente imposible: con el sol detrás del plano, la
irradiancia de haz sobre el módulo ya es cero por el ángulo de incidencia
(AOI > 90°); no hay haz directo que sombrear. Pero `p_shade = 1` llega al
modelo de bypass (`mismatch_bypass.simular_bypass_horario`), que aplica
`G_shade = G_eff × (1 − p_shade)` sobre la irradiancia efectiva **total**,
difusa incluida. Resultado: se borra la producción difusa real de la fachada
en esas horas y la pérdida por sombra se sobreestima de forma masiva.

## Evidencia

Todas las corridas usan el motor oficial de `main` (`9398948e`) sin
modificarlo, en un entorno aislado (Python 3.12, `requirements.txt`).
Línea base: las 10 suites de la prueba de cierre multisuperficie dan
`110 passed`.

1. **Invariante violado — torre convexa aislada.** Caja de
   17,29 × 17,29 × 36,42 m, `northOffset = 160,5°` (datos del informe
   provisional de Torre 5, La Salle), un punto a 10 cm de cada cara:

   | Cara (azimut) | Horas con sol | Horas con "sombra" | Con sol delante | Con sol detrás del plano |
   |---|---|---|---|---|
   | 70,5° | 4.411 | 2.172 | 0 | 2.172 |
   | 160,5° (SE) | 4.411 | 2.021 | 0 | 2.021 |
   | 250,5° (SO) | 4.411 | 2.225 | 0 | 2.225 |
   | 340,5° | 4.411 | 2.302 | 0 | 2.302 |

   Un volumen convexo no puede sombrear sus propias caras: queda entero detrás
   del plano de cada una. El 100 % de la "sombra" es con el sol detrás del plano.
   Las horas SE/SO (23,1 % y 25,4 % del año) coinciden con las reportadas por
   el informe provisional de Torre 5 (20,80 % y 25,07 %).

2. **Escena sintética de la prueba de cierre** (JSON Site Designer
   `attached_assets/site-designer-2026-07-14-1606-10_1786198985402.json`,
   árbol, `northOffset = 7°`; 5 puntos de la Fachada Sur, tilt 90°, azimut 180°):

   | Escena | Horas-punto con sombra | Sol delante (reales) | Sol detrás del plano (imposibles) |
   |---|---|---|---|
   | Tal cual (solo árbol) | 4.080 | 678 | 3.402 (83 %) |
   | Más el edificio de la fachada | 10.908 | 678 | 10.230 (94 %) |

   Las 678 horas-punto reales no cambian: la corrección debe eliminar solo las
   imposibles.

3. **Energía afectada.** Con cielo despejado (pvlib, Ineichen), las horas con
   el sol detrás del plano aportan el 24,0 % (SE 160,5°) y el 20,2 %
   (SO 250,5°) de la irradiancia anual sobre fachadas verticales en Bogotá,
   toda difusa y reflejada. Con el cielo nublado real la fracción difusa es
   mayor, consistente con la pérdida del 26–38 % del informe provisional frente
   al 3,7 % de PV·SOL.

## Contexto

- El SVF difuso (`calcular_svf_difuso`) ya usa la normal del módulo y solo
  integra el hemisferio delantero; el haz directo no.
- `calcular_fs_horario_por_superficie` ya recibe `tilt_deg` y `azimuth_deg`
  por superficie y los escribe en la firma, pero no se los pasa al ray-casting.
- Varias rutas llaman a `calcular_fs_horario` sin orientación: pruebas de
  contrato, Site Designer, comparativo SketchUp/Marsh, página
  `5a_🌳_Sombras_SketchUp`, `scripts/run_shading_contract.py` (app web) y
  scripts de auditoría.
- La invalidación de sombras persistidas (`invalidar_sombra_por_cambio_tmy`)
  compara solo la huella del TMY; `version_algoritmo` se firma pero nunca se
  verifica. Subir la versión, por sí solo, no retira sombras ya guardadas.
- La prueba de cierre multisuperficie valida el flujo (8760 valores, firmas,
  cobertura, adopción, rollback), no la plausibilidad física de cada hora
  sombreada; por eso no detectó el defecto.
- Fuera de alcance, con Spec propia posterior: el bypass aplica `p_shade`
  también a la difusa (`mismatch_bypass.py`, archivo protegido por
  `physics-guard`).
