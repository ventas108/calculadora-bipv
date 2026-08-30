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
  🔆 Motor Óptico (`K_BIPV_POR_MONTAJE`: 1.0 ventilado libre · 1.15
  semi-ventilado · 1.3 fachada confinada · 1.5 sellado total).

Son el mismo concepto físico con distinto nivel de detalle — no hacía falta
construir nada nuevo, solo (a) corregir el default por tipo de instalación y
(b) documentar la equivalencia para que la comparación con PVsyst sea
trazable.

## (a) Bug real corregido: default de montaje binario, no por los 6 tipos

Antes de este fix, `pages/5b_🔆_Motor_Optico.py` solo distinguía dos casos.
Se corrigió en 2 pasadas el mismo día — primero a 2 grupos (reutilizando los
3 valores que ya existían), y luego, tras la auto-auditoría de la sección
(d), a 3 grupos con un 4to valor de `k_BIPV` nuevo:

| Tipo de instalación | Default ANTES | Default AHORA | Correcto físicamente |
|---|---|---|---|
| Fachada BIPV | Fachada confinada (k=1.3) | Fachada confinada (k=1.3) | ✅ sin cambio |
| Techo inclinado (BIPV) | Fachada confinada (k=1.3) | Fachada confinada (k=1.3) | ✅ sin cambio |
| Techo plano (con soporte) | Fachada confinada (k=1.3) | **Ventilado libre (k=1.0)** | corregido |
| Pérgola / sombreadero | Fachada confinada (k=1.3) | **Semi-ventilado (k=1.15)** | corregido |
| Marquesina / voladizo | Fachada confinada (k=1.3) | **Semi-ventilado (k=1.15)** | corregido |
| Granja fotovoltaica | Ventilado libre (k=1.0) | Ventilado libre (k=1.0) | ✅ sin cambio (ya corregido 26-ago-2026) |

Un soporte de techo plano no tiene nada que restrinja el flujo de aire — se
queda en ventilado libre pleno. Una pérgola/sombreadero o una
marquesina/voladizo sí son estructuras elevadas, pero con un lado más
expuesto a obstrucción (adosadas a una edificación, o con cerramiento
parcial) que un campo abierto — de ahí el nivel intermedio nuevo
`k=1.15`, **sin calibración propia todavía** (interpolado linealmente entre
1.0 y 1.3, documentado como estimación en el código, no como dato medido).
Con el default original (k=1.3 para los 3), esos tipos sobreestimaban la
temperatura de celda y subestimaban producción sin que nada en pantalla lo
señalara (mismo patrón de incoherencia por `tipo_instalacion` ya
documentado para `factor_ocupacion_pct`, `mo_montaje_tipo_ref` y
`opex_kw_guardado_tipo_ref`).

**Cambio**: `calculos/motor_optico.py`:
- `K_BIPV_POR_MONTAJE` gana una 4ta opción: `"Semi-ventilado (k=1.15)"`.
- `TIPOS_MONTAJE_CONFINADO = {"Fachada BIPV", "Techo inclinado (BIPV)"}` → k=1.3.
- `TIPOS_MONTAJE_SEMIVENTILADO = {"Pérgola / sombreadero", "Marquesina / voladizo"}` → k=1.15.
- Cualquier otro tipo → k=1.0.
- `indice_montaje_default(tipo_instalacion)` — nueva función pura que resuelve el índice del selectbox buscando por VALOR de k_BIPV (no por posición fija en el dict), para no depender de que `K_BIPV_POR_MONTAJE` mantenga un orden concreto.

El usuario sigue pudiendo cambiar el montaje manualmente si su proyecto real
es distinto al default. Sin cambios en la fórmula ni en proyectos que ya
fijaron su montaje explícitamente (el default solo aplica si `mo_montaje`
no está en `session_state` para el tipo activo).

Tests: `tests/test_motor_optico.py` (5 tests: clasificación de los 3
grupos, el índice default para cada uno de los 6 tipos, y que la función no
dependa del orden del dict).

## (b) Tabla de equivalencia k_BIPV ↔ Uc/Uv para validar contra PVsyst

| k_BIPV (app) | Preset PVsyst sugerido | Uc (W/m²K) | Uv (W/m²K por m/s) |
|---|---|---|---|
| 1.0 — Ventilado libre | Free standing | 29.0 | 0.0 |
| 1.15 — Semi-ventilado | *(sin preset oficial — Uc interpolado)* | 24.5 | 0.0 |
| 1.3 — Fachada confinada | Semi-integrated | 20.0 | 0.0 |
| 1.5 — Sin ventilación | Integrated | 15.0 | 0.0 |

