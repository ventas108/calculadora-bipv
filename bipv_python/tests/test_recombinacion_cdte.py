"""
Tests del término de recombinación en capa intrínseca (Merten et al. 1998,
IEEE Trans. Electron Devices 45, 423-429 -- adoptado por PVsyst para capa
fina CdTe/a-Si, vía pvlib.singlediode.bishop88). Ver DIAGNOSTICO_RECOMBINACION_CDTE.md.

Investigado el 2-sep-2026 tras encontrar en PVsyst 8.1.5 (módulo real
ASP-ST1-T40 reconstruido y validado) que el término de recombinación SÍ está
activo (d²/µτ=1,13 1/V) en la corrida real que reproduce mejor el patrón
mensual de irradiancia baja. El motor ahora soporta el mecanismo, pero NO
está activado para ningún panel del catálogo (d2mutau=0 por defecto en todos,
incluido ASP-ST1-T40) -- agregarlo sobre R_s/R_sh_ref ya calibrados con datos
reales de laboratorio (sin ese término) rompía la validación real de FF a
G=200 W/m² (47.06% calculado vs 76.28% real medido) porque el R_s real ya
"absorbe" implícitamente el efecto de recombinación. Estos tests verifican
que el MECANISMO en sí es correcto y no afecta a ningún panel existente.
"""
import copy

import numpy as np
import pytest

from calculos.modelo_iv import (
    _parametros_recombinacion,
    calcular_pmax_vectorizado,
    resolver_curva_iv,
    trasladar_parametros_gt,
)
from datos.tecnologias_bipv import ASP_ST1_T40, MODULOS_BIPV


def test_parametros_recombinacion_por_defecto_es_nulo():
    # Ningún panel del catálogo trae d2mutau hoy -- el mecanismo debe quedar
    # inactivo (0.0, inf) para todos, sin excepción.
    for nombre, panel in MODULOS_BIPV.items():
        d2mutau, NsVbi = _parametros_recombinacion(panel)
        assert d2mutau == 0.0, nombre
        assert NsVbi == np.inf, nombre


def test_asp_st1_t40_no_activa_recombinacion():
    # El panel real de Teusaquillo (único candidato con evidencia real de
    # PVsyst) se dejó deliberadamente SIN d2mutau -- ver docstring del
    # módulo y el comentario en datos/tecnologias_bipv.py.
    d2mutau, NsVbi = _parametros_recombinacion(ASP_ST1_T40)
    assert d2mutau == 0.0
    assert NsVbi == np.inf


def test_bishop88_con_d2mutau_cero_reproduce_singlediode_estandar():
    # d2mutau=0 debe ser matemáticamente idéntico al modelo de un diodo
    # estándar (pvlib.pvsystem.singlediode) -- verifica que
    # calcular_pmax_vectorizado() no introduce ninguna diferencia para
    # cualquier panel real del catálogo cuando el mecanismo está inactivo.
    G = np.array([1000.0, 500.0, 100.0, 20.0])
    T = np.full_like(G, 25.0)
    for nombre, panel in list(MODULOS_BIPV.items())[:5]:
        from calculos.modelo_iv import tiene_sdm_completo
        if not tiene_sdm_completo(panel):
            continue
        I_L, I_o, R_s, R_sh, nNsVth = trasladar_parametros_gt(G, T, panel)
        import pvlib
        esperado = np.array(
            pvlib.pvsystem.singlediode(
                photocurrent=I_L, saturation_current=I_o,
                resistance_series=R_s, resistance_shunt=R_sh,
                nNsVth=nNsVth, method="lambertw",
            )["p_mp"], dtype=float,
        )
        obtenido = calcular_pmax_vectorizado(G, T, panel)
        np.testing.assert_allclose(obtenido, esperado, rtol=1e-9, err_msg=nombre)


