# -*- coding: utf-8 -*-
"""Consistencia cruzada del SDM entre sus 5 implementaciones (2026-08-25).

Hallazgo de la auditoría del 25-ago-2026 (PR #38): el modelo Rsh exponencial
NO vivía en un solo lugar -- estaba copiado y pegado en calculos/modelo_iv.py,
produccion.py, produccion_iv.py, mismatch_bypass.py y mppt_combinado.py, y
las 5 copias tenían el MISMO bug (Rsh sin saturar). Se corrigió centralizando
la fórmula en calculos.modelo_iv.calcular_rsh_cdte() y haciendo que las otras
4 la llamen en vez de reimplementarla.

Este archivo es la salvaguarda para que esa clase de bug -- "una fórmula
física se corrige en un lugar pero no en sus copias" -- no pueda volver a
colarse en silencio: verifica que, para el MISMO panel/irradiancia/
temperatura, las 5 implementaciones den el MISMO resultado dentro de una
tolerancia numérica estrecha (no de calibración -- todas deberían coincidir
casi al bit, porque usan pvlib.pvsystem.singlediode(method='lambertw') con
los mismos parámetros derivados). Si en el futuro alguien cambia una de las
5 sin actualizar las demás, este test lo revienta de inmediato.

Extendido el 1-sep-2026 con XTP_50_17B (Poli-Si): el mismo modelo Rsh
exponencial CdTe se aplicaba SIN filtrar tecnología en las 5 implementaciones
-- bug real encontrado comparando contra PVsyst con este panel real (base de
datos original de PVsyst, verificado con un reporte real de simulación). El
panel CdTe (ASP_ST1_T40) sigue debiendo dar el mismo resultado exacto que
antes (el modelo exponencial SÍ le corresponde); el de silicio ahora debe
usar el Rsh estándar de pvlib en las 5 implementaciones por igual.
"""
import numpy as np
import pytest

from calculos.modelo_iv import resolver_curva_iv, trasladar_parametros_gt
from calculos.produccion import _calcular_pmax_vectorizado
from calculos.produccion_iv import _pmp_iv_vectorizado
from calculos.mismatch_bypass import _sdm_vectorizado
from calculos.mppt_combinado import _params_grupo
from datos.tecnologias_bipv import ASP_ST1_T40

# G >= 5 W/m² para evitar la zona de apagado nocturno (cada módulo la trata
# un poco distinto: <5 → 0 exacto), y una mezcla de irradiancias baja/media/
# alta/STC para cubrir el rango completo de la curva de Rsh saturada.
G_PRUEBA = np.array([50.0, 100.0, 300.0, 700.0, 1000.0])
T_PRUEBA = 25.0   # todas las funciones vectorizadas usan T uniforme aquí

# XTP 50-17B (Sun Tech Solar, Si-poly) -- panel REAL de la base de datos
# original de PVsyst, extraído de un reporte de simulación real corrido por
# el usuario (1-sep-2026). Parámetros SDM: mismo ajuste Batzelis on-demand
# que usa calculos.modelo_iv.estimar_sdm_desde_ficha() para cualquier panel
# real del catálogo Excel sin SDM precalibrado.
XTP_50_17B = {
    "nombre": "XTP 50-17B", "fabricante": "Sun Tech Solar", "tecnologia": "Poli-Si",
    "Voc_stc": 21.50, "Isc_stc": 3.300, "Vmp_stc": 17.30, "Imp_stc": 2.850,
    "Pmax_stc": 50.0, "Tk_beta": -0.34, "Tk_alfa": 0.04, "Tk_gamma": -0.45,
    "I_L_ref": 3.3280621683489193, "I_o_ref": 5.5322736788824886e-11,
    "R_s": 0.5247000612677759, "R_sh_ref": 61.70265179277618,
    "a_ref": 33.71514270005188, "N_s": 36, "gamma_ref": 33.71514270005188/36,
    "NOCT": 45.0,
}

_PANELES_PRUEBA = {"CdTe (ASP_ST1_T40)": ASP_ST1_T40, "Poli-Si (XTP_50_17B)": XTP_50_17B}


