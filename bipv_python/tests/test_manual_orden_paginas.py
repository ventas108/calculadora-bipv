# -*- coding: utf-8 -*-
"""Spec 07-informes/manual-orden-paginas (2-oct-2026).

El usuario preguntó «cuál es el orden ideal tanto para un sistema BIPV y un
agrivoltaico como el de Urabá». El orden estaba repartido entre las secciones
2, 107 y 108, y la sección 2 todavía ponía Producción antes de Vista 3D y
Financiero antes de Presupuesto. La sección 119 lo resume por tipo de
instalación y dice qué volver a ejecutar cuando se cambia algo.
"""
from pathlib import Path

from calculos.asistente import BaseConocimiento

_RAIZ = Path(__file__).resolve().parents[1]
_KB = _RAIZ / "datos" / "base_conocimiento_asistente.md"


def _seccion(n: int) -> str:
    kb = _KB.read_text(encoding="utf-8")
    i = kb.index(f"## {n}.")
    j = kb.find("\n## ", i + 5)
    return kb[i:j if j > 0 else None]


def _bloque(s: str, titulo: str) -> str:
    i = s.index(titulo)
    j = s.find("\n### ", i + 5)
    return s[i:j if j > 0 else None]


def _en_orden(texto: str, pasos: list[str]) -> None:
    pos = -1
    for p in pasos:
        k = texto.find(p, pos + 1)
        assert k > pos, f"«{p}» fuera de orden"
        pos = k


def test_seccion_119_existe_antes_del_pie():
    kb = _KB.read_text(encoding="utf-8")
    assert kb.index("## 119.") < kb.rindex("Calculadora BIPV — Innovación Química")
    s = _seccion(119)
    assert "PVsyst" not in s and "pendiente" not in s


def test_orden_bipv_una_superficie():
    b = _bloque(_seccion(119), "### BIPV de una superficie")
    for tipo in ("Fachada BIPV", "Techo inclinado", "Techo plano", "Pérgola", "Marquesina"):
        assert tipo in b, tipo
    _en_orden(b, ["🏠 Proyecto", "☀️ Recurso Solar", "🔬 Motor IV", "📐 Dimensionamiento",
                  "🔆 Motor Óptico", "🔀 Mismatch", "⚡ Diagrama Unifilar", "📊 Producción",
                  "💼 Presupuesto", "💰 Financiero", "🌿 Impacto CO₂", "📋 Ficha RETIE", "📄 Reporte"])
    assert "Sky View Factor" in b                       # SketchUp devuelve a Recurso Solar


def test_orden_granja_agrivoltaica():
    b = _bloque(_seccion(119), "### Granja fotovoltaica y agrivoltaica")
    _en_orden(b, ["🏠 Proyecto", "☀️ Recurso Solar", "📐 Dimensionamiento", "🌾 Granja FV",
                  "☀️ Recurso Solar", "🔆 Motor Óptico", "🔀 Mismatch", "⚡ Diagrama Unifilar",
                  "📊 Producción", "💼 Presupuesto", "💰 Financiero", "🌿 Impacto CO₂", "📄 Reporte"])
    assert "segunda pasada" in b and "107" in b and "Cantidad de inversores del proyecto" in b


def test_varias_superficies_remite_a_108():
    b = _bloque(_seccion(119), "### BIPV de varias superficies")
    assert "108" in b and "🗺️ Vista 3D" in b


def test_que_volver_a_ejecutar_si_cambias_algo():
    b = _bloque(_seccion(119), "### Si cambias algo")
    for t in ("inversor", "inclinación", "Granja FV", "ciudad", "Motor Óptico", "El diseño cambió después"):
        assert t in b, t


def test_la_seccion_2_remite_a_la_119():
    assert "sección 119" in _seccion(2)


def test_el_asistente_encuentra_la_seccion():
    kb = BaseConocimiento.cargar(str(_KB))
    for pregunta in ("¿cuál es el orden de las páginas para una granja agrivoltaica?",
                     "en qué orden ejecuto las páginas de una fachada BIPV"):
        titulos = [s["titulo"] for s in kb.buscar(pregunta, k=4)]
        assert any(t.startswith("119.") or "BIPV de una superficie" in t or "Granja fotovoltaica y agrivoltaica" in t
                   for t in titulos), titulos
