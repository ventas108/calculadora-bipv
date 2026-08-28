# -*- coding: utf-8 -*-
"""
Tests de calculos/trm_utils.py -- auditoría (27-ago-2026).

Bug real encontrado: la TRM oficial real del día (verificada en vivo contra
datos.gov.co: 3.118,24 COP/USD) estaba por debajo del umbral `_ALERTA_BAJA`
(3.800) y muy por debajo de `TRM_DEFAULT` (4.200) -- el widget mostraba una
advertencia falsa de "TRM parece baja" para la tasa oficial correcta.
"""
from calculos.trm_utils import TRM_DEFAULT, _ALERTA_BAJA, _ALERTA_ALTA

# TRM oficial real, verificada en vivo contra datos.gov.co durante la
# auditoría de esta sesión (27-ago-2026) -- no es un valor inventado.
_TRM_REAL_VERIFICADA_27AGO2026 = 3_118.24


def test_trm_real_verificada_no_dispara_alerta_baja():
    assert _TRM_REAL_VERIFICADA_27AGO2026 > _ALERTA_BAJA


def test_trm_real_verificada_no_dispara_alerta_alta():
    assert _TRM_REAL_VERIFICADA_27AGO2026 < _ALERTA_ALTA


def test_trm_default_esta_dentro_de_las_alertas():
    # El valor de respaldo (si las 2 APIs fallan) no debería disparar sus
    # propias alertas -- sería una contradicción mostrar el default y de
    # inmediato advertir que ese mismo valor "parece raro".
    assert _ALERTA_BAJA < TRM_DEFAULT < _ALERTA_ALTA


def test_alerta_baja_tiene_margen_bajo_la_trm_real():
    # No debe quedar pegado al valor real de hoy -- necesita margen para
    # absorber una fluctuación normal del peso sin generar falsos positivos
    # de nuevo en unas semanas.
    assert _ALERTA_BAJA <= _TRM_REAL_VERIFICADA_27AGO2026 * 0.90
