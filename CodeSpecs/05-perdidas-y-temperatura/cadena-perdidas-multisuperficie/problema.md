# Spec — Cadena de pérdidas del sistema multi-superficie (Vista 3D)

**Estado:** validación

## Alcance de la fase

App Streamlit (`bipv_python/`): energía que 🗺️ Vista 3D publica a 💰
Financiero, 🔋 Baterías y 🌿 CO₂ en sus tres orígenes (simplificado, bypass con
CSV y físico). Evidencia del 27-sep-2026, revisando el código con el proyecto
de un cliente en Bogotá: fachada ASP-ST1-T40 90°/180° (112 módulos) y techo
SPR-E20-327 10°/180° (4 módulos), 8,36 kWp, 6.155 kWh/año con el origen
simplificado.

## Problema a resolver

La cadena de superficie única (📐 Dimensionamiento → 📊 Producción) usa los
tres motores; la cadena multi-superficie, que es la que llega a Financiero con
`multisup_activo`, no los usa:

| Origen de Vista 3D | Fórmula actual | 🔆 Motor Óptico | 🔬 Motor IV | 🔀 Mismatch |
|---|---|---|---|---|
| simplificado | POA × área instalada × η STC × **PR 0,78 fijo** | no | no (solo aviso de validación) | no |
| bypass con CSV | lo anterior × (1 − pérdida por bypass) | no | sí (SDM del catálogo) | solo la sombra del CSV |
| físico | POA pvlib → SDM + T celda NOCT (`k_bipv` = 1) + sombra 3D + inversor con recorte | no (sin IAM, suciedad ni transmitancia; `k_bipv` fijo en 1) | sí | solo sombra 3D y bypass |

Consecuencias:

1. **El 0,78 no es del proyecto.** `pr_sistema` no lo escribe ninguna página
   (hallazgo H2): TIR y VPN del cliente dependen de un PR genérico. En una
   fachada vertical BIPV la pérdida por ángulo (IAM) y el calentamiento por
   confinamiento son mayores que en un techo ventilado; si el PR real fuera
   0,72, la energía bajaría 7,7 % y la TIR ~1–1,5 puntos.
2. **Lo que el usuario calcula en 🔆 Motor Óptico y 🔀 Mismatch no cambia la
   energía publicada** ni los resultados financieros, sin ningún aviso.
3. **El físico sobreestima** respecto a 📊 Producción con la misma geometría:
   usa la POA sin IAM ni suciedad y `k_bipv` = 1 aunque la superficie sea una
   fachada confinada.
4. **Datos preparados que nadie usa:** 🔀 Mismatch guarda
   `factor_global_mismatch_multisup`, que ningún consumidor lee.

## Contexto

- `calculos/motor_optico.cascada_optica` (IAM ASHRAE directa + difusa,
  suciedad mensual Colombia, térmico NOCT + `k_bipv`, transparencia) y
  `factor_termico_bipv`; `K_BIPV_POR_MONTAJE` e `indice_montaje_default`.
- `calculos/produccion.simular_produccion_anual`: pérdidas de mismatch de
  fabricación, cableado DC/AC, inversor y recorte; publica `PR_sistema`.
- `calculos/mismatch_bypass.simular_bypass_horario` ya acepta `k_bipv` y
  espera una POA con IAM + suciedad (`poa_sin_termico_df`).
- `calculos/multi_superficie.calcular_poa_superficie` entrega `poa_direct` y
  `poa_sky_diffuse`, que `cascada_optica` necesita.
- `calculos/transicion_multisuperficie.recalcular_fisica_superficie` (físico).
- Director: desviación activa H2 en `contratos-entre-modulos.md`; Specs
  `05/panel-por-superficie`, `05/publicacion-energia-multisuperficie`,
  `06/sistema-multisuperficie`.
