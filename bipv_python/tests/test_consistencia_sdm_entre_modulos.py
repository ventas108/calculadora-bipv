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


def test_pmax_identico_entre_modelo_iv_produccion_produccion_iv_y_bypass():
    pmax_modelo_iv = np.array([
        resolver_curva_iv(float(g), T_PRUEBA, ASP_ST1_T40, n_puntos=0)["Pmax"]
        for g in G_PRUEBA
    ])
    pmax_produccion    = _calcular_pmax_vectorizado(G_PRUEBA, np.full_like(G_PRUEBA, T_PRUEBA), ASP_ST1_T40)
    pmax_produccion_iv = _pmp_iv_vectorizado(G_PRUEBA, np.full_like(G_PRUEBA, T_PRUEBA), ASP_ST1_T40)
    pmax_bypass, _, _, _ = _sdm_vectorizado(G_PRUEBA, np.full_like(G_PRUEBA, T_PRUEBA), ASP_ST1_T40)

    np.testing.assert_allclose(pmax_produccion, pmax_modelo_iv, rtol=1e-6,
                               err_msg="produccion.py diverge de modelo_iv.py")
    np.testing.assert_allclose(pmax_produccion_iv, pmax_modelo_iv, rtol=1e-6,
                               err_msg="produccion_iv.py diverge de modelo_iv.py")
    np.testing.assert_allclose(pmax_bypass, pmax_modelo_iv, rtol=1e-6,
                               err_msg="mismatch_bypass.py diverge de modelo_iv.py")


def test_parametros_sdm_identicos_entre_modelo_iv_y_mppt_combinado():
    # _params_grupo() con N_serie=1, N_paralelo=1 debe reducirse EXACTO a
    # los parámetros de un solo módulo (sin escalar) -- mismos que
    # trasladar_parametros_gt() para el mismo G/T/panel.
    for g in G_PRUEBA:
        I_L_ref, I_o_ref, R_s_ref, R_sh_ref, nNsVth_ref = trasladar_parametros_gt(
            float(g), T_PRUEBA, ASP_ST1_T40)
        I_L_g, I_o_g, R_s_g, R_sh_g, nNsVth_g = _params_grupo(
            np.array([g]), np.array([T_PRUEBA]), ASP_ST1_T40, n_serie=1, n_paralelo=1)

        assert I_L_g[0]    == pytest.approx(I_L_ref, rel=1e-6)
        assert I_o_g[0]    == pytest.approx(I_o_ref, rel=1e-6)
        assert R_s_g[0]    == pytest.approx(R_s_ref, rel=1e-6)
        assert R_sh_g[0]   == pytest.approx(R_sh_ref, rel=1e-6)
        assert nNsVth_g[0] == pytest.approx(nNsVth_ref, rel=1e-6)


def test_rsh_identico_entre_las_5_implementaciones_a_traves_de_calcular_rsh_cdte():
    # Salvaguarda directa contra el bug original: las 5 implementaciones
    # ahora llaman a la MISMA función -- este test falla de inmediato si
    # alguna vuelve a traer su propia copia de la fórmula.
    import inspect

    import calculos.produccion as produccion
    import calculos.produccion_iv as produccion_iv
    import calculos.mismatch_bypass as mismatch_bypass
    import calculos.mppt_combinado as mppt_combinado

    for modulo in (produccion, produccion_iv, mismatch_bypass, mppt_combinado):
        assert modulo.calcular_rsh_cdte is not None
        fuente = inspect.getsource(modulo)
        # No debe existir una fórmula de Rsh escrita a mano en el módulo --
        # solo la llamada a la función compartida.
        assert "np.exp(-constantes" not in fuente, (
            f"{modulo.__name__} parece tener su propia fórmula de Rsh en vez de "
            "llamar a calcular_rsh_cdte() -- eso es exactamente el bug original."
        )
