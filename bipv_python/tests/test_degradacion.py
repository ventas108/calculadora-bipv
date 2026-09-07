# -*- coding: utf-8 -*-
"""Tests de calculos/degradacion.py -- degradación no lineal (curva real de
garantía del fabricante), 7-sep-2026. Ver el módulo para contexto completo."""
import pytest

from calculos.degradacion import (
    factor_geometrico,
    factor_curva_fabricante,
    factor_tabla_fabricante,
    resolver_factor_degradacion,
)
from calculos.financiero import calcular_flujo_caja


# ─── factor_geometrico -- retrocompatibilidad exacta con el modelo histórico ──

def test_geometrico_anio1_sin_degradacion():
    assert factor_geometrico(1, tasa_pct=0.5) == pytest.approx(1.0)


def test_geometrico_calculado_a_mano():
    # (1 - 0.5/100)**(5-1) = 0.995**4 = 0.98015...
    assert factor_geometrico(5, tasa_pct=0.5) == pytest.approx(0.995 ** 4)


def test_geometrico_tasa_cero_nunca_degrada():
    for anio in (1, 10, 25):
        assert factor_geometrico(anio, tasa_pct=0.0) == pytest.approx(1.0)


# ─── factor_curva_fabricante -- modelo real de 2 tramos (LID + lineal) ────────

def test_curva_fabricante_anio1_es_solo_la_caida_lid():
    # Ficha típica: 2.5% LID año 1, 0.55%/año después.
    assert factor_curva_fabricante(1, caida_anio1_pct=2.5, tasa_lineal_pct_anio=0.55) == pytest.approx(0.975)


def test_curva_fabricante_calculado_a_mano_anio10():
    # nivel_post_lid = 0.975; año 10 -> 0.975 - 0.55/100 * 9 = 0.975 - 0.0495 = 0.9255
    f = factor_curva_fabricante(10, caida_anio1_pct=2.5, tasa_lineal_pct_anio=0.55)
    assert f == pytest.approx(0.975 - 0.0055 * 9)


def test_curva_fabricante_anio25_coincide_con_ficha_real_tier1_tipica():
    # Ficha típica de garantía lineal Tier 1 (ej. Trina/Canadian): ≤2.0% año 1,
    # ≤0.55%/año después -> piso ≥84.8% al año 25 (calculado a mano:
    # 0.98 - 0.0055*24 = 0.848).
    f = factor_curva_fabricante(25, caida_anio1_pct=2.0, tasa_lineal_pct_anio=0.55)
    assert f == pytest.approx(0.848, abs=0.001)


def test_curva_fabricante_sin_lid_reduce_al_caso_lineal_puro():
    assert factor_curva_fabricante(1, caida_anio1_pct=0.0, tasa_lineal_pct_anio=0.5) == pytest.approx(1.0)
    assert factor_curva_fabricante(11, caida_anio1_pct=0.0, tasa_lineal_pct_anio=0.5) == pytest.approx(0.95)


# ─── factor_tabla_fabricante -- interpolación entre puntos reales publicados ──

def test_tabla_fabricante_punto_exacto():
    tabla = {1: 98.0, 10: 91.0, 25: 84.8}
    assert factor_tabla_fabricante(10, tabla) == pytest.approx(0.91)


def test_tabla_fabricante_interpolacion_calculada_a_mano():
    tabla = {1: 98.0, 10: 91.0, 25: 84.8}
    # año 5, entre (1, 98.0) y (10, 91.0): frac = 4/9
    esperado = (98.0 + (4 / 9) * (91.0 - 98.0)) / 100.0
    assert factor_tabla_fabricante(5, tabla) == pytest.approx(esperado)


def test_tabla_fabricante_fuera_de_rango_extrapola_ultimo_tramo():
    tabla = {1: 98.0, 10: 91.0, 25: 84.8}
    # año 30: extrapola con el tramo (10, 91.0) -> (25, 84.8)
    esperado = (91.0 + ((30 - 10) / (25 - 10)) * (84.8 - 91.0)) / 100.0
    assert factor_tabla_fabricante(30, tabla) == pytest.approx(esperado)


def test_tabla_fabricante_vacia_lanza_error_nunca_inventa():
    with pytest.raises(ValueError):
        factor_tabla_fabricante(10, {})


# ─── resolver_factor_degradacion -- despachador, nunca falla en silencio ──────

def test_resolver_config_none_no_degrada():
    r = resolver_factor_degradacion(10, None)
    assert r["factor"] == pytest.approx(1.0)
    assert r["modo_usado"] == "geometrica"
    assert r["fallback"] is False


def test_resolver_geometrica_explicita():
    r = resolver_factor_degradacion(5, {"modo": "geometrica", "tasa_pct": 0.5})
    assert r["factor"] == pytest.approx(factor_geometrico(5, 0.5))
    assert r["fallback"] is False


