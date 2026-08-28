# -*- coding: utf-8 -*-
"""
Tests de calculos/solar.py::verificar_consistencia_radiativa() (27-ago-2026).

Origen: al auditar un motor BIPV Python puro que aportó el usuario, su
propio chequeo de cierre físico GHI≈DNI·cosZ+DHI encontró un bug real de
desfase de 30 minutos en el centrado del timestamp (misma familia que el
bug de 5 horas de DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md, 26-ago-2026).
pvlib no trae este chequeo; existe en el paquete hermano `pvanalytics`
como el algoritmo QCRad (Long & Shi, 2008) pero se portó solo la fórmula
central aquí para no agregar esa dependencia (arrastra statsmodels +
scikit-image sin usarlos). Ver docstring de módulo en calculos/solar.py.

Proyecto de referencia para los tests de integración: "Teusaquillo,
Bogotá" -- el único proyecto de fachada vertical ya auditado contra el
XLSM original en este repo (panel ASP-ST1-T40 × 128 = 92,16 m², inversor
Growatt-MID15KTL3-X, ver datos/catalogo_inversores.py y
scripts/generar_auditoria_vba.py). Coordenadas de Bogotá tomadas de
datos/ciudades_colombia.py (fuente real de la app, no un valor de prueba
inventado): lat=4,711, lon=-74,072, alt=2.600 m. Fachada vertical:
tilt=90°, azimuth=180° (sur), igual convención que
tests/test_escenarios_fase4.py::_estado_base().

El TMY real de PVGIS para estas coordenadas se verificó en vivo antes de
escribir estos tests (0 horas inconsistentes, diferencia media 0,3 W/m²,
máxima 2,8 W/m²) -- los tests de integración usan en cambio un TMY
sintético de cielo despejado (mismo patrón que
tests/test_simulation_pipeline.py::_tmy_sintetico_offline, modelo
Ineichen de pvlib) para no depender de la red ni de la disponibilidad de
PVGIS en cada corrida de la suite; por construcción física (modelo de
turbidez atmosférica), este TMY sintético también satisface el cierre
GHI≈DNI·cosZ+DHI casi exactamente, así que sirve igual de bien para
probar el chequeo.
"""
import warnings

import numpy as np
import pandas as pd
import pytest
import pvlib

from calculos.solar import calcular_poa, verificar_consistencia_radiativa

# Bogotá real -- datos/ciudades_colombia.py (no un valor de prueba inventado)
LAT, LON, ALT_M = 4.711, -74.072, 2600.0
# Fachada vertical sur, misma convención que el proyecto real Teusaquillo
TILT, AZIMUTH = 90.0, 180.0


def _tmy_despejado_bogota() -> pd.DataFrame:
    """TMY sintético de cielo despejado (Ineichen) para Bogotá -- mismo
    patrón que test_simulation_pipeline.py::_tmy_sintetico_offline.
    Físicamente consistente por construcción (modelo de turbidez), útil
    para probar el chequeo QCRad sin depender de la red."""
    idx = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    loc = pvlib.location.Location(latitude=LAT, longitude=LON, altitude=ALT_M, tz="UTC")
    cs = loc.get_clearsky(idx, model="ineichen")
    return pd.DataFrame({
        "G_h": cs["ghi"].values, "Gb_n": cs["dni"].values, "Gd_h": cs["dhi"].values,
        "T2m": 14.0, "WS10m": 2.0, "SP": 101_325.0,
    }, index=idx)


# ══════════════════════════════════════════════════════════════════════════
# Unidad: verificar_consistencia_radiativa() -- caso mínimo calculado a mano
# ══════════════════════════════════════════════════════════════════════════
def test_caso_minimo_calculado_a_mano():
    # 3 "horas": h1 perfectamente consistente, h2 inconsistente a propósito,
    # h3 de noche (elevación < 3°) con valores basura que deben ignorarse.
    #
    # h1: zenit=60° -> cos=0,5 -> GHI_consistente = 800*0,5+100 = 500,0
    # h2: zenit=30° -> cos=0,866025 -> suma_componentes = 700*0,866025+150
    #     = 756,22 ; GHI real = 850 -> diferencia = |850-756,22| = 93,78 W/m²
    # h3: zenit=89° -> elevación=1° < 3° -> excluida sin importar sus valores
    zenit = np.array([60.0, 30.0, 89.0])
    tmy = pd.DataFrame({
        "G_h":  [500.0, 850.0, 1.0],
        "Gb_n": [800.0, 700.0, 1000.0],
        "Gd_h": [100.0, 150.0, 1000.0],
    })

    with warnings.catch_warnings(record=True) as capturados:
        warnings.simplefilter("always")
        resultado = verificar_consistencia_radiativa(tmy, zenit)

    assert resultado["horas_evaluadas"] == 2          # h3 excluida por elevación
    assert resultado["horas_inconsistentes"] == 1      # solo h2
    assert resultado["pct_inconsistente"] == 50.0
    # abs=0.05: verificar_consistencia_radiativa() redondea a 1 decimal por diseño
    assert resultado["diferencia_media_wm2"] == pytest.approx((0.0 + 93.78) / 2, abs=0.05)
    assert resultado["diferencia_maxima_wm2"] == pytest.approx(93.78, abs=0.05)
    # 50% > pct_alerta (2% default) -> debe emitir el warning
    assert len(capturados) == 1
    assert issubclass(capturados[0].category, UserWarning)
    assert "QCRad" in str(capturados[0].message)


