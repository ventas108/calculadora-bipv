# -*- coding: utf-8 -*-
"""
⚖️ Comparador de Inversores — Tarea #180
========================================
1. Filtra el catálogo completo por compatibilidad con el panel y string actuales.
2. Compara 2–4 configuraciones (modelo × unidades) con la simulación horaria
   ya corrida en 📊 Producción: E_ac con clipping AC real + financiero 25 años.
3. Barrido de ratio DC/AC con el óptimo por LCOE marcado.
4. Botón para adoptar la configuración ganadora y exportar la tabla.
"""
import math
import os

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Comparador de Inversores", page_icon="⚖️", layout="wide")

from calculos.auth import requerir_login
from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()   # #63 — proyecto activo visible en cada página

requerir_login()

# Sin esto, session_state["tipo_cambio"] no existe hasta que el usuario visite
# 💰 Financiero/💼 Presupuesto en la misma sesión, y el number_input de abajo
# cae silenciosamente en el default hardcodeado (4000.0) en vez de la TRM real
# -- encontrado auditando pages/4c_🧩_Comparador_Paneles.py (hermano de esta
# página, con el mismo patrón de TRM). init_trm() solo hace la llamada al API
# si la clave aún no existe, así que no pisa un valor ya cargado/editado.
from calculos.trm_utils import init_trm
init_trm()


from calculos.comparador_inversores import (
    barrido_dc_ac,
    comparar_configuraciones,
    comparar_todos_los_inversores_compatibles,
    filtrar_inversores_compatibles,
    formatear_comparacion_inversores,
    unidades_necesarias,
)
from calculos.invalidacion import KEYS_DERIVADOS_POA

try:
    from datos.catalogo_inversores_excel import cargar_catalogo_inversores
except Exception:
    cargar_catalogo_inversores = None
from datos.catalogo_inversores import INVERSORES

st.title("⚖️ Comparador de configuraciones de inversor")
st.caption(
    "Filtra el catálogo por compatibilidad eléctrica, compara configuraciones con "
    "la simulación horaria real (clipping incluido) y encuentra el ratio DC/AC óptimo."
)

# ══════════════════════════════════════════════════════════════════════════════
# Prerrequisitos
# ══════════════════════════════════════════════════════════════════════════════
panel = st.session_state.get("panel_dict")
res_prod = st.session_state.get("res_produccion")

if not panel:
    st.warning("⚠️ Primero selecciona el panel en 📐 **Dimensionamiento** (se guarda al optimizar).")
    st.stop()

_faltan = [k for k in ("Voc_stc", "Vmp_stc", "Isc_stc", "Tk_beta", "Tk_gamma") if panel.get(k) is None]
if _faltan:
    st.error(
        f"El panel **{st.session_state.get('panel_nombre_dim', '?')}** no tiene los campos "
        f"necesarios para el filtro eléctrico: `{'`, `'.join(_faltan)}`. "
        "Complétalos en 📋 Catálogo Paneles."
    )
    st.stop()

if res_prod is None or "df_horario" not in res_prod:
    st.warning(
        "⚠️ Este comparador reutiliza la simulación horaria: corre primero "
        "▶️ **Simular producción** en 📊 **Producción** (misma sesión)."
    )
    st.stop()

df_h = res_prod["df_horario"]
# Producción publica la serie horaria como P_ac_kW (ver calculos/produccion.py)
_col_ac = "P_ac_kW" if "P_ac_kW" in df_h.columns else ("P_ac" if "P_ac" in df_h.columns else None)
if _col_ac is None:
    st.error("La simulación guardada no tiene la columna horaria P_ac_kW — vuelve a correr 📊 Producción.")
    st.stop()

# ── Modos donde la serie base NO es la energía oficial del proyecto ──────────
if st.session_state.get("multisup_activo"):
    st.error(
        "🏢 Este proyecto usa **multi-superficie**: la simulación horaria guardada "
        "corresponde a UNA sola superficie, no al total del edificio. El comparador "
        "quedaría con energía incompleta. Usa el desglose de 🏢 Multi-superficie para "
        "dimensionar inversores por superficie."
    )
    st.stop()

