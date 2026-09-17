# -*- coding: utf-8 -*-
"""Regresión térmica de simular_bypass_horario() (mismatch_bypass.py).

Contexto del bug (diagnóstico 17-sep-2026, ver /tmp/diagnostico_motor_optico.txt):
cuando el Motor Óptico estaba activo, la página Mismatch pasaba
poa_efectiva_df (POA YA con el factor térmico multiplicativo f_term
aplicado) como G_eff a simular_bypass_horario(), y esta a su vez calculaba
T_cel con una fórmula local que NO recibía k_BIPV. Producción, en cambio,
usa poa_sin_termico_df (sin f_term) + temperatura_celda_noct(..., k_bipv=...)
-- dos referencias térmicas distintas para el mismo array físico, que
producían una energía DC/pérdida de bypass no comparable entre páginas
(~12-13% de sesgo en el caso sintético del diagnóstico).

El fix centraliza el cálculo de T_cel en calculos.temperatura.temperatura_celda_noct()
y hace que simular_bypass_horario() acepte k_bipv (default 1.0 = comportamiento
legado / ventilado libre). Este archivo es la salvaguarda para que:
  1) T_cel interno de simular_bypass_horario() nunca vuelva a divergir de
     temperatura_celda_noct() (fuente única de verdad).
  2) Pasar poa_efectiva_df (con f_term ya aplicado) en vez de poa_sin_termico_df
     siga produciendo un resultado MEDIBLEMENTE distinto -- si algún día ambos
     caminos dieran "casualmente" el mismo número, este test lo detectaría
     como ausencia de la diferencia esperada, señal de que el bug volvió.
  3) El comportamiento legado (sin Motor Óptico, k_bipv=1.0 explícito o por
     default) permanezca bit-a-bit idéntico al de antes del fix.
"""
import numpy as np
import pytest

from calculos.ejecutor_escenarios import ejecutar_escenarios
from calculos.escenarios_fase4 import capturar_base_comparacion
from calculos.mismatch_bypass import _sdm_vectorizado, simular_bypass_horario
from calculos.motor_optico import factor_termico_bipv
from calculos.temperatura import temperatura_celda_noct
from datos.tecnologias_bipv import ASP_ST1_T40
from tests.test_ejecutor_escenarios import (
    _PANEL_SDM,
    _definicion_con_base,
    _df_fs,
    _estado_con_panel_sdm,
    _poa_diurna,
)

# ── Datos sintéticos deterministas (mismos que el diagnóstico dirigido) ──────
# Mediodía cálido de fachada BIPV: irradiancia creciente + temperatura ambiente
# creciente, para que el efecto térmico (y su eventual duplicación) sea visible.
G_SIN_TERMICO = np.array([200.0, 400.0, 600.0, 800.0, 900.0])   # W/m² -- poa_sin_termico_df
T_AMB         = np.array([25.0,  27.0,  30.0,  32.0,  33.0])    # °C
P_SHADE       = np.array([0.30,  0.30,  0.30,  0.30,  0.30])    # 30% de módulos sombreados/hora

PANEL     = ASP_ST1_T40
NOCT      = float(PANEL["NOCT"])
K_BIPV    = 1.3       # "Fachada confinada" -- default típico Motor Óptico
COEF_TEMP = -0.0045   # default de factor_termico_bipv / cascada_optica

N_SERIES, N_PARALLEL = 8, 1


def _poa_efectiva_desde_sin_termico(g_sin_termico, t_amb, k_bipv):
    """Reproduce cascada_optica(): poa_efectiva = poa_sin_termico × f_term."""
    f_term = factor_termico_bipv(
        g_sin_termico, t_amb, noct=NOCT, coef_temp=COEF_TEMP, k_bipv=k_bipv
    )
    return np.maximum(g_sin_termico * f_term, 0.0)


