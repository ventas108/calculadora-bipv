"""
Tests de JRC/Huld como motor PRIMARIO de energía para CdTe en produccion.py
(2-sep-2026). Ver DIAGNOSTICO_JRC_HULD_PRIMARIO_CDTE.md.

Decisión basada en evidencia real: comparado contra una corrida real de
PVsyst 8.1.5 (panel ASP-ST1-T40, fachada vertical, Teusaquillo), el patrón
mensual de PR de JRC/Huld correlaciona con el real (r=0.545, RMSE=13.2pts)
mientras el SDM no correlaciona en absoluto (r=-0.142, RMSE=16.2pts) -- el
SDM con Rsh exponencial produce una "joroba" de eficiencia >100% entre
G=100-300 W/m² que ni PVsyst real ni el modelo empírico JRC/Huld reproducen.

Alcance del cambio: SOLO calculos/produccion.py (cálculo de energía). Motor
IV (produccion_iv.py), mismatch/bypass (mismatch_bypass.py) y MPPT compartido
(mppt_combinado.py) siguen exclusivamente en el SDM -- necesitan la curva I-V
completa (Vmp/Voc/Isc) que JRC/Huld no calcula.
"""
import copy

import numpy as np
import pytest

from calculos.produccion import _calcular_pmax_vectorizado
from calculos.produccion_iv import _pmp_iv_vectorizado
from calculos.modelo_iv import trasladar_parametros_gt
from calculos.modelo_jrc_huld import potencia_jrc
from datos.tecnologias_bipv import ASP_ST1_T40, MODULOS_BIPV
import pvlib


def test_cdte_en_produccion_usa_jrc_huld_no_sdm():
    # Ancla real: en STC (G=1000, T=25), JRC/Huld reproduce EXACTO Pmax_stc
    # (factor=1 por construcción, ln(1)=0) -- el SDM da 60.48W (4% menos,
    # por la inconsistencia real de la ficha Vmpp*Impp vs Pmax nominal, ver
    # DIAGNOSTICO_RECOMBINACION_CDTE.md). Esta es la firma distintiva que
    # confirma cuál motor está corriendo de verdad.
    G = np.array([1000.0])
    T = np.array([25.0])
    pmax = _calcular_pmax_vectorizado(G, T, ASP_ST1_T40)
    assert pmax[0] == pytest.approx(63.0, abs=0.01)   # JRC/Huld: exacto a Pmax_stc

    IL, Io, Rs, Rsh, nNsVth = trasladar_parametros_gt(1000.0, 25.0, ASP_ST1_T40)
    r = pvlib.pvsystem.singlediode(IL, Io, Rs, Rsh, nNsVth, method='lambertw')
    assert pmax[0] != pytest.approx(float(r['p_mp']), rel=1e-3)   # distinto del SDM (60.48W)


def test_cdte_en_produccion_coincide_con_potencia_jrc_directa():
    G = np.array([1000.0, 500.0, 200.0, 100.0, 50.0, 20.0])
    T = np.full_like(G, 25.0)
    esperado = potencia_jrc(G, T, float(ASP_ST1_T40["Pmax_stc"]), tecnologia="CdTe")
    obtenido = _calcular_pmax_vectorizado(G, T, ASP_ST1_T40)
    np.testing.assert_allclose(obtenido, esperado, rtol=1e-9)


def test_cdte_en_produccion_no_muestra_joroba_sobre_100_por_ciento():
    # El defecto real que motivó este cambio: el SDM mostraba un pico de
    # ~106% de eficiencia relativa alrededor de G=200 W/m² (una "joroba" de
    # +6 puntos sobre STC). JRC/Huld, al ser empírico (ajustado contra
    # mediciones reales, sin el término Rsh exponencial), tiene como mucho un
    # sobrepico real MUY pequeño cerca de STC (~+0.7% a G=700 W/m², visto en
    # los datos reales) -- lejos del +6% del SDM. El límite de 2% separa
    # claramente ese comportamiento real del defecto que se corrigió.
    G_arr = np.array([1000.0, 700.0, 500.0, 300.0, 200.0, 150.0, 100.0])
    T_arr = np.full_like(G_arr, 25.0)
    pmax = _calcular_pmax_vectorizado(G_arr, T_arr, ASP_ST1_T40)
    eff_rel = pmax / (ASP_ST1_T40["Pmax_stc"] * G_arr / 1000.0)
    assert np.all(eff_rel <= 1.02), f"sobrepico mayor al esperado: {eff_rel}"
    # a partir de G=500 (donde el sobrepico real, si existe, ya quedó atrás),
    # la eficiencia relativa debe ser monótona no-creciente al bajar G (los
    # valores están en orden de G DECRECIENTE, así que diff <= 0 = no-creciente).
    assert np.all(np.diff(eff_rel[2:]) <= 1e-9), f"no es monótona por debajo de G=500: {eff_rel}"


def test_produccion_iv_sigue_usando_sdm_para_cdte():
    # Motor IV (curva I-V completa) NO debe cambiar -- necesita Vmp/Voc/Isc,
    # que JRC/Huld no calcula. Debe seguir dando el mismo Pmax que el SDM
    # directo (60.48W en STC para ASP-ST1-T40), no el 63.0W de JRC/Huld.
    G = np.array([1000.0])
    T = np.array([25.0])
    pmax_iv = _pmp_iv_vectorizado(G, T, ASP_ST1_T40)
    IL, Io, Rs, Rsh, nNsVth = trasladar_parametros_gt(1000.0, 25.0, ASP_ST1_T40)
    r = pvlib.pvsystem.singlediode(IL, Io, Rs, Rsh, nNsVth, method='lambertw')
    assert pmax_iv[0] == pytest.approx(float(r['p_mp']), rel=1e-6)
    assert pmax_iv[0] != pytest.approx(63.0, abs=0.5)   # NO debe ser JRC/Huld


def test_paneles_no_cdte_no_cambian_de_motor():
    # Verificación de blast radius: solo CdTe cambia. Cualquier panel real
    # del catálogo clasificado como CIS/Crystalline/otro sigue en el SDM
    # dentro de produccion.py, sin excepción.
    from calculos.modelo_iv import tiene_sdm_completo
    G = np.array([500.0])
    T = np.array([25.0])
    no_cdte = [p for p in MODULOS_BIPV.values() if p.get("tecnologia") != "CdTe"]
    for panel in no_cdte:
        if not tiene_sdm_completo(panel):
            continue
        pmax_prod = _calcular_pmax_vectorizado(G, T, panel)
        IL, Io, Rs, Rsh, nNsVth = trasladar_parametros_gt(500.0, 25.0, panel)
        r = pvlib.pvsystem.singlediode(IL, Io, Rs, Rsh, nNsVth, method='lambertw')
        assert pmax_prod[0] == pytest.approx(float(r['p_mp']), rel=1e-6), panel.get("nombre")


def test_cdte_sin_pmax_stc_cae_al_fallback_lineal_sin_reventar():
    # Panel CdTe con Pmax_stc ausente/0: no debe intentar JRC/Huld (división
    # por 0 / resultado sin sentido) -- debe caer al mismo fallback lineal
    # genérico que ya existía para paneles sin SDM completo.
    panel = copy.deepcopy(ASP_ST1_T40)
    panel["Pmax_stc"] = 0
    G = np.array([500.0, 2.0])
    T = np.array([25.0, 25.0])
    pmax = _calcular_pmax_vectorizado(G, T, panel)
    assert np.all(np.isfinite(pmax))
    assert pmax[1] == 0.0   # G<5 sigue apagado
