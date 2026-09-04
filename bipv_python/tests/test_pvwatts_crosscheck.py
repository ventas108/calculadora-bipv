"""
Tests de calculos/pvwatts_crosscheck.py.

El fixture _RESPUESTA_PVWATTS_BOGOTA_REAL es una respuesta REAL de PVWatts v8
(capturada 4-sep-2026, lat=4.6097/lon=-74.0817 Bogotá, tilt=90/azimuth=180 --
fachada vertical sur, mismo tipo de proyecto que Teusaquillo), no inventada --
mismo criterio que el resto de la suite (ver test_solar_qcrad.py).
"""
import math

import pandas as pd
import pytest
import requests

from calculos.pvwatts_crosscheck import (
    _leer_nrel_api_key,
    comparar_poa_pvgis_vs_pvwatts,
    obtener_produccion_pvwatts,
    poa_horaria_a_mensual_kwh_m2,
)

_RESPUESTA_PVWATTS_BOGOTA_REAL = {
    "errors": [],
    "warnings": [],
    "station_info": {
        "state": "Bogota",
        "country": "Colombia",
        "weather_data_source": "NSRDB PSM V3 GOES tmy-2020 3.2.0",
    },
    "outputs": {
        "ac_monthly": [
            87.7713106271195, 48.6907462938893, 31.1392649148181,
            25.84042619499371, 27.23258882500128, 25.49257467562443,
            25.38866293582987, 27.61016895643215, 26.30700699389401,
            41.67773088221414, 58.10326448784574, 81.36135643389896,
        ],
        "poa_monthly": [
            116.6812284813355, 68.34929898331215, 46.77222953866647,
            35.67531543135566, 37.53717939872076, 35.01271953922213,
            35.03374855250805, 37.95406538400938, 38.86131251869679,
            59.90725674590202, 77.666620526928, 106.9581953943469,
        ],
        "dc_monthly": [
            92.51425748764218, 51.84192727689503, 33.80436272724819,
            28.22482773818512, 29.7365918836517, 27.88921518211764,
            27.83509758105938, 30.12596120126612, 28.74874802651929,
            44.69943427650121, 61.65936506910064, 85.84224344531614,
        ],
    },
}


class _FakeResp:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


# ── _leer_nrel_api_key() ────────────────────────────────────────────────────

def test_leer_key_desde_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("NREL_API_KEY", "clave-de-prueba")
    assert _leer_nrel_api_key() == "clave-de-prueba"


def test_leer_key_ausente_retorna_none_sin_reventar(monkeypatch, tmp_path):
    monkeypatch.delenv("NREL_API_KEY", raising=False)
    ruta_inexistente = tmp_path / "no_existe.env"
    assert _leer_nrel_api_key(env_path=str(ruta_inexistente)) is None


def test_leer_key_desde_archivo_env(monkeypatch, tmp_path):
    monkeypatch.delenv("NREL_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=algo\nNREL_API_KEY=clave-del-archivo\nOTRA=cosa\n", encoding="utf-8")
    assert _leer_nrel_api_key(env_path=str(env_file)) == "clave-del-archivo"


# ── obtener_produccion_pvwatts() ────────────────────────────────────────────

def test_obtener_produccion_sin_key_retorna_none(monkeypatch):
    monkeypatch.delenv("NREL_API_KEY", raising=False)
    resultado = obtener_produccion_pvwatts(
        lat=4.6097, lon=-74.0817, tilt=90, azimuth=180, system_capacity_kw=1.0,
    )
    assert resultado is None


def test_obtener_produccion_con_key_y_respuesta_real(monkeypatch):
    monkeypatch.setenv("NREL_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(
        requests, "get",
        lambda url, params=None, timeout=None: _FakeResp(200, _RESPUESTA_PVWATTS_BOGOTA_REAL),
    )
    resultado = obtener_produccion_pvwatts(
        lat=4.6097, lon=-74.0817, tilt=90, azimuth=180, system_capacity_kw=1.0,
    )
    assert resultado is not None
    assert len(resultado["poa_monthly_kwh_m2"]) == 12
    assert resultado["poa_monthly_kwh_m2"][0] == pytest.approx(116.6812284813355)
    assert resultado["weather_data_source"] == "NSRDB PSM V3 GOES tmy-2020 3.2.0"


def test_obtener_produccion_con_errores_de_pvwatts_retorna_none(monkeypatch):
    monkeypatch.setenv("NREL_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(
        requests, "get",
        lambda url, params=None, timeout=None: _FakeResp(
            200, {"errors": ["You have exceeded your rate limit"], "outputs": {}}
        ),
    )
    assert obtener_produccion_pvwatts(4.6097, -74.0817, 90, 180) is None