def test_datos_perfectamente_consistentes_no_dispara_warning():
    # Mismas 2 horas de día, pero ambas con GHI exactamente igual a la
    # suma de componentes -- 0% inconsistente, sin warning.
    zenit = np.array([60.0, 30.0])
    tmy = pd.DataFrame({
        "G_h":  [500.0, 756.22],
        "Gb_n": [800.0, 700.0],
        "Gd_h": [100.0, 150.0],
    })
    with warnings.catch_warnings():
        warnings.simplefilter("error")   # cualquier warning hace fallar el test
        resultado = verificar_consistencia_radiativa(tmy, zenit)
    assert resultado["pct_inconsistente"] == 0.0
    assert resultado["horas_inconsistentes"] == 0


def test_horas_nocturnas_no_cuentan_aunque_haya_diferencia_enorme():
    zenit = np.array([95.0])   # elevación = -5°, de noche
    tmy = pd.DataFrame({"G_h": [500.0], "Gb_n": [0.0], "Gd_h": [0.0]})
    resultado = verificar_consistencia_radiativa(tmy, zenit)
    assert resultado["horas_evaluadas"] == 0
    assert resultado["pct_inconsistente"] == 0.0


def test_sin_horas_de_dia_no_revienta():
    zenit = np.array([95.0, 100.0, 91.0])
    tmy = pd.DataFrame({"G_h": [0.0, 0.0, 0.0], "Gb_n": [0.0, 0.0, 0.0], "Gd_h": [0.0, 0.0, 0.0]})
    resultado = verificar_consistencia_radiativa(tmy, zenit)
    assert resultado == {
        "horas_evaluadas": 0, "horas_inconsistentes": 0, "pct_inconsistente": 0.0,
        "diferencia_media_wm2": 0.0, "diferencia_maxima_wm2": 0.0,
    }


# ══════════════════════════════════════════════════════════════════════════
# Integración: calcular_poa() -- proyecto real Teusaquillo, Bogotá
# ══════════════════════════════════════════════════════════════════════════
def test_calcular_poa_adjunta_qcrad_en_attrs():
    tmy = _tmy_despejado_bogota()
    with warnings.catch_warnings():
        warnings.simplefilter("error")   # el TMY de cielo despejado no debe disparar nada
        poa = calcular_poa(tmy, LAT, LON, ALT_M, tilt=TILT, azimuth=AZIMUTH)
    assert "qcrad" in poa.attrs
    assert poa.attrs["qcrad"]["pct_inconsistente"] < 1.0   # cielo despejado: cierre casi perfecto
    assert poa.attrs["qcrad"]["horas_evaluadas"] > 4000    # ~4.1k horas de día/año en Bogotá


def test_calcular_poa_bifacial_tambien_conserva_qcrad_en_attrs():
    # out = poa.copy() en la rama bifacial -- confirma que .attrs sobrevive
    # el .copy() (comportamiento de pandas verificado antes de integrar).
    tmy = _tmy_despejado_bogota()
    poa = calcular_poa(
        tmy, LAT, LON, ALT_M, tilt=10.0, azimuth=180.0,
        bifacial={"bifacialidad": 0.80, "altura_m": 1.0, "gcr": 0.35, "ancho_colector_m": 2.6},
    )
    assert "qcrad" in poa.attrs
    assert poa.attrs["qcrad"]["pct_inconsistente"] < 1.0


def test_desfase_de_30_min_en_el_timestamp_dispara_el_warning():
    # Regresión directa del hallazgo de la auditoría (27-ago-2026): un TMY
    # cuyo índice está desfasado 30 min respecto a la posición solar real
    # (el mismo tipo de bug que traía el script del usuario, y el mismo
    # tipo de bug de DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md, aquí de menor
    # magnitud) debe ser detectado automáticamente por calcular_poa().
    tmy = _tmy_despejado_bogota()
    tmy_desfasado = tmy.copy()
    tmy_desfasado.index = tmy_desfasado.index + pd.Timedelta(minutes=30)

    with pytest.warns(UserWarning, match="QCRad"):
        poa = calcular_poa(tmy_desfasado, LAT, LON, ALT_M, tilt=TILT, azimuth=AZIMUTH)

    assert poa.attrs["qcrad"]["pct_inconsistente"] > 2.0   # supera el umbral de alerta
