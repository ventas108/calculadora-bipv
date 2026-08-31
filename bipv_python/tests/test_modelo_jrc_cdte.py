# -*- coding: utf-8 -*-
"""Verificación cruzada CdTe (Huld/JRC power-rating model) -- ver docstring
de `calculos/modelo_jrc_cdte.py` para el contexto completo (por qué existe:
Teusaquillo dio PR>100%, la literatura de CdTe BIPV tropical nunca reporta
más de 77%).
"""
import numpy as np
import pytest

from calculos.modelo_jrc_cdte import (
    potencia_jrc_cdte,
    calcular_pr_jrc_cdte,
    temperatura_modulo_faiman_cdte,
)


def test_potencia_en_condiciones_stc_exactas_da_p_stc():
    # En I'=1 (1000 W/m²) y T'=0 (T_módulo=25°C), ln(I')=0 y T'=0 -- el
    # corchete del polinomio se reduce a 1 exactamente, sin importar los
    # coeficientes. Es el ancla física más simple del modelo: a condiciones
    # STC, el modelo debe reproducir la potencia nominal de placa.
    p = potencia_jrc_cdte(poa_wm2=1000.0, t_modulo_c=25.0, p_stc_w=63.0)
    assert p == pytest.approx(63.0, abs=1e-9)


def test_potencia_de_noche_es_cero_no_nan():
    p = potencia_jrc_cdte(poa_wm2=np.array([0.0, 0.0]), t_modulo_c=np.array([15.0, 14.0]), p_stc_w=63.0)
    assert list(p) == [0.0, 0.0]
    assert not np.any(np.isnan(p))


def test_potencia_a_baja_irradiancia_no_supera_proporcion_lineal_de_forma_desbocada():
    # Sanity check de orden de magnitud: a G=200 W/m² (I'=0.2) sin corrección
    # de temperatura (T'=0), el factor de corrección no debe disparar la
    # potencia a un múltiplo absurdo de la proporción lineal ideal
    # (200/1000 × P_STC = 12.6 W) -- debe quedar en el mismo orden de magnitud.
    p = potencia_jrc_cdte(poa_wm2=200.0, t_modulo_c=25.0, p_stc_w=63.0)
    p_lineal = 0.2 * 63.0
    assert 0 < p < p_lineal * 3


def test_temperatura_modulo_usa_coeficientes_cdte_no_los_genericos_de_pvlib():
    # Los coeficientes CdTe (n=23.37, n*=5.44) son distintos de los default
    # de pvlib.temperature.faiman (u0=25.0, u1=6.84, calibrados para c-Si) --
    # deben dar una temperatura de módulo distinta para el mismo input.
    from pvlib.temperature import faiman as faiman_generico

    t_cdte = temperatura_modulo_faiman_cdte(poa_wm2=800.0, t_ambiente_c=20.0, viento_ms=2.0)
    t_generico = faiman_generico(800.0, 20.0, 2.0)
    assert t_cdte != pytest.approx(t_generico, abs=0.01)


def test_calcular_pr_jrc_cdte_caso_sintetico_dia_completo():
    # Día sintético simple (irradiancia tipo campana, 12 horas de luz) para
    # verificar que el pipeline completo (temperatura -> potencia -> PR)
    # corre sin errores y da un PR en un rango físicamente plausible
    # (ni 0%, ni por encima de 100% para un caso simple sin efectos
    # especiales de baja irradiancia extrema).
    horas = np.arange(24)
    poa = np.clip(800 * np.sin(np.pi * (horas - 6) / 12), 0, None)  # pico ~800 W/m² al mediodía
    t_amb = np.full(24, 15.0)
    viento = np.full(24, 2.0)

    r = calcular_pr_jrc_cdte(poa, t_amb, viento, p_stc_w=63.0)

    assert r["POA_anual_kWh_m2"] > 0
    assert r["E_anual_kWh"] > 0
    assert 0 < r["PR_pct"] < 120  # rango amplio -- 1 solo día no es representativo de un PR anual
    assert len(r["P_dc_jrc_w"]) == 24


def test_calcular_pr_jrc_cdte_sin_irradiancia_no_revienta():
    r = calcular_pr_jrc_cdte(
        poa_wm2=np.zeros(24), t_ambiente_c=np.full(24, 10.0), viento_ms=np.full(24, 1.0),
        p_stc_w=63.0,
    )
    assert r["E_anual_kWh"] == 0.0
    assert r["PR_pct"] is None  # sin irradiancia, PR no es evaluable -- no se inventa un 0%
