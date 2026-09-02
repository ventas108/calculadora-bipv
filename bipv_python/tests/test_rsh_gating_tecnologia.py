# -*- coding: utf-8 -*-
"""Bug real encontrado el 1-sep-2026 comparando esta app contra PVsyst 8.1.5
con un panel real de silicio cristalino (XTP 50-17B, Sun Tech Solar, base de
datos original de PVsyst): `calcular_rsh_cdte()` (modelo Rsh exponencial
saturado, Mermoud 2005/PVsyst) se aplicaba con la MISMA razón Rsh_0/Rsh_ref
que capa fina para cualquier tecnología, sin distinguir.

Esta investigación llevó, el 2-sep-2026, a un hallazgo más profundo: el
modelo de diodo único en sí (De Soto 2006) no es el que usa PVsyst realmente
-- PVsyst usa su propio modelo v6 (Sauer/Roessler/Hansen 2015, IEEE J.
Photovoltaics, `pvlib.pvsystem.calcparams_pvsyst`), que SÍ aplica el modelo
Rsh exponencial a CUALQUIER tecnología (documentado oficialmente en
pvsyst.com/help-pvsyst7/pvmodule_rshexp.htm: R_sh_exp=5.5 "fairly constant
... regardless of technology", con la única excepción real de CdTe~3, y una
razón oficial documentada Rsh(0)/Rsh(STC)≈4 para cristalino). Se migró el
motor completo de De Soto a calcparams_pvsyst (ver DIAGNOSTICO_MOTOR_PVSYST.md)
-- la diferencia real entre CdTe y silicio cristalino no es "exponencial sí/
no", sino la RAZÓN Rsh_0/Rsh_ref (≈13.76 para el CdTe real calibrado de esta
app vs. 4 oficial para cristalino).

Validado contra el reporte real de PVsyst (mismo panel XTP 50-17B, mismos
parámetros Rs=0,716Ω/Rsh=190Ω/Gamma=1,070 que PVsyst calculó, T=25°C fijo
para aislar solo el efecto de irradiancia): con calcparams_pvsyst y
parámetros derivados 100% de la ficha (sin espiar ningún valor de PVsyst),
el resultado reproduce el caso real dentro de 0.2 puntos porcentuales.

Ver DIAGNOSTICO_RSH_TECNOLOGIA.md y DIAGNOSTICO_MOTOR_PVSYST.md.
"""
import numpy as np
import pytest

from calculos.modelo_iv import calcular_rsh_cdte, trasladar_parametros_gt
from calculos.produccion import _calcular_pmax_vectorizado
from calculos.produccion_iv import _pmp_iv_vectorizado
from calculos.mismatch_bypass import _sdm_vectorizado
from datos.tecnologias_bipv import ASP_ST1_T40
from tests.test_consistencia_sdm_entre_modulos import XTP_50_17B

G_PRUEBA = np.array([50.0, 100.0, 300.0, 700.0, 1000.0])
T_PRUEBA = 25.0


def test_silicio_cristalino_usa_razon_rsh0_distinta_de_capa_fina():
    # trasladar_parametros_gt() devuelve (I_L, I_o, R_s, R_sh, nNsVth) -- el
    # R_sh (índice 3) para Poli-Si usa el modelo exponencial CON la razón
    # oficial de PVsyst para cristalino (Rsh_0=4×Rsh_ref), DISTINTA de la
    # razón real calibrada para el CdTe de esta app (Rsh_0/Rsh_ref≈13.76).
    _, _, _, R_sh_obtenido, _ = trasladar_parametros_gt(700.0, T_PRUEBA, XTP_50_17B)

    R_sh_ref = XTP_50_17B["R_sh_ref"]
    R_sh_razon_cristalino = calcular_rsh_cdte(
        700.0, R_sh_ref, c_Rsh=5.5, R_sh_0=4.0 * R_sh_ref,
    )
    razon_cdte = ASP_ST1_T40["R_sh_0"] / ASP_ST1_T40["R_sh_ref"]
    R_sh_razon_cdte = calcular_rsh_cdte(
        700.0, R_sh_ref, c_Rsh=5.5, R_sh_0=razon_cdte * R_sh_ref,
    )

    assert R_sh_obtenido == pytest.approx(R_sh_razon_cristalino, rel=1e-6)
    # Las dos razones dan valores REALMENTE distintos a G=700 -- si no, el
    # test no probaría nada.
    assert abs(R_sh_razon_cristalino - R_sh_razon_cdte) > 1.0


def test_cdte_sigue_usando_su_propia_razon_rsh0_sin_cambios():
    # Regresión: el panel CdTe real (ASP_ST1_T40) sigue usando su razón
    # Rsh_0/Rsh_ref real calibrada -- no la razón oficial "4" de cristalino.
    _, _, _, R_sh_obtenido, _ = trasladar_parametros_gt(700.0, T_PRUEBA, ASP_ST1_T40)
    R_sh_exponencial_esperado = calcular_rsh_cdte(
        700.0, ASP_ST1_T40["R_sh_ref"], c_Rsh=5.5, R_sh_0=ASP_ST1_T40.get("R_sh_0"),
    )
    assert R_sh_obtenido == pytest.approx(R_sh_exponencial_esperado, rel=1e-6)


@pytest.mark.parametrize("nombre_func,func", [
    ("_calcular_pmax_vectorizado", lambda G, T, p: _calcular_pmax_vectorizado(G, T, p)),
    ("_pmp_iv_vectorizado",        lambda G, T, p: _pmp_iv_vectorizado(G, T, p)),
    ("_sdm_vectorizado",           lambda G, T, p: _sdm_vectorizado(G, T, p)[0]),
])
def test_las_3_funciones_vectorizadas_dan_menos_potencia_a_baja_irradiancia_con_razon_cristalina(
    nombre_func, func,
):
    # A G bajas/medias, la razón Rsh_0/Rsh_ref=4 (cristalino) produce MENOS
    # potencia que la razón real de capa fina (≈13.76, mucho más saturante)
    # aplicada al mismo panel -- mismo sentido de corrección que confirmó
    # PVsyst hoy: capa fina recupera mucho más Fill Factor a baja luz que
    # el silicio cristalino.
    T_arr = np.full_like(G_PRUEBA, T_PRUEBA)
    pmax_razon_cristalina = func(G_PRUEBA, T_arr, XTP_50_17B)

    razon_cdte = ASP_ST1_T40["R_sh_0"] / ASP_ST1_T40["R_sh_ref"]
    panel_razon_capa_fina = dict(
        XTP_50_17B, R_sh_0=razon_cdte * XTP_50_17B["R_sh_ref"],
    )
    pmax_razon_capa_fina = func(G_PRUEBA, T_arr, panel_razon_capa_fina)

    assert np.all(pmax_razon_cristalina <= pmax_razon_capa_fina + 1e-9), (
        f"{nombre_func}: la razón Rsh_0/Rsh_ref de cristalino debería dar "
        "menos Pmax a baja/media irradiancia que la razón de capa fina"
    )
    assert np.any(pmax_razon_capa_fina - pmax_razon_cristalina > 0.01)
