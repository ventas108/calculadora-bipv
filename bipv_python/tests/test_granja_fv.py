# -*- coding: utf-8 -*-
"""Spec ``03-dimensionamiento/granja-fv-campo`` (fase 1, 30-sep-2026).

Módulo 🌾 Granja FV: campo de filas (mesas) para granjas solares y
agrivoltaicas, separado de 🗺️ Vista 3D (BIPV) pero con los mismos datos del
proyecto. Referencia: informe de Apartadó de la referencia estándar
internacional — 308 × JAM66D46-720/LB (2384 × 1303 mm), mesas de 2 módulos
horizontales, inclinación 10°, separación entre filas 6,60 m, ancho de mesa
2,65 m, GCR 40,1 %, ángulo límite de sombra 6,5°, altura 3,00 m.
"""
import math
from pathlib import Path

import pytest

from calculos.granja_fv import (
    GEOMETRIA_DEFECTO,
    calcular_campo,
    coherencia_campo,
    dimensiones_modulo,
    geometria_desde_estado,
    modulos_del_proyecto,
    sugerir_distribucion,
    trazas_campo,
)

PAGINAS = Path(__file__).resolve().parents[1] / "pages"
JAM = {"nombre": "JA Solar JAM66D46-720/LB", "dimensiones_mm": "2384x1303x33 mm",
       "area_m2": 3.1064, "Pmax_stc": 720.0}


def _geo(**kw):
    g = dict(GEOMETRIA_DEFECTO)
    g.update(dict(tilt_deg=10.0, azimut_deg=180.0, ancho_terreno_m=80.0, largo_terreno_m=30.0,
                  modulos_pendiente=2, orientacion="horizontal", modulos_por_mesa=31,
                  mesas_por_fila=1, pasillo_m=3.0, pitch_m=6.60, altura_libre_m=2.4))
    g.update(kw)
    return g


# ── Dimensiones del módulo ───────────────────────────────────────────────────
def test_dimensiones_desde_la_ficha():
    d = dimensiones_modulo(JAM)
    assert (d["largo_m"], d["ancho_m"], d["origen"]) == (2.384, 1.303, "ficha")


def test_dimensiones_desde_largo_ancho_mm_y_estimadas():
    assert dimensiones_modulo({"largo_mm": 1200, "ancho_mm": 600})["largo_m"] == 1.2
    d = dimensiones_modulo({"area_m2": 2.0})
    assert d["origen"] == "estimado"
    assert d["largo_m"] * d["ancho_m"] == pytest.approx(2.0)


# ── Geometría de una mesa: la referencia de Apartadó ─────────────────────────
def test_mesa_de_apartado_coincide_con_la_referencia():
    c = calcular_campo(_geo(), dimensiones_modulo(JAM), 308, pmax_w=720.0)
    # 2 × 1,303 + 1 × 0,02 = 2,626 m en la pendiente
    assert c["ancho_mesa_m"] == pytest.approx(2.626)
    assert c["gcr"] == pytest.approx(2.626 / 6.60)              # 39,8 %
    assert c["gcr"] == pytest.approx(0.401, abs=0.004)           # referencia 40,1 %
    assert c["angulo_limite_deg"] == pytest.approx(6.5, abs=0.1)  # referencia 6,5°
    assert c["huella_ns_m"] == pytest.approx(2.626 * math.cos(math.radians(10)))
    assert c["corredor_m"] == pytest.approx(6.60 - c["huella_ns_m"])
    assert c["altura_superior_m"] == pytest.approx(2.4 + 2.626 * math.sin(math.radians(10)))
    assert c["altura_centro_m"] == pytest.approx(2.4 + 2.626 * math.sin(math.radians(10)) / 2)


def test_apartado_cabe_completo_y_cuenta_308():
    c = calcular_campo(_geo(), dimensiones_modulo(JAM), 308, pmax_w=720.0)
    assert c["cabe"] is True
    assert c["modulos_colocados"] == 308
    assert c["kwp"] == pytest.approx(221.76)
    assert c["filas_usadas"] == 5                    # 5 × 62 = 310 ≥ 308
    assert sum(m["modulos"] for m in c["mesas"]) == 308
    assert c["largo_fila_m"] == pytest.approx(31 * 2.384 + 30 * 0.02)


