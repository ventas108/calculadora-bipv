# -*- coding: utf-8 -*-
"""Cliente compartido para los 3 proveedores de IA que la app puede usar
(Gemini, OpenAI, Anthropic) -- el primero con clave de API configurada en el
servidor gana. Centraliza la resiliencia ante 429/timeout de Gemini (varios
modelos de fallback, ver PR #30) para que cualquier función de la app que
necesite una llamada de IA -- el chat del 🧭 Asistente, el extractor de
cotizaciones -- la reutilice sin duplicar la lógica de red.
"""
from __future__ import annotations

import os


def proveedor_disponible() -> str | None:
    """Nombre del proveedor configurado ('Gemini'/'OpenAI'/'Anthropic'), o None
    si el servidor no tiene ninguna clave de API de IA en el entorno."""
    if os.environ.get("GEMINI_API_KEY", "").strip():
        return "Gemini"
    if os.environ.get("OPENAI_API_KEY", "").strip():
        return "OpenAI"
    if os.environ.get("ANTHROPIC_API_KEY", "").strip():
        return "Anthropic"
    return None


def llamar_ia(prompt_sistema: str, contenido_usuario: str,
              historial: list[dict] | None = None,
              temperature: float = 0.2, max_tokens: int = 1024,
              timeout: int = 60) -> dict:
    """Llama al proveedor de IA configurado en el servidor.

    `historial` es una lista de {"rol": "usuario"|"asistente", "texto": str}.
    Devuelve {"texto": str, "proveedor": str}. Lanza RuntimeError con un
    mensaje claro (sin URLs ni datos sensibles) si no hay clave configurada o
    si la llamada falla.
    """
    import requests  # ya está en requirements

    gem = os.environ.get("GEMINI_API_KEY", "").strip()
    oai = os.environ.get("OPENAI_API_KEY", "").strip()
    ant = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    hist = historial or []

    if not (gem or oai or ant):
        raise RuntimeError(
            "No hay clave de API configurada. Define GEMINI_API_KEY (recomendado, "
            "tiene nivel gratuito), OPENAI_API_KEY o ANTHROPIC_API_KEY como variable "
            "de entorno en el servidor y reinicia la app."
        )

    # Errores de red/HTTP se traducen a mensajes SIN URL ni encabezados: la URL de
    # una excepción de requests podría contener información sensible.
    if gem:
        prov = "Gemini"
        contents = []
        for h in hist[-6:]:
            contents.append({"role": "user" if h["rol"] == "usuario" else "model",
                             "parts": [{"text": h["texto"]}]})
        contents.append({"role": "user", "parts": [{"text": contenido_usuario}]})
        # Modelos en orden de preferencia: las variantes "lite" primero -- en el
        # nivel gratuito tienen cupo por minuto más alto que las variantes "flash"
        # completas, así que fallan menos seguido con HTTP 429. Si uno no existe
        # (404), su cuota está agotada (429), o no responde a tiempo, se intenta el
        # siguiente en vez de abortar toda la llamada.
        modelos = ("gemini-flash-lite-latest", "gemini-2.5-flash-lite",
                   "gemini-2.0-flash", "gemini-flash-latest", "gemini-2.5-flash")
        timeout_modelo = max(15, timeout // len(modelos))
        r = None
        hubo_timeout = False
        for modelo in modelos:
            try:
                r = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{modelo}:generateContent",
                    headers={"x-goog-api-key": gem},  # header, nunca en la URL
                    json={"systemInstruction": {"parts": [{"text": prompt_sistema}]},
                          "contents": contents,
                          "generationConfig": {"temperature": temperature,
                                               "maxOutputTokens": max_tokens}},
                    timeout=timeout_modelo,
                )
            except requests.exceptions.Timeout:
                hubo_timeout, r = True, None
                continue
            except requests.exceptions.RequestException:
                r = None
                continue
            if r.status_code not in (404, 429):
                break
        if r is None:
            if hubo_timeout:
                raise RuntimeError(f"{prov} no respondió a tiempo en ninguno de sus "
                                   "modelos disponibles. Intenta de nuevo en un momento.")
            raise RuntimeError(f"No se pudo conectar con {prov}. Revisa la conexión a "
                               "internet del servidor e intenta de nuevo.")
    else:
        try:
            if oai:
                prov = "OpenAI"
                msgs = [{"role": "system", "content": prompt_sistema}]
                for h in hist[-6:]:
                    msgs.append({"role": "user" if h["rol"] == "usuario" else "assistant",
                                 "content": h["texto"]})
                msgs.append({"role": "user", "content": contenido_usuario})
                r = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {oai}"},
                    json={"model": "gpt-4o-mini", "messages": msgs, "temperature": temperature,
                          "max_tokens": max_tokens},
                    timeout=timeout,
                )
            else:
                prov = "Anthropic"
                msgs = []
                for h in hist[-6:]:
                    msgs.append({"role": "user" if h["rol"] == "usuario" else "assistant",
                                 "content": h["texto"]})
                msgs.append({"role": "user", "content": contenido_usuario})
                r = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": ant, "anthropic-version": "2023-06-01"},
                    json={"model": "claude-3-5-haiku-latest", "system": prompt_sistema,
                          "messages": msgs, "max_tokens": max_tokens},
                    timeout=timeout,
                )
        except requests.exceptions.Timeout:
            raise RuntimeError(f"{prov} no respondió a tiempo. Intenta de nuevo en un momento.")
        except requests.exceptions.RequestException:
            raise RuntimeError(f"No se pudo conectar con {prov}. Revisa la conexión a "
                               "internet del servidor e intenta de nuevo.")

    if r.status_code == 429:
        raise RuntimeError(f"{prov} alcanzó el límite de uso (HTTP 429). Espera un "
                           "minuto e intenta de nuevo.")
    if r.status_code in (401, 403):
        raise RuntimeError(f"La clave de API de {prov} fue rechazada (HTTP "
                           f"{r.status_code}). Verifica la variable de entorno.")
    if r.status_code >= 400:
        raise RuntimeError(f"{prov} respondió con error HTTP {r.status_code}. "
                           "Intenta de nuevo más tarde.")

    try:
        data = r.json()
        if prov == "Gemini":
            texto = data["candidates"][0]["content"]["parts"][0]["text"]
        elif prov == "OpenAI":
            texto = data["choices"][0]["message"]["content"]
        else:
            texto = data["content"][0]["text"]
    except (ValueError, KeyError, IndexError, TypeError):
        raise RuntimeError(f"{prov} devolvió una respuesta inesperada. Intenta de nuevo.")

    return {"texto": texto.strip(), "proveedor": prov}
