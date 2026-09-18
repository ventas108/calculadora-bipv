# -*- coding: utf-8 -*-
"""
Fase 1 del CodeSpec de Producción — pruebas de integración (estructurales)
para la conexión de las piezas puras (calculos.produccion_vigencia,
calculos.mismatch.calcular_factor_mismatch_sin_soiling) dentro de
pages/5_🔀_Mismatch.py y pages/6_📊_Produccion.py.

Las páginas de Streamlit no son testeables como funciones puras (ejecutan
top-level `st.*` al importarse), así que estas pruebas verifican el
CONTRATO estructural del código fuente: qué se llama, con qué argumentos, y
en qué orden -- comparaciones de posición de línea exactas, no búsquedas de
texto genéricas, siguiendo el patrón ya establecido en
test_seleccion_poa_bypass_pagina5.py para el mismo tipo de verificación.
"""
import os

import pytest

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_PAGINA_5 = os.path.join(_ROOT, "pages", "5_🔀_Mismatch.py")
_PAGINA_6 = os.path.join(_ROOT, "pages", "6_📊_Produccion.py")


def _leer(ruta: str) -> str:
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _lineas(ruta: str) -> list[str]:
    with open(ruta, "r", encoding="utf-8") as f:
        return f.readlines()


# ══════════════════════════════════════════════════════════════════════════
# Objetivo 2 — Soiling único: Página 5 publica factor_mismatch_sin_soiling
# ══════════════════════════════════════════════════════════════════════════

def test_pagina5_importa_calcular_factor_mismatch_sin_soiling():
    src = _leer(_PAGINA_5)
    assert "calcular_factor_mismatch_sin_soiling" in src


def test_pagina5_publica_factor_mismatch_sin_soiling_junto_a_global():
    src = _leer(_PAGINA_5)
    assert 'st.session_state["factor_mismatch_sin_soiling"]' in src
    # Debe seguir conservando la clave histórica (compatibilidad).
    assert 'st.session_state["factor_global_mismatch"]' in src


def test_pagina5_factor_sin_soiling_usa_sombra_y_mismatch_orientacion_no_soiling():
    """La llamada debe pasar factor_sombra_anual y factor_mismatch_or_pct --
    nunca pct_soiling ni cascada_mismatch -- para que el resultado
    estructuralmente no pueda incluir soiling."""
    src = _leer(_PAGINA_5)
    idx = src.index("calcular_factor_mismatch_sin_soiling(")
    llamada = src[idx: idx + 200]
    assert "factor_sombra_anual" in llamada
    assert "factor_mismatch_or_pct" in llamada
    assert "pct_soiling" not in llamada


# ══════════════════════════════════════════════════════════════════════════
# Objetivo 3 — Página 5 firma el bypass justo tras simular_bypass_horario()
# ══════════════════════════════════════════════════════════════════════════

def test_pagina5_firma_bypass_despues_de_simular_y_antes_de_bypass_ok():
    lineas = _lineas(_PAGINA_5)
    idx_simular = next(
        (i for i, ln in enumerate(lineas) if "res_bp = simular_bypass_horario(" in ln), None
    )
    idx_firma = next(
        (i for i, ln in enumerate(lineas)
         if 'st.session_state["bypass_run_signature_v1"]' in ln), None
    )
    idx_bypass_ok_true = next(
        (i for i, ln in enumerate(lineas)
         if ln.strip() == 'st.session_state["bypass_ok"]         = True'), None
    )
    assert idx_simular is not None, "simular_bypass_horario() debe seguir presente en Página 5."
    assert idx_firma is not None, (
        "Página 5 debe guardar bypass_run_signature_v1 tras simular el bypass."
    )
    assert idx_bypass_ok_true is not None
    assert idx_simular < idx_firma < idx_bypass_ok_true, (
        "El orden debe ser: simular → firmar → marcar bypass_ok=True, para "
        "que nunca quede bypass_ok=True sin una firma coherente con ese "
        "resultado."
    )


