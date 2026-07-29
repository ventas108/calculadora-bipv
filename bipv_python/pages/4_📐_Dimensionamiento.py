"""Página 4 — Dimensionamiento de strings."""
import streamlit as st
import pandas as pd
from calculos.dimensionamiento import optimizar_n_serie, dimensionar_sistema
from datos.tecnologias_bipv import MODULOS_BIPV
from datos.catalogo_paneles_excel import cargar_catalogo_excel, obtener_panel_excel
from datos.catalogo_inversores_excel import cargar_catalogo_inversores, obtener_inversor_excel
from datos.catalogo_inversores import INVERSORES, seleccionar_inversor

st.set_page_config(page_title="Dimensionamiento — BIPV", page_icon="📐", layout="wide")
st.title("📐 Dimensionamiento de Strings")
st.caption("Equivalente de Mod_OptimizarStringSizing + Mod_CalculoStringSizing (VBA)")

col1, col2 = st.columns(2)

with col1:
    _cat_excel = cargar_catalogo_excel()
    _lista_paneles = list(_cat_excel.keys()) if _cat_excel else list(MODULOS_BIPV.keys())
    _idx_default = _lista_paneles.index("ASP-ST1-T40") if "ASP-ST1-T40" in _lista_paneles else 0
    panel_nombre   = st.selectbox("Panel", _lista_paneles, index=_idx_default)
    _cat_inv = cargar_catalogo_inversores()
    _lista_inv = list(_cat_inv.keys()) if _cat_inv else list(INVERSORES.keys())
    _idx_inv = next((i for i,k in enumerate(_lista_inv) if "MID15KTL3" in k or "MID 15KTL3" in k), 0)
    inversor_nombre = st.selectbox("Inversor", _lista_inv, index=_idx_inv)

with col2:
    T_frio   = st.number_input("T_mín diseño (°C)", value=float(
                                st.session_state.get("T_min_diseno", 5.0)),
                key="T_min_diseno")
    T_real   = st.number_input("T_celda caliente realista (°C)", value=float(
                                st.session_state.get("T_cel_realista", 36.35)),
                key="T_cel_realista")
    T_extr   = st.number_input("T_celda caliente extremo (°C)", value=float(
                                st.session_state.get("T_cel_extremo", 41.94)),
                key="T_cel_extremo")
    N_str_tr = st.number_input("N_strings por tracker (via combinadoras)", value=int(st.session_state.get("N_str_tr", 8)), min_value=1, key="N_str_tr")

panel    = obtener_panel_excel(panel_nombre) if _cat_excel else MODULOS_BIPV[panel_nombre]
if panel.get("costo_usd"):
    st.session_state["costo_modulo_usd"] = panel["costo_usd"]
_iv_params = ["Voc", "Vmp", "Isc", "Imp", "N_s", "NsA"]
_faltantes = [k for k in _iv_params if not panel.get(k)]
if not _faltantes:
    st.success("🟢 Ficha completa — motor IV disponible")
elif len(_faltantes) <= 2:
    st.warning(f"🟡 Ficha parcial — faltan: {', '.join(_faltantes)} | solo cálculo energético")
else:
    st.error(f"🔴 Ficha incompleta — faltan: {', '.join(_faltantes)} | no se aplicará motor IV")
if panel.get("notas"):
    st.caption(f"📋 {panel['notas'][:120]}")
    # Propagar costo al session_state para Financiero
    if panel.get("costo_usd"):
        st.session_state["costo_modulo_usd"] = panel["costo_usd"]
    # ── Indicador completitud ficha técnica ───────────────────────────────────
    _iv_params = ["Voc", "Vmp", "Isc", "Imp", "N_s", "NsA"]
    _faltantes = [k for k in _iv_params if not panel.get(k)]
    if not _faltantes:
        st.success("🟢 Ficha completa — motor IV disponible")
    elif len(_faltantes) <= 2:
        st.warning(f"🟡 Ficha parcial — faltan: {', '.join(_faltantes)} | solo cálculo energético")
    else:
        st.error(f"🔴 Ficha incompleta — faltan: {', '.join(_faltantes)} | no se aplicará motor IV")
    if panel.get("notas"):
        st.caption(f"📋 {panel['notas'][:120]}")
inversor = obtener_inversor_excel(inversor_nombre) if _cat_inv else seleccionar_inversor(inversor_nombre)
if inversor.get("costo_usd"):
    st.session_state["costo_inversor_usd"] = inversor["costo_usd"]
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
        N_min=5, N_max=12,
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
            "2-Vmp≥Vmppt": r.v2_vmp_real,
            "3-Vmp_ext≥Vmppt": r.v3_vmp_extr,
            "4-I≤Imax": r.v4_i_max,
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

    styled = df.style.applymap(colorear,
                                subset=["1-Voc≤Vdc", "2-Vmp≥Vmppt",
                                        "3-Vmp_ext≥Vmppt", "4-I≤Imax"])
    st.dataframe(styled, use_container_width=True)

    # Mejor opción
    sin_riesgos = [r for r in resultados if r.riesgos == 0]
    if sin_riesgos:
        mejor = sin_riesgos[0]
        st.success(f"✅ N óptimo = **{mejor.N_serie} paneles/string** — 0 riesgos")
        st.session_state["N_serie"] = mejor.N_serie

        # Dimensionamiento del sistema
        area = st.session_state.get("area_fachada_m2", 97.34)
        dim  = dimensionar_sistema(panel, area, mejor.N_serie,
                                    int(N_str_tr), inversor["N_mppt"])
        st.markdown("### 📊 Sistema dimensionado")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("N_paneles total", dim["N_paneles"])
        c2.metric("P_DC instalada", f"{dim['P_dc_stc_kW']:.2f} kW")
        c3.metric("Área ocupada", f"{dim['area_ocupada_m2']} m²")
        c4.metric("Cobertura fachada", f"{dim['cobertura_pct']}%")
    else:
        st.error("❌ Ningún N válido en el rango. Revisar parámetros del inversor o temperaturas.")