def test_calcular_pmax_vectorizado_devuelve_array_escribible():
    # Bug real encontrado y corregido (2-sep-2026): np.asarray() puede
    # devolver una vista de solo lectura del array interno de pvlib,
    # rompiendo las mutaciones in-place que hacen produccion.py/
    # produccion_iv.py (`pmax[G < 5.0] = 0.0`) -- ValueError: assignment
    # destination is read-only. calcular_pmax_vectorizado() debe usar
    # np.array() (copia) para que el resultado sea siempre mutable.
    G = np.array([1000.0, 2.0])
    T = np.array([25.0, 25.0])
    pmax = calcular_pmax_vectorizado(G, T, ASP_ST1_T40)
    pmax[G < 5.0] = 0.0   # no debe lanzar
    assert pmax[1] == 0.0


def test_recombinacion_activada_reduce_pmax_respecto_al_modelo_estandar():
    # Verifica que el MECANISMO en sí (no un panel real) funciona: activar
    # d2mutau en una copia sintética del panel debe reducir Pmax en STC
    # respecto al mismo panel sin el término (el término de recombinación es
    # una pérdida adicional, nunca una ganancia).
    panel_sin = copy.deepcopy(ASP_ST1_T40)
    panel_con = copy.deepcopy(ASP_ST1_T40)
    panel_con["d2mutau"] = 0.885   # V -- valor real leído de PVsyst 8.1.5 (ver
                                    # DIAGNOSTICO_RECOMBINACION_CDTE.md), usado
                                    # aquí solo para probar el mecanismo, no
                                    # como calibración de producción.
    panel_con["V_bi"] = 0.9

    r_sin = resolver_curva_iv(1000.0, 25.0, panel_sin, n_puntos=0)
    r_con = resolver_curva_iv(1000.0, 25.0, panel_con, n_puntos=0)

    assert r_con["Pmax"] < r_sin["Pmax"]
    assert r_con["Voc"] < r_sin["Voc"]


def test_stc_recombinacion_reproduce_ajuste_real_pvsyst():
    # Ancla real (2-sep-2026): con el set COMPLETO de parámetros que PVsyst
    # 8.1.5 ajustó de verdad para el módulo ASP-ST1-T40 reconstruido y
    # validado (Rs=12.347 Ω, Rsh_ref=2600 Ω, gamma_ref=2.15, d2mutau=0.885 V
    # [=1/1.13, ver conversión de unidades en DIAGNOSTICO_RECOMBINACION_CDTE.md],
    # V_bi=0.9 V típico), resolviendo I_L_ref/I_o_ref por autoconsistencia en
    # Isc=0.80A/Voc=116.0V, el modelo reproduce Pmax_STC=60.87 W -- muy
    # cerca del Pmax_STC=60.59 W que PVsyst calculó internamente para esa
    # misma corrida (0.5% de diferencia), confirmando que la integración de
    # bishop88 replica correctamente el ajuste real de PVsyst cuando se le
    # dan sus mismos parámetros (no es válido para ASP_ST1_T40 en producción
    # -- ver test_asp_st1_t40_no_activa_recombinacion).
    N_s = 141
    panel = {
        "tecnologia": "CdTe",
        "N_s": N_s,
        "gamma_ref": 2.15,
        "mu_gamma": 0.0,
        "R_s": 12.347,
        "R_sh_ref": 2600.0,
        "R_sh_0": 13.76 * 2600.0,
        "I_L_ref": 0.8099,
        "I_o_ref": 2.381e-07,
        "d2mutau": 0.885,
        "V_bi": 0.9,
        "Pmax_stc": 63.0,
        "Isc_stc": 0.80,
        "Tk_alfa": 0.060,  # %/°C -- mismo valor real que ASP_ST1_T40
    }
    r = resolver_curva_iv(1000.0, 25.0, panel, n_puntos=0)
    assert r["Voc"] == pytest.approx(116.0, abs=0.05)
    assert r["Isc"] == pytest.approx(0.80, abs=0.005)
    assert r["Pmax"] == pytest.approx(60.59, rel=0.01)
