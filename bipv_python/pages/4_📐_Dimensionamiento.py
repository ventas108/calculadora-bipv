"""Página 4 — Dimensionamiento de strings."""
import math
import streamlit as st

from calculos.auth import requerir_login
requerir_login()
import pandas as pd
import plotly.graph_objects as go
from calculos.dimensionamiento import optimizar_n_serie, dimensionar_sistema
from calculos.modelo_iv import preparar_panel_iv, resolver_curva_iv
from datos.tecnologias_bipv import MODULOS_BIPV
from datos.catalogo_paneles_excel import cargar_catalogo_excel, obtener_panel_excel
from datos.catalogo_inversores_excel import cargar_catalogo_inversores, obtener_inversor_excel
from datos.catalogo_inversores import INVERSORES, seleccionar_inversor
from calculos.panel_iv_check import analizar_panel_motiv as _check_iv_dim

st.set_page_config(page_title="Dimensionamiento — BIPV", page_icon="📐", layout="wide")
from utils.ui import bloquear_traduccion
bloquear_traduccion()
st.title("📐 Dimensionamiento de Strings")
st.caption("Equivalente de Mod_OptimizarStringSizing + Mod_CalculoStringSizing (VBA)")

col1, col2 = st.columns(2)

with col1:
    _cat_excel = cargar_catalogo_excel()
    _lista_paneles = list(_cat_excel.keys()) if _cat_excel else list(MODULOS_BIPV.keys())
    _idx_default = _lista_paneles.index("ASP-ST1-T40") if "ASP-ST1-T40" in _lista_paneles else 0
    # #118 — badge ✅/⚠️ en la lista (mismo criterio que Motor IV: faltan Voc/Isc/Vmp/Imp)
    def _fmt_panel_dim(name: str) -> str:
        _p = (_cat_excel.get(name) if _cat_excel else None) or MODULOS_BIPV.get(name) or {}
        _err, _ = _check_iv_dim(_p)
        return f"{'⚠️' if _err else '✅'} {name}"
    panel_nombre   = st.selectbox("Panel", _lista_paneles, index=_idx_default,
                                  format_func=_fmt_panel_dim)
    _cat_inv = cargar_catalogo_inversores()
    _lista_inv = list(_cat_inv.keys()) if _cat_inv else list(INVERSORES.keys())
    _idx_inv = next((i for i,k in enumerate(_lista_inv) if "MID15KTL3" in k or "MID 15KTL3" in k), 0)
    inversor_nombre = st.selectbox("Inversor", _lista_inv, index=_idx_inv)

# Cargar dicts antes de col2 para que estén disponibles al calcular N_min_scan
panel    = obtener_panel_excel(panel_nombre) if _cat_excel else MODULOS_BIPV[panel_nombre]
inversor = obtener_inversor_excel(inversor_nombre) if _cat_inv else seleccionar_inversor(inversor_nombre)

# ── Aviso Motor IV: panel sin datos IV suficientes (#118) ─────────────────────
_iv_err, _iv_adv = _check_iv_dim(panel)
if _iv_err:
    _falt = ", ".join(f"`{c}`" for c, _ in _iv_err)
    st.warning(
        f"⚠️ **{panel_nombre}** no tiene datos IV suficientes para Motor IV.  \n"
        f"Campos requeridos ausentes: {_falt}.  \n"
        f"El dimensionamiento eléctrico funcionará, pero la curva I-V no podrá "
        f"simularse en Motor IV. Completa el catálogo Excel con estos valores."
    )
elif _iv_adv:
    _adv_campos = [c for c, _ in _iv_adv if not c.startswith("⚠️")]
    if _adv_campos:
        st.info(
            f"ℹ️ **{panel_nombre}** puede simularse en Motor IV con estimaciones.  \n"
            f"Campos opcionales ausentes: {', '.join(f'`{c}`' for c in _adv_campos)} "
            f"— se usarán defaults por tecnología."
        )

