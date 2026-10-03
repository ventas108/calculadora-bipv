# -*- coding: utf-8 -*-
"""Escenario de validación externa — East2, SunPower E20-327 (CIEMAT, Madrid).

Reconstruye en la APP, a través del pipeline FÍSICO multi-superficie real
(``calculos.vinculador_sombra_multisuperficie.construir_y_recalcular_proyecto_fisico``),
el caso East2 del artículo *Dealing with Shadows When Modelling BIPV Façades
with Conventional PV Tools* (DOI 10.3390/buildings16091668), usando:

- el módulo SunPower E20-327 ya catalogado en ``datos.tecnologias_bipv``;
- la máscara angular reconstruida de la Tabla 4 del artículo
  (``references/east2-fs-angular-reconstruido.csv``, ya validada en
  ``references/east2-validacion-informe.md``), NUNCA ``p_shade=0``;
- un TMY sintético clear-sky Ineichen (Madrid, 40.45/-3.74, 667 m, T2m=20°C
  constante, año 2023 hora local Europe/Madrid) — la MISMA familia de
  supuesto ya documentada en ``references/east2-validacion-informe.md``
  para la reconstrucción previa vía ``ejecutor_escenarios`` (el artículo usa
  CAMS/ERA5 2017-2023 reales, que no están disponibles en este repositorio).

Este archivo NO valida contra el artículo como homologación oficial (el
artículo no publica una energía anual agregada de East2, ver
``references/buildings-16-01668-east2-caso.md``): valida que (a) el pipeline
físico multi-superficie real de la app puede ejecutar el caso de punta a
punta con datos angulares reales, (b) es determinista, (c) resuelve
correctamente la ficha SunPower E20-327, (d) no mezcla superficies/sombras, y
(e) es sensible a geometría/TMY/sombra — no una tabla de valores fijos.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib
import pytest

from datos.tecnologias_bipv import SUNPOWER_E20_327
from calculos.mismatch_bypass import cargar_csv_fs, alinear_fs_con_tmy
from calculos.transicion_multisuperficie import (
    recalcular_fisica_superficie,
    superficie_nueva,
)
from calculos.vinculador_sombra_multisuperficie import (
    construir_y_recalcular_proyecto_fisico,
)
from calculos.adaptador_multisuperficie import aplicar_proyecto_a_session_state
from calculos.produccion_vigencia import huella_horaria

# ── Parámetros publicados del caso East2 (buildings-16-01668-east2-caso.md) ──
LAT, LON = 40.45, -3.74
ALT_M = 667.0          # NO publicado por el artículo -- supuesto ya documentado
                        # en references/east2-validacion-informe.md, reutilizado
                        # aquí para no mezclar dos supuestos distintos de altitud.
TZ = "Europe/Madrid"
TILT_DEG, AZIMUTH_DEG = 90.0, 82.65   # fachada vertical; azimut publicado
N_SERIE, N_PARALELO = 7, 2             # "7S x 2P", 14 módulos, publicado
ETA_INVERSOR = 0.97   # Fronius IG Plus 50 V-1 no está en datos/catalogo_inversores.py
                        # (solo Fronius Primo 15.0-1); 0.97 es el mismo supuesto ya
                        # documentado en east2-validacion-informe.md, reutilizado
                        # para no inventar un segundo valor sin respaldo.
INVERSOR_ID = "FRONIUS-IGPLUS50-SUPUESTO"

_CSV_EAST2 = (
    Path(__file__).resolve().parents[2] / "references" / "east2-fs-angular-reconstruido.csv"
)
_HORAS_ANIO = 8760


def _tmy_east2_clearsky(t2m: float = 20.0, alt_m: float = ALT_M) -> pd.DataFrame:
    """TMY sintético clear-sky Ineichen para East2 -- mismo supuesto que la
    reconstrucción previa (ejecutor_escenarios), documentado en
    east2-validacion-informe.md. Índice en hora LOCAL Europe/Madrid (no UTC)
    a propósito: calculos.sombras_3d.posiciones_solares() (que generó el CSV
    de sombra) usa exactamente esta misma construcción de índice
    (``pd.date_range("2023-01-01 00:00", "2023-12-31 23:00", freq="h",
    tz="Europe/Madrid")``) -- si el TMY usara UTC, mes/dia/hora ya no
    coincidirían con los del CSV y alinear_fs_con_tmy() desalinearía la
    sombra respecto a la posición solar real que la generó.
    """
    idx = pd.date_range("2023-01-01 00:00", "2023-12-31 23:00", freq="h", tz=TZ)
    assert len(idx) == _HORAS_ANIO
    loc = pvlib.location.Location(latitude=LAT, longitude=LON, altitude=alt_m, tz=TZ)
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


def _p_shade_east2(tmy: pd.DataFrame, modo: str) -> np.ndarray:
    with open(_CSV_EAST2, "rb") as f:
        df_fs, _meta = cargar_csv_fs(f)
    serie = alinear_fs_con_tmy(df_fs, tmy.index, modo=modo, modo_agregacion="auto")
    return serie.to_numpy()


def _superficie_east2(tmy: pd.DataFrame, p_shade: np.ndarray, *, tilt=TILT_DEG,
                       azimuth=AZIMUTH_DEG, nombre="East2") -> dict:
    sup = superficie_nueva(
        nombre=nombre, tipo="Fachada", tilt_deg=tilt, azimuth_deg=azimuth,
        area_m2=SUNPOWER_E20_327["area_m2"] * N_SERIE * N_PARALELO,
        panel=SUNPOWER_E20_327, n_serie=N_SERIE, n_paralelo=N_PARALELO,
        inversor_id=INVERSOR_ID, p_shade=p_shade, albedo=0.2,
    )
    sup["estado_sombra"] = "calculado_completo"
    sup["firma_sombra"] = {
        "geometria": {"tilt_deg": tilt, "azimuth_deg": azimuth},
        "tmy_fingerprint": huella_horaria(tmy.index, tmy["T2m"].to_numpy(dtype=float)),
        "fuente": "east2_tabla4_articulo_10.3390_buildings16091668",
    }
    return sup


def _session_state_east2(tmy: pd.DataFrame, modo: str = "mensual") -> dict:
    p_shade = _p_shade_east2(tmy, modo)
    superficie = _superficie_east2(tmy, p_shade)
    return {
        "panel_dict": SUNPOWER_E20_327,
        "superficies_bipv": [superficie],
        "multisup_inversores": [
            {
                "inversor_id": INVERSOR_ID, "tipo": "dedicado",
                "eta_inversor": ETA_INVERSOR, "P_ac_nom_W": None,
                # Ficha vacía a propósito: Fronius IG Plus 50 V-1 no está en
                # el catálogo con Vdc_max/Vmppt/Isc_max verificados -- no se
                # inventan (regla 4 del encargo). El pipeline debe seguir
                # funcionando y marcar la compatibilidad como "no evaluable"
                # en vez de fallar o inventar un valor.
                "ficha": {},
            },
        ],
    }


# ══════════════════════════════════════════════════════════════════════════
# 1. El escenario corre de punta a punta con la máscara angular real
# ══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("modo", ["mensual", "exacto"])
def test_escenario_east2_corre_con_mascara_angular_real(modo):
    tmy = _tmy_east2_clearsky()
    session_state = _session_state_east2(tmy, modo=modo)

    proyecto = construir_y_recalcular_proyecto_fisico(
        session_state, tmy, lat=LAT, lon=LON, alt_m=ALT_M
    )

    sup = proyecto["superficies"]["East2"]
    assert sup["resultados_dc"] is not None
    assert sup["resultados_ac"] is not None
    # La sombra reconstruida real produce horas de sombra y de bypass -- si
    # esto fuera 0, alguien habría sustituido p_shade por ceros (regla 9).
    assert sup["resultados_dc"]["horas_sombra"] > 3000
    assert sup["resultados_dc"]["horas_bypass"] > 3000
    assert 0.0 < float(np.mean(session_state["superficies_bipv"][0]["p_shade"])) < 1.0

    agregados = proyecto["agregados"]
    assert agregados["n_superficies"] == 1
    assert agregados["E_ac_total_kWh"] > 0.0

    destino: dict = {}
    aplicar_proyecto_a_session_state(proyecto, destino)
    assert destino["multisup_activo"] is True
    assert destino["E_ac_anual_kWh_multisup"] == agregados["E_ac_total_kWh"]


# ══════════════════════════════════════════════════════════════════════════
# 2. Determinismo -- misma entrada, misma firma y mismos resultados
# ══════════════════════════════════════════════════════════════════════════
def test_escenario_east2_es_determinista():
    tmy = _tmy_east2_clearsky()
    session_state_1 = _session_state_east2(tmy, modo="mensual")
    session_state_2 = _session_state_east2(tmy, modo="mensual")

    p1 = construir_y_recalcular_proyecto_fisico(session_state_1, tmy, lat=LAT, lon=LON, alt_m=ALT_M)
    p2 = construir_y_recalcular_proyecto_fisico(session_state_2, tmy, lat=LAT, lon=LON, alt_m=ALT_M)

    assert p1["superficies"]["East2"]["huellas"] == p2["superficies"]["East2"]["huellas"]
    assert p1["agregados"]["huella"] == p2["agregados"]["huella"]
    assert (
        p1["superficies"]["East2"]["resultados_ac"]["E_ac_anual_kWh"]
        == p2["superficies"]["East2"]["resultados_ac"]["E_ac_anual_kWh"]
    )


@pytest.mark.parametrize(
    ("modo", "dc_kwh", "ac_kwh", "horas_sombra", "p_shade_medio"),
    [
        # Anclas actualizadas el 3-oct-2026 con main en el PR #113 (antes
        # 2373.9/2302.7/3563 y 2379.8/2308.4/3536, 22-sep): la física
        # multi-superficie ahora aplica la cadena óptica del Motor Óptico,
        # calidad del módulo, mismatch y cables (-8,1 % en DC). La POA y la
        # p_shade no cambian. Ver references/informe-lasalle-east2-sobre-main-2026-10-03.md.
        ("mensual", 2182.1, 2116.7, 3558, 0.38594211095890407),
        ("exacto", 2187.8, 2122.2, 3531, 0.3552770547945206),
    ],
)
def test_resultados_numericos_east2_son_la_referencia_reproducible(
    modo, dc_kwh, ac_kwh, horas_sombra, p_shade_medio
):
    """Fija la salida del TMY sintético y la Tabla 4, no un valor del artículo.

    El artículo no publica energía anual East2; estos valores son anclas de
    regresión de esta reconstrucción concreta y deben cambiarse junto con el
    informe si cambia un supuesto de entrada.
    """
    tmy = _tmy_east2_clearsky()
    session_state = _session_state_east2(tmy, modo=modo)
    proyecto = construir_y_recalcular_proyecto_fisico(
        session_state, tmy, lat=LAT, lon=LON, alt_m=ALT_M
    )
    sup = proyecto["superficies"]["East2"]
    dc, ac = sup["resultados_dc"], sup["resultados_ac"]

    assert dc["poa_anual_kWh_m2"] == pytest.approx(1038.81, abs=0.01)
    assert dc["E_dc_anual_kWh"] == pytest.approx(dc_kwh, abs=0.01)
    assert ac["E_ac_anual_kWh"] == pytest.approx(ac_kwh, abs=0.01)
    assert dc["horas_sombra"] == horas_sombra
    assert dc["horas_bypass"] == horas_sombra
    assert float(np.mean(session_state["superficies_bipv"][0]["p_shade"])) == pytest.approx(
        p_shade_medio, abs=1e-12
    )


# ══════════════════════════════════════════════════════════════════════════
# 3. SunPower E20-327 se resuelve correctamente (ficha de placa)
# ══════════════════════════════════════════════════════════════════════════
def test_sunpower_e20_327_ficha_coincide_con_el_articulo():
    """Pmax, Voc, Isc, Vmp, Imp y eficiencia deben coincidir con la ficha
    pública citada por el artículo (327 W, 20.1%) dentro de redondeo."""
    panel = SUNPOWER_E20_327
    assert panel["Pmax_stc"] == pytest.approx(327.106, abs=0.2)
    assert panel["Voc_stc"] == pytest.approx(64.9, abs=0.05)
    assert panel["Isc_stc"] == pytest.approx(6.46, abs=0.01)
    assert panel["Vmp_stc"] == pytest.approx(54.7, abs=0.05)
    assert panel["Imp_stc"] == pytest.approx(5.98, abs=0.01)
    eficiencia_pct = panel["Pmax_stc"] / (panel["area_m2"] * 1000.0) * 100.0
    assert eficiencia_pct == pytest.approx(20.1, abs=0.1)


def test_sunpower_e20_327_resuelve_potencia_dc_stc_del_string():
    tmy = _tmy_east2_clearsky()
    session_state = _session_state_east2(tmy, modo="mensual")
    proyecto = construir_y_recalcular_proyecto_fisico(session_state, tmy, lat=LAT, lon=LON, alt_m=ALT_M)
    sup = proyecto["superficies"]["East2"]
    esperado_kW = SUNPOWER_E20_327["Pmax_stc"] * N_SERIE * N_PARALELO / 1000.0
    assert sup["resultados_ac"]["P_dc_stc_kW"] == pytest.approx(esperado_kW, abs=0.01)
    assert esperado_kW == pytest.approx(4.578, abs=0.01)  # 327.106 W x 14


# ══════════════════════════════════════════════════════════════════════════
# 4. Dos superficies (East2 + control) no mezclan geometría, POA ni sombra
# ══════════════════════════════════════════════════════════════════════════
def test_east2_no_mezcla_con_otra_superficie_del_mismo_proyecto():
    tmy = _tmy_east2_clearsky()
    p_shade_east2 = _p_shade_east2(tmy, modo="mensual")
    sup_east2 = _superficie_east2(tmy, p_shade_east2)

    # Superficie de control: mismo panel, geometría y sombra DISTINTAS
    # (techo horizontal, sin sombra) -- si algo se mezclara, esta superficie
    # heredaría sombra o POA de East2, o viceversa.
    p_shade_control = np.zeros(_HORAS_ANIO)
    sup_control = superficie_nueva(
        nombre="Control-techo", tipo="Techo", tilt_deg=10.0, azimuth_deg=180.0,
        area_m2=SUNPOWER_E20_327["area_m2"] * N_SERIE * N_PARALELO,
        panel=SUNPOWER_E20_327, n_serie=N_SERIE, n_paralelo=N_PARALELO,
        inversor_id=INVERSOR_ID, p_shade=p_shade_control, albedo=0.2,
    )
    sup_control["estado_sombra"] = "calculado_completo"
    sup_control["firma_sombra"] = {
        "geometria": {"tilt_deg": 10.0, "azimuth_deg": 180.0},
        "tmy_fingerprint": huella_horaria(tmy.index, tmy["T2m"].to_numpy(dtype=float)),
        "fuente": "control_sin_sombra",
    }

    session_state = {
        "panel_dict": SUNPOWER_E20_327,
        "superficies_bipv": [sup_east2, sup_control],
        "multisup_inversores": [
            {"inversor_id": INVERSOR_ID, "tipo": "compartido",
             "eta_inversor": ETA_INVERSOR, "P_ac_nom_W": None, "ficha": {}},
        ],
    }
    proyecto = construir_y_recalcular_proyecto_fisico(session_state, tmy, lat=LAT, lon=LON, alt_m=ALT_M)

    e2 = proyecto["superficies"]["East2"]
    ctrl = proyecto["superficies"]["Control-techo"]

    # Geometrías, POA y sombra deben ser distintas entre las dos superficies.
    assert e2["huellas"]["geometria"] != ctrl["huellas"]["geometria"]
    assert e2["huellas"]["poa"] != ctrl["huellas"]["poa"]
    assert e2["huellas"]["sombra"] != ctrl["huellas"]["sombra"]
    assert e2["resultados_dc"]["poa_anual_kWh_m2"] != ctrl["resultados_dc"]["poa_anual_kWh_m2"]
    # Control sin sombra: 0 horas de sombra/bypass; East2 con sombra real: >3000.
    assert ctrl["resultados_dc"]["horas_sombra"] == 0
    assert e2["resultados_dc"]["horas_sombra"] > 3000

    bus = proyecto["resultados_bus"][INVERSOR_ID]
    assert set(bus["superficies"]) == {"East2", "Control-techo"}


# ══════════════════════════════════════════════════════════════════════════
# 5. Sensibilidad -- tilt, azimuth, TMY y sombra deben cambiar el resultado
# ══════════════════════════════════════════════════════════════════════════
def test_cambiar_tilt_cambia_huella_y_resultado():
    tmy = _tmy_east2_clearsky()
    p_shade = _p_shade_east2(tmy, modo="mensual")
    base = _superficie_east2(tmy, p_shade, tilt=90.0)
    alterada = _superficie_east2(tmy, p_shade, tilt=45.0)

    def _correr(sup):
        ss = {
            "panel_dict": SUNPOWER_E20_327, "superficies_bipv": [sup],
            "multisup_inversores": [
                {"inversor_id": INVERSOR_ID, "tipo": "dedicado",
                 "eta_inversor": ETA_INVERSOR, "P_ac_nom_W": None, "ficha": {}},
            ],
        }
        return construir_y_recalcular_proyecto_fisico(ss, tmy, lat=LAT, lon=LON, alt_m=ALT_M)

    p_base = _correr(base)["superficies"]["East2"]
    p_alt = _correr(alterada)["superficies"]["East2"]
    assert p_base["huellas"]["geometria"] != p_alt["huellas"]["geometria"]
    assert p_base["huellas"]["poa"] != p_alt["huellas"]["poa"]
    assert p_base["resultados_dc"]["poa_anual_kWh_m2"] != p_alt["resultados_dc"]["poa_anual_kWh_m2"]


def test_cambiar_azimuth_cambia_huella_y_resultado():
    tmy = _tmy_east2_clearsky()
    p_shade = _p_shade_east2(tmy, modo="mensual")
    base = _superficie_east2(tmy, p_shade, azimuth=82.65)
    alterada = _superficie_east2(tmy, p_shade, azimuth=180.0)

    def _correr(sup):
        ss = {
            "panel_dict": SUNPOWER_E20_327, "superficies_bipv": [sup],
            "multisup_inversores": [
                {"inversor_id": INVERSOR_ID, "tipo": "dedicado",
                 "eta_inversor": ETA_INVERSOR, "P_ac_nom_W": None, "ficha": {}},
            ],
        }
        return construir_y_recalcular_proyecto_fisico(ss, tmy, lat=LAT, lon=LON, alt_m=ALT_M)

    p_base = _correr(base)["superficies"]["East2"]
    p_alt = _correr(alterada)["superficies"]["East2"]
    assert p_base["huellas"]["geometria"] != p_alt["huellas"]["geometria"]
    assert p_base["resultados_dc"]["poa_anual_kWh_m2"] != p_alt["resultados_dc"]["poa_anual_kWh_m2"]


def test_cambiar_tmy_invalida_la_sombra_y_cambia_el_resultado():
    """TMY distinto -> firma_sombra queda obsoleta (tmy_fingerprint no
    coincide) -> invalidar_sombra_por_cambio_tmy() retira p_shade/firma_sombra
    -> construir_proyecto_desde_session_state() debe rechazar la superficie
    (p_shade ausente), igual que exige el flujo real de Recurso Solar."""
    tmy_original = _tmy_east2_clearsky(t2m=20.0)
    tmy_distinto = _tmy_east2_clearsky(t2m=35.0)  # mismo sitio, T2m distinta -> huella distinta
    session_state = _session_state_east2(tmy_original, modo="mensual")

    with pytest.raises(ValueError, match="p_shade|firma_sombra|NOCT"):
        construir_y_recalcular_proyecto_fisico(
            session_state, tmy_distinto, lat=LAT, lon=LON, alt_m=ALT_M
        )


def test_tmy_nuevo_con_sombra_regenerada_cambia_el_resultado():
    """Tras invalidar, regenerar sombra/firma permite recalcular el nuevo TMY."""
    tmy_original = _tmy_east2_clearsky(t2m=20.0)
    tmy_distinto = _tmy_east2_clearsky(t2m=35.0)
    base = _session_state_east2(tmy_original, modo="mensual")
    nuevo = _session_state_east2(tmy_distinto, modo="mensual")

    p_base = construir_y_recalcular_proyecto_fisico(
        base, tmy_original, lat=LAT, lon=LON, alt_m=ALT_M
    )
    p_nuevo = construir_y_recalcular_proyecto_fisico(
        nuevo, tmy_distinto, lat=LAT, lon=LON, alt_m=ALT_M
    )
    s_base = p_base["superficies"]["East2"]
    s_nuevo = p_nuevo["superficies"]["East2"]

    assert (
        s_base["_firma_sombra"]["tmy_fingerprint"]
        != s_nuevo["_firma_sombra"]["tmy_fingerprint"]
    )
    assert s_base["huellas"]["resultados_dc"] != s_nuevo["huellas"]["resultados_dc"]
    assert s_base["resultados_ac"]["E_ac_anual_kWh"] != s_nuevo["resultados_ac"]["E_ac_anual_kWh"]


def test_cambiar_mascara_de_sombra_cambia_el_resultado():
    """Los modos mensual/exacto usan la misma máscara, pero agregan distinto."""
    tmy = _tmy_east2_clearsky()
    ss_mensual = _session_state_east2(tmy, modo="mensual")
    ss_exacto = _session_state_east2(tmy, modo="exacto")

    p_mensual = construir_y_recalcular_proyecto_fisico(ss_mensual, tmy, lat=LAT, lon=LON, alt_m=ALT_M)
    p_exacto = construir_y_recalcular_proyecto_fisico(ss_exacto, tmy, lat=LAT, lon=LON, alt_m=ALT_M)

    e_ac_mensual = p_mensual["superficies"]["East2"]["resultados_ac"]["E_ac_anual_kWh"]
    e_ac_exacto = p_exacto["superficies"]["East2"]["resultados_ac"]["E_ac_anual_kWh"]
    assert e_ac_mensual != e_ac_exacto
    assert (
        p_mensual["superficies"]["East2"]["huellas"]["sombra"]
        != p_exacto["superficies"]["East2"]["huellas"]["sombra"]
    )


def test_mascara_de_sombra_realmente_alterada_cambia_huella_y_energia():
    """Una modificación efectiva de p_shade no puede pasar desapercibida."""
    tmy = _tmy_east2_clearsky()
    p_shade_original = _p_shade_east2(tmy, modo="mensual")
    p_shade_alterado = np.clip(p_shade_original * 0.80, 0.0, 1.0)

    def _correr(p_shade):
        ss = {
            "panel_dict": SUNPOWER_E20_327,
            "superficies_bipv": [_superficie_east2(tmy, p_shade)],
            "multisup_inversores": [
                {"inversor_id": INVERSOR_ID, "tipo": "dedicado",
                 "eta_inversor": ETA_INVERSOR, "P_ac_nom_W": None, "ficha": {}},
            ],
        }
        return construir_y_recalcular_proyecto_fisico(
            ss, tmy, lat=LAT, lon=LON, alt_m=ALT_M
        )

    original = _correr(p_shade_original)["superficies"]["East2"]
    alterado = _correr(p_shade_alterado)["superficies"]["East2"]
    assert original["huellas"]["sombra"] != alterado["huellas"]["sombra"]
    assert alterado["resultados_ac"]["E_ac_anual_kWh"] > original["resultados_ac"]["E_ac_anual_kWh"]


def test_sombra_cero_no_sustituye_a_la_mascara_real():
    """Guarda contra una regresión silenciosa: la energía con la máscara
    angular real debe ser estrictamente menor que con p_shade=0 (regla 9 --
    nunca sustituir la sombra real por cero)."""
    tmy = _tmy_east2_clearsky()
    ss_con_sombra = _session_state_east2(tmy, modo="mensual")
    sup_sin_sombra = _superficie_east2(tmy, np.zeros(_HORAS_ANIO))
    ss_sin_sombra = {
        "panel_dict": SUNPOWER_E20_327, "superficies_bipv": [sup_sin_sombra],
        "multisup_inversores": [
            {"inversor_id": INVERSOR_ID, "tipo": "dedicado",
             "eta_inversor": ETA_INVERSOR, "P_ac_nom_W": None, "ficha": {}},
        ],
    }

    p_con_sombra = construir_y_recalcular_proyecto_fisico(ss_con_sombra, tmy, lat=LAT, lon=LON, alt_m=ALT_M)
    p_sin_sombra = construir_y_recalcular_proyecto_fisico(ss_sin_sombra, tmy, lat=LAT, lon=LON, alt_m=ALT_M)

    e_con = p_con_sombra["superficies"]["East2"]["resultados_ac"]["E_ac_anual_kWh"]
    e_sin = p_sin_sombra["superficies"]["East2"]["resultados_ac"]["E_ac_anual_kWh"]
    assert e_con < e_sin


# ══════════════════════════════════════════════════════════════════════════
# 6. Coherencia radiativa (QCRad, Long & Shi 2008) del TMY sintético East2
# ══════════════════════════════════════════════════════════════════════════
# Auditoría 22-sep-2026: se pidió confirmar si el TMY sintético de East2
# produce la advertencia "Inconsistencia radiativa" que emite
# calculos.solar.verificar_consistencia_radiativa() (usada internamente por
# calcular_poa() en cada llamada). Verificado con evidencia cuantitativa
# (capturando poa_df.attrs["qcrad"] y las UserWarning emitidas): el TMY de
# East2 construido en este archivo tiene 0.0% de horas inconsistentes tanto
# en modo mensual como exacto, con o sin sombra -- CERO advertencias QCRad.
# La advertencia que SÍ aparece al correr la batería completa junto con
# test_transicion_multisuperficie.py / test_flujo_fisico_multisuperficie_
# end_to_end.py proviene de los fixtures `_tmy()` de ESOS archivos (una
# aproximación sinusoidal G_h/Gb_n/Gd_h que su propio docstring ya advierte
# "no pretende ser un TMY real"), no de East2 -- no comparten TMY, session
# ni estado con las pruebas de este archivo. Esas pruebas quedan fuera de
# este cambio (regla 3 del encargo: no tocar TMY/fixtures ajenos a East2).
# Estas dos pruebas son el guardián permanente pedido para East2.
def test_tmy_east2_es_radiativamente_coherente_qcrad():
    """El TMY sintético de East2 (clear-sky Ineichen, pvlib) cierra
    físicamente GHI=DNI*cosZ+DHI por construcción: ambos componentes salen
    de la MISMA llamada a `Location.get_clearsky()` sobre el MISMO índice
    que luego usa `calcular_poa()` para la posición solar -- no hay margen
    para que se desalineen. Se verifica con evidencia cuantitativa, no solo
    con la ausencia de la advertencia."""
    tmy = _tmy_east2_clearsky()
    p_shade = _p_shade_east2(tmy, modo="mensual")
    sup = _superficie_east2(tmy, p_shade)

    with warnings.catch_warnings(record=True) as capturadas:
        warnings.simplefilter("always", UserWarning)
        nueva = recalcular_fisica_superficie(sup, tmy, LAT, LON, ALT_M)

    de_qcrad = [
        w for w in capturadas
        if issubclass(w.category, UserWarning) and "radiativa" in str(w.message)
    ]
    assert not de_qcrad, f"QCRad emitió advertencia inesperada: {de_qcrad}"

    qcrad = nueva["poa_df"].attrs.get("qcrad")
    assert qcrad is not None, "calcular_poa() debe adjuntar el diagnóstico QCRad en .attrs"
    assert qcrad["horas_evaluadas"] > 4000
    assert qcrad["horas_inconsistentes"] == 0
    assert qcrad["pct_inconsistente"] == pytest.approx(0.0, abs=1e-9)
    assert qcrad["diferencia_media_wm2"] == pytest.approx(0.0, abs=1e-6)


@pytest.mark.parametrize("modo", ["mensual", "exacto"])
def test_tmy_east2_coherente_con_y_sin_sombra(modo):
    """La coherencia QCRad depende solo del TMY y la geometría (POA), nunca
    de `p_shade` -- debe seguir en 0% de inconsistencia con la máscara real
    de sombra Y con la referencia sin sombra, en ambos modos de alineación."""
    tmy = _tmy_east2_clearsky()
    for p_shade in (_p_shade_east2(tmy, modo=modo), np.zeros(_HORAS_ANIO)):
        sup = _superficie_east2(tmy, p_shade)
        with warnings.catch_warnings(record=True) as capturadas:
            warnings.simplefilter("always", UserWarning)
            nueva = recalcular_fisica_superficie(sup, tmy, LAT, LON, ALT_M)
        assert not any(
            issubclass(w.category, UserWarning) and "radiativa" in str(w.message)
            for w in capturadas
        )
        assert nueva["poa_df"].attrs["qcrad"]["pct_inconsistente"] == pytest.approx(0.0, abs=1e-9)


def test_tmy_east2_coherencia_qcrad_es_determinista():
    """Dos construcciones independientes del mismo TMY East2 deben dar
    exactamente el mismo diagnóstico QCRad (mismo dict, no solo mismo
    veredicto de advertencia)."""
    tmy_1 = _tmy_east2_clearsky()
    tmy_2 = _tmy_east2_clearsky()
    p_shade = _p_shade_east2(tmy_1, modo="mensual")

    sup_1 = _superficie_east2(tmy_1, p_shade)
    sup_2 = _superficie_east2(tmy_2, p_shade)
    r1 = recalcular_fisica_superficie(sup_1, tmy_1, LAT, LON, ALT_M)
    r2 = recalcular_fisica_superficie(sup_2, tmy_2, LAT, LON, ALT_M)

    assert r1["poa_df"].attrs["qcrad"] == r2["poa_df"].attrs["qcrad"]
