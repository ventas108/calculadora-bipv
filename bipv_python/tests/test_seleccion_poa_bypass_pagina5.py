# -*- coding: utf-8 -*-
"""Regresión: selección de POA (G_eff) para el bypass en Página 5 Mismatch.

Contexto (auditoría 17-sep-2026): Página 5 usaba poa_sin_termico_df cuando
estaba disponible, pero si motor_optico_ok=True y poa_sin_termico_df faltaba
(estado inconsistente -- normalmente ambos se escriben/invalidan juntos, ver
calculos/invalidacion.py::KEYS_DERIVADOS_POA), caía en silencio a
poa_efectiva_df. poa_efectiva_df YA incluye el factor térmico, y
simular_bypass_horario() vuelve a calcular T_cel con NOCT + k_BIPV -- ese
fallback duplicaba la corrección térmica sin ningún aviso.

test_mismatch_bypass_termico.py ya cubre el motor (simular_bypass_horario) y
los escenarios (ejecutor_escenarios); este archivo cubre específicamente la
función calculos.mismatch_bypass.seleccionar_poa_bypass(), que es la lógica
de selección extraída de pages/5_🔀_Mismatch.py para poder testearla sin
Streamlit (separación cálculo/presentación).
"""
import inspect
import os
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from calculos.invalidacion import (
    KEYS_BYPASS_MULTISUP_RESULTADO,
    KEYS_BYPASS_RESULTADO,
    KEYS_DERIVADOS_POA,
    KEYS_DOWNSTREAM_MOTOR_OPTICO,
    KEYS_MULTISUP_ESTADO,
    invalidar_downstream_motor_optico,
)
from calculos.mismatch_bypass import (
    exigir_poa_sin_termico,
    invalidar_resultados_bypass,
    resolver_poa_bypass,
    seleccionar_poa_bypass,
)

IDX = pd.date_range("2001-01-01", periods=5, freq="h", tz="UTC")

POA_SIN_TERMICO = pd.DataFrame({"poa_global": [200.0, 400.0, 600.0, 800.0, 900.0]}, index=IDX)
# poa_efectiva simula la serie CON térmico ya aplicado (siempre <= sin_termico)
POA_EFECTIVA = pd.DataFrame({"poa_global": [180.0, 360.0, 540.0, 720.0, 810.0]}, index=IDX)
POA_BRUTA = pd.DataFrame({"poa_global": [250.0, 450.0, 650.0, 850.0, 950.0]}, index=IDX)

K_BIPV_MOTOR = 1.3
FACTOR_MISMATCH = 0.9


# ══════════════════════════════════════════════════════════════════════════
# 1) Motor Óptico activo + poa_sin_termico_df disponible → debe usarla
# ══════════════════════════════════════════════════════════════════════════
def test_motor_activo_con_poa_sin_termico_disponible():
    g_eff, fuente, k_bipv = seleccionar_poa_bypass(
        motor_optico_ok=True,
        poa_sin_termico_df=POA_SIN_TERMICO,
        poa_df=POA_BRUTA,
        factor_global_mismatch=FACTOR_MISMATCH,
        motor_optico_k_bipv=K_BIPV_MOTOR,
    )
    np.testing.assert_allclose(g_eff, POA_SIN_TERMICO["poa_global"].values)
    assert "sin térmico" in fuente.lower()
    assert "⛔" not in fuente
    assert k_bipv == pytest.approx(K_BIPV_MOTOR)


# ══════════════════════════════════════════════════════════════════════════
# 2) Motor Óptico activo SIN poa_sin_termico_df → debe bloquear (G_eff=None),
#    nunca usar poa_efectiva_df como sustituto silencioso.
# ══════════════════════════════════════════════════════════════════════════
def test_motor_activo_sin_poa_sin_termico_bloquea():
    g_eff, fuente, k_bipv = seleccionar_poa_bypass(
        motor_optico_ok=True,
        poa_sin_termico_df=None,
        poa_df=POA_BRUTA,
        factor_global_mismatch=FACTOR_MISMATCH,
        motor_optico_k_bipv=K_BIPV_MOTOR,
    )
    assert g_eff is None, (
        "Con motor_optico_ok=True y poa_sin_termico_df=None, G_eff debe ser "
        "None (bloqueo explícito) -- nunca un array que reintroduzca en "
        "silencio la corrección térmica."
    )
    assert "⛔" in fuente
    assert "poa_sin_termico_df" in fuente
    # k_bipv se conserva incluso en el caso bloqueado: si el llamador decide
    # ignorar el bloqueo, no debe además perder la fuente de k_BIPV.
    assert k_bipv == pytest.approx(K_BIPV_MOTOR)


# ══════════════════════════════════════════════════════════════════════════
# 3) Motor Óptico desactivado → POA bruta × factor_global_mismatch, k_bipv=1.0
# ══════════════════════════════════════════════════════════════════════════
def test_motor_desactivado_usa_poa_bruta_por_factor():
    g_eff, fuente, k_bipv = seleccionar_poa_bypass(
        motor_optico_ok=False,
        poa_sin_termico_df=POA_SIN_TERMICO,  # presente pero irrelevante: motor OFF
        poa_df=POA_BRUTA,
        factor_global_mismatch=FACTOR_MISMATCH,
        motor_optico_k_bipv=K_BIPV_MOTOR,    # presente pero irrelevante: motor OFF
    )
    np.testing.assert_allclose(
        g_eff, POA_BRUTA["poa_global"].values * FACTOR_MISMATCH,
    )
    assert "bruta" in fuente.lower()
    assert k_bipv == pytest.approx(1.0), (
        "Sin Motor Óptico, k_bipv debe ser 1.0 (ventilado libre) -- "
        "comportamiento legado, no el motor_optico_k_bipv de sesión."
    )


# ══════════════════════════════════════════════════════════════════════════
# 4) Imposibilidad estructural de usar poa_efectiva_df como G_eff en
#    silencio: la firma de la función no acepta esa serie en absoluto, y el
#    caso bloqueado (test 2) nunca devuelve un array numéricamente igual a
#    poa_efectiva.
# ══════════════════════════════════════════════════════════════════════════
def test_no_existe_via_silenciosa_hacia_poa_efectiva():
    parametros = set(inspect.signature(seleccionar_poa_bypass).parameters)
    assert "poa_efectiva_df" not in parametros, (
        "seleccionar_poa_bypass() no debe aceptar poa_efectiva_df -- si algún "
        "día se necesita, debe ser explícito y documentado en la firma, no un "
        "fallback implícito interno."
    )

    g_eff_bloqueado, _, _ = seleccionar_poa_bypass(
        motor_optico_ok=True,
        poa_sin_termico_df=None,
        poa_df=POA_BRUTA,
        factor_global_mismatch=FACTOR_MISMATCH,
        motor_optico_k_bipv=K_BIPV_MOTOR,
    )
    assert g_eff_bloqueado is None
    # Si por error se reintrodujera el fallback, g_eff_bloqueado sería un
    # array igual a POA_EFECTIVA -- lo dejamos explícito para que el diff de
    # un futuro cambio sea imposible de pasar por alto.
    assert not (
        isinstance(g_eff_bloqueado, np.ndarray)
        and np.allclose(g_eff_bloqueado, POA_EFECTIVA["poa_global"].values)
    )


# ══════════════════════════════════════════════════════════════════════════
# 5) Conservación de k_bipv: motor_optico_k_bipv de sesión llega intacto
#    hasta el resultado cuando el motor está activo (con o sin
#    poa_sin_termico_df), y nunca se usa cuando el motor está desactivado.
# ══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("k_bipv_sesion", [1.0, 1.3, 1.5])
def test_conservacion_k_bipv_con_motor_activo(k_bipv_sesion):
    _, _, k_bipv_out = seleccionar_poa_bypass(
        motor_optico_ok=True,
        poa_sin_termico_df=POA_SIN_TERMICO,
        poa_df=POA_BRUTA,
        factor_global_mismatch=FACTOR_MISMATCH,
        motor_optico_k_bipv=k_bipv_sesion,
    )
    assert k_bipv_out == pytest.approx(k_bipv_sesion)


