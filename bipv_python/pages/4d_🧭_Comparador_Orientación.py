# -*- coding: utf-8 -*-
"""
🧭 Comparador de Orientación — hermano de 4b ⚖️ Comparador de Inversores y
4c 🧩 Comparador de Paneles, pero variando GEOMETRÍA (tilt/azimuth) en vez
de hardware.

Responde la pregunta "¿cuál sería la mejor posición de mi fachada/superficie
respecto al azimut e inclinación, para maximizar la generación?" -- barre
una malla de tilt × azimuth sobre el MISMO sitio, panel, inversor y strings
del proyecto, re-simulando cada combinación con run_bipv_simulation() (motor
de Fase 2/4 completo, no un atajo), y deja opinar al mismo Analista de
Producción (agentes/analista_produccion.py) que ya evalúa paneles.

A diferencia de 4c: el hardware no cambia, así que no hay CAPEX ni
compatibilidad eléctrica que comparar -- ver calculos/comparador_orientacion.py.

Advertencia de costo real: cada combinación de la malla es una simulación
física de 8.760 horas -- una malla fina (paso pequeño en tilt Y azimuth)
puede tardar. La página avisa el tamaño de la malla ANTES de correrla.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Comparador de Orientación", page_icon="🧭", layout="wide")

from calculos.auth import requerir_login
requerir_login()

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()   # #63 — proyecto activo visible en cada página

from datos.ciudades_colombia import CIUDADES
from calculos.solar import ORIENTACIONES, calcular_poa
from calculos.comparador_orientacion import (
    comparar_orientacion,
    formatear_comparacion_orientacion,
    malla_tilt_azimuth,
)
from calculos.invalidacion import KEYS_DERIVADOS_POA
from simulation.schemas import BIPVConfiguration
from agentes.analista_produccion import ejecutar_analisis_produccion, texto_final as _texto_analista_prod

# Mismo hallazgo que en 4c/4b: sin esto, session_state["tipo_cambio"] no
# existe hasta que el usuario visite 💰 Financiero/💼 Presupuesto en esta
# sesión. Esta página no usa TRM directamente, pero mostrar_proyecto_activo()
# y otras utilidades compartidas sí pueden leerla -- se llama por consistencia
# con las páginas hermanas.
from calculos.trm_utils import init_trm
init_trm()

st.title("🧭 Comparador de Orientación")
st.caption(
    "Barre inclinación (tilt) y orientación (azimuth) sobre el MISMO sitio, panel, inversor "
    "y strings de tu proyecto — re-simula cada combinación con el motor físico completo "
    "(SDM De Soto), no un atajo ni una fórmula aproximada. El hardware no cambia entre "
    "candidatos: el criterio es puramente energético (E_ac, PR), no financiero."
)
st.page_link(
    "pages/4c_🧩_Comparador_Paneles.py",
    label="¿Buscas comparar hardware en vez de orientación? Ir a 🧩 Comparador de Paneles →",
    icon="🧩",
)

# ── Prerrequisitos: mismo criterio que 4c ────────────────────────────────────
_faltan = []
if st.session_state.get("recurso_solar_ok") is not True:
    _faltan.append("☀️ Recurso Solar")
if st.session_state.get("produccion_ok") is not True:
    _faltan.append("📊 Producción")

if _faltan:
    st.warning(
        "Completa primero: " + ", ".join(_faltan) + ". El comparador necesita el sitio, el "
        "panel, el string y el inversor ya definidos para simular candidatos reales.",
        icon="🔒",
    )
    st.stop()

if not st.session_state.get("panel_dict"):
    st.warning("No hay panel seleccionado en 📐 Dimensionamiento — sin él no se puede simular ninguna orientación.", icon="🔒")
    st.stop()

if st.session_state.get("inversor_dict_dim") is None:
    st.warning("No hay inversor seleccionado en 📐 Dimensionamiento — sin él no se puede simular ninguna orientación.", icon="🔒")
    st.stop()

# Multi-inversor (ver la nota completa en pages/4c_🧩_Comparador_Paneles.py y
# simulation/schemas.py::BIPVConfiguration) -- misma lógica: si el proyecto
# declaró varios inversores idénticos en 📐 Dimensionamiento, cada fila del
# barrido ya representa el PROYECTO COMPLETO, no un solo inversor.
_n_inv_total = int(st.session_state.get("N_inv_total", 1) or 1)
if _n_inv_total > 1:
    st.info(
        f"ℹ️ Tu proyecto usa **{_n_inv_total} inversores** — cada fila de abajo representa el "
        f"**proyecto completo** (energía ya escalada × {_n_inv_total}), no un solo inversor.",
        icon="ℹ️",
    )


def _coords_proyecto() -> tuple[float, float, float]:
    ciudad_nombre = st.session_state.get("ciudad")
    c = CIUDADES.get(ciudad_nombre, {})
    lat = float(st.session_state.get("lat_proyecto", c.get("lat", 4.711)))
    lon = float(st.session_state.get("lon_proyecto", c.get("lon", -74.072)))
    alt_m = float(st.session_state.get("alt_proyecto", c.get("alt_m", 2600)))
    return lat, lon, alt_m


def _config_base() -> BIPVConfiguration:
    from calculos.dimensionamiento import diseno_electrico_confirmado
    _diseno_co = diseno_electrico_confirmado(st.session_state)
    if _diseno_co["aviso"]:
        st.warning(_diseno_co["aviso"])
    lat, lon, alt_m = _coords_proyecto()
    return BIPVConfiguration(
        lat=lat, lon=lon, alt_m=alt_m,
        tilt=float(st.session_state.get("tilt_fachada", 90.0)),
        azimuth=float(st.session_state.get("azimuth_fachada", 180.0)),
        area_m2=float(st.session_state.get("area_util_m2", 0.0)),
        albedo=float(st.session_state.get("albedo_suelo", 0.20)),
        panel=st.session_state.get("panel_dict") or {},
        N_serie=int(_diseno_co["N_serie"] or 1),
        N_strings_tracker=_diseno_co["N_strings_tracker"],
        N_inversores=_n_inv_total,
        eta_inversor=float(st.session_state.get("eta_inversor", 0.97)),
        k_bipv=float(st.session_state.get("motor_optico_k_bipv", 1.0)),
        inversor=st.session_state.get("inversor_dict_dim"),
        pct_mismatch_fab=float(st.session_state.get("pct_mismatch_fab", 2.0)),
        pct_soiling=float(st.session_state.get("pct_soiling", 2.0)),
        pct_cableado=float(st.session_state.get("pct_cableado", 1.5)),
    )


_cfg_actual = _config_base()

st.subheader("⚙️ Malla de barrido")
st.caption(
    f"Orientación actual del proyecto: tilt={_cfg_actual.tilt:.0f}°, "
    f"azimuth={_cfg_actual.azimuth:.0f}°. Se incluye siempre en el barrido, aunque no caiga "
    "exactamente en la malla."
)
c1, c2 = st.columns(2)
with c1:
    st.markdown("**Inclinación (tilt)**")
    tilt_min, tilt_max = st.slider(
        "Rango de tilt (°)", min_value=0, max_value=90, value=(0, 90),
        help="0°=horizontal, 90°=vertical (fachada). Mismo rango físico que el slider de 📐 Recurso Solar.",
    )
    tilt_paso = st.number_input("Paso de tilt (°)", min_value=1.0, max_value=45.0, value=15.0, step=1.0)
with c2:
    st.markdown("**Orientación (azimuth)**")
    azimuth_min, azimuth_max = st.slider(
        "Rango de azimuth (°)", min_value=0, max_value=360, value=(0, 360),
        help="Convención pvlib: 0°=Norte, 90°=Este, 180°=Sur, 270°=Oeste.",
    )
    azimuth_paso = st.number_input("Paso de azimuth (°)", min_value=1.0, max_value=180.0, value=45.0, step=1.0)

tilt_valores, azimuth_valores = malla_tilt_azimuth(
    tilt_min=float(tilt_min), tilt_max=float(tilt_max), tilt_paso=float(tilt_paso),
    azimuth_min=float(azimuth_min), azimuth_max=float(azimuth_max), azimuth_paso=float(azimuth_paso),
    tilt_actual=_cfg_actual.tilt, azimuth_actual=_cfg_actual.azimuth,
)
_n_sims = len(tilt_valores) * len(azimuth_valores)
st.caption(
    f"Malla: {len(tilt_valores)} valores de tilt × {len(azimuth_valores)} valores de azimuth "
    f"= **{_n_sims} simulaciones** de 8.760 horas."
)
if _n_sims > 80:
    st.warning(
        f"{_n_sims} simulaciones es una malla grande — puede tardar varios minutos. "
        "Considera un paso más grueso (tilt/azimuth) o un rango más acotado.",
        icon="⏱️",
    )

if st.button("▶️ Comparar orientaciones", type="primary"):
    with st.spinner(f"Simulando {_n_sims} combinaciones de tilt/azimuth con el motor físico completo…"):
        tmy = st.session_state.get("tmy_df")
        df_or = comparar_orientacion(_cfg_actual, tmy, tilt_valores, azimuth_valores)
        st.session_state["_df_comparador_orientacion"] = df_or

df_or = st.session_state.get("_df_comparador_orientacion")
if df_or is not None and not df_or.empty:
    st.subheader("Resultados — ordenado por energía anual (mayor primero)")
    st.dataframe(
        df_or.style.format({
            "Tilt (°)": "{:.0f}", "Azimuth (°)": "{:.0f}", "P_dc (kWp)": "{:,.2f}",
            "E_ac (kWh/año)": "{:,.0f}", "PR": "{:.3f}",
        }).apply(
            lambda fila: ["background-color: #fff3cd" if fila["Actual"] else "" for _ in fila],
            axis=1,
        ),
        use_container_width=True, hide_index=True,
    )
    st.caption("🟡 Fila resaltada = orientación actual del proyecto.")

    if len(tilt_valores) > 1 and len(azimuth_valores) > 1:
        st.subheader("🗺️ Mapa de calor — energía anual (kWh/año) por tilt × azimuth")
        pivot = df_or.pivot_table(index="Tilt (°)", columns="Azimuth (°)", values="E_ac (kWh/año)")
        fig = go.Figure(go.Heatmap(
            z=pivot.values, x=pivot.columns, y=pivot.index,
            colorscale="YlOrRd", colorbar=dict(title="kWh/año"),
        ))
        fig.update_layout(xaxis_title="Azimuth (°)", yaxis_title="Tilt (°)", height=400)
        st.plotly_chart(fig, use_container_width=True)

    _mejor = df_or.iloc[0]
    st.success(
        f"🏆 Mejor combinación simulada: **tilt={_mejor['Tilt (°)']:.0f}°, "
        f"azimuth={_mejor['Azimuth (°)']:.0f}°** — {_mejor['E_ac (kWh/año)']:,.0f} kWh/año "
        f"(PR={_mejor['PR']:.3f})."
    )

    st.download_button(
        "⬇️ Descargar comparativa (CSV)",
        df_or.to_csv(index=False).encode("utf-8-sig"),
        "comparativa_orientacion.csv", "text/csv",
    )

    st.divider()
    st.subheader("🔍 Analista de Producción")
    st.caption(
        "Agente de IA (Claude) que lee SOLO la comparación de arriba — nunca inventa un "
        "número — y opina cuál orientación conviene implementar para optimizar la generación "
        "de energía. Criterio técnico (energía, PR), no financiero."
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
    elif st.button("🔍 Ejecutar Analista de Producción", key="btn_analista_orient"):
        with st.spinner("Consultando a Claude (Analista de Producción)…"):
            try:
                tipo_instalacion = st.session_state.get("tipo_instalacion", "no especificado en el proyecto")
                contexto = formatear_comparacion_orientacion(df_or, tipo_instalacion)
                pregunta = (
                    "Analiza estas combinaciones de tilt/azimuth y dame tu recomendación técnica "
                    "sobre cuál orientación conviene implementar para optimizar la generación de "
                    "energía."
                )
                mensaje = ejecutar_analisis_produccion(contexto, pregunta=pregunta)
                st.session_state["ia_orientacion_texto"] = _texto_analista_prod(mensaje)
                st.session_state["ia_orientacion_uso"] = (
                    mensaje.usage.input_tokens, mensaje.usage.output_tokens,
                )
            except Exception as e:
                st.session_state["ia_orientacion_texto"] = None
                st.error(f"❌ {e}")

    if st.session_state.get("ia_orientacion_texto"):
        st.markdown(st.session_state["ia_orientacion_texto"])
        tin, tout = st.session_state.get("ia_orientacion_uso", (0, 0))
        st.caption(f"🔢 {tin:,} tokens de entrada · {tout:,} de salida")
        if st.button("🗑️ Limpiar", key="btn_limpiar_analista_orient"):
            st.session_state.pop("ia_orientacion_texto", None)
            st.session_state.pop("ia_orientacion_uso", None)
            st.rerun()

    st.divider()
    st.subheader("✅ Adoptar una orientación")
    st.caption(
        "Recalcula la POA del sitio (mismo TMY, nueva geometría) y actualiza tilt/azimuth del "
        "proyecto -- equivale a volver a 📐 Recurso Solar y cambiar el slider manualmente, pero "
        "sin perder el resultado del barrido. Invalida producción/financiero/CO₂: hay que "
        "volver a correr esas páginas con la orientación nueva."
    )
    _opciones = [
        f"tilt={r['Tilt (°)']:.0f}°, azimuth={r['Azimuth (°)']:.0f}° "
        f"({r['E_ac (kWh/año)']:,.0f} kWh/año)"
        for _, r in df_or.iterrows()
    ]
    _idx_elegido = st.selectbox("Combinación a adoptar", range(len(_opciones)), format_func=lambda i: _opciones[i])
    if st.button("✅ Adoptar esta orientación", type="primary"):
        _fila = df_or.iloc[_idx_elegido]
        _tilt_adopt = float(_fila["Tilt (°)"])
        _az_adopt = float(_fila["Azimuth (°)"])
        _albedo_actual = float(st.session_state.get("albedo_suelo", 0.20))
        lat, lon, alt_m = _coords_proyecto()
        tmy = st.session_state.get("tmy_df")
        _bifacial_cfg = st.session_state.get("bifacial_cfg") if st.session_state.get("bifacial_activo") else None

        # Recalcula la POA localmente para la nueva geometría -- mismo TMY del
        # sitio, misma lógica que el branch "_drift_geom" de
        # pages/2_☀️_Recurso_Solar.py cuando detecta que tilt/azimuth cambiaron.
        # Sin este recálculo, poa_df quedaría desfasado del nuevo tilt_fachada/
        # azimuth_fachada -- justo el tipo de inconsistencia silenciosa que
        # calculos/invalidacion.py existe para evitar.
        poa_nueva = calcular_poa(
            tmy, lat, lon, alt_m, _tilt_adopt, _az_adopt,
            albedo=_albedo_actual, bifacial=_bifacial_cfg,
        )
        _orientacion_label_adopt = next(
            (lbl for lbl, az in ORIENTACIONES.items() if abs(az - _az_adopt) < 0.5),
            f"Azimuth {_az_adopt:.0f}°",
        )
        st.session_state.update({
            "tilt_fachada": _tilt_adopt,
            "tilt_default": _tilt_adopt,
            "azimuth_fachada": _az_adopt,
            "orientacion_label": _orientacion_label_adopt,
            "poa_df": poa_nueva,
            "poa_anual_kWh_m2": round(poa_nueva["poa_global"].sum() / 1000.0, 1),
            # Guardas de drift (#64/#172) -- si no se actualizan aquí, la próxima
            # visita a 📐 Recurso Solar detectaría un "drift" falso (o, peor,
            # ninguno, si el slider vuelve al tilt_default viejo) contra la
            # geometría que acabamos de adoptar.
            "_solar_tilt_guardado": _tilt_adopt,
            "_solar_az_guardado": _az_adopt,
            "_solar_albedo_guardado": _albedo_actual,
        })
        _limpiadas = [k for k in KEYS_DERIVADOS_POA if k in st.session_state]
        for k in _limpiadas:
            st.session_state.pop(k, None)
        st.success(
            f"Adoptado: **tilt={_tilt_adopt:.0f}°, azimuth={_az_adopt:.0f}°**. POA recalculada. "
            f"Se invalidaron {len(_limpiadas)} resultados derivados: vuelve a correr "
            "📊 Producción y 💰 Financiero con la orientación nueva."
        )
elif df_or is not None:
    st.error("El barrido no produjo ninguna fila — revisa la malla configurada arriba.")