# ══════════════════════════════════════════════════════════════════════════
# 1) T_cel de simular_bypass_horario() == temperatura_celda_noct() (fuente única)
# ══════════════════════════════════════════════════════════════════════════
def test_t_cel_bypass_coincide_con_temperatura_celda_noct():
    p_shade_cero = np.zeros_like(G_SIN_TERMICO)  # sin sombra → sin bypass activo

    res = simular_bypass_horario(
        G_eff=G_SIN_TERMICO, T_amb=T_AMB, p_shade=p_shade_cero,
        N_series=1, N_parallel=1, panel=PANEL, NOCT=NOCT, k_bipv=K_BIPV,
    )

    # Réplica independiente: T_cel con la MISMA función de referencia que usa
    # Producción, y Pmp con el mismo SDM vectorizado que usa internamente
    # simular_bypass_horario().
    T_cel_esperado = temperatura_celda_noct(G_SIN_TERMICO, T_AMB, NOCT=NOCT, k_bipv=K_BIPV)
    Pmp_esperado, _, _, _ = _sdm_vectorizado(G_SIN_TERMICO, T_cel_esperado, PANEL)

    # Sin sombra, P_dc_uniforme_kW == P_dc_kW == Pmp_esperado/1000 (N_series=N_parallel=1)
    np.testing.assert_allclose(
        res["P_dc_uniforme_kW"], Pmp_esperado / 1000.0, rtol=1e-9,
        err_msg="T_cel interno de simular_bypass_horario() diverge de "
                "temperatura_celda_noct() -- ya no comparten fuente única de verdad.",
    )
    np.testing.assert_allclose(
        res["P_dc_kW"], Pmp_esperado / 1000.0, rtol=1e-9,
        err_msg="Sin sombra activa, P_dc_kW debe ser idéntico a la potencia "
                "uniforme calculada con temperatura_celda_noct().",
    )


# ══════════════════════════════════════════════════════════════════════════
# 2) El flujo corregido (G_eff=poa_sin_termico) difiere del flujo incorrecto
#    (G_eff=poa_efectiva, con f_term ya aplicado) -- el bug de doble conteo
#    térmico debe seguir siendo detectable si alguien reintroduce
#    poa_efectiva_df como entrada.
# ══════════════════════════════════════════════════════════════════════════
def test_flujo_corregido_difiere_del_flujo_incorrecto_con_poa_efectiva():
    poa_efectiva = _poa_efectiva_desde_sin_termico(G_SIN_TERMICO, T_AMB, K_BIPV)

    # poa_efectiva debe ser estrictamente menor que poa_sin_termico (f_term < 1
    # en este rango de irradiancia/temperatura) -- si no, el fixture ya no
    # ejercita el escenario del bug.
    assert np.all(poa_efectiva < G_SIN_TERMICO), (
        "El fixture sintético dejó de representar un f_term < 1; revisar "
        "COEF_TEMP/K_BIPV/T_AMB del test."
    )

    res_corregido = simular_bypass_horario(
        G_eff=G_SIN_TERMICO, T_amb=T_AMB, p_shade=P_SHADE,
        N_series=N_SERIES, N_parallel=N_PARALLEL, panel=PANEL,
        NOCT=NOCT, k_bipv=K_BIPV,
    )
    res_incorrecto = simular_bypass_horario(
        G_eff=poa_efectiva, T_amb=T_AMB, p_shade=P_SHADE,
        N_series=N_SERIES, N_parallel=N_PARALLEL, panel=PANEL,
        NOCT=NOCT, k_bipv=K_BIPV,
    )

    kwh_bypass_corregido  = float(res_corregido["P_bypass_loss_kW"].sum())
    kwh_bypass_incorrecto = float(res_incorrecto["P_bypass_loss_kW"].sum())
    e_dc_uniforme_corregido  = float(res_corregido["P_dc_uniforme_kW"].sum())
    e_dc_uniforme_incorrecto = float(res_incorrecto["P_dc_uniforme_kW"].sum())

    # Umbral de 5%: muy por debajo de la brecha real observada en el
    # diagnóstico (~12-13%), para no ser frágil ante cambios menores de
    # calibración del panel, pero suficiente para detectar que el doble
    # conteo térmico volvió a colarse.
    diff_pct_uniforme = abs(e_dc_uniforme_corregido - e_dc_uniforme_incorrecto) / e_dc_uniforme_corregido * 100
    diff_pct_bypass = abs(kwh_bypass_corregido - kwh_bypass_incorrecto) / kwh_bypass_corregido * 100

    assert diff_pct_uniforme > 5.0, (
        f"La energía DC uniforme apenas difiere ({diff_pct_uniforme:.2f}%) entre "
        "G_eff=poa_sin_termico y G_eff=poa_efectiva -- el doble conteo térmico "
        "ya no es detectable con este fixture; confirmar que el bug no reapareció "
        "de otra forma antes de relajar este umbral."
    )
    assert diff_pct_bypass > 5.0, (
        f"kwh_bypass_anual apenas difiere ({diff_pct_bypass:.2f}%) entre los dos "
        "caminos de G_eff -- revisar si el doble conteo térmico reapareció."
    )
    # La energía uniforme con poa_efectiva (ya derateada por f_term Y por el
    # propio SDM vía T_cel) debe quedar por DEBAJO de la calculada con
    # poa_sin_termico -- ese es el signo físico del doble conteo.
    assert e_dc_uniforme_incorrecto < e_dc_uniforme_corregido


