# -*- coding: utf-8 -*-
"""Asistente de la Calculadora BIPV.

Nivel 1 — Guía determinista: evalúa st.session_state contra el flujo de trabajo
recomendado y devuelve el estado de cada paso (✅/⚠️/⬜) y el siguiente paso.
No usa IA: cero posibilidad de error.

Nivel 2 — Chat con el Manual (RAG): busca las secciones relevantes de la base de
conocimiento (extraída del Manual de Usuario) y se las entrega a un modelo de IA
junto con el estado real de la sesión. El modelo tiene prohibido inventar: si la
respuesta no está en el manual, debe decirlo.

El asistente NUNCA modifica valores ni ejecuta cálculos.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Mapping

# ═════════════════════════════ NIVEL 1: GUÍA ════════════════════════════════

@dataclass
class Paso:
    orden: int
    pagina: str          # nombre visible de la página
    descripcion: str
    claves_resultado: tuple[str, ...]   # basta UNA presente y no-None → listo
    claves_previas: tuple[str, ...] = ()  # pasos que deben estar listos antes
    opcional: bool = False
    consejo: str = ""    # qué hacer / por qué importa


FLUJO: list[Paso] = [
    Paso(1, "🏠 Proyecto", "Definir el proyecto (ciudad, tipo, áreas)",
         ("nombre_proyecto", "ciudad"),
         consejo="Todo parte de aquí: la ciudad define el recurso solar y la zona geográfica."),
    Paso(2, "☀️ Recurso Solar", "Descargar el TMY y calcular la irradiancia POA",
         ("tmy_df",),
         claves_previas=("ciudad",),
         consejo="Obligatorio antes de Producción, Sombras SketchUp y Dimensionamiento."),
    Paso(3, "🔬 Motor IV", "Simular la curva IV del panel elegido",
         ("panel_dict",),
         consejo="Elige el panel del catálogo y verifica que la ficha esté completa."),
    Paso(4, "📐 Dimensionamiento", "Definir strings, inversor y potencia DC",
         ("inversor_dict_dim", "N_serie"),
         claves_previas=("tmy_df", "panel_dict"),
         consejo="Usa el ⚖️ Comparador de Inversores para elegir con LCOE y clipping a la vista."),
    Paso(5, "🔆 Motor Óptico", "Corregir la POA por reflexión/suciedad (opcional)",
         ("poa_efectiva_df",),
         claves_previas=("tmy_df",), opcional=True,
         consejo="Si lo corres, Producción usará la POA efectiva automáticamente."),
    Paso(6, "🌳 Sombras / 🔀 Mismatch", "Sombras (web o SketchUp) y bypass diodes (opcional)",
         ("bypass_result", "bypass_ok"),
         claves_previas=("panel_dict",), opcional=True,
         consejo="Con sombras cercanas reales, este paso corrige la energía anual (E_ac bypass)."),
    Paso(7, "📊 Producción", "Calcular la energía anual E_ac hora a hora",
         ("res_produccion",),
         claves_previas=("tmy_df", "inversor_dict_dim"),
         consejo="Recórrelo de nuevo SIEMPRE que cambies panel, inversor o sombras."),
    Paso(8, "💼 Presupuesto", "CAPEX, costos blandos y OPEX",
         ("presupuesto_capex_usd",),
         consejo="Completa los Costos Blandos antes de pasar a Financiero: sin ellos la TIR sale optimista."),
    Paso(9, "💰 Financiero", "Flujo de caja, TIR, LCOE y Ley 1715",
         ("metricas_financiero",),
         claves_previas=("res_produccion", "presupuesto_capex_usd"),
         consejo="Verifica TRM y tarifa eléctrica vigentes antes de presentar."),
    Paso(10, "🔋 Baterías y Balance", "Almacenamiento y balance energético (opcional)",
         ("balance_metricas", "bateria_dim"),
         claves_previas=("res_produccion",), opcional=True,
         consejo="Solo si el proyecto lleva baterías o quieres la fracción solar."),
    Paso(11, "📄 Reporte PDF", "Generar el reporte para el cliente",
         ("reporte_generado",),
         claves_previas=("metricas_financiero",), opcional=True,
         consejo="Genera el reporte al final, cuando toda la cadena esté verde."),
]


def _listo(estado: Mapping[str, Any], claves: tuple[str, ...]) -> bool:
    return any(estado.get(k) is not None for k in claves)


def evaluar_flujo(estado: Mapping[str, Any]) -> list[dict]:
    """Devuelve el checklist: [{paso, pagina, estado: listo|pendiente|bloqueado,
    opcional, consejo, faltan_previas:[...]}]."""
    resultado = []
    for p in FLUJO:
        listo = _listo(estado, p.claves_resultado)
        faltan = [k for k in p.claves_previas if estado.get(k) is None]
        if listo:
            st_paso = "listo"
        elif faltan:
            st_paso = "bloqueado"
        else:
            st_paso = "pendiente"
        resultado.append({
            "orden": p.orden, "pagina": p.pagina, "descripcion": p.descripcion,
            "estado": st_paso, "opcional": p.opcional, "consejo": p.consejo,
            "faltan_previas": faltan,
        })
    return resultado


def siguiente_paso(checklist: list[dict]) -> dict | None:
    """Primer paso obligatorio no listo y no bloqueado; si todos los obligatorios
    están listos, primer opcional pendiente; si todo listo, None."""
    for it in checklist:
        if not it["opcional"] and it["estado"] == "pendiente":
            return it
    for it in checklist:
        if not it["opcional"] and it["estado"] == "bloqueado":
            return it
    for it in checklist:
        if it["opcional"] and it["estado"] == "pendiente":
            return it
    return None


def avisos_coherencia(estado: Mapping[str, Any]) -> list[str]:
    """Avisos deterministas de coherencia entre páginas (Nivel 1 'proactivo')."""
    avisos: list[str] = []
    if estado.get("res_produccion") is not None:
        if estado.get("poa_efectiva_df") is not None and not estado.get("produccion_ok"):
            avisos.append("Corriste el Motor Óptico: verifica que 📊 Producción se haya "
                          "recalculado con la POA efectiva.")
    if estado.get("metricas_financiero") is not None and estado.get("presupuesto_capex_blando") is None:
        avisos.append("Financiero está corrido pero no veo Costos Blandos en el Presupuesto: "
                      "la TIR puede estar optimista.")
    if estado.get("bypass_result") is not None and estado.get("E_ac_anual_kWh_bypass") is None:
        avisos.append("Calculaste el bypass en la Página 5 pero Producción aún no aplica esa "
                      "corrección: vuelve a 📊 Producción.")
    if estado.get("csv_fs_sketchup_bytes") is not None and estado.get("bypass_result") is None:
        avisos.append("Tienes un CSV de Sombras SketchUp listo para usar: ábrelo en 🔀 Mismatch "
                      "con el botón «🌳 Usar el CSV generado en Sombras SketchUp».")
    return avisos


# ═════════════════════════ NIVEL 2: CHAT CON EL MANUAL ══════════════════════

RUTA_BASE_CONOCIMIENTO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "datos", "base_conocimiento_asistente.md",
)

_STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "de", "del", "en", "y", "o", "que",
    "como", "por", "para", "con", "sin", "es", "se", "mi", "tu", "al", "a",
    "me", "te", "le", "lo", "su", "si", "no", "ya", "hay", "muy", "mas",
}


def _normalizar(texto: str) -> list[str]:
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    palabras = re.findall(r"[a-z0-9_]+", t)
    return [p for p in palabras if p not in _STOPWORDS and len(p) > 1]


@dataclass
class BaseConocimiento:
    secciones: list[dict] = field(default_factory=list)  # {titulo, texto, tokens}

    @classmethod
    def cargar(cls, ruta: str = RUTA_BASE_CONOCIMIENTO) -> "BaseConocimiento":
        with open(ruta, encoding="utf-8") as f:
            crudo = f.read()
        secciones = []
        # Secciones separadas por encabezados markdown ## / ###
        bloques = re.split(r"\n(?=#{2,3} )", crudo)
        for b in bloques:
            b = b.strip()
            if not b:
                continue
            lineas = b.split("\n", 1)
            titulo = lineas[0].lstrip("# ").strip()
            texto = b
            secciones.append({
                "titulo": titulo, "texto": texto,
                "tokens": set(_normalizar(texto)),
            })
        return cls(secciones)

    def buscar(self, pregunta: str, k: int = 4) -> list[dict]:
        q = set(_normalizar(pregunta))
        if not q:
            return []
        puntuadas = []
        for s in self.secciones:
            inter = q & s["tokens"]
            if not inter:
                continue
            # peso extra si la palabra aparece en el título
            t_toks = set(_normalizar(s["titulo"]))
            score = len(inter) + 2 * len(q & t_toks)
            puntuadas.append((score, s))
        puntuadas.sort(key=lambda x: -x[0])
        return [s for _, s in puntuadas[:k]]


def contexto_sesion(estado: Mapping[str, Any]) -> str:
    """Resumen textual del estado de la sesión para el modelo (sin datos sensibles)."""
    chk = evaluar_flujo(estado)
    lineas = []
    for it in chk:
        icono = {"listo": "✅", "pendiente": "⬜", "bloqueado": "🔒"}[it["estado"]]
        opc = " (opcional)" if it["opcional"] else ""
        lineas.append(f"{icono} {it['pagina']}{opc}: {it['estado']}")
    sig = siguiente_paso(chk)
    if sig:
        lineas.append(f"👉 Siguiente paso sugerido: {sig['pagina']}")
    for a in avisos_coherencia(estado):
        lineas.append(f"⚠️ {a}")
    return "\n".join(lineas)


PROMPT_SISTEMA = """Eres el Asistente de la Calculadora BIPV (fotovoltaica integrada en \
edificios, mercado colombiano). Tu ÚNICA fuente de verdad es el MANUAL adjunto y el \
ESTADO DE LA SESIÓN del usuario. Reglas estrictas:
1. Responde SOLO con información del manual o del estado de la sesión. Si la respuesta \
no está ahí, di claramente: «Eso no está cubierto en el manual» y sugiere a qué página \
de la calculadora acudir.
2. NUNCA inventes números, fórmulas, precios ni normativa. NUNCA hagas cálculos que la \
calculadora hace (producción, TIR, strings): en su lugar indica qué página los hace.
3. Guía paso a paso: si el usuario está bloqueado, mira el estado de la sesión y dile \
exactamente qué página correr y en qué orden.
4. Responde en español, breve y concreto, con los nombres de las páginas tal como \
aparecen (ej. «☀️ Recurso Solar»). Cita la sección del manual cuando aplique.
5. No modificas nada en la aplicación: solo orientas."""


def _extraer_texto_gemini(data: dict) -> str:
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Respuesta inesperada del proveedor: {json.dumps(data)[:300]}")


def responder(pregunta: str, estado: Mapping[str, Any],
              base: BaseConocimiento | None = None,
              historial: list[dict] | None = None,
              timeout: int = 60) -> dict:
    """Responde una pregunta usando RAG sobre el manual + estado de sesión.

    Devuelve {"respuesta": str, "fuentes": [títulos], "proveedor": str}.
    Lanza RuntimeError con mensaje claro si no hay clave de API configurada.
    """
    import requests  # ya está en requirements

    if base is None:
        base = BaseConocimiento.cargar()
    secciones = base.buscar(pregunta, k=4)
    manual_ctx = "\n\n---\n\n".join(s["texto"][:4000] for s in secciones) or \
        "(No se encontraron secciones relevantes del manual para esta pregunta.)"

    contenido_usuario = (
        f"ESTADO DE LA SESIÓN DEL USUARIO:\n{contexto_sesion(estado)}\n\n"
        f"SECCIONES RELEVANTES DEL MANUAL:\n{manual_ctx}\n\n"
        f"PREGUNTA DEL USUARIO:\n{pregunta}"
    )

    gem = os.environ.get("GEMINI_API_KEY", "").strip()
    oai = os.environ.get("OPENAI_API_KEY", "").strip()
    ant = os.environ.get("ANTHROPIC_API_KEY", "").strip()

    hist = historial or []

    if gem:
        contents = []
        for h in hist[-6:]:
            contents.append({"role": "user" if h["rol"] == "usuario" else "model",
                             "parts": [{"text": h["texto"]}]})
        contents.append({"role": "user", "parts": [{"text": contenido_usuario}]})
        r = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-2.0-flash:generateContent",
            params={"key": gem},
            json={"systemInstruction": {"parts": [{"text": PROMPT_SISTEMA}]},
                  "contents": contents,
                  "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024}},
            timeout=timeout,
        )
        r.raise_for_status()
        texto = _extraer_texto_gemini(r.json())
        prov = "Gemini"
    elif oai:
        msgs = [{"role": "system", "content": PROMPT_SISTEMA}]
        for h in hist[-6:]:
            msgs.append({"role": "user" if h["rol"] == "usuario" else "assistant",
                         "content": h["texto"]})
        msgs.append({"role": "user", "content": contenido_usuario})
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {oai}"},
            json={"model": "gpt-4o-mini", "messages": msgs, "temperature": 0.2,
                  "max_tokens": 1024},
            timeout=timeout,
        )
        r.raise_for_status()
        texto = r.json()["choices"][0]["message"]["content"]
        prov = "OpenAI"
    elif ant:
        msgs = []
        for h in hist[-6:]:
            msgs.append({"role": "user" if h["rol"] == "usuario" else "assistant",
                         "content": h["texto"]})
        msgs.append({"role": "user", "content": contenido_usuario})
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ant, "anthropic-version": "2023-06-01"},
            json={"model": "claude-3-5-haiku-latest", "system": PROMPT_SISTEMA,
                  "messages": msgs, "max_tokens": 1024},
            timeout=timeout,
        )
        r.raise_for_status()
        texto = r.json()["content"][0]["text"]
        prov = "Anthropic"
    else:
        raise RuntimeError(
            "No hay clave de API configurada. Define GEMINI_API_KEY (recomendado, "
            "tiene nivel gratuito), OPENAI_API_KEY o ANTHROPIC_API_KEY como variable "
            "de entorno en el servidor y reinicia la app."
        )

    return {"respuesta": texto.strip(),
            "fuentes": [s["titulo"] for s in secciones],
            "proveedor": prov}
