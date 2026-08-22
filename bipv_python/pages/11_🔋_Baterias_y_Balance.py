"""
Página 11 — Baterías y Balance Energético
B-6: Dimensionado eléctrico strings + baterías
B-7: Balance energético mensual + Clasificación A+/A/B/C/D
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from datos.catalogo_baterias_excel import (
    cargar_catalogo_baterias,
    obtener_bateria,
    lista_baterias,
    diagnostico_catalogo,
    excel_mtime as _excel_mtime,
)
from calculos.baterias_balance import (
    dimensionar_bateria,
    balance_mensual,
    balance_horario,
    metricas_balance,
    clasificar_energia,
    distribuir_consumo_anual,
    tabla_clasificaciones,
    PERFILES_TIPICOS,
    PERFILES_HORARIOS,
    MESES,
)

st.set_page_config(
    page_title="Baterías y Balance — BIPV",
    page_icon="🔋",
    layout="wide",
)

from calculos.auth import requerir_login
requerir_login()

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()   # #63 — proyecto activo visible en cada página
st.title("🔋 Baterías y Balance Energético")
st.caption(
    "B-6: Dimensionado de baterías · "
    "B-7: Balance mensual producción vs consumo · "
    "Clasificación energética A+/A/B/C/D"
)

# ── Pre-requisitos ────────────────────────────────────────────────────────────
prod_ok   = st.session_state.get("produccion_ok", False)
df_m_prod = st.session_state.get("df_mensual_produccion", None)

# Prioridad E_ac: multi-superficie > bypass > base (claves exclusivas)
_e_ac_base_bat     = float(st.session_state.get("E_ac_anual_kWh", 0.0))
_e_ac_bypass_bat   = float(st.session_state.get("E_ac_anual_kWh_bypass", 0.0))
_e_ac_multisup_bat = float(st.session_state.get("E_ac_anual_kWh_multisup", 0.0))
_bypass_ok_bat     = st.session_state.get("bypass_ok", False)
_multisup_ok_bat   = st.session_state.get("multisup_activo", False)
_kwh_bp_bat        = float(st.session_state.get("kwh_bypass_anual", 0.0))

if _multisup_ok_bat and _e_ac_multisup_bat > 0:
    e_ac_anual = _e_ac_multisup_bat
elif _bypass_ok_bat and _e_ac_bypass_bat > 0:
    e_ac_anual = _e_ac_bypass_bat
else:
    e_ac_anual = _e_ac_base_bat

if not prod_ok or df_m_prod is None or e_ac_anual <= 0:
    st.warning(
        "⚠️ **Producción no calculada.** "
        "Complete primero la Página 6 — Producción Anual para obtener los datos mensuales "
        "que necesita esta página."
    )
    st.info(
        "💡 Puede continuar configurando baterías, pero el balance energético "
        "requiere los resultados de producción."
    )

# Banner bypass (#37)
if prod_ok and _bypass_ok_bat and _e_ac_bypass_bat > 0:
    st.info(
        f"⚡ **Corrección bypass activa:** "
        f"E_ac base = {_e_ac_base_bat:,.0f} kWh/año → "
        f"pérdida bypass = {_kwh_bp_bat:,.0f} kWh/año → "
        f"**E_ac usada en el balance = {e_ac_anual:,.0f} kWh/año** "
        f"({(_e_ac_base_bat - e_ac_anual) / _e_ac_base_bat * 100:.1f}% menos). "
        "La autogeneración y el dimensionamiento de la batería se calculan con la producción real."
    )
elif prod_ok and e_ac_anual > 0:
    st.caption(
        "💡 Ejecuta el modelo Bypass Diodes en Página 5 para usar la E_ac corregida "
        "por sombra parcial en este balance energético."
    )

# ══════════════════════════════════════════════════════════════════════════════
# B-6 — Dimensionado de baterías
# ══════════════════════════════════════════════════════════════════════════════
_hdr_col, _btn_col = st.columns([8, 2])
with _hdr_col:
    st.header("⚡ B-6 — Dimensionado de Baterías")
with _btn_col:
    st.write("")   # alinear verticalmente con el header
    # #26 — Botón de recarga inmediata (invalida caché sin reiniciar PM2)
    if st.button(
        "🔄 Recargar catálogo",
        help=(
            "Invalida el caché y recarga el catálogo de baterías desde el Excel del servidor. "
            "Úsalo tras agregar o modificar la hoja `Catalogo_Baterias` para confirmar "
            "que los cambios se ven en la app sin necesidad de reiniciar PM2."
        ),
        use_container_width=True,
    ):
        cargar_catalogo_baterias.clear()
        diagnostico_catalogo.clear()
        st.rerun()

# Caché auto-invalidante: si el Excel cambia en disco, _mtime cambia → cache miss
_mtime_bat = _excel_mtime()
cat_bat = cargar_catalogo_baterias(_mtime=_mtime_bat)
tiene_catalogo = len(cat_bat) > 0

# ── #26 — Banner de estado de carga del catálogo ─────────────────────────────
_diag = diagnostico_catalogo(_mtime=_mtime_bat)
_hojas_disp = _diag.get("hojas_disponibles", [])
_hoja_usada = _diag.get("hoja_usada")

if not tiene_catalogo:
    if "error" in _diag:
        st.error(f"🔴 **Excel no accesible:** {_diag['error']}")
    elif not _hoja_usada:
        st.error(
            f"🔴 **Hoja `Catalogo_Baterias` no encontrada** en el archivo Excel del servidor. "
            f"Hojas disponibles: `{'`, `'.join(_hojas_disp) if _hojas_disp else 'ninguna'}`"
        )
    else:
        st.warning("🟡 **Catálogo vacío** — la hoja existe pero no se cargaron modelos. "
                   "Verifique que las columnas del Excel coincidan con el formato esperado.")
else:
    _n_modelos   = _diag.get("modelos_cargados", len(cat_bat))
    _incompletos = _diag.get("modelos_incompletos", [])
    _no_mapeadas = _diag.get("columnas_no_mapeadas", [])
    # #24 — campos cuyo alias no apareció en NINGUNA columna del Excel
    _ausentes    = _diag.get("campos_sin_columna_excel", [])
    # #123 — modelos que aparecen más de una vez en el Excel
    _duplicados  = _diag.get("modelos_duplicados", [])

    _criticos_aus    = [c for c in _ausentes if c.get("critico")]
    _importantes_aus = [c for c in _ausentes if c.get("importante") and not c.get("critico")]

    # ── Alertas de columnas ausentes — visibles sin abrir el expander ──────────
    if _criticos_aus:
        st.error(
            "🔴 **Columnas críticas ausentes en el Excel** — sin ellas ninguna batería "
            "puede dimensionarse: `"
            + "`, `".join(c["campo"] for c in _criticos_aus) + "`  \n"
            "Abre el diagnóstico ↓ para ver exactamente qué encabezados agregar al Excel."
        )
    if _importantes_aus:
        st.warning(
            "⚠️ **Columnas importantes ausentes en el Excel**: `"
            + "`, `".join(c["campo"] for c in _importantes_aus) + "`  \n"
            "Se usarán valores por defecto (80 % DoD · 95 % RTE · 3 000 ciclos). "
            "Abre el diagnóstico ↓ para ver qué encabezados agregar."
        )

    _ambiguas = _diag.get("columnas_ambiguas", [])
    if _ausentes or _incompletos or _no_mapeadas or _duplicados or _ambiguas:
        st.warning(
            f"🟡 **Catálogo parcial** — hoja `{_hoja_usada}` · **{_n_modelos} modelos** cargados"
            + (f" · {len(_ausentes)} columnas ausentes en Excel" if _ausentes else "")
            + (f" · {len(_incompletos)} modelos con valores vacíos" if _incompletos else "")
            + (f" · {len(_no_mapeadas)} columnas no reconocidas" if _no_mapeadas else "")
            + (f" · {len(_duplicados)} modelos duplicados" if _duplicados else "")
            + (f" · {len(_ambiguas)} campos con columnas repetidas" if _ambiguas else "")
        )
    else:
        st.success(
            f"✅ **Catálogo OK** — hoja `{_hoja_usada}` · **{_n_modelos} modelos** · "
            "todas las columnas reconocidas y sin valores vacíos"
        )

# ── #24 — Expander de diagnóstico detallado ──────────────────────────────────
if tiene_catalogo:
    _incompletos = _diag.get("modelos_incompletos", [])
    _no_mapeadas = _diag.get("columnas_no_mapeadas", [])
    _ausentes    = _diag.get("campos_sin_columna_excel", [])
    _duplicados  = _diag.get("modelos_duplicados", [])
    _ambiguas    = _diag.get("columnas_ambiguas", [])
    if _ausentes or _incompletos or _no_mapeadas or _duplicados or _ambiguas:
        with st.expander("🔍 Diagnóstico detallado del catálogo"):

            # ⓪ #24 — Dos o más columnas del Excel mapean al mismo campo
            if _ambiguas:
                st.markdown("**⓪ Campos con columnas repetidas en el Excel:**")
                _rows_amb = [{
                    "Campo interno":      _a["campo"],
                    "Columnas en Excel":  ", ".join(f"`{c}`" for c in _a["columnas"]),
                    "Columna usada":      f"`{_a['usada']}`",
                } for _a in _ambiguas]
                st.dataframe(pd.DataFrame(_rows_amb), use_container_width=True, hide_index=True)
                st.warning(
                    "⚠️ Cuando dos columnas mapean al mismo campo, se usa **la primera "
                    "de izquierda a derecha** y las demás se ignoran. Elimina o renombra "
                    "las repetidas para evitar leer el valor equivocado.",
                    icon="⚠️",
                )

            # ① Columnas completamente ausentes del Excel (#24)
            if _ausentes:
                st.markdown("**① Columnas sin ningún alias en el Excel:**")
                st.caption(
                    "Estas columnas internas no tienen NINGUNA columna mapeada en tu Excel. "
                    "Agrega **UNA** de las opciones sugeridas como encabezado de columna en "
                    f"la hoja `{_diag.get('hoja_usada', 'Catalogo_Baterias')}`."
                )
                _rows_aus = []
                for _c in _ausentes:
                    _nivel = (
                        "🔴 Crítico"    if _c.get("critico")    else
                        "🟡 Importante" if _c.get("importante") else
                        "🔵 Opcional"
                    )
                    _rows_aus.append({
                        "Campo interno":  _c["campo"],
                        "Nivel":          _nivel,
                        "Agregar UNA de estas columnas al Excel":
                            " | ".join(_c.get("columnas_sugeridas", [])),
                    })
                st.dataframe(pd.DataFrame(_rows_aus), use_container_width=True, hide_index=True)

            # ② Columnas del Excel no reconocidas
            if _no_mapeadas:
                st.markdown("**② Columnas del Excel NO reconocidas por el loader:**")
                st.code(", ".join(_no_mapeadas))
                st.caption(
                    "Estas columnas están en el Excel pero no tienen un alias en el loader. "
                    "Si contienen datos importantes, agrega el nombre exacto al `_COL_MAP` "
                    "en `datos/catalogo_baterias_excel.py`."
                )

            # ③ Modelos con valores vacíos (la columna existe pero la celda está vacía)
            if _incompletos:
                st.markdown("**③ Modelos con valores vacíos en campos críticos:**")
                _rows_inc = []
                for _m in _incompletos:
                    _rows_inc.append({
                        "Modelo":                   _m["modelo"],
                        "Campos con valor vacío":   ", ".join(_m["campos_faltantes"]) if _m["campos_faltantes"] else "—",
                        "Ficha marcada completa":   "✅ Sí" if _m.get("datos_completos") else "🟡 No",
                    })
                st.dataframe(
                    pd.DataFrame(_rows_inc), use_container_width=True, hide_index=True
                )
                st.caption(
                    "Modelos sin `capacidad_kWh` no pueden dimensionarse. "
                    "Modelos sin `dod_pct`, `eta_rte_pct` o `ciclos_vida` usan valores por defecto "
                    "(80 % DoD · 95 % RTE · 3 000 ciclos)."
                )

            # ④ Modelos duplicados en el Excel (solo sobrevive la última fila)
            _duplicados = _diag.get("modelos_duplicados", [])
            if _duplicados:
                st.markdown("**④ Modelos duplicados en el Excel:**")
                _rows_dup = [{
                    "Modelo":            _d["modelo"],
                    "Veces que aparece": _d["n"],
                    "Filas en el Excel": ", ".join(str(f) for f in _d["filas_excel"]),
                } for _d in _duplicados]
                st.dataframe(
                    pd.DataFrame(_rows_dup), use_container_width=True, hide_index=True
                )
                st.warning(
                    "⚠️ Cuando un modelo se repite, **solo se carga la última fila** y las "
                    "anteriores se descartan en silencio. Elimina o renombra las filas "
                    "duplicadas en el Excel para saber exactamente qué datos se están usando.",
                    icon="⚠️",
                )
elif not tiene_catalogo:
    with st.expander("📋 Columnas esperadas en la hoja Catalogo_Baterias"):
        st.markdown("""
