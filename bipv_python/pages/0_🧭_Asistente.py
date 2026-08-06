# -*- coding: utf-8 -*-
"""🧭 Asistente — guía paso a paso + chat con el Manual de Usuario."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from calculos.auth import requerir_login
requerir_login()

from calculos.asistente import (
    BaseConocimiento,
    RUTA_BASE_CONOCIMIENTO,
    avisos_coherencia,
    evaluar_flujo,
    responder,
    siguiente_paso,
)

st.set_page_config(page_title="Asistente", page_icon="🧭", layout="wide")
st.title("🧭 Asistente de la Calculadora")
st.caption(
    "El asistente **orienta, no modifica**: la guía lee el estado real de tu sesión y "
    "el chat responde únicamente con base en el Manual de Usuario."
)

col_guia, col_chat = st.columns([1, 1.4], gap="large")

# ═════════════════ NIVEL 1: GUÍA PASO A PASO (determinista) ══════════════════
with col_guia:
    st.subheader("📋 Tu avance en el flujo de trabajo")
    checklist = evaluar_flujo(st.session_state)
    sig = siguiente_paso(checklist)

    for it in checklist:
        icono = {"listo": "✅", "pendiente": "⬜", "bloqueado": "🔒"}[it["estado"]]
        opc = " *(opcional)*" if it["opcional"] else ""
        es_sig = sig is not None and it["orden"] == sig["orden"]
        marca = " 👈 **SIGUIENTE**" if es_sig else ""
        st.markdown(f"{icono} **{it['orden']}. {it['pagina']}**{opc} — {it['descripcion']}{marca}")
        if es_sig and it["consejo"]:
            st.info(it["consejo"], icon="💡")
        if it["estado"] == "bloqueado" and not it["opcional"]:
            st.caption(f"   🔒 Requiere antes: {', '.join(it['faltan_previas'])}")

    if sig is None:
        st.success("🎉 ¡Flujo completo! Puedes generar el 📄 Reporte PDF para el cliente.")

    avisos = avisos_coherencia(st.session_state)
    if avisos:
        st.subheader("⚠️ Avisos de coherencia")
        for a in avisos:
            st.warning(a, icon="⚠️")

# ═════════════════ NIVEL 2: CHAT CON EL MANUAL (RAG) ═════════════════════════
with col_chat:
    st.subheader("💬 Pregúntale al Manual")

    if not os.path.exists(RUTA_BASE_CONOCIMIENTO):
        st.error(
            "Falta la base de conocimiento (datos/base_conocimiento_asistente.md). "
            "Genérala con: `python scripts/generar_base_conocimiento.py`"
        )
        st.stop()

    hay_clave = any(os.environ.get(k, "").strip()
                    for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"))
    if not hay_clave:
        st.warning(
            "El chat necesita una clave de API de IA en el servidor. Recomendado "
            "**Gemini** (nivel gratuito): crea la clave en aistudio.google.com → "
            "en el servidor agrega `GEMINI_API_KEY` al entorno de PM2 y reinicia. "
            "También sirven `OPENAI_API_KEY` o `ANTHROPIC_API_KEY`.",
            icon="🔑",
        )

    @st.cache_resource
    def _cargar_base():
        return BaseConocimiento.cargar()

    base = _cargar_base()
    st.caption(f"📖 Base de conocimiento cargada: {len(base.secciones)} secciones del manual.")

    if "asistente_chat" not in st.session_state:
        st.session_state["asistente_chat"] = []

    for msg in st.session_state["asistente_chat"]:
        with st.chat_message("user" if msg["rol"] == "usuario" else "assistant"):
            st.markdown(msg["texto"])
            if msg.get("fuentes"):
                st.caption("📖 Secciones consultadas: " + " · ".join(msg["fuentes"]))

    pregunta = st.chat_input(
        "Ej: ¿por qué mi TIR sale negativa? · ¿cómo uso Sombras SketchUp?",
        disabled=not hay_clave,
    )
    if pregunta:
        st.session_state["asistente_chat"].append({"rol": "usuario", "texto": pregunta})
        with st.chat_message("user"):
            st.markdown(pregunta)
        with st.chat_message("assistant"):
            with st.spinner("Consultando el manual…"):
                try:
                    out = responder(
                        pregunta, st.session_state, base=base,
                        historial=st.session_state["asistente_chat"][:-1],
                    )
                    st.markdown(out["respuesta"])
                    if out["fuentes"]:
                        st.caption("📖 Secciones consultadas: " + " · ".join(out["fuentes"]))
                    st.session_state["asistente_chat"].append(
                        {"rol": "asistente", "texto": out["respuesta"],
                         "fuentes": out["fuentes"]})
                except Exception as e:
                    st.error(f"❌ {e}")

    if st.session_state["asistente_chat"]:
        if st.button("🗑️ Limpiar conversación"):
            st.session_state["asistente_chat"] = []
            st.rerun()