@pytest.mark.parametrize("nombre_panel,panel", _PANELES_PRUEBA.items())
def test_pmax_identico_entre_modelo_iv_produccion_produccion_iv_y_bypass(nombre_panel, panel):
    pmax_modelo_iv = np.array([
        resolver_curva_iv(float(g), T_PRUEBA, panel, n_puntos=0)["Pmax"]
        for g in G_PRUEBA
    ])
    pmax_produccion    = _calcular_pmax_vectorizado(G_PRUEBA, np.full_like(G_PRUEBA, T_PRUEBA), panel)
    pmax_produccion_iv = _pmp_iv_vectorizado(G_PRUEBA, np.full_like(G_PRUEBA, T_PRUEBA), panel)
    pmax_bypass, _, _, _ = _sdm_vectorizado(G_PRUEBA, np.full_like(G_PRUEBA, T_PRUEBA), panel)

    np.testing.assert_allclose(pmax_produccion, pmax_modelo_iv, rtol=1e-6,
                               err_msg=f"produccion.py diverge de modelo_iv.py ({nombre_panel})")
    np.testing.assert_allclose(pmax_produccion_iv, pmax_modelo_iv, rtol=1e-6,
                               err_msg=f"produccion_iv.py diverge de modelo_iv.py ({nombre_panel})")
    np.testing.assert_allclose(pmax_bypass, pmax_modelo_iv, rtol=1e-6,
                               err_msg=f"mismatch_bypass.py diverge de modelo_iv.py ({nombre_panel})")


@pytest.mark.parametrize("nombre_panel,panel", _PANELES_PRUEBA.items())
def test_parametros_sdm_identicos_entre_modelo_iv_y_mppt_combinado(nombre_panel, panel):
    # _params_grupo() con N_serie=1, N_paralelo=1 debe reducirse EXACTO a
    # los parámetros de un solo módulo (sin escalar) -- mismos que
    # trasladar_parametros_gt() para el mismo G/T/panel.
    for g in G_PRUEBA:
        I_L_ref, I_o_ref, R_s_ref, R_sh_ref, nNsVth_ref = trasladar_parametros_gt(
            float(g), T_PRUEBA, panel)
        I_L_g, I_o_g, R_s_g, R_sh_g, nNsVth_g = _params_grupo(
            np.array([g]), np.array([T_PRUEBA]), panel, n_serie=1, n_paralelo=1)

        assert I_L_g[0]    == pytest.approx(I_L_ref, rel=1e-6), nombre_panel
        assert I_o_g[0]    == pytest.approx(I_o_ref, rel=1e-6), nombre_panel
        assert R_s_g[0]    == pytest.approx(R_s_ref, rel=1e-6), nombre_panel
        assert R_sh_g[0]   == pytest.approx(R_sh_ref, rel=1e-6), nombre_panel
        assert nNsVth_g[0] == pytest.approx(nNsVth_ref, rel=1e-6), nombre_panel


def test_las_5_implementaciones_centralizan_en_trasladar_parametros_gt():
    # Salvaguarda directa contra el bug original ("una fórmula física se
    # corrige en un lugar pero no en sus copias"): desde la migración al
    # motor PVsyst v6 (2-sep-2026, ver DIAGNOSTICO_MOTOR_PVSYST.md), las 4
    # implementaciones fuera de modelo_iv.py NO reimplementan la llamada a
    # calcparams_pvsyst -- todas llaman directo a
    # calculos.modelo_iv.trasladar_parametros_gt(). Este test falla de
    # inmediato si alguna vuelve a traer su propia copia de la fórmula.
    import inspect

    import calculos.produccion as produccion
    import calculos.produccion_iv as produccion_iv
    import calculos.mismatch_bypass as mismatch_bypass
    import calculos.mppt_combinado as mppt_combinado

    for modulo in (produccion, produccion_iv, mismatch_bypass, mppt_combinado):
        assert modulo.trasladar_parametros_gt is not None
        fuente = inspect.getsource(modulo)
        assert "calcparams_pvsyst" not in fuente, (
            f"{modulo.__name__} parece llamar a calcparams_pvsyst() por su "
            "cuenta en vez de usar trasladar_parametros_gt() -- eso es "
            "exactamente el bug original (fórmula duplicada en 5 lugares)."
        )
        assert "calcparams_desoto" not in fuente, (
            f"{modulo.__name__} todavía usa el motor De Soto 2006 -- "
            "debería centralizar en trasladar_parametros_gt() (PVsyst v6)."
        )