def test_resolver_curva_fabricante_completa():
    r = resolver_factor_degradacion(
        10, {"modo": "curva_fabricante", "caida_anio1_pct": 2.5, "tasa_lineal_pct_anio": 0.55}
    )
    assert r["modo_usado"] == "curva_fabricante"
    assert r["fallback"] is False
    assert r["factor"] == pytest.approx(factor_curva_fabricante(10, 2.5, 0.55))


def test_resolver_curva_fabricante_sin_datos_cae_a_geometrica_y_avisa():
    r = resolver_factor_degradacion(10, {"modo": "curva_fabricante", "tasa_pct": 0.4})
    assert r["modo_usado"] == "geometrica"
    assert r["fallback"] is True
    assert r["factor"] == pytest.approx(factor_geometrico(10, 0.4))


def test_resolver_tabla_fabricante_completa():
    tabla = {1: 98.0, 25: 84.8}
    r = resolver_factor_degradacion(1, {"modo": "tabla_fabricante", "tabla_anio_pct": tabla})
    assert r["modo_usado"] == "tabla_fabricante"
    assert r["fallback"] is False
    assert r["factor"] == pytest.approx(0.98)


def test_resolver_tabla_fabricante_sin_datos_cae_a_geometrica_y_avisa():
    r = resolver_factor_degradacion(10, {"modo": "tabla_fabricante", "tasa_pct": 0.4})
    assert r["modo_usado"] == "geometrica"
    assert r["fallback"] is True


def test_resolver_medida_campo_usa_geometrico_con_tasa_medida():
    r = resolver_factor_degradacion(10, {"modo": "medida_campo", "tasa_pct": 0.7})
    assert r["modo_usado"] == "medida_campo"
    assert r["factor"] == pytest.approx(factor_geometrico(10, 0.7))


def test_resolver_modo_desconocido_cae_a_geometrica():
    r = resolver_factor_degradacion(5, {"modo": "algo_inventado", "tasa_pct": 0.3})
    assert r["modo_usado"] == "geometrica"
    assert r["fallback"] is True
    assert r["factor"] == pytest.approx(factor_geometrico(5, 0.3))


# ─── Integración con calcular_flujo_caja() -- cero regresión ──────────────────

def test_flujo_caja_sin_config_degradacion_es_identico_al_historico():
    """El caso más importante: config_degradacion=None debe dar EXACTAMENTE
    el mismo resultado que antes de este cambio -- ningún proyecto/informe
    ya entregado puede cambiar de cifra por este trabajo."""
    kwargs = dict(
        capex_usd=100_000.0,
        beneficios_1715_usd=20_000.0,
        e_ac_kWh_anual=150_000.0,
        tarifa_cop_kWh=950.0,
        tipo_cambio=3900.0,
        tasa_escalacion_tarifa=3.0,
        tasa_degradacion_pct=0.5,
        opex_pct_capex=1.5,
        n_anos=25,
    )
    flujos_sin_config = calcular_flujo_caja(**kwargs)
    flujos_con_config_none = calcular_flujo_caja(**kwargs, config_degradacion=None)
    flujos_con_config_geometrica_explicita = calcular_flujo_caja(
        **kwargs, config_degradacion={"modo": "geometrica", "tasa_pct": 0.5}
    )
    for a, b, c in zip(flujos_sin_config, flujos_con_config_none, flujos_con_config_geometrica_explicita):
        assert a["produccion_kWh"] == b["produccion_kWh"] == c["produccion_kWh"]
        assert a["flujo_usd"] == b["flujo_usd"] == c["flujo_usd"]


def test_flujo_caja_con_curva_fabricante_produce_energia_distinta_a_geometrica():
    """Verifica que activar el modo real de curva de fabricante SÍ cambia
    la energía proyectada (si no cambiara nada, la feature no serviría)."""
    kwargs = dict(
        capex_usd=100_000.0,
        beneficios_1715_usd=0.0,
        e_ac_kWh_anual=150_000.0,
        tarifa_cop_kWh=950.0,
        tipo_cambio=3900.0,
        tasa_escalacion_tarifa=0.0,
        tasa_degradacion_pct=0.5,
        opex_pct_capex=0.0,
        n_anos=25,
    )
    flujos_geom = calcular_flujo_caja(**kwargs)
    flujos_curva = calcular_flujo_caja(
        **kwargs,
        config_degradacion={"modo": "curva_fabricante", "caida_anio1_pct": 2.5, "tasa_lineal_pct_anio": 0.55},
    )
    # Año 1: geométrico no degrada nada; curva real sí tiene la caída LID.
    assert flujos_geom[1]["produccion_kWh"] > flujos_curva[1]["produccion_kWh"]
    # Año 25: la curva real (piso ~87.4%) debe dar menos energía que un
    # 0.5%/año geométrico compuesto 24 veces (~0.995**24 ≈ 88.6%).
    assert flujos_curva[25]["produccion_kWh"] < flujos_geom[25]["produccion_kWh"]
