"""Página 3 — Motor I-V (SDM De Soto 2006).

Auto-activación: si el panel seleccionado en Dimensionamiento tiene ficha
suficiente (Voc, Isc, Vmp, Imp, N_s/NsA), el motor carga y ejecuta
automáticamente sin que el usuario tenga que hacer nada.
"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go

from calculos.modelo_iv import (
    resolver_curva_iv,
    validar_sdm_vs_ficha,
    tiene_sdm_completo,
    estimar_sdm_desde_ficha,
    verificar_ns_halfcut,
)
from calculos.panel_iv_check import analizar_panel_motiv as _analizar_panel_motiv
from calculos.temperatura import temperatura_celda_noct
from datos.tecnologias_bipv import ASP_ST1_T40, MODULOS_BIPV
from datos.catalogo_paneles_excel import cargar_catalogo_paneles

st.set_page_config(page_title="Motor IV — BIPV", page_icon="🔬", layout="wide")
st.title("🔬 Motor I-V — Modelo De Soto 2006")
st.caption("Equivalente Python de SimuladorIV_CdTe_v2 + Mod_ModeloDiodo (VBA auditado)")

# ═══════════════════════════════════════════════════════════════════════════════
# 1. DETECCIÓN AUTOMÁTICA DEL PANEL DESDE DIMENSIONAMIENTO
# ═══════════════════════════════════════════════════════════════════════════════

_panel_ss       = st.session_state.get("panel_dict")
_panel_nom_ss   = st.session_state.get("panel_nombre_dim", "")

_modo_auto      = False   # True si se usa el panel del Dimensionamiento
_panel_activo   = None    # dict que se usará en el motor
_estimado       = False   # True si se usaron parámetros estimados
_metodo_est     = ""

if _panel_ss and _panel_nom_ss:
    if tiene_sdm_completo(_panel_ss):
        # ── Ficha SDM calibrada (ej. ASP-ST1-T40 de MODULOS_BIPV) ─────────────
        _modo_auto   = True
        _panel_activo = _panel_ss
        _estimado    = False
        st.success(
            f"⚡ **Auto-activado** — Panel detectado en Dimensionamiento: "
            f"**{_panel_nom_ss}** · parámetros SDM calibrados."
        )
    else:
        # ── Ficha básica (catálogo Excel) → estimar SDM ────────────────────────
        _err_auto, _adv_auto = _analizar_panel_motiv(_panel_ss)
        if _err_auto:
            # Campos esenciales ausentes — no se puede estimar
            _falt_str = ", ".join(f"**{c}**" for c, _ in _err_auto)
            st.error(
                f"❌ **Panel `{_panel_nom_ss}` no tiene datos suficientes para el Motor IV.**  \n"
                f"Campos requeridos ausentes en el catálogo Excel: {_falt_str}.  \n\n"
                "| Campo | Descripción |\n|---|---|\n"
                + "\n".join(f"| `{c}` | {d} |" for c, d in _err_auto)
                + f"\n\n⬇️ Se usará el panel por defecto **ASP-ST1-T40** para esta simulación."
            )
            # _panel_activo queda None → caerá al default más abajo, pero ahora avisado
        else:
            _sdm_est = estimar_sdm_desde_ficha(_panel_ss)
            if _sdm_est is not None:
                _modo_auto    = True
                _panel_activo = _sdm_est
                _estimado     = True
                _metodo_est   = _sdm_est.get("_metodo", "estimado")
                _adv_lines = ""
                if _adv_auto:
                    _adv_lines = "  \n" + "  \n".join(
                        f"- ⚠️ `{c}` no definido — {d}" for c, d in _adv_auto
                    )
                st.warning(
                    f"🟡 **Auto-activado con estimación** — Panel: **{_panel_nom_ss}** "
                    f"(catálogo Excel). Parámetros SDM estimados por **{_metodo_est}** "
                    f"desde ficha técnica. Resultados orientativos.{_adv_lines}"
                )
                # ── #67 — Aviso si N_s fue corregido por half-cut ────────────
                if _sdm_est.get("_ns_corregido"):
                    _hci = _sdm_est.get("_ns_halfcut_info", {})
                    st.error(
                        f"🔺 **N_s corregido automáticamente (half-cut):**  \n"
                        f"El catálogo tiene N_s = **{_sdm_est['_ns_original']}** "
                        f"(Voc/celda = {_hci.get('Voc_por_celda', '?'):.3f} V, "
                        f"fuera del rango {_hci.get('rango_esperado', ('?','?'))[0]:.2f}–"
                        f"{_hci.get('rango_esperado', ('?','?'))[1]:.2f} V para "
                        f"{_hci.get('tecnologia', '?')}).  \n"
                        f"Se usó **N_s = {_sdm_est['_N_s_usado']}** para el SDM.  \n"
                        f"⚠️ Para que todos los motores sean consistentes, corrige "
                        f"`Ns (Celdas Serie)` = **{_sdm_est['_N_s_usado']}** en la hoja "
                        f"`Catalogo_Paneles_FV` del Excel."
                    )
            else:
                st.error(
                    f"❌ **No se pudo estimar el SDM para `{_panel_nom_ss}`.**  \n"
                    "Los datos básicos (Voc, Isc, Vmp, Imp) están presentes pero el ajuste "
                    "De Soto no convergió. Verifica que los valores sean físicamente coherentes "
                    "(Vmp < Voc, Imp < Isc, Pmax = Vmp × Imp).  \n"
                    "⬇️ Se usará el panel por defecto **ASP-ST1-T40** para esta simulación."
                )

# ── Selector manual como alternativa / fallback ────────────────────────────────
# Combinar catálogo SDM calibrado (BIPV ASP-ST1) + catálogo Excel por tecnología
_cat_excel = {}
try:
    _cat_excel = cargar_catalogo_paneles()
except Exception:
    _cat_excel = {}

_opciones_sdm   = list(MODULOS_BIPV.keys())
_opciones_excel = [k for k in _cat_excel if k not in MODULOS_BIPV]

# ── Función auxiliar: comprobar si un panel Excel tiene datos IV completos ──────
def _tiene_iv(panel_dict: dict) -> bool:
    voc = panel_dict.get("Voc") or panel_dict.get("V_oc_ref") or 0
    isc = panel_dict.get("Isc") or panel_dict.get("I_sc_ref") or 0
    vmp = panel_dict.get("Vmp") or panel_dict.get("V_mp_ref") or 0
    imp = panel_dict.get("Imp") or panel_dict.get("I_mp_ref") or 0
    return float(voc) > 10 and float(isc) > 0.1 and float(vmp) > 5 and float(imp) > 0.05

# ── Agrupar paneles Excel por tecnología (tarea #84) ────────────────────────────
from collections import defaultdict as _ddict
_tech_groups: dict = _ddict(list)
for _k in _opciones_excel:
    _tech = (_cat_excel.get(_k) or {}).get("tecnologia") or "Otros"
    _tech_groups[_tech.strip()].append(_k)

_TECH_ORDER = ["CdTe", "CIGS", "Mono-Si", "Poli-Si"]

# Lista combinada: ASP-ST1 primero, luego grupos por tecnología
_opciones_all = ["── BIPV ASP-ST1 (SDM calibrado) ──"] + _opciones_sdm
for _t in _TECH_ORDER:
    if _tech_groups.get(_t):
        _opciones_all += [f"── {_t} (SDM estimado) ──"] + _tech_groups[_t]
for _t, _plist in sorted(_tech_groups.items()):
    if _t not in _TECH_ORDER:
        _opciones_all += [f"── {_t} ──"] + _plist

# ── format_func: agrega ✅/⚠️ y potencia al nombre (tarea #85) ─────────────────
def _fmt_panel(name: str) -> str:
    if name.startswith("──"):
        return name
    if name in MODULOS_BIPV:
        p = MODULOS_BIPV[name]
        return f"✅ {name} — {p.get('Pmax_stc', '?')} W (SDM calibrado)"
    p = _cat_excel.get(name, {})
    ok   = _tiene_iv(p)
    pmax = p.get("Pmax_stc") or 0
    wpstr = f" — {pmax:.0f} W" if pmax else ""
    badge = "✅" if ok else "⚠️"
    return f"{badge} {name}{wpstr}"

# Contadores para caption
_n_completos = sum(1 for k in _opciones_excel if _tiene_iv(_cat_excel.get(k, {})))
_n_incompletos = len(_opciones_excel) - _n_completos

st.markdown("---")
with st.expander(
    "🔧 Seleccionar panel manualmente" if _modo_auto else "🔬 Seleccionar panel",
    expanded=not _modo_auto,
):
    st.caption(
        f"✅ {len(_opciones_sdm)} BIPV ASP-ST1 (SDM calibrado) · "
        f"✅ {_n_completos} catálogo Excel con datos IV completos · "
        f"⚠️ {_n_incompletos} catálogo Excel con datos incompletos"
    )
    _panel_manual_nom = st.selectbox(
        "Panel del catálogo interno",
        _opciones_all,
        index=_opciones_all.index("ASP-ST1-T40") if "ASP-ST1-T40" in _opciones_all else 1,
        format_func=_fmt_panel,
        key="motor_iv_panel_manual",
    )

    _es_separador = _panel_manual_nom.startswith("──")
    if _es_separador:
        st.info("☝️ Selecciona un panel de la lista (no el encabezado de grupo).")
    elif _panel_manual_nom in MODULOS_BIPV:
        st.success("✅ SDM calibrado — parámetros completos y verificados.")
    else:
        _p_sel = _cat_excel.get(_panel_manual_nom, {})
        _err_sel, _adv_sel = _analizar_panel_motiv(_p_sel)
        if _err_sel:
            st.error(
                f"❌ **Datos insuficientes para simular `{_panel_manual_nom}`.**  \n"
                "Campos requeridos ausentes en el catálogo Excel:\n\n"
                "| Campo | Descripción |\n|---|---|\n"
                + "\n".join(f"| `{c}` | {d} |" for c, d in _err_sel)
                + "\n\nCompleta estos campos en la hoja `Catalogo_Paneles` del Excel antes de usar este panel."
            )
        else:
            _msg_adv = ""
            if _adv_sel:
                _msg_adv = "  \n" + "  \n".join(
                    f"- ⚠️ `{c}` ausente — {d}" for c, d in _adv_sel
                )
            st.warning(
                f"🟡 **Catálogo Excel** — SDM estimado desde ficha. Resultados orientativos.{_msg_adv}"
            )

    if st.button("▶️ Usar este panel", key="btn_panel_manual", disabled=_es_separador):
        if _panel_manual_nom in MODULOS_BIPV:
            _panel_activo = MODULOS_BIPV[_panel_manual_nom]
            _estimado     = False
        else:
            from calculos.modelo_iv import estimar_sdm_desde_ficha
            _base = _cat_excel.get(_panel_manual_nom, {})
            if not _tiene_iv(_base):
                _err_btn, _ = _analizar_panel_motiv(_base)
                _falt_btn = ", ".join(f"`{c}`" for c, _ in _err_btn) if _err_btn else "Voc, Isc, Vmp o Imp"
                st.error(
                    f"❌ **{_panel_manual_nom}** — faltan campos requeridos: {_falt_btn}.  \n"
                    "Completa la ficha en la hoja `Catalogo_Paneles` del Excel."
                )
                _panel_activo = None
            else:
                _sdm = estimar_sdm_desde_ficha(_base)
                if _sdm:
                    _panel_activo = _sdm
                    _estimado     = True
                    _metodo_est   = _sdm.get("_metodo", "estimado")
                else:
                    st.error(f"❌ No se pudo estimar SDM para **{_panel_manual_nom}**.")
                    _panel_activo = None
        if _panel_activo is not None:
            _modo_auto    = True
            _panel_nom_ss = _panel_manual_nom
            st.success(f"✅ Panel cargado: **{_panel_manual_nom}**")

# Si aún no hay panel activo, usar el default con aviso explícito
if _panel_activo is None:
    _panel_activo = ASP_ST1_T40
    _panel_nom_ss = "ASP-ST1-T40"
    _estimado     = False
    if _panel_ss and st.session_state.get("panel_nombre_dim"):
        # El usuario tenía un panel seleccionado pero no pudo cargarse
        st.warning(
            f"⚠️ No se pudo cargar **{st.session_state.get('panel_nombre_dim')}** — "
            "la simulación está usando el panel de referencia **ASP-ST1-T40 (SDM calibrado)**.  \n"
            "Selecciona manualmente un panel con ficha completa en el selector de abajo."
        )

# ═══════════════════════════════════════════════════════════════════════════════
# 2. CONDICIONES DE SIMULACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("⚙️ Condiciones de simulación")

col1, col2 = st.columns([1, 2])

with col1:
    G     = st.slider("Irradiancia G (W/m²)", 50, 1200, 1000, step=25, key="iv_G")
    T_amb = st.slider("T_ambiente (°C)", 0, 40, 20, key="iv_Tamb")
    NOCT  = st.slider(
        "NOCT (°C)",
        35, 55,
        int(_panel_activo.get("NOCT") or 45),
        key="iv_NOCT",
    )
    T_cel = float(temperatura_celda_noct(G, T_amb, NOCT))
    st.metric("T_celda calculada", f"{T_cel:.1f} °C")

    st.markdown("---")
    st.subheader("Parámetros SDM @ STC")
    if _estimado:
        st.caption("⚠️ Estimados — no calibrados")
    _prec = 3 if _estimado else 2
    st.code(
        f"Iph  = {_panel_activo['I_L_ref']:.{_prec}f} A\n"
        f"I0   = {_panel_activo['I_o_ref']:.2e} A\n"
        f"Rs   = {_panel_activo['R_s']:.{_prec}f} Ω\n"
        f"Rsh  = {_panel_activo['R_sh_ref']:.1f} Ω\n"
        f"nNsVt= {_panel_activo['a_ref']:.4f} V\n"
        f"Tec  = {_panel_activo.get('tecnologia','—')}"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# 3. CURVA I-V (AUTO-RUN)
# ═══════════════════════════════════════════════════════════════════════════════

with col2:
    res = resolver_curva_iv(G, T_cel, _panel_activo, n_puntos=150)

    if res["V"] is not None:
        fig = go.Figure()
        V_arr = np.array(res["V"])
        I_arr = np.array(res["I"])
        P_arr = V_arr * I_arr

        fig.add_trace(go.Scatter(
            x=V_arr, y=I_arr, name="I-V",
            line=dict(color="#1F497D", width=2.5),
        ))
        fig.add_trace(go.Scatter(
            x=V_arr, y=P_arr, name="P-V",
            yaxis="y2", line=dict(color="#E07B00", width=2, dash="dash"),
        ))
        fig.add_vline(x=res["Vmp"], line_dash="dot", line_color="green",
                      annotation_text=f"Vmp={res['Vmp']:.1f}V")
        fig.add_vline(x=res["Voc"], line_dash="dot", line_color="red",
                      annotation_text=f"Voc={res['Voc']:.1f}V")
        fig.update_layout(
            title=(
                f"{_panel_nom_ss} — G={G} W/m², T_cel={T_cel:.1f}°C"
                + (" (estimado)" if _estimado else "")
            ),
            xaxis_title="Tensión (V)",
            yaxis_title="Corriente (A)",
            yaxis2=dict(title="Potencia (W)", overlaying="y", side="right"),
            height=400,
            legend=dict(x=0.02, y=0.98),
        )
        st.plotly_chart(fig, use_container_width=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Voc",  f"{res['Voc']:.2f} V")
    m2.metric("Isc",  f"{res['Isc']:.4f} A")
    m3.metric("Vmp",  f"{res['Vmp']:.2f} V")
    m4.metric("Pmax", f"{res['Pmax']:.2f} W")
    m5.metric("FF",   f"{res['FF']*100:.2f} %")

    # Comparación vs ficha cuando hay datos de referencia
    if _panel_activo.get("Pmax_stc") and _panel_activo.get("Voc_stc"):
        _err_p = abs(res["Pmax"] - _panel_activo["Pmax_stc"]) / _panel_activo["Pmax_stc"] * 100
        _err_v = abs(res["Voc"]  - _panel_activo["Voc_stc"])  / _panel_activo["Voc_stc"]  * 100
        _icono = "✅" if max(_err_p, _err_v) < 5 else "⚠️"
        st.caption(
            f"{_icono} vs ficha STC — "
            f"Pmax: {res['Pmax']:.1f} W vs {_panel_activo['Pmax_stc']:.1f} W "
            f"(err {_err_p:.1f}%) | "
            f"Voc: {res['Voc']:.1f} V vs {_panel_activo['Voc_stc']:.1f} V "
            f"(err {_err_v:.1f}%)"
        )

# ═══════════════════════════════════════════════════════════════════════════════
# 4. VALIDACIÓN FORMAL (solo paneles con SDM calibrado)
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("✅ Validación SDM vs Ficha Técnica")

if _estimado:
    st.info(
        "ℹ️ La validación formal requiere parámetros SDM calibrados. "
        "Este panel usa estimación — los errores pueden superar el 5 %. "
        "Para validar exactamente, agrega los parámetros calibrados al catálogo Excel."
    )
else:
    if st.button("Ejecutar validación (G=1000 W/m², T=25°C)", key="btn_validar"):
        val = validar_sdm_vs_ficha(_panel_activo)
        for param, datos in val.items():
            if param == "validacion_ok":
                continue
            icono = "✅" if datos["ok"] else "❌"
            st.write(
                f"{icono} **{param}**: calculado={datos['calculado']} | "
                f"ficha={datos['referencia']} | error={datos['error_pct']}%"
            )
        if val["validacion_ok"]:
            st.success("✅ SDM validado — error < 5% en todos los parámetros")
        else:
            st.error("❌ Revisar calibración SDM")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. CURVA FF vs IRRADIANCIA
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("📈 Curva FF vs Irradiancia (validación VBA)")
if st.button("Generar curva FF vs G (T=25°C isotérmico)", key="btn_ff_g"):
    Gs_plot  = list(range(50, 1050, 25))
    FFs_plot = [
        resolver_curva_iv(G_i, 25.0, _panel_activo, n_puntos=0)["FF"] * 100
        for G_i in Gs_plot
    ]
    fig2 = go.Figure(go.Scatter(
        x=Gs_plot, y=FFs_plot,
        mode="lines+markers", line=dict(color="#1F497D"),
        name=_panel_nom_ss,
    ))
    if not _estimado:
        # Puntos de referencia del VBA (solo válidos para ASP-ST1-T40 CdTe)
        vba_G  = [100, 200, 400, 600, 800, 1000]
        vba_FF = [69.75, 76.28, 74.51, 72.87, 71.55, 64.92]
        fig2.add_trace(go.Scatter(
            x=vba_G, y=vba_FF, mode="markers",
            name="VBA (referencia CdTe)",
            marker=dict(color="red", size=10, symbol="x"),
        ))
    fig2.update_layout(
        title="FF vs G — De Soto 2006" + (" (estimado)" if _estimado else " + Rsh exp CdTe"),
        xaxis_title="G (W/m²)", yaxis_title="FF (%)", height=350,
    )
    st.plotly_chart(fig2, use_container_width=True)
    if not _estimado:
        st.caption(
            "Los puntos rojos ✕ son los valores del VBA. "
            "Las líneas azules son el resultado de Python."
        )