# ── Auto-población de temperaturas desde TMY ──────────────────────────────────
# Se recalcula SOLO cuando cambia el origen de datos climáticos (nueva ciudad/TMY).
# Una vez aplicado para una ciudad, el usuario puede editar libremente los campos.
_tmy_df    = st.session_state.get("tmy_df")
_ciudad_ss = st.session_state.get("tmy_ciudad", "")
_ciudad_applied = st.session_state.get("_dim_tmy_ciudad_ref", None)
_temp_auto_info = None

if _tmy_df is not None and _ciudad_ss and _ciudad_ss != _ciudad_applied:
    try:
        _noct    = float(panel.get("NOCT", 45.0))
        _t2m     = _tmy_df["T2m"] if "T2m" in _tmy_df.columns else _tmy_df.iloc[:, 0]
        _t_min   = round(float(_t2m.min()), 1)
        _t_p95   = round(float(_t2m.quantile(0.95)), 1)
        _t_max   = round(float(_t2m.max()), 1)
        # T_celda = T_amb + (NOCT-20)/800 * G  (fórmula Mod_TemperaturasDiseno VBA)
        _t_real  = round(_t_p95 + (_noct - 20.0) / 800.0 * 800.0, 1)   # G=800 W/m²
        _t_extr  = round(_t_max + (_noct - 20.0) / 800.0 * 1000.0, 1)  # G=1000 W/m²
        # Pre-poblar session_state ANTES de renderizar los widgets
        st.session_state["T_min_diseno"]       = _t_min
        st.session_state["T_cel_realista"]     = _t_real
        st.session_state["T_cel_extremo"]      = _t_extr
        st.session_state["_dim_tmy_ciudad_ref"] = _ciudad_ss
        _temp_auto_info = (
            f"🌡️ Temperaturas actualizadas desde TMY **{_ciudad_ss}** — "
            f"T_mín: {_t_min}°C · T_celda realista: {_t_real}°C · T_celda extremo: {_t_extr}°C "
            f"(NOCT {_noct}°C del panel)"
        )
    except Exception:
        pass  # Si falla, usa defaults anteriores sin interrumpir

with col2:
    T_frio   = st.number_input("T_mín diseño (°C)", value=float(
                                st.session_state.get("T_min_diseno", 5.0)),
                key="T_min_diseno",
                help="Auto-calculado como mínimo histórico del TMY. Determina Voc_max y riesgo sobre Vdc_max del inversor.")
    T_real   = st.number_input("T_celda caliente realista (°C)", value=float(
                                st.session_state.get("T_cel_realista", 36.35)),
                key="T_cel_realista",
                help="T_amb P95 + (NOCT-20)/800×800 W/m². Determina Vmp de operación habitual.")
    T_extr   = st.number_input("T_celda caliente extremo (°C)", value=float(
                                st.session_state.get("T_cel_extremo", 41.94)),
                key="T_cel_extremo",
                help="T_amb máxima histórica + (NOCT-20)/800×1000 W/m². Determina Vmp mínimo (peor caso MPPT).")
    N_str_tr = st.number_input("N_strings por tracker (via combinadoras)", value=int(st.session_state.get("N_str_tr", 1)), min_value=1, key="N_str_tr")
    col_nm1, col_nm2 = st.columns(2)
    with col_nm1:
        # Auto-calcular N_min eléctrico desde MPPT del inversor para evitar que
        # un restart resetee a 5 y el optimizador proponga N inviables para el MPPT
        _vmppt_min  = inversor.get("Vmppt_min") or inversor.get("Vmppt_activo_min") or 0
        _vmp_panel  = panel.get("Vmp_stc") or panel.get("Vmp") or 1
        _n_min_elec = max(1, math.ceil(_vmppt_min / _vmp_panel)) if _vmppt_min else 5
        _n_min_def  = max(_n_min_elec, int(st.session_state.get("N_min_scan", _n_min_elec)))
        N_min_scan = st.number_input(
            f"N mínimo a explorar (eléctrico: {_n_min_elec})",
            value=_n_min_def, min_value=1, max_value=40, key="N_min_scan",
            help=f"Calculado como ⌈Vmppt_min({_vmppt_min}V) / Vmp_panel({_vmp_panel:.1f}V)⌉ = {_n_min_elec}"
        )
    with col_nm2:
        N_max_scan = st.number_input("N máximo a explorar", value=int(st.session_state.get("N_max_scan", 20)), min_value=2, max_value=40, key="N_max_scan")

