# -*- coding: utf-8 -*-
"""#67: el camino NsA de estimar_sdm_desde_ficha también detecta half-cut."""
import pytest

from calculos.modelo_iv import estimar_sdm_desde_ficha

# Panel típico 144 half-cells (equivalente eléctrico: 72 celdas en serie)
_FICHA_144 = {
    "nombre": "HalfCut 540W",
    "tecnologia": "Mono-Si",
    "Voc_stc": 49.5, "Isc_stc": 13.85,
    "Vmp_stc": 41.65, "Imp_stc": 12.97,
}


def test_nsa_duplicado_se_corrige():
    panel = dict(_FICHA_144, N_s=144, NsA=1.05 * 144)  # NsA arrastra el doble conteo
    res = estimar_sdm_desde_ficha(panel)
    assert res is not None
    assert res["_ns_corregido"] is True
    assert res["_N_s_usado"] == 72
    # a_ref recomputado con el Ns corregido: 1.05 × 72 × 0.025693 ≈ 1.94 V
    assert res["a_ref"] == pytest.approx(1.05 * 72 * 0.025693, rel=0.01)
    assert res["_ns_halfcut_info"]["tipo"] == "ns_duplicado"


def test_nsa_sin_ns_tambien_detecta():
    panel = dict(_FICHA_144, NsA=1.05 * 144)  # sin N_s explícito
    res = estimar_sdm_desde_ficha(panel)
    assert res is not None
    assert res["_ns_corregido"] is True
    assert res["_N_s_usado"] == 72


def test_nsa_correcto_no_se_toca():
    panel = dict(_FICHA_144, N_s=72, NsA=1.05 * 72)
    res = estimar_sdm_desde_ficha(panel)
    assert res is not None
    assert res["_ns_corregido"] is False
    assert res["_N_s_usado"] == 72
    assert res["a_ref"] == pytest.approx(1.05 * 72 * 0.025693, rel=0.01)


def test_voc_modelo_fisico_tras_correccion():
    # Con Ns duplicado sin corregir, a_ref se duplica y el Voc del SDM se
    # dispararía; corregido, Voc/celda vuelve al rango físico (0.55-0.76 V)
    panel = dict(_FICHA_144, N_s=144, NsA=1.05 * 144)
    res = estimar_sdm_desde_ficha(panel)
    voc_por_celda = panel["Voc_stc"] / res["_N_s_usado"]
    assert 0.55 <= voc_por_celda <= 0.76
