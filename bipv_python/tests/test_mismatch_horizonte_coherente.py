# -*- coding: utf-8 -*-
"""Spec ``05-perdidas-y-temperatura/mismatch-horizonte-coherente`` (29-sep-2026).

Auditoría de 🔀 Mismatch: el horizonte se contaba dos veces con el bypass,
borraba también la luz difusa (1.85 % en vez de 0.93 % con 15°), llegaba a
Producción como un factor anual aplicado a todas las horas, y la suciedad,
la cascada y los resultados viejos no mostraban lo que Producción aplicaba.
Cada prueba termina en lo que recibe el motor de 📊 Producción.
"""
import os

import numpy as np
import pandas as pd
import pytest

from calculos.mismatch import (
    CLAVE_VERSION_MISMATCH,
    DEFAULTS_MISMATCH,
    VERSION_MISMATCH,
    aplicar_factor_horario,
    calcular_sombreado_horizonte,
    cascada_perdidas,
    factor_global_perdidas,
    factor_horizonte_horario,
    factores_mismatch_produccion,
    firma_horizonte,
    publicar_cascada_mismatch,
)
from calculos.mismatch_bypass import excluir_horas_horizonte
from calculos.solar import calcular_poa
from tests.test_simulation_pipeline import _tmy_sintetico_offline

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAG5 = os.path.join(_ROOT, "pages", "5_🔀_Mismatch.py")
_PAG6 = os.path.join(_ROOT, "pages", "6_📊_Produccion.py")
_PAG10 = os.path.join(_ROOT, "pages", "10_📄_Reporte_PDF.py")
LAT, LON, ALT = 7.883, -76.6259, 44
HORIZONTE_15 = [(0, 15), (90, 15), (180, 15), (270, 15)]
_BIFACIAL = {"bifacialidad": 0.80, "altura_m": 1.0, "gcr": 0.4, "ancho_colector_m": 2.4}