def test_k_bipv_default_uno_si_no_se_pasa_explicito():
    # motor_optico_k_bipv tiene default 1.0 en la firma -- refleja el default
    # histórico de session_state.get("motor_optico_k_bipv", 1.0) en la página.
    g_eff, _, k_bipv_out = seleccionar_poa_bypass(
        motor_optico_ok=True,
        poa_sin_termico_df=POA_SIN_TERMICO,
        poa_df=POA_BRUTA,
        factor_global_mismatch=FACTOR_MISMATCH,
    )
    assert k_bipv_out == pytest.approx(1.0)
    assert g_eff is not None


# ══════════════════════════════════════════════════════════════════════════
# 6) Salvaguarda de fuente única: la página ya no debe contener el patrón
#    peligroso `st.session_state["poa_efectiva_df"]` como valor de poa_bp.
#    Esto detecta si alguien reintroduce el fallback directamente en la
#    página en vez de usar seleccionar_poa_bypass().
# ══════════════════════════════════════════════════════════════════════════
def test_pagina_mismatch_no_usa_poa_efectiva_df_como_poa_bp():
    ruta = os.path.join(
        os.path.dirname(__file__), "..", "pages", "5_🔀_Mismatch.py",
    )
    with open(ruta, "r", encoding="utf-8") as f:
        src = f.read()
    assert "resolver_poa_bypass" in src, (
        "Página 5 debe delegar selección + invalidación de POA del bypass a "
        "calculos.mismatch_bypass.resolver_poa_bypass() (que a su vez usa "
        "seleccionar_poa_bypass() e invalidar_resultados_bypass())."
    )
    assert 'poa_bp = st.session_state["poa_efectiva_df"]' not in src, (
        "Reapareció el fallback silencioso a poa_efectiva_df como G_eff del "
        "bypass -- duplica la corrección térmica cuando falta "
        "poa_sin_termico_df con el Motor Óptico activo."
    )


# ══════════════════════════════════════════════════════════════════════════
# Regresión (ronda 2, 17-sep-2026): cuando poa_bp queda bloqueada (None), un
# bypass_result de una corrida anterior debía dejar de mostrarse/consumirse
# de inmediato -- ANTES de que `if btn_bypass or bypass_ok` pudiera volver a
# leerlo. invalidar_resultados_bypass() y resolver_poa_bypass() cierran esa
# brecha; estas pruebas cubren ambas funciones con un dict plano que simula
# session_state (sin depender de Streamlit ni de búsquedas textuales).
# ══════════════════════════════════════════════════════════════════════════

def _session_state_con_bypass_vigente() -> dict:
    """dict que simula un session_state con un bypass_result "vivo" de una
    corrida anterior, más claves no relacionadas que NUNCA deben tocarse."""
    return {
        "bypass_ok": True,
        "bypass_result": {"kwh_bypass_anual": 123.4, "horas_bypass": 42},
        "bypass_p_shade": pd.Series([0.1, 0.2, 0.3]),
        "bypass_n_series_usado": 8,
        "bypass_n_parallel_usado": 4,
        "bypass_panel_usado": "ASP-ST1-T40",
        "bypass_horizonte_info": {"horas_horizonte": 10},
        "bypass_horizonte_incluido": True,
        "bypass_modo_usado": "mensual",
        "bypass_modo_agregacion_usado": "auto",
        "E_ac_anual_kWh_bypass": 5000.0,
        "kwh_bypass_anual": 123.4,
        # ── claves NO relacionadas -- deben sobrevivir intactas ────────────
        "motor_optico_ok": True,
        "poa_sin_termico_df": None,  # justo lo que falta -- no debe tocarse
        "poa_efectiva_df": POA_EFECTIVA,
        "produccion_ok": True,
        "E_ac_anual_kWh": 9999.0,
        "nombre_proyecto": "Proyecto BIPV Bogotá Teusaquillo",
        "factor_global_mismatch": FACTOR_MISMATCH,
        "motor_optico_k_bipv": K_BIPV_MOTOR,
        # ── bypass MULTI-superficie (Página 9) -- ciclo de vida separado,
        # NUNCA debe eliminarse junto con el bypass monofacial ────────────
        "bypass_multisup_ok": True,
        "bypass_multisup_resultados": [{"fachada": "Norte", "kwh_bypass": 42.0}],
    }


# 7) bypass_ok=True + bypass_result antiguo → invalidar_resultados_bypass()
#    los deja inválidos (eliminados de session_state).
def test_invalidar_resultados_bypass_limpia_estado_con_bypass_ok_true():
    estado = _session_state_con_bypass_vigente()
    eliminadas = invalidar_resultados_bypass(estado)

    assert set(eliminadas) == set(KEYS_BYPASS_RESULTADO)
    for clave in KEYS_BYPASS_RESULTADO:
        assert clave not in estado, f"'{clave}' debió eliminarse de session_state"


# 8) Ninguna métrica anterior queda "vigente": tras invalidar, leer bypass_ok
#    / bypass_result con los defaults que usa la página da el estado "sin
#    bypass calculado", no el resultado antiguo.
def test_invalidar_resultados_bypass_ninguna_metrica_queda_vigente():
    estado = _session_state_con_bypass_vigente()
    invalidar_resultados_bypass(estado)

    assert estado.get("bypass_ok", False) is False
    assert estado.get("bypass_result", {}) == {}
    assert estado.get("kwh_bypass_anual") is None
    assert estado.get("E_ac_anual_kWh_bypass") is None


# 9) E_ac_anual_kWh_bypass y kwh_bypass_anual (los valores que Producción
#    resta de la energía anual) caducan explícitamente -- no solo bypass_ok.
def test_invalidar_resultados_bypass_incluye_energia_y_kwh_bypass():
    estado = _session_state_con_bypass_vigente()
    eliminadas = invalidar_resultados_bypass(estado)

    assert "E_ac_anual_kWh_bypass" in eliminadas
    assert "kwh_bypass_anual" in eliminadas
    assert "E_ac_anual_kWh_bypass" not in estado
    assert "kwh_bypass_anual" not in estado


# 10) Claves NO relacionadas con el bypass permanecen intactas -- en
#     particular motor_optico_ok y poa_efectiva_df, que siguen siendo
#     válidos aunque el bypass se haya bloqueado (nunca usar todo
#     KEYS_DERIVADOS_POA aquí).
def test_invalidar_resultados_bypass_no_toca_claves_no_relacionadas():
    estado = _session_state_con_bypass_vigente()
    claves_previas_no_bypass = {
        k: v for k, v in estado.items() if k not in KEYS_BYPASS_RESULTADO
    }
    invalidar_resultados_bypass(estado)

    for clave, valor in claves_previas_no_bypass.items():
        assert clave in estado, f"'{clave}' no debía eliminarse"
        if isinstance(valor, pd.Series):
            pd.testing.assert_series_equal(estado[clave], valor)
        elif isinstance(valor, pd.DataFrame):
            pd.testing.assert_frame_equal(estado[clave], valor)
        else:
            assert estado[clave] == valor

    # Salvaguarda explícita: el bypass NUNCA debe invalidarse arrastrando
    # todo KEYS_DERIVADOS_POA (borraría motor_optico_ok/summary válidos).
    assert not (set(KEYS_BYPASS_RESULTADO) >= set(KEYS_DERIVADOS_POA)), (
        "KEYS_BYPASS_RESULTADO debe seguir siendo un subconjunto ACOTADO, "
        "nunca el superconjunto completo KEYS_DERIVADOS_POA."
    )


# 11) invalidar_resultados_bypass() es idempotente sobre un estado ya
#     limpio (sin las 10 claves) -- no revienta, no elimina nada de más.
def test_invalidar_resultados_bypass_idempotente_sobre_estado_limpio():
    estado = {"motor_optico_ok": True, "nombre_proyecto": "X"}
    eliminadas = invalidar_resultados_bypass(estado)

    assert eliminadas == []
    assert estado == {"motor_optico_ok": True, "nombre_proyecto": "X"}


