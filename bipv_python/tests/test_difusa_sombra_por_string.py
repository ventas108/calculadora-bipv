# -*- coding: utf-8 -*-
"""Spec 05-perdidas-y-temperatura/difusa-sombra-por-string (3-oct-2026).

La sombra 3D de cada superficie solo restaba la luz directa: el cielo que
tapan balcones, aleros y edificios vecinos (luz difusa) no llegaba al cálculo
de energía del modo físico. Además, el bypass quitaba también la difusa a los
módulos a la sombra. Caso: La Salle, fachada SO, 4,98 % de sombra en
irradiación frente a 2,83 % de pérdida de energía.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import trimesh

import calculos.sombras_3d as sombras_3d
from calculos.persistencia_multisuperficie import _superficie_input
from calculos.sombras_3d import calcular_fs_horario_por_superficie
from calculos.vinculador_sombra_multisuperficie import (
    aplicar_sombra_a_superficies, construir_y_recalcular_proyecto_fisico, invalidar_sombra_por_cambio_tmy,
)
from tests.test_flujo_fisico_multisuperficie_end_to_end import _ALT_M, _LAT, _LON, _session_state_realista, _tmy

_RAIZ = Path(__file__).resolve().parents[1]
_PUNTOS = [{"nombre": f"P{i}", "fachada": "S", "x": float(i), "y": 0.0, "z": 2.0} for i in range(3)]


def _tmy_utc():
    idx = pd.date_range("2023-01-01", periods=8760, freq="h", tz="UTC")
    return pd.DataFrame({"T2m": np.full(8760, 20.0)}, index=idx)


def _sin_sombra_directa(malla, puntos, lat, lon, indice_tmy, transparencia):
    ts = indice_tmy[10].tz_convert("UTC").isoformat().replace("+00:00", "Z")
    return pd.DataFrame({"timestamp_utc": [ts] * len(puntos), "FS_geometrico": [0.0] * len(puntos),
                         "Punto": [p["nombre"] for p in puntos]})


def _cielo(malla, monkeypatch, transparencia=0.0):
    monkeypatch.setattr(sombras_3d, "calcular_fs_horario", _sin_sombra_directa)
    return calcular_fs_horario_por_superficie(
        malla, {"S": _PUNTOS}, 4.65, -74.08, _tmy_utc(), {"S": {"tilt_deg": 90.0, "azimuth_deg": 180.0}},
        malla_horizonte="m", transparencia=transparencia)["S"]["factor_cielo_visible"]


def test_cada_superficie_trae_su_factor_de_cielo_visible(monkeypatch):
    lejos = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
    lejos.apply_translation([0.0, 300.0, 0.5])                 # detrás de la fachada (al norte)
    assert _cielo(lejos, monkeypatch) == pytest.approx(1.0, abs=0.01)
    muro = trimesh.creation.box(extents=[200.0, 2.0, 10.0])
    muro.apply_translation([0.0, -6.0, 5.0])                   # edificio de 10 m enfrente (al sur)
    tapado = _cielo(muro, monkeypatch)
    assert 0.1 < tapado < 0.7
    # Árboles semitransparentes: tapan menos cielo.
    assert _cielo(muro, monkeypatch, transparencia=0.5) == pytest.approx(1 - (1 - tapado) * 0.5, abs=1e-9)


def test_viaja_con_la_superficie_caduca_y_se_guarda():
    res = {"S": {"p_shade": np.zeros(8760), "firma_sombra": {"tmy_fingerprint": "x"},
                 "factor_cielo_visible": 0.7, "estado_sombra": "calculado_completo"}}
    [con] = aplicar_sombra_a_superficies([{"nombre": "S"}], res)
    assert con["factor_cielo_visible"] == 0.7
    [sin] = invalidar_sombra_por_cambio_tmy([con], _tmy_utc())
    assert "factor_cielo_visible" not in sin
    [vieja] = aplicar_sombra_a_superficies([{"nombre": "S", "factor_cielo_visible": 0.5}],
                                           {"S": {**res["S"], "factor_cielo_visible": None}})
    assert "factor_cielo_visible" not in vieja
    sup = {"uid": "u", "nombre": "S", "tipo": "Fachada", "area_m2": 1.0, "tilt_deg": 90.0,
           "azimuth_deg": 180.0, "factor_cielo_visible": 0.7}
    assert _superficie_input(sup)["factor_cielo_visible"] == 0.7


def test_el_modo_fisico_resta_la_difusa_tapada():
    tmy = _tmy()

    def energia(factor):
        ss = _session_state_realista(tmy)
        if factor is not None:
            ss["superficies_bipv"][0]["factor_cielo_visible"] = factor
        pr = construir_y_recalcular_proyecto_fisico(ss, tmy, lat=_LAT, lon=_LON, alt_m=_ALT_M)
        s = pr["superficies"][ss["superficies_bipv"][0]["nombre"]]
        return s["resultados_ac"]["E_ac_anual_kWh"], s["resultados_dc"]["poa_anual_kWh_m2"]

    (e_base, poa_base), (e_uno, poa_uno), (e_medio, poa_medio) = energia(None), energia(1.0), energia(0.5)
    assert e_uno == pytest.approx(e_base) and poa_uno == pytest.approx(poa_base)
    # Medio cielo tapado: baja la difusa isotrópica (la de alrededor del sol
    # se tapa con la sombra hora a hora, no con el cielo visible).
    assert poa_medio < poa_base * 0.99
    assert e_medio < e_base * 0.99


def test_manual_del_asistente_seccion_124():
    kb = (_RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    i = kb.index("## 124.")
    s = kb[i:kb.find("\n## ", i + 5) if kb.find("\n## ", i + 5) > 0 else None]
    for t in ("difusa", "cielo", "balcon", "La Salle", "Calcular sombra"):
        assert t in s, t
    assert i < kb.rindex("Calculadora BIPV — Innovación Química")
    # Los nombres comerciales se arman por partes para que no aparezcan en el repositorio.
    for prohibido in ("PV" + "syst", "PV" + "·SOL", "PV" + " SOL", "PV" + "SOL", "pendi" + "ente"):
        assert prohibido not in s, prohibido
