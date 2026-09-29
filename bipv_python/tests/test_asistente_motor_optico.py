# -*- coding: utf-8 -*-
"""El Asistente explica las constantes y métricas de 🔆 Motor Óptico con
cálculos simples (sección 83 de la base de conocimiento, 29-sep-2026).

Pedido del usuario: que responda con claridad qué son b₀, Uc, IAM difusa,
NOCT/k_BIPV, γ, suciedad y transparencia, con una cuenta de ejemplo como
«(NOCT 45 − 20) ÷ 800 × k … k = 1,15 es la opción más cercana al Uc = 20».
"""
import pytest

from calculos.asistente import BaseConocimiento


def _recuperado(pregunta: str) -> str:
    secciones = BaseConocimiento.cargar().buscar(pregunta, k=6)
    candidatas = [s for s in secciones if "Motor Óptico —" in s["titulo"]]
    assert candidatas, [s["titulo"] for s in secciones]
    return "\n".join(s["texto"] for s in candidatas)


@pytest.mark.parametrize("pregunta, texto", [
    ("que es b0 del vidrio y como se calcula el IAM", "1 − 0,05 × 1,000"),
    ("que significa la IAM difusa 0.95", "100 × (1 − 0,95) = **5 kWh/m²**"),
    ("que es Uc en PVsyst y a que k_BIPV equivale", "k = 1,15 es la opción más cercana"),
    ("como convierto Uc 20 de PVsyst a k BIPV de la app", "0,9 × (1 − 0,232) ÷ 20"),
    ("como se calcula la temperatura de la celda con NOCT y k_BIPV", "58,75 °C"),
    ("cuanta potencia pierde el panel por temperatura con gamma", "9,8 %"),
    ("que porcentaje de suciedad usa el motor optico por mes", "3,75 %"),
    ("que es la transparencia tau del vidrio", "800 kWh/m²"),
    ("como leo las metricas del motor optico POA bruta y POA efectiva", "POA efectiva → Producción"),
])
def test_asistente_explica_motor_optico(pregunta, texto):
    assert texto in _recuperado(pregunta)


def test_la_tabla_de_presets_advierte_que_no_es_numerica():
    from calculos.asistente import RUTA_BASE_CONOCIMIENTO
    with open(RUTA_BASE_CONOCIMIENTO, encoding="utf-8") as f:
        texto = f.read()
    assert "Uc = 20 equivale a k ≈ 1,1 (no a 1,3)" in texto


def test_cuentas_de_la_seccion_83_son_correctas():
    """Las cifras del manual salen de las mismas fórmulas de la app."""
    import math
    b0 = 0.05
    iam = lambda grados: 1 - b0 * (1 / math.cos(math.radians(grados)) - 1)
    assert round(iam(60), 3) == 0.950 and round(iam(70), 3) == 0.904 and round(iam(80), 3) == 0.762
    pvsyst = 0.9 * (1 - 0.232) / 20
    app = lambda k: (45 - 20) / 800 * k
    assert round(pvsyst, 4) == 0.0346 and round(pvsyst * 800, 1) == 27.6
    assert round(app(1.0) / pvsyst - 1, 3) == pytest.approx(-0.096, abs=1e-3)
    assert round(app(1.15) / pvsyst - 1, 3) == pytest.approx(0.040, abs=1e-3)
    assert round(pvsyst / app(1.0), 2) == 1.11
    t_cel = 30 + 800 * (45 - 20) / 800 * 1.15
    assert t_cel == 58.75 and round((t_cel - 25) * 0.29, 1) == 9.8
    from calculos.motor_optico import SOILING_COLOMBIA
    assert round(sum(SOILING_COLOMBIA.values()) / 12 * 100, 2) == 3.75
