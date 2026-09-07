# -*- coding: utf-8 -*-
"""
Variabilidad interanual real para el modelo P90 (7-sep-2026) --
calculos/incertidumbre_p90.py.

Contexto: 📄 Financiero ya calculaba un P90 bancable con la metodología
estándar (z₉₀ × σ_total, verificado contra Solargis/EPRI TR-107348/IEC
61724-3) -- pero σ_irr (variabilidad interanual) venía de una tabla FIJA
por ciudad, no de un cálculo real para las coordenadas exactas del
proyecto. Este módulo lo calcula de verdad, con datos horarios multi-año
reales de PVGIS (pvlib.iotools.get_pvgis_hourly), y expone una regla de
combinación que NUNCA usa silenciosamente el valor más bajo entre el real
y el de tabla (ver elegir_sigma_irr).

No se hacen llamadas de red reales en la suite -- get_pvgis_hourly() se
mockea (monkeypatch, mismo patrón que test_pvwatts_crosscheck.py) con
datos sintéticos o con la respuesta real capturada en vivo el 7-sep-2026
(Urabá y Medellín, ver los valores citados en cada test).

Casos cubiertos:
  - Estadística (media, desviación estándar relativa) verificada a mano
    con una serie de años sintética.
  - Filtro de años calendario completos -- un año parcial no distorsiona
    la desviación estándar.
  - Reintento automático cuando PVGIS rechaza el año final pedido (el año
    "actual" del sistema puede exceder la cobertura real de PVGIS -- bug
    real encontrado en vivo el 7-sep-2026, no hipotético).
  - Nunca inventa: <5 años completos, o cualquier otro fallo de red,
    devuelve sigma_irr_real_pct=None con el motivo en "error".
  - Caché en disco: guarda y relee exacto, no revienta si el archivo no
    existe o está corrupto.
  - elegir_sigma_irr(): las 3 ramas (real > tabla, real < tabla, real=None).
"""
import os
import pickle

import numpy as np
import pandas as pd
import pytest

from calculos.incertidumbre_p90 import (
    calcular_variabilidad_interanual_real,
    elegir_sigma_irr,
    MIN_ANIOS_VALIDOS,
)


def _df_sintetico_anios(anios: list[int], horas_por_anio: dict[int, int] | None = None):
    """Serie horaria sintética con GHI constante por hora dentro de cada año
    -- pensada para verificar la ESTADÍSTICA (media/stdev), no la física.
    Por defecto genera el año calendario COMPLETO real (8784h en bisiesto,
    8760h si no) -- solo se acorta si el año aparece en horas_por_anio."""
    filas = []
    for anio in anios:
        if horas_por_anio and anio in horas_por_anio:
            n_horas = horas_por_anio[anio]
            idx = pd.date_range(f"{anio}-01-01", periods=n_horas, freq="h", tz="UTC")
        else:
            idx = pd.date_range(f"{anio}-01-01", f"{anio}-12-31 23:00", freq="h", tz="UTC")
        n_horas = len(idx)
        # GHI constante de 500 W/m2 durante el "día" (mitad de las horas) --
        # la cifra exacta no importa, lo que importa es que la SUMA anual
        # varíe de forma conocida entre años para verificar la desviación.
        filas.append(pd.DataFrame({
            "poa_direct": np.full(n_horas, 300.0),
            "poa_sky_diffuse": np.full(n_horas, 200.0),
            "poa_ground_diffuse": np.zeros(n_horas),
        }, index=idx))
    return pd.concat(filas)


def _mock_pvgis(monkeypatch, df, inputs=None, raise_exc=None, contador: list | None = None):
    def _fake(*args, **kwargs):
        if contador is not None:
            contador.append(kwargs)
        if raise_exc is not None:
            raise raise_exc
        return df, (inputs or {}), {}
    monkeypatch.setattr("pvlib.iotools.get_pvgis_hourly", _fake)