El nivel 1.15 no tiene preset propio en PVsyst — es una interpolación
lineal entre "Free standing" y "Semi-integrated", igual de no-calibrada que
el propio `k_BIPV=1.15` (ver (a)). Al configurar el proyecto en PVsyst con
este nivel, lo más honesto es introducir el Uc manualmente (24,5) y dejarlo
marcado como estimación, no como preset del fabricante del software.

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
2. Los coeficientes de temperatura disponibles (μVoc, μPmax, μIsc) — y una
   advertencia explícita solo cuando μIsc realmente falta en el panel (nunca
   se rellena con un valor inventado sin marcarlo como supuesto). Acepta los
   dos esquemas de campo reales del repo (Excel: `marca`/`Imp`, sin μIsc;
   `MODULOS_BIPV`: `fabricante`/`Imp_stc`/`Tk_alfa`) — ver (d) más abajo.
3. El preset Uc/Uv sugerido según la tabla de (b), a partir del `k_BIPV`
   elegido en 🔆 Motor Óptico para ese proyecto.

Tests: `tests/test_ficha_pvsyst.py` (12 tests: 7 con el panel JA Solar
JAM66D46-720/LB de Urabá, incluida la equivalencia del nivel semi-ventilado,
4 anclados al panel real de Teusaquillo ASP-ST1-T40, 1 que ancla la
redacción legal de (e)).

## (d) Auto-auditoría contra el plan original (30-ago-2026)

El usuario pidió explícitamente auditar la implementación contra el plan de
4 fases tal como quedó escrito, con el estándar "cero fallas, cero
incoherencias". Resultado, punto por punto:

**Fase 1 (default por tipo)** — implementada, en 2 pasadas. La primera
versión clasificaba Pérgola/Marquesina como **k=1.0 (ventilado libre)**,
igual que Granja fotovoltaica, reutilizando solo los 3 valores que ya
existían en `K_BIPV_POR_MONTAJE` — una simplificación defendible pero que no
coincidía literalmente con el ejemplo del plan original ("Pérgola/Marquesina
→ semi-ventilado", un tercer nivel entre 1.0 y 1.3). Puesto a elegir
explícitamente entre dejar la simplificación o ser fiel al plan, el usuario
pidió agregar el nivel intermedio real: `K_BIPV_POR_MONTAJE` ahora tiene 4
valores (1.0/1.15/1.3/1.5), `TIPOS_MONTAJE_SEMIVENTILADO` clasifica
Pérgola/Marquesina en el nuevo k=1.15, y `indice_montaje_default()`
reemplaza la lógica binaria anterior por una búsqueda por valor, robusta a
reordenar el dict. El propio k=1.15 queda documentado como interpolación
sin calibración propia (ver (a)), no como un dato medido — honestidad sobre
sus límites, igual que el resto de la tabla de equivalencia.

**Fase 2 (modelo Faiman Uc/Uv real)** — **NO implementada**, por decisión
explícita del usuario en esta misma sesión (eligió "Fase 1+3+4" cuando se
le preguntó el alcance). No es un olvido ni un recorte silencioso.

**Fase 3 (tests + ficha de equivalencia, anclados a Teusaquillo)** —
implementada, con 1 bug real encontrado y corregido en la propia
auditoría: el primer test que se escribió para `ficha_pvsyst.py` usaba como
fixture el panel de Urabá (JA Solar, esquema del catálogo Excel:
`marca`/`Imp`, sin coeficiente de Isc) en vez del panel real de Teusaquillo
que pedía el plan. Eso ocultó que `generar_ficha_conversion_pvsyst()` no
sabía leer el otro esquema real del repo (`datos/tecnologias_bipv.py
MODULOS_BIPV`: `fabricante`/`Imp_stc`/`Tk_alfa`) — con el panel real de
Teusaquillo (`ASP-ST1-T40`) habría mostrado "—" en Fabricante e Imp pese a
que el dato existe, y "μIsc no disponible" pese a que `Tk_alfa=+0.06 %/°C`
sí está en la ficha real. Corregido con el mismo fallback `Tk_alfa or
alpha_sc` que ya usa `modelo_iv.py:449` en el resto del código; 4 tests
nuevos anclados al panel real de Teusaquillo confirman el fix
(`tests/test_ficha_pvsyst.py::test_ficha_teusaquillo_*`).

El punto de "validación numérica cruzada entre ambos modos" (NOCT×k_BIPV
vs. Faiman) del plan original **no se hizo** — depende de la Fase 2, que no
se implementó. Correcto no hacerlo, no un hallazgo pendiente.

**Fase 4 (conectar Uc/Uv a la ficha de exportación)** — implementada y, tras
el fix de (Fase 3) arriba, verificada con el panel real de Teusaquillo, no
solo con un panel sintético.

**Lección para el propio proceso**: este bug es la prueba de por qué el
plan pedía anclar la regresión a un caso real específico (Teusaquillo) en
vez de un fixture cualquiera — un panel "genérico" con el esquema de campos
equivocado no lo habría detectado.

Suite completa tras todos los fixes de esta auditoría (incluido el 4to
nivel de k_BIPV pedido explícitamente por el usuario en (a)): **759/759**.

## (e) Redacción legal: "PVsyst" no se nombra en NINGÚN texto visible al usuario (30-ago-2026)

Por instrucción explícita del usuario ("por cuestiones legales"), se extendió
la política ya vigente en el resto de la app (nunca nombrar "PVsyst" en
texto visible al usuario, solo en comentarios/docstrings internos) en tres
rondas:

1. **3 fugas reales encontradas en páginas ya desplegadas**, que se habían
   quedado fuera del fix original del 29-ago-2026 (que solo cubrió la
   alarma DC/AC):
   - `pages/5a_🌳_Sombras_SketchUp.py` — `st.caption()` decía "la brecha que
     nos separaba de PVsyst, con un modelador mejor".
   - `pages/5_🔀_Mismatch.py` — tooltip (`help=`) de la métrica "Factor
     mismatch" decía "PVsyst 1er orden".
   - `pages/7_💰_Financiero.py` — texto del expander "Modelo P90" (visible,
     no un comentario) decía "PVsyst aplica un factor P90 manual fijo...".

   Las 3 corregidas reemplazando "PVsyst" por "referencia estándar
   internacional". Ningún test las cubría (eran texto de UI, no lógica), así
   que no rompieron ninguna aserción — hallazgo puramente por auditoría
   manual con `grep`, no por fallo de test.

2. **`ficha_pvsyst.py` decidido explícitamente que SÍ debe redactarse**,
   pese a no ser visible dentro de la app en ejecución (solo se genera bajo
   demanda para el propio usuario). Se preguntó explícitamente porque
   redactarlo tiene un costo funcional real: la ficha citaba rutas de menú
   específicas del software de referencia (ej. "Détails du système") que
   identifican el producto sin necesidad de nombrarlo por marca. El usuario
   eligió redactar de todos modos, **aceptando la pérdida de precisión
   operativa** — el texto generado ya no dice en qué pestaña exacta hacer
   clic, solo que existe una sección de pérdidas térmicas del sistema donde
   introducir Uc/Uv manualmente. Nuevo test de regresión
   (`test_ficha_no_menciona_pvsyst_por_nombre`) verifica que la palabra
   "PVsyst" nunca aparece en el texto generado, para cualquier panel/tipo/k.

3. **Hallazgo más importante de esta ronda**: `datos/base_conocimiento_asistente.md`
   NO es documentación puramente interna como los `DIAGNOSTICO_*.md` de la
   raíz — es el corpus que lee `calculos/asistente.py` (Nivel 2: "chat con
   el manual") para el chatbot 🧭 Asistente, cuyo propio system prompt
   instruye "cita la sección del manual cuando aplique". Cualquier mención
   de "PVsyst" ahí puede llegarle textualmente a un cliente real, no solo
   quedarse en el repo. Se encontraron **~40 apariciones** acumuladas de
   varias sesiones (algunas agregadas por el propio asistente en sesiones
   anteriores, incluida esta) y se redactaron todas a "referencia estándar
   internacional" (o paráfrasis equivalente según el contexto gramatical de
   cada frase), salvo las que son identificadores de código reales
   (`ficha_pvsyst.py`, `generar_ficha_conversion_pvsyst()`,
   `test_ficha_pvsyst.py`) — esos nombres de archivo/función son ingeniería
   interna pura, nunca leídos como prosa por un cliente. También se
   renombró el archivo `DIAGNOSTICO_VALIDACION_TEUSAQUILLO_PVSYST.md` →
   `DIAGNOSTICO_VALIDACION_TEUSAQUILLO_REFERENCIA_ESTANDAR.md` (su nombre
   estaba citado 2 veces desde la base de conocimiento) y se actualizaron
   sus 2 referencias cruzadas.

Suite completa tras este fix: **760/760**.

## Alcance de esta sesión

Se hizo (a) el fix de coherencia de default por los 6 tipos, con 4 niveles
reales de k_BIPV + (b) la tabla de equivalencia documentada (4 niveles) +
(c) la ficha de conversión por panel, con soporte para los 2 esquemas reales
de datos de panel del repo + (d) la auto-auditoría contra el plan original,
que encontró y corrigió 1 bug real de esquema y 1 desviación de alcance
(resuelta explícitamente por el usuario). **No** se implementó el modelo
Faiman de dos parámetros con viento real — el usuario, dado el
riesgo/alcance de tocar el motor de cálculo ya validado, decidió
explícitamente posponerlo y quedarse con el k_BIPV actual, ahora de 4
niveles, bien calibrado por los 6 tipos.