def test_pagina5_firma_bypass_usa_los_mismos_argumentos_efectivos():
    """calcular_bypass_run_signature_v1() debe recibir G_eff=poa_bp,
    T_amb=T_amb_bp, panel=panel_bp y umbral_shade=0.05 -- los MISMOS valores
    literales que la llamada a simular_bypass_horario() justo arriba, no una
    reconstrucción aparte que pudiera divergir."""
    src = _leer(_PAGINA_5)
    idx = src.index("calcular_bypass_run_signature_v1(")
    llamada = src[idx: idx + 700]
    assert "panel=panel_bp" in llamada
    assert "G_eff=poa_bp" in llamada
    assert "T_amb=T_amb_bp" in llamada
    assert "umbral_shade=0.05" in llamada


# ══════════════════════════════════════════════════════════════════════════
# Objetivo 2 (Producción) — selección de factor según Motor Óptico
# ══════════════════════════════════════════════════════════════════════════

def test_pagina6_selecciona_factor_mismatch_sin_soiling_cuando_motor_activo():
    src = _leer(_PAGINA_6)
    idx = src.index("factor_pr = st.session_state.get(")
    bloque = src[idx: idx + 200]
    assert "factor_mismatch_sin_soiling" in bloque
    assert "factor_global_mismatch" in bloque
    assert "_motor_ok" in bloque


# ══════════════════════════════════════════════════════════════════════════
# Objetivo 1 — vigencia de produccion_ok
# ══════════════════════════════════════════════════════════════════════════

def test_pagina6_importa_firma_de_produccion():
    src = _leer(_PAGINA_6)
    assert "calcular_produccion_run_signature_v1" in src
    assert "determinar_source_mode" in src


def test_pagina6_guarda_firma_al_simular_antes_de_marcar_produccion_ok():
    lineas = _lineas(_PAGINA_6)
    idx_firma_calculada = next(
        (i for i, ln in enumerate(lineas)
         if "_firma_produccion = _firma_produccion_config_actual()" in ln), None
    )
    idx_produccion_ok_true = next(
        (i for i, ln in enumerate(lineas)
         if ln.strip() == 'st.session_state["produccion_ok"]          = True'), None
    )
    assert idx_firma_calculada is not None, (
        "Página 6 debe calcular la firma justo después de simular."
    )
    assert idx_produccion_ok_true is not None
    assert idx_firma_calculada < idx_produccion_ok_true


def test_pagina6_valida_firma_antes_de_usar_res_en_rama_reutilizada():
    """En la rama `else` (produccion_ok=True sin volver a pulsar Simular),
    la comparación de firmas debe ejecutarse ANTES de `if not res:
    st.stop()` -- que es el primer punto donde `res` se usa para renderizar
    algo. Si la firma no coincide, la rama hace st.stop() antes de llegar
    ahí con datos obsoletos."""
    lineas = _lineas(_PAGINA_6)
    idx_else = next(
        (i for i, ln in enumerate(lineas) if ln.rstrip() == "    else:"), None
    )
    idx_comparacion = next(
        (i for i, ln in enumerate(lineas)
         if "_firma_guardada != _firma_actual" in ln), None
    )
    idx_not_res_stop = next(
        (i for i, ln in enumerate(lineas) if ln.strip() == "if not res:"), None
    )
    assert idx_else is not None
    assert idx_comparacion is not None, (
        "Página 6 debe comparar _firma_guardada contra _firma_actual en la "
        "rama de reutilización."
    )
    assert idx_not_res_stop is not None
    assert idx_else < idx_comparacion < idx_not_res_stop, (
        "La validación de vigencia debe ejecutarse ANTES de que `res` se dé "
        "por bueno para renderizar (if not res: st.stop())."
    )