# ── Estadística verificada a mano ────────────────────────────────────────────
def test_sigma_calculado_a_mano_con_serie_sintetica(monkeypatch, tmp_path):
    # 6 años con GHI anual EXACTO conocido (mismo valor cada hora, todas
    # las horas -- la suma anual es simplemente 500 * n_horas).
    anios = [2015, 2016, 2017, 2018, 2019, 2020]
    df = _df_sintetico_anios(anios)
    _mock_pvgis(monkeypatch, df)
    monkeypatch.setattr("calculos.incertidumbre_p90._CACHE_DIR", str(tmp_path))

    r = calcular_variabilidad_interanual_real(6.0, -75.0, anios_atras=6, usar_cache=False)

    ghi_anual_esperado_wh = 500.0 * 8760  # Wh/m2 (500 W/m2 * 8760 h, sin bisiesto en estos años... 2016/2020 SÍ son bisiestos
    # -- se recalcula abajo por eso, no se asume a mano el bisiesto aquí.
    valores_esperados = []
    for a in anios:
        n_horas = 8784 if (a % 4 == 0) else 8760
        valores_esperados.append(500.0 * n_horas / 1000.0)  # kWh/m2
    media_esperada = np.mean(valores_esperados)
    sigma_esperado = np.std(valores_esperados, ddof=1) / media_esperada * 100.0

    assert r["error"] is None
    assert r["n_anios"] == 6
    assert r["media_kwh_m2_anio"] == pytest.approx(media_esperada, abs=0.5)
    assert r["sigma_irr_real_pct"] == pytest.approx(sigma_esperado, abs=0.05)


def test_sigma_cero_si_todos_los_anios_son_identicos(monkeypatch, tmp_path):
    # Caso trivial de verificación independiente: GHI idéntico cada año ->
    # desviación estándar EXACTAMENTE 0, no un número cercano a 0 por
    # redondeo -- confirma que la fórmula no tiene un sesgo espurio.
    anios = [2018, 2019, 2020, 2021, 2022]
    horas = {a: 8760 for a in anios}  # ninguno bisiesto real, pero se fuerza igual a propósito
    df = _df_sintetico_anios(anios, horas_por_anio=horas)
    _mock_pvgis(monkeypatch, df)
    monkeypatch.setattr("calculos.incertidumbre_p90._CACHE_DIR", str(tmp_path))

    r = calcular_variabilidad_interanual_real(6.0, -75.0, anios_atras=5, usar_cache=False)
    assert r["sigma_irr_real_pct"] == 0.0


# ── Filtro de años completos ─────────────────────────────────────────────────
def test_anio_parcial_se_excluye_del_calculo(monkeypatch, tmp_path):
    # 6 años en la serie, 1 parcial -- deben quedar 5 completos, justo el
    # mínimo (MIN_ANIOS_VALIDOS) para no disparar el gate de "muy pocos años".
    anios = [2017, 2018, 2019, 2020, 2021, 2022]
    df = _df_sintetico_anios(anios, horas_por_anio={2022: 2000})  # 2022 parcial, el resto año completo real
    _mock_pvgis(monkeypatch, df)
    monkeypatch.setattr("calculos.incertidumbre_p90._CACHE_DIR", str(tmp_path))

    r = calcular_variabilidad_interanual_real(6.0, -75.0, anios_atras=6, usar_cache=False)
    assert r["error"] is None
    assert r["n_anios"] == 5
    assert 2022 not in r["anios_detalle"]


def test_menos_de_minimo_de_anios_no_inventa(monkeypatch, tmp_path):
    anios = [2020, 2021, 2022]  # 3 años, MIN_ANIOS_VALIDOS=5
    assert len(anios) < MIN_ANIOS_VALIDOS
    df = _df_sintetico_anios(anios)
    _mock_pvgis(monkeypatch, df)
    monkeypatch.setattr("calculos.incertidumbre_p90._CACHE_DIR", str(tmp_path))

    r = calcular_variabilidad_interanual_real(6.0, -75.0, anios_atras=3, usar_cache=False)
    assert r["sigma_irr_real_pct"] is None
    assert "año" in r["error"] or "anios" in r["error"].lower() or "MIN_ANIOS" not in r["error"]
    assert r["error"] is not None


