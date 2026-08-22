# -*- coding: utf-8 -*-
"""Resiliencia del chat del 🧭 Asistente frente a 429/timeout de Gemini (2026-08-21).

Hallazgo del usuario: el chat mostraba un error rojo con frecuencia. Se
encontró que un timeout (o cualquier excepción de red) en el PRIMER modelo de
la lista de fallback abortaba toda la respuesta sin intentar los otros 4
modelos -- el fallback solo cubría HTTP 404/429, no excepciones de red. Estos
tests verifican que ahora los 5 modelos se intentan ante timeout/errores de
conexión, no solo ante 404/429, y que los proveedores sin fallback (OpenAI,
Anthropic) conservan su comportamiento anterior sin cambios.
"""
import os

import pytest
import requests

from calculos.asistente import responder


class _FakeResp:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


_PAYLOAD_OK = {"candidates": [{"content": {"parts": [{"text": "Respuesta de prueba"}]}}]}


@pytest.fixture(autouse=True)
def _solo_gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def test_timeout_en_el_primer_modelo_no_aborta_prueba_los_demas(monkeypatch):
    llamadas = []

    def fake_post(url, headers=None, json=None, timeout=None):
        llamadas.append(url)
        if len(llamadas) == 1:
            raise requests.exceptions.Timeout("simulado")
        return _FakeResp(200, _PAYLOAD_OK)

    monkeypatch.setattr(requests, "post", fake_post)
    out = responder("¿hay alarma en Motor IV?", {})
    assert out["respuesta"] == "Respuesta de prueba"
    assert len(llamadas) == 2  # el primero falló, el segundo sí se intentó


def test_todos_los_modelos_con_timeout_da_error_claro(monkeypatch):
    llamadas = []

    def fake_post(url, headers=None, json=None, timeout=None):
        llamadas.append(url)
        raise requests.exceptions.Timeout("simulado")

    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(RuntimeError, match="no respondió a tiempo"):
        responder("¿hay alarma en Motor IV?", {})
    assert len(llamadas) == 5  # probó los 5 modelos de fallback antes de rendirse


def test_todos_los_modelos_con_429_da_error_de_limite_de_uso(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        return _FakeResp(429)

    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(RuntimeError, match="límite de uso"):
        responder("¿hay alarma en Motor IV?", {})


def test_404_en_el_primero_pasa_al_segundo_modelo(monkeypatch):
    llamadas = []

    def fake_post(url, headers=None, json=None, timeout=None):
        llamadas.append(url)
        if len(llamadas) == 1:
            return _FakeResp(404)
        return _FakeResp(200, _PAYLOAD_OK)

    monkeypatch.setattr(requests, "post", fake_post)
    out = responder("¿hay alarma en Motor IV?", {})
    assert out["respuesta"] == "Respuesta de prueba"
    assert len(llamadas) == 2


def test_error_de_conexion_en_todos_los_modelos(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        raise requests.exceptions.ConnectionError("simulado")

    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(RuntimeError, match="No se pudo conectar"):
        responder("¿hay alarma en Motor IV?", {})


def test_openai_sin_clave_gemini_sigue_sin_fallback_entre_modelos(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "clave-de-prueba")
    llamadas = []

    def fake_post(url, headers=None, json=None, timeout=None):
        llamadas.append(url)
        raise requests.exceptions.Timeout("simulado")

    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(RuntimeError, match="OpenAI no respondió a tiempo"):
        responder("¿hay alarma en Motor IV?", {})
    assert len(llamadas) == 1  # sin fallback -- un solo modelo, como antes