def test_pagina6_rechazo_de_vigencia_limpia_produccion_ok_y_energia():
    """El bloque de rechazo (firma no coincide) debe limpiar produccion_ok,
    E_ac_anual_kWh y produccion_run_signature_v1 -- no solo mostrar un
    error."""
    src = _leer(_PAGINA_6)
    idx = src.index("_firma_guardada != _firma_actual")
    bloque = src[idx: idx + 900]
    assert '"produccion_ok"] = False' in bloque
    assert "st.stop()" in bloque
    assert '"E_ac_anual_kWh"' in bloque
    assert '"produccion_run_signature_v1"' in bloque


# ══════════════════════════════════════════════════════════════════════════
# Objetivo 3/4 — vigencia y cero de bypass en Producción
# ══════════════════════════════════════════════════════════════════════════

def test_pagina6_importa_piezas_de_vigencia_de_bypass():
    src = _leer(_PAGINA_6)
    assert "calcular_bypass_run_signature_v1" in src
    assert "seleccionar_poa_bypass" in src


def test_pagina6_bypass_ok_efectivo_depende_de_la_firma():
    """`_bypass_ok` (el nombre que consume el resto de la sección) debe
    quedar definido como `_bypass_ok_raw and _bypass_vigente` -- no como el
    valor crudo de session_state["bypass_ok"]."""
    src = _leer(_PAGINA_6)
    assert "_bypass_ok  = _bypass_ok_raw and _bypass_vigente" in src


def test_pagina6_bypass_cero_o_no_vigente_limpia_energia_bypass_pero_no_bypass_result():
    """El `else` del bloque `if _bypass_ok and kwh_bypass > 0:` (el que
    guarda E_ac_anual_kWh_bypass -- hay otro `if` idéntico antes, para el
    waterfall, que no lleva else propio) debe hacer pop() de
    E_ac_anual_kWh_bypass/kwh_bypass_anual -- y NO debe tocar bypass_ok ni
    bypass_result (esos se conservan para trazabilidad, ver Objetivo
    "Bypass cero")."""
    lineas = _lineas(_PAGINA_6)
    idx_if = next(
        (i for i, ln in enumerate(lineas)
         if ln.strip() == "if _bypass_ok and kwh_bypass > 0:"
         and 'st.session_state["E_ac_anual_kWh_bypass"]' in "".join(lineas[i:i + 15])),
        None,
    )
    assert idx_if is not None
    # Buscar el "else:" correspondiente a ese if (misma indentación: 4 espacios).
    idx_else = next(
        (i for i in range(idx_if, len(lineas)) if lineas[i].rstrip() == "    else:"), None
    )
    assert idx_else is not None, (
        "Debe existir un else: al mismo nivel para limpiar bypass cero / no vigente."
    )
    bloque_else = "".join(lineas[idx_else: idx_else + 10])
    assert '"E_ac_anual_kWh_bypass"' in bloque_else
    assert '"kwh_bypass_anual"' in bloque_else
    assert '"bypass_ok"' not in bloque_else
    assert '"bypass_result"' not in bloque_else


def test_pagina6_reconstruye_bypass_con_su_propia_configuracion_no_con_lo_registrado():
    """La reconstrucción de la firma esperada debe usar _n_serie_cfg /
    N_paneles (config VIGENTE de Producción) para N_series/N_parallel, no
    los valores bypass_n_series_usado/bypass_n_parallel_usado que Página 5
    registró -- de lo contrario la comparación sería tautológica (siempre
    coincidiría) y nunca detectaría una topología distinta."""
    src = _leer(_PAGINA_6)
    idx = src.index("calcular_bypass_run_signature_v1(")
    llamada = src[idx: idx + 700]
    assert "_n_serie_cfg" in llamada
    assert "_n_par_bp_prod" in llamada
    assert "bypass_n_series_usado" not in llamada
    assert "bypass_n_parallel_usado" not in llamada


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