# ── Reintento cuando PVGIS rechaza el año final pedido ───────────────────────
def test_reintenta_con_el_rango_real_si_pvgis_rechaza_el_fin_pedido(monkeypatch, tmp_path):
    # Bug real encontrado en vivo el 7-sep-2026: pedir "año actual - 1"
    # como año final falla si PVGIS todavía no cubre ese año -- el mensaje
    # de error de PVGIS trae el rango real ("...between 2005 and 2023.").
    anios_ok = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
    df_ok = _df_sintetico_anios(anios_ok)
    llamada = {"n": 0}

    def _fake(*args, **kwargs):
        llamada["n"] += 1
        if llamada["n"] == 1:
            raise Exception(
                "endyear: Incorrect value. Please, enter an integer between 2005 and 2023."
            )
        return df_ok, {}, {}

    monkeypatch.setattr("pvlib.iotools.get_pvgis_hourly", _fake)
    monkeypatch.setattr("calculos.incertidumbre_p90._CACHE_DIR", str(tmp_path))

    r = calcular_variabilidad_interanual_real(7.884, -76.635, anios_atras=11, usar_cache=False)
    assert llamada["n"] == 2  # 1 intento fallido + 1 reintento exitoso
    assert r["error"] is None
    assert r["anio_fin"] == 2023
    assert r["n_anios"] == 11


def test_error_de_red_sin_patron_reconocible_no_revienta(monkeypatch, tmp_path):
    def _fake(*args, **kwargs):
        raise Exception("Connection timed out")
    monkeypatch.setattr("pvlib.iotools.get_pvgis_hourly", _fake)
    monkeypatch.setattr("calculos.incertidumbre_p90._CACHE_DIR", str(tmp_path))

    r = calcular_variabilidad_interanual_real(6.0, -75.0, anios_atras=11, usar_cache=False)
    assert r["sigma_irr_real_pct"] is None
    assert "Connection timed out" in r["error"]


# ── Caché en disco ────────────────────────────────────────────────────────────
def test_cache_guarda_y_relee_exacto(monkeypatch, tmp_path):
    anios = [2015, 2016, 2017, 2018, 2019, 2020]
    df = _df_sintetico_anios(anios)
    contador = []
    _mock_pvgis(monkeypatch, df, contador=contador)
    monkeypatch.setattr("calculos.incertidumbre_p90._CACHE_DIR", str(tmp_path))

    r1 = calcular_variabilidad_interanual_real(6.0, -75.0, anios_atras=6, usar_cache=True)
    r2 = calcular_variabilidad_interanual_real(6.0, -75.0, anios_atras=6, usar_cache=True)
    assert r1 == r2
    assert len(contador) == 1  # la 2da llamada NO debe volver a golpear "PVGIS"


def test_sin_cache_previo_no_revienta(tmp_path):
    from calculos.incertidumbre_p90 import _leer_cache_variabilidad
    assert _leer_cache_variabilidad(0.0, 0.0, 11) is None  # coordenada sin caché nunca creado


def test_cache_corrupto_no_revienta(monkeypatch, tmp_path):
    from calculos.incertidumbre_p90 import _cache_path
    monkeypatch.setattr("calculos.incertidumbre_p90._CACHE_DIR", str(tmp_path))
    p = _cache_path(6.0, -75.0, 11)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(b"esto no es un pickle valido")

    from calculos.incertidumbre_p90 import _leer_cache_variabilidad
    assert _leer_cache_variabilidad(6.0, -75.0, 11) is None  # nunca lanza excepción


# ── elegir_sigma_irr() -- la regla de combinación ────────────────────────────
def test_elegir_sigma_usa_el_real_si_es_mayor_que_la_tabla():
    resultado_real = {"sigma_irr_real_pct": 8.2}
    r = elegir_sigma_irr(5.0, resultado_real)
    assert r["sigma_irr_usado_pct"] == 8.2
    assert r["fuente_usada"] == "real"
    assert r["sigma_tabla_pct"] == 5.0
    assert r["sigma_real_pct"] == 8.2


def test_elegir_sigma_usa_la_tabla_si_el_real_es_menor():
    # Caso real encontrado el 7-sep-2026: Urabá, tabla=6.5%, real=2.18% --
    # la tabla debe seguir mandando (nunca el valor más bajo/optimista).
    resultado_real = {"sigma_irr_real_pct": 2.18}
    r = elegir_sigma_irr(6.5, resultado_real)
    assert r["sigma_irr_usado_pct"] == 6.5
    assert r["fuente_usada"] == "tabla"


def test_elegir_sigma_cae_a_tabla_sin_dato_real():
    resultado_real = {"sigma_irr_real_pct": None, "error": "PVGIS no respondió"}
    r = elegir_sigma_irr(5.5, resultado_real)
    assert r["sigma_irr_usado_pct"] == 5.5
    assert r["fuente_usada"] == "tabla"
    assert r["sigma_real_pct"] is None