| Columna | Descripción | Ejemplo |
|---|---|---|
| Modelo | Nombre del modelo | BYD Battery-Box HVM |
| Datos completos (Si/No) | Si / No | Si |
| Capacidad (kWh) | Capacidad nominal | 11.04 |
| Potencia Continua (kW) | Potencia de carga/descarga | 5.0 |
| Voltaje Nominal (V) | Tensión del bus DC | 48 |
| DoD Máximo (%) | Profundidad de descarga máxima | 90 |
| Ciclos de Vida | Ciclos garantizados a DoD nominal | 4000 |
| Eficiencia RTE (%) | Rendimiento round-trip | 96 |
| Tecnología | Química | LFP |
| Costo (USD) | Precio unitario sin IVA | 4200 |
| Garantía (años) | Años de garantía | 10 |
        """)

# ══════════════════════════════════════════════════════════════════════════════
# #163 — Agregar / Editar / Eliminar baterías desde la app (sin SSH al Excel)
# ══════════════════════════════════════════════════════════════════════════════
from datos.catalogo_baterias_excel import guardar_bateria_excel, eliminar_bateria_excel
from calculos.validador_bateria import validar_bateria as _validar_bat_form

with st.expander("🛠️ Agregar / Editar / Eliminar batería del catálogo"):
    st.caption(
        "Escribe directamente en la hoja `Catalogo_Baterias` del Excel del servidor. "
        "Antes de guardar se ejecuta la verificación de coherencia física (#162): "
        "los datos imposibles 🔴 bloquean el guardado."
    )
    # Mensajes del guardado/eliminación anterior (sobreviven al st.rerun)
    _flash = st.session_state.pop("bat_mm_flash", None)
    if _flash:
        st.success(_flash["exito"])
        for _a in _flash.get("avisos", []):
            st.warning(f"🟠 {_a}")

    # ── Extractor PDF de fichas de baterías (como el de paneles/inversores) ──
    from calculos.pdf_bateria_extractor import extraer_parametros_bateria
    st.markdown("**📄 Cargar desde ficha técnica PDF** (opcional)")
    _pdf_bat = st.file_uploader("Ficha técnica de la batería (PDF)", type=["pdf"],
                                key="bat_pdf_up", label_visibility="collapsed")
    if _pdf_bat is not None and st.button("🔎 Extraer datos del PDF", key="bat_pdf_btn"):
        with st.spinner("Leyendo la ficha…"):
            st.session_state["bat_pdf_extr"] = extraer_parametros_bateria(_pdf_bat.getvalue())

    _extr = st.session_state.get("bat_pdf_extr")
    if _extr:
        if _extr.get("error"):
            st.error(f"❌ {_extr['error']}")
        elif not _extr["modelos_detectados"]:
            st.warning(
                "🟠 No se detectaron modelos en el PDF"
                + (" (parece escaneado y no hay OCR disponible en el servidor)."
                   if _extr.get("es_escaneado") and not _extr.get("ocr_disponible")
                   else ". Revisa que sea una ficha técnica de batería o "
                        "ingresa los datos a mano abajo.")
            )
        else:
            _mod_pdf = st.selectbox("Modelo detectado en la ficha",
                                    _extr["modelos_detectados"], key="bat_pdf_modelo")
            _v_pdf = _extr["valores_por_modelo"].get(_mod_pdf, {})
            _fmt = lambda v, u="": f"{v:g}{u}" if v is not None else "—"
            st.markdown(
                f"| Capacidad | Voltaje | Potencia | Química | Ciclos | C-rate |\n"
                f"|---|---|---|---|---|---|\n"
                f"| {_fmt(_v_pdf.get('capacidad_kWh'), ' kWh')} "
                f"| {_fmt(_v_pdf.get('voltaje_V'), ' V')} "
                f"| {_fmt(_v_pdf.get('potencia_kW'), ' kW')}"
                f"{' (estimada a ' + str(_extr['c_rate']) + 'C)' if _v_pdf.get('potencia_estimada') and _extr.get('c_rate') else (' (calculada por corriente×voltaje)' if _v_pdf.get('potencia_estimada') else '')} "
                f"| {_extr.get('quimica') or '—'} "
                f"| {_fmt(_extr.get('ciclos'))} "
                f"| {_fmt(_extr.get('c_rate'), 'C')} |"
            )
            _faltan = [n for n, k in [("DoD", "dod_pct"), ("RTE", "rte_pct")]
                       if _extr.get(k) is None]
            if _faltan:
                st.caption(f"🟠 La ficha no trae {' ni '.join(_faltan)} — quedarán "
                           "vacíos y el sistema usará valores por defecto conservadores.")
            if st.button("📋 Usar estos datos en el formulario", key="bat_pdf_usar",
                         type="primary"):
                _notas_pdf = "Extraída de ficha PDF"
                if _v_pdf.get("potencia_estimada"):
                    if _extr.get("c_rate") is not None:
                        _notas_pdf += f"; potencia estimada a {_extr['c_rate']:g}C nominal"
                    else:
                        _notas_pdf += "; potencia calculada por corriente continua × voltaje"
                st.session_state["bat_pdf_prefill"] = {
                    "nombre": _mod_pdf if _mod_pdf != "(modelo sin nombre)" else "",
                    "fabricante": _extr.get("fabricante") or None,
                    "tipo": _extr.get("quimica") or None,
                    "notas": _notas_pdf,
                    "capacidad_kWh": _v_pdf.get("capacidad_kWh"),
                    "potencia_kW": _v_pdf.get("potencia_kW"),
                    "voltaje_V": _v_pdf.get("voltaje_V"),
                    "dod_pct": _extr.get("dod_pct"),
                    "eta_rte_pct": _extr.get("rte_pct"),
                    "ciclos_vida": _extr.get("ciclos"),
                    "garantia_anos": _extr.get("garantia_anos"),
                }
                # Forzar el modo "Nueva batería" para que Guardar no renombre
                # el modelo que estuviera seleccionado en el editor.
                st.session_state["bat_mm_sel"] = "➕ Nueva batería…"
                st.rerun()
    st.divider()

    _NUEVA = "➕ Nueva batería…"
    _opciones_mm = [_NUEVA] + (sorted(cat_bat.keys()) if tiene_catalogo else [])
    _sel_mm = st.selectbox("Modelo a editar (o crear uno nuevo)", _opciones_mm,
                           key="bat_mm_sel")
    _base = cat_bat.get(_sel_mm, {}) if _sel_mm != _NUEVA else {}
    # Prefill desde la ficha PDF extraída (un solo uso; se consume aquí)
    _pref_pdf = st.session_state.pop("bat_pdf_prefill", None)
    if _pref_pdf is not None:
        _base = _pref_pdf
        st.info("📄 Formulario prellenado con los datos de la ficha PDF — "
                "revisa y completa lo que falte antes de guardar.")

    def _v0(campo, default=0.0):
        try:
            return float(_base.get(campo) or 0)
        except (TypeError, ValueError):
            return default

    with st.form("form_bateria_mm"):
        c1, c2, c3 = st.columns(3)
        with c1:
            f_nombre = st.text_input("Modelo *", value=_base.get("nombre", ""),
                                     max_chars=60)
            f_fabricante = st.text_input("Fabricante", value=_base.get("fabricante", "") or "")
            f_tipo = st.text_input("Tecnología / Química", value=_base.get("tipo", "") or "",
                                   placeholder="LFP, NMC, Plomo-ácido…")
            f_notas = st.text_input("Notas", value=_base.get("notas", "") or "")
        with c2:
            f_cap = st.number_input("Capacidad (kWh) *", min_value=0.0, step=0.1,
                                    value=_v0("capacidad_kWh"), format="%.2f")
            f_pot = st.number_input("Potencia continua (kW)", min_value=0.0, step=0.1,
                                    value=_v0("potencia_kW"), format="%.2f")
            f_volt = st.number_input("Voltaje nominal (V)", min_value=0.0, step=1.0,
                                     value=_v0("voltaje_V"), format="%.1f")
            f_costo = st.number_input("Costo unitario (USD)", min_value=0.0, step=50.0,
                                      value=_v0("costo_usd"), format="%.0f")
        with c3:
            f_dod = st.number_input("DoD máximo (%)", min_value=0.0, max_value=150.0,
                                    step=1.0, value=_v0("dod_pct"), format="%.0f")
            f_rte = st.number_input("Eficiencia RTE (%)", min_value=0.0, max_value=150.0,
                                    step=1.0, value=_v0("eta_rte_pct"), format="%.0f")
            f_cic = st.number_input("Ciclos de vida", min_value=0, step=100,
                                    value=int(_v0("ciclos_vida")))
            f_gar = st.number_input("Garantía (años)", min_value=0, step=1,
                                    value=int(_v0("garantia_anos")))
        st.caption("Campos en 0 se guardan vacíos (dato no disponible). * = obligatorio.")
        _guardar_mm = st.form_submit_button("💾 Guardar batería", type="primary")

    if _guardar_mm:
        _n0 = lambda v: None if not v else v          # 0 / "" → None
        _datos_mm = {
            "nombre": f_nombre.strip(), "fabricante": _n0(f_fabricante.strip()),
            "tipo": _n0(f_tipo.strip()), "notas": _n0(f_notas.strip()),
            "capacidad_kWh": _n0(f_cap), "potencia_kW": _n0(f_pot),
            "voltaje_V": _n0(f_volt), "costo_usd": _n0(f_costo),
            "dod_pct": _n0(f_dod), "eta_rte_pct": _n0(f_rte),
            "ciclos_vida": _n0(f_cic), "garantia_anos": _n0(f_gar),
        }
        if not _datos_mm["nombre"]:
            st.error("❌ El nombre del modelo es obligatorio.")
        else:
            _val_mm = _validar_bat_form(_datos_mm)
            if not _val_mm["ok"]:
                st.error("🔴 **No se guardó** — corrige estos datos físicamente "
                         "imposibles:\n\n"
                         + "\n".join(f"- {e}" for e in _val_mm["errores"]))
            else:
                try:
                    _orig = _sel_mm if _sel_mm != _NUEVA else None
                    guardar_bateria_excel(_datos_mm, nombre_original=_orig)
                except Exception as _e_mm:
                    st.error(f"❌ No se pudo escribir en el Excel del servidor: {_e_mm}")
                else:
                    st.session_state["bat_mm_flash"] = {
                        "exito": f"✅ Batería **{_datos_mm['nombre']}** guardada en el catálogo.",
                        "avisos": _val_mm["avisos"],
                    }
                    st.rerun()

    # ── Eliminar ───────────────────────────────────────────────────────────
    if _sel_mm != _NUEVA:
        st.divider()
        _chk_del = st.checkbox(f"Confirmo que quiero eliminar **{_sel_mm}** del catálogo",
                               key="bat_mm_chk_del")
        if st.button("🗑️ Eliminar batería", disabled=not _chk_del, key="bat_mm_btn_del"):
            try:
                _ok_del = eliminar_bateria_excel(_sel_mm)
            except Exception as _e_del:
                st.error(f"❌ No se pudo eliminar: {_e_del}")
            else:
                if _ok_del:
                    st.session_state["bat_mm_flash"] = {
                        "exito": f"🗑️ **{_sel_mm}** eliminada del catálogo.", "avisos": [],
                    }
                    st.rerun()
                else:
                    st.error(f"❌ No se encontró la fila de **{_sel_mm}** en el Excel.")

col_b1, col_b2 = st.columns([1, 1])

with col_b1:
    st.subheader("Selección de batería")

    if not tiene_catalogo:
        # El banner de error ya fue mostrado arriba — solo bloquear la selección
        st.info("👆 Ver instrucciones arriba para agregar la hoja al Excel del servidor.")
        usa_bateria = False
    else:
        lista = lista_baterias()
        bat_sel = st.selectbox("Batería del catálogo", lista, key="bat_nombre_sel")
        bat = obtener_bateria(bat_sel)

        # Indicador completitud ficha
        if bat.get("datos_completos"):
            st.success("🟢 Ficha completa")
        else:
            _falt = [k for k in ["capacidad_kWh", "potencia_kW", "dod_pct", "ciclos_vida"]
                     if not bat.get(k)]
            # Campos que el loader rellenó con defaults conservadores porque
            # no venían en la ficha (DoD 80%, RTE 95%, 3000 ciclos)
            _DEF_TXT = {"dod_pct": "DoD 80%", "eta_rte_pct": "RTE 95%",
                        "ciclos_vida": "3000 ciclos"}
            _defs = [_DEF_TXT[d] for d in bat.get("_defaults_aplicados", []) if d in _DEF_TXT]
            if _falt:
                st.warning(f"🟡 Datos incompletos — faltan: {', '.join(_falt)}")
            elif _defs:
                st.warning(
                    "🟡 La ficha no traía todos los datos — se usan valores por "
                    f"defecto conservadores: {', '.join(_defs)}. Si conoces los "
                    "reales, edítalos arriba en '🛠️ Agregar / Editar' para "
                    "afinar el dimensionamiento."
                )
            else:
                st.warning("🟡 Ficha marcada como incompleta en catálogo")

        # ── #25 — Compatibilidad batería ↔ inversor ───────────────────────────
        _inv_dim    = st.session_state.get("inversor_dict_dim", {})
        _inv_nombre = st.session_state.get("inversor_nombre_dim", "")
        _bat_v      = bat.get("voltaje_V")

        # Función pura extraída a calculos/compatibilidad_bateria.py (testeable
        # en el banco de regresión; mensajes con ruta de corrección explícita).
        from calculos.compatibilidad_bateria import check_compatibilidad as _check_compatibilidad

        _compat_estado, _compat_msg = _check_compatibilidad(bat, _inv_dim, _inv_nombre)
        if _compat_estado == "error":
            st.error(_compat_msg)
        elif _compat_estado == "warning":
            st.warning(_compat_msg)
        else:
            st.success(_compat_msg)

        # ── #162 — Semáforo de coherencia física de la batería seleccionada ──
        from calculos.validador_bateria import validar_bateria, icono_estado
        _val_bat = validar_bateria(bat)
        _ETIQ_BAT = {
            "capacidad_kWh": "Capacidad (kWh)", "potencia_kW": "Potencia (kW)",
            "voltaje_V": "Voltaje nominal (V)", "dod_pct": "DoD máximo (%)",
            "eta_rte_pct": "Eficiencia RTE (%)", "ciclos_vida": "Ciclos de vida",
            "costo_usd": "Costo (USD)", "garantia_anos": "Garantía (años)",
        }
        _n_err_bat = sum(1 for c in _val_bat["campos"].values() if c["estado"] == "error")
        with st.expander("🚦 Verificación de coherencia física de la batería",
                         expanded=bool(_n_err_bat)):
            if _n_err_bat:
                st.error(
                    f"🔴 **{_n_err_bat} dato(s) físicamente imposible(s)** en la hoja "
                    "Catalogo_Baterias del Excel — el dimensionamiento se bloquea "
                    "hasta corregirlos en el archivo del servidor."
                )
            elif _val_bat["avisos"]:
                st.warning(f"🟠 {len(_val_bat['avisos'])} dato(s) para revisar — puedes "
                           "dimensionar, pero verifícalos en el Excel.")
            else:
                st.success("🟢 Todos los datos de la batería pasan las verificaciones físicas.")
            _filas_bat = []
            for _campo, _lbl in _ETIQ_BAT.items():
                _info = _val_bat["campos"].get(_campo)
                if _info is None:
                    continue
                _v = bat.get(_campo)
                _filas_bat.append({
                    "": icono_estado(_info["estado"]),
                    "Campo": _lbl,
                    "Valor": "—" if _v in (None, 0, "") else str(_v),
                    "Observación": _info["detalle"] or "OK",
                })
            st.dataframe(
                pd.DataFrame(_filas_bat), use_container_width=True, hide_index=True,
                column_config={
                    "": st.column_config.TextColumn(width="small"),
                    "Campo": st.column_config.TextColumn(width="medium"),
                    "Valor": st.column_config.TextColumn(width="small"),
                    "Observación": st.column_config.TextColumn(width="large"),
                },
            )

        # Ficha técnica
        with st.expander("📋 Ficha técnica del modelo seleccionado"):
            ficha = {
                "Capacidad (kWh)":      bat.get("capacidad_kWh", "—"),
                "Potencia (kW)":        bat.get("potencia_kW", "—"),
                "Voltaje nominal (V)":  bat.get("voltaje_V", "—"),
                "Rango de voltaje (V)": (
                    f"{bat['voltaje_min_V']:.0f}–{bat['voltaje_max_V']:.0f}"
                    if bat.get("voltaje_min_V") and bat.get("voltaje_max_V") else "—"
                ),
                "DoD máximo (%)":       bat.get("dod_pct", "—"),
                "Ciclos de vida":       bat.get("ciclos_vida", "—"),
                "Eficiencia RTE (%)":   bat.get("eta_rte_pct", "—"),
                "Tecnología":           bat.get("tipo", "—"),
                "Costo unitario (USD)": f"${bat.get('costo_usd', 0):,.0f}" if bat.get("costo_usd") else "—",
                "Garantía (años)":      bat.get("garantia_anos", "—"),
            }
            if _inv_nombre:
                ficha["Inversor del proyecto"] = _inv_nombre
            st.table(pd.DataFrame(ficha.items(), columns=["Parámetro", "Valor"]))

        usa_bateria = st.checkbox("✅ Incluir batería en el balance energético", value=True)

with col_b2:
    st.subheader("Parámetros de diseño")

    # Consumo diario — prioridad: factura real de 🏠 Proyecto (modo "Conozco mi
    # consumo") > estimado desde la propia producción > default genérico.
    # Corregido (2026-08-21): antes SIEMPRE se estimaba desde E_ac_anual/365
    # (un promedio de la PRODUCCIÓN, no del consumo real del usuario), incluso
    # cuando el usuario ya había declarado su consumo real de la factura en
    # 🏠 Proyecto -- los dos quedaban desconectados.
    _consumo_mes_factura_b6 = float(st.session_state.get("consumo_kwh_mes", 0.0))
    if _consumo_mes_factura_b6 > 0:
        consumo_diario_default = round(_consumo_mes_factura_b6 * 12 / 365, 1)
        _fuente_consumo_b6 = "tu factura real (🏠 Proyecto)"
    elif e_ac_anual > 0:
        consumo_diario_default = round(e_ac_anual / 365, 1)
        _fuente_consumo_b6 = "tu propia producción (sin factura registrada en 🏠 Proyecto)"
    else:
        consumo_diario_default = 30.0
        _fuente_consumo_b6 = "un valor genérico (sin datos disponibles)"
    E_consumo_diario = st.number_input(
        "Consumo diario del edificio (kWh/día)",
        min_value=1.0,
        max_value=5000.0,
        value=float(st.session_state.get("consumo_diario_kWh", consumo_diario_default)),
        step=1.0,
        help=(
            f"Promedio diario. Valor sugerido desde {_fuente_consumo_b6}. "
            "Si tiene la factura mensual, divida por 30."
        ),
        key="consumo_diario_kWh",
    )
    if _consumo_mes_factura_b6 > 0:
        st.caption(f"📄 Sugerido desde {_fuente_consumo_b6}: {consumo_diario_default:.1f} kWh/día.")

    autonomia_h = st.slider(
        "Autonomía deseada (horas sin sol / red)",
        min_value=1,
        max_value=48,
        value=int(st.session_state.get("autonomia_baterias_h", 4)),
        step=1,
        key="autonomia_baterias_h",
        help="Horas que la batería debe cubrir sin producción solar ni red. "
             "Valor típico: 4–8 h (respaldo nocturno). "
             "24 h = autonomía completa 1 día.",
    )

# #25 — la incompatibilidad batería↔inversor también bloquea el dimensionamiento
# (antes solo se mostraba el error rojo pero el botón seguía habilitado).
_bloqueo_compat = _compat_estado == "error" if tiene_catalogo else False
if tiene_catalogo and _bloqueo_compat:
    _help_dim = ("Batería incompatible con el inversor del proyecto (ver 🔴 arriba). "
                 "Selecciona otra batería o cambia el inversor en Página 4.")
elif tiene_catalogo and not _val_bat["ok"]:
    _help_dim = "Corrige los datos marcados en 🔴 en la hoja Catalogo_Baterias del Excel."
else:
    _help_dim = None

if tiene_catalogo and st.button(
    "▶️ Dimensionar batería", type="primary",
    disabled=(not _val_bat["ok"]) or _bloqueo_compat,
    help=_help_dim,
):
    if _bloqueo_compat:
        st.error(
            "🔴 **No se dimensionó** — la batería seleccionada es incompatible con el "
            "inversor del proyecto (ver detalle arriba). Un banco de baterías con "
            "voltaje fuera del rango del inversor es un error de diseño costoso en campo."
        )
    elif not _val_bat["ok"]:
        st.error(
            "🔴 **No se dimensionó** — la batería tiene datos físicamente imposibles "
            "en la hoja Catalogo_Baterias del Excel. Corrige y recarga:\n\n"
            + "\n".join(f"- {e}" for e in _val_bat["errores"])
        )
    elif not bat.get("capacidad_kWh"):
        st.error("❌ La batería seleccionada no tiene capacidad definida en el catálogo.")
    else:
        dim = dimensionar_bateria(bat, E_consumo_diario, autonomia_h)
        if "error" in dim:
            st.error(f"❌ {dim['error']}")
        else:
            st.session_state["bateria_dim"] = dim
            st.session_state["bateria_nombre"] = bat_sel
            st.session_state["bateria_dict"] = bat
            st.session_state["bateria_ok"] = True

# Mostrar resultado del dimensionamiento
dim_res = st.session_state.get("bateria_dim")
if dim_res and not dim_res.get("error"):
    st.success(f"✅ Dimensionamiento calculado — {st.session_state.get('bateria_nombre','')}")
    bat_nom = st.session_state.get("bateria_nombre", "—")

    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    col_r1.metric("Unidades requeridas", dim_res["N_baterias"])
    col_r2.metric("Capacidad instalada", f"{dim_res['C_instalada_kWh']:.1f} kWh")
    col_r3.metric("Capacidad útil (DoD+η)", f"{dim_res['C_util_kWh']:.1f} kWh")
    col_r4.metric("Vida estimada", f"{dim_res['vida_estimada_anos']} años")

    col_r5, col_r6, col_r7, col_r8 = st.columns(4)
    col_r5.metric("DoD real de operación", f"{dim_res['dod_real_pct']:.1f}%",
                  delta=f"Máx: {dim_res['dod_max_pct']}%", delta_color="off")
    col_r6.metric("Eficiencia RTE", f"{dim_res['eta_rte_pct']:.0f}%")
    col_r7.metric("Ciclos garantizados", f"{dim_res['ciclos_vida']:,}")
    if dim_res.get("costo_total_usd"):
        col_r8.metric("Costo total baterías",
                      f"USD {dim_res['costo_total_usd']:,.0f}",
                      delta=f"USD {dim_res['costo_unitario_usd']:,.0f}/unid", delta_color="off")
    else:
        col_r8.metric("Costo total baterías", "No disponible")

    for adv in dim_res.get("advertencias", []):
        st.warning(f"⚠️ {adv}")

    # ── #25 — Check potencia post-dimensionamiento ────────────────────────────
    # Una vez conocido N_baterias, verificar que la potencia total del banco no
    # supere la capacidad del inversor (cuello de botella de carga/descarga).
    _n_bat       = dim_res.get("N_baterias", 1)
    _p_bat_unit  = bat.get("potencia_kW") or 0
    _p_bat_total = _n_bat * _p_bat_unit
    _p_inv_w     = (_inv_dim.get("P_ac_nom_W") or _inv_dim.get("P_dc_max_W") or 0)
    _p_inv_kw    = _p_inv_w / 1000
    if _p_bat_total > 0 and _p_inv_kw > 0:
        _ratio = _p_bat_total / _p_inv_kw
        if _ratio > 1.5:
            st.error(
                f"🔴 **Potencia del banco sobredimensionada:** {_n_bat} × {_p_bat_unit:.1f} kW = "
                f"**{_p_bat_total:.1f} kW** vs inversor **{_p_inv_kw:.1f} kW**.  \n"
                f"El inversor limitará la carga/descarga a {_p_inv_kw:.1f} kW — "
                "considera reducir el número de unidades o usar un inversor de mayor potencia."
            )
        elif _ratio > 1.1:
            st.warning(
                f"⚠️ **Potencia del banco ({_p_bat_total:.1f} kW) supera la del inversor "
                f"({_p_inv_kw:.1f} kW) en {(_ratio-1)*100:.0f}%.** "
                "El inversor será el cuello de botella en picos de carga/descarga."
            )
        else:
            st.info(
                f"⚡ Potencia del banco: **{_p_bat_total:.1f} kW** "
                f"({_n_bat} × {_p_bat_unit:.1f} kW) — "
                f"dentro de la capacidad del inversor ({_p_inv_kw:.1f} kW)."
            )

    with st.expander("📐 Tabla de dimensionamiento detallada"):
        tabla_dim = {
            "Parámetro":  [
                "Modelo seleccionado", "Capacidad unitaria (kWh)", "Número de unidades",
                "Capacidad instalada total (kWh)", "Capacidad útil aprovechable (kWh)",
                "DoD real de operación (%)", "DoD máximo del fabricante (%)",
                "Eficiencia round-trip (%)", "Ciclos de vida garantizados",
                "Vida estimada de operación (años)", "Costo total baterías (USD)"
            ],
            "Valor": [
                bat_nom,
                dim_res["cap_unitaria_kWh"],
                dim_res["N_baterias"],
                dim_res["C_instalada_kWh"],
                dim_res["C_util_kWh"],
                f"{dim_res['dod_real_pct']:.1f}%",
                f"{dim_res['dod_max_pct']:.0f}%",
                f"{dim_res['eta_rte_pct']:.0f}%",
                f"{dim_res['ciclos_vida']:,}",
                dim_res["vida_estimada_anos"],
                f"USD {dim_res['costo_total_usd']:,.0f}" if dim_res.get("costo_total_usd") else "—",
            ],
        }
        st.table(pd.DataFrame(tabla_dim))

# ══════════════════════════════════════════════════════════════════════════════
# Comparador de TODAS las baterías del catálogo + Analista de Producción
# ══════════════════════════════════════════════════════════════════════════════
# A diferencia de 🧩 Comparador de Paneles / 🧭 Comparador de Orientación (páginas
# propias, hermanas de 4b), esto vive dentro de la misma página 11 -- batería ya
# tiene su propio flujo B-6 completo aquí (consumo/autonomía/inversor ya están
# en pantalla), así que un comparador separado solo duplicaría esos mismos
# widgets sin necesidad.
if tiene_catalogo:
    st.divider()
    st.subheader("🔍 Comparar todas las baterías del catálogo")
    st.caption(
        f"Dimensiona y evalúa compatibilidad con **{_inv_nombre or 'el inversor del proyecto'}** "
        f"para las {len(cat_bat)} baterías del catálogo, con el mismo consumo diario "
        f"({E_consumo_diario:.0f} kWh/día) y autonomía ({autonomia_h} h) configurados arriba."
    )

    from calculos.comparador_baterias import comparar_baterias, formatear_comparacion_baterias

    if st.button("▶️ Comparar baterías", type="primary", key="btn_comparar_baterias"):
        df_bat_cmp = comparar_baterias(
            cat_bat, _inv_dim, _inv_nombre, E_consumo_diario, autonomia_h,
        )
        st.session_state["_df_comparador_baterias"] = df_bat_cmp

    df_bat_cmp = st.session_state.get("_df_comparador_baterias")
    if df_bat_cmp is not None and not df_bat_cmp.empty:
        _cols_internas = [c for c in df_bat_cmp.columns if c.startswith("_")]
        st.dataframe(
            df_bat_cmp.drop(columns=_cols_internas).style.format({
                "N° unidades": "{:.0f}", "Capacidad instalada (kWh)": "{:,.1f}",
                "Capacidad útil (kWh)": "{:,.1f}", "DoD real (%)": "{:.1f}",
                "Vida estimada (años)": "{:.1f}", "Costo total (USD)": "{:,.0f}",
            }, na_rep="—"),
            use_container_width=True, hide_index=True,
        )
        st.caption(
            "Compatible: ✅ confirmado · ⚠️ el catálogo no tiene datos suficientes para "
            "confirmar (no es un sí garantizado) · ❌ incompatibilidad detectada."
        )

        st.download_button(
            "⬇️ Descargar comparativa (CSV)",
            df_bat_cmp.drop(columns=_cols_internas).to_csv(index=False).encode("utf-8-sig"),
            "comparativa_baterias.csv", "text/csv",
        )

        st.divider()
        st.subheader("🔍 Analista de Producción")
        st.caption(
            "Agente de IA (Claude) que lee SOLO la comparación de arriba — nunca inventa un "
            "número — y opina qué batería conviene implementar. Criterio técnico (autonomía, "
            "DoD, vida útil, compatibilidad de voltaje), no financiero: esa decisión sigue "
            "siendo del Asesor de Inversión, en 🤖 Análisis IA."
        )
        st.page_link(
            "pages/18_🤖_Análisis_IA.py",
            label="Ir al Analista Técnico-Financiero y al Asesor de Inversión (🤖 Análisis IA) →",
            icon="🤖",
        )
        st.caption(
            "Este botón hace una llamada real a la API y tiene un costo pequeño; "
            "no se ejecuta automáticamente."
        )
        import os as _os_ia
        if not _os_ia.environ.get("ANTHROPIC_API_KEY", "").strip():
            st.info(
                "Falta `ANTHROPIC_API_KEY` en el entorno del servidor para activar este agente "
                "(el resto de la página funciona igual sin ella). En el droplet: "
                "`export ANTHROPIC_API_KEY=\"sk-ant-...\"` → `pm2 restart streamlit-bipv "
                "--update-env` → `pm2 save`.",
                icon="🔑",
            )
        elif st.button("🔍 Ejecutar Analista de Producción", key="btn_analista_baterias"):
            with st.spinner("Consultando a Claude (Analista de Producción)…"):
                try:
                    from agentes.analista_produccion import (
                        ejecutar_analisis_produccion, texto_final as _texto_analista_prod,
                    )
                    _tipo_inst_bat = st.session_state.get("tipo_instalacion", "no especificado en el proyecto")
                    contexto = formatear_comparacion_baterias(df_bat_cmp, _tipo_inst_bat)
                    pregunta = (
                        "Analiza estas baterías y dame tu recomendación técnica sobre cuál "
                        "implementar para garantizar la autonomía configurada con la mejor "
                        "vida útil posible."
                    )
                    mensaje = ejecutar_analisis_produccion(contexto, pregunta=pregunta)
                    st.session_state["ia_bateria_texto"] = _texto_analista_prod(mensaje)
                    st.session_state["ia_bateria_uso"] = (
                        mensaje.usage.input_tokens, mensaje.usage.output_tokens,
                    )
                except Exception as e:
                    st.session_state["ia_bateria_texto"] = None
                    st.error(f"❌ {e}")

        if st.session_state.get("ia_bateria_texto"):
            st.markdown(st.session_state["ia_bateria_texto"])
            tin, tout = st.session_state.get("ia_bateria_uso", (0, 0))
            st.caption(f"🔢 {tin:,} tokens de entrada · {tout:,} de salida")
            if st.button("🗑️ Limpiar", key="btn_limpiar_analista_baterias"):
                st.session_state.pop("ia_bateria_texto", None)
                st.session_state.pop("ia_bateria_uso", None)
                st.rerun()
    elif df_bat_cmp is not None:
        st.error("Ninguna batería del catálogo pudo compararse — revisa el diagnóstico del catálogo arriba.")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# B-7 — Balance energético mensual + Clasificación
# ══════════════════════════════════════════════════════════════════════════════
st.header("📊 B-7 — Balance Energético Mensual y Clasificación")

# ── Sección consumo ──────────────────────────────────────────────────────────
st.subheader("1️⃣ Perfil de consumo del edificio")

modo_consumo = st.radio(
    "¿Cómo desea ingresar el consumo?",
    [
        "Consumo anual + perfil típico",
        "Ingresar 12 valores mensuales manualmente",
        "⏱️ Resolución horaria (más preciso)",
    ],
    horizontal=True,
    key="modo_consumo_b7",
)

# Consumo anual — prioridad: factura real de 🏠 Proyecto > estimado desde
# producción propia (E_ac × 1.2, supone algo de déficit) > default genérico.
# Corregido (2026-08-21): antes SIEMPRE se estimaba desde la producción,
# desconectado del consumo real que el usuario ya declaró en 🏠 Proyecto
# (modo "Conozco mi consumo/factura") -- mismo hallazgo que en B-6 arriba.
_consumo_mes_factura_b7 = float(st.session_state.get("consumo_kwh_mes", 0.0))
_consumo_anual_default_b7 = (
    round(_consumo_mes_factura_b7 * 12, 0) if _consumo_mes_factura_b7 > 0
    else max(e_ac_anual * 1.2, 10000.0)
)
if _consumo_mes_factura_b7 > 0:
    st.caption(
        f"📄 Consumo anual sugerido desde tu factura real (🏠 Proyecto): "
        f"**{_consumo_anual_default_b7:,.0f} kWh/año**."
    )

_modo_horario = (modo_consumo == "⏱️ Resolución horaria (más preciso)")

if modo_consumo == "Consumo anual + perfil típico":
    col_c1, col_c2 = st.columns([1, 1])
    with col_c1:
        consumo_anual_input = st.number_input(
            "Consumo anual total (kWh/año)",
            min_value=100.0,
            max_value=10_000_000.0,
            value=float(st.session_state.get("consumo_anual_edificio_kWh",
                        _consumo_anual_default_b7)),
            step=500.0,
            key="consumo_anual_edificio_kWh",
            help="Puede obtenerlo sumando 12 meses de facturas de energía.",
        )
    with col_c2:
        perfil_sel = st.selectbox(
            "Perfil de distribución mensual",
            list(PERFILES_TIPICOS.keys()),
            key="perfil_consumo_tipico",
            help="Distribución estacional del consumo. 'Uniforme' si no sabe.",
        )
    consumo_mensual_list = distribuir_consumo_anual(consumo_anual_input, perfil_sel)

elif _modo_horario:
    # ── Resolución horaria ────────────────────────────────────────────────────
    st.info(
        "⏱️ **Resolución horaria:** el balance se calcula hora a hora (8 760 puntos), "
        "cruzando la producción real de la fachada BIPV con el perfil de consumo típico "
        "del edificio. Los resultados son más conservadores y honestos que el balance mensual "
        "porque capturan el desfase temporal entre generación solar (9–16 h) y consumo nocturno."
    )
    col_h1, col_h2 = st.columns([1, 1])
    with col_h1:
        consumo_anual_input = st.number_input(
            "Consumo anual total (kWh/año)",
            min_value=100.0,
            max_value=10_000_000.0,
            value=float(st.session_state.get("consumo_anual_edificio_kWh",
                        _consumo_anual_default_b7)),
            step=500.0,
            key="consumo_anual_edificio_kWh",
            help="Puede obtenerlo sumando 12 meses de facturas de energía.",
        )
    with col_h2:
        perfil_horario_sel = st.selectbox(
            "Arquetipo de consumo horario",
            list(PERFILES_HORARIOS.keys()),
            key="perfil_horario_sel",
            help=(
                "Distribución típica del consumo a lo largo del día.\n\n"
                "• Oficina/Comercio: pico 9–18 h, casi nulo de noche.\n"
                "• Residencial: pico mañana y noche, bajo en horas de trabajo.\n"
                "• Industrial: turno diurno 6–18 h, mínimo nocturno.\n"
                "• Hospital/Institucional: carga relativamente plana las 24 h."
            ),
        )
    # Mostrar el perfil 24 h seleccionado
    with st.expander("👁️ Perfil horario seleccionado"):
        _p24 = PERFILES_HORARIOS[perfil_horario_sel]
        _diario_ref = float(st.session_state.get("consumo_anual_edificio_kWh",
                            _consumo_anual_default_b7)) / 365.0
        _fig_h = go.Figure()
        _fig_h.add_trace(go.Bar(
            x=list(range(24)),
            y=[v * _diario_ref for v in _p24],
            marker_color="#3498db",
            name="Consumo promedio (kWh/h)",
        ))
        _fig_h.update_layout(
            title=f"Perfil horario — {perfil_horario_sel}",
            xaxis_title="Hora del día",
            yaxis_title="Consumo promedio (kWh/h)",
            height=260, margin=dict(t=40, b=20),
            plot_bgcolor="white",
            xaxis=dict(tickmode="linear", dtick=2),
        )
        st.plotly_chart(_fig_h, use_container_width=True)
        st.caption(
            f"Consumo diario de referencia: **{_diario_ref:,.1f} kWh/día** "
            f"({_diario_ref * 365:,.0f} kWh/año ÷ 365)."
        )
    # Para que el flujo de abajo siga funcionando con consumo_anual_input definido
    consumo_anual_input = float(st.session_state.get(
        "consumo_anual_edificio_kWh", _consumo_anual_default_b7
    ))
    consumo_mensual_list = distribuir_consumo_anual(consumo_anual_input)

else:
    st.info("Ingrese el consumo de cada mes (kWh). Puede basarse en facturas históricas.")
    cols_mes = st.columns(6)
    consumo_mensual_list = []
    defaults_mens = st.session_state.get(
        "consumo_mensual_manual",
        [round(_consumo_anual_default_b7 / 12, 0)] * 12
    )
    for i, mes in enumerate(MESES):
        col = cols_mes[i % 6]
        val = col.number_input(
            mes, min_value=0.0, max_value=500_000.0,
            value=float(defaults_mens[i]),
            step=100.0, key=f"cons_mes_{i}"
        )
        consumo_mensual_list.append(val)
    st.session_state["consumo_mensual_manual"] = consumo_mensual_list

# Vista previa del consumo (solo para modos mensuales)
if not _modo_horario:
    with st.expander("👁️ Vista previa del perfil de consumo"):
        df_cons_prev = pd.DataFrame({
            "Mes": MESES,
            "Consumo (kWh)": [round(v, 0) for v in consumo_mensual_list],
        })
        fig_cons = px.bar(df_cons_prev, x="Mes", y="Consumo (kWh)",
                          title="Perfil de consumo mensual",
                          color_discrete_sequence=["#3498db"])
        fig_cons.update_layout(height=280, margin=dict(t=40, b=20))
        st.plotly_chart(fig_cons, use_container_width=True)
        st.caption(f"Total anual: **{sum(consumo_mensual_list):,.0f} kWh/año**")

# ── Calcular balance ─────────────────────────────────────────────────────────
st.subheader("2️⃣ Calcular balance")

# Acceso a datos horarios de producción (para modo resolución horaria)
_res_prod_dict  = st.session_state.get("res_produccion", {})
_df_horario_prod = _res_prod_dict.get("df_horario") if _res_prod_dict else None

_btn_label = (
    "▶️ Calcular balance horario (resolución hora a hora)"
    if _modo_horario else
    "▶️ Calcular balance energético mensual"
)
_btn_disabled = (
    (_df_horario_prod is None) if _modo_horario else (df_m_prod is None)
)
if _modo_horario and _df_horario_prod is None:
    st.warning(
        "⚠️ El balance horario requiere los datos de producción hora a hora. "
        "Complete la Página 6 — Producción Anual y vuelva aquí."
    )

if st.button(_btn_label, type="primary", disabled=_btn_disabled):
    _bat_dim_activo = (st.session_state.get("bateria_dim")
                       if (usa_bateria if tiene_catalogo else False)
                          and st.session_state.get("bateria_ok")
                       else None)

    if _modo_horario:
        # ── Balance horario ───────────────────────────────────────────────────
        try:
            _consumo_anual_h = float(st.session_state.get(
                "consumo_anual_edificio_kWh", _consumo_anual_default_b7
            ))
            _perfil_h = st.session_state.get("perfil_horario_sel", "Residencial")
            res_h = balance_horario(
                _df_horario_prod,
                _consumo_anual_h,
                _perfil_h,
                _bat_dim_activo,
            )
            metr  = res_h["metricas"]
            df_bal = res_h["df_balance_mensual"]
            clase  = clasificar_energia(metr["fraccion_solar_pct"])

            st.session_state["balance_mensual_df"]         = df_bal
            st.session_state["balance_horario_res"]        = res_h
            st.session_state["balance_metricas"]           = metr
            st.session_state["clasificacion_energetica"]   = clase
            st.session_state["fraccion_solar_pct"]         = metr["fraccion_solar_pct"]
            st.session_state["consumo_anual_edificio_kWh_calc"] = metr["E_consumo_anual_kWh"]
            st.session_state["balance_ok"]                 = True
            st.session_state["balance_modo"]               = "horario"
            st.success("✅ Balance horario calculado (8 760 horas simuladas)")

            # Mostrar comparación si también existe el balance mensual previo
            _metr_prev = st.session_state.get("_balance_mensual_metr_ref")
            if _metr_prev:
                _delta = metr["fraccion_solar_pct"] - _metr_prev["fraccion_solar_pct"]
                st.info(
                    f"📊 **Comparación mensual → horario:** "
                    f"Fracción solar mensual = {_metr_prev['fraccion_solar_pct']:.1f}% "
                    f"→ horario = {metr['fraccion_solar_pct']:.1f}% "
                    f"({'−' if _delta < 0 else '+'}{abs(_delta):.1f} pp). "
                    "El balance horario captura el desfase solar-nocturno y es más conservador."
                )
        except Exception as e:
            st.error(f"❌ Error en el cálculo horario: {e}")
    else:
        # ── Balance mensual (modo original) ───────────────────────────────────
        if df_m_prod is None:
            st.error("❌ No hay datos de producción mensual. Complete primero la Página 6.")
        else:
            try:
                df_bal = balance_mensual(df_m_prod, consumo_mensual_list, _bat_dim_activo)
                metr   = metricas_balance(df_bal)
                clase  = clasificar_energia(metr["fraccion_solar_pct"])

                st.session_state["balance_mensual_df"]       = df_bal
                st.session_state["balance_metricas"]         = metr
                st.session_state["clasificacion_energetica"] = clase
                st.session_state["fraccion_solar_pct"]       = metr["fraccion_solar_pct"]
                st.session_state["consumo_anual_edificio_kWh_calc"] = metr["E_consumo_anual_kWh"]
                st.session_state["balance_ok"]               = True
                st.session_state["balance_modo"]             = "mensual"
                # Guardar referencia para comparar con horario después
                st.session_state["_balance_mensual_metr_ref"] = metr
                st.success("✅ Balance calculado correctamente")
            except Exception as e:
                st.error(f"❌ Error en el cálculo: {e}")

# ── Mostrar resultados ───────────────────────────────────────────────────────
df_bal  = st.session_state.get("balance_mensual_df")
metr    = st.session_state.get("balance_metricas")
clase   = st.session_state.get("clasificacion_energetica")

if df_bal is not None and metr and clase:

    # ── Clasificación energética ────────────────────────────────────────────
    st.divider()
    st.subheader("3️⃣ Clasificación energética del edificio")

    col_cl1, col_cl2 = st.columns([1, 2])
    with col_cl1:
        color = clase["color_hex"]
        clase_letra = clase["clase"]
        frac = clase["fraccion_solar_pct"]
        st.markdown(
            f"""
            <div style="
                background:{color}22;
                border: 3px solid {color};
                border-radius: 16px;
                padding: 24px;
                text-align: center;
            ">
                <div style="font-size:64px; font-weight:900; color:{color};">
                    {clase_letra}
                </div>
                <div style="font-size:18px; font-weight:600; color:{color}; margin-top:4px;">
                    {clase['emoji']} {clase['descripcion']}
                </div>
                <div style="font-size:28px; font-weight:700; margin-top:12px;">
                    {frac:.1f}%
                </div>
                <div style="font-size:13px; color:#666;">
                    fracción solar (% consumo cubierto)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_cl2:
        st.markdown("**Tabla de clasificaciones energéticas**")
        df_clases = tabla_clasificaciones()
        # Resaltar la fila activa
        def _highlight_row(row):
            if row["Clase"].endswith(clase_letra) or clase_letra in row["Clase"]:
                return [f"background-color:{color}33; font-weight:bold"] * len(row)
            return [""] * len(row)
        st.dataframe(df_clases.style.apply(_highlight_row, axis=1),
                     use_container_width=True, hide_index=True)

    # ── KPIs anuales ────────────────────────────────────────────────────────
    st.divider()
    st.subheader("4️⃣ Indicadores anuales del balance")

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Producción solar",
              f"{metr['E_solar_anual_kWh']:,.0f} kWh/año")
    k2.metric("Consumo edificio",
              f"{metr['E_consumo_anual_kWh']:,.0f} kWh/año")
    k3.metric("Autoconsumo solar",
              f"{metr['E_autoconsumo_anual_kWh']:,.0f} kWh/año",
              delta=f"{metr['fraccion_solar_pct']:.1f}% del consumo")
    k4.metric("Excedente exportado",
              f"{metr['E_exportacion_anual_kWh']:,.0f} kWh/año",
              delta=f"{metr['tasa_autoconsumo_pct']:.1f}% autoc. solar")
    k5.metric("Déficit residual",
              f"{metr['E_deficit_anual_kWh']:,.0f} kWh/año",
              delta=f"Ratio solar/consumo: {metr['ratio_solar_consumo']:.2f}x",
              delta_color="off")

    if metr.get("E_bateria_total_kWh", 0) > 0:
        st.info(
            f"🔋 **Contribución batería:** {metr['E_bateria_total_kWh']:,.0f} kWh/año "
            f"(energía descargada que cubre consumo nocturno/déficit)"
        )

    # ── Gráfico de balance mensual ───────────────────────────────────────────
    st.divider()
    st.subheader("5️⃣ Balance mensual — Producción vs Consumo")

    fig = go.Figure()

    # Barras apiladas del autoconsumo
    fig.add_trace(go.Bar(
        name="Autoconsumo directo (solar→edificio)",
        x=df_bal["mes"], y=df_bal["autoconsumo_directo_kWh"],
        marker_color="#27ae60",
        hovertemplate="%{y:,.0f} kWh<extra>Autoconsumo directo</extra>",
    ))
    if df_bal["E_bateria_descargada_kWh"].sum() > 0:
        fig.add_trace(go.Bar(
            name="Batería → edificio",
            x=df_bal["mes"], y=df_bal["E_bateria_descargada_kWh"],
            marker_color="#2ecc71",
            hovertemplate="%{y:,.0f} kWh<extra>Batería → edificio</extra>",
        ))
    fig.add_trace(go.Bar(
        name="Déficit (de la red)",
        x=df_bal["mes"], y=df_bal["deficit_neto_kWh"],
        marker_color="#e74c3c",
        hovertemplate="%{y:,.0f} kWh<extra>Déficit (red)</extra>",
    ))
    fig.add_trace(go.Bar(
        name="Excedente exportado",
        x=df_bal["mes"], y=df_bal["exportacion_kWh"],
        marker_color="#f39c12", opacity=0.7,
        hovertemplate="%{y:,.0f} kWh<extra>Excedente exportado</extra>",
    ))

    # Línea de consumo total
    fig.add_trace(go.Scatter(
        name="Consumo edificio",
        x=df_bal["mes"], y=df_bal["E_consumo_kWh"],
        mode="lines+markers",
        line=dict(color="#2c3e50", width=2.5, dash="dot"),
        marker=dict(size=7),
        hovertemplate="%{y:,.0f} kWh<extra>Consumo</extra>",
    ))

    # Línea de producción solar
    fig.add_trace(go.Scatter(
        name="Producción solar (E_ac)",
        x=df_bal["mes"], y=df_bal["E_solar_kWh"],
        mode="lines+markers",
        line=dict(color="#e67e22", width=2.5),
        marker=dict(size=7, symbol="diamond"),
        hovertemplate="%{y:,.0f} kWh<extra>Producción solar</extra>",
    ))

    fig.update_layout(
        barmode="stack",
        title="Balance energético mensual — Autoconsumo · Déficit · Excedente",
        xaxis_title="Mes",
        yaxis_title="Energía (kWh)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=480,
        margin=dict(t=80, b=40),
        plot_bgcolor="white",
    )
    fig.update_xaxes(gridcolor="#f0f0f0")
    fig.update_yaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig, use_container_width=True)

    # ── Gráfico perfil diario promedio (solo en modo horario) ───────────────
    _res_h_disp = st.session_state.get("balance_horario_res")
    _balance_modo_disp = st.session_state.get("balance_modo", "mensual")
    if _balance_modo_disp == "horario" and _res_h_disp:
        st.divider()
        st.subheader("5b️⃣ Perfil energético diario promedio (hora a hora)")
        st.caption(
            "Promedio de las 8 760 horas simuladas, agrupadas por hora del día. "
            "Muestra el desfase entre la generación solar (pico 10–15 h) y el consumo del edificio."
        )
        _df_pd = _res_h_disp["df_perfil_diario"]
        _fig_pd = go.Figure()
        _fig_pd.add_trace(go.Scatter(
            x=_df_pd["hora"], y=_df_pd["solar_prom_kWh"],
            name="Producción solar promedio",
            fill="tozeroy", fillcolor="rgba(230,126,34,0.15)",
            line=dict(color="#e67e22", width=2.5),
            hovertemplate="%{y:.3f} kWh<extra>Solar</extra>",
        ))
        _fig_pd.add_trace(go.Scatter(
            x=_df_pd["hora"], y=_df_pd["consumo_prom_kWh"],
            name="Consumo promedio",
            line=dict(color="#2c3e50", width=2.5, dash="dot"),
            hovertemplate="%{y:.3f} kWh<extra>Consumo</extra>",
        ))
        _fig_pd.add_trace(go.Bar(
            x=_df_pd["hora"], y=_df_pd["autoconsumo_prom_kWh"],
            name="Autoconsumo horario promedio",
            marker_color="#27ae60", opacity=0.7,
            hovertemplate="%{y:.3f} kWh<extra>Autoconsumo</extra>",
        ))
        _fig_pd.add_trace(go.Bar(
            x=_df_pd["hora"], y=_df_pd["deficit_prom_kWh"],
            name="Déficit horario promedio (de la red)",
            marker_color="#e74c3c", opacity=0.6,
            hovertemplate="%{y:.3f} kWh<extra>Déficit</extra>",
        ))
        _fig_pd.update_layout(
            barmode="overlay",
            title=f"Perfil diario promedio — {_res_h_disp.get('perfil_tipo', '')}",
            xaxis=dict(title="Hora del día", tickmode="linear", dtick=2),
            yaxis_title="Energía promedio (kWh/h)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=400, margin=dict(t=80, b=40),
            plot_bgcolor="white",
        )
        _fig_pd.update_xaxes(gridcolor="#f0f0f0")
        _fig_pd.update_yaxes(gridcolor="#f0f0f0")
        st.plotly_chart(_fig_pd, use_container_width=True)

        # Indicadores de desfase
        _h_solar_peak = int(_df_pd.loc[_df_pd["solar_prom_kWh"].idxmax(), "hora"])
        _h_consumo_peak = int(_df_pd.loc[_df_pd["consumo_prom_kWh"].idxmax(), "hora"])
        _frac_solar_dia = (
            _df_pd[(_df_pd["hora"] >= 7) & (_df_pd["hora"] <= 18)]["solar_prom_kWh"].sum() /
            max(_df_pd["solar_prom_kWh"].sum(), 0.001) * 100
        )
        _frac_consumo_noche = (
            _df_pd[(_df_pd["hora"] < 7) | (_df_pd["hora"] > 18)]["consumo_prom_kWh"].sum() /
            max(_df_pd["consumo_prom_kWh"].sum(), 0.001) * 100
        )
        _c_des1, _c_des2, _c_des3 = st.columns(3)
        _c_des1.metric("Hora pico de generación", f"{_h_solar_peak:02d}:00 h")
        _c_des2.metric("Hora pico de consumo", f"{_h_consumo_peak:02d}:00 h")
        _c_des3.metric(
            "Desfase temporal",
            f"{abs(_h_consumo_peak - _h_solar_peak)} h",
            delta="Energía que necesita batería para cubrirse",
            delta_color="off",
        )
        st.caption(
            f"☀️ El **{_frac_solar_dia:.0f}%** de la generación solar ocurre entre 7–18 h. "
            f"El **{_frac_consumo_noche:.0f}%** del consumo ocurre fuera de ese rango (noche/madrugada). "
            "Sin batería, ese consumo nocturno proviene íntegramente de la red."
        )

    # ── Gráfico fracción solar mensual ──────────────────────────────────────
    fig2 = go.Figure()

    colores_bar = []
    for v in df_bal["fraccion_solar_pct"]:
        if v >= 90:   colores_bar.append("#2ecc71")
        elif v >= 75: colores_bar.append("#27ae60")
        elif v >= 50: colores_bar.append("#f39c12")
        elif v >= 25: colores_bar.append("#e67e22")
        else:         colores_bar.append("#e74c3c")

    fig2.add_trace(go.Bar(
        x=df_bal["mes"],
        y=df_bal["fraccion_solar_pct"],
        marker_color=colores_bar,
        text=[f"{v:.0f}%" for v in df_bal["fraccion_solar_pct"]],
        textposition="outside",
        name="Fracción solar mensual",
        hovertemplate="%{y:.1f}%<extra>Fracción solar</extra>",
    ))

    # Líneas de clasificación
    for umbral, clase_l, _, color_l, _ in [
        (90, "A+", "", "#2ecc71", ""),
        (75, "A",  "", "#27ae60", ""),
        (50, "B",  "", "#f39c12", ""),
        (25, "C",  "", "#e67e22", ""),
    ]:
        fig2.add_hline(
            y=umbral, line_dash="dash", line_color=color_l, line_width=1.5,
            annotation_text=f" {clase_l} ({umbral}%)",
            annotation_position="right",
        )

    fig2.update_layout(
        title="Fracción solar mensual — % del consumo cubierto por solar",
        xaxis_title="Mes",
        yaxis_title="Fracción solar (%)",
        yaxis=dict(range=[0, 115]),
        height=380,
        plot_bgcolor="white",
        margin=dict(t=60, b=40),
    )
    fig2.update_xaxes(gridcolor="#f0f0f0")
    fig2.update_yaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig2, use_container_width=True)

    # ── Tabla detallada ──────────────────────────────────────────────────────
    with st.expander("📋 Tabla detallada del balance mensual"):
        df_show = df_bal[[
            "mes", "E_solar_kWh", "E_consumo_kWh",
            "autoconsumo_directo_kWh", "E_bateria_descargada_kWh",
            "autoconsumo_total_kWh", "deficit_neto_kWh",
            "exportacion_kWh", "fraccion_solar_pct",
        ]].copy()
        df_show.columns = [
            "Mes", "Solar (kWh)", "Consumo (kWh)",
            "Autoconsumo directo", "Batería→edificio",
            "Autoconsumo total", "Déficit (red)", "Exportado", "Fracción solar (%)",
        ]
        # Fila de totales
        totales = {
            "Mes": "TOTAL",
            "Solar (kWh)": df_show["Solar (kWh)"].sum(),
            "Consumo (kWh)": df_show["Consumo (kWh)"].sum(),
            "Autoconsumo directo": df_show["Autoconsumo directo"].sum(),
            "Batería→edificio": df_show["Batería→edificio"].sum(),
            "Autoconsumo total": df_show["Autoconsumo total"].sum(),
            "Déficit (red)": df_show["Déficit (red)"].sum(),
            "Exportado": df_show["Exportado"].sum(),
            "Fracción solar (%)": round(metr["fraccion_solar_pct"], 1),
        }
        df_show = pd.concat([df_show, pd.DataFrame([totales])], ignore_index=True)
        st.dataframe(df_show.style.format({
            "Solar (kWh)": "{:,.0f}",
            "Consumo (kWh)": "{:,.0f}",
            "Autoconsumo directo": "{:,.0f}",
            "Batería→edificio": "{:,.0f}",
            "Autoconsumo total": "{:,.0f}",
            "Déficit (red)": "{:,.0f}",
            "Exportado": "{:,.0f}",
            "Fracción solar (%)": "{:.1f}%",
        }), use_container_width=True, hide_index=True)

    # ── Flujo de ahorro estimado ─────────────────────────────────────────────
    tarifa = float(st.session_state.get(
        "tarifa_cop_kwh",                        # clave canónica (Proyecto/Financiero)
        st.session_state.get("tarifa_cop_kWh", 650.0)  # fallback legacy
    ))
    if tarifa > 0 and metr["E_autoconsumo_anual_kWh"] > 0:
        ahorro_anual_cop = metr["E_autoconsumo_anual_kWh"] * tarifa
        tipo_cambio = float(st.session_state.get("tipo_cambio", 4100.0))
        ahorro_anual_usd = ahorro_anual_cop / tipo_cambio
        st.divider()
        st.subheader("6️⃣ Estimación de ahorro en factura")
        col_a1, col_a2, col_a3 = st.columns(3)
        col_a1.metric("Autoconsumo anual",
                      f"{metr['E_autoconsumo_anual_kWh']:,.0f} kWh")
        col_a2.metric("Ahorro anual estimado",
                      f"COP {ahorro_anual_cop / 1e6:,.1f}M",
                      delta=f"USD {ahorro_anual_usd:,.0f}")
        col_a3.metric("Ahorro mensual promedio",
                      f"COP {ahorro_anual_cop / 12 / 1e3:,.0f}K/mes")
        st.caption(
            f"Cálculo: {metr['E_autoconsumo_anual_kWh']:,.0f} kWh × "
            f"{tarifa:,.0f} COP/kWh = {ahorro_anual_cop/1e6:.2f} M COP/año. "
            "Tarifa y TRM tomadas de la página Financiero."
        )

    # ── Guardar en session_state para Financiero y Reporte ──────────────────
    st.session_state["balance_ok"]               = True
    st.session_state["fraccion_solar_pct"]       = metr["fraccion_solar_pct"]
    st.session_state["clasificacion_energetica"] = clase
    st.session_state["balance_metricas"]         = metr

    # Nota de integración con Financiero
    with st.expander("🔗 Integración con otras páginas"):
        st.markdown("""
| Página | Dato que recibe de esta página |
|---|---|
| **7 — Financiero** | `fraccion_solar_pct`, `E_autoconsumo_anual_kWh` para calcular LCOE con storage |
| **8 — Presupuesto** | `bateria_dim` → N baterías × costo unitario se suman al CAPEX |
| **10 — Reporte PDF** | Clase energética A+/A/B/C/D, tabla de balance, KPIs de autoconsumo |

Los valores se propagan automáticamente vía `session_state` cuando calcule en esta página primero.
        """)

else:
    if prod_ok and df_m_prod is not None:
        st.info("👆 Configure el perfil de consumo y haga clic en **Calcular balance energético mensual**")