def _src(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def tmy():
    return _tmy_sintetico_offline(LAT, LON, ALT)


@pytest.fixture(scope="module")
def poa(tmy):
    return calcular_poa(tmy, LAT, LON, ALT, 10, 180)


@pytest.fixture(scope="module")
def poa_bif(tmy):
    return calcular_poa(tmy, LAT, LON, ALT, 10, 180, bifacial=_BIFACIAL)


@pytest.fixture(scope="module")
def sombra(tmy, poa):
    return calcular_sombreado_horizonte(LAT, LON, ALT, tmy, poa, HORIZONTE_15)


def _estado_publicado(sombra, *, motor_ok=False, pct_soiling=0.0, mm_or=0.0, sombra_ok=True):
    estado = {"res_sombra": sombra, "sombra_ok": sombra_ok,
              "res_mismatch_or": {"factor_mismatch_pct": mm_or}}
    poa_anual = 2000.0
    publicar_cascada_mismatch(estado, poa_anual=poa_anual, pct_soiling=pct_soiling, motor_ok=motor_ok)
    return estado


# ── Criterio 1: el horizonte solo quita la luz directa frontal ───────────────
def test_horizonte_quita_solo_la_directa(poa, sombra):
    m = sombra["mascara_sombra"].to_numpy()
    tot = float(poa["poa_global"].sum())
    esperado = float(poa["poa_direct"].to_numpy()[m].sum()) / tot
    assert sombra["solo_directa"] is True
    assert sombra["factor_sombra_anual"] == pytest.approx(esperado, abs=1e-4)
    assert 0.008 < sombra["factor_sombra_anual"] < 0.011       # ≈ 0.93 %, no 1.85 %
    f = sombra["factor_horario"].to_numpy()
    assert np.all(f[~m] == 1.0)                                 # horas sin sombra intactas
    g = poa["poa_global"].to_numpy()
    d = poa["poa_direct"].to_numpy()
    ok = m & (g > 0)
    np.testing.assert_allclose(f[ok], 1 - np.minimum(d[ok], g[ok]) / g[ok])


def test_horizonte_sin_poa_direct_quita_toda_la_poa(tmy, poa):
    solo_global = poa[["poa_global"]].copy()
    r = calcular_sombreado_horizonte(LAT, LON, ALT, tmy, solo_global, HORIZONTE_15)
    assert r["solo_directa"] is False
    assert r["factor_sombra_anual"] > 0.017                     # comportamiento anterior


def test_horizonte_bifacial_no_toca_la_trasera(tmy, poa_bif):
    r = calcular_sombreado_horizonte(LAT, LON, ALT, tmy, poa_bif, HORIZONTE_15)
    nueva = aplicar_factor_horario(poa_bif, r["factor_horario"].to_numpy())
    trasera_antes = (poa_bif["poa_global"] - poa_bif["poa_front"]).to_numpy()
    trasera_despues = (nueva["poa_global"] - nueva["poa_front"]).to_numpy()
    np.testing.assert_allclose(trasera_despues, trasera_antes, atol=1e-9)


def test_firma_horizonte_cambia_con_puntos_y_poa(poa):
    a = firma_horizonte(HORIZONTE_15, poa)
    assert a == firma_horizonte(list(reversed(HORIZONTE_15)), poa)
    assert a != firma_horizonte([(0, 15)], poa)
    otra = poa.copy()
    otra["poa_global"] = otra["poa_global"] * 1.01
    assert a != firma_horizonte(HORIZONTE_15, otra)


def test_factor_horario_desde_la_mascara(poa, sombra):
    np.testing.assert_allclose(
        factor_horizonte_horario(sombra["mascara_sombra"], poa),
        sombra["factor_horario"].to_numpy())


# ── Criterio 2: lo que recibe Producción ─────────────────────────────────────
def test_publicacion_escalar_sin_horizonte(sombra):
    e = _estado_publicado(sombra, pct_soiling=2.0, mm_or=1.0)
    assert e[CLAVE_VERSION_MISMATCH] == VERSION_MISMATCH
    assert e["factor_global_mismatch"] == pytest.approx(0.99 * 0.98, abs=1e-4)
    assert e["factor_mismatch_sin_soiling"] == pytest.approx(0.99, abs=1e-4)
    assert e["factor_sombra_anual"] == sombra["factor_sombra_anual"]
    assert e["pct_soiling_cascada"] == 2.0 and e["mismatch_ok"] is True
    # la cascada visible sí muestra el horizonte
    etapas = [r["etapa"] for r in e["cascada_mismatch"]]
    assert any("horizonte" in x.lower() for x in etapas)


@pytest.mark.parametrize("motor_ok", [False, True])
def test_produccion_recibe_horizonte_hora_a_hora(poa, sombra, motor_ok):
    e = _estado_publicado(sombra, motor_ok=motor_ok, pct_soiling=2.0)
    r = factores_mismatch_produccion(e, poa, motor_ok)
    assert r["legado"] is False
    esperado_escalar = e["factor_mismatch_sin_soiling" if motor_ok else "factor_global_mismatch"]
    assert r["factor_escalar"] == esperado_escalar
    np.testing.assert_allclose(r["factor_horario"], sombra["factor_horario"].to_numpy())


def test_sin_mismatch_ok_no_aplica_nada(poa):
    r = factores_mismatch_produccion({}, poa, False)
    assert r["factor_escalar"] == 1.0 and r["factor_horario"] is None


def test_sin_horizonte_ni_bifacial_no_hay_factor_horario(poa, tmy):
    vacio = calcular_sombreado_horizonte(LAT, LON, ALT, tmy, poa, [])
    e = _estado_publicado(vacio, pct_soiling=2.0)
    r = factores_mismatch_produccion(e, poa, False)
    assert r["factor_horario"] is None


def test_mascara_desalineada_no_aplica_y_avisa(poa, sombra):
    e = _estado_publicado(sombra)
    corto = dict(sombra, mascara_sombra=sombra["mascara_sombra"].iloc[:100])
    e["res_sombra"] = corto
    r = factores_mismatch_produccion(e, poa, False)
    assert r["factor_horario"] is None and r["avisos"]


# ── Criterio 3: bypass sin horas de horizonte ────────────────────────────────
def test_bypass_excluye_horas_de_horizonte():
    idx = pd.date_range("2023-01-01", periods=24, freq="h", tz="UTC")
    fs3d = pd.Series(0.4, index=idx)
    mask = pd.Series([True] * 6 + [False] * 18, index=idx)
    p, info = excluir_horas_horizonte(fs3d, mask)
    assert (p.iloc[:6] == 0.0).all() and (p.iloc[6:] == 0.4).all()
    assert info["horas_excluidas"] == 6
    with pytest.raises(ValueError):
        excluir_horas_horizonte(fs3d, mask.iloc[:10])


def test_pagina5_bypass_usa_exclusion_y_no_la_casilla():
    src = _src(_PAG5)
    assert "excluir_horas_horizonte(" in src
    assert "bypass_incluir_horizonte" not in src
    assert "combinar_fs_con_horizonte(" not in src


# ── Criterio 4: estado de una versión anterior ───────────────────────────────
@pytest.mark.parametrize("motor_ok", [False, True])
def test_estado_legado_igual_que_antes(poa, sombra, motor_ok):
    legado = {"mismatch_ok": True, "sombra_ok": True, "res_sombra": sombra,
              "factor_global_mismatch": 0.9551, "factor_mismatch_sin_soiling": 0.9812,
              "factor_sombra_anual": 0.0188}
    r = factores_mismatch_produccion(legado, poa, motor_ok)
    assert r["legado"] is True and r["factor_horario"] is None
    assert r["factor_escalar"] == (0.9812 if motor_ok else 0.9551)
    assert r["avisos"]                                           # pide recalcular


# ── Criterio 5: suciedad con Motor Óptico ────────────────────────────────────
def test_cascada_con_motor_no_resta_suciedad(sombra):
    e = _estado_publicado(sombra, motor_ok=True, pct_soiling=3.0)
    fila = next(r for r in e["cascada_mismatch"] if "uciedad" in r["etapa"])
    assert fila["perdida"] == 0.0 and "Motor Óptico" in fila["etapa"]
    # el factor para cuando no hay Motor Óptico sí la conserva
    assert e["factor_global_mismatch"] == pytest.approx(0.97, abs=1e-4)


def test_pagina5_deshabilita_suciedad_con_motor():
    src = _src(_PAG5)
    assert "disabled=_motor_ok_mm" in src


# ── Criterio 6: cascada sin filas eléctricas en 0 ────────────────────────────
def test_cascada_sin_filas_en_cero(sombra):
    e = _estado_publicado(sombra, pct_soiling=2.0)
    etapas = [r["etapa"] for r in e["cascada_mismatch"]]
    assert "Mismatch fabricación" not in etapas and "Cableado DC" not in etapas
    src = _src(_PAG5)
    assert "Factor global PR" not in src
    assert "Factor sobre la irradiancia" in src
    assert "Pérdidas que 📊 Producción aplica sobre la potencia" in src


# ── Criterio 7: vigencia ─────────────────────────────────────────────────────
def test_pagina5_recalcula_si_cambian_datos():
    src = _src(_PAG5)
    assert "firma_horizonte(puntos_horizonte, poa_base)" in src
    assert '_res_or_prev.get("configs") != configs' in src
    assert 'st.session_state["mismatch_or_ok"] = False' in src


# ── Criterio 8: valores por defecto y aviso en Producción ────────────────────
def test_defaults_en_un_solo_lugar():
    assert DEFAULTS_MISMATCH == {"pct_calidad_modulo": 0.0, "pct_mismatch_fab": 1.0,
                                 "pct_soiling": 2.0, "pct_cableado": 1.5, "pct_cableado_ac": 0.0}
    assert "DEFAULTS_MISMATCH[" in _src(_PAG5)


def test_produccion_avisa_si_mismatch_no_se_abrio():
    src = _src(_PAG6)
    assert "factores_mismatch_produccion(" in src
    assert "aplicar_factor_horario(" in src
    assert "🔀 Mismatch no se ha abierto" in src
    assert 'st.session_state["factor_mismatch_aplicado"]' in src
    # el horizonte entra a la POA ANTES de la firma y de la simulación
    assert src.index("aplicar_factor_horario(") < src.index("def _payload_y_firma_produccion_config_actual")


def test_reporte_muestra_el_factor_aplicado():
    assert 'st.session_state.get("factor_mismatch_aplicado"' in _src(_PAG10)


# ── Criterio 9: bifacial sin Motor Óptico ────────────────────────────────────
def test_bifacial_sin_motor_suciedad_solo_frontal(tmy, poa_bif):
    vacio = calcular_sombreado_horizonte(LAT, LON, ALT, tmy, poa_bif, [])
    e = _estado_publicado(vacio, pct_soiling=5.0)
    r = factores_mismatch_produccion(e, poa_bif, False)
    g = poa_bif["poa_global"].to_numpy()
    front = poa_bif["poa_front"].to_numpy()
    final = g * r["factor_horario"] * r["factor_escalar"]
    np.testing.assert_allclose(final, g - 0.05 * front, atol=1e-3)


def test_bifacial_sin_motor_horizonte_y_suciedad_exactos(tmy, poa_bif):
    """Detectado en la verificación de punta a punta con las páginas: la
    suciedad debe actuar sobre la cara frontal que queda tras el horizonte."""
    r_h = calcular_sombreado_horizonte(LAT, LON, ALT, tmy, poa_bif, HORIZONTE_15)
    e = _estado_publicado(r_h, pct_soiling=2.0)
    r = factores_mismatch_produccion(e, poa_bif, False)
    g = poa_bif["poa_global"].to_numpy()
    m = r_h["mascara_sombra"].to_numpy()
    d = np.where(m, np.minimum(poa_bif["poa_direct"].to_numpy(), g), 0.0)
    esperado = g - d - 0.02 * (poa_bif["poa_front"].to_numpy() - d)
    np.testing.assert_allclose(g * r["factor_horario"] * r["factor_escalar"], esperado, atol=1e-9)


# ── Punta a punta: estado publicado → motor de Producción ────────────────────
@pytest.fixture(scope="module")
def panel():
    from datos.catalogo_paneles_excel import cargar_catalogo_paneles
    cat = cargar_catalogo_paneles()
    nombre = next(k for k in cat if "JAM66D46-720" in k)
    return dict(cat[nombre])


def test_punta_a_punta_horizonte_una_sola_vez(tmy, poa, sombra, panel):
    from calculos.produccion import simular_produccion_anual
    e = _estado_publicado(sombra, pct_soiling=0.0)
    r = factores_mismatch_produccion(e, poa, False)
    poa_prod = aplicar_factor_horario(poa, r["factor_horario"])
    res = simular_produccion_anual(tmy, poa_prod, panel, 28, 0.98, r["factor_escalar"])
    # Referencia física a mano: quitar la luz directa en las horas bloqueadas
    m = sombra["mascara_sombra"].to_numpy()
    ref = poa.copy()
    ref["poa_global"] = poa["poa_global"] - np.where(m, np.minimum(poa["poa_direct"], poa["poa_global"]), 0.0)
    res_ref = simular_produccion_anual(tmy, ref, panel, 28, 0.98, 1.0)
    assert res["E_ac_anual_kWh"] == pytest.approx(res_ref["E_ac_anual_kWh"], rel=1e-9)
    # y el camino anterior (factor anual de toda la POA) perdía de más
    res_viejo = simular_produccion_anual(tmy, poa, panel, 28, 0.98, 1 - 0.0185)
    assert res_viejo["E_ac_anual_kWh"] < res["E_ac_anual_kWh"]


def test_punta_a_punta_sin_horizonte_misma_energia_y_factor(tmy, poa, panel):
    """Sin horizonte, una orientación y monofacial: igual que antes."""
    from calculos.produccion import simular_produccion_anual
    vacio = calcular_sombreado_horizonte(LAT, LON, ALT, tmy, poa, [])
    e = _estado_publicado(vacio, pct_soiling=2.0, mm_or=0.0)
    r = factores_mismatch_produccion(e, poa, False)
    antes = factor_global_perdidas(cascada_perdidas(2000.0, 0.0, 0.0, 0.0, 2.0, 0.0))
    assert r["factor_escalar"] == antes and r["factor_horario"] is None
    a = simular_produccion_anual(tmy, poa, panel, 28, 0.98, antes)
    b = simular_produccion_anual(tmy, poa, panel, 28, 0.98, r["factor_escalar"])
    assert a["E_ac_anual_kWh"] == b["E_ac_anual_kWh"]


# ── Criterio 11: manual del Asistente ────────────────────────────────────────
@pytest.mark.parametrize("pregunta, texto", [
    ("como calcula la app la sombra del horizonte en mismatch", "0,93 %"),
    ("el horizonte se cuenta dos veces con el bypass", "una sola vez"),
    ("por que la suciedad de mismatch esta deshabilitada", "Motor Óptico"),
])
def test_manual_explica_horizonte(pregunta, texto):
    from calculos.asistente import BaseConocimiento
    secciones = BaseConocimiento.cargar().buscar(pregunta, k=6)
    candidatas = [s for s in secciones if "horizonte y cascada de mismatch" in s["titulo"].lower()]
    assert candidatas, [s["titulo"] for s in secciones]
    assert texto in "\n".join(s["texto"] for s in candidatas)
