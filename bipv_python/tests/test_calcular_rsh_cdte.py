# -*- coding: utf-8 -*-
"""calcular_rsh_cdte() -- Rsh exponencial SATURADO (2026-08-25).

Hallazgo: la fórmula anterior (R_sh_ref × exp(−c_Rsh×(G/Gref−1)) + R_sh_base,
con R_sh_base siempre en 0.0 porque ningún panel lo definía) crecía SIN
LÍMITE a medida que G bajaba -- a G=100 W/m² con c_Rsh=5.5 llegaba a ~245×
R_sh_ref, un valor sin sentido físico. La corrección usa el mismo modelo
saturado que pvlib.pvsystem.calcparams_pvsyst/_pvsyst_Rsh (Mermoud 2005):
Rsh satura hacia un techo FINITO (R_sh_0) a baja irradiancia, en vez de
diverger. Ver tests/test_validacion_vba.py para la validación de extremo a
extremo (Fill Factor) contra la hoja FF_vs_Irradiancia del XLSM auditado.
"""
import numpy as np
import pytest

from calculos.modelo_iv import calcular_rsh_cdte

R_SH_REF = 1340.6
C_RSH = 5.5


def test_satura_hacia_un_techo_finito_en_vez_de_diverger():
    # Antes: Rsh(G=1) ~ 245x R_sh_ref para c_Rsh=5.5 (sin límite al bajar G).
    # Ahora: con R_sh_0 explícito, Rsh nunca supera R_sh_0.
    r_sh_0 = 18450.0
    rsh_muy_bajo = calcular_rsh_cdte(1.0, R_SH_REF, c_Rsh=C_RSH, R_sh_0=r_sh_0)
    assert rsh_muy_bajo <= r_sh_0 * 1.001  # tolerancia de punto flotante


def test_ancla_exactamente_en_r_sh_ref_al_llegar_a_g_ref():
    # Rsh(G_ref) debe ser EXACTAMENTE R_sh_ref, sin importar R_sh_0/c_Rsh --
    # R_sh_ref ya está calibrado contra la ficha técnica en STC.
    for r_sh_0 in (5000.0, 18450.0, 50000.0):
        rsh = calcular_rsh_cdte(1000.0, R_SH_REF, c_Rsh=C_RSH, R_sh_0=r_sh_0, G_ref=1000.0)
        assert rsh == pytest.approx(R_SH_REF, rel=1e-9)


def test_sin_r_sh_0_reproduce_exactamente_la_formula_anterior_sin_regresion():
    # Un panel sin R_sh_0 calibrado (la mayoría del catálogo, por ahora) no
    # debe cambiar de comportamiento con esta corrección.
    G = np.array([100.0, 300.0, 1000.0])
    formula_anterior = R_SH_REF * np.exp(-C_RSH * (G / 1000.0 - 1.0))
    rsh_nueva = calcular_rsh_cdte(G, R_SH_REF, c_Rsh=C_RSH, R_sh_0=None)
    np.testing.assert_allclose(rsh_nueva, formula_anterior, rtol=1e-9)


def test_es_monotonamente_decreciente_con_la_irradiancia():
    Gs = np.array([50.0, 100.0, 200.0, 400.0, 600.0, 800.0, 1000.0])
    rsh = calcular_rsh_cdte(Gs, R_SH_REF, c_Rsh=C_RSH, R_sh_0=18450.0)
    assert all(rsh[i] > rsh[i + 1] for i in range(len(rsh) - 1))


def test_acepta_entrada_vectorizada_y_escalar():
    escalar = calcular_rsh_cdte(500.0, R_SH_REF, c_Rsh=C_RSH, R_sh_0=18450.0)
    assert isinstance(escalar, float)

    vector = calcular_rsh_cdte(np.array([500.0, 600.0]), R_SH_REF, c_Rsh=C_RSH, R_sh_0=18450.0)
    assert vector.shape == (2,)
    assert vector[0] == pytest.approx(escalar)


def test_nunca_es_negativo_incluso_con_r_sh_0_muy_grande():
    # R_sh_0 extremadamente grande podría, en teoría, hacer que el término
    # de anclaje (Rsh_base) se vuelva negativo -- debe recortarse a 0, no
    # propagar una resistencia física sin sentido.
    rsh = calcular_rsh_cdte(1000.0, R_SH_REF, c_Rsh=1.0, R_sh_0=1e9, G_ref=1000.0)
    assert rsh >= 0.0
