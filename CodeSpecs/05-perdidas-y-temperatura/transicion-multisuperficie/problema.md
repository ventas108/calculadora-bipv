# Spec — Integración de la transición transaccional multi-superficie con Streamlit

**Estado:** aprobado para iniciar integración opt-in, con gates técnicos explícitos

## Alcance de la fase

App hermana Streamlit (`bipv_python/`): integrar `calculos/transicion_multisuperficie.py`
(prototipo Python puro, validado por 27 pruebas propias en 4 rondas de auditoría,
2026-09-20) con `pages/9_🗺️_Vista_3D.py`, hoy el único productor de estado
multi-superficie en la app.

## Problema a resolver

`pages/9_🗺️_Vista_3D.py` calcula producción multi-superficie con un modelo
simplificado (`calculos/multi_superficie.py`: `POA × área × eta_panel ×
PR_sistema`, sin SDM, sin sombra horaria, sin clipping de inversor). Ese
resultado se publica en 5 claves de `session_state`
(`E_ac_anual_kWh_multisup`, `area_total_multisup`, `multisup_desglose`,
`multisup_activo`, `poa_df_multisup`) que consumen **7 páginas y
`calculos/invalidacion.py`** con la
prioridad `multisuperficie > bypass > base` (Financiero, Impacto CO₂,
Baterías y Balance, Mismatch, Reporte PDF, Diagrama Unifilar, Comparador de
Inversores, y el propio `calculos/invalidacion.py` que declara el ciclo de
vida de esas claves).

Existe ahora un módulo físico (`transicion_multisuperficie.py`) que sí usa
el SDM real (`simular_bypass_horario`), sombra horaria, clipping de
inversor (dedicado o compartido) y transiciones transaccionales con
rollback — pero **ningún archivo de Streamlit lo invoca**. `session_state`
no tiene los datos que ese módulo necesita: no hay inversor por superficie,
no hay `p_shade` por superficie, no hay firma de sombra ni de POA óptica, y
Motor Óptico corre una sola vez para todo el proyecto, no por superficie.

## Contexto

Este problema es una continuación directa de `05-perdidas-y-temperatura/
conservacion-optica-inversor`, cuyo `validacion.md` deja registrado
explícitamente: *"Permanecen fuera de alcance las deudas ya registradas de
Multi-Superficie y vigencia de tablas/IA."* El Director también registró
(2026-09-19, `registro-de-decisiones.md`) como desviación activa: *"la
adopción global de orientación en modo multi-superficie"* — la página no
bloquea ni diferencia por superficie hoy.

Un documento de diseño previo (`bipv_python/calculos/transicion_multisuperficie.py`
y su análisis de integración, 2026-09-20) confirmó por lectura directa del
código, no por suposición:

- `session_state["superficies_bipv"]` (única lista real hoy) solo trae
  `nombre, tipo, tilt_deg, azimuth_deg, area_m2, activa, uid` — panel,
  inversor y `N_serie` son GLOBALES del proyecto, compartidos por todas las
  superficies.
- Faltan por completo: inversor por superficie (dedicado/compartido),
  `p_shade` por superficie, `firma_sombra`, `poa_sin_termico_df` por
  superficie y `firma_poa_optica`. No son claves con otro nombre: el
  concepto mismo no está modelado.
- `calculos.sombras_3d` no calcula sombra por superficie (opera sobre un
  único conjunto de puntos de análisis del proyecto) — es un bloqueo real
  para poblar `p_shade`/`firma_sombra` por superficie, no solo un dato
  faltante en `session_state`.
- Motor Óptico (página 5b) corre una sola vez para todo el proyecto —
  modelarlo por superficie es un cambio a esa página, fuera del alcance de
  un simple adaptador.

La corrección debe diseñarse (no implementarse todavía) como una
integración vertical: entrada desde `session_state`, adaptador,
`transicion_multisuperficie.py`, adaptador de salida hacia las 5 claves
`multisup_*` existentes — sin modificar las 7 páginas consumidoras ni
`calculos/invalidacion.py`, sin
tocar el Director, y sin reemplazar el modelo simplificado hasta que una
estrategia de activación segura (opt-in, comparación, adopción explícita)
esté probada.