# Serie AC horaria SIN límite (W) — el clipping se aplica aquí por configuración
_factor_kW = 1000.0 if _col_ac == "P_ac_kW" else 1.0
p_ac_W = df_h[_col_ac].to_numpy(dtype=float) * _factor_kW

# Corrección bypass: si Producción registró pérdida por diodos de bypass, la
# energía oficial es E_ac_anual_kWh_bypass — se aplica el mismo derating uniforme
# a la serie horaria (aproximación declarada) para que E_ac/LCOE sean coherentes.
_e_base = float(res_prod.get("E_ac_anual_kWh") or 0)
_e_bypass = st.session_state.get("E_ac_anual_kWh_bypass")
if _e_bypass and _e_base > 0 and float(_e_bypass) < _e_base:
    _f_bp = float(_e_bypass) / _e_base
    p_ac_W = p_ac_W * _f_bp
    st.warning(
        f"🌗 Corrección por diodos de bypass aplicada: la serie horaria se escaló por "
        f"×{_f_bp:.4f} para que el total coincida con la E_ac oficial corregida "
        f"({float(_e_bypass):,.0f} kWh/año). Aproximación uniforme — el clipping real "
        "en horas sombreadas puede diferir levemente.",
        icon="⚠️",
    )
p_dc_stc_kW = float(res_prod.get("P_stc_kW") or st.session_state.get("P_dc_stc_kW_dim") or 0)
n_paneles = int(st.session_state.get("N_paneles_dim") or st.session_state.get("N_paneles_granja") or 0)

st.info(
    f"Simulación base: **{p_dc_stc_kW:.2f} kWp** · {n_paneles} módulos "
    f"**{st.session_state.get('panel_nombre_final', st.session_state.get('panel_nombre_dim', ''))}** · "
    f"E_ac sin límite AC = **{np.nan_to_num(p_ac_W).sum()/1000:,.0f} kWh/año** · "
    f"pico AC = **{np.nan_to_num(p_ac_W).max()/1000:,.1f} kW**"
)

# ══════════════════════════════════════════════════════════════════════════════
# 1. Filtro de compatibilidad
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("1️⃣ Inversores del catálogo compatibles con tu string")

c1, c2, c3 = st.columns(3)
with c1:
    N_serie = st.number_input(
        "Módulos en serie por string (N)",
        min_value=4, max_value=40,
        value=int(st.session_state.get("N_serie", 18)),
        help="El mismo N del Dimensionamiento. Cambia para explorar strings más largos/cortos.",
    )
with c2:
    T_frio = st.number_input(
        "T. mínima de diseño (°C)",
        min_value=-30.0, max_value=30.0,
        value=float(st.session_state.get("T_min_diseno", 10.0)),
        help="Para el Voc frío del string. En clima cálido (Urabá ~22 °C) casi no corrige.",
    )
with c3:
    T_real = st.number_input(
        "T. de celda realista (°C)",
        min_value=10.0, max_value=80.0,
        value=float(st.session_state.get("T_cel_realista", 36.35)),
        help="Para el Vmp realista del string (verificación de ventana MPPT).",
    )

_cat = {}
if cargar_catalogo_inversores is not None:
    try:
        _cat = cargar_catalogo_inversores() or {}
    except Exception:
        _cat = {}
if not _cat:
    _cat = INVERSORES

df_comp = filtrar_inversores_compatibles(panel, _cat, int(N_serie), T_frio, T_real)
n_ok = int(df_comp["compatible"].sum())
st.markdown(
    f"**{n_ok} de {len(df_comp)} inversores** del catálogo aceptan strings de "
    f"**{int(N_serie)} × {st.session_state.get('panel_nombre_dim', 'panel actual')}** "
    f"(Voc frío {df_comp['Voc_string_frio (V)'].iloc[0]:,.0f} V · "
    f"Isc×1,25 = {panel['Isc_stc'] * 1.25:.1f} A por string)."
)