def test_terreno_chico_no_cabe_y_dice_cuantos_faltan():
    c = calcular_campo(_geo(largo_terreno_m=15.0), dimensiones_modulo(JAM), 308, pmax_w=720.0)
    assert c["cabe"] is False
    assert c["modulos_colocados"] == c["capacidad"] < 308
    assert c["faltan"] == 308 - c["capacidad"]


def test_filas_que_se_tocan_es_error():
    c = calcular_campo(_geo(pitch_m=2.0), dimensiones_modulo(JAM), 308, pmax_w=720.0)
    assert any("se tocan" in e for e in c["errores"])


def test_suelo_libre_y_area_de_modulos():
    c = calcular_campo(_geo(), dimensiones_modulo(JAM), 308, pmax_w=720.0)
    assert c["area_modulos_m2"] == pytest.approx(308 * 2.384 * 1.303)
    proy = sum((m["x1"] - m["x0"]) * (m["y1"] - m["y0"]) for m in c["mesas"])
    assert c["suelo_libre_pct"] == pytest.approx(100 * (1 - proy / (80.0 * 30.0)))


def test_orientacion_vertical_usa_el_largo_en_la_pendiente():
    c = calcular_campo(_geo(orientacion="vertical", modulos_pendiente=1), dimensiones_modulo(JAM),
                       100, pmax_w=720.0)
    assert c["ancho_mesa_m"] == pytest.approx(2.384)


def test_varias_mesas_por_fila_con_pasillo():
    c = calcular_campo(_geo(modulos_por_mesa=10, mesas_por_fila=3, pasillo_m=4.0, ancho_terreno_m=90.0),
                       dimensiones_modulo(JAM), 120, pmax_w=720.0)
    assert c["largo_fila_m"] == pytest.approx(3 * (10 * 2.384 + 9 * 0.02) + 2 * 4.0)
    assert c["modulos_colocados"] == 120
    xs = sorted({round(m["x0"], 6) for m in c["mesas"]})
    assert len(xs) == 3


# ── Sugerir distribución ─────────────────────────────────────────────────────
def test_sugerir_distribucion_apartado_cabe_en_el_terreno():
    s = sugerir_distribucion(308, dimensiones_modulo(JAM), _geo(ancho_terreno_m=48.9, largo_terreno_m=48.9))
    c = calcular_campo(_geo(ancho_terreno_m=48.9, largo_terreno_m=48.9, **s), dimensiones_modulo(JAM),
                       308, pmax_w=720.0)
    assert c["cabe"] and c["modulos_colocados"] == 308


def test_sugerir_distribucion_imposible_devuelve_none():
    assert sugerir_distribucion(308, dimensiones_modulo(JAM), _geo(ancho_terreno_m=5.0,
                                                                   largo_terreno_m=5.0)) is None


# ── Datos del proyecto ───────────────────────────────────────────────────────
def test_modulos_del_proyecto_prefiere_produccion():
    assert modulos_del_proyecto({"N_paneles_final": 308, "N_paneles_granja": 300}) == \
        {"n": 308, "fuente": "produccion", "dimensionamiento": 300}
    assert modulos_del_proyecto({"N_paneles_granja": 308})["fuente"] == "dimensionamiento"
    assert modulos_del_proyecto({})["n"] == 0


def test_geometria_desde_estado_usa_tilt_y_azimut_del_proyecto():
    g = geometria_desde_estado({"tilt_fachada": 10, "azimuth_fachada": 180, "area_fachada_m2": 2393.0,
                                "granja_fv": {"pitch_m": 6.6}})
    assert (g["tilt_deg"], g["azimut_deg"], g["pitch_m"]) == (10.0, 180.0, 6.6)
    assert g["ancho_terreno_m"] * g["largo_terreno_m"] == pytest.approx(2393.0)


