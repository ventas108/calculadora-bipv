
"""Página 7 — Análisis financiero BIPV — Ley 1715 de 2014 (Colombia)."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from calculos.financiero import (
    calcular_beneficios_ley_1715,
    calcular_flujo_caja,
    calcular_metricas,
    comparativo_ley_1715,
)

st.set_page_config(page_title="Financiero — BIPV", page_icon="💰", layout="wide")
st.title("💰 Análisis Financiero — Ley 1715 de 2014")
st.caption(
    "Art. 11 Deducción renta · Art. 12 Exclusión IVA · Art. 14 Depreciación acelerada "
    "· TIR · VPN · Payback · LCOE"
)

# ── Prerequisitos ─────────────────────────────────────────────────────────────
prod_ok = st.session_state.get("produccion_ok", False)
# Fallback: Producción > Dimensionamiento > 0  (nunca usar defaults de prueba hardcodeados)
p_stc   = (st.session_state.get("P_stc_kW_sistema")
           or st.session_state.get("P_dc_stc_kW_dim", 0.0))
n_pan   = (st.session_state.get("N_paneles_final")
           or st.session_state.get("N_paneles_dim", 0))
ciudad  = (st.session_state.get("municipio_predio")
           or st.session_state.get("tmy_ciudad", "Bogotá"))

# ── Prioridad E_ac: multi-superficie > bypass > base ─────────────────────────
# Claves exclusivas — nunca se sobreescriben entre sí
_e_ac_base     = st.session_state.get("E_ac_anual_kWh", 0.0)
_e_ac_bypass   = st.session_state.get("E_ac_anual_kWh_bypass", 0.0)
_e_ac_multisup = st.session_state.get("E_ac_anual_kWh_multisup", 0.0)
_bypass_ok     = st.session_state.get("bypass_ok", False)
_kwh_bypass    = st.session_state.get("kwh_bypass_anual", 0.0)
_multisup_ok   = st.session_state.get("multisup_activo", False)
_area_multisup = st.session_state.get("area_total_multisup", 0.0)
_desglose_ms   = st.session_state.get("multisup_desglose", [])
_n_sups        = len(_desglose_ms)

if _multisup_ok and _e_ac_multisup > 0:
    e_ac = _e_ac_multisup
elif _bypass_ok and _e_ac_bypass > 0:
    e_ac = _e_ac_bypass
else:
    e_ac = _e_ac_base

if prod_ok and e_ac > 0:
    if _multisup_ok and _e_ac_multisup > 0:
        st.success(
            f"✅ Sistema multi-superficie — **{e_ac:,.0f} kWh/año** | "
            f"{_n_sups} superficie(s) · Área total: **{_area_multisup:.1f} m²** | Ciudad: **{ciudad}**"
        )
        st.info(
            f"🏗️ **Modo multi-superficie activo:** TIR y Payback calculados con la suma "
            f"de todas las superficies BIPV definidas en 🗺️ Vista 3D. "
            f"Producción superficie principal: {_e_ac_base:,.0f} kWh/año."
        )
        if _desglose_ms:
            import pandas as _pd_fin
            _df_des = _pd_fin.DataFrame([
                {"Superficie": d["nombre"], "Tipo": d["tipo"],
                 "Área (m²)": f"{d['area_m2']:.1f}",
                 "POA (kWh/m²/año)": f"{d['poa_kWh_m2']:.0f}",
                 "E_ac (kWh/año)": f"{d['e_ac_kWh']:,.0f}"}
                for d in _desglose_ms
            ])
            with st.expander("📋 Desglose por superficie"):
                st.dataframe(_df_des, use_container_width=True, hide_index=True)
    elif _bypass_ok and _e_ac_bypass > 0:
        st.success(
            f"✅ Producción con corrección bypass — **{e_ac:,.0f} kWh/año** | "
            f"Sistema: **{p_stc:.2f} kWp** ({n_pan} módulos) | Ciudad: **{ciudad}**"
        )
        st.info(
            f"⚡ **Corrección bypass diodes aplicada:** "
            f"E_ac base = {_e_ac_base:,.0f} kWh/año → "
            f"pérdida bypass = {_kwh_bypass:,.0f} kWh/año → "
            f"**E_ac neta = {e_ac:,.0f} kWh/año** "
            f"({(_e_ac_base - e_ac) / _e_ac_base * 100:.1f}% menos). "
            "TIR y Payback calculados con la producción real corregida."
        )
    else:
        st.success(
            f"✅ Producción cargada — **{e_ac:,.0f} kWh/año** | "
            f"Sistema: **{p_stc:.2f} kWp** ({n_pan} módulos) | Ciudad: **{ciudad}**"
        )
        if prod_ok:
            st.caption(
                "💡 Ejecuta el modelo Bypass Diodes en Página 5 (Sección 5) para usar "
                "la E_ac corregida por sombra parcial en este análisis financiero."
            )
else:
    st.warning(
        "⚠️ **Producción no detectada en esta sesión.** "
        "Si ya ejecutaste 📊 Producción, asegúrate de estar en la **misma pestaña** del navegador "
        "— cada pestaña es una sesión independiente. "
        "Navega a Producción desde el menú lateral y vuelve aquí."
    )
    # Usar valores de Dimensionamiento si existen; si no, dejar en 0 para que el
    # usuario los ingrese — nunca mostrar defaults de prueba que confundan.
    _e_ac_default  = float(st.session_state.get("E_ac_anual_kWh", 0.0)) or 0.0
    _p_stc_default = float(p_stc) if p_stc > 0 else 0.0
    _n_pan_default = int(n_pan) if n_pan > 0 else 1

    e_ac = st.number_input(
        "Ingresa la energía AC anual manualmente (kWh/año)",
        min_value=0.0, max_value=1e7, value=_e_ac_default, step=1000.0,
    )
    p_stc = st.number_input(
        "Potencia instalada (kWp)",
        min_value=0.0, max_value=100000.0, value=_p_stc_default, step=1.0,
    )
    n_pan = st.number_input(
        "Número de módulos",
        min_value=0, max_value=100000, value=_n_pan_default, step=1,
    )


# TRM disponible desde el inicio (se actualiza en Sección 2)
# Default 4200 para consistencia con Presupuesto y el widget de Sección 2
tipo_cambio = float(st.session_state.get("tipo_cambio", 4200.0))

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — CAPEX
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🏗️ 1. Inversión (CAPEX)")

col_cx1, col_cx2 = st.columns(2)

with col_cx1:
    st.markdown("**Costos del sistema**")
    costo_modulo_usd = st.number_input(
        "Costo módulos BIPV (USD/módulo)",
        min_value=10.0, max_value=500.0,
        value=65.0, step=5.0,
        help="ASP-ST1-T40 SolTech ~ USD 60–80 / módulo (precio mercado Colombia 2024)",
    )
    costo_inversor_usd_kw = st.number_input(
        "Costo inversor (USD/kWp)",
        min_value=50.0, max_value=400.0,
        value=120.0, step=10.0,
        help="Growatt MID15KTL3-X ~ USD 100–150/kWp en Colombia 2024",
    )
    costo_estructura_usd_kw = st.number_input(
        "Estructura, cableado, protecciones (USD/kWp)",
        min_value=50.0, max_value=500.0,
        value=200.0, step=25.0,
        help="BIPV de fachada requiere subestructura especializada. Típico: USD 150–300/kWp",
    )
    costo_instalacion_pct = st.number_input(
        "Ingeniería + instalación + puesta en marcha (%CAPEX equipos)",
        min_value=5.0, max_value=40.0,
        value=18.0, step=1.0,
        help="Para Colombia: 15–25% del costo de equipos",
    )
    imprevistos_pct = st.number_input(
        "Imprevistos y contingencia (%)",
        min_value=0.0, max_value=20.0,
        value=5.0, step=1.0,
    )

with col_cx2:
    # Cálculo automático de CAPEX
    capex_modulos     = n_pan * costo_modulo_usd
    capex_inversor    = p_stc * costo_inversor_usd_kw
    capex_estructura  = p_stc * costo_estructura_usd_kw
    capex_equipos     = capex_modulos + capex_inversor + capex_estructura
    capex_instalacion = capex_equipos * costo_instalacion_pct / 100
    capex_sub_total   = capex_equipos + capex_instalacion
    capex_imprev      = capex_sub_total * imprevistos_pct / 100
    capex_total       = capex_sub_total + capex_imprev
    fraccion_equipos  = capex_equipos / capex_total if capex_total > 0 else 0.65

    # Override: CAPEX real desde Presupuesto Detallado
    _ppto = float(st.session_state.get("presupuesto_capex_usd", 0.0))
    if _ppto > 0:
        capex_total      = _ppto
        _sub             = float(st.session_state.get("presupuesto_sub_directo", _ppto*0.65))
        fraccion_equipos = _sub / capex_total if capex_total > 0 else 0.65
        st.info(f"💼 CAPEX real desde Presupuesto Detallado: **USD {capex_total:,.0f}** "
                f"| $ {capex_total*tipo_cambio/1e6:.2f} M COP")

    st.markdown("**Desglose CAPEX**")
    items_capex = {
        "Módulos BIPV":        capex_modulos,
        "Inversor":            capex_inversor,
        "Estructura/cables":   capex_estructura,
        "Ingeniería/instal.":  capex_instalacion,
        "Imprevistos":         capex_imprev,
    }
    df_capex = pd.DataFrame.from_dict(
        items_capex, orient="index", columns=["USD"]
    )
    df_capex["COP (M)"] = (df_capex["USD"] * tipo_cambio / 1e6).round(1)
    st.dataframe(df_capex.style.format({"USD": "{:,.0f}", "COP (M)": "{:.1f}"}),
                 use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("CAPEX total",    f"USD {capex_total:,.0f}",
              delta=f"$ {capex_total*tipo_cambio/1e6:.1f} M COP", delta_color="off")
    c2.metric("Costo por Wp",   f"USD {capex_total/p_stc/1000:.2f}/Wp" if p_stc > 0 else "—",
              delta=f"$ {capex_total*tipo_cambio/p_stc/1000:,.0f} COP/Wp" if p_stc > 0 else None,
              delta_color="off")
    c3.metric("Costo módulo",   f"USD {capex_total/n_pan:,.0f}/módulo" if n_pan > 0 else "—",
              delta=f"$ {capex_total*tipo_cambio/n_pan:,.0f} COP/módulo" if n_pan > 0 else None,
              delta_color="off")

# ── Puente con Presupuesto detallado ──────────────────────────────────────────
_ppto_capex = float(st.session_state.get("presupuesto_capex_usd", 0.0))
_ppto_frac  = float(st.session_state.get("presupuesto_fraccion_equipos", fraccion_equipos))
_tc0        = float(st.session_state.get("tipo_cambio", 4200.0))

if _ppto_capex > 0:
    _diff_pct = abs(_ppto_capex - capex_total) / max(capex_total, 1) * 100
    _color    = "🟢" if _diff_pct < 20 else "🟡" if _diff_pct < 60 else "🔴"
    st.markdown("---")
    usar_ppto = st.toggle(
        f"{_color} Reemplazar CAPEX paramétrico con el 💼 Presupuesto detallado "
        f"— **USD {_ppto_capex:,.0f}** ($ {_ppto_capex*_tc0/1e6:.2f} M COP)",
        value=True,
        help=(
            f"Presupuesto detallado: USD {_ppto_capex:,.0f}  |  "
            f"Modelo paramétrico: USD {capex_total:,.0f}  |  "
            f"Diferencia: {_diff_pct:.0f}%. "
            f"Si la diferencia supera el 50% verifica que los precios del "
            f"Presupuesto estén en USD (no en COP)."
        ),
    )
    if usar_ppto:
        capex_total      = _ppto_capex
        fraccion_equipos = _ppto_frac if _ppto_frac > 0 else fraccion_equipos
        st.success(
            f"✅ CAPEX activo: **USD {capex_total:,.0f}** "
            f"($ {capex_total*_tc0/1e6:.2f} M COP) — desde 💼 Presupuesto detallado"
        )
    else:
        st.info(
            f"ℹ️ Usando CAPEX paramétrico: USD {capex_total:,.0f}. "
            f"Activa el toggle para usar el Presupuesto detallado."
        )
else:
    st.caption(
        "💡 Completa la página 💼 **Presupuesto** para vincular el CAPEX real "
        "aquí automáticamente."
    )

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — TARIFA Y PARÁMETROS OPERATIVOS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚡ 2. Tarifa eléctrica y parámetros operativos")

col_t1, col_t2, col_t3 = st.columns(3)

with col_t1:
    tarifa_cop = st.number_input(
        "Tarifa electricidad (COP/kWh)",
        min_value=100.0, max_value=2000.0,
        value=650.0, step=25.0,
        help="Tarifa comercial/industrial Bogotá 2024: ~550–750 COP/kWh. "
             "Residencial estrato 4-6: ~600–850 COP/kWh",
    )
    tipo_cambio = st.number_input(
        "Tipo de cambio (COP/USD)",
        min_value=3000.0, max_value=6000.0,
        value=float(st.session_state.get("tipo_cambio", 4200.0)),
        step=50.0,
        help="TRM referencia ago 2026: ~4.200 COP/USD. Ajusta según la tasa del día "
             "(Banco de la República: banrep.gov.co).",
    )
    st.session_state["tipo_cambio"] = tipo_cambio
    # ── Alerta TRM desactualizado (tarea #86) ─────────────────────────────────
    # El campo persiste entre sesiones. Si el valor guardado es < 3,900
    # (rango pre-2024) avisamos al usuario con sugerencia de actualizar.
    if tipo_cambio < 3_900:
        st.warning(
            f"⚠️ **TRM {tipo_cambio:,.0f} COP/USD parece desactualizado.** "
            f"La tasa de referencia en agosto 2026 ronda **~4.200 COP/USD**. "
            f"Con TRM bajo, el CAPEX y los beneficios Ley 1715 quedarán "
            f"subestimados en COP. "
            f"Ajusta el valor para resultados correctos."
        )

with col_t2:
    esc_tarifa = st.slider(
        "Escalación anual tarifa (%)",
        min_value=0.0, max_value=15.0, value=5.0, step=0.5,
        help="Colombia: inflación energética histórica ~5–8%/año. "
             "Escenario base: 5%.",
    )
    # ── Label dinámico según tecnología del panel ─────────────────────────────
    _panel_info_raw = (
        str(st.session_state.get("panel_nombre", ""))
        + str(st.session_state.get("panel_modelo", ""))
        + str(st.session_state.get("panel_seleccionado", ""))
    ).lower()
    if "cdte" in _panel_info_raw or "cadmium" in _panel_info_raw:
        _deg_lbl  = "Degradación módulos CdTe (%/año)"
        _deg_help = "CdTe thin-film: 0.30–0.45%/año — la más baja del mercado. Fuente: Jordan & Kurtz 2013."
        _deg_def  = 0.4
    elif any(x in _panel_info_raw for x in ["n-type", "n type", "ntype", "topcon", "hjt", "heterojunction"]):
        _deg_lbl  = "Degradación módulos N-type (TOPCon/HJT) (%/año)"
        _deg_help = "N-type monocristalino (TOPCon / HJT): 0.35–0.50%/año. Fuente: Fraunhofer ISE 2022."
        _deg_def  = 0.45
    elif "perc" in _panel_info_raw:
        _deg_lbl  = "Degradación módulos PERC (%/año)"
        _deg_help = "PERC monocristalino: 0.45–0.60%/año. Fuente: Jordan & Kurtz 2013."
        _deg_def  = 0.5
    elif any(x in _panel_info_raw for x in ["bifacial", "bifi"]):
        _deg_lbl  = "Degradación módulos bifaciales (%/año)"
        _deg_help = "Bifacial Si-mono: 0.40–0.55%/año. Cara trasera degrada ~10% más lento. Fuente: NREL 2021."
        _deg_def  = 0.5
    elif any(x in _panel_info_raw for x in ["mono", "monocristalino", "monocrystalline", "rsm", "jinko", "longi", "risen", "canadian", "trina"]):
        # Panel Si monocristalino convencional sin keyword específico PERC/N-type
        _deg_lbl  = "Degradación módulos Si monocristalino (%/año)"
        _deg_help = (
            "Si monocristalino estándar: 0.45–0.60%/año. "
            "Año 1 puede ser mayor (LID). Fuente: Jordan & Kurtz 2013 / NREL 2021."
        )
        _deg_def  = 0.5
    elif any(x in _panel_info_raw for x in ["poli", "poly", "multicristalino", "multicrystalline"]):
        _deg_lbl  = "Degradación módulos Si policristalino (%/año)"
        _deg_help = "Si policristalino: 0.50–0.70%/año. Fuente: Jordan & Kurtz 2013."
        _deg_def  = 0.6
    elif any(x in _panel_info_raw for x in ["bipv", "fachada", "soltech", "onyx", "issol", "megasol"]):
        _deg_lbl  = "Degradación módulos BIPV (%/año)"
        _deg_help = (
            "Módulos BIPV Si monocristalino: 0.45–0.60%/año. "
            "Temperatura de operación confinada puede acelerar la degradación. "
            "Ref: SUPSI / Fraunhofer."
        )
        _deg_def  = 0.5
    else:
        _deg_lbl  = "Degradación módulos Si monocristalino (%/año)"
        _deg_help = (
            "Sin panel específico detectado — usando referencia Si mono estándar: 0.45–0.55%/año. "
            "Si-mono (PERC): 0.45–0.55% · N-type: 0.35–0.50% · "
            "Si-poli: 0.50–0.70% · CdTe: 0.30–0.45%. Fuente: Jordan & Kurtz 2013."
        )
        _deg_def  = 0.5
    _deg_saved = float(st.session_state.get("tasa_deg_guardada", _deg_def))
    tasa_deg = st.slider(
        _deg_lbl,
        min_value=0.2, max_value=1.5,
        value=_deg_saved,
        step=0.1,
        help=_deg_help,
    )
    st.session_state["tasa_deg_guardada"] = tasa_deg
    # ── #28 · Usar tasa calculada desde historial PR real ────────────────────
    _tasa_calc = st.session_state.get("tasa_degradacion_calculada", None)
    if _tasa_calc is not None and _tasa_calc > 0:
        _usar_deg_real = st.toggle(
            f"Usar degradación del historial real — **{_tasa_calc:.2f}%/año** "
            f"(calculada en 📊 Producción › Degradación anual)",
            value=True, key="usar_deg_historico",
            help="Tasa calculada por regresión lineal sobre PR_corr_T histórico. "
                 "Desactiva para usar el slider paramétrico.",
        )
        if _usar_deg_real:
            tasa_deg = _tasa_calc
            st.caption(
                f"✅ Degradación activa: **{_tasa_calc:.2f}%/año** — desde historial PR real"
            )
    # ── Modelo P90 basado en zona climática y correcciones aplicadas ─────────
    # Metodología: incertidumbre combinada cuadrática EPRI TR-107348 / IEC 61724-3
    # σ_irr: variabilidad interanual del TMY calibrada por zona climática Colombia
    # (IDEAM Atlas de Radiación Solar 2022 + Solargis long-term variability dataset)
    _sigma_irr_map_fin = {
        "urab": 6.5, "turbo": 6.5, "apartad": 6.5,
        "choc": 6.5, "quibd": 6.5,
        "bogot": 5.5, "saban": 5.5, "tunja": 5.5, "cundin": 5.5,
        "llano": 5.5, "villavicenc": 5.5, "vichada": 5.5, "casanare": 5.5,
        "bucaramanga": 5.0, "santand": 5.0, "pasto": 5.0,
        "medell": 5.0, "antioq": 5.0, "rionegro": 5.0,
        "cali": 4.5, "valle": 4.5, "palmira": 4.5,
        "barranq": 4.0, "cartagena": 4.0, "santa marta": 4.0,
    }
    _ciu_low_fin = str(ciudad).lower()
    _sigma_irr_fin = 5.0
    for _kw_fin, _sv_fin in _sigma_irr_map_fin.items():
        if _kw_fin in _ciu_low_fin:
            _sigma_irr_fin = _sv_fin
            break

    # σ_PR: incertidumbre del modelo de pérdidas — disminuye con cada corrección activa
    _motor_ok_p90  = st.session_state.get("poa_efectiva_df") is not None
    _bypass_ok_p90 = bool(st.session_state.get("bypass_ok", False))
    if _motor_ok_p90 and _bypass_ok_p90:
        _sigma_pr_fin  = 3.5
        _pr_label      = "Motor Óptico + Bypass Diodes activos — precisión máxima"
    elif _motor_ok_p90:
        _sigma_pr_fin  = 4.2
        _pr_label      = "Motor Óptico activo (sin bypass)"
    elif _bypass_ok_p90:
        _sigma_pr_fin  = 4.2
        _pr_label      = "Bypass Diodes activos (sin Motor Óptico)"
    else:
        _sigma_pr_fin  = 5.0
        _pr_label      = "Modelo base — sin correcciones ópticas ni bypass"

    _sigma_tot_fin   = (_sigma_irr_fin**2 + _sigma_pr_fin**2) ** 0.5
    _f_p90_auto      = round(1.28 * _sigma_tot_fin, 1)   # z₉₀ = 1.28

    factor_p90 = _f_p90_auto    # valor por defecto (puede sobreescribirse abajo)

    with st.expander(
        f"📊 Modelo P90 — σ_total {_sigma_tot_fin:.1f}%  →  factor {_f_p90_auto:.1f}%  "
        f"→  P90 = {e_ac*(1-_f_p90_auto/100):,.0f} kWh/año",
        expanded=False,
    ):
        st.markdown(
            "**Metodología de incertidumbre combinada** *(EPRI TR-107348 / IEC 61724-3)*\n\n"
            f"| Fuente | σ (%) | Origen |\n"
            f"|---|---|---|\n"
            f"| Variabilidad interanual TMY — {ciudad} | **{_sigma_irr_fin:.1f}** "
            f"| IDEAM / Solargis — zona climática Colombia |\n"
            f"| Incertidumbre modelo de pérdidas | **{_sigma_pr_fin:.1f}** "
            f"| {_pr_label} |\n"
            f"| **σ total combinado** | **{_sigma_tot_fin:.1f}** | √(σ_irr² + σ_PR²) |\n"
            f"| **Factor P90** | **{_f_p90_auto:.1f}%** | z₉₀ × σ_total = 1.28 × {_sigma_tot_fin:.1f}% |\n\n"
            f"**P90 = {e_ac:,.0f} × (1 − {_f_p90_auto/100:.3f}) = "
            f"{e_ac*(1-_f_p90_auto/100):,.0f} kWh/año**\n\n"
            f"*PVsyst aplica un factor P90 manual fijo sin diferenciación regional. "
            f"Este modelo ajusta automáticamente σ_irr según la zona climática colombiana "
            f"y reduce σ_PR a medida que se activan el Motor Óptico y los Bypass Diodes, "
            f"premiando la profundidad de la simulación.*"
        )
        _usar_p90_man = st.checkbox(
            "Ajustar factor P90 manualmente", value=False, key="p90_manual_override"
        )
        if _usar_p90_man:
            factor_p90 = st.slider(
                "Factor P90 manual (%)", 0.0, 25.0,
                float(_f_p90_auto), 0.5, key="p90_slider_manual"
            )
        else:
            factor_p90 = _f_p90_auto
            st.caption(
                f"✅ P90 automático: **{factor_p90:.1f}%** → "
                f"E_ac P90 = **{e_ac*(1-factor_p90/100):,.0f} kWh/año** "
                f"(P50 = {e_ac:,.0f} kWh/año)"
            )
    # Garantizar valor fuera del expander (Streamlit ejecuta widgets aunque esté cerrado)
    if not st.session_state.get("p90_manual_override", False):
        factor_p90 = _f_p90_auto

with col_t3:
    # ── OPEX: desde Presupuesto detallado o slider paramétrico ───────────────
    _ppto_opex_anual = float(st.session_state.get("presupuesto_opex_anual_usd", 0.0))
    _capex_para_opex = float(st.session_state.get("presupuesto_capex_usd", capex_total))
    if _ppto_opex_anual > 0 and _capex_para_opex > 0:
        _opex_pct_ppto = _ppto_opex_anual / _capex_para_opex * 100
        usar_opex_ppto = st.toggle(
            f"Usar OPEX del 💼 Presupuesto — **USD {_ppto_opex_anual:,.0f}/año** ({_opex_pct_ppto:.2f}% CAPEX)",
            value=True, key="usar_opex_ppto",
            help=f"OPEX detallado ingresado en pestaña 📅 OPEX Anual del Presupuesto. "
                 f"Desactiva para usar el slider paramétrico."
        )
        if usar_opex_ppto:
            opex_pct = _opex_pct_ppto
            st.caption(f"✅ OPEX activo: USD {_ppto_opex_anual:,.0f}/año ({_opex_pct_ppto:.2f}% CAPEX) — desde 💼 Presupuesto")
        else:
            opex_pct = st.slider(
                "O&M anual (%CAPEX) — paramétrico",
                min_value=0.5, max_value=3.0, value=1.5, step=0.25,
                help="FV Colombia zona tropical: 1.5–2.5%/año. "
                     "Incluye limpieza bimestral, revisión semestral y monitoreo.",
            )
    else:
        # ── Modo O&M: USD/kWp·año (realista) o % CAPEX ──────────────────────
        _opex_modo = st.radio(
            "Modo O&M",
            ["USD/kWp·año", "% del CAPEX"],
            index=0,
            horizontal=True,
            key="opex_modo_radio",
            label_visibility="collapsed",
            help="USD/kWp·año es más preciso para proyectos grandes; "
                 "%CAPEX es útil cuando no se conoce el detalle.",
        )
        if _opex_modo == "USD/kWp·año":
            # ── Default OPEX según tipo de instalación ───────────────────────
            _tipo_inst_fin = str(st.session_state.get("tipo_instalacion", "")).lower()
            if any(x in _tipo_inst_fin for x in ["bipv", "fachada", "pergola", "pérgola", "marquesina"]):
                _opex_kw_default = 20.0
                _opex_kw_help = (
                    "**BIPV fachada/pérgola: 18–32 USD/kWp·año** (referencia Colombia 2026). "
                    "Mayor que FV convencional porque incluye: O&M especializado de fachada integrada, "
                    "seguro sobre CAPEX alto (0.2–0.4%/yr), inspección estructural semestral. "
                    "Con contrato O&M especializado: 20–28 USD/kWp·año."
                )
            elif any(x in _tipo_inst_fin for x in ["techo", "roof", "cubierta"]):
                _opex_kw_default = 12.0
                _opex_kw_help = (
                    "**Techo industrial/comercial: 9–16 USD/kWp·año** (referencia Colombia 2026). "
                    "Incluye: limpieza mensual, revisión semestral inversores, monitoreo remoto. "
                    "IRENA 2023 rooftop: 10–15 USD/kWp·año zona tropical."
                )
            else:  # Granja FV campo / utility-scale
                _opex_kw_default = 10.0
                _opex_kw_help = (
                    "**Granja FV campo / utility-scale: 8–14 USD/kWp·año** (referencia Colombia 2026). "
                    "Incluye: limpieza bimestral módulos, revisión semestral inversores, "
                    "monitoreo remoto y mantenimiento preventivo. "
                    "Con contrato O&M local: 9–11 USD/kWp·año. "
                    "IRENA 2023 utility-scale: 9–15 USD/kWp·año zona tropical."
                )
            _opex_kw = st.slider(
                "O&M anual (USD/kWp·año)",
                min_value=3.0, max_value=35.0,
                value=float(st.session_state.get("opex_kw_guardado", _opex_kw_default)),
                step=0.5,
                help=_opex_kw_help,
            )
            st.session_state["opex_kw_guardado"] = _opex_kw
            _opex_usd_anual = _opex_kw * p_stc
            opex_pct = _opex_usd_anual / capex_total * 100 if capex_total > 0 else 1.5
            st.caption(
                f"≡ **USD {_opex_usd_anual:,.0f}/año** · {opex_pct:.2f}% del CAPEX"
            )
        else:
            opex_pct = st.slider(
                "O&M anual (%CAPEX)",
                min_value=0.5, max_value=3.0, value=1.5, step=0.25,
                help="FV Colombia zona tropical: 1.5–2.5%/año. "
                     "Incluye limpieza, revisión y seguros. "
                     "Completa 📅 OPEX Anual en Presupuesto para usar valores reales.",
            )
    tasa_desc = st.slider(
        "Tasa de descuento WACC (%)",
        min_value=5.0, max_value=20.0, value=10.0, step=0.5,
        help="WACC Colombia: 9–14% para proyectos de energía renovable. Base: 10%.",
    )
    n_anos = st.slider(
        "Horizonte de análisis (años)",
        min_value=10, max_value=30, value=25, step=5,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL DE CONVERSIÓN USD → COP (en tiempo real)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
with st.expander("💱 Conversor de cifras USD → COP (TRM del día)", expanded=True):
    st.caption(f"Usando TRM: **{tipo_cambio:,.0f} COP/USD** — ajusta la tasa en la sección anterior para actualizar.")

    col_cv1, col_cv2, col_cv3, col_cv4 = st.columns(4)
    col_cv1.metric("CAPEX bruto",
                   f"${capex_total*tipo_cambio/1e6:.2f} M COP",
                   delta=f"USD {capex_total:,.0f}", delta_color="off")
    col_cv2.metric("Módulos BIPV",
                   f"${capex_modulos*tipo_cambio/1e6:.2f} M COP",
                   delta=f"USD {capex_modulos:,.0f}", delta_color="off")
    col_cv3.metric("Inversor",
                   f"${capex_inversor*tipo_cambio/1e6:.2f} M COP",
                   delta=f"USD {capex_inversor:,.0f}", delta_color="off")
    col_cv4.metric("Estructura + Instalación",
                   f"${(capex_estructura+capex_instalacion)*tipo_cambio/1e6:.2f} M COP",
                   delta=f"USD {(capex_estructura+capex_instalacion):,.0f}", delta_color="off")

    st.markdown("---")
    col_cv5, col_cv6, col_cv7, col_cv8 = st.columns(4)
    ben_lv = calcular_beneficios_ley_1715(
        capex_usd       = capex_total,
        fraccion_equipo = fraccion_equipos,
        tasa_renta      = 0.35,
        tipo_cambio     = tipo_cambio,
    )
    col_cv5.metric("Beneficios Ley 1715",
                   f"${ben_lv['total_usd']*tipo_cambio/1e6:.2f} M COP",
                   delta=f"USD {ben_lv['total_usd']:,.0f}", delta_color="off")
    col_cv6.metric("CAPEX neto (con Ley 1715)",
                   f"${ben_lv['capex_neto_usd']*tipo_cambio/1e6:.2f} M COP",
                   delta=f"USD {ben_lv['capex_neto_usd']:,.0f}", delta_color="off")
    col_cv7.metric("Ahorro energía año 1",
                   f"${e_ac * (tarifa_cop/1e6):.2f} M COP/año",
                   delta=f"USD {e_ac * tarifa_cop / tipo_cambio:,.0f}/año", delta_color="off")
    col_cv8.metric("Tarifa referencia",
                   f"{tarifa_cop:,.0f} COP/kWh",
                   delta=f"USD {tarifa_cop/tipo_cambio:.4f}/kWh", delta_color="off")

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — BENEFICIOS LEY 1715
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📜 3. Beneficios Ley 1715 de 2014")

col_l1, col_l2 = st.columns([1, 1])

with col_l1:
    tasa_renta = st.number_input(
        "Tasa impuesto de renta corporativo (%)",
        min_value=15.0, max_value=40.0,
        value=35.0, step=1.0,
        help="Colombia 2024: tasa general corporativa 35% (Ley 2277 de 2022)",
    )
    st.markdown("""
    **Artículos aplicables:**
    - **Art. 11** — Deducción especial renta: 50% del CAPEX deducible de la base gravable
    - **Art. 12** — Exclusión IVA: no se paga IVA (19%) sobre equipos SRFNC calificados
    - **Art. 14** — Depreciación acelerada: hasta 5 años (vs 10 años estándar)

    > ⚠️ Requiere certificación UPME previa al inicio del proyecto.
    > Aplicable a personas jurídicas obligadas a llevar contabilidad.
    """)

with col_l2:
    ben = calcular_beneficios_ley_1715(
        capex_usd        = capex_total,
        fraccion_equipo  = fraccion_equipos,
        tasa_renta       = tasa_renta / 100,
        tipo_cambio      = tipo_cambio,
        tasa_descuento   = tasa_desc / 100,
    )

    b1, b2, b3, b4 = st.columns(2), st.columns(2), None, None
    bb1, bb2 = st.columns(2)
    bbb1, bbb2 = st.columns(2)

    bb1.metric("Art. 11 — Deducción renta",
               f"USD {ben['ahorro_renta_usd']:,.0f}",
               delta=f"$ {ben['ahorro_renta_usd']*tipo_cambio/1e6:.2f} M COP",
               delta_color="off",
               help="50% × CAPEX × tasa_renta")
    bb2.metric("Art. 12 — Ahorro IVA",
               f"USD {ben['ahorro_iva_usd']:,.0f}",
               delta=f"$ {ben['ahorro_iva_usd']*tipo_cambio/1e6:.2f} M COP",
               delta_color="off",
               help="19% × CAPEX_equipos")
    bbb1.metric("Art. 14 — Dep. acelerada",
                f"USD {ben['ahorro_dep_vpn_usd']:,.0f}",
                delta=f"$ {ben['ahorro_dep_vpn_usd']*tipo_cambio/1e6:.2f} M COP",
                delta_color="off",
                help="VPN del ahorro por diferencial de depreciación 5 vs 10 años")
    bbb2.metric("💚 Total beneficios",
                f"USD {ben['total_usd']:,.0f}",
                delta=f"$ {ben['total_usd']*tipo_cambio/1e6:.2f} M COP  ·  -{ben['pct_capex']:.1f}% CAPEX",
                delta_color="off")

    st.info(
        f"**CAPEX bruto:** USD {capex_total:,.0f}  ($ {capex_total*tipo_cambio/1e6:.2f} M COP) → "
        f"**CAPEX neto (con Ley 1715):** USD {ben['capex_neto_usd']:,.0f}  "
        f"($ {ben['capex_neto_usd']*tipo_cambio/1e6:.2f} M COP)  "
        f"— {ben['pct_capex']:.1f}% de reducción efectiva"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — ANÁLISIS FINANCIERO
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📈 4. Análisis financiero")

# Invalidar caché si el CAPEX activo cambió respecto al último cálculo
_last_capex_calc = float(st.session_state.get("capex_total_usd", 0.0))
if _last_capex_calc > 0 and abs(_last_capex_calc - capex_total) > 0.5:
    st.session_state.pop("financiero_ok", None)
    st.session_state.pop("comp_financiero", None)
    st.warning(
        f"⚠️ El CAPEX cambió de **USD {_last_capex_calc:,.0f}** → **USD {capex_total:,.0f}**. "
        f"Presiona **Calcular** para actualizar TIR, VPN y Payback."
    )

btn_fin = st.button(
    "📊 Calcular TIR, VPN, Payback y LCOE", type="primary", use_container_width=True
)

if btn_fin or st.session_state.get("financiero_ok"):

    # ── E_ac P90 ──────────────────────────────────────────────────────────────
    e_ac_p90 = e_ac * (1.0 - factor_p90 / 100.0)

    if btn_fin:
        # Escenario P50 (base)
        comp = comparativo_ley_1715(
            capex_usd         = capex_total,
            e_ac_kWh_anual    = e_ac,
            tarifa_cop_kWh    = tarifa_cop,
            tipo_cambio       = tipo_cambio,
            tasa_descuento    = tasa_desc / 100,
            tasa_escalacion   = esc_tarifa,
            tasa_degradacion  = tasa_deg,
            opex_pct          = opex_pct,
            n_anos            = n_anos,
            beneficios_1715   = ben,
        )
        # Escenario P90 (conservador — mismo CAPEX, menos producción)
        comp_p90 = comparativo_ley_1715(
            capex_usd         = capex_total,
            e_ac_kWh_anual    = e_ac_p90,
            tarifa_cop_kWh    = tarifa_cop,
            tipo_cambio       = tipo_cambio,
            tasa_descuento    = tasa_desc / 100,
            tasa_escalacion   = esc_tarifa,
            tasa_degradacion  = tasa_deg,
            opex_pct          = opex_pct,
            n_anos            = n_anos,
            beneficios_1715   = ben,
        )
        st.session_state["comp_financiero"]    = comp
        st.session_state["comp_financiero_p90"] = comp_p90
        st.session_state["financiero_ok"]      = True
        st.session_state["factor_p90_guardado"] = factor_p90
    else:
        comp     = st.session_state.get("comp_financiero", {})
        comp_p90 = st.session_state.get("comp_financiero_p90", {})
        if not comp:
            st.warning("Presiona el botón para calcular.")
            st.stop()
        # Si el factor P90 cambió desde el último cálculo, avisar
        _factor_guardado = st.session_state.get("factor_p90_guardado", factor_p90)
        if abs(_factor_guardado - factor_p90) > 0.1:
            st.info(
                f"ℹ️ El factor P90 cambió ({_factor_guardado:.1f}% → {factor_p90:.1f}%). "
                f"Presiona **Calcular** para actualizar el escenario P90."
            )

    m_sin  = comp["sin"]["metricas"]
    m_con  = comp["con"]["metricas"]
    m_p90  = comp_p90["con"]["metricas"] if comp_p90 else None

    # ── Tabla comparativa: Sin Ley 1715 | Con Ley 1715 (P50) | Con Ley 1715 (P90) ──
    st.subheader("⚖️ Comparativo sin / con Ley 1715  ·  P50 vs P90")
    st.caption(
        f"**P50** = producción esperada ({e_ac:,.0f} kWh/año) · "
        f"**P90** = escenario conservador banco ({e_ac_p90:,.0f} kWh/año, "
        f"−{factor_p90:.1f}%) · "
        f"CAPEX igual en ambos escenarios"
    )

    _col_p90 = [
        f"USD {ben['capex_neto_usd']:,.0f}",
        f"$ {ben['capex_neto_usd']*tipo_cambio/1e6:.2f} M",
        f"{m_p90['tir_pct']:.1f}%" if (m_p90 and m_p90['tir_pct']) else "N/A",
        f"USD {m_p90['vpn_usd']:,.0f}" if m_p90 else "—",
        f"$ {m_p90['vpn_cop_millon']:.1f} M" if m_p90 else "—",
        f"{m_p90['payback_simple']:.1f} años" if (m_p90 and m_p90['payback_simple']) else "> horizonte",
        f"{m_p90['payback_desc']:.1f} años" if (m_p90 and m_p90['payback_desc']) else "> horizonte",
        f"{m_p90['lcoe_usd_kWh']:.4f}" if m_p90 else "—",
        f"{m_p90['lcoe_cop_kWh']:.0f}" if m_p90 else "—",
    ] if m_p90 else ["—"] * 9

    df_comp = pd.DataFrame({
        "Métrica": [
            "CAPEX efectivo",
            "CAPEX efectivo (COP)",
            "TIR (%)",
            f"VPN a {int(tasa_desc)}% (USD)",
            f"VPN a {int(tasa_desc)}% (COP)",
            "Payback simple (años)",
            "Payback descontado (años)",
            "LCOE (USD/kWh)",
            "LCOE (COP/kWh)",
        ],
        "Sin Ley 1715 · P50": [
            f"USD {capex_total:,.0f}",
            f"$ {capex_total*tipo_cambio/1e6:.2f} M",
            f"{m_sin['tir_pct']:.1f}%" if m_sin['tir_pct'] else "N/A",
            f"USD {m_sin['vpn_usd']:,.0f}",
            f"$ {m_sin['vpn_cop_millon']:.1f} M",
            f"{m_sin['payback_simple']:.1f} años" if m_sin['payback_simple'] else "> horizonte",
            f"{m_sin['payback_desc']:.1f} años" if m_sin['payback_desc'] else "> horizonte",
            f"{m_sin['lcoe_usd_kWh']:.4f}",
            f"{m_sin['lcoe_cop_kWh']:.0f}",
        ],
        "Con Ley 1715 · P50 ✅": [
            f"USD {ben['capex_neto_usd']:,.0f}",
            f"$ {ben['capex_neto_usd']*tipo_cambio/1e6:.2f} M",
            f"{m_con['tir_pct']:.1f}%" if m_con['tir_pct'] else "N/A",
            f"USD {m_con['vpn_usd']:,.0f}",
            f"$ {m_con['vpn_cop_millon']:.1f} M",
            f"{m_con['payback_simple']:.1f} años" if m_con['payback_simple'] else "> horizonte",
            f"{m_con['payback_desc']:.1f} años" if m_con['payback_desc'] else "> horizonte",
            f"{m_con['lcoe_usd_kWh']:.4f}",
            f"{m_con['lcoe_cop_kWh']:.0f}",
        ],
        f"Con Ley 1715 · P90 🏦 (−{factor_p90:.0f}%)": _col_p90,
    })

    def _color_comp(row):
        n = len(row)
        styles = [""] * n
        for i in range(1, n):
            try:
                val_str = str(row.iloc[i])
                # TIR row — verde P50, amarillo P90
                if "%" in val_str and i == 1:
                    styles[i] = "background-color: #E8F5E9; font-weight: bold"
                elif "%" in val_str and i == 2:
                    styles[i] = "background-color: #FFF9C4; font-weight: bold"
            except Exception:
                pass
        return styles

    st.dataframe(df_comp.style.apply(_color_comp, axis=1), use_container_width=True, hide_index=True)

    # ── Métricas clave: 3 columnas P50 / P90 / Delta ──────────────────────────
    c1, c2, c3 = st.columns(3)
    tir_delta = ((m_con['tir_pct'] or 0) - (m_sin['tir_pct'] or 0))
    c1.metric(
        "TIR P50 con Ley 1715",
        f"{m_con['tir_pct']:.1f}%" if m_con['tir_pct'] else "—",
        delta=f"+{tir_delta:.1f}pp vs sin Ley 1715",
    )
    if m_p90:
        tir_caida = (m_con['tir_pct'] or 0) - (m_p90['tir_pct'] or 0)
        c2.metric(
            f"TIR P90 con Ley 1715 (−{factor_p90:.0f}%)",
            f"{m_p90['tir_pct']:.1f}%" if m_p90['tir_pct'] else "—",
            delta=f"−{tir_caida:.1f}pp vs P50",
            delta_color="inverse",
        )
        vpn_p90_ok = m_p90.get("vpn_positivo", False)
        c3.metric(
            "VPN P90 con Ley 1715",
            f"USD {m_p90['vpn_usd']:,.0f}",
            delta="✅ Positivo — bancable" if vpn_p90_ok else "⚠️ Negativo — revisar",
            delta_color="normal" if vpn_p90_ok else "inverse",
        )
    else:
        c2.metric("TIR P90", "Recalcula →", delta="")
        c3.metric("VPN P90", "Recalcula →", delta="")

    c4, c5, c6 = st.columns(3)
    c4.metric("VPN P50 con Ley 1715",
              f"USD {m_con['vpn_usd']:,.0f}  |  $ {m_con['vpn_usd']*tipo_cambio/1e6:.1f} M COP",
              delta="✅ Positivo" if m_con['vpn_positivo'] else "❌ Negativo",
              delta_color="normal" if m_con['vpn_positivo'] else "inverse")
    c5.metric("Payback P50", f"{m_con['payback_simple']:.1f} años" if m_con['payback_simple'] else "—")
    if m_p90:
        c6.metric("Payback P90",
                  f"{m_p90['payback_simple']:.1f} años" if m_p90['payback_simple'] else "> horizonte",
                  delta=f"+{(m_p90['payback_simple'] or n_anos)-(m_con['payback_simple'] or 0):.1f} años vs P50"
                        if m_p90['payback_simple'] and m_con['payback_simple'] else "",
                  delta_color="inverse")
    else:
        c6.metric("LCOE P50", f"{m_con['lcoe_cop_kWh']:.0f} COP/kWh  ·  USD {m_con['lcoe_usd_kWh']:.4f}",
                  delta=f"Tarifa: {tarifa_cop:.0f} COP/kWh", delta_color="off")

    # ── Gráfica flujo de caja acumulado con banda P50–P90 ────────────────────
    st.subheader("💵 Flujo de caja acumulado (USD)  —  banda P50 / P90")

    fc_sin  = comp["sin"]["flujos"]
    fc_con  = comp["con"]["flujos"]
    fc_p90  = comp_p90["con"]["flujos"] if comp_p90 else None
    anos    = [f["año"] for f in fc_sin]

    fig_fc = go.Figure()

    # Banda entre P50 y P90 (relleno semitransparente)
    if fc_p90:
        fig_fc.add_trace(go.Scatter(
            x=anos,
            y=[f["flujo_acum_usd"] for f in fc_p90],
            name=f"Con Ley 1715 · P90 (−{factor_p90:.0f}%)",
            line=dict(color="#F57F17", width=1.5, dash="dot"),
            mode="lines",
            fill=None,
        ))
        fig_fc.add_trace(go.Scatter(
            x=anos,
            y=[f["flujo_acum_usd"] for f in fc_con],
            name="Con Ley 1715 · P50",
            line=dict(color="#2E7D32", width=2.5),
            fill="tonexty",
            fillcolor="rgba(255,179,0,0.12)",   # banda P50–P90 en ámbar suave
            mode="lines",
        ))
    else:
        fig_fc.add_trace(go.Scatter(
            x=anos,
            y=[f["flujo_acum_usd"] for f in fc_con],
            name="Con Ley 1715 · P50",
            line=dict(color="#2E7D32", width=2.5),
            mode="lines",
        ))

    fig_fc.add_trace(go.Scatter(
        x=anos, y=[f["flujo_acum_usd"] for f in fc_sin],
        name="Sin Ley 1715 · P50",
        line=dict(color="#EF5350", width=2, dash="dash"),
        mode="lines",
    ))
    fig_fc.add_hline(y=0, line_color="gray", line_dash="dot", line_width=1)

    # Payback P50
    if m_con.get("payback_simple"):
        fig_fc.add_vline(
            x=m_con["payback_simple"],
            line_color="#2E7D32", line_dash="dot",
            annotation_text=f"Payback P50: {m_con['payback_simple']:.1f} a",
            annotation_position="top right",
        )
    # Payback P90
    if m_p90 and m_p90.get("payback_simple"):
        fig_fc.add_vline(
            x=m_p90["payback_simple"],
            line_color="#F57F17", line_dash="dot",
            annotation_text=f"Payback P90: {m_p90['payback_simple']:.1f} a",
            annotation_position="bottom right",
        )
    if m_sin.get("payback_simple"):
        fig_fc.add_vline(
            x=m_sin["payback_simple"],
            line_color="#EF5350", line_dash="dot",
            annotation_text=f"Payback sin 1715: {m_sin['payback_simple']:.1f} a",
            annotation_position="top left",
        )

    fig_fc.update_layout(
        xaxis_title="Año",
        yaxis_title="Flujo acumulado (USD)",
        height=440,
        legend=dict(orientation="h", y=-0.22),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
    )
    st.plotly_chart(fig_fc, use_container_width=True)
    if fc_p90:
        st.caption(
            "🟡 La banda **ámbar** muestra la incertidumbre P50–P90: "
            "el proyecto debería ser rentable incluso en el escenario conservador "
            f"(producción {factor_p90:.0f}% menor). "
            "Un banco típicamente financia si el VPN P90 ≥ 0."
        )

    # ── Gráfica ingresos anuales vs OPEX ──────────────────────────────────────
    with st.expander("📊 Ver ingresos anuales vs O&M"):
        fig_ing = go.Figure()
        fig_ing.add_trace(go.Bar(
            name="Ingreso energía",
            x=anos[1:], y=[f["ingreso_energia_usd"] for f in fc_con[1:]],
            marker_color="#66BB6A",
        ))
        fig_ing.add_trace(go.Bar(
            name="O&M (OPEX)",
            x=anos[1:], y=[-f["opex_usd"] for f in fc_con[1:]],
            marker_color="#EF9A9A",
        ))
        fig_ing.update_layout(
            barmode="relative",
            xaxis_title="Año",
            yaxis_title="USD",
            height=340,
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_ing, use_container_width=True)

    # ── Tabla de beneficios Ley 1715 ─────────────────────────────────────────
    with st.expander("📜 Detalle Ley 1715 — base de cálculo"):
        st.markdown(f"""
