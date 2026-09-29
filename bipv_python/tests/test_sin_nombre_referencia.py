# -*- coding: utf-8 -*-
"""Spec ``08-interfaz/sin-nombre-referencia`` (29-sep-2026).

Regla del usuario («por cuestiones legales», 30-ago-2026; reafirmada el
29-sep-2026): la app, el manual del 🧭 Asistente, sus respuestas y los textos
de los catálogos que se muestran no nombran el software de simulación de
referencia; dicen «la referencia estándar internacional».
"""
import ast
import os
import re

import pytest

from calculos.texto_referencia import anonimizar_referencia, menciona_referencia

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_NOMBRE = re.compile(r"(?i)pvsyst(?!em)")
_SOLO_IDENTIFICADOR = re.compile(r"[a-z0-9_]+")


@pytest.mark.parametrize("entrada, salida", [
    ("Para comparar con un informe de PVsyst 8 usa 5.3",
     "Para comparar con un informe de la referencia estándar internacional usa 5.3"),
    ("PVsyst reporta 339,033 kWh", "La referencia estándar internacional reporta 339,033 kWh"),
    ("balance IEC 61724 (estilo PVsyst)", "balance IEC 61724 (estilo de la referencia estándar internacional)"),
    ("verificada desde base PVsyst V8.1.5 (Datasheets 2020)",
     "verificada desde base de datos de la referencia estándar internacional (Datasheets 2020)"),
    ("ver DIAGNOSTICO_MOTOR_PVSYST.md", "ver un documento interno de diagnóstico"),
    ("pvlib.pvsystem es la librería", "pvlib.pvsystem es la librería"),
    ("sin nada que cambiar", "sin nada que cambiar"),
])
def test_anonimizar(entrada, salida):
    assert anonimizar_referencia(entrada) == salida


def test_no_texto_queda_igual():
    assert anonimizar_referencia(None) is None and anonimizar_referencia(3) == 3
    assert menciona_referencia("PVsyst") and not menciona_referencia("pvlib.pvsystem")


def test_manual_del_asistente_no_lo_nombra():
    with open(os.path.join(_ROOT, "datos", "base_conocimiento_asistente.md"), encoding="utf-8") as f:
        texto = f.read()
    assert not _NOMBRE.search(texto), _NOMBRE.findall(texto)[:5]


def _docstrings(arbol):
    ids = set()
    for n in ast.walk(arbol):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body:
            f = n.body[0]
            if isinstance(f, ast.Expr) and isinstance(f.value, ast.Constant) and isinstance(f.value.value, str):
                ids.add(id(f.value))
    return ids


def test_textos_de_la_app_no_lo_nombran():
    """Todo texto entre comillas de páginas, cálculos y utilidades (los
    comentarios, docstrings y nombres internos como «sdm_pvsyst» no se ven)."""
    hallazgos = []
    for base in ("pages", "calculos", "utils"):
        for raiz, _, archivos in os.walk(os.path.join(_ROOT, base)):
            for nombre in archivos:
                if not nombre.endswith(".py") or nombre == "texto_referencia.py":
                    continue
                ruta = os.path.join(raiz, nombre)
                with open(ruta, encoding="utf-8") as f:
                    arbol = ast.parse(f.read())
                docs = _docstrings(arbol)
                for n in ast.walk(arbol):
                    if (isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs
                            and not _SOLO_IDENTIFICADOR.fullmatch(n.value)
                            and anonimizar_referencia(n.value, identificadores=False) != n.value):
                        hallazgos.append(f"{os.path.relpath(ruta, _ROOT)}:{n.lineno}")
    assert not hallazgos, hallazgos


def test_catalogos_se_muestran_sin_el_nombre():
    from datos.catalogo_inversores_excel import _cargar_catalogo_inversores_cached
    from datos.catalogo_paneles_excel import cargar_catalogo_paneles
    campos = ("notas", "confianza", "fuente_NsA", "sdm_fuente", "sdm_advertencia")
    paneles = cargar_catalogo_paneles()
    assert paneles
    malos = [n for n, p in paneles.items() for c in campos if menciona_referencia(p.get(c))]
    assert not malos, malos[:5]
    invs = _cargar_catalogo_inversores_cached(0.0)
    assert not [n for n, i in invs.items() for c in ("notas", "confianza") if menciona_referencia(i.get(c))]


def test_respuestas_del_asistente_no_lo_nombran(monkeypatch):
    import calculos.ia_proveedor as ia
    from calculos.asistente import PROMPT_SISTEMA, responder
    monkeypatch.setattr(ia, "llamar_ia", lambda *a, **k: {
        "texto": "En PVsyst el Uc = 20 equivale a k ≈ 1,1.", "proveedor": "prueba"})
    r = responder("¿Uc de PVsyst?", {})
    assert not menciona_referencia(r["respuesta"])
    assert "la referencia estándar internacional" in r["respuesta"]
    assert "Nunca nombres el software de simulación de referencia" in PROMPT_SISTEMA
    assert "SÍ puedes explicar paso a paso los ejemplos con números del manual" in PROMPT_SISTEMA
