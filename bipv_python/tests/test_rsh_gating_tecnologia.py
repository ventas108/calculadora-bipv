# -*- coding: utf-8 -*-
"""Bug real encontrado el 1-sep-2026 comparando esta app contra PVsyst 8.1.5
con un panel real de silicio cristalino (XTP 50-17B, Sun Tech Solar, base de
datos original de PVsyst): `calcular_rsh_cdte()` (modelo Rsh exponencial
saturado, Mermoud 2005 -- diseñado para replicar el comportamiento real de
capa fina, validado contra Batzner et al. 2001 para CdTe) se aplicaba SIN
verificar la tecnología en las 5 implementaciones del SDM. `datos/
tecnologias_bipv.py::CONSTANTES_TECNOLOGIA` ya tenía `c_Rsh=5.5` idéntico
para CdTe, Mono-Si Y Poli-Si -- pero nada evitaba que ese modelo de capa fina
se usara también para silicio cristalino, que no tiene ese comportamiento.

Prueba aislada corrida contra el reporte real de PVsyst (mismo panel, mismos
parámetros Rs=0,716Ω/Rsh=190Ω/Gamma=1,070 que PVsyst calculó, T=25°C fijo
para aislar solo el efecto de irradiancia): el modelo CdTe daba +3,2% de
ganancia irreal donde PVsyst midió -3,90% de pérdida real; con el Rsh
estándar de pvlib (correcto para silicio) el resultado bajó a +0,5% --
mucho más cerca de la física real, aunque no exacto (esperable: pvlib y el
motor interno de PVsyst no son la misma implementación).

Ver DIAGNOSTICO_RSH_TECNOLOGIA.md para el análisis completo.
"""
import numpy as np
import pytest

from calculos.modelo_iv import calcular_rsh_cdte, trasladar_parametros_gt
from calculos.produccion import _calcular_pmax_vectorizado
from calculos.produccion_iv import _pmp_iv_vectorizado
from calculos.mismatch_bypass import _sdm_vectorizado
from calculos.mppt_combinado import _params_grupo
from datos.tecnologias_bipv import ASP_ST1_T40
from tests.test_consistencia_sdm_entre_modulos import XTP_50_17B

G_PRUEBA = np.array([50.0, 100.0, 300.0, 700.0, 1000.0])
T_PRUEBA = 25.0


def _rsh_esperado_estandar(panel, G):
    """Rsh que pvlib.calcparams_desoto calcula por sí solo (lineal en 1/G) --
    lo que las 5 implementaciones deben usar ahora para tecnologías que NO
    son capa fina."""
    import pvlib
    K_BOLTZMANN, Q_ELECTRON, T_REF_K, G_REF = (
        1.380649e-23, 1.602176634e-19, 298.15, 1000.0,
    )
    from calculos.modelo_iv import obtener_constantes_tecnologia
    constantes = obtener_constantes_tecnologia(panel["tecnologia"])
    Vt_ref = K_BOLTZMANN * T_REF_K / Q_ELECTRON
    nNsVth_ref = panel["a_ref"] * Vt_ref
    _, _, _, R_sh, _ = pvlib.pvsystem.calcparams_desoto(
        effective_irradiance=G, temp_cell=np.full_like(G, T_PRUEBA),
        alpha_sc=panel["Tk_alfa"] / 100.0 * panel["Isc_stc"],
        a_ref=nNsVth_ref, I_L_ref=panel["I_L_ref"], I_o_ref=panel["I_o_ref"],
        R_sh_ref=panel["R_sh_ref"], R_s=panel["R_s"],
        EgRef=constantes["Eg_ref"], dEgdT=constantes["dEgdT"],
        irrad_ref=G_REF, temp_ref=25.0,
    )
    return R_sh


def test_silicio_cristalino_ya_no_usa_el_rsh_exponencial_de_capa_fina():
    # trasladar_parametros_gt() devuelve (I_L, I_o, R_s, R_sh, nNsVth) -- el
    # R_sh (índice 3) para Poli-Si debe coincidir con el estándar de pvlib,
    # NO con calcular_rsh_cdte() (que sí le correspondía antes del fix).
    _, _, _, R_sh_obtenido, _ = trasladar_parametros_gt(700.0, T_PRUEBA, XTP_50_17B)
    R_sh_exponencial = calcular_rsh_cdte(700.0, XTP_50_17B["R_sh_ref"], c_Rsh=5.5)
    R_sh_estandar = _rsh_esperado_estandar(XTP_50_17B, np.array([700.0]))[0]

    assert R_sh_obtenido == pytest.approx(R_sh_estandar, rel=1e-6)
    # El estándar y el exponencial dan valores REALMENTE distintos a G=700 --
    # si no, el test no probaría nada (ambos modelos podrían coincidir por
    # casualidad en un punto particular).
    assert abs(R_sh_obtenido - R_sh_exponencial) > 1.0


def test_cdte_sigue_usando_el_rsh_exponencial_sin_cambios():
    # Regresión: el panel CdTe real (ASP_ST1_T40) SÍ debe seguir usando el
    # modelo exponencial -- ese comportamiento es correcto para capa fina y
    # no debe alterarse por este fix.
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
def test_las_3_funciones_vectorizadas_dan_menos_potencia_a_baja_irradiancia_para_silicio(
    nombre_func, func,
):
    # Verificación directa del efecto del fix: a G moderada/baja, el Rsh
    # estándar (más bajo que el exponencial de capa fina en ese rango) debe
    # producir MENOS potencia que si se hubiera usado el modelo CdTe --
    # exactamente el sentido de corrección que confirmó PVsyst (pérdida real
    # a baja irradiancia, no ganancia).
    T_arr = np.full_like(G_PRUEBA, T_PRUEBA)
    pmax_corregido = func(G_PRUEBA, T_arr, XTP_50_17B)

    # Panel "viejo" sintético: mismos parámetros pero forzando manualmente el
    # Rsh exponencial (el comportamiento de antes del fix) via un panel con
    # tecnologia="CdTe" -- reutiliza el mismo c_Rsh=5.5 que Poli-Si ya tenía
    # asignado, aislando el efecto SOLO al cambio de modelo de Rsh.
    panel_pre_fix = dict(XTP_50_17B, tecnologia="CdTe")
    pmax_pre_fix = func(G_PRUEBA, T_arr, panel_pre_fix)

    # A G bajas/medias (donde el modelo exponencial diverge más del estándar)
    # el resultado corregido debe ser estrictamente menor o igual.
    assert np.all(pmax_corregido <= pmax_pre_fix + 1e-9), (
        f"{nombre_func}: el fix debería reducir Pmax a baja/media irradiancia "
        "para silicio, no aumentarlo"
    )
    # Y la diferencia debe ser real, no numéricamente insignificante, en al
    # menos un punto de la malla de irradiancia probada.
    assert np.any(pmax_pre_fix - pmax_corregido > 0.01)
