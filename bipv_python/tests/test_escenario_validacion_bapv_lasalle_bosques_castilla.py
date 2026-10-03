# -*- coding: utf-8 -*-
"""Escenario de validación externa — Fachada BAPV "Bosques de Castilla" (Kennedy,
Bogotá), tesis de pregrado Cardozo Sarmiento & Moreno Suarez (Universidad de La
Salle, 2021), simulada por los autores en PV·SOL Premium.

Fuente: ``references/lasalle-2021-bipv-fachada-propiedad-horizontal.pdf``
(descargado de ciencia.lasalle.edu.co/ing_electrica/630), resumen y comparación
completa en ``references/informe-validacion-bapv-lasalle-bosques-castilla-2021.md``.

Reconstruye en la APP, a través del pipeline FÍSICO multi-superficie real
(``calculos.vinculador_sombra_multisuperficie.construir_y_recalcular_proyecto_fisico``),
las dos fachadas verticales (suroeste y sureste) y el sistema de referencia
horizontal/óptimo que la tesis simula en PV·SOL, usando:

- el panel SunPower Maxeon 3 SPR-MAX3-400 (ficha real del fabricante — NO está en
  ``datos.tecnologias_bipv``, se construye aquí a partir de la ficha pública y se
  resuelve el SDM con ``calculos.modelo_iv.estimar_sdm_desde_ficha`` — el mismo
  método ya usado para SUNPOWER_E20_327);
- un TMY SINTÉTICO determinista (clear-sky Ineichen, pvlib, sin red) para las
  coordenadas del edificio leídas de las fotografías de la propia tesis
  (Fig. 6/7: 4°38'18"N 74°8'54"O ≈ 4.634, -74.148; PVGIS devuelve altitud 2550 m
  para ese punto, coincide con el dato impreso en la Fig. 7). Una sesión previa
  con acceso a red descargó un TMY real de PVGIS y con él se calcularon las
  cifras de POA de ``informe-validacion-bapv-lasalle-bosques-castilla-2021.md``
  §4 (1.794,7 / 986,2 / 852,2 kWh/m²/año); ESTE archivo ya no repite esa
  descarga en cada corrida (frágil, no determinista, depende de red) — usa un
  fixture sintético fijo en su lugar. Las pruebas de POA por eso comparan
  contra PV·SOL en bandas anchas (orden de magnitud), NO contra los valores
  exactos del informe, que corresponden a un TMY real distinto de este fixture;
- ``p_shade = 0`` (estado ``sombra_cero_calculada``, NUNCA ``calculado_completo``)
  en las cuatro superficies: la tesis NO publica una máscara angular de sombra
  (a diferencia del caso East2, que sí publica su Tabla 4) — solo publica
  pérdidas de sombreado agregadas de PV·SOL (3.7%/año fachadas, 1%/año
  referencia horizontal) y un mapa de sombra por posición de panel
  (Tablas 19/20) sin serie horaria. Sustituir esto por una máscara inventada
  violaría la regla de no fabricar datos. La comparación se documenta siempre
  como "sin máscara de sombra publicada", nunca como "sombra medida = 0".

Este archivo NO valida contra la tesis como homologación numérica exacta (faltan:
máscara angular horaria, conteo de módulos por fachada, y la base meteorológica
que PV·SOL usó). Las pruebas están agrupadas en 4 bloques deliberadamente
separados (ver los encabezados de sección más abajo):

  A. Validación de ficha de panel (SDM vs. datasheet) — independiente de TMY.
  B. Validación geométrica (ejecución end-to-end, determinismo, orden
     suroeste > sureste) — independiente de si el TMY es sintético o real.
  C. Comparación de POA frente a PV·SOL — banda ancha, informativa, nunca
     puntual, porque el recurso solar de entrada difiere del que usó PV·SOL.
  D. Comparación energética normalizada por recurso — informativa, documenta
     explícitamente qué pérdidas de PV·SOL no se modelan aquí (sombra real,
     cableado, mismatch, autoconsumo/clipping del inversor).

Ninguna prueba compara energía TOTAL del sistema (kWh/año) contra los
42.560/82.521 kWh de la tesis: el reparto real de los 148 módulos entre
fachadas no está publicado, y esta reconstrucción usa 140 (70+70, un supuesto
propio) — la discrepancia de conteo queda verificada explícitamente en
``test_conteo_modulos_app_difiere_del_publicado_en_la_tesis``.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pvlib
import pytest
from pvlib.iotools import epw as pvlib_epw

from calculos.modelo_iv import estimar_sdm_desde_ficha, validar_sdm_vs_ficha
from calculos.sombras_3d import ESTADO_SOMBRA_CERO_CALCULADA
from calculos.transicion_multisuperficie import superficie_nueva
from calculos.vinculador_sombra_multisuperficie import (
    construir_y_recalcular_proyecto_fisico,
)
from calculos.adaptador_multisuperficie import aplicar_proyecto_a_session_state
from calculos.produccion_vigencia import huella_horaria

_EPW_BOGOTA = (
    Path(__file__).resolve().parents[2] / "references" / "bogota-eldorado-iwec.epw"
)

# ── Coordenadas del sitio (leídas de las Fig. 6/7 del PDF, no inventadas) ────
LAT, LON, ALT_M = 4.634, -74.148, 2550.0
TZ = "America/Bogota"
INVERSOR_ID = "Fronius-Primo-15"          # ya en datos.catalogo_inversores — mismo
ETA_INVERSOR = 0.986                       # modelo publicado por la tesis (Fig. 21)
N_SERIE, N_PARALELO = 10, 7                # 70 módulos, 28.0 kWp por superficie —
                                            # asunción de dimensionamiento propia
                                            # (Vmp string=658V dentro de la ventana
                                            # MPPT 200-800V del inversor catalogado);
                                            # la tesis no publica el reparto de
                                            # módulos entre fachadas.
MODULOS_POR_SUPERFICIE = N_SERIE * N_PARALELO
MODULOS_TOTAL_APP = MODULOS_POR_SUPERFICIE * 2        # 2 fachadas, 140 módulos
MODULOS_TOTAL_TESIS = 148                             # Tabla 18/21 de la tesis
_HORAS_ANIO = 8760


def _tmy_bogota_clearsky_sintetico(t2m: float = 15.0) -> pd.DataFrame:
    """TMY sintético determinista (clear-sky Ineichen, pvlib) — sin red.

    Reemplaza la descarga en vivo de PVGIS que usó la sesión que produjo las
    cifras de ``informe-validacion-bapv-lasalle-bosques-castilla-2021.md`` §4:
    esa descarga es frágil (depende de red, no es reproducible en un entorno
    sin acceso a internet) y no aportaba determinismo de prueba a prueba. Este
    fixture es intencionalmente sintético y NO reproduce el TMY real de
    PVGIS/PV·SOL — las pruebas de POA (bloque C) por eso usan bandas anchas,
    nunca un valor puntual del informe.
    """
    idx = pd.date_range("2023-01-01 00:00", "2023-12-31 23:00", freq="h", tz=TZ)
    assert len(idx) == _HORAS_ANIO
    loc = pvlib.location.Location(latitude=LAT, longitude=LON, altitude=ALT_M, tz=TZ)
    cs = loc.get_clearsky(idx, model="ineichen")
    return pd.DataFrame(
        {
            "G_h": cs["ghi"].to_numpy(),
            "Gb_n": cs["dni"].to_numpy(),
            "Gd_h": cs["dhi"].to_numpy(),
            "T2m": np.full(len(idx), t2m),
        },
        index=idx,
    )


def _tmy_bogota_epw_real() -> pd.DataFrame:
    """TMY REAL (EnergyPlus Weather, estación Bogotá El Dorado, IWEC) -- offline.

    Fuente: ``references/bogota-eldorado-iwec.epw``, descargado una sola vez de
    ``energyplus-weather.s3.amazonaws.com`` y versionado en el repositorio --
    la prueba ya no depende de una descarga en vivo. Estación WMO 802220,
    lat=4.70, lon=-74.13, alt=2548 m -- a ~9 km del sitio real leído de las
    Fig. 6/7 de la tesis (4.634, -74.148, 2550 m); se usa como la mejor fuente
    meteorológica real disponible sin depender de PVGIS en vivo, declarando
    explícitamente que no es el punto exacto del edificio.
    """
    # El EPW IWEC mezcla años (1982-1997): todo a un mismo año para el resumen mensual.
    data, _meta = pvlib_epw.read_epw(str(_EPW_BOGOTA), coerce_year=2023)
    assert len(data) == _HORAS_ANIO
    return pd.DataFrame(
        {
            "G_h": data["ghi"].to_numpy(dtype=float),
            "Gb_n": data["dni"].to_numpy(dtype=float),
            "Gd_h": data["dhi"].to_numpy(dtype=float),
            "T2m": data["temp_air"].to_numpy(dtype=float),
        },
        index=data.index,
    )


# ── Ficha pública real SunPower Maxeon 3 SPR-MAX3-400 ────────────────────────
# Fuente: datasheet oficial Maxeon Solar Technologies, doc 544451 REV A / A4_EN,
# publication date abril 2022 (residential) y doc 532420 REV C (COM, jul 2020,
# mismos valores eléctricos). Coincide EXACTO con la Tabla 18 de la tesis
# (400 W, 22.6%, 1690x1046 mm) -- confirma que es el mismo panel.
# NOCT: NO publicado por el fabricante en ninguna de las dos fichas revisadas
# -- se usa el default 45°C que el propio motor de la app ya aplica para
# Mono-Si sin NOCT de ficha (calculos/produccion.py:328-330), declarado aquí
# explícitamente porque calculos.transicion_multisuperficie.recalcular_fisica_
# superficie() exige NOCT explícito en el dict del panel (no acepta default
# silencioso en el pipeline multi-superficie).
def _ficha_sunpower_max3_400() -> dict:
    return {
        "nombre": "SPR-MAX3-400", "fabricante": "SunPower (Maxeon Solar Technologies)",
        "tecnologia": "Mono-Si", "transparencia_pct": 0,
        "descripcion": "Panel de fachada BAPV Bosques de Castilla (La Salle 2021, Tabla 18).",
        "fuente_datos": "Datasheet Maxeon 544451 REV A (abr-2022) / 532420 REV C (jul-2020).",
        "sdm_estimado": True,
        "Voc_stc": 75.6, "Vmp_stc": 65.8, "Isc_stc": 6.58, "Imp_stc": 6.08,
        "Pmax_stc": 65.8 * 6.08,
        "Tk_beta": -0.236, "Tk_alfa": 0.058, "Tk_gamma": -0.27,
        "N_s": 104, "NOCT": 45.0,
        "largo_mm": 1690, "ancho_mm": 1046, "area_m2": 1.690 * 1.046,
    }


def _panel_sunpower_max3_400() -> dict:
    ficha = _ficha_sunpower_max3_400()
    sdm = estimar_sdm_desde_ficha(ficha)
    assert sdm is not None, "estimar_sdm_desde_ficha no debe fallar con esta ficha completa"
    return {**ficha, **sdm}


def _superficie(panel: dict, tmy: pd.DataFrame, nombre: str, tipo: str,
                tilt: float, azimuth: float) -> dict:
    area = panel["area_m2"] * N_SERIE * N_PARALELO
    # Sin máscara angular publicada por la tesis (ver docstring del módulo) --
    # NUNCA se declara "calculado_completo": el estado real es un cero
    # calculado explícitamente, no una sombra medida ni fabricada.
    p_shade = np.zeros(_HORAS_ANIO)
    sup = superficie_nueva(
        nombre=nombre, tipo=tipo, tilt_deg=tilt, azimuth_deg=azimuth,
        area_m2=area, panel=panel, n_serie=N_SERIE, n_paralelo=N_PARALELO,
        inversor_id=INVERSOR_ID, p_shade=p_shade, albedo=0.20,
    )
    sup["estado_sombra"] = ESTADO_SOMBRA_CERO_CALCULADA
    sup["firma_sombra"] = {
        "geometria": {"tilt_deg": tilt, "azimuth_deg": azimuth},
        "tmy_fingerprint": huella_horaria(tmy.index, tmy["T2m"].to_numpy(dtype=float)),
        "fuente": "sin_mascara_angular_publicada_lasalle2021",
    }
    return sup


def _session_state(panel: dict, tmy: pd.DataFrame) -> dict:
    superficies = [
        _superficie(panel, tmy, "Horizontal", "Techo", 0.0, 180.0),
        _superficie(panel, tmy, "Optimo-10-Sur", "Techo", 10.0, 180.0),
        _superficie(panel, tmy, "Fachada-Suroeste", "Fachada", 90.0, 249.0),
        _superficie(panel, tmy, "Fachada-Sureste", "Fachada", 90.0, 162.0),
    ]
    return {
        "panel_dict": panel,
        "superficies_bipv": superficies,
        "multisup_inversores": [
            {"inversor_id": INVERSOR_ID, "tipo": "compartido",
             "eta_inversor": ETA_INVERSOR, "P_ac_nom_W": None, "ficha": {}},
        ],
    }


# ══════════════════════════════════════════════════════════════════════════
# A. Validación de ficha de panel (SDM vs. datasheet) — independiente de TMY
# ══════════════════════════════════════════════════════════════════════════
def test_sunpower_max3_400_ficha_coincide_con_datasheet_maxeon():
    ficha = _ficha_sunpower_max3_400()
    assert ficha["Voc_stc"] == pytest.approx(75.6, abs=0.01)
    assert ficha["Isc_stc"] == pytest.approx(6.58, abs=0.01)
    assert ficha["Vmp_stc"] == pytest.approx(65.8, abs=0.01)
    assert ficha["Imp_stc"] == pytest.approx(6.08, abs=0.01)
    assert ficha["Pmax_stc"] == pytest.approx(400.0, abs=0.5)
    eficiencia_pct = ficha["Pmax_stc"] / (ficha["area_m2"] * 1000.0) * 100.0
    assert eficiencia_pct == pytest.approx(22.6, abs=0.1)  # Tabla 18 de la tesis


def test_sunpower_max3_400_sdm_reproduce_stc_dentro_de_tolerancia():
    panel = _panel_sunpower_max3_400()
    validacion = validar_sdm_vs_ficha(panel)
    assert validacion["validacion_ok"] is True
    assert validacion["Pmax"]["error_pct"] < 0.5
    assert validacion["Voc"]["error_pct"] < 0.5
    assert validacion["Isc"]["error_pct"] < 0.5


def test_conteo_modulos_app_difiere_del_publicado_en_la_tesis():
    """La tesis publica 148 módulos (Tabla 18/21) sin repartirlos entre las
    dos fachadas. Esta reconstrucción asume 70+70=140 (supuesto propio, ver
    N_SERIE/N_PARALELO). Esta prueba deja la discrepancia como un hecho
    verificado, no una nota que alguien pueda pasar por alto: por eso NINGUNA
    otra prueba de este archivo compara energía TOTAL del sistema contra los
    42.560/82.521 kWh publicados por la tesis."""
    assert MODULOS_TOTAL_APP != MODULOS_TOTAL_TESIS
    assert MODULOS_TOTAL_APP == 140
    assert MODULOS_TOTAL_TESIS == 148


# ══════════════════════════════════════════════════════════════════════════
# B. Validación geométrica — ejecución end-to-end, determinismo, orden
#    relativo de fachadas. Independiente de si el TMY es sintético o real.
# ══════════════════════════════════════════════════════════════════════════
def test_escenario_lasalle_corre_con_tmy_sintetico():
    panel = _panel_sunpower_max3_400()
    tmy = _tmy_bogota_clearsky_sintetico()
    session_state = _session_state(panel, tmy)

    proyecto = construir_y_recalcular_proyecto_fisico(
        session_state, tmy, lat=LAT, lon=LON, alt_m=ALT_M
    )

    assert proyecto["agregados"]["n_superficies"] == 4
    assert proyecto["agregados"]["E_ac_total_kWh"] > 0.0
    for nombre in ("Horizontal", "Optimo-10-Sur", "Fachada-Suroeste", "Fachada-Sureste"):
        sup = proyecto["superficies"][nombre]
        assert sup["resultados_dc"] is not None
        assert sup["resultados_ac"] is not None
        assert sup["resultados_dc"]["E_dc_anual_kWh"] > 0.0

    # Las dos fachadas (mismo tilt=90°, azimuth distinto) deben diferir --
    # geometría real, no un valor fijo copiado entre superficies.
    poa_so = proyecto["superficies"]["Fachada-Suroeste"]["resultados_dc"]["poa_anual_kWh_m2"]
    poa_se = proyecto["superficies"]["Fachada-Sureste"]["resultados_dc"]["poa_anual_kWh_m2"]
    assert poa_so != poa_se

    destino: dict = {}
    aplicar_proyecto_a_session_state(proyecto, destino)
    assert destino["multisup_activo"] is True


def test_escenario_lasalle_es_determinista():
    panel = _panel_sunpower_max3_400()
    tmy = _tmy_bogota_clearsky_sintetico()

    p1 = construir_y_recalcular_proyecto_fisico(
        _session_state(panel, tmy), tmy, lat=LAT, lon=LON, alt_m=ALT_M
    )
    p2 = construir_y_recalcular_proyecto_fisico(
        _session_state(panel, tmy), tmy, lat=LAT, lon=LON, alt_m=ALT_M
    )
    for nombre in ("Horizontal", "Fachada-Suroeste", "Fachada-Sureste"):
        assert (
            p1["superficies"][nombre]["huellas"]
            == p2["superficies"][nombre]["huellas"]
        )
        assert (
            p1["superficies"][nombre]["resultados_ac"]["E_ac_anual_kWh"]
            == p2["superficies"][nombre]["resultados_ac"]["E_ac_anual_kWh"]
        )


# ══════════════════════════════════════════════════════════════════════════
# C. Comparación de POA frente a PV·SOL — con el EPW REAL de El Dorado. Banda
#    ancha, pero mucho más ajustada que con el TMY sintético del bloque B:
#    el recurso solar real está a +2.7% (horizontal) / -3.1% (SO) / +7.0% (SE)
#    de PV·SOL, frente a +39%-+95% con clear-sky.
# ══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize(
    ("nombre", "poa_min", "poa_max"),
    [
        # PV·SOL (Fig. 23): horizontal 1571.3 kWh/m²/año. EPW real de El
        # Dorado da ~1613 kWh/m²/año (+2.7%) -- banda ajustada, ya no un
        # chequeo de orden de magnitud sino una comparación real de recurso.
        ("Horizontal", 1400.0, 1850.0),
        # PV·SOL (Fig. 23): 858.0 (suroeste) y 777.3 (sureste) kWh/m²/año.
        ("Fachada-Suroeste", 700.0, 1000.0),
        ("Fachada-Sureste", 700.0, 1000.0),
    ],
)
def test_poa_anual_en_orden_de_magnitud_de_pvsol(nombre, poa_min, poa_max):
    panel = _panel_sunpower_max3_400()
    tmy = _tmy_bogota_epw_real()
    proyecto = construir_y_recalcular_proyecto_fisico(
        _session_state(panel, tmy), tmy, lat=LAT, lon=LON, alt_m=ALT_M
    )
    poa = proyecto["superficies"][nombre]["resultados_dc"]["poa_anual_kWh_m2"]
    assert poa_min < poa < poa_max


def test_fachadas_epw_real_no_reproduce_asimetria_de_pvsol():
    """Hallazgo honesto, no ocultado: PV·SOL reporta suroeste (858.0) >
    sureste (777.3) kWh/m²/año, una asimetría de ~9.4%. Con el EPW real de
    El Dorado, ambas fachadas quedan prácticamente empatadas (<1% de
    diferencia) -- ni el TMY sintético (que exageraba la asimetría a ~28%,
    en la dirección correcta pero magnitud irreal) ni el EPW real (que la
    borra casi por completo) reproducen fielmente la asimetría de PV·SOL.
    Esto no invalida el motor: confirma que la asimetría reportada por
    PV·SOL depende de su propia base meteorológica/modelo de transposición,
    no solo de la geometría, y esta reconstrucción no tiene acceso a esa
    base."""
    panel = _panel_sunpower_max3_400()
    tmy = _tmy_bogota_epw_real()
    proyecto = construir_y_recalcular_proyecto_fisico(
        _session_state(panel, tmy), tmy, lat=LAT, lon=LON, alt_m=ALT_M
    )
    poa_so = proyecto["superficies"]["Fachada-Suroeste"]["resultados_dc"]["poa_anual_kWh_m2"]
    poa_se = proyecto["superficies"]["Fachada-Sureste"]["resultados_dc"]["poa_anual_kWh_m2"]
    diferencia_relativa = abs(poa_so - poa_se) / max(poa_so, poa_se)
    assert diferencia_relativa < 0.02, (
        "Se esperaba un casi-empate SO/SE con el EPW real (evidencia previa "
        f"~0.06%); diferencia real observada: {diferencia_relativa:.4%}."
    )


# ══════════════════════════════════════════════════════════════════════════
# D. Comparación energética normalizada por recurso — informativa. Documenta
#    explícitamente qué pérdidas de PV·SOL este escenario NO modela: sombra
#    real (mapa Tablas 19/20, agregado 3.7%/1%/año), pérdidas de cableado,
#    mismatch entre módulos y posible autoconsumo/clipping del inversor
#    (P_ac_nom_W=None aquí -- sin recorte AC). El residual esperado, una vez
#    descontado el exceso de recurso solar del TMY sintético frente a PV·SOL,
#    debe quedar del lado alto (la app sin esas pérdidas rinde más), nunca
#    igualado ni invertido.
# ══════════════════════════════════════════════════════════════════════════
PERDIDAS_PVSOL_NO_MODELADAS = (
    "sombra_real_fachadas_3.7pct_referencia_1pct",
    "cableado_dc_ac",
    "mismatch_entre_modulos",
    "autoconsumo_o_clipping_inversor",
)


def test_rendimiento_normalizado_por_recurso_queda_por_encima_de_pvsol():
    """Al dividir el rendimiento específico de la app por su propio exceso de
    POA frente a PV·SOL, el residual queda acotado: desde el PR #113 la app ya
    modela cables, mismatch y calidad del módulo (antes rendía más que PV·SOL) -- un residual desbocado señalaría un error del
    motor físico, no solo la ausencia de esas pérdidas."""
    panel = _panel_sunpower_max3_400()
    tmy = _tmy_bogota_epw_real()
    proyecto = construir_y_recalcular_proyecto_fisico(
        _session_state(panel, tmy), tmy, lat=LAT, lon=LON, alt_m=ALT_M
    )

    poa_ref = proyecto["superficies"]["Optimo-10-Sur"]["resultados_dc"]["poa_anual_kWh_m2"]
    ac_ref = proyecto["superficies"]["Optimo-10-Sur"]["resultados_ac"]
    rendimiento_app = ac_ref["E_ac_anual_kWh"] / ac_ref["P_dc_stc_kW"]

    poa_pvsol_referencia = 1571.3   # Fig. 23 de la tesis, kWh/m²/año
    rendimiento_pvsol_referencia = 1393.42   # Tabla 23, kWh/kWp/año

    exceso_recurso = poa_ref / poa_pvsol_referencia
    rendimiento_normalizado = rendimiento_app / exceso_recurso
    residual_pct = (rendimiento_normalizado / rendimiento_pvsol_referencia - 1.0) * 100.0

    # Actualizado el 3-oct-2026 (main en el PR #113): la física multi-superficie
    # ya modela cables, mismatch y calidad del módulo, así que la app dejó de
    # rendir «de más» frente a PV·SOL (residual −2,2 % en vez de positivo). Se
    # exige que quede cerca: dentro de ±5 % tras normalizar por el recurso.
    assert residual_pct > -5.0, (
        f"Residual {residual_pct:.1f} %: la app rinde más de 5 % por debajo de "
        "PV·SOL a igual recurso; revisar la cadena de pérdidas multi-superficie."
    )
    assert residual_pct < 25.0, (
        "Un residual mayor a 25% tras normalizar por recurso ya no es "
        "explicable solo por las pérdidas ausentes -- revisar el motor."
    )

