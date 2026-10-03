# -*- coding: utf-8 -*-
"""Spec 08-interfaz/guia-vista-3d (3-oct-2026).

Guía paso a paso al entrar a 🗺️ Vista 3D: sombra por string (#115) y difusa
en la sombra (#116), con los errores frecuentes, para que el usuario corra un
proyecto sin equivocarse. La misma guía queda en el manual del Asistente.
"""
from pathlib import Path

from calculos.guia_vista_3d import ERRORES_FRECUENTES, GUIA_TITULO, PASOS, RESUMEN, guia_markdown

_RAIZ = Path(__file__).resolve().parents[1]
_PAGINA = _RAIZ / "pages" / "9_🗺️_Vista_3D.py"
_PROHIBIDOS = ("PV" + "syst", "PV" + "·SOL", "PV" + " SOL", "PV" + "SOL", "pendi" + "ente")


def test_la_guia_cubre_el_flujo_en_orden():
    texto = guia_markdown()
    claves = ["Recurso Solar", "Superficies BIPV", "Site Designer", "un punto por módulo",
              "Calcular sombra", "estado", "Inversores", "comparación física", "Adoptar"]
    posiciones = [texto.index(c) for c in claves]
    assert posiciones == sorted(posiciones), "los pasos deben ir en el orden del flujo"
    assert len(PASOS) >= 7


def test_explica_los_dos_cambios_y_los_errores_frecuentes():
    texto = guia_markdown()
    for t in ("string", "bypass", "difusa", "cielo", "metros", "milímetros", "0,3 m", "northOffset"):
        assert t in texto, t
    assert len(ERRORES_FRECUENTES) >= 6
    for t in ("dentro", "otra ubicación", "un solo punto", "recalcul"):
        assert any(t in e for e in ERRORES_FRECUENTES), t
    for p in _PROHIBIDOS:
        assert p not in texto, p


def test_la_pagina_muestra_la_guia_al_entrar():
    src = _PAGINA.read_text(encoding="utf-8")
    i_titulo = src.index('st.title("🗺️ Vista 3D del Sitio")')
    i_guia = src.index("st.expander(GUIA_TITULO")
    assert i_titulo < i_guia < src.index("tab_mapa, tab_modelo, tab_solar = st.tabs(")
    assert "st.info(RESUMEN)" in src
    assert "st.markdown(guia_markdown())" in src
    # Recordatorio junto a los puntos 3D
    i_puntos = src.index('f"Puntos 3D — {_nombre_sombra}')
    assert "AYUDA_PUNTOS" in src[i_puntos - 1500:i_puntos + 600]


def test_manual_del_asistente_seccion_125():
    kb = (_RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    i = kb.index("## 125.")
    s = kb[i:kb.find("\n## ", i + 5) if kb.find("\n## ", i + 5) > 0 else None]
    for t in ("Vista 3D", "paso a paso", "un punto por módulo", "Calcular sombra", "difusa",
              "string", "errores frecuentes", "0,3 m", "milímetros"):
        assert t in s, t
    assert i < kb.rindex("Calculadora BIPV — Innovación Química")
    for p in _PROHIBIDOS:
        assert p not in s, p
    assert RESUMEN and GUIA_TITULO