# 12) resolver_poa_bypass(): mientras poa_sin_termico_df esté PRESENTE
#     (no-None), resolver_poa_bypass() no invalida nada -- ese es su
#     contrato real y completo: un gate de presencia/ausencia, no de
#     identidad. CORRECCIÓN (ronda 3, 17-sep-2026): la versión anterior de
#     esta prueba afirmaba en un comentario que el bypass_result "sigue
#     siendo válido porque la POA que lo produjo no cambió" -- eso NUNCA fue
#     algo que este test pudiera demostrar, porque nunca varía la POA entre
#     el cálculo del bypass_result "vigente" y la llamada a
#     resolver_poa_bypass(): solo prueba que la MISMA constante
#     POA_SIN_TERMICO sigue presente, no que sea la que produjo el
#     resultado. resolver_poa_bypass() NO tiene forma de saber si
#     poa_sin_termico_df cambió de contenido -- esa garantía de FRESCURA
#     real la da invalidar_resultados_bypass() en el punto donde Motor
#     Óptico REEMPLAZA poa_sin_termico_df (pages/5b_🔆_Motor_Optico.py, ver
#     test_pagina_motor_optico_invalida_bypass_antes_de_publicar_poa()
#     más abajo en este archivo), no este gate de Página 5.
def test_resolver_poa_bypass_con_poa_sin_termico_presente_no_invalida():
    estado = _session_state_con_bypass_vigente()
    estado["poa_sin_termico_df"] = POA_SIN_TERMICO  # presente (no-None)

    g_eff, fuente, k_bipv, claves_invalidadas = resolver_poa_bypass(estado, POA_BRUTA)

    assert g_eff is not None
    np.testing.assert_allclose(g_eff, POA_SIN_TERMICO["poa_global"].values)
    assert claves_invalidadas == []
    # Lo único que este test demuestra: si nadie invalidó bypass_result
    # ANTES de llamar a resolver_poa_bypass(), este gate no lo hace por su
    # cuenta -- la responsabilidad de invalidar al REEMPLAZAR la POA es de
    # quien la reemplaza (Motor Óptico), no de este gate de selección.
    assert estado.get("bypass_ok") is True
    assert "bypass_result" in estado


# 13) resolver_poa_bypass(): la invalidación ocurre estructuralmente ANTES
#     de que cualquier lectura de bypass_ok pueda ver el resultado antiguo
#     -- se verifica ejecutando la función y comprobando que, para el mismo
#     dict, bypass_ok YA es False al retornar (no depende del orden de
#     líneas de la página, que es justamente lo frágil que esto reemplaza).
def test_resolver_poa_bypass_invalida_antes_de_poder_leer_bypass_ok():
    estado = _session_state_con_bypass_vigente()
    assert estado["bypass_ok"] is True  # precondición: bypass "vigente"

    g_eff, _, _, claves_invalidadas = resolver_poa_bypass(estado, POA_BRUTA)

    assert g_eff is None  # motor activo, poa_sin_termico_df=None → bloqueado
    assert set(claves_invalidadas) == set(KEYS_BYPASS_RESULTADO)
    # Para cuando resolver_poa_bypass() retorna -- es decir, ANTES de que la
    # página llegue a `if btn_bypass or st.session_state.get("bypass_ok")`
    # más abajo -- bypass_ok ya no está en el estado.
    assert "bypass_ok" not in estado
    assert estado.get("bypass_ok", False) is False


# 14) El bypass MULTI-superficie (Página 9 Vista 3D) tiene un ciclo de vida
#     separado del bypass monofacial -- invalidar_resultados_bypass() NUNCA
#     debe borrarlo de paso.
def test_invalidar_resultados_bypass_no_borra_estado_multisuperficie():
    estado = _session_state_con_bypass_vigente()
    assert estado["bypass_multisup_ok"] is True  # precondición

    invalidar_resultados_bypass(estado)

    for clave in KEYS_BYPASS_MULTISUP_RESULTADO:
        assert clave in estado, (
            f"'{clave}' es del bypass multi-superficie (Página 9) -- "
            "invalidar_resultados_bypass() del bypass monofacial no debe "
            "tocarlo."
        )
    assert estado["bypass_multisup_ok"] is True
    assert estado["bypass_multisup_resultados"] == [
        {"fachada": "Norte", "kwh_bypass": 42.0}
    ]


# ══════════════════════════════════════════════════════════════════════════
# Ronda 3 (17-sep-2026) -- dos caminos que quedaban abiertos tras la ronda 2:
#   (a) Producción visitada DIRECTAMENTE (sin pasar por Página 5) con
#       motor_optico_ok=True y poa_sin_termico_df ausente: antes caía a
#       poa_efectiva_df o poa_df vía _get_poa_df() -- doble conteo térmico o
#       pérdida de IAM/soiling, sin bloqueo ni invalidación.
#   (b) Motor Óptico recalculado (nueva poa_sin_termico_df publicada) sin
#       invalidar un bypass_result calculado con la POA ANTERIOR -- el
#       resultado obsoleto sobrevivía indefinidamente en session_state.
# calculos.mismatch_bypass.exigir_poa_sin_termico() cierra (a); la llamada a
# invalidar_resultados_bypass() en pages/5b_🔆_Motor_Optico.py, ANTES de
# publicar la nueva poa_sin_termico_df, cierra (b).
# ══════════════════════════════════════════════════════════════════════════

# 15) Producción con motor_optico_ok=True + poa_sin_termico_df disponible →
#     debe usarla, sin invalidar nada.
def test_exigir_poa_sin_termico_motor_activo_con_poa_disponible():
    estado = {"motor_optico_ok": True, "poa_sin_termico_df": POA_SIN_TERMICO}
    poa, claves_invalidadas = exigir_poa_sin_termico(estado)

    assert poa is POA_SIN_TERMICO
    assert claves_invalidadas == []


# 16) Producción con motor_optico_ok=True SIN poa_sin_termico_df → NUNCA usa
#     poa_efectiva_df ni poa_df como sustituto (ambas presentes en el
#     estado, pero exigir_poa_sin_termico() ni siquiera las recibe como
#     parámetro -- imposibilidad estructural, no solo de comportamiento).
def test_exigir_poa_sin_termico_motor_activo_sin_poa_no_usa_fallback():
    parametros = set(inspect.signature(exigir_poa_sin_termico).parameters)
    assert "poa_efectiva_df" not in parametros
    assert "poa_df" not in parametros

    estado = _session_state_con_bypass_vigente()
    estado["poa_sin_termico_df"] = None  # explícitamente ausente
    assert estado["poa_efectiva_df"] is POA_EFECTIVA  # presente, pero irrelevante

    poa, claves_invalidadas = exigir_poa_sin_termico(estado)

    assert poa is None, (
        "Con motor_optico_ok=True y poa_sin_termico_df ausente, Producción "
        "debe bloquear -- nunca recibir poa_efectiva_df ni poa_df como G_eff "
        "del SDM."
    )
    # poa_efectiva_df sigue en el estado (no se borra), simplemente nunca se
    # devuelve como sustituto de poa_sin_termico_df.
    assert estado["poa_efectiva_df"] is POA_EFECTIVA


# 17) Ese mismo estado (motor activo, sin poa_sin_termico_df) invalida
#     bypass_ok, bypass_result y las energías derivadas (E_ac_anual_kWh_bypass,
#     kwh_bypass_anual) -- Producción no puede depender de que Página 5 haya
#     saneado session_state.
def test_exigir_poa_sin_termico_invalida_bypass_y_energias_derivadas():
    estado = _session_state_con_bypass_vigente()
    estado["poa_sin_termico_df"] = None
    assert estado["bypass_ok"] is True  # precondición: bypass "vigente"

    poa, claves_invalidadas = exigir_poa_sin_termico(estado)

    assert poa is None
    assert set(claves_invalidadas) == set(KEYS_BYPASS_RESULTADO)
    for clave in ("bypass_ok", "bypass_result", "E_ac_anual_kWh_bypass", "kwh_bypass_anual"):
        assert clave not in estado, f"'{clave}' debió invalidarse"


