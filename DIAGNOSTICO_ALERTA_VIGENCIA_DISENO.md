# Alerta de vigencia: panel/inversor cambiado sin re-confirmar el diseño

**Fecha**: 31 de agosto de 2026
**Disparador**: al entregar el artefacto "Coherencia Aguas Abajo" (mapa de los 12 módulos y sus
mecanismos de blindaje, pedido tras `DIAGNOSTICO_BLINDAJE_DISENO_CONFIRMADO.md`), quedó identificado
un hueco real y sin cubrir en la cadena: nada avisaba si el usuario cambiaba de panel o inversor en
📐 Dimensionamiento sin volver a confirmar el diseño eléctrico. El usuario pidió explícitamente:
*"sí, construye esa alerta con el mismo rigor"*.

## El hueco exacto

En `pages/4_📐_Dimensionamiento.py`, `panel_dict`/`inversor_dict_dim`/`panel_nombre_dim`/
`inversor_nombre_dim` se escriben **incondicionalmente en cada render** — apenas el usuario cambia
la selección en los `selectbox`, estas variables ya reflejan la elección nueva. En cambio,
`N_serie`/`N_str_tr_usado` (el diseño **confirmado**, fuente única desde el blindaje anterior) solo
se actualizan dentro de los 2 manejadores de botón ("▶️ Optimizar N paneles/string" y "Prorrateo
preliminar").

Consecuencia real: el usuario confirma un diseño con el panel A, luego cambia a panel B (sin volver
a oprimir el botón) y navega a 📊 Producción / 📄 Reporte PDF / 🤖 Análisis IA / 🧩 Comparador
Paneles / 🧭 Comparador Orientación — las 5 páginas seguían evaluando la compatibilidad eléctrica
del panel/inversor **B** contra el N/string calculado para el panel/inversor **A**, sin ningún aviso.
Es la misma familia de bug que `DIAGNOSTICO_NSTRTR_PRODUCCION_DESALINEADO.md`, pero del lado del
panel/inversor en vez del N_strings/tracker.

## Diseño: nunca un falso positivo

`diseno_electrico_confirmado()` solo puede avisar con **evidencia positiva**: una referencia
guardada (`N_serie_panel_ref`/`N_serie_inversor_ref`, escrita en el mismo punto donde se confirma
`N_serie`) que ya no coincide con la selección actual (`panel_nombre_dim`/`inversor_nombre_dim`).
Si la referencia simplemente no existe — por ejemplo, un proyecto guardado antes de que esta
función existiera, o una sesión donde nunca se tocó panel/inversor después de confirmar — `vigente`
queda en `True` y `aviso` en `None`. Nunca se infiere una alarma de la sola ausencia del dato.

Nuevos campos en el dict que devuelve `calculos/dimensionamiento.py::diseno_electrico_confirmado()`:

- `vigente` (bool) — `False` solo si hay referencia guardada Y ya no coincide.
- `aviso` (str | None) — texto listo para `st.warning()` / nota de reporte, con el N/string y el
  panel/inversor con el que se confirmó, y la instrucción de qué hacer (volver a 📐 Dimensionamiento
  y re-confirmar).
- `panel_confirmado` / `inversor_confirmado` — los nombres guardados en la referencia, para que un
  consumidor pueda mostrarlos sin releer session_state directamente.

## Dónde se escribe la referencia y dónde se muestra el aviso

Escritura (2 puntos, junto a donde ya se confirma `N_serie`/`N_str_tr_usado`):

- `pages/4_📐_Dimensionamiento.py`, botón "Prorrateo preliminar".
- `pages/4_📐_Dimensionamiento.py`, botón "▶️ Optimizar N paneles/string".

Lectura/aviso (los mismos 6 puntos que ya consumían `diseno_electrico_confirmado()` desde el
blindaje anterior, más un banner nuevo en la propia Dimensionamiento):

- `pages/4_📐_Dimensionamiento.py` — banner persistente (`st.warning`/`st.caption`), colocado
  deliberadamente DESPUÉS del bloque que reescribe `panel_dict`/`inversor_dict_dim` en cada render
  (para comparar contra la selección ya fresca de ESTE render, no la del anterior).
- `pages/6_📊_Produccion.py` — `st.warning(aviso)`.
- `pages/18_🤖_Análisis_IA.py` — `st.warning(aviso)`, evaluado en el punto de página donde se arma
  `registro = {"Actual": _candidato_actual()}` (la construcción interna de `_candidato_actual()` no
  se tocó; se llama a `diseno_electrico_confirmado()` una segunda vez, función pura y barata, solo
  para el aviso).
- `pages/4c_🧩_Comparador_Paneles.py` / `pages/4d_🧭_Comparador_Orientación.py` — `st.warning(aviso)`
  dentro de `_config_base()`, verificado que cada una se llama una sola vez por render (sin riesgo
  de aviso duplicado).
- `pages/10_📄_Reporte_PDF.py` — el `aviso` se agrega al final del `nota=` ya existente de la
  sección "Compatibilidad Eléctrica String–Inversor" (no bloquea el reporte, coherente con el resto
  de esa página, que nunca detiene la generación por advertencias).

## Verificación

5 tests nuevos en `tests/test_compatibilidad_string.py`:

1. `test_diseno_confirmado_vigente_cuando_panel_e_inversor_no_cambiaron` — referencia y selección
   actual coinciden: `vigente=True`, `aviso=None`.
2. `test_diseno_confirmado_avisa_si_panel_cambio_sin_reconfirmar` — panel distinto: `vigente=False`,
   el aviso cita el panel con el que se confirmó.
3. `test_diseno_confirmado_avisa_si_inversor_cambio_sin_reconfirmar` — mismo caso, del lado inversor.
4. `test_diseno_confirmado_sin_referencia_historica_no_inventa_alarma` — sin `*_ref` guardado:
   `vigente=True` (garantía explícita de no-falso-positivo).
5. `test_diseno_confirmado_sin_diseno_confirmado_todavia_no_avisa` — Dimensionamiento nunca corrió:
   sin diseño que pueda quedar desactualizado, tampoco hay aviso.

Suite completa: **814/814** (809 previos + 5 nuevos). Sintaxis de los 8 archivos tocados verificada
con `ast.parse()` bajo `PYTHONUTF8=1` (los nombres de página usan emoji en el filename).