# ── Coherencia con el resto del proyecto ─────────────────────────────────────
def _estado_apartado(**kw):
    e = {"N_paneles_final": 308, "N_paneles_granja": 308, "factor_ocupacion_pct": 40.0,
         "area_fachada_m2": 2393.0, "tipo_instalacion": "Granja fotovoltaica",
         "bifacial_activo": True, "bifacial_cfg": {"gcr": 0.40, "altura_m": 2.63}}
    e.update(kw)
    return e


def _niveles(checks):
    return {c["id"]: c["nivel"] for c in checks}


def test_coherencia_apartado_todo_verde():
    c = calcular_campo(_geo(), dimensiones_modulo(JAM), 308, pmax_w=720.0)
    niv = _niveles(coherencia_campo(c, _estado_apartado()))
    assert niv["modulos"] == "🟢"
    assert niv["gcr_bifacial"] == "🟢"
    assert niv["altura_bifacial"] == "🟢"


def test_coherencia_detecta_gcr_y_altura_distintos_del_modelo_bifacial():
    c = calcular_campo(_geo(), dimensiones_modulo(JAM), 308, pmax_w=720.0)
    checks = coherencia_campo(c, _estado_apartado(bifacial_cfg={"gcr": 0.25, "altura_m": 1.0}))
    niv = _niveles(checks)
    assert niv["gcr_bifacial"] == "🟠" and niv["altura_bifacial"] == "🟠"
    texto = " ".join(x["texto"] for x in checks)
    assert "0.40" in texto and "Recurso Solar" in texto


def test_coherencia_dimensionamiento_distinto_de_produccion():
    c = calcular_campo(_geo(), dimensiones_modulo(JAM), 308, pmax_w=720.0)
    niv = _niveles(coherencia_campo(c, _estado_apartado(N_paneles_granja=300)))
    assert niv["modulos_fuentes"] == "🟠"


def test_coherencia_no_cabe_es_rojo():
    c = calcular_campo(_geo(largo_terreno_m=15.0), dimensiones_modulo(JAM), 308, pmax_w=720.0)
    assert _niveles(coherencia_campo(c, _estado_apartado()))["modulos"] == "🔴"


def test_coherencia_avisa_si_hay_energia_multisuperficie_publicada():
    c = calcular_campo(_geo(), dimensiones_modulo(JAM), 308, pmax_w=720.0)
    niv = _niveles(coherencia_campo(c, _estado_apartado(multisup_activo=True)))
    assert niv["multisuperficie"] == "🟠"


# ── 3D ───────────────────────────────────────────────────────────────────────
def test_trazas_dibujan_una_mesa_por_rectangulo_y_el_suelo():
    c = calcular_campo(_geo(), dimensiones_modulo(JAM), 308, pmax_w=720.0)
    trazas = trazas_campo(c)
    nombres = [t.name for t in trazas]
    assert "Suelo / cultivo" in nombres and "Mesas de paneles" in nombres
    mesas = next(t for t in trazas if t.name == "Mesas de paneles")
    assert len(mesas.x) == 4 * len(c["mesas"])


# ── Páginas ──────────────────────────────────────────────────────────────────
def _fuente(patron):
    return next(PAGINAS.glob(patron)).read_text(encoding="utf-8")


def test_pagina_granja_usa_el_modulo_comun():
    src = _fuente("9b_*Granja_FV.py")
    for f in ("calcular_campo(", "coherencia_campo(", "trazas_campo(", "sugerir_distribucion("):
        assert f in src


def test_vista_3d_dibuja_la_granja_con_el_mismo_calculo():
    src = _fuente("9_*Vista_3D.py")
    assert "calcular_campo(" in src and "trazas_campo(" in src
    assert "Filas de paneles por matriz" not in src


def test_manual_del_asistente_lo_explica():
    kb = (Path(__file__).resolve().parents[1] / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    seccion = kb[kb.index("## 93."):]
    for texto in ("GCR", "ángulo límite", "6,60", "2,626", "39,8", "Sugerir distribución"):
        assert texto in seccion
    assert "PVsyst" not in seccion