# 18) Producción funciona con poa_sin_termico_df VÁLIDA: no bloquea, no
#     invalida el bypass vigente (sigue siendo responsabilidad de Motor
#     Óptico invalidarlo AL REEMPLAZAR la POA, no de este gate -- ver test 12).
def test_exigir_poa_sin_termico_funciona_con_poa_valida():
    estado = _session_state_con_bypass_vigente()
    estado["poa_sin_termico_df"] = POA_SIN_TERMICO

    poa, claves_invalidadas = exigir_poa_sin_termico(estado)

    assert poa is POA_SIN_TERMICO
    assert claves_invalidadas == []
    assert estado.get("bypass_ok") is True


# 19) Motor Óptico DESACTIVADO conserva el comportamiento legado: el gate no
#     interviene en absoluto -- ni bloquea, ni invalida, ni toca nada --
#     dejando que el llamador (Producción) use su propio fallback histórico
#     (POA bruta).
def test_exigir_poa_sin_termico_motor_desactivado_conserva_legado():
    estado = _session_state_con_bypass_vigente()
    estado["motor_optico_ok"] = False
    estado["poa_sin_termico_df"] = None  # ni siquiera importa si está o no

    poa, claves_invalidadas = exigir_poa_sin_termico(estado)

    assert poa is None
    assert claves_invalidadas == []
    # Comportamiento legado: NADA se invalida cuando el motor está inactivo
    # -- ni siquiera el bypass "vigente" (que en ese caso se calculó con
    # POA bruta × factor_mismatch, no con el Motor Óptico).
    assert estado.get("bypass_ok") is True
    assert "bypass_result" in estado


# 20) Claves no relacionadas permanecen intactas al pasar por
#     exigir_poa_sin_termico() en su camino de bloqueo.
def test_exigir_poa_sin_termico_no_toca_claves_no_relacionadas():
    estado = _session_state_con_bypass_vigente()
    estado["poa_sin_termico_df"] = None
    claves_previas_no_bypass = {
        k: v for k, v in estado.items() if k not in KEYS_BYPASS_RESULTADO
    }

    exigir_poa_sin_termico(estado)

    for clave, valor in claves_previas_no_bypass.items():
        assert clave in estado, f"'{clave}' no debía eliminarse"
        if isinstance(valor, pd.Series):
            pd.testing.assert_series_equal(estado[clave], valor)
        elif isinstance(valor, pd.DataFrame):
            pd.testing.assert_frame_equal(estado[clave], valor)
        else:
            assert estado[clave] == valor


# 21) Estado multi-superficie no se elimina accidentalmente al pasar por
#     exigir_poa_sin_termico() (ni en el camino de bloqueo, ni con el motor
#     desactivado).
def test_exigir_poa_sin_termico_no_borra_estado_multisuperficie():
    for motor_activo, poa_disponible in [(True, False), (False, False), (True, True)]:
        estado = _session_state_con_bypass_vigente()
        estado["motor_optico_ok"] = motor_activo
        estado["poa_sin_termico_df"] = POA_SIN_TERMICO if poa_disponible else None

        exigir_poa_sin_termico(estado)

        assert estado.get("bypass_multisup_ok") is True, (
            f"caso motor_activo={motor_activo}, poa_disponible={poa_disponible}"
        )
        assert estado.get("bypass_multisup_resultados") == [
            {"fachada": "Norte", "kwh_bypass": 42.0}
        ]


# 22) Motor Óptico invalida TODO lo downstream (no solo el bypass) ANTES de
#     publicar la nueva poa_sin_termico_df -- verificado en dos niveles:
#     (a) comprobación de comportamiento con la MISMA secuencia de
#         operaciones que ejecuta pages/5b_🔆_Motor_Optico.py, sobre un dict;
#     (b) comprobación estructural precisa de que esa llamada existe en el
#         código de la página y aparece ANTES de la línea que escribe
#         poa_sin_termico_df (no una búsqueda de texto genérica: compara
#         posiciones de línea de dos sentencias exactas).
#
# CORRECCIÓN (ronda 4, 17-sep-2026): esta prueba usaba
# invalidar_resultados_bypass() (solo bypass) para simular la secuencia de
# Motor Óptico, y por eso nunca ejercitaba -- ni podía detectar -- que
# produccion_ok, E_ac_anual_kWh, res_produccion*, financiero_ok,
# comp_financiero*, metricas_financiero* e impacto_co2_* seguían vigentes
# después de recalcular la POA. La página real usa
# invalidar_downstream_motor_optico(); esta prueba ahora hace lo mismo.
def test_secuencia_recalculo_motor_optico_invalida_bypass_anterior():
    estado = _session_state_con_bypass_vigente()
    estado["poa_sin_termico_df"] = POA_SIN_TERMICO  # POA "anterior"
    estado.update({
        "produccion_ok": True,
        "E_ac_anual_kWh": 12345.0,
        "res_produccion": {"E_ac_anual_kWh": 12345.0},
        "financiero_ok": True,
        "comp_financiero": {"tir": 0.18},
        "metricas_financiero": {"payback_anos": 6.2},
        "impacto_co2_ok": True,
        "co2_anual_t": 4.2,
        # Ítem 6 del encargo (ronda 5): soiling personalizado, persistido
        # COMO RESULTADO de la corrida anterior (ver comentario en
        # calculos/invalidacion.py junto a estas dos claves).
        "motor_optico_soiling_custom": True,
        "motor_optico_soiling_config": {1: 0.03, 2: 0.04},
    })
    assert estado["bypass_ok"] is True  # bypass calculado con la POA anterior

    # Réplica exacta de la secuencia de pages/5b_🔆_Motor_Optico.py: invalidar
    # ANTES de publicar la nueva poa_sin_termico_df.
    invalidar_downstream_motor_optico(estado)
    poa_nueva = POA_SIN_TERMICO * 1.1  # "nueva" cascada óptica recalculada
    estado["poa_sin_termico_df"] = poa_nueva
    estado["motor_optico_ok"] = True
    # Motor Óptico republica SUS PROPIAS claves justo después de invalidar
    # -- incluidas las nuevas de soiling, con los valores de ESTA corrida
    # (no los de la corrida anterior).
    estado["motor_optico_soiling_custom"] = False
    estado["motor_optico_soiling_config"] = None

    # Bypass -- sigue caducando (subconjunto de lo downstream).
    assert "bypass_ok" not in estado
    assert "bypass_result" not in estado
    # Producción, Financiero, CO₂ -- ahora TAMBIÉN caducan (era el gap
    # reportado: "permanecen vigentes resultados calculados con la POA y
    # el bypass anteriores").
    for clave in (
        "produccion_ok", "E_ac_anual_kWh", "res_produccion",
        "financiero_ok", "comp_financiero", "metricas_financiero",
        "impacto_co2_ok", "co2_anual_t",
    ):
        assert clave not in estado, f"'{clave}' debió invalidarse al recalcular Motor Óptico"
    # La POA nueva y las claves nuevas del Motor Óptico se republican
    # correctamente DESPUÉS de invalidar -- con los valores de ESTA
    # corrida, no arrastrando los de la anterior (True/{1:0.03,2:0.04}).
    assert estado["poa_sin_termico_df"] is poa_nueva
    assert estado["motor_optico_ok"] is True
    assert estado["motor_optico_soiling_custom"] is False
    assert estado["motor_optico_soiling_config"] is None
    # Multi-superficie sobrevive -- no depende de esta POA.
    assert estado.get("bypass_multisup_ok") is True
    assert estado.get("bypass_multisup_resultados") == [
        {"fachada": "Norte", "kwh_bypass": 42.0}
    ]