# ══════════════════════════════════════════════════════════════════════════
# 3) Comportamiento legado (sin Motor Óptico -> k_bipv=1.0, explícito o por
#    default) permanece exactamente igual al de antes del fix.
# ══════════════════════════════════════════════════════════════════════════
def test_comportamiento_legado_sin_motor_optico_k_bipv_uno_es_compatible():
    # Fórmula pre-fix, tal como vivía en mismatch_bypass.py:142 antes del
    # cambio: T_cel = T_amb + (NOCT-20)/800 * G_eff (sin factor k_BIPV, es
    # decir, equivalente a k_bipv=1.0).
    T_cel_legado = T_AMB + (NOCT - 20.0) / 800.0 * G_SIN_TERMICO
    Pmp_legado, _, _, _ = _sdm_vectorizado(G_SIN_TERMICO, T_cel_legado, PANEL)

    p_shade_cero = np.zeros_like(G_SIN_TERMICO)

    # (a) sin pasar k_bipv -> debe usar el default 1.0
    res_default = simular_bypass_horario(
        G_eff=G_SIN_TERMICO, T_amb=T_AMB, p_shade=p_shade_cero,
        N_series=1, N_parallel=1, panel=PANEL, NOCT=NOCT,
    )
    # (b) pasando k_bipv=1.0 explícito -> debe dar exactamente lo mismo
    res_explicito = simular_bypass_horario(
        G_eff=G_SIN_TERMICO, T_amb=T_AMB, p_shade=p_shade_cero,
        N_series=1, N_parallel=1, panel=PANEL, NOCT=NOCT, k_bipv=1.0,
    )

    np.testing.assert_allclose(
        res_default["P_dc_uniforme_kW"], Pmp_legado / 1000.0, rtol=1e-9,
        err_msg="El default k_bipv=1.0 ya no reproduce el comportamiento "
                "legado (pre-fix) de simular_bypass_horario().",
    )
    np.testing.assert_allclose(
        res_default["P_dc_uniforme_kW"], res_explicito["P_dc_uniforme_kW"], rtol=1e-12,
        err_msg="k_bipv por default y k_bipv=1.0 explícito deben ser idénticos.",
    )

    # También debe coincidir con simular con sombra activa (P_SHADE real):
    # esto cubre el default k_bipv=1.0 de cualquier llamador que no lo pase
    # explícitamente (p. ej. ejecutor_escenarios.py cuando su propio
    # parámetro k_bipv tampoco se especifica -- ver tests siguientes).
    res_con_sombra = simular_bypass_horario(
        G_eff=G_SIN_TERMICO, T_amb=T_AMB, p_shade=P_SHADE,
        N_series=N_SERIES, N_parallel=N_PARALLEL, panel=PANEL, NOCT=NOCT,
    )
    assert res_con_sombra["kwh_bypass_anual"] >= 0.0
    assert res_con_sombra["horas_sombra"] == int((P_SHADE > 0.05).sum())


