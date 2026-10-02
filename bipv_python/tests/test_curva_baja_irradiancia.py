# -*- coding: utf-8 -*-
"""Spec 04-produccion-energia/curva-baja-irradiancia-ficha (2-oct-2026).

Motor IV calibraba la baja luz con un solo dato: la eficiencia relativa a
200 W/m² de la ficha o, para CIGS sin él, el 97 % genérico. Las fichas suelen
traer una gráfica «Performance at low irradiance» con varios puntos (la teja
Hanergy HW-MQSB-V1 empieza en 300 W/m²) y no se podía usar. Con el 97 % la
teja de 32 W daba ~99-100 % entre 300 y 600 W/m² cuando la ficha dice 80-96 %.
"""
from pathlib import Path

import numpy as np
import pytest

from calculos.modelo_iv import (
    calcular_pmax_vectorizado,
    estimar_sdm_desde_ficha,
    parsear_curva_baja_irradiancia,
    validar_sdm_vs_ficha,
)

_RAIZ = Path(__file__).resolve().parents[1]

# Hanergy HanTile HW-MQSB-V1, 32 W (ficha real): tabla STC y puntos leídos de
# la gráfica «Performance at low irradiance».
TEJA_32 = {
    "nombre": "HW-MQSB-V1 32 W", "tecnologia": "CIGS", "N_s": 19,
    "Voc_stc": 10.8, "Isc_stc": 4.1, "Vmp_stc": 8.9, "Imp_stc": 3.6, "Pmax_stc": 32.0,
    "Tk_beta": -0.36, "Tk_gamma": -0.40, "Tk_alfa": 0.003, "NOCT": 52.7,
}
CURVA_TEJA = "300:80; 400:88; 500:93; 600:96; 700:97,5; 800:98,5; 900:99"


def _rel(sdm, gs):
    gs = np.asarray(list(gs) + [1000.0], dtype=float)
    p = calcular_pmax_vectorizado(gs, np.full(len(gs), 25.0), sdm)
    return 100.0 * (p[:-1] / gs[:-1]) / (p[-1] / 1000.0)


@pytest.mark.parametrize("texto, esperado", [
    ("300:80; 400:88", [(300.0, 80.0), (400.0, 88.0)]),
    ("800:98,5;300:80", [(300.0, 80.0), (800.0, 98.5)]),             # coma decimal, se ordena
    ("300:0.80; 600:0.96", [(300.0, 80.0), (600.0, 96.0)]),            # fracciones → %
    ("300:80; 1000:100; 1200:101", [(300.0, 80.0)]),                   # 1.000 es la referencia
    ("", []), (None, []), (float("nan"), []), ("texto", []),
    ([(300, 80), (500, 93)], [(300.0, 80.0), (500.0, 93.0)]),
])
def test_parsear_curva(texto, esperado):
    assert parsear_curva_baja_irradiancia(texto) == esperado


def test_la_teja_se_calibra_con_su_curva():
    est = estimar_sdm_desde_ficha({**TEJA_32, "curva_baja_irradiancia": CURVA_TEJA})
    sdm = {**TEJA_32, **est}
    assert est["_ajuste_200"] == "curva"
    assert validar_sdm_vs_ficha(sdm)["validacion_ok"]                       # STC sigue anclado
    puntos = {round(p["G"]): p for p in est["_ajuste_curva"]}
    assert set(puntos) == {300, 400, 500, 600, 700, 800, 900}
    # Zona alta: ±2 puntos. Con R_s ≥ 1 % de Vmp/Imp (Spec 04/coef-temperatura-
    # ficha) el ajuste ya no puede llevar R_s a 0 Ω y a 500 W/m² queda ~1,9.
    for g in (500, 600, 700, 800, 900):
        assert abs(puntos[g]["modelo"] - puntos[g]["ficha"]) <= 2.0, g
    rel = dict(zip((300, 400, 500, 600), _rel(sdm, (300, 400, 500, 600))))
    assert rel[300] == pytest.approx(puntos[300]["modelo"], abs=0.05)
    # Mucho más cerca de la ficha que el 97 % genérico (que daba ~99-100 %).
    defecto = dict(zip((300, 400, 500), _rel({**TEJA_32, **estimar_sdm_desde_ficha(TEJA_32)}, (300, 400, 500))))
    for g in (300, 400, 500):
        assert abs(rel[g] - puntos[g]["ficha"]) < abs(defecto[g] - puntos[g]["ficha"]) - 4.0, g