_df_view = df_comp.copy()
_df_view["compatible"] = _df_view["compatible"].map({True: "✅", False: "—"})
st.dataframe(
    _df_view[["modelo", "compatible", "modo", "strings_max", "P_ac_nom_kW", "costo_usd", "motivo"]],
    use_container_width=True, height=300,
)
st.caption(
    "**modo** = cómo conectar: *normal* usa todos los strings por tracker; "
    "*1 string/tracker* significa que la corriente del panel obliga a conectar un solo "
    "string por entrada MPPT (se usan más entradas, sin riesgo eléctrico)."
)

# ══════════════════════════════════════════════════════════════════════════════
# 2. Configuraciones candidatas
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("2️⃣ Configuraciones candidatas (E_ac, clipping y financiero)")

n_strings_total = max(1, math.ceil(n_paneles / int(N_serie))) if n_paneles else 1
st.caption(f"Strings totales del proyecto: **{n_strings_total}** ({n_paneles} módulos / {int(N_serie)} en serie).")
if n_paneles and n_paneles % int(N_serie) != 0:
    st.warning(
        f"⚠️ {n_paneles} módulos NO es múltiplo de {int(N_serie)} en serie: quedaría un string "
        f"parcial de {n_paneles % int(N_serie)} módulos (eléctricamente inválido — distinta tensión). "
        f"Ajusta N o el número de módulos (p. ej. {(n_paneles // int(N_serie)) * int(N_serie)} módulos = "
        f"{n_paneles // int(N_serie)} strings completos).",
        icon="⚠️",
    )

_compatibles = df_comp[df_comp["compatible"]]
if _compatibles.empty:
    st.error("Ningún inversor del catálogo es compatible — revisa N en serie o carga fichas nuevas en 🔌 Catálogo Inversores.")
    st.stop()

_sel = st.multiselect(
    "Elige 2–4 modelos a comparar",
    _compatibles["modelo"].tolist(),
    max_selections=4,
    help="Las unidades necesarias se calculan solas según las entradas de cada equipo.",
)

with st.expander("⚙️ Supuestos financieros del comparador", expanded=False):
    f1, f2, f3 = st.columns(3)
    with f1:
        # Inicializar ANTES del widget y usar solo key= (evita el conflicto
        # value+key de Streamlit tras la primera ejecución).
        st.session_state.setdefault("comp_capex_sin_inv", 150_000.0)
        capex_sin_inv = st.number_input(
            "CAPEX sin inversores (USD)",
            min_value=0.0, step=1000.0, key="comp_capex_sin_inv",
            help="Todo el proyecto menos los inversores (módulos, estructura, BOS, montaje, blandos).",
        )
        tarifa = st.number_input(
            "Tarifa (COP/kWh)", min_value=0.0,
            value=float(st.session_state.get("tarifa_cop_kwh", 950.0)), step=10.0,
        )
    with f2:
        trm = st.number_input(
            "TRM (COP/USD)", min_value=1000.0,
            value=float(st.session_state.get("tipo_cambio", 4000.0)), step=50.0,
        )
        tasa_desc = st.number_input("Tasa de descuento (%)", min_value=0.0, max_value=30.0, value=10.0, step=0.5)
    with f3:
        degradacion = st.number_input("Degradación (%/año)", min_value=0.0, max_value=2.0, value=0.4, step=0.1)
        opex_pct = st.number_input("OPEX (% del CAPEX/año)", min_value=0.0, max_value=10.0, value=1.5, step=0.1)