# Caption estable de temperaturas (siempre presente → evita removeChild de React)
_tmy_applied = st.session_state.get("_dim_tmy_ciudad_ref", "")
if _tmy_applied:
    st.caption(
        f"🌡️ Temperaturas desde TMY **{_tmy_applied}** — "
        f"T_mín: {T_frio:.1f}°C · T_cel realista: {T_real:.1f}°C · "
        f"T_cel extremo: {T_extr:.1f}°C  "
        f"*(NOCT {panel.get('NOCT', 45.0):.0f}°C · editable manualmente)*"
    )

# (panel e inversor ya cargados arriba)
if panel.get("costo_usd"):
    st.session_state["costo_modulo_usd"] = panel["costo_usd"]

# ── Indicador completitud ficha técnica ───────────────────────────────────────
_iv_params  = ["Voc", "Vmp", "Isc", "Imp", "N_s", "NsA"]
_faltantes  = [k for k in _iv_params if not panel.get(k)]
if not _faltantes:
    st.success("🟢 Ficha completa — Motor IV se activará automáticamente")
elif len(_faltantes) <= 2:
    st.warning(f"🟡 Ficha parcial — faltan: {', '.join(_faltantes)} | Motor IV usará estimación")
else:
    st.error(f"🔴 Ficha incompleta — faltan: {', '.join(_faltantes)} | solo cálculo energético")
if panel.get("notas"):
    st.caption(f"📋 {panel['notas'][:120]}")

