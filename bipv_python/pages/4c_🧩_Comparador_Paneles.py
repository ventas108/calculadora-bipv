# -*- coding: utf-8 -*-
"""
🧩 Comparador de Paneles — hermano de 4b ⚖️ Comparador de Inversores.

Diferencia de fondo con el de inversores: cambiar de inversor solo afecta
el lado AC (clipping sobre una serie DC ya simulada) -- cambiar de panel
cambia la física DC completa (Voc/Isc/Vmp propios, tecnología). No hay
forma de "reclipear" una serie existente para simular otro panel, así que
esta página re-simula cada candidato de verdad con run_bipv_simulation()
(motor de Fase 2/4), reusando calculos/comparador_paneles.py.

v1 -- alcance real, no maquillado: hoy el catálogo interno (MODULOS_BIPV)
solo tiene 1 panel con ficha completa (ASP-ST1-T40); los otros 6 tienen
Pmax_stc=None y quedan excluidos (ver optimization/variables.py::variable_panel()).
Esta página se vuelve útil de verdad en cuanto se completen esas fichas o
se agreguen paneles nuevos -- hoy compara 1 fila, honestamente, en vez de
fingir una comparación que no existe.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(page_title="Comparador de Paneles", page_icon="🧩", layout="wide")

from calculos.auth import requerir_login
requerir_login()

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()   # #63 — proyecto activo visible en cada página

from datos.ciudades_colombia import CIUDADES
from calculos.presupuesto import BENCH, ZONA_FACTOR
from calculos.comparador_paneles import comparar_paneles, paneles_excluidos_por_ficha_incompleta
from calculos.invalidacion import KEYS_DERIVADOS_POA
from simulation.schemas import BIPVConfiguration

st.title("🧩 Comparador de Paneles")
st.caption(
    "Compara paneles reales del catálogo sobre el MISMO sitio, geometría e inversor de tu "
    "proyecto — re-simula cada candidato con el motor físico completo (SDM De Soto), no un "
    "atajo. Los datos financieros usan una estimación paramétrica de CAPEX, no una cotización "
    "real — sirve para comparar orden de magnitud entre paneles, no para presupuestar."
)

# ── Prerrequisitos: mismo criterio que 🤖 Análisis IA ────────────────────────
_faltan = []
if st.session_state.get("recurso_solar_ok") is not True:
    _faltan.append("☀️ Recurso Solar")
if st.session_state.get("produccion_ok") is not True:
    _faltan.append("📊 Producción")

if _faltan:
    st.warning(
        "Completa primero: " + ", ".join(_faltan) + ". El comparador necesita el sitio, la "
        "geometría, el string y el inversor ya definidos para simular candidatos reales.",
        icon="🔒",
    )
    st.stop()

if st.session_state.get("inversor_dict_dim") is None:
    st.warning(
        "No hay inversor seleccionado en 📐 Dimensionamiento — sin él, la compatibilidad "
        "eléctrica no es evaluable para ningún panel.",
        icon="🔒",
    )
    st.stop()

# Multi-inversor (corregido 2026-08-22 -- ver la nota en
# simulation/schemas.py::BIPVConfiguration para el detalle completo y por
# qué escalar N_paneles/P_dc_stc_kW como ENTRADAS de la simulación es
# matemáticamente exacto, no una aproximación). Un proyecto con varios
# inversores idénticos (Granja FV típicamente) declara N_inv_total en
# 📐 Dimensionamiento -- _config_base() lo pasa como N_inversores.
_n_inv_total = int(st.session_state.get("N_inv_total", 1) or 1)
if _n_inv_total > 1:
    st.info(
        f"ℹ️ Tu proyecto usa **{_n_inv_total} inversores** — la comparación de abajo "
        "representa el **proyecto completo** (energía, CAPEX y financiero ya escalados "
        f"× {_n_inv_total}), no un solo inversor.",
        icon="ℹ️",
    )


def _config_base() -> BIPVConfiguration:
    ciudad_nombre = st.session_state.get("ciudad")
    c = CIUDADES.get(ciudad_nombre, {})
    lat = float(st.session_state.get("lat_proyecto", c.get("lat", 4.711)))
    lon = float(st.session_state.get("lon_proyecto", c.get("lon", -74.072)))
    alt_m = float(st.session_state.get("alt_proyecto", c.get("alt_m", 2600)))

    return BIPVConfiguration(
        lat=lat, lon=lon, alt_m=alt_m,
        tilt=float(st.session_state.get("tilt_fachada", 90.0)),
        azimuth=float(st.session_state.get("azimuth_fachada", 180.0)),
        area_m2=float(st.session_state.get("area_util_m2", 0.0)),
        albedo=float(st.session_state.get("albedo_suelo", 0.20)),
        N_serie=int(st.session_state.get("N_serie", 1)),
        N_strings_tracker=int(st.session_state.get("N_str_tr_usado", 1)),
        N_inversores=_n_inv_total,
        eta_inversor=float(st.session_state.get("eta_inversor", 0.97)),
        k_bipv=float(st.session_state.get("motor_optico_k_bipv", 1.0)),
        inversor=st.session_state.get("inversor_dict_dim"),
        pct_mismatch_fab=float(st.session_state.get("pct_mismatch_fab", 2.0)),
        pct_soiling=float(st.session_state.get("pct_soiling", 2.0)),
        pct_cableado=float(st.session_state.get("pct_cableado", 1.5)),
        panel={},   # se sobreescribe por candidato en comparar_paneles()
    )


_excluidos = paneles_excluidos_por_ficha_incompleta()
if _excluidos:
    st.info(
        f"ℹ️ {len(_excluidos)} panel(es) del catálogo no aparecen en la comparación por tener "
        f"ficha incompleta (falta potencia nominal Pmax_stc): {', '.join(_excluidos)}. "
        "Complétalos en 📋 Catálogo Paneles para que entren al barrido.",
        icon="ℹ️",
    )

st.subheader("⚙️ Supuestos para estimar CAPEX y financiero")
c1, c2, c3 = st.columns(3)
with c1:
    tipo_instalacion = st.selectbox("Tipo de instalación (referencia CAPEX)", list(BENCH.keys()))
    tarifa = st.number_input(
        "Tarifa (COP/kWh)", min_value=0.0,
        value=float(st.session_state.get("tarifa_cop_kwh", 750.0)), step=10.0,
    )
with c2:
    zona = st.selectbox("Zona (referencia CAPEX)", list(ZONA_FACTOR.keys()))
    trm = st.number_input(
        "TRM (COP/USD)", min_value=1000.0,
        value=float(st.session_state.get("tipo_cambio", 4000.0)), step=50.0,
    )
with c3:
    escenario = st.selectbox("Escenario CAPEX", ["Optimista", "Base", "Conservador"], index=1)
    tasa_desc = st.number_input("Tasa de descuento (%)", min_value=0.0, max_value=30.0, value=10.0, step=0.5)

if st.button("▶️ Comparar paneles", type="primary"):
    with st.spinner("Simulando cada panel con el motor físico completo…"):
        tmy = st.session_state.get("tmy_df")
        df_cmp = comparar_paneles(
            _config_base(), tmy, tipo_instalacion,
            tarifa_cop_kWh=tarifa, tipo_cambio=trm,
            tasa_descuento=tasa_desc / 100.0,
            escenario_capex=escenario, zona_capex=zona,
        )
        st.session_state["_df_comparador_paneles"] = df_cmp

df_cmp = st.session_state.get("_df_comparador_paneles")
if df_cmp is not None and not df_cmp.empty:
    st.subheader("Resultados — ordenado por LCOE (menor primero)")
    st.dataframe(
        df_cmp.drop(columns=["_motivo_electrico"]).style.format({
            "P_dc (kWp)": "{:,.2f}", "E_ac (kWh/año)": "{:,.0f}", "PR": "{:.3f}",
            "CAPEX (USD)": "{:,.0f}", "VPN (USD)": "{:,.0f}", "TIR (%)": "{:.1f}",
            "Payback (años)": "{:.1f}", "LCOE (USD/kWh)": "{:.4f}",
        }, na_rep="—"),
        use_container_width=True, hide_index=True,
    )

    _incompatibles = df_cmp[df_cmp["Compatible"] == "❌"]
    if not _incompatibles.empty:
        for _, r in _incompatibles.iterrows():
            st.warning(f"**{r['Panel']}**: {r['_motivo_electrico']}", icon="⚠️")

    st.download_button(
        "⬇️ Descargar comparativa (CSV)",
        df_cmp.drop(columns=["_motivo_electrico"]).to_csv(index=False).encode("utf-8-sig"),
        "comparativa_paneles.csv", "text/csv",
    )

    _elegibles = df_cmp[df_cmp["Compatible"] != "❌"]["Panel"].tolist()
    if _elegibles:
        _elegido = st.selectbox("Panel a adoptar en el proyecto", _elegibles)
        if st.button("✅ Adoptar este panel", type="primary"):
            from datos.tecnologias_bipv import MODULOS_BIPV
            fila = df_cmp[df_cmp["Panel"] == _elegido].iloc[0]
            st.session_state["panel_dict"] = MODULOS_BIPV[_elegido]
            st.session_state["panel_nombre_dim"] = _elegido
            # "N° módulos"/"P_dc (kWp)" ya son el PROYECTO COMPLETO (× N_inversores,
            # ver comparar_paneles()) -- para un proyecto multi-inversor van en las
            # claves de GRANJA (📐 Dimensionamiento), no en las de "un inversor"
            # (N_paneles_dim/P_dc_stc_kW_dim), que 📊 Producción solo usa como
            # fallback cuando N_paneles_granja no está definido.
            if _n_inv_total > 1:
                st.session_state["N_paneles_granja"] = int(fila["N° módulos"])
                st.session_state["P_dc_total_kWp"] = float(fila["P_dc (kWp)"])
            else:
                st.session_state["N_paneles_dim"] = int(fila["N° módulos"])
                st.session_state["P_dc_stc_kW_dim"] = float(fila["P_dc (kWp)"])
            # Adopción atómica: a diferencia de adoptar un inversor (que solo
            # invalida el lado AC), cambiar de panel invalida TAMBIÉN la POA
            # efectiva del Motor Óptico (depende de NOCT/transparencia del
            # panel) -- por eso aquí SÍ se limpia poa_efectiva_df/
            # poa_sin_termico_df, a diferencia de 4b.
            _limpiadas = [k for k in KEYS_DERIVADOS_POA if k in st.session_state]
            for k in _limpiadas:
                st.session_state.pop(k, None)
            st.success(
                f"Adoptado: **{_elegido}**. Se invalidaron {len(_limpiadas)} resultados "
                "derivados: vuelve a correr 📊 Producción y 💰 Financiero con el panel nuevo."
            )
elif df_cmp is not None:
    st.error("Ningún panel del catálogo pasó la simulación — revisa el mensaje anterior sobre fichas incompletas.")