if _sel:
    configs, avisos = [], []
    for m in _sel:
        row = _compatibles[_compatibles["modelo"] == m].iloc[0]
        p_ac_u = (row["P_ac_nom_kW"] or 0) * 1000.0
        if p_ac_u <= 0:
            avisos.append(f"**{m}**: sin potencia AC nominal en el catálogo — se excluye.")
            continue
        n_u = unidades_necesarias(n_strings_total, int(row["strings_max"]))
        costo_u = row["costo_usd"]
        if costo_u is None:
            avisos.append(f"**{m}**: sin costo en el catálogo — CAPEX solo incluye la base (compara E_ac/clipping, no LCOE).")
            costo_u = 0.0
        configs.append({
            "nombre": f"{m}" + (" (1 str/MPPT)" if row["modo"] == "1 string/tracker" else ""),
            "p_ac_unidad_W": p_ac_u,
            "n_unidades": n_u,
            "costo_unidad_usd": costo_u,
        })
    for a in avisos:
        st.warning(a, icon="⚠️")

    if configs:
        df_cmp = comparar_configuraciones(
            p_ac_W, configs, p_dc_stc_kW,
            capex_sin_inversores_usd=capex_sin_inv,
            tarifa_cop_kwh=tarifa, tipo_cambio=trm,
            tasa_descuento=tasa_desc / 100.0,
            tasa_degradacion_pct=degradacion,
            opex_pct_capex=opex_pct,
        )
        st.dataframe(
            df_cmp.style.format({
                "E_ac (kWh/año)": "{:,.0f}", "CAPEX (USD)": "{:,.0f}",
                "VPN (USD)": "{:,.0f}", "Clipping (%)": "{:.2f}",
                "TIR (%)": "{:.1f}", "Payback (años)": "{:.1f}",
                "LCOE (USD/kWh)": "{:.4f}", "LCOE (COP/kWh)": "{:.0f}",
            }, na_rep="—"),
            use_container_width=True,
        )
        st.download_button(
            "⬇️ Descargar comparativa (CSV)",
            df_cmp.to_csv(index=False).encode("utf-8-sig"),
            "comparativa_inversores.csv", "text/csv",
        )

        # ── Adoptar configuración ganadora ────────────────────────────────────
        _opciones = df_cmp["Configuración"].tolist()
        _elegida = st.selectbox("Configuración a adoptar en el proyecto", _opciones)
        if st.button("✅ Adoptar esta configuración", type="primary"):
            _idx = _opciones.index(_elegida)
            _modelo_full = configs[_idx]["nombre"].replace(" (1 str/MPPT)", "")
            st.session_state["inversor_nombre_dim"] = _modelo_full
            st.session_state["inversor_dict_dim"] = _cat.get(_modelo_full, {})
            st.session_state["N_inv_total"] = configs[_idx]["n_unidades"]
            st.session_state["N_serie"] = int(N_serie)
            # Adopción atómica: la producción/bypass/financiero/CO₂ guardados
            # corresponden al inversor ANTERIOR → se invalidan (misma filosofía
            # de calculos/invalidacion.py; POA no depende del inversor).
            _KEYS_DERIVADOS_INVERSOR = tuple(
                k for k in KEYS_DERIVADOS_POA if k != "poa_efectiva_df"
            )
            _limpiadas = [k for k in _KEYS_DERIVADOS_INVERSOR if k in st.session_state]
            for k in _limpiadas:
                st.session_state.pop(k, None)
            st.success(
                f"Adoptado: **{_elegida}** (N={int(N_serie)} en serie, "
                f"{configs[_idx]['n_unidades']} unidades). Se invalidaron "
                f"{len(_limpiadas)} resultados derivados: vuelve a correr "
                "📊 Producción y 💰 Financiero con la nueva configuración."
            )

# ══════════════════════════════════════════════════════════════════════════════
# Comparar TODOS los inversores compatibles + Analista de Producción
# ══════════════════════════════════════════════════════════════════════════════
# A diferencia del multiselect de arriba (2-4 modelos elegidos a mano), esto
# corre para TODO el catálogo compatible de una sola vez -- barato porque
# reusa la misma serie horaria p_ac_W ya simulada (solo aplica clipping/
# escala por candidato, no vuelve a correr física). No reemplaza el flujo
# manual: ese sigue sirviendo para comparar puntualmente 2-4 modelos que ya
# tienes en mente; esto sirve para un barrido amplio con opinión de IA.
st.markdown("---")
st.subheader("🔍 Comparar TODOS los inversores compatibles del catálogo")
st.caption(
    f"Corre la misma comparación de arriba (E_ac con clipping real, CAPEX, VPN, TIR, LCOE) "
    f"para los **{n_ok} inversores compatibles** con tu string actual, de una sola vez."
)

