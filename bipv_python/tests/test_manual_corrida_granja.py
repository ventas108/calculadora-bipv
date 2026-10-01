# -*- coding: utf-8 -*-
"""Manual del Asistente, sección 107 (1-oct-2026): corrida completa de una
granja desde cero, en orden, con las trampas encontradas en las pruebas de
Urabá (strings por tracker con total de cadenas, CSV de la calculadora
hermana y dobles conteos)."""
from pathlib import Path

KB = (Path(__file__).resolve().parents[1] / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")


def _seccion(n):
    i = KB.index(f"## {n}.")
    j = KB.find("\n## ", i + 5)
    return KB[i:j if j > 0 else None]


def test_orden_completo_de_la_granja():
    s = _seccion(107)
    s = s[s.index("### Granja FV — orden de las páginas"):s.index("### Trampa")]
    orden = ["🏠 Proyecto", "☀️ Recurso Solar, primera pasada", "📐 Dimensionamiento", "🌾 Granja FV, secciones 1 a 5",
             "☀️ Recurso Solar, segunda pasada", "🌾 Granja FV, secciones 5 a 9", "🔆 Motor Óptico", "🔀 Mismatch",
             "⚡ Diagrama Unifilar", "📊 Producción", "⚖️ Comparador", "📋 Ficha RETIE", "📄 Reporte"]
    posiciones = [s.index(t) for t in orden]
    assert posiciones == sorted(posiciones)


def test_trampas_y_csv():
    s = _seccion(107)
    for t in ("46,5 A", "40 A", "Escribe **1**", "solo FS_geometrico", "no** duplica", "nunca las filas de paneles",
              "Invertir FS", "no pulses «Adoptar»", "suciedad", "20 en serie × 16 strings"):
        assert t in s, t
    assert "PVsyst" not in s and "pendiente" not in s


def test_la_seccion_2_remite_a_la_107():
    assert "está en la **sección 107**" in _seccion(2)