def test_si_la_curva_no_se_puede_seguir_queda_avisado():
    # A 300 W/m² la gráfica dice 80 % pero las curvas I-V de la misma ficha
    # dan ~88 %; el modelo de un diodo no baja de ~90 %: se avisa en qué punto.
    est = estimar_sdm_desde_ficha({**TEJA_32, "curva_baja_irradiancia": CURVA_TEJA})
    assert est["_error_ajuste_200"] and "300 W/m²" in est["_error_ajuste_200"]
    assert est["_desv_max_curva"] > 3.0


def test_una_curva_coherente_se_reproduce():
    # Curva fabricada con el propio modelo (92 % a 200 W/m²): el ajuste por
    # varios puntos la recupera.
    base = {**TEJA_32, **estimar_sdm_desde_ficha({**TEJA_32, "eficiencia_rel_200": 92.0})}
    gs = (200, 300, 400, 600, 800)
    curva = "; ".join(f"{g}:{r:.2f}" for g, r in zip(gs, _rel(base, gs)))
    est = estimar_sdm_desde_ficha({**TEJA_32, "curva_baja_irradiancia": curva})
    assert est["_error_ajuste_200"] is None and est["_desv_max_curva"] <= 0.3
    assert est["_rel_200_modelo"] == pytest.approx(92.0, abs=0.3)


def test_la_curva_manda_sobre_el_dato_de_200():
    est = estimar_sdm_desde_ficha({**TEJA_32, "curva_baja_irradiancia": CURVA_TEJA,
                                   "eficiencia_rel_200": 99.0})
    assert est["_ajuste_200"] == "curva"


def test_sin_curva_nada_cambia():
    est = estimar_sdm_desde_ficha(TEJA_32)
    assert est["_ajuste_200"] == "defecto" and est["_rel_200_modelo"] == pytest.approx(97.0, abs=0.3)
    assert est.get("_ajuste_curva") is None


def test_catalogo_pagina_y_motor_iv():
    src_cat = (_RAIZ / "datos" / "catalogo_paneles_excel.py").read_text(encoding="utf-8")
    assert '"curva_baja_irradiancia"' in src_cat and "CurvaBajaIrradiancia" in src_cat
    pag = (_RAIZ / "pages" / "14_📋_Catálogo_Paneles.py").read_text(encoding="utf-8")
    assert '"Curva baja irradiancia (G:η %)":' in pag and '"CurvaBajaIrradiancia":' in pag
    iv = (_RAIZ / "pages" / "3_🔬_Motor_IV.py").read_text(encoding="utf-8")
    assert "Eficiencia relativa vs G" in iv and "_ajuste_curva" in iv
    assert '== "curva"' in iv


def test_el_catalogo_lee_la_columna(monkeypatch, tmp_path):
    import pandas as pd
    import datos.catalogo_paneles_excel as cpe
    ruta = tmp_path / "cat.xlsx"
    pd.DataFrame([{"TipoPanel": "Teja prueba 32", "PmaxWp": 32, "Voc_STC": 10.8, "Isc_STC": 4.1,
                   "Vmp_STC": 8.9, "Imp_STC": 3.6, "Tecnologia": "CIGS",
                   "CurvaBajaIrradiancia": CURVA_TEJA}]).to_excel(ruta, sheet_name=cpe._SHEET, index=False)
    monkeypatch.setattr(cpe, "_EXCEL", ruta)
    p = cpe.cargar_catalogo_paneles()["Teja prueba 32"]
    assert parsear_curva_baja_irradiancia(p["curva_baja_irradiancia"])[0] == (300.0, 80.0)


def test_manual_del_asistente_seccion_114():
    kb = (_RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    i = kb.index("## 114.")
    s = kb[i:kb.find("\n## ", i + 5) if kb.find("\n## ", i + 5) > 0 else None]
    for t in ("Curva baja irradiancia (G:η %)", "300:80", "Eficiencia relativa vs G", "Hanergy",
              "97 %", "Origen del modelo"):
        assert t in s, t
    assert i < kb.rindex("Calculadora BIPV — Innovación Química")
    assert "PVsyst" not in s and "pendiente" not in s
