# -*- coding: utf-8 -*-
"""Spec 04-produccion-energia/coef-temperatura-ficha (2-oct-2026).

El SDM estimado desde ficha ajustaba solo el coeficiente de la potencia (γ)
y no el del Voc (β), que salía de la física de la celda: teja Hanergy de
32 W con β −0,22 %/°C (ficha −0,36) y, en Motor IV, Voc a 61 °C de 9,92 V
cuando la ficha da 9,39 V. Los paneles que caen al método de respaldo
(Batzelis) quedaban además con mu_gamma = 0 y γ de hasta −0,88 %/°C (ficha
−0,36). Y el ajuste a la curva de baja irradiancia llevaba R_s a 0 Ω.
"""
from pathlib import Path

import pytest

from calculos.modelo_iv import estimar_sdm_desde_ficha, resolver_curva_iv, validar_sdm_vs_ficha

_RAIZ = Path(__file__).resolve().parents[1]

TEJA_32 = {"nombre": "HW-MQSB-V1 32 W", "tecnologia": "CIGS", "N_s": 19,
           "Voc_stc": 10.8, "Isc_stc": 4.1, "Vmp_stc": 8.9, "Imp_stc": 3.6, "Pmax_stc": 32.0,
           "Tk_beta": -0.36, "Tk_gamma": -0.40, "Tk_alfa": 0.003, "NOCT": 52.7}
CURVA = "300:80; 400:88; 500:93; 600:96; 700:97,5; 800:98,5; 900:99"
JAM_730 = {"nombre": "JAM66D46-730/LB", "tecnologia": "N-Type TOPCon Bifacial",
           "Voc_stc": 49.0, "Isc_stc": 18.85, "Vmp_stc": 41.39, "Imp_stc": 17.64, "Pmax_stc": 730.0,
           "N_s": 66, "Tk_beta": -0.25, "Tk_gamma": -0.29, "Tk_alfa": 0.045}
# EINNOVA ESM-550T (catálogo real): cae al método de respaldo Batzelis.
ESM_550T = {"nombre": "EINNOVA ESM-550T", "tecnologia": "N-Type TopCon Bifacial Mono",
            "Voc_stc": 47.1, "Isc_stc": 14.43, "Vmp_stc": 39.8, "Imp_stc": 13.81, "Pmax_stc": 550.0,
            "N_s": 132, "NsA": 171.6, "Tk_beta": -0.26, "Tk_gamma": -0.36}


def _coef(sdm):
    """(β Voc, γ Pmax) en %/°C con el mismo resolutor que usan todos los motores."""
    a = resolver_curva_iv(1000, 25, sdm, n_puntos=0)
    b = resolver_curva_iv(1000, 26, sdm, n_puntos=0)
    return 100 * (b["Voc"] / a["Voc"] - 1), 100 * (b["Pmax"] / a["Pmax"] - 1)


def _sdm(ficha):
    return {**ficha, **estimar_sdm_desde_ficha(ficha)}


def test_silicio_reproduce_beta_y_gamma_de_la_ficha():
    beta, gamma = _coef(_sdm(JAM_730))
    assert beta == pytest.approx(-0.25, abs=0.005) and gamma == pytest.approx(-0.29, abs=0.005)


def test_metodo_de_respaldo_ya_no_deja_gamma_mal():
    est = estimar_sdm_desde_ficha(ESM_550T)
    assert est["_metodo"] == "fit_desoto_batzelis"
    beta, gamma = _coef({**ESM_550T, **est})
    assert gamma == pytest.approx(-0.36, abs=0.01)                          # antes −0,88
    assert beta == pytest.approx(-0.26, abs=0.01)


@pytest.mark.parametrize("ficha", [TEJA_32, {**TEJA_32, "curva_baja_irradiancia": CURVA}])
def test_teja_gamma_exacto_beta_mas_cerca_y_avisado(ficha):
    est = estimar_sdm_desde_ficha(ficha)
    sdm = {**ficha, **est}
    beta, gamma = _coef(sdm)
    assert gamma == pytest.approx(-0.40, abs=0.01)
    assert abs(beta + 0.36) < 0.08                                          # antes −0,22 a −0,25
    assert est["_beta_voc_modelo"] == pytest.approx(beta, abs=0.01)
    assert est["_aviso_temperatura"] and "β de la ficha" in est["_aviso_temperatura"]
    assert validar_sdm_vs_ficha(sdm)["validacion_ok"]                       # STC sin cambios


def test_r_s_no_llega_a_cero_con_la_curva():
    est = estimar_sdm_desde_ficha({**TEJA_32, "curva_baja_irradiancia": CURVA})
    assert est["R_s"] >= 0.01 * 8.9 / 3.6 - 1e-9                            # antes 0,0001 Ω
    assert est["_ajuste_200"] == "curva"


def test_miasole_70n_dentro_de_tolerancia():
    f = {"nombre": "FLEX-03-70N", "tecnologia": "CIGS", "N_s": 40, "Voc_stc": 23.2, "Isc_stc": 4.67,
         "Vmp_stc": 18.1, "Imp_stc": 3.88, "Pmax_stc": 70.0, "Tk_beta": -0.28, "Tk_gamma": -0.38,
         "Tk_alfa": 0.008}
    est = estimar_sdm_desde_ficha(f)
    beta, gamma = _coef({**f, **est})
    assert abs(beta + 0.28) <= 0.03 and gamma == pytest.approx(-0.38, abs=0.01)
    assert est["_aviso_temperatura"] is None
    assert est["_rel_200_modelo"] == pytest.approx(97.0, abs=0.3)            # baja luz sin cambios


def test_el_resolutor_usa_la_eg_del_panel():
    sdm = _sdm(JAM_730)
    v_hot = resolver_curva_iv(1000, 60, sdm, n_puntos=0)["Voc"]
    v_hot_nominal = resolver_curva_iv(1000, 60, {**sdm, "EgRef": None}, n_puntos=0)["Voc"]
    assert abs(v_hot - v_hot_nominal) > 0.05


def test_motor_iv_muestra_beta_y_gamma():
    iv = (_RAIZ / "pages" / "3_🔬_Motor_IV.py").read_text(encoding="utf-8")
    assert "_beta_voc_modelo" in iv and "_gamma_pmax_modelo" in iv and "_aviso_temperatura" in iv


def test_manual_del_asistente_seccion_115():
    kb = (_RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    i = kb.index("## 115.")
    s = kb[i:kb.find("\n## ", i + 5) if kb.find("\n## ", i + 5) > 0 else None]
    for t in ("β", "γ", "Voc", "Origen del modelo", "−0,88", "Hanergy", "Dimensionamiento"):
        assert t in s, t
    assert i < kb.rindex("Calculadora BIPV — Innovación Química")
    assert "PVsyst" not in s and "pendiente" not in s