| Beneficio | Base | Cálculo | USD | COP |
|---|---|---|---|---|
| **Art. 11** Deducción renta | 50% × CAPEX × tasa_renta | 0.50 × {capex_total:,.0f} × {tasa_renta/100:.2f} | **{ben['ahorro_renta_usd']:,.0f}** | **$ {ben['ahorro_renta_usd']*tipo_cambio/1e6:.2f} M** |
| **Art. 12** Exclusión IVA | 19% × CAPEX_equipos | 0.19 × {capex_total*fraccion_equipos:,.0f} | **{ben['ahorro_iva_usd']:,.0f}** | **$ {ben['ahorro_iva_usd']*tipo_cambio/1e6:.2f} M** |
| **Art. 14** Dep. acelerada | VPN diferencial 5yr vs 10yr | — | **{ben['ahorro_dep_vpn_usd']:,.0f}** | **$ {ben['ahorro_dep_vpn_usd']*tipo_cambio/1e6:.2f} M** |
| **Total Ley 1715** | — | — | **{ben['total_usd']:,.0f}** | **$ {ben['total_usd']*tipo_cambio/1e6:.2f} M** |
| **CAPEX neto** | CAPEX − Ley 1715 | {capex_total:,.0f} − {ben['total_usd']:,.0f} | **{ben['capex_neto_usd']:,.0f}** | **$ {ben['capex_neto_usd']*tipo_cambio/1e6:.2f} M** |
        """)
        st.caption(
            "⚠️ Los beneficios Art. 11 y 14 requieren declaración de renta con utilidades suficientes. "
            "Art. 12 aplica desde la compra de equipos. Requiere certificación UPME previa."
        )

    # ── Sensibilidad de tarifa eléctrica ──────────────────────────────────────
    with st.expander("💡 Sensibilidad de tarifa — ¿qué pasa si vendo a diferente precio?"):
        st.markdown(
            "Compara TIR, Payback y VPN según el precio al que vendas o ahorres la energía. "
            "Aplica **con Ley 1715**, todos los demás parámetros iguales al escenario principal."
        )

        _tarifas_sens = [
            ("Autoconsumo industrial",           650),
            ("Medición neta alta (CREG 174)",    450),
            ("PPA bilateral privado",            280),
            ("Precio bolsa XM (promedio)",       220),
            ("Precio bolsa XM (mínimo histór.)", 160),
        ]

        # Calcular umbral donde VPN ≈ 0 (búsqueda binaria)
        def _metricas_tarifa(t_cop):
            try:
                _c = comparativo_ley_1715(
                    capex_usd        = capex_total,
                    e_ac_kWh_anual   = e_ac,
                    tarifa_cop_kWh   = float(t_cop),
                    tipo_cambio      = tipo_cambio,
                    tasa_descuento   = tasa_desc / 100,
                    tasa_escalacion  = esc_tarifa,
                    tasa_degradacion = tasa_deg,
                    opex_pct         = opex_pct,
                    n_anos           = n_anos,
                    beneficios_1715  = ben,
                )
                return _c["con"]["metricas"]
            except Exception:
                return None

        _tlo, _thi = 50.0, 600.0
        for _ in range(22):
            _tmid = (_tlo + _thi) / 2
            _mm = _metricas_tarifa(_tmid)
            if _mm and (_mm.get("vpn_usd") or 0) > 0:
                _thi = _tmid
            else:
                _tlo = _tmid
        _t_umbral = int(round((_tlo + _thi) / 2))

        _rows_sens = []
        for _nm, _tc in _tarifas_sens:
            _m2 = _metricas_tarifa(_tc)
            if _m2:
                _vpn_ok = (_m2.get("vpn_usd") or 0) > 0
                _rows_sens.append({
                    "Escenario":             _nm,
                    "COP/kWh":               _tc,
                    "USD/kWh":               round(_tc / tipo_cambio, 4),
                    "Ingreso año 1 (USD)":   int(e_ac * _tc / tipo_cambio),
                    "Payback":               f"{_m2['payback_simple']:.1f} a" if _m2.get("payback_simple") else f">{n_anos}a",
                    "TIR":                   f"{_m2['tir_pct']:.1f}%" if _m2.get("tir_pct") else "—",
                    "VPN a WACC (USD)":      f"{_m2['vpn_usd']:,.0f}",
                    "Estado":                "✅ Bancable" if _vpn_ok else "⚠️ Revisar",
                })

        _m_umb = _metricas_tarifa(_t_umbral)
        _rows_sens.append({
            "Escenario":             f"⛔ Umbral mínimo (VPN ≈ 0)",
            "COP/kWh":               _t_umbral,
            "USD/kWh":               round(_t_umbral / tipo_cambio, 4),
            "Ingreso año 1 (USD)":   int(e_ac * _t_umbral / tipo_cambio),
            "Payback":               f"≈{n_anos}a",
            "TIR":                   f"≈{tasa_desc:.0f}% (WACC)",
            "VPN a WACC (USD)":      "≈ 0",
            "Estado":                "⛔ Límite",
        })

        _df_sens = pd.DataFrame(_rows_sens)

        def _hl_tarifa(row):
            base = [""] * len(row)
            if int(row["COP/kWh"]) == int(tarifa_cop):
                return ["background-color:#E8F5E9; font-weight:bold"] * len(row)
            if "⚠️" in str(row.get("Estado", "")):
                return ["background-color:#FFF9C4"] * len(row)
            if "⛔" in str(row.get("Estado", "")):
                return ["background-color:#FFEBEE"] * len(row)
            return base

        st.dataframe(
            _df_sens.style.apply(_hl_tarifa, axis=1).format({
                "COP/kWh":             "{:,.0f}",
                "USD/kWh":             "{:.4f}",
                "Ingreso año 1 (USD)": "{:,.0f}",
            }),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            f"🟢 Verde = escenario activo ({tarifa_cop:.0f} COP/kWh) · "
            f"🟡 Amarillo = rentable con menor margen · "
            f"🔴 Rojo = no viable al WACC del {tasa_desc:.0f}% · "
            f"**Umbral calculado: {_t_umbral} COP/kWh** — "
            f"por debajo de este precio el VPN se vuelve negativo."
        )

    # ── Tabla flujo de caja completo ─────────────────────────────────────────
    with st.expander("📋 Ver tabla de flujo de caja anual"):
        df_fc = pd.DataFrame(fc_con)
        df_fc.columns = ["Año", "Producción (kWh)", "Ingreso energía (USD)",
                          "O&M (USD)", "Flujo (USD)", "Flujo acum. (USD)"]
        df_fc["Ingreso (M COP)"]    = (df_fc["Ingreso energía (USD)"] * tipo_cambio / 1e6).round(3)
        df_fc["Flujo acum. (M COP)"] = (df_fc["Flujo acum. (USD)"] * tipo_cambio / 1e6).round(3)
        st.dataframe(
            df_fc.style.format({
                "Producción (kWh)":      "{:,.0f}",
                "Ingreso energía (USD)":  "{:,.0f}",
                "O&M (USD)":             "{:,.0f}",
                "Flujo (USD)":           "{:+,.0f}",
                "Flujo acum. (USD)":     "{:+,.0f}",
                "Ingreso (M COP)":       "{:.3f}",
                "Flujo acum. (M COP)":   "{:+.3f}",
            }).background_gradient(subset=["Flujo acum. (USD)"], cmap="RdYlGn"),
            use_container_width=True,
        )

    # ── Mensaje final ─────────────────────────────────────────────────────────
    color_vpn = "✅" if m_con["vpn_positivo"] else "⚠️"
    st.success(
        f"{color_vpn} **{ciudad}** — {n_pan} módulos "
        f"{st.session_state.get('panel_nombre_dim') or st.session_state.get('panel_nombre') or st.session_state.get('panel_modelo') or '—'} | "
        f"CAPEX neto: **USD {ben['capex_neto_usd']:,.0f}** ($ {ben['capex_neto_usd']*tipo_cambio/1e6:.2f} M COP) | "
        f"TIR: **{m_con['tir_pct']:.1f}%** | " if m_con['tir_pct'] else "TIR: **N/A** | "
        f"VPN: **USD {m_con['vpn_usd']:,.0f}** ($ {m_con['vpn_usd']*tipo_cambio/1e6:.1f} M COP) | "
        + (f"Payback: **{m_con['payback_simple']:.1f} años** | " if m_con['payback_simple'] else "Payback: **> horizonte** | ")
        + f"LCOE: **{m_con['lcoe_cop_kWh']:.0f} COP/kWh** "
        f"({'<' if m_con['lcoe_cop_kWh'] < tarifa_cop else '>'} tarifa {tarifa_cop:.0f} COP/kWh)"
    )

    # Guardar para Reporte
    st.session_state["capex_total_usd"]        = capex_total
    st.session_state["ben_1715"]               = ben
    st.session_state["metricas_financiero"]    = m_con
    st.session_state["metricas_financiero_p90"] = m_p90   # para Reporte PDF
    st.session_state["e_ac_p90_kWh"]           = e_ac_p90
    st.session_state["factor_p90_pct"]         = factor_p90
    st.session_state["tarifa_cop_kWh"]         = tarifa_cop
    st.session_state["financiero_ok"]          = True