def test_pagina_motor_optico_invalida_downstream_antes_de_publicar_poa():
    ruta = os.path.join(
        os.path.dirname(__file__), "..", "pages", "5b_🔆_Motor_Optico.py",
    )
    with open(ruta, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    idx_invalidar = next(
        (i for i, ln in enumerate(lineas) if "invalidar_downstream_motor_optico(st.session_state)" in ln),
        None,
    )
    idx_publica_poa = next(
        (i for i, ln in enumerate(lineas)
         if 'st.session_state["poa_sin_termico_df"]' in ln and "=" in ln),
        None,
    )
    assert idx_invalidar is not None, (
        "pages/5b_🔆_Motor_Optico.py debe llamar a "
        "invalidar_downstream_motor_optico(st.session_state) al recalcular "
        "la cascada óptica -- no solo invalidar_resultados_bypass() (que "
        "deja vigentes produccion_ok/financiero_ok/impacto_co2_ok)."
    )
    assert idx_publica_poa is not None, (
        "pages/5b_🔆_Motor_Optico.py debe seguir publicando "
        "st.session_state['poa_sin_termico_df']."
    )
    assert idx_invalidar < idx_publica_poa, (
        "invalidar_downstream_motor_optico() debe ejecutarse ANTES de "
        "publicar la nueva poa_sin_termico_df -- si no, un resultado "
        "downstream calculado con la POA anterior podría leerse como "
        "vigente entre ambas líneas."
    )


# ══════════════════════════════════════════════════════════════════════════
# Ronda 4 (17-sep-2026) -- gap downstream: invalidar_resultados_bypass()
# (bypass monofacial) e invalidar_downstream_motor_optico() (todo lo demás)
# dejaban vigentes produccion_ok, E_ac_anual_kWh, res_produccion*,
# financiero_ok, comp_financiero*, metricas_financiero* e impacto_co2_* tras
# recalcular Motor Óptico -- calculados con la POA/bypass ANTERIORES.
# calculos.invalidacion.KEYS_DOWNSTREAM_MOTOR_OPTICO /
# invalidar_downstream_motor_optico() cierran esa brecha, derivando la lista
# de KEYS_DERIVADOS_POA (fuente única) en vez de duplicarla a mano.
# ══════════════════════════════════════════════════════════════════════════

def _session_state_con_resultados_downstream_vigentes() -> dict:
    """Extiende el fixture de bypass con resultados de Producción, pérdida
    óhmica, Financiero e impacto CO₂ -- todos "vigentes" de una corrida
    anterior, calculados con la POA que Motor Óptico está por reemplazar."""
    estado = _session_state_con_bypass_vigente()
    estado.update({
        # Motor Óptico -- claves que el fixture de bypass no traía
        "motor_optico_result_df": pd.DataFrame({"poa_efectiva": [1.0]}),
        "motor_optico_summary": {"factor_global": 0.87},
        "poa_efectiva_anual_kWh_m2": 1500.0,
        "motor_optico_b0": 0.05,
        "motor_optico_tau": 0.9,
        "motor_optico_noct": 45.0,
        "motor_optico_coef_temp": -0.0045,
        "motor_optico_f_iam_dif": 0.9,
        "motor_optico_k_soil_vert": 0.65,
        # Producción
        "produccion_ok": True,
        "produccion_modo_iv": "SDM",
        "E_ac_anual_kWh": 12345.0,
        "PR_sistema": 0.81,
        "res_produccion": {"E_ac_anual_kWh": 12345.0},
        "res_produccion_base": {"E_ac_anual_kWh": 12000.0},
        "res_produccion_iv": {"E_ac_anual_kWh": 12345.0},
        "perdida_ohmica_unifilar": {"pct": 1.2, "kwh": 150.0},
        # Financiero
        "financiero_ok": True,
        "comp_financiero": {"tir": 0.18},
        "comp_financiero_p90": {"tir": 0.15},
        "metricas_financiero": {"payback_anos": 6.2},
        "metricas_financiero_p90": {"payback_anos": 7.1},
        # Impacto CO₂
        "impacto_co2_ok": True,
        "co2_anual_t": 4.2,
        "co2_total_t": 84.0,
        "co2_total_prom_t": 80.0,
        "co2_total_marg_t": 90.0,
        "co2_arboles_equiv": 120,
        "co2_hogares_equiv": 15,
        "co2_km_vehiculo_equiv": 20000,
        "co2_valor_bonos_usd": 500.0,
        # Multi-superficie NO-bypass (Página 9) -- debe sobrevivir intacto
        "E_ac_anual_kWh_multisup": 3000.0,
        "poa_df_multisup": pd.DataFrame({"poa_global": [500.0]}),
        "area_total_multisup": 120.0,
        "multisup_desglose": [{"nombre": "Fachada Norte", "area_m2": 60.0}],
        "multisup_activo": True,
        "multisup_origen": "fisico",
        "multisup_perdida_bus_kWh": 12.0,
        "multisup_estado_electrico": {"estado": "verde", "n_bloqueos": 0, "n_avisos": 0, "texto": "🟢"},
        "_multisup_proyecto_fisico": {"agregados": {"E_ac_total_kWh": 3000.0}},
        # ── Configuración/datos independientes -- deben sobrevivir intactos
        # (auditoría ronda 5, 17-sep-2026): ninguna depende de la POA del
        # Motor Óptico.
        "diag_real_kwh": {"Ene": 950.0, "Feb": 900.0},  # lecturas REALES tipeadas a mano
        "diag_total_real_kwh": 1850.0,                   # suma pura del dato anterior
        "tasa_degradacion_calculada": 0.5,                # regresión sobre PR histórico multi-año, tipeado a mano
        "P_stc_kW_sistema": 10.0,                         # eco de Dimensionamiento (paneles × Pmax), no depende de POA
        "N_paneles_final": 20,
        "panel_nombre_final": "ASP-ST1-T40",
        "eta_inversor": 0.96,
    })
    # Cualquier clave de KEYS_DOWNSTREAM_MOTOR_OPTICO que este fixture aún no
    # haya fijado arriba recibe un placeholder -- así el fixture queda
    # automáticamente completo frente a futuras claves que se agreguen a la
    # constante (fuente única en calculos/invalidacion.py), sin tener que
    # enumerarlas todas a mano en este archivo de pruebas.
    for _clave in KEYS_DOWNSTREAM_MOTOR_OPTICO:
        estado.setdefault(_clave, f"valor_anterior::{_clave}")
    return estado


# 24) Recalcular Motor Óptico invalida bypass, Producción y Financiero
#     anteriores en una sola llamada.
def test_invalidar_downstream_motor_optico_limpia_bypass_produccion_financiero():
    estado = _session_state_con_resultados_downstream_vigentes()
    eliminadas = invalidar_downstream_motor_optico(estado)

    assert set(eliminadas) == set(KEYS_DOWNSTREAM_MOTOR_OPTICO)
    for clave in KEYS_DOWNSTREAM_MOTOR_OPTICO:
        assert clave not in estado, f"'{clave}' debió invalidarse"
    # Explícitamente los tres grupos reportados como el gap:
    for clave in ("bypass_ok", "bypass_result"):
        assert clave not in estado
    for clave in ("produccion_ok", "E_ac_anual_kWh", "res_produccion",
                  "res_produccion_base", "res_produccion_iv", "PR_sistema"):
        assert clave not in estado
    for clave in ("financiero_ok", "comp_financiero", "comp_financiero_p90",
                  "metricas_financiero", "metricas_financiero_p90"):
        assert clave not in estado
    for clave in ("impacto_co2_ok", "co2_anual_t", "co2_total_t"):
        assert clave not in estado


# 25) E_ac_anual_kWh (Producción) y E_ac_anual_kWh_bypass (bypass) dejan de
#     estar vigentes -- las dos energías mencionadas explícitamente en el
#     reporte del gap.
def test_invalidar_downstream_motor_optico_invalida_energias_produccion_y_bypass():
    estado = _session_state_con_resultados_downstream_vigentes()
    invalidar_downstream_motor_optico(estado)

    assert estado.get("E_ac_anual_kWh") is None
    assert estado.get("E_ac_anual_kWh_bypass") is None
    assert estado.get("kwh_bypass_anual") is None


# 25b) Ronda 5 (17-sep-2026): E_dc_anual_kWh, Y_f_kWh_kWp,
#      df_mensual_produccion y verificacion_jrc -- las 4 salidas de
#      Producción que la auditoría anterior había omitido de
#      KEYS_DOWNSTREAM_MOTOR_OPTICO -- también quedan invalidadas.
def test_invalidar_downstream_motor_optico_invalida_salidas_produccion_omitidas():
    estado = _session_state_con_resultados_downstream_vigentes()
    invalidar_downstream_motor_optico(estado)

    for clave in (
        "E_dc_anual_kWh", "Y_f_kWh_kWp", "df_mensual_produccion", "verificacion_jrc",
    ):
        assert clave not in estado, f"'{clave}' debió invalidarse (gap de la auditoría anterior)"


# 25c) El lado DERIVADO del diagnóstico real-vs-simulado (Página 6, #28;
#      consumido por Reporte) también caduca -- depende de e_sim/HSP, que
#      salen de la POA. El lado de ENTRADA del usuario (lecturas reales)
#      sobrevive (verificado en el test de configuración independiente).
def test_invalidar_downstream_motor_optico_invalida_lado_simulado_del_diagnostico():
    estado = _session_state_con_resultados_downstream_vigentes()
    invalidar_downstream_motor_optico(estado)

    for clave in (
        "df_diagnostico_real", "diag_meses_rojo", "diag_meses_amarillo",
        "diag_total_sim_kwh", "diag_total_stc_kwh", "diag_pr_conv_global",
        "diag_pr_corr_global", "diag_perdida_t_pct", "diag_perdida_t_kwh",
        "diag_gamma_pct",
    ):
        assert clave not in estado, f"'{clave}' (lado simulado) debió invalidarse"
    # El lado de entrada (dato real tipeado a mano) sobrevive.
    assert estado.get("diag_real_kwh") == {"Ene": 950.0, "Feb": 900.0}
    assert estado.get("diag_total_real_kwh") == 1850.0


# 26) Reporte no puede presentar resultados anteriores como actuales.
#     reporte_generado (Página 10) es SOLO un flag de checklist para el
#     🧭 Asistente ("¿el usuario generó un reporte alguna vez?"), no una
#     caché de contenido -- Página 10 reconstruye html_str en vivo desde
#     session_state en CADA render, antes de fijar la bandera. No hay
#     ningún otro punto en el código que LEA reporte_generado para saltarse
#     ese recálculo y reutilizar un reporte viejo. Por eso NO se agrega a
#     KEYS_DOWNSTREAM_MOTOR_OPTICO (el propio encargo lo condiciona a "si
#     existe y REALMENTE se reutiliza"): este test documenta y verifica esa
#     conclusión, para que agregar una caché real de reporte en el futuro
#     obligue a revisar esta decisión.
def test_reporte_generado_no_es_cache_reutilizable():
    ruta_reporte = os.path.join(
        os.path.dirname(__file__), "..", "pages", "10_📄_Reporte_PDF.py",
    )
    with open(ruta_reporte, "r", encoding="utf-8") as f:
        src_reporte = f.read()
    ruta_asistente = os.path.join(
        os.path.dirname(__file__), "..", "calculos", "asistente.py",
    )
    with open(ruta_asistente, "r", encoding="utf-8") as f:
        src_asistente = f.read()

    assert "reporte_generado" not in KEYS_DOWNSTREAM_MOTOR_OPTICO
    assert "reporte_generado" not in KEYS_DERIVADOS_POA

    # Único punto de escritura conocido: justo después de construir html_str
    # en vivo (no antes -- si apareciera antes, podría gatearse una reutilización).
    assert 'st.session_state["reporte_generado"] = True' in src_reporte
    # Único punto de lectura conocido: el checklist del Asistente (Paso 10),
    # que solo pregunta "¿no es None?" -- nunca reutiliza el contenido.
    assert '("reporte_generado",)' in src_asistente
    # Si reporte_generado se leyera en Página 10 para SALTARSE la
    # reconstrucción de html_str, este test debe fallar y forzar revisar
    # si ahora sí necesita entrar en KEYS_DOWNSTREAM_MOTOR_OPTICO.
    assert 'session_state.get("reporte_generado")' not in src_reporte


# 27) Configuración de entrada NO derivada permanece intacta (paneles,
#     inversores, nombre de proyecto, parámetros de sesión que NO dependen
#     de la POA del Motor Óptico).
def test_invalidar_downstream_motor_optico_no_toca_configuracion_no_derivada():
    estado = _session_state_con_resultados_downstream_vigentes()
    claves_previas_no_downstream = {
        k: v for k, v in estado.items() if k not in KEYS_DOWNSTREAM_MOTOR_OPTICO
    }
    invalidar_downstream_motor_optico(estado)

    for clave, valor in claves_previas_no_downstream.items():
        assert clave in estado, f"'{clave}' no debía eliminarse"
        if isinstance(valor, pd.Series):
            pd.testing.assert_series_equal(estado[clave], valor)
        elif isinstance(valor, pd.DataFrame):
            pd.testing.assert_frame_equal(estado[clave], valor)
        else:
            assert estado[clave] == valor


# 28) Estado multi-superficie NO se elimina salvo dependencia demostrada --
#     se demostró (auditoría de pages/9_🗺️_Vista_3D.py) que usa su propia
#     POA por superficie, nunca poa_sin_termico_df/poa_efectiva_df del Motor
#     Óptico, así que ninguna de sus claves (bypass o no) debe caducar aquí.
def test_invalidar_downstream_motor_optico_no_borra_estado_multisuperficie():
    estado = _session_state_con_resultados_downstream_vigentes()
    invalidar_downstream_motor_optico(estado)

    for clave in KEYS_MULTISUP_ESTADO + KEYS_BYPASS_MULTISUP_RESULTADO:
        assert clave in estado, (
            f"'{clave}' es estado multi-superficie con POA propia -- no "
            "debe invalidarse al recalcular Motor Óptico."
        )
    assert estado["bypass_multisup_ok"] is True
    assert estado["bypass_multisup_resultados"] == [
        {"fachada": "Norte", "kwh_bypass": 42.0}
    ]


# 29) Invariantes arquitectónicos de KEYS_DOWNSTREAM_MOTOR_OPTICO -- guardan
#     contra que las listas se vuelvan a desincronizar en silencio (como
#     pasó con KEYS_DERIVADOS_POA vs. KEYS_BYPASS_RESULTADO, corregido en
#     esta misma ronda).
def test_keys_downstream_motor_optico_invariantes_arquitectonicos():
    # (a) Todo el bypass monofacial debe caducar al recalcular Motor Óptico.
    assert set(KEYS_BYPASS_RESULTADO) <= set(KEYS_DOWNSTREAM_MOTOR_OPTICO)
    # (b) Nada multi-superficie debe caducar aquí.
    assert not (set(KEYS_MULTISUP_ESTADO) & set(KEYS_DOWNSTREAM_MOTOR_OPTICO))
    assert not (set(KEYS_BYPASS_MULTISUP_RESULTADO) & set(KEYS_DOWNSTREAM_MOTOR_OPTICO))
    # (c) KEYS_DOWNSTREAM_MOTOR_OPTICO es un subconjunto de la fuente única
    # KEYS_DERIVADOS_POA -- nunca inventa claves nuevas por su cuenta.
    assert set(KEYS_DOWNSTREAM_MOTOR_OPTICO) <= set(KEYS_DERIVADOS_POA)
    # (d) Guarda de regresión del bug de esta ronda: KEYS_DERIVADOS_POA ya
    # no puede desincronizarse de KEYS_BYPASS_RESULTADO.
    assert set(KEYS_BYPASS_RESULTADO) <= set(KEYS_DERIVADOS_POA)
    # (e) Los resultados de Producción/Financiero/CO₂ mínimos exigidos están
    # cubiertos.
    for clave in (
        "produccion_ok", "produccion_modo_iv", "E_ac_anual_kWh", "PR_sistema",
        "res_produccion", "res_produccion_base", "res_produccion_iv",
        "financiero_ok", "comp_financiero", "comp_financiero_p90",
        "metricas_financiero", "metricas_financiero_p90",
    ):
        assert clave in KEYS_DOWNSTREAM_MOTOR_OPTICO, clave


# 23) Producción (Página 6) ya no debe contener el patrón peligroso de
#     fallback multi-clave (_get_poa_df con poa_efectiva_df/poa_df como
#     sustitutos) ni usar poa_efectiva_df/poa_df directamente como G_eff
#     del SDM cuando el Motor Óptico está activo.
def test_pagina_produccion_no_usa_fallback_a_poa_efectiva_ni_poa_bruta():
    ruta = os.path.join(
        os.path.dirname(__file__), "..", "pages", "6_📊_Produccion.py",
    )
    with open(ruta, "r", encoding="utf-8") as f:
        src = f.read()

    assert "exigir_poa_sin_termico" in src, (
        "Página 6 debe usar calculos.mismatch_bypass.exigir_poa_sin_termico() "
        "para exigir poa_sin_termico_df cuando el Motor Óptico está activo."
    )
    assert "_get_poa_df(" not in src, (
        "Reapareció el helper _get_poa_df() con fallback multi-clave "
        "(poa_sin_termico_df → poa_efectiva_df → poa_df) -- ese patrón "
        "permitía doble conteo térmico en el SDM de Producción."
    )


# ══════════════════════════════════════════════════════════════════════════
# Ronda 5 (17-sep-2026) -- tres brechas finales:
#   (a) La persistencia a disco (calculos/persistencia_resultados.py) podía
#       sobrevivir a la invalidación en memoria y ser "restaurada" por
#       Financiero con E_ac/E_dc de la POA anterior.
#   (b) KEYS_DOWNSTREAM_MOTOR_OPTICO omitía E_dc_anual_kWh, Y_f_kWh_kWp,
#       df_mensual_produccion y verificacion_jrc (cubierto arriba, tests
#       25b/25c).
#   (c) Página 5 leía bypass_ok/bypass_result en sus métricas iniciales
#       ANTES de llamar resolver_poa_bypass() -- si el usuario nunca subía
#       un CSV, esa invalidación no llegaba a ejecutarse nunca.
# ══════════════════════════════════════════════════════════════════════════

# 30) Página 5: el saneamiento del bypass (resolver_poa_bypass()) ahora se
#     ejecuta de forma INCONDICIONAL cerca del inicio de la página -- antes
#     de la primera lectura de bypass_ok/bypass_result (sección "Métricas
#     separadas") y antes del bloque `if btn_bypass or bypass_ok` de la
#     sección 5 -- en vez de vivir dentro de `if csv_ok and df_fs_raw is not
#     None:`, que nunca se ejecuta si el usuario no sube un CSV.
def test_pagina_mismatch_saneamiento_bypass_es_incondicional_y_temprano():
    ruta = os.path.join(
        os.path.dirname(__file__), "..", "pages", "5_🔀_Mismatch.py",
    )
    with open(ruta, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    idx_resolver = next(
        (i for i, ln in enumerate(lineas)
         if ln.strip().startswith("poa_bp, poa_src, _k_bipv_bp, _bypass_claves_invalidadas = resolver_poa_bypass(")),
        None,
    )
    assert idx_resolver is not None, (
        "No se encontró la asignación de resolver_poa_bypass() en Página 5."
    )
    # Incondicional: sin sangría (no anidada dentro de ningún if/for/with).
    assert lineas[idx_resolver].startswith("poa_bp"), (
        "resolver_poa_bypass() debe ejecutarse SIN indentación (a nivel de "
        "módulo, incondicional) -- si vuelve a quedar anidada dentro de "
        "`if csv_ok and df_fs_raw is not None:`, el saneamiento vuelve a "
        "depender de que el usuario suba un CSV."
    )

    idx_primera_lectura_bypass_result = next(
        (i for i, ln in enumerate(lineas)
         if 'st.session_state.get("bypass_result")' in ln),
        None,
    )
    idx_if_btn_bypass = next(
        (i for i, ln in enumerate(lineas)
         if 'if btn_bypass or st.session_state.get("bypass_ok")' in ln),
        None,
    )
    idx_if_csv_ok = next(
        (i for i, ln in enumerate(lineas)
         if ln.strip().startswith("if csv_ok and df_fs_raw is not None:")),
        None,
    )
    assert idx_primera_lectura_bypass_result is not None
    assert idx_if_btn_bypass is not None
    assert idx_if_csv_ok is not None

    assert idx_resolver < idx_primera_lectura_bypass_result, (
        "resolver_poa_bypass() debe ejecutarse ANTES de la primera lectura "
        "de bypass_result (sección 'Métricas separadas')."
    )
    assert idx_resolver < idx_if_btn_bypass, (
        "resolver_poa_bypass() debe ejecutarse ANTES de "
        "`if btn_bypass or bypass_ok`."
    )
    assert idx_resolver < idx_if_csv_ok, (
        "resolver_poa_bypass() debe ejecutarse ANTES del bloque gateado por "
        "csv_ok -- así corre aunque el usuario nunca suba un CSV."
    )


# 31) Comportamiento: incluso SIN CSV (csv_ok=False, sección de simulación
#     de bypass nunca se renderiza), resolver_poa_bypass() -- llamado tal
#     como lo hace ahora Página 5, de forma incondicional -- sí invalida un
#     bypass_result obsoleto. Réplica de comportamiento sobre un dict, sin
#     Streamlit.
def test_saneamiento_bypass_ocurre_incluso_sin_csv_cargado():
    estado = _session_state_con_bypass_vigente()
    # csv_ok=False / df_fs_raw=None: el usuario nunca subió un CSV -- la
    # sección "5. Bypass Diodes" de la página nunca se renderiza.
    estado["csv_fs_ok"] = False
    estado["df_fs_raw"] = None
    assert estado["bypass_ok"] is True  # bypass "vigente" de una corrida anterior

    # Página 5 ahora llama esto de forma incondicional, sin mirar csv_ok.
    g_eff, _, _, claves_invalidadas = resolver_poa_bypass(estado, POA_BRUTA)

    assert g_eff is None  # motor activo, poa_sin_termico_df=None → bloqueado
    assert "bypass_ok" not in estado, (
        "El saneamiento debe ocurrir aunque no haya CSV cargado -- las "
        "métricas de la sección 'Auditoría' no deben leer bypass_ok/"
        "bypass_result obsoletos solo porque el usuario no subió un CSV."
    )
    assert set(claves_invalidadas) == set(KEYS_BYPASS_RESULTADO)


# ── Fixtures de persistencia a disco (gap a) ─────────────────────────────────
# Usan tmp_path + monkeypatch para aislar completamente el directorio de
# persistencia -- NUNCA tocan datos reales de usuarios.

@pytest.fixture
def _pr_aislado(tmp_path, monkeypatch):
    """calculos.persistencia_resultados apuntando a un directorio temporal."""
    import calculos.persistencia_resultados as pr
    monkeypatch.setattr(pr, "DIR_PERSISTENCIA", str(tmp_path))
    return pr


# 32) Recalcular Motor Óptico elimina la persistencia de Producción anterior.
def test_recalculo_motor_optico_elimina_persistencia_produccion_anterior(_pr_aislado):
    pr = _pr_aislado
    usuario = "ronda5-test@example.com"
    sesion_guardada = {
        "E_ac_anual_kWh": 12345.6, "E_dc_anual_kWh": 13000.0,
        "PR_sistema": 0.81, "Y_f_kWh_kWp": 1500.0,
        "P_stc_kW_sistema": 10.0, "N_paneles_final": 20,
        "panel_nombre_final": "ASP-ST1-T40", "eta_inversor": 0.96,
        "ciudad": "Bogotá", "lat_proyecto": 4.7110, "lon_proyecto": -74.0721,
    }
    assert pr.guardar_resultados_produccion(sesion_guardada, usuario) is True
    ruta_json = pr._ruta_resultados(usuario)
    assert os.path.exists(ruta_json), "precondición: el JSON debe existir antes de recalcular"

    # Réplica exacta de la secuencia de pages/5b_🔆_Motor_Optico.py: invalidar
    # en memoria, LUEGO limpiar la persistencia a disco, ANTES de publicar
    # la nueva POA -- mismo patrón que pages/1_🏠_Proyecto.py.
    estado = _session_state_con_resultados_downstream_vigentes()
    invalidar_downstream_motor_optico(estado)
    pr.limpiar_resultados_produccion(usuario)
    estado["poa_sin_termico_df"] = POA_SIN_TERMICO * 1.05  # nueva POA
    estado["motor_optico_ok"] = True

    assert not os.path.exists(ruta_json), (
        "limpiar_resultados_produccion() debe borrar el JSON persistido -- "
        "si sobrevive, restaurar_resultados_produccion() lo repoblaría en "
        "la próxima visita a Financiero."
    )


# 33) Financiero NO puede restaurar E_ac/E_dc anteriores después del
#     recálculo -- ni siquiera en una sesión/pestaña NUEVA (que es
#     precisamente el caso de uso de restaurar_resultados_produccion()).
def test_financiero_no_restaura_energia_anterior_tras_recalculo(_pr_aislado):
    pr = _pr_aislado
    usuario = "ronda5-test-financiero@example.com"
    sesion_guardada = {
        "E_ac_anual_kWh": 12345.6, "E_dc_anual_kWh": 13000.0,
        "PR_sistema": 0.81, "Y_f_kWh_kWp": 1500.0,
        "P_stc_kW_sistema": 10.0, "N_paneles_final": 20,
        "panel_nombre_final": "ASP-ST1-T40", "eta_inversor": 0.96,
        "ciudad": "Bogotá", "lat_proyecto": 4.7110, "lon_proyecto": -74.0721,
    }
    assert pr.guardar_resultados_produccion(sesion_guardada, usuario) is True

    # Motor Óptico recalcula: invalida en memoria + limpia disco.
    estado_5b = _session_state_con_resultados_downstream_vigentes()
    invalidar_downstream_motor_optico(estado_5b)
    pr.limpiar_resultados_produccion(usuario)

    # Financiero se abre en una sesión/pestaña NUEVA (el caso exacto que
    # restaurar_resultados_produccion() existe para cubrir, ver
    # pages/7_💰_Financiero.py): sin produccion_ok, sin E_ac/E_dc en memoria.
    estado_financiero_nuevo = {
        "auth_email": usuario, "ciudad": "Bogotá",
        "lat_proyecto": 4.7110, "lon_proyecto": -74.0721,
    }
    restauro = pr.restaurar_resultados_produccion(estado_financiero_nuevo, usuario)

    assert restauro is False, (
        "Financiero no debe poder restaurar nada -- el JSON que lo hubiera "
        "permitido ya se limpió al recalcular Motor Óptico."
    )
    assert "E_ac_anual_kWh" not in estado_financiero_nuevo
    assert "E_dc_anual_kWh" not in estado_financiero_nuevo


# 34) Salvaguarda: sin limpiar la persistencia, Financiero SÍ restauraría
#     (demuestra que el test 33 realmente ejercita la limpieza, y no un
#     comportamiento por default de restaurar_resultados_produccion()).
#
#     produccion-codespec Fase 1 ("Persistencia", integrado 19-sep-2026) +
#     CodeSpecs/06-analisis-financiero/diseno.md (payload de integridad,
#     20-sep-2026): restaurar exige ADEMÁS que el SHA-256 recalculado del
#     payload canónico PERSISTIDO coincida exactamente con
#     produccion_run_signature_v1 -- ver tests/test_produccion_vigencia.py
#     para esa cobertura completa. Este control sigue siendo válido con un
#     payload real y consistente: el punto del test (que el "no restaura"
#     del test 33 viene de limpiar_resultados_produccion(), no de un
#     default) no depende de la firma/payload en sí, así que se mantiene el
#     mismo caso feliz salvo por ese requisito nuevo.
def test_sin_limpiar_persistencia_financiero_si_restauraria(_pr_aislado):
    from calculos.produccion_vigencia import (
        construir_payload_produccion_run_signature_v1, firma_desde_payload,
    )

    pr = _pr_aislado
    usuario = "ronda5-test-control@example.com"
    _idx_control = pd.date_range("2001-01-01", periods=5, freq="h", tz="UTC")
    _payload_control = construir_payload_produccion_run_signature_v1(
        panel={"nombre": "PANEL-CONTROL", "Pmax_stc": 63.0, "NOCT": 45.0},
        panel_nombre="PANEL-CONTROL",
        inversor={"modelo": "INV-CONTROL", "P_ac_nom_W": 15000},
        inversor_nombre="INV-CONTROL",
        N_paneles=20, N_serie=5, N_strings_tracker=4, n_inversores=1,
        P_dc_stc_kW=1.26, eta_inversor=0.975, P_ac_nom_W_total=15000.0,
        NOCT=45.0, k_bipv=1.3, produccion_usar_iv=False, source_mode="sdm_pvsyst",
        tmy_index=_idx_control, tmy_T2m=np.array([20.0, 21.0, 22.0, 21.0, 20.0]),
        poa_source="poa_sin_termico_df", poa_index=_idx_control,
        poa_global=np.array([300.0, 500.0, 700.0, 500.0, 300.0]),
        factor_mismatch_aplicado=0.92,
    )
    _firma_control = firma_desde_payload(_payload_control)
    sesion_guardada = {
        "E_ac_anual_kWh": 12345.6, "E_dc_anual_kWh": 13000.0,
        "PR_sistema": 0.81, "Y_f_kWh_kWp": 1500.0,
        "P_stc_kW_sistema": 10.0, "N_paneles_final": 20,
        "panel_nombre_final": "ASP-ST1-T40", "eta_inversor": 0.96,
        "produccion_run_signature_v1": _firma_control,
        pr.CLAVE_PAYLOAD_FIRMA: _payload_control,
        "ciudad": "Bogotá", "lat_proyecto": 4.7110, "lon_proyecto": -74.0721,
    }
    pr.guardar_resultados_produccion(sesion_guardada, usuario)
    # NO se llama limpiar_resultados_produccion() -- control negativo.
    estado_nuevo = {
        "auth_email": usuario, "ciudad": "Bogotá",
        "lat_proyecto": 4.7110, "lon_proyecto": -74.0721,
        # SIN produccion_run_signature_v1 -- pestaña nueva real, la
        # verificación depende solo del payload ya persistido.
    }
    restauro = pr.restaurar_resultados_produccion(estado_nuevo, usuario)
    assert restauro is True
    assert estado_nuevo["E_ac_anual_kWh"] == 12345.6
    assert estado_nuevo["E_dc_anual_kWh"] == 13000.0


# 35) pages/5b_🔆_Motor_Optico.py llama a limpiar_resultados_produccion()
#     ANTES de publicar la nueva POA -- mismo patrón estructural que
#     pages/1_🏠_Proyecto.py (invalidar estado, luego limpiar disco).
def test_pagina_motor_optico_limpia_persistencia_antes_de_publicar_poa():
    ruta = os.path.join(
        os.path.dirname(__file__), "..", "pages", "5b_🔆_Motor_Optico.py",
    )
    with open(ruta, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    idx_invalidar = next(
        (i for i, ln in enumerate(lineas) if "invalidar_downstream_motor_optico(st.session_state)" in ln),
        None,
    )
    idx_limpiar = next(
        (i for i, ln in enumerate(lineas) if "limpiar_resultados_produccion(" in ln
         and "def " not in ln and "import" not in ln),
        None,
    )
    idx_publica_poa = next(
        (i for i, ln in enumerate(lineas)
         if 'st.session_state["poa_sin_termico_df"]' in ln and "=" in ln),
        None,
    )
    assert idx_invalidar is not None
    assert idx_limpiar is not None, (
        "pages/5b_🔆_Motor_Optico.py debe llamar a "
        "limpiar_resultados_produccion(auth_email) al recalcular -- si no, "
        "el JSON persistido sobrevive y Financiero lo restauraría."
    )
    assert idx_publica_poa is not None
    assert idx_invalidar < idx_limpiar < idx_publica_poa, (
        "El orden debe ser: invalidar en memoria → limpiar disco → publicar "
        "la nueva POA (mismo patrón que pages/1_🏠_Proyecto.py)."
    )


# 36) No aparecen ciclos de importación -- se verifica en un intérprete
#     Python FRESCO (subprocess), no reutilizando módulos ya cacheados por
#     este proceso de pruebas.
def test_no_hay_ciclos_de_importacion():
    modulos = [
        "calculos.invalidacion",
        "calculos.mismatch_bypass",
        "calculos.persistencia_resultados",
    ]
    codigo = "; ".join(f"import {m}" for m in modulos)
    resultado = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=os.path.join(os.path.dirname(__file__), ".."),
        capture_output=True, text=True, timeout=60,
    )
    assert resultado.returncode == 0, (
        f"Import falló (posible ciclo): {resultado.stderr}"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
