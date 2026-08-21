# -*- coding: utf-8 -*-
"""Página 18 — Análisis IA: interpretación técnica-financiera y recomendación
de inversión sobre el diseño YA calculado del proyecto activo (Fase 5).

Alcance v1 — deliberadamente acotado: analiza el ÚNICO diseño actual (los
resultados que ya muestran 📊 Producción y 💰 Financiero), NO genera variantes
ni corre un barrido de sensibilidad (Fase 4) nuevo. Ampliar a "explorar
variantes cercanas" es un paso posterior — requiere reconstruir
FinancialConfiguration completo desde session_state (tasa de descuento, OPEX,
escalación...), varios de esos parámetros hoy son variables locales de
🔀_Mismatch/💰_Financiero, no claves persistidas, y reconstruirlos mal
correría el riesgo real de que el barrido use una tasa de descuento distinta
a la que el usuario configuró — un candidato inventado silenciosamente, que
es justo lo que este proyecto evita en cada módulo. Mejor no ofrecerlo que
ofrecerlo con un supuesto incorrecto agazapado.

Los dos agentes (agentes/analista_tecnico_financiero.py,
agentes/asesor_inversion.py) hacen llamadas reales a la API de Anthropic
(claude-opus-5) — cada clic en "Ejecutar" tiene un costo pequeño pero real.
Nunca se ejecutan automáticamente al cargar la página.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(page_title="Análisis IA — BIPV", page_icon="🤖", layout="wide")

from calculos.auth import requerir_login
requerir_login()

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()   # #63 — proyecto activo visible en cada página

from datos.ciudades_colombia import CIUDADES
from simulation.schemas import BIPVConfiguration, FinancialResult
from optimization.numerical_optimizer import ResultadoCandidato
from agentes.herramientas import CandidatoRegistrado, formatear_candidatos
from agentes.analista_tecnico_financiero import ejecutar_analisis, texto_final as _texto_analista
from agentes.asesor_inversion import ejecutar_asesoria, texto_final as _texto_asesor

st.title("🤖 Análisis IA")
st.caption(
    "Los agentes de IA (Claude, vía Anthropic) leen SOLO resultados que la calculadora "
    "ya calculó — nunca inventan un número financiero ni de producción. Cada botón de "
    "abajo hace una llamada real a la API y tiene un costo pequeño; no se ejecuta nada "
    "automáticamente."
)
st.info(
    "Estos son 2 de los 3 agentes de IA de la calculadora — el Analista Técnico-Financiero "
    "y el Asesor de Inversión, ambos aquí abajo. El tercero, el **Analista de Producción** "
    "(criterio técnico según el candidato: energía/PR para paneles y orientación, "
    "autonomía/DoD/vida útil para baterías — nunca decide la inversión), vive dentro de "
    "los resultados de 🧩 Comparador de Paneles, 🧭 Comparador de Orientación y "
    "🔋 Baterías y Balance.",
    icon="🧭",
)
col_link1, col_link2, col_link3 = st.columns(3)
with col_link1:
    st.page_link(
        "pages/4c_🧩_Comparador_Paneles.py",
        label="Ir al Analista de Producción (🧩 Comparador de Paneles) →",
        icon="🧩",
    )
with col_link2:
    st.page_link(
        "pages/4d_🧭_Comparador_Orientación.py",
        label="Ir al Analista de Producción (🧭 Comparador de Orientación) →",
        icon="🧭",
    )
with col_link3:
    st.page_link(
        "pages/11_🔋_Baterias_y_Balance.py",
        label="Ir al Analista de Producción (🔋 Baterías y Balance) →",
        icon="🔋",
    )

# ── Prerrequisitos: el mismo criterio que usa 🧭 Asistente para 'listo' ──────
_faltan = []
if st.session_state.get("recurso_solar_ok") is not True:
    _faltan.append("☀️ Recurso Solar")
if st.session_state.get("produccion_ok") is not True:
    _faltan.append("📊 Producción")
if st.session_state.get("financiero_ok") is not True:
    _faltan.append("💰 Financiero")

if _faltan:
    st.warning(
        "Completa primero: " + ", ".join(_faltan) + ". El Análisis IA necesita un diseño "
        "con producción y flujo financiero ya calculados para tener algo real que interpretar.",
        icon="🔒",
    )
    st.stop()

if st.session_state.get("metricas_financiero") is None:
    st.warning("No encuentro métricas financieras en la sesión. Vuelve a correr 💰 Financiero.", icon="🔒")
    st.stop()

# ── Clave de API ──────────────────────────────────────────────────────────────
if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
    st.error(
        "Falta `ANTHROPIC_API_KEY` en el entorno del servidor. El proceso corre bajo "
        "**PM2** (`streamlit-bipv`), no systemctl. En el droplet:\n\n"
        "`export ANTHROPIC_API_KEY=\"sk-ant-...\"` (tu clave real) → "
        "`pm2 restart streamlit-bipv --update-env` → `pm2 save` para que persista.",
        icon="🔑",
    )
    st.stop()


# ── Ensamblar el candidato "Actual" desde resultados YA calculados ──────────
def _candidato_actual() -> CandidatoRegistrado:
    ciudad_nombre = st.session_state.get("ciudad")
    c = CIUDADES.get(ciudad_nombre, {})
    lat = float(st.session_state.get("lat_proyecto", c.get("lat", 4.711)))
    lon = float(st.session_state.get("lon_proyecto", c.get("lon", -74.072)))
    alt_m = float(st.session_state.get("alt_proyecto", c.get("alt_m", 2600)))

    config = BIPVConfiguration(
        lat=lat, lon=lon, alt_m=alt_m,
        tilt=float(st.session_state.get("tilt_fachada", 90.0)),
        azimuth=float(st.session_state.get("azimuth_fachada", 180.0)),
        area_m2=float(st.session_state.get("area_util_m2", 0.0)),
        albedo=float(st.session_state.get("albedo_suelo", 0.20)),
        panel=st.session_state.get("panel_dict") or {},
        N_serie=int(st.session_state.get("N_serie", 1)),
        N_strings_tracker=int(st.session_state.get("N_str_tr_usado", 1)),
        eta_inversor=float(st.session_state.get("eta_inversor", 0.97)),
        k_bipv=float(st.session_state.get("motor_optico_k_bipv", 1.0)),
        inversor=st.session_state.get("inversor_dict_dim"),
        pct_mismatch_fab=float(st.session_state.get("pct_mismatch_fab", 2.0)),
        pct_soiling=float(st.session_state.get("pct_soiling", 2.0)),
        pct_cableado=float(st.session_state.get("pct_cableado", 1.5)),
    )

    metricas = st.session_state["metricas_financiero"]
    fin = FinancialResult(
        beneficios_1715=st.session_state.get("ben_1715"),
        flujos=[],   # no reconstruido: ni el registro ni los agentes leen .flujos
        metricas=metricas,
    )
    objetivos = {
        "energia_anual": st.session_state.get("E_ac_anual_kWh"),
        "pr": st.session_state.get("PR_sistema"),
        "capacidad_instalada": st.session_state.get("P_stc_kW_sistema"),
        "npv": metricas.get("vpn_usd"),
        "irr": metricas.get("tir_pct"),
        "payback_simple": metricas.get("payback_simple"),
        "lcoe": metricas.get("lcoe_usd_kWh"),
    }
    resultado = ResultadoCandidato(config=config, objetivos=objetivos)
    capex_usd = float(st.session_state.get("capex_total_usd", 0.0))
    return CandidatoRegistrado(resultado=resultado, fin=fin, capex_usd=capex_usd)


registro = {"Actual": _candidato_actual()}

# El SYSTEM_PROMPT de ambos agentes ya no asume "fachada" por defecto, pero
# además le declaramos el tipo real como dato explícito -- así el agente
# nunca tiene que adivinarlo a partir del nombre genérico "BIPV" de la
# plataforma. Encontrado en producción: un usuario corrió un ejercicio de
# Granja fotovoltaica y el Analista narró en clave de fachada de edificio.
_tipo_instalacion = st.session_state.get("tipo_instalacion", "no especificado en el proyecto")
_contexto_tipo = f"Tipo de instalación de este proyecto: {_tipo_instalacion}."

st.subheader("📋 Diseño que van a leer los agentes")
st.info(
    f"v1: un único candidato — el diseño actual del proyecto ({_tipo_instalacion}), tal "
    "como quedó en 📊 Producción y 💰 Financiero. Todavía no genera variantes ni corre un "
    "barrido de sensibilidad — ver el porqué en el docstring de este archivo.",
    icon="ℹ️",
)
st.markdown(formatear_candidatos(registro, titulo="Candidato"))

st.divider()

col_analista, col_asesor = st.columns(2, gap="large")

# ── Agente 1: Analista Técnico-Financiero ────────────────────────────────────
with col_analista:
    st.subheader("🔍 Analista Técnico-Financiero")
    st.caption("Hallazgos técnicos priorizados — para quien va a iterar el diseño.")
    if st.button("Ejecutar Analista", key="btn_analista", use_container_width=True):
        with st.spinner("Consultando a Claude (Analista Técnico-Financiero)…"):
            try:
                pregunta = (
                    f"{_contexto_tipo} Este es el ÚNICO diseño actual del proyecto — no se "
                    "corrió un barrido de sensibilidad ni se generaron variantes todavía, así "
                    "que no compares contra alternativas que no existen. Evalúa su salud "
                    "financiera y su bancabilidad contra los tres perfiles de inversionista, y "
                    "dime explícitamente qué información adicional (sensibilidad, variantes de "
                    "diseño) haría falta para un diagnóstico más completo."
                )
                mensaje = ejecutar_analisis([], registro, pregunta=pregunta)
                st.session_state["ia_analista_texto"] = _texto_analista(mensaje)
                st.session_state["ia_analista_uso"] = (
                    mensaje.usage.input_tokens, mensaje.usage.output_tokens,
                )
            except Exception as e:
                st.session_state["ia_analista_texto"] = None
                st.error(f"❌ {e}")

    if st.session_state.get("ia_analista_texto"):
        st.markdown(st.session_state["ia_analista_texto"])
        tin, tout = st.session_state.get("ia_analista_uso", (0, 0))
        st.caption(f"🔢 {tin:,} tokens de entrada · {tout:,} de salida")
        if st.button("🗑️ Limpiar", key="btn_limpiar_analista"):
            st.session_state.pop("ia_analista_texto", None)
            st.session_state.pop("ia_analista_uso", None)
            st.rerun()

# ── Agente 2: Asesor de Inversión ────────────────────────────────────────────
with col_asesor:
    st.subheader("💼 Asesor de Inversión")
    st.caption("Memo de decisión de inversión — para quien va a poner el dinero.")
    if st.button("Ejecutar Asesor", key="btn_asesor", use_container_width=True):
        with st.spinner("Consultando a Claude (Asesor de Inversión)…"):
            try:
                pregunta_asesor = (
                    f"{_contexto_tipo} Evalúa estos candidatos contra los tres perfiles de "
                    "inversionista y dame tu recomendación de inversión."
                )
                mensaje = ejecutar_asesoria(registro, pregunta=pregunta_asesor)
                st.session_state["ia_asesor_texto"] = _texto_asesor(mensaje)
                st.session_state["ia_asesor_uso"] = (
                    mensaje.usage.input_tokens, mensaje.usage.output_tokens,
                )
            except Exception as e:
                st.session_state["ia_asesor_texto"] = None
                st.error(f"❌ {e}")

    if st.session_state.get("ia_asesor_texto"):
        st.markdown(st.session_state["ia_asesor_texto"])
        tin, tout = st.session_state.get("ia_asesor_uso", (0, 0))
        st.caption(f"🔢 {tin:,} tokens de entrada · {tout:,} de salida")
        if st.button("🗑️ Limpiar", key="btn_limpiar_asesor"):
            st.session_state.pop("ia_asesor_texto", None)
            st.session_state.pop("ia_asesor_uso", None)
            st.rerun()
