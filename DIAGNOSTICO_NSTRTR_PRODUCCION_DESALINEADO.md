# Bug real: Producción leía N_strings/tracker del widget en vivo, no del diseño confirmado

**Fecha**: 31 de agosto de 2026
**Disparador**: el usuario pidió revisar unas capturas reales de la simulación de Teusaquillo
(`Doc5.docx`, carpeta `PRUEBA PVSYST vs MI APP`) para confirmar visualmente que el trabajo de la
sesión (Motor IV, gráfica de compatibilidad eléctrica) quedó bien desplegado. Revisando las
capturas se encontró, de forma no buscada, una inconsistencia real entre 📐 Dimensionamiento y
📊 Producción para la MISMA sesión.

## El hallazgo en las capturas

| | 📐 Dimensionamiento (6:20 a.m.) | 📊 Producción (6:23 a.m., misma pestaña/sesión) |
|---|---|---|
| Strings/tracker | 8 (capacidad real del Growatt MID15KTL3-X) | **1** |
| Paneles/inversor | 128 | **16** |
| Inversores para 256 paneles | 2 | **16** |
| CA total | 30 kW (2×15 kW) | **240 kW (16×15 kW)** |

El usuario confirmó explícitamente que navegó dentro de la MISMA pestaña con el menú lateral de la
app, sin recargar — descartando que fuera un artefacto de sesiones de navegador separadas.

## Causa raíz

`pages/6_📊_Produccion.py` leía la configuración de strings/tracker desde `session_state["N_str_tr"]`
— la clave del **widget en vivo** de 📐 Dimensionamiento (`st.number_input(key="N_str_tr", ...)`),
que `resolver_n_strings_tracker()` puede volver a calcular en **cualquier render posterior** de esa
página (por ejemplo, si la "firma" mecanismo/inversor/total declarado ya no coincide con la que se
usó la última vez) — no necesariamente el valor con el que el usuario confirmó un diseño.

Los otros 4 lugares de la app que consumen este mismo dato ya usaban la clave correcta,
`session_state["N_str_tr_usado"]` — una **foto fija** que solo se escribe cuando el usuario
confirma un diseño explícitamente, al presionar "▶️ Optimizar N paneles/string" o cargar un
"Prorrateo preliminar":

- `pages/10_📄_Reporte_PDF.py:733`
- `pages/18_🤖_Análisis_IA.py:142`
- `pages/4c_🧩_Comparador_Paneles.py:121`
- `pages/4d_🧭_Comparador_Orientación.py:126`

📊 Producción era el único de los 5 consumidores desalineado — leía la clave "en vivo" en vez de
la "confirmada", exactamente la misma clase de bug que este proyecto ya ha encontrado varias veces
antes (un dato que depende de una elección anterior, pero que otro módulo lee de una fuente que
puede haber cambiado desde entonces, sin que se invalide/sincronice explícitamente).

## Corrección

Un cambio de una línea en `pages/6_📊_Produccion.py`:

```python
# Antes:
_n_strings_tracker_cfg = int(st.session_state.get("N_str_tr", 1) or 1)
# Después:
_n_strings_tracker_cfg = int(st.session_state.get("N_str_tr_usado", 1) or 1)
```

Esta variable ya alimentaba correctamente el resto de la página (banner de compatibilidad
eléctrica, gráfica de compatibilidad string-inversor agregada hoy, y `escalar_p_ac_nom_por_inversores()`
para el DC/AC y el recorte) — el fix corrige el dato en el único punto de entrada, sin tocar la
lógica aguas abajo.

## Impacto real

Con `N_str_tr=1` en vez de `N_str_tr_usado=8`, Producción mostraba una compatibilidad eléctrica
evaluada con el string equivocado (aunque para este caso concreto seguía dando "🟢 compatible", el
riesgo genérico es real: un `N_strings_tracker` distinto puede cambiar `Isc_equiv_tracker` y por
tanto el veredicto de compatibilidad), y calculaba el escalado DC/AC y el recorte del inversor
asumiendo 16 inversores/240 kW CA en vez de los 2 inversores/30 kW CA reales — información
visiblemente incorrecta mostrada al usuario, aunque en este caso concreto (DC/AC muy por debajo de
1) no llegara a activar recorte de producción de cualquier forma.

## Verificación

Fix de una línea en código de página (Streamlit, no unit-testeable directamente por el mismo motivo
que el resto de `pages/6_📊_Produccion.py` — usa `st.set_page_config()` en tiempo de import). Se
verificó: (1) sintaxis del archivo con `ast.parse()`, (2) que ya no queda ninguna lectura de la
clave `"N_str_tr"` (sin sufijo) en el archivo, (3) suite completa: **806/806** (sin cambios, fix de
página no afecta ningún test unitario existente).
