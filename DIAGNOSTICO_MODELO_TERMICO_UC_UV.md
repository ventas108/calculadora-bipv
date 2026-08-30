# Factor térmico diferenciador BIPV: k_BIPV (app) ↔ Uc/Uv (PVsyst)

**Fecha:** 30-ago-2026
**Origen:** al intentar validar la app contra PVsyst 8.1.5 específicamente en
BIPV, el usuario reportó que el catálogo de PVsyst no trae paneles BIPV
(solo silicio cristalino o amorfo "de catálogo"). El bloqueo real no es el
panel — PVsyst permite crear un módulo custom con los parámetros exactos del
datasheet — sino igualar el **modelo térmico de montaje**, que es el factor
que más cambia el resultado entre un BIPV confinado (fachada, sin
ventilación trasera) y un panel en estructura libre.

## El concepto físico

Un panel integrado a fachada u otra estructura sin cámara de aire trasera
opera más caliente que un panel en montaje libre, a igual irradiancia y
temperatura ambiente — la diferencia de temperatura de celda cae
directamente sobre la producción (coeficiente de temperatura negativo).

- **PVsyst** modela esto con un balance térmico de dos parámetros
  (modelo de Faiman): `T_cel = T_amb + G_poa / (Uc + Uv·v_viento)`,
  configurable en "Détails du système" → pérdidas térmicas.
- **Esta app** ya modela el mismo fenómeno desde antes de esta sesión, con
  un multiplicador de un solo parámetro sobre el modelo NOCT
  (`calculos/temperatura.py::temperatura_celda_noct`):
  `T_c = T_amb + G_poa × (NOCT − 20)/800 × k_BIPV`, con `k_BIPV` elegido en
  🔆 Motor Óptico (`K_BIPV_POR_MONTAJE`: 1.0 ventilado libre · 1.3 fachada
  confinada · 1.5 sellado total).

Son el mismo concepto físico con distinto nivel de detalle — no hacía falta
construir nada nuevo, solo (a) corregir el default por tipo de instalación y
(b) documentar la equivalencia para que la comparación con PVsyst sea
trazable.

## (a) Bug real corregido: default de montaje binario, no por los 6 tipos

Antes de este fix, `pages/5b_🔆_Motor_Optico.py` solo distinguía dos casos:

| Tipo de instalación | Default ANTES | Default AHORA | Correcto físicamente |
|---|---|---|---|
| Fachada BIPV | Fachada confinada (k=1.3) | Fachada confinada (k=1.3) | ✅ sin cambio |
| Techo inclinado (BIPV) | Fachada confinada (k=1.3) | Fachada confinada (k=1.3) | ✅ sin cambio |
| Techo plano (con soporte) | Fachada confinada (k=1.3) | **Ventilado libre (k=1.0)** | corregido |
| Pérgola / sombreadero | Fachada confinada (k=1.3) | **Ventilado libre (k=1.0)** | corregido |
| Marquesina / voladizo | Fachada confinada (k=1.3) | **Ventilado libre (k=1.0)** | corregido |
| Granja fotovoltaica | Ventilado libre (k=1.0) | Ventilado libre (k=1.0) | ✅ sin cambio (ya corregido 26-ago-2026) |

Un soporte de techo plano, una pérgola o una marquesina son estructuras
elevadas con flujo de aire libre en ambas caras del panel — no fachadas
selladas. Con el default anterior, esos 3 tipos sobreestimaban la
temperatura de celda y, en consecuencia, subestimaban producción, sin que
nada en pantalla lo señalara (mismo patrón de incoherencia por
`tipo_instalacion` ya documentado para `factor_ocupacion_pct`,
`mo_montaje_tipo_ref` y `opex_kw_guardado_tipo_ref`).

**Cambio**: `calculos/motor_optico.py::TIPOS_MONTAJE_CONFINADO = {"Fachada
BIPV", "Techo inclinado (BIPV)"}` — solo estos dos tipos defaultean a k=1.3;
el resto defaultea a k=1.0. El usuario sigue pudiendo cambiar el montaje
manualmente si su proyecto real es distinto al default. Sin cambios en la
fórmula ni en proyectos que ya fijaron su montaje explícitamente (el default
solo aplica si `mo_montaje` no está en `session_state` para el tipo activo).

Tests: `tests/test_motor_optico.py` (4 tests, ancla la clasificación de los
6 tipos y la lógica de índice que usa la página).

## (b) Tabla de equivalencia k_BIPV ↔ Uc/Uv para validar contra PVsyst

| k_BIPV (app) | Preset PVsyst sugerido | Uc (W/m²K) | Uv (W/m²K por m/s) |
|---|---|---|---|
| 1.0 — Ventilado libre | Free standing | 29.0 | 0.0 |
| 1.3 — Fachada confinada | Semi-integrated | 20.0 | 0.0 |
| 1.5 — Sin ventilación | Integrated | 15.0 | 0.0 |

**Advertencia honesta sobre esta equivalencia**: no es una igualdad
numérica exacta. El modelo de la app es un multiplicador de un solo
parámetro sobre NOCT; el de PVsyst es un balance térmico real de dos
parámetros con dependencia explícita de la velocidad del viento del sitio
(que esta app ya trae en el TMY vía PVGIS — se usa hoy para el autolavado
de soiling, pero el modelo térmico de la app todavía no la usa). Esta tabla
da un punto de partida físicamente coherente para que ambas herramientas
arranquen del mismo supuesto de montaje — no elimina la diferencia
estructural entre los dos modelos.

Si más adelante se necesita una comparación más rigurosa que esta
equivalencia aproximada, el siguiente paso natural es implementar el modelo
de Faiman completo (`T_cel = T_amb + G_poa/(Uc + Uv·viento)`) como modo
opcional junto al NOCT×k_BIPV actual, usando el viento real del TMY —
evaluado y **pospuesto explícitamente** en esta sesión a pedido del usuario,
para no arriesgar el modelo de producción ya validado con un cambio de
mayor alcance sin necesidad inmediata.

## (c) Ficha de conversión por panel

`calculos/ficha_pvsyst.py::generar_ficha_conversion_pvsyst(panel,
tipo_instalacion, k_bipv)` genera, para cualquier panel del catálogo, un
texto con:

1. Los parámetros eléctricos STC en el orden que pide el diálogo
   "PV module → New" de PVsyst (Pnom, Vmp, Imp, Voc, Isc, área,
   tecnología).
2. Los coeficientes de temperatura disponibles (μVoc, μPmax) — y una
   advertencia explícita si falta μIsc (no está en el catálogo de esta app;
   nunca se rellena con un valor inventado sin marcarlo como supuesto).
3. El preset Uc/Uv sugerido según la tabla de (b), a partir del `k_BIPV`
   elegido en 🔆 Motor Óptico para ese proyecto.

Tests: `tests/test_ficha_pvsyst.py` (6 tests, con el panel real JA Solar
JAM66D46-720/LB de Urabá como fixture).

## Alcance de esta sesión

Se hizo (a) el fix de coherencia de default + (b) la tabla de equivalencia
documentada + (c) la ficha de conversión por panel. **No** se implementó el
modelo Faiman de dos parámetros con viento real — el usuario, dado el
riesgo/alcance de tocar el motor de cálculo ya validado, decidió explícitamente
posponerlo y quedarse con el k_BIPV actual bien calibrado por los 6 tipos.
