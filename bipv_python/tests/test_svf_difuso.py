# -*- coding: utf-8 -*-
"""
Tests del Sky View Factor (SVF) difuso — calcular_svf_difuso() en
calculos/sombras_3d.py — y de su agregación por arreglo,
agregar_valor_por_puntos() en calculos/agregacion_fs.py.

Caso de validación analítico: panel VERTICAL (tilt=90°, mirando al Sur)
frente a una pared DELGADA de ancho finito W a distancia horizontal d,
infinitamente alta (bloquea TODA elevación por igual, sin dependencia
de gamma -- ver nota de geometría abajo). La pared bloquea exactamente el
rango de azimut relativo |psi| < psi_max = atan((W/2)/d), para toda
elevación. Con el peso Lambertiano/isotrópico que usa calcular_svf_difuso()
-- cos(theta) con dOmega, y cos(theta)=cos(gamma)cos(psi) -- el integrando
factoriza en gamma y psi:

    peso = cos²(gamma)·cos(psi) dgamma dpsi   (dOmega=cos(gamma)dgamma dpsi)

y como el bloqueo NO depende de gamma, la integral en gamma se cancela entre
numerador y denominador, dejando un cierre exacto de una sola variable:

    f_svf(psi_max) = 1 - sin(psi_max)

(∫cos(psi)dpsi = sin(psi); ver derivación completa y verificación numérica
independiente -- por dos caminos distintos, incluida una integración pura
sin ray-casting -- en la sesión que escribió este test).

Nota de geometría del mesh de prueba: la pared se modela con espesor FINO
(2 cm) a propósito -- con espesor grueso, las caras LATERALES de la pared
(en los bordes ±W/2) bloquean unos grados extra para rayos muy rasantes
(gamma≈0°, donde el peso cos²(gamma) es MÁXIMO), sesgando el resultado
observable hasta un ~3% aun con grilla fina. Verificado empíricamentemente:
el resultado converge al valor analítico a medida que el espesor de la
pared de prueba se reduce (0.5 m → 3% de error; 0.02 m → <0.05% de error)
-- esto es un artefacto de la GEOMETRÍA SINTÉTICA de este test, no de
calcular_svf_difuso() (que solo lanza rayos contra lo que se le da).
"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calculos.sombras_3d import calcular_svf_difuso  # noqa: E402
from calculos.agregacion_fs import agregar_valor_por_puntos  # noqa: E402


def _pared_delgada(ancho_m: float, distancia_m: float,
                    espesor_m: float = 0.02, alto_m: float = 2000.0):
    """Pared rectangular DELGADA y muy alta (aprox. infinita en elevación,
    ver docstring del módulo) al SUR (Y negativo) del punto, de ancho
    `ancho_m` centrado en X=0, a `distancia_m` de distancia horizontal."""
    caja = trimesh.creation.box(extents=[ancho_m, espesor_m, alto_m])
    caja.apply_translation([0.0, -distancia_m, alto_m / 2.0])
    return caja


def _punto(nombre="P1", fachada="Test", x=0.0, y=0.0, z=0.0):
    return {
        "nombre": nombre, "fachada": fachada, "x": x, "y": y, "z": z,
        "n_modulos": 1.0, "area_activa_m2": 0.0, "potencia_instalada_kw": 0.0,
    }


def _f_svf_analitico_pared_ancho_finito(psi_max_rad: float) -> float:
    return 1.0 - math.sin(psi_max_rad)


# ── 1. Sin obstrucción → f_svf = 1.0 exacto (por construcción, ver docstring) ──

def test_sin_obstruccion_f_svf_es_uno():
    # Malla lejos de cualquier punto de análisis: no puede bloquear nada.
    malla_lejana = trimesh.creation.box(extents=[1, 1, 1])
    malla_lejana.apply_translation([10_000.0, 10_000.0, 10_000.0])
    puntos = [_punto(x=0.0, y=0.0, z=1.5)]
    df = calcular_svf_difuso(malla_lejana, puntos, tilt_deg=90.0, azimuth_deg=180.0,
                              resolucion_deg=5.0)
    assert df.loc[0, "f_svf"] == 1.0


# ── 2. Pared delgada de ancho finito — cierre analítico independiente ────────

@pytest.mark.parametrize("ancho_m,distancia_m", [
    (20.0, 10.0),   # psi_max = 45°
    (10.0, 10.0),   # psi_max ≈ 26.57°
    (6.0, 10.0),    # psi_max ≈ 16.70°
    (40.0, 10.0),   # psi_max ≈ 63.43°
])
def test_pared_finita_coincide_con_formula_analitica(ancho_m, distancia_m):
    psi_max = math.atan((ancho_m / 2.0) / distancia_m)
    esperado = _f_svf_analitico_pared_ancho_finito(psi_max)

    pared = _pared_delgada(ancho_m, distancia_m)
    puntos = [_punto(x=0.0, y=0.0, z=0.0)]
    df = calcular_svf_difuso(pared, puntos, tilt_deg=90.0, azimuth_deg=180.0,
                              resolucion_deg=1.0)
    obtenido = df.loc[0, "f_svf"]

    # Tolerancia: solo discretización de la grilla (paso 1°) -- con pared
    # delgada el residuo medido es <0.05% (ver docstring del módulo).
    assert obtenido == pytest.approx(esperado, abs=0.002), (
        f"psi_max={math.degrees(psi_max):.2f}°: analítico={esperado:.5f} "
        f"vs ray-casting={obtenido:.5f}"
    )


def test_pared_muy_ancha_bloquea_casi_todo():
    # psi_max→90° (pared mucho más ancha que la distancia) => f_svf→0.
    pared = _pared_delgada(ancho_m=2000.0, distancia_m=5.0)
    puntos = [_punto(x=0.0, y=0.0, z=0.0)]
    df = calcular_svf_difuso(pared, puntos, tilt_deg=90.0, azimuth_deg=180.0,
                              resolucion_deg=2.0)
    assert df.loc[0, "f_svf"] < 0.02


# ── 3. Panel horizontal (tilt=0) no debe reventar el caso degenerado ──────────

def test_panel_horizontal_no_falla_caso_degenerado():
    malla_lejana = trimesh.creation.box(extents=[1, 1, 1])
    malla_lejana.apply_translation([10_000.0, 10_000.0, 10_000.0])
    puntos = [_punto(x=0.0, y=0.0, z=1.5)]
    df = calcular_svf_difuso(malla_lejana, puntos, tilt_deg=0.0, azimuth_deg=0.0,
                              resolucion_deg=5.0)
    assert df.loc[0, "f_svf"] == 1.0


# ── 4. Múltiples puntos, distintas distancias a la MISMA pared ───────────────

def test_puntos_mas_lejos_de_la_pared_ven_mas_cielo():
    # Pared fija en Y=-10 (ancho 10 m). Un punto MÁS CERCA de la pared la ve
    # bajo un ángulo MAYOR (psi_max mayor, más sombra angular) -> f_svf MENOR.
    pared = _pared_delgada(ancho_m=10.0, distancia_m=10.0)
    puntos = [
        _punto(nombre="lejos_de_pared", x=0.0, y=-2.0, z=0.0),   # a 8 m de la pared
        _punto(nombre="cerca_de_pared", x=0.0, y=-9.0, z=0.0),   # a 1 m de la pared
    ]
    df = calcular_svf_difuso(pared, puntos, tilt_deg=90.0, azimuth_deg=180.0,
                              resolucion_deg=2.0)
    f_lejos = df.set_index("Punto").loc["lejos_de_pared", "f_svf"]
    f_cerca = df.set_index("Punto").loc["cerca_de_pared", "f_svf"]
    assert f_lejos > f_cerca


# ── 5. Agregación por arreglo (agregacion_fs.agregar_valor_por_puntos) ───────

def test_agregar_valor_por_puntos_promedio_simple_sin_pesos():
    df = pd.DataFrame({
        "Punto": ["P1", "P2"],
        "f_svf": [0.8, 0.6],
        "n_modulos": [0.0, 0.0],
        "area_activa_m2": [0.0, 0.0],
        "potencia_instalada_kw": [0.0, 0.0],
    })
    valor, auditoria = agregar_valor_por_puntos(df, columna_valor="f_svf")
    assert valor == pytest.approx(0.7)  # promedio simple: pesos inválidos -> fallback
    assert auditoria["modo_aplicado"] == "simple"


def test_agregar_valor_por_puntos_ponderado_por_modulos():
    df = pd.DataFrame({
        "Punto": ["P1", "P2"],
        "f_svf": [1.0, 0.0],
        "n_modulos": [3.0, 1.0],   # P1 pesa 3x más que P2
        "area_activa_m2": [0.0, 0.0],
        "potencia_instalada_kw": [0.0, 0.0],
    })
    valor, auditoria = agregar_valor_por_puntos(df, columna_valor="f_svf")
    assert valor == pytest.approx(0.75)  # (1.0*3 + 0.0*1) / 4
    assert auditoria["modo_aplicado"] == "modulos"


def test_agregar_valor_por_puntos_df_vacio_no_falla():
    df = pd.DataFrame(columns=["Punto", "f_svf", "n_modulos", "area_activa_m2", "potencia_instalada_kw"])
    valor, auditoria = agregar_valor_por_puntos(df, columna_valor="f_svf")
    assert valor == 1.0  # sin puntos -> sin reducción, comportamiento neutro
