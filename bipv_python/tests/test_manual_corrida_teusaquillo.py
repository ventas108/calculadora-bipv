# -*- coding: utf-8 -*-
"""Manual del Asistente, secciones 108 y 109 (1-oct-2026): corrida completa
de un proyecto BIPV de varias superficies (Teusaquillo) y la tensión máxima
del sistema del módulo como límite del Voc."""
from pathlib import Path

KB = (Path(__file__).resolve().parents[1] / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")


def _seccion(n):
    i = KB.index(f"## {n}.")
    j = KB.find("\n## ", i + 5)
    return KB[i:j if j > 0 else None]


def test_orden_de_teusaquillo():
    s = _seccion(108)
    s = s[s.index("### Teusaquillo — orden de las páginas"):s.index("### Teusaquillo — valores de referencia")]
    orden = ["📋 Catálogo de Paneles", "🏠 Proyecto", "☀️ Recurso Solar", "📐 Dimensionamiento", "🔆 Motor Óptico",
             "🔀 Mismatch", "🗺️ Vista 3D", "🔌 Inversor y grupos", "🔗 Usar sistema multi-superficie",
             "⚡ Unifilar", "📄 Reporte"]
    posiciones = [s.index(t) for t in orden]
    assert posiciones == sorted(posiciones)


def test_trampas_de_teusaquillo():
    s = _seccion(108)
    for t in ("SG8.0RT", "7 en serie × 16 strings", "1.000 V", "1.002 V", "293 V", "caja combinadora",
              "fusible gPV de 2 A", "**no trae NOCT**", "45 °C", "81 m²", "80,64 m²", "MID 15KTL3-X",
              "DC/AC 1,05", "5.944 kWh"):
        assert t in s, t
    assert "PVsyst" not in s and "pendiente" not in s


def test_regla_de_la_tension_del_modulo():
    s = _seccion(109)
    for t in ("el menor de los dos", "IEC 61730", "Sin el dato, todo queda como antes", "V sistema máx",
              "Maximum System Voltage", "tensión máx. del módulo"):
        assert t in s, t
    assert "PVsyst" not in s and "pendiente" not in s


def test_secciones_antes_del_pie_y_remision_desde_la_2():
    assert KB.index("## 109.") < KB.rindex("Calculadora BIPV — Innovación Química")
    assert "está en la **sección 108**" in _seccion(2)