# ── Motor IV automático — curva IV real para paneles 🟢 ───────────────────────
if not _faltantes:  # panel 🟢: tiene Voc, Vmp, Isc, Imp, N_s, NsA
    _panel_iv = preparar_panel_iv(panel)
    if _panel_iv is not None:
        with st.expander("📈 Curva I-V real (Motor IV activado automáticamente)", expanded=False):
            _col_iv1, _col_iv2 = st.columns(2)
            with _col_iv1:
                _G_iv = st.slider("Irradiancia (W/m²)", 100, 1200, 1000, 100, key="iv_G")
                _T_iv = st.slider("T celda (°C)", 15, 75, 25, 5, key="iv_T")
            try:
                _res = resolver_curva_iv(float(_G_iv), float(_T_iv), _panel_iv, n_puntos=200)
                if _res["V"] is not None:
                    _V = _res["V"]
                    _I = _res["I"]
                    _P = _V * _I

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=list(_V), y=list(_I),
                        name="I-V", line=dict(color="#1f77b4", width=2),
                        yaxis="y1",
                    ))
                    fig.add_trace(go.Scatter(
                        x=list(_V), y=list(_P),
                        name="P-V", line=dict(color="#ff7f0e", width=2, dash="dash"),
                        yaxis="y2",
                    ))
                    # Punto MPP
                    fig.add_trace(go.Scatter(
                        x=[_res["Vmp"]], y=[_res["Pmax"]],
                        name=f"MPP ({_res['Pmax']:.1f} W)",
                        mode="markers",
                        marker=dict(size=10, color="red", symbol="star"),
                        yaxis="y2",
                    ))
                    fig.update_layout(
                        xaxis_title="Voltaje (V)",
                        yaxis=dict(title="Corriente (A)", side="left"),
                        yaxis2=dict(title="Potencia (W)", side="right", overlaying="y"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        height=340,
                        margin=dict(l=10, r=10, t=30, b=10),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Métricas STC
                    _mc1, _mc2, _mc3, _mc4, _mc5 = st.columns(5)
                    _mc1.metric("Voc", f"{_res['Voc']:.2f} V")
                    _mc2.metric("Isc", f"{_res['Isc']:.3f} A")
                    _mc3.metric("Vmp", f"{_res['Vmp']:.2f} V")
                    _mc4.metric("Imp", f"{_res['Imp']:.3f} A")
                    _mc5.metric("FF", f"{_res['FF']*100:.1f} %")

                    if _panel_iv.get("_estimado"):
                        _metodo = _panel_iv.get("_metodo", "fit_desoto")
                        st.caption(
                            f"⚠️ Parámetros SDM estimados vía **{_metodo}** desde ficha técnica "
                            f"(NsA={panel.get('NsA', '?')}, n={panel.get('n_idealidad', '?')}). "
                            "Resultado orientativo — para calibración exacta se requieren mediciones de laboratorio."
                        )
                    else:
                        st.caption("✅ Parámetros SDM calibrados directamente del catálogo.")
                else:
                    st.info("G=0 — introduce irradiancia > 0 para ver la curva.")
            except Exception as _e_iv:
                st.warning(f"Motor IV: no se pudo calcular la curva ({_e_iv})")

# ── Guardar panel en session_state para Motor IV automático (#7) ─────────────
st.session_state["panel_dict"]        = panel
st.session_state["panel_nombre_dim"]  = panel_nombre
# inversor ya cargado antes de col2
if inversor.get("costo_usd"):
    st.session_state["costo_inversor_usd"] = inversor["costo_usd"]
# Propagar inversor a session_state para compatibilidad baterías (#25)
st.session_state["inversor_nombre_dim"] = inversor_nombre
st.session_state["inversor_dict_dim"]   = inversor
if inversor.get("datos_completos"):
    st.success("🟢 Inversor: ficha completa")
else:
    _inv_falt = [k for k in ["Vdc_max","Vmppt_min","Vmppt_max","n_trackers","n_strings_tracker","I_max_tracker","P_dc_max_W"] if not inversor.get(k)]
    st.warning(f"🟡 Inversor incompleto — faltan: {', '.join(_inv_falt)}" if _inv_falt else "🟡 Inversor marcado como incompleto en catálogo")

if st.button("▶️ Optimizar N paneles/string", type="primary"):
    resultados = optimizar_n_serie(
        panel, inversor,
        T_frio=T_frio, T_real=T_real, T_extremo=T_extr,
        N_strings_tracker=int(N_str_tr),
        N_min=int(N_min_scan), N_max=int(N_max_scan),
    )

    filas = []
    for r in resultados:
        filas.append({
            "N/string": r.N_serie,
            "Voc frío (V)": r.Voc_frio,
            "Vmp realista (V)": r.Vmp_real,
            "Vmp extremo (V)": r.Vmp_extremo,
            "I equiv (A)": r.I_equiv_tracker,
            "1-Voc≤Vdc": r.v1_voc_max,
            "2-Vmp≥Vmppt_min": r.v2_vmp_real,
            "3-Vmp_ext≥Vmppt_min": r.v3_vmp_extr,
            "4-I≤Imax": r.v4_i_max,
            "5-Vmp≤Vmppt_max": r.v5_vmp_max,
            "MPPT util %": r.mppt_util_pct,
            "Riesgos": r.riesgos,
            "": r.semaforo_color(),
        })

    df = pd.DataFrame(filas)

    def colorear(val):
        if val == "FALLA":
            return "background-color: #FFCCCC; color: #CC0000; font-weight: bold"
        elif val == "ALERTA":
            return "background-color: #FFF3CD; color: #856404; font-weight: bold"
        elif val == "OK":
            return "background-color: #D4EDDA; color: #155724; font-weight: bold"
        return ""

    styled = df.style.map(colorear,
                          subset=["1-Voc≤Vdc", "2-Vmp≥Vmppt_min",
                                  "3-Vmp_ext≥Vmppt_min", "4-I≤Imax",
                                  "5-Vmp≤Vmppt_max"])
    st.dataframe(styled, use_container_width=True)

    # Mejor opción: N con 0 riesgos y MÁXIMA utilización del rango MPPT
    # (Vmp_real / Vmppt_max). Con el check v5 activo, candidatos con Vmp > Vmppt_max
    # ya quedan excluidos por riesgos > 0, así que max(mppt_util_pct) es seguro.
    sin_riesgos = [r for r in resultados if r.riesgos == 0]
    if sin_riesgos:
        mejor = max(sin_riesgos, key=lambda r: r.mppt_util_pct if r.mppt_util_pct > 0 else r.Vmp_real)
        _util_msg = f" · {mejor.mppt_util_pct:.1f}% MPPT" if mejor.mppt_util_pct > 0 else ""
        st.success(
            f"✅ N óptimo = **{mejor.N_serie} paneles/string** — "
            f"0 riesgos · Vmp = {mejor.Vmp_real:.1f} V{_util_msg}"
        )
        st.session_state["N_serie"] = mejor.N_serie

        # Dimensionamiento del sistema — respeta el factor de ocupación
        # (agrivoltaica: los paneles solo cubren un % del terreno; el resto
        # queda libre para el cultivo)
        _area_bruta = float(st.session_state.get("area_fachada_m2", 97.34))
        _f_ocup     = float(st.session_state.get("factor_ocupacion_pct", 100.0))
        area        = _area_bruta * _f_ocup / 100.0
        if _f_ocup < 100.0:
            st.info(
                f"🌱 **Factor de ocupación {_f_ocup:.0f}%** — de los "
                f"{_area_bruta:,.0f} m² del terreno solo se dimensionan paneles "
                f"sobre **{area:,.0f} m²**; el resto queda libre para el cultivo. "
                f"(Se ajusta en 🏠 Proyecto.)"
            )
        dim  = dimensionar_sistema(panel, area, mejor.N_serie,
                                    int(N_str_tr), inversor["N_mppt"])

        st.markdown("### 📊 Por inversor (1 unidad)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Paneles / inversor", dim["N_paneles"])
        c2.metric("P_DC / inversor",    f"{dim['P_dc_stc_kW']:.2f} kW")
        c3.metric("Área / inversor",    f"{dim['area_ocupada_m2']} m²")
        c4.metric("Cobertura unitaria", f"{dim['cobertura_pct']}%")

        # ── Escalado a la granja completa ─────────────────────────────────────
        if dim["area_ocupada_m2"] > 0:
            N_inv        = math.ceil(area / dim["area_ocupada_m2"])
            total_panels = N_inv * dim["N_paneles"]
            total_kWp    = N_inv * dim["P_dc_stc_kW"]
            total_area   = N_inv * dim["area_ocupada_m2"]
            cobert_total = min(round(total_area / area * 100, 1), 100.0) if area > 0 else 0
            P_ac_inv_kW  = (inversor.get("P_ac_nom_W") or inversor.get("P_dc_max_W") or 0) / 1000
            _tit_area = ("área útil para paneles" if _f_ocup < 100.0 else "toda el área")
            st.markdown(f"### 🏭 Proyecto completo ({_tit_area})")
            g1, g2, g3, g4, g5 = st.columns(5)
            g1.metric("Inversores",       N_inv)
            g2.metric("Paneles totales",  f"{total_panels:,}")
            g3.metric("kWp instalados",   f"{total_kWp:,.1f} kWp")
            g4.metric("Área cubierta",    f"{total_area:,.0f} m²")
            g5.metric("Cobertura del área útil" if _f_ocup < 100.0 else "Cobertura total",
                      f"{cobert_total} %",
                      help=(f"Sobre los {area:,.0f} m² útiles para paneles "
                            f"({_f_ocup:.0f}% del terreno)") if _f_ocup < 100.0 else None)
            st.session_state["N_inv_total"]      = N_inv
            st.session_state["P_dc_total_kWp"]  = round(total_kWp, 2)
            st.session_state["N_paneles_granja"] = total_panels
    else:
        st.error("❌ Ningún N válido en el rango. Revisar parámetros del inversor o temperaturas.")
