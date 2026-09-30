# -*- coding: utf-8 -*-
"""Spec ``05-perdidas-y-temperatura/motor-optico-ficha-termica`` (30-sep-2026).

Apartadó contra la referencia estándar internacional: al abrir el proyecto
guardado, 🔆 Motor Óptico quedó con NOCT = 35 °C y γ = −0.70 %/°C (valores
viejos del proyecto) aunque la ficha del JAM66D46-720/LB dice 45 °C y
−0.29 %/°C. El auto-llenado solo corre cuando cambia el panel, así que no los
corrigió, y 📊 Producción usa el NOCT del Motor Óptico para la temperatura de
celda: la pérdida por temperatura bajó de ≈ 6,3 % a 3,8 % en silencio.
"""
from pathlib import Path

import pytest

from calculos.motor_optico_ficha import (
    diferencias_ficha,
    ficha_termica,
    texto_aviso_ficha,
)

PAGINAS = Path(__file__).resolve().parents[1] / "pages"
JAM = {"nombre": "JAM66D46-720/LB", "NOCT": 45.0, "gamma_mp": -0.29, "Tk_gamma": -0.29}


def _fuente(patron):
    return next(PAGINAS.glob(patron)).read_text(encoding="utf-8")


# ── ficha_termica ────────────────────────────────────────────────────────────
def test_ficha_lee_noct_y_gamma():
    assert ficha_termica(JAM) == {"noct": 45.0, "gamma_pct": -0.29}


def test_ficha_usa_la_misma_prioridad_de_gamma_que_el_modelo():
    # modelo_iv: Tk_gamma, luego gamma_mp, luego beta_mp
    assert ficha_termica({"NOCT": 44, "Tk_gamma": -0.30, "gamma_mp": -0.40})["gamma_pct"] == -0.30
    assert ficha_termica({"NOCT": 44, "beta_mp": -0.35})["gamma_pct"] == -0.35


def test_ficha_sin_datos_devuelve_none():
    assert ficha_termica({}) == {"noct": None, "gamma_pct": None}
    assert ficha_termica({"NOCT": 0, "gamma_mp": None}) == {"noct": None, "gamma_pct": None}


# ── diferencias_ficha ────────────────────────────────────────────────────────
def test_apartado_detecta_noct_y_gamma_distintos():
    d = {x["campo"]: x for x in diferencias_ficha(35.0, -0.70, JAM)}
    assert d["NOCT"]["motor"] == 35.0 and d["NOCT"]["ficha"] == 45.0
    assert d["γ"]["motor"] == -0.70 and d["γ"]["ficha"] == -0.29
    assert d["NOCT"]["afecta_energia"] is True
    assert d["γ"]["afecta_energia"] is False


def test_iguales_o_casi_iguales_no_avisan():
    assert diferencias_ficha(45.0, -0.29, JAM) == []
    assert diferencias_ficha(45.4, -0.293, JAM) == []


def test_ficha_sin_datos_no_avisa():
    assert diferencias_ficha(35.0, -0.70, {}) == []


# ── texto_aviso_ficha ────────────────────────────────────────────────────────
def test_aviso_explica_el_efecto_en_temperatura():
    t = texto_aviso_ficha(diferencias_ficha(35.0, -0.70, JAM), "JAM66D46-720/LB", k_bipv=1.0)
    assert "NOCT" in t and "35" in t and "45" in t
    # (35 − 45) ÷ 800 × 1000 × 1,0 = −12,5 °C a 1000 W/m²
    assert "12.5 °C" in t
    assert "más fría" in t
    assert "Usar los de la ficha" in t


def test_aviso_vacio_sin_diferencias():
    assert texto_aviso_ficha([], "JAM", k_bipv=1.0) == ""


# ── páginas ──────────────────────────────────────────────────────────────────
def test_motor_optico_avisa_y_ofrece_boton():
    src = _fuente("5b_*Motor_Optico.py")
    assert "diferencias_ficha(" in src
    assert "Usar los de la ficha" in src
    assert "on_click=" in src


def test_motor_optico_autollenado_usa_ficha_termica():
    src = _fuente("5b_*Motor_Optico.py")
    assert "ficha_termica(" in src


def test_produccion_avisa_antes_de_simular():
    src = _fuente("6_*Produccion.py")
    assert "diferencias_ficha(" in src
    assert "texto_aviso_ficha(" in src


def test_manual_del_asistente_lo_explica():
    kb = (Path(__file__).resolve().parents[1] / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    assert "## 92." in kb
    seccion = kb[kb.index("## 92."):]
    for texto in ("NOCT", "Usar los de la ficha", "35", "45", "más fría"):
        assert texto in seccion
    assert "PVsyst" not in seccion