if st.button("▶️ Comparar todos los inversores", type="primary", key="btn_comparar_todos_inv"):
    df_inv_cmp = comparar_todos_los_inversores_compatibles(
        df_comp, n_strings_total, p_ac_W, p_dc_stc_kW,
        capex_sin_inversores_usd=capex_sin_inv,
        tarifa_cop_kwh=tarifa, tipo_cambio=trm,
        tasa_descuento=tasa_desc / 100.0,
        tasa_degradacion_pct=degradacion, opex_pct_capex=opex_pct,
    )
    st.session_state["_df_comparador_inversores"] = df_inv_cmp

df_inv_cmp = st.session_state.get("_df_comparador_inversores")
if df_inv_cmp is not None and not df_inv_cmp.empty:
    _cols_internas_inv = [c for c in df_inv_cmp.columns if c.startswith("_")]
    st.dataframe(
        df_inv_cmp.drop(columns=_cols_internas_inv).style.format({
            "AC total (kW)": "{:,.1f}", "Ratio DC/AC": "{:.2f}",
            "E_ac (kWh/año)": "{:,.0f}", "Clipping (%)": "{:.2f}",
            "CAPEX (USD)": "{:,.0f}", "VPN (USD)": "{:,.0f}", "TIR (%)": "{:.1f}",
            "Payback (años)": "{:.1f}", "LCOE (USD/kWh)": "{:.4f}", "LCOE (COP/kWh)": "{:.0f}",
        }, na_rep="—"),
        use_container_width=True, hide_index=True,
    )

    _incompatibles_inv = df_inv_cmp[df_inv_cmp["Compatible"] == "❌"]
    if not _incompatibles_inv.empty:
        for _, r in _incompatibles_inv.iterrows():
            st.warning(f"**{r['Modelo']}**: {r['_motivo']}", icon="⚠️")

    # Compatibles con CAPEX/LCOE que NO incluye el costo real del inversor
    # (el catálogo no lo trae) -- mismo aviso que ya daba el flujo manual de
    # arriba, ahora también aquí para no perderlo al comparar todo el catálogo.
    _sin_costo_inv = df_inv_cmp[(df_inv_cmp["Compatible"] == "✅") & (df_inv_cmp["_motivo"] != "")]
    if not _sin_costo_inv.empty:
        st.warning(
            f"⚠️ **{len(_sin_costo_inv)} de {int((df_inv_cmp['Compatible'] == '✅').sum())}** "
            "modelos compatibles no tienen costo en el catálogo — su CAPEX/LCOE en la tabla "
            "de arriba solo incluye el CAPEX base, no el costo del equipo. No son comparables "
            "en igualdad de condiciones contra un modelo que sí tenga costo real: "
            + ", ".join(f"**{m}**" for m in _sin_costo_inv["Modelo"]) + "."
        )

    st.download_button(
        "⬇️ Descargar comparativa completa (CSV)",
        df_inv_cmp.drop(columns=_cols_internas_inv).to_csv(index=False).encode("utf-8-sig"),
        "comparativa_todos_inversores.csv", "text/csv",
    )

    st.divider()
    st.subheader("🔍 Analista de Producción")
    st.caption(
        "Agente de IA (Claude) que lee SOLO la comparación de arriba — nunca inventa un "
        "número — y opina qué inversor conviene implementar. Criterio técnico (energía con "
        "clipping real, % de clipping, compatibilidad eléctrica), no financiero: esa decisión "
        "sigue siendo del Asesor de Inversión, en 🤖 Análisis IA."
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
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        st.info(
            "Falta `ANTHROPIC_API_KEY` en el entorno del servidor para activar este agente "
            "(el resto de la página funciona igual sin ella). En el droplet: "
            "`export ANTHROPIC_API_KEY=\"sk-ant-...\"` → `pm2 restart streamlit-bipv "
            "--update-env` → `pm2 save`.",
            icon="🔑",
        )
    elif st.button("🔍 Ejecutar Analista de Producción", key="btn_analista_inversores"):
        with st.spinner("Consultando a Claude (Analista de Producción)…"):
            try:
                from agentes.analista_produccion import (
                    ejecutar_analisis_produccion, texto_final as _texto_analista_prod,
                )
                _tipo_inst_inv = st.session_state.get("tipo_instalacion", "no especificado en el proyecto")
                contexto = formatear_comparacion_inversores(df_inv_cmp, _tipo_inst_inv)
                pregunta = (
                    "Analiza estos inversores y dame tu recomendación técnica sobre cuál "
                    "implementar, considerando energía con clipping real y compatibilidad "
                    "eléctrica con el string ya definido."
                )
                mensaje = ejecutar_analisis_produccion(contexto, pregunta=pregunta)
                st.session_state["ia_inversor_texto"] = _texto_analista_prod(mensaje)
                st.session_state["ia_inversor_uso"] = (
                    mensaje.usage.input_tokens, mensaje.usage.output_tokens,
                )
            except Exception as e:
                st.session_state["ia_inversor_texto"] = None
                st.error(f"❌ {e}")

    if st.session_state.get("ia_inversor_texto"):
        st.markdown(st.session_state["ia_inversor_texto"])
        tin, tout = st.session_state.get("ia_inversor_uso", (0, 0))
        st.caption(f"🔢 {tin:,} tokens de entrada · {tout:,} de salida")
        if st.button("🗑️ Limpiar", key="btn_limpiar_analista_inversores"):
            st.session_state.pop("ia_inversor_texto", None)
            st.session_state.pop("ia_inversor_uso", None)
            st.rerun()
elif df_inv_cmp is not None:
    st.error("Ningún inversor pudo compararse — revisa el catálogo o el filtro de compatibilidad arriba.")

# ══════════════════════════════════════════════════════════════════════════════
# 3. Barrido de ratio DC/AC
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("3️⃣ Barrido de ratio DC/AC — ¿cuánta capacidad AC realmente necesitas?")

b1, b2 = st.columns(2)
with b1:
    costo_kw_ac = st.number_input(
        "Costo de inversor (USD por kW AC)",
        min_value=5.0, max_value=500.0, value=43.0, step=1.0,
        help="Referencia clase string 100 kW ≈ 40–55 USD/kW. Ajusta con cotizaciones reales.",
    )
with b2:
    st.caption(
        "La capacidad AC de cada punto = kWp / ratio. El costo del inversor escala con "
        "los kW AC; el resto del CAPEX es el mismo de arriba. ⭐ marca el LCOE mínimo."
    )

# Los supuestos financieros del expander aplican también aquí (siempre definidos).
df_sweep = barrido_dc_ac(
    p_ac_W, p_dc_stc_kW,
    capex_sin_inversores_usd=capex_sin_inv,
    costo_usd_por_kw_ac=costo_kw_ac,
    tarifa_cop_kwh=tarifa,
    tipo_cambio=trm,
    tasa_descuento=tasa_desc / 100.0,
    tasa_degradacion_pct=degradacion,
    opex_pct_capex=opex_pct,
)
st.dataframe(
    df_sweep.style.format({
        "E_ac (kWh/año)": "{:,.0f}", "CAPEX (USD)": "{:,.0f}",
        "Clipping (%)": "{:.2f}", "TIR (%)": "{:.1f}", "LCOE (USD/kWh)": "{:.4f}",
    }, na_rep="—"),
    use_container_width=True,
)

_row_opt = df_sweep[df_sweep["óptimo"] == "⭐"]
if not _row_opt.empty:
    _r = _row_opt.iloc[0]
    st.success(
        f"⭐ Óptimo por LCOE: **ratio {_r['Ratio DC/AC']}** → "
        f"**{_r['AC (kW)']:,.1f} kW AC** · clipping {_r['Clipping (%)']:.2f}% · "
        f"LCOE {_r['LCOE (USD/kWh)']:.4f} USD/kWh. "
        "Busca inversores cuya suma de potencia AC se acerque a ese valor."
    )

_chart = df_sweep.set_index("Ratio DC/AC")[["Clipping (%)"]].join(
    df_sweep.set_index("Ratio DC/AC")["LCOE (USD/kWh)"] * 1000
).rename(columns={"LCOE (USD/kWh)": "LCOE (milésimas USD/kWh)"})
st.line_chart(_chart)

st.download_button(
    "⬇️ Descargar barrido DC/AC (CSV)",
    df_sweep.to_csv(index=False).encode("utf-8-sig"),
    "barrido_dc_ac.csv", "text/csv",
)