# ══════════════════════════════════════════════════════════════════════════
# 4) ejecutor_escenarios.ejecutar_escenarios() propaga k_bipv hasta
#    simular_bypass_horario() y, por tanto, hasta temperatura_celda_noct().
#    (brecha residual detectada en el diagnóstico de la sesión anterior:
#    el G_eff ya llegaba corregido vía poa_bp, pero k_bipv se perdía porque
#    ejecutar_escenarios()/_simular_escenario() no lo aceptaban).
# ══════════════════════════════════════════════════════════════════════════
def test_ejecutar_escenarios_propaga_k_bipv_a_temperatura_celda_noct():
    state = _estado_con_panel_sdm()
    definicion = _definicion_con_base(state)
    poa = _poa_diurna(state["tmy_df"].index)
    t_amb = state["tmy_df"]["T2m"].to_numpy(dtype=float)
    n_serie = state["N_serie"]
    n_paralelo = state["N_paneles_dim"] // state["N_serie"]

    resultados = ejecutar_escenarios(
        definicion=definicion,
        base_estado_actual=capturar_base_comparacion(state),
        tmy=state["tmy_df"],
        poa_global=poa,
        panel=state["panel_dict"],
        n_serie=n_serie,
        n_paralelo=n_paralelo,
        eta_inversor=state["eta_inversor"],
        df_fs_actual=_df_fs(0.5),
        k_bipv=K_BIPV,
    )

    # La "referencia" fuerza p_shade=0 en todo el año -> sin bypass activo ->
    # E_DC_anual_kWh debe ser EXACTAMENTE la potencia uniforme del SDM con el
    # T_cel que produce temperatura_celda_noct() para el mismo k_bipv.
    T_cel_esperado = temperatura_celda_noct(poa, t_amb, NOCT=float(_PANEL_SDM["NOCT"]), k_bipv=K_BIPV)
    Pmp_esperado, _, _, _ = _sdm_vectorizado(poa, T_cel_esperado, state["panel_dict"])
    e_dc_esperado_kwh = float(np.sum(Pmp_esperado)) * n_serie * n_paralelo / 1000.0
    e_ac_esperado_kwh = e_dc_esperado_kwh * state["eta_inversor"]

    ref = resultados["referencia"]
    assert ref["E_DC_anual_kWh"] == pytest.approx(e_dc_esperado_kwh, abs=0.1)
    assert ref["E_AC_anual_kWh"] == pytest.approx(e_ac_esperado_kwh, abs=0.1)

    # Con un k_bipv distinto (1.0, ventilado libre) el resultado debe DIFERIR
    # -- confirma que el parámetro realmente participa en el cálculo y no se
    # queda ignorado en el camino desde ejecutar_escenarios() hasta el SDM.
    resultados_k1 = ejecutar_escenarios(
        definicion=definicion,
        base_estado_actual=capturar_base_comparacion(state),
        tmy=state["tmy_df"],
        poa_global=poa,
        panel=state["panel_dict"],
        n_serie=n_serie,
        n_paralelo=n_paralelo,
        eta_inversor=state["eta_inversor"],
        df_fs_actual=_df_fs(0.5),
        k_bipv=1.0,
    )
    assert resultados_k1["referencia"]["E_DC_anual_kWh"] != ref["E_DC_anual_kWh"]


def test_ejecutar_escenarios_sin_k_bipv_usa_default_uno_compatibilidad():
    """Compatibilidad: no pasar k_bipv a ejecutar_escenarios() debe dar
    exactamente el mismo resultado que pasarlo explícito en 1.0 -- ningún
    llamador existente (p. ej. la sección Fase 4 de Mismatch antes de este
    cambio) queda roto por el nuevo parámetro."""
    state = _estado_con_panel_sdm()
    definicion = _definicion_con_base(state)
    poa = _poa_diurna(state["tmy_df"].index)
    n_serie = state["N_serie"]
    n_paralelo = state["N_paneles_dim"] // state["N_serie"]

    comunes = dict(
        definicion=definicion,
        base_estado_actual=capturar_base_comparacion(state),
        tmy=state["tmy_df"],
        poa_global=poa,
        panel=state["panel_dict"],
        n_serie=n_serie,
        n_paralelo=n_paralelo,
        eta_inversor=state["eta_inversor"],
        df_fs_actual=_df_fs(0.5),
    )

    resultado_sin_k_bipv = ejecutar_escenarios(**comunes)
    resultado_k_bipv_uno = ejecutar_escenarios(**comunes, k_bipv=1.0)

    assert resultado_sin_k_bipv == resultado_k_bipv_uno


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