def test_obtener_produccion_con_timeout_de_red_retorna_none(monkeypatch):
    monkeypatch.setenv("NREL_API_KEY", "clave-de-prueba")

    def _timeout(*a, **k):
        raise requests.exceptions.Timeout("simulado")

    monkeypatch.setattr(requests, "get", _timeout)
    assert obtener_produccion_pvwatts(4.6097, -74.0817, 90, 180) is None


# ── poa_horaria_a_mensual_kwh_m2() ──────────────────────────────────────────

def test_poa_horaria_a_mensual_caso_calculado_a_mano():
    # 3 horas sintéticas: 2 en enero (500 y 300 W/m²), 1 en febrero (400 W/m²).
    # Enero esperado: (500+300)/1000 = 0.8 kWh/m². Febrero: 400/1000 = 0.4 kWh/m².
    idx = pd.DatetimeIndex(["2001-01-01 10:00", "2001-01-01 11:00", "2001-02-01 10:00"])
    serie = pd.Series([500.0, 300.0, 400.0], index=idx)
    mensual = poa_horaria_a_mensual_kwh_m2(serie)
    assert len(mensual) == 12
    assert mensual[0] == pytest.approx(0.8)   # enero
    assert mensual[1] == pytest.approx(0.4)   # febrero
    assert mensual[2] == 0.0                  # marzo, sin datos


def test_poa_horaria_a_mensual_serie_vacia_lanza_error():
    with pytest.raises(ValueError, match="vacía"):
        poa_horaria_a_mensual_kwh_m2(pd.Series([], dtype=float, index=pd.DatetimeIndex([])))


# ── comparar_poa_pvgis_vs_pvwatts() ─────────────────────────────────────────

def test_comparar_caso_calculado_a_mano():
    # PVGIS: 100 kWh/m² todos los meses (1200 anual). PVWatts: 110 (+10%).
    pvgis = [100.0] * 12
    pvwatts = [110.0] * 12
    resultado = comparar_poa_pvgis_vs_pvwatts(pvgis, pvwatts)
    assert resultado["diferencia_pct_mensual"] == pytest.approx([10.0] * 12)
    assert resultado["diferencia_pct_anual"] == pytest.approx(10.0)
    assert resultado["poa_pvgis_anual_kwh_m2"] == pytest.approx(1200.0)
    assert resultado["poa_pvwatts_anual_kwh_m2"] == pytest.approx(1320.0)
    assert resultado["alerta"] is False  # 10% < umbral default de 15%


def test_comparar_dispara_alerta_sobre_el_umbral():
    pvgis = [100.0] * 12
    pvwatts = [120.0] * 12  # +20%, supera el umbral default de 15%
    resultado = comparar_poa_pvgis_vs_pvwatts(pvgis, pvwatts)
    assert resultado["diferencia_pct_anual"] == pytest.approx(20.0)
    assert resultado["alerta"] is True


def test_comparar_respeta_umbral_personalizado():
    pvgis = [100.0] * 12
    pvwatts = [112.0] * 12  # +12%
    assert comparar_poa_pvgis_vs_pvwatts(pvgis, pvwatts, umbral_alerta_pct=15.0)["alerta"] is False
    assert comparar_poa_pvgis_vs_pvwatts(pvgis, pvwatts, umbral_alerta_pct=10.0)["alerta"] is True


def test_comparar_pvgis_con_meses_en_cero_no_revienta():
    pvgis = [0.0] + [100.0] * 11
    pvwatts = [50.0] + [110.0] * 11
    resultado = comparar_poa_pvgis_vs_pvwatts(pvgis, pvwatts)
    assert resultado["diferencia_pct_mensual"][0] is None  # 0/0 indefinido, no se inventa un número
    assert resultado["diferencia_pct_mensual"][1] == pytest.approx(10.0)


def test_comparar_exige_exactamente_12_meses():
    with pytest.raises(ValueError, match="12"):
        comparar_poa_pvgis_vs_pvwatts([100.0] * 11, [100.0] * 12)


def test_comparar_con_valores_reales_pvwatts_bogota_vs_pvgis_hipotetico():
    # PVGIS hipotético ~5% menor que PVWatts en cada mes, usando los valores
    # REALES de PVWatts capturados arriba (fachada vertical sur, Bogotá) --
    # no valida PVGIS en sí (eso ya lo hace test_solar_qcrad.py), solo que la
    # función combina bien datos reales de PVWatts con cualquier serie PVGIS.
    poa_pvwatts_real = _RESPUESTA_PVWATTS_BOGOTA_REAL["outputs"]["poa_monthly"]
    poa_pvgis_hipotetico = [v * 0.95 for v in poa_pvwatts_real]
    resultado = comparar_poa_pvgis_vs_pvwatts(poa_pvgis_hipotetico, poa_pvwatts_real)
    assert resultado["diferencia_pct_anual"] == pytest.approx(100.0 / 0.95 - 100.0, rel=1e-6)
    assert resultado["alerta"] is False
