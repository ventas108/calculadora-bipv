# -*- coding: utf-8 -*-
"""Spec 05-perdidas-y-temperatura/puntos-automaticos-por-modulo: sombra de
cada string (puntos generados con su string) hasta el modo físico."""
import numpy as np
import pandas as pd
import pytest
import trimesh

import calculos.sombras_3d as sombras_3d
from calculos.adaptador_multisuperficie import construir_proyecto_desde_session_state
from calculos.persistencia_multisuperficie import _superficie_input
from calculos.sombras_3d import calcular_fs_horario_por_superficie
from calculos.vinculador_sombra_multisuperficie import (
    aplicar_sombra_a_superficies, construir_y_recalcular_proyecto_fisico, invalidar_sombra_por_cambio_tmy,
)
from tests.test_flujo_fisico_multisuperficie_end_to_end import _ALT_M, _LAT, _LON, _session_state_realista, _tmy


def _tmy_utc():
    idx = pd.date_range("2023-01-01", periods=8760, freq="h", tz="UTC")
    return pd.DataFrame({"T2m": np.full(8760, 20.0)}, index=idx)


def _fs(malla, puntos, lat, lon, indice_tmy, transparencia):
    ts = indice_tmy[10].tz_convert("UTC").isoformat().replace("+00:00", "Z")
    return pd.DataFrame({"timestamp_utc": [ts] * len(puntos),
                         "FS_geometrico": [1.0] + [0.0] * (len(puntos) - 1),
                         "Punto": [p["nombre"] for p in puntos]})


def _puntos(con_string=True):
    pts = [{"nombre": f"P{i}", "fachada": "S", "x": 9.0, "y": float(i), "z": 2.0} for i in range(4)]
    if con_string:
        for p, s in zip(pts, ["G1-S1", "G1-S1", "G1-S2", "G1-S2"]):
            p["string"] = s
    return pts


def _calc(monkeypatch, pts):
    monkeypatch.setattr(sombras_3d, "calcular_fs_horario", _fs)
    return calcular_fs_horario_por_superficie(
        trimesh.creation.box(extents=[1.0, 1.0, 1.0]), {"S": pts}, 4.65, -74.08, _tmy_utc(),
        {"S": {"tilt_deg": 90.0, "azimuth_deg": 249.0}}, malla_horizonte="m")["S"]


def test_cada_string_trae_su_fraccion_y_profundidad(monkeypatch):
    r = _calc(monkeypatch, _puntos())
    s1, s2 = r["sombra_por_string"]["G1-S1"], r["sombra_por_string"]["G1-S2"]
    assert s1["fraccion"][10] == pytest.approx(0.5) and s1["profundidad"][10] == pytest.approx(1.0)
    assert s2["fraccion"][10] == 0 and s2["profundidad"][10] == 0
    assert r["fraccion_modulos_sombra"][10] == pytest.approx(0.25)        # la superficie sigue igual
    assert _calc(monkeypatch, _puntos(False))["sombra_por_string"] is None


def test_viaja_caduca_y_se_guarda():
    sps = {"G1-S1": {"fraccion": np.full(8760, 0.5), "profundidad": np.ones(8760)}}
    res = {"S": {"p_shade": np.zeros(8760), "firma_sombra": {"tmy_fingerprint": "x"},
                 "sombra_por_string": sps, "estado_sombra": "calculado_completo"}}
    [con] = aplicar_sombra_a_superficies([{"nombre": "S"}], res)
    assert con["sombra_por_string"]["G1-S1"]["fraccion"][0] == 0.5
    assert "sombra_por_string" not in invalidar_sombra_por_cambio_tmy([con], _tmy_utc())[0]
    [vieja] = aplicar_sombra_a_superficies([{"nombre": "S", "sombra_por_string": sps}],
                                           {"S": {**res["S"], "sombra_por_string": None}})
    assert "sombra_por_string" not in vieja
    sup = {"uid": "u", "nombre": "S", "tipo": "Fachada", "area_m2": 1.0, "tilt_deg": 90.0,
           "azimuth_deg": 180.0, "sombra_por_string": sps}
    assert "G1-S1" in _superficie_input(sup)["sombra_por_string"]


def _con_strings(ss, sombras):
    s = ss["superficies_bipv"][0]
    s["sombra_por_string"] = sombras
    return ss


def test_el_adaptador_reparte_los_strings_de_cada_grupo():
    tmy = _tmy()
    ss = _session_state_realista(tmy)
    s = ss["superficies_bipv"][0]
    n_par = int(s.get("n_paralelo") or s["grupos"][0]["n_paralelo"])
    gid = (s.get("grupos") or [{"gid": "G1"}])[0].get("gid", "G1")
    sombras = {f"{gid}-S{k}": {"fraccion": np.zeros(8760), "profundidad": np.zeros(8760)}
               for k in range(1, n_par + 1)}
    pr = construir_proyecto_desde_session_state(_con_strings(ss, sombras))
    unidad = next(iter(pr["superficies"].values()))
    assert len(unidad["sombra_strings"]) == n_par
    # Si los strings no cuadran con el grupo, la sombra está desactualizada.
    sombras.pop(f"{gid}-S1")
    if n_par >= 1:
        with pytest.raises(ValueError, match="Calcular sombra"):
            construir_proyecto_desde_session_state(_con_strings(_session_state_realista(tmy), sombras))


def test_el_modo_fisico_usa_la_sombra_de_cada_string():
    tmy = _tmy()
    base_ss = _session_state_realista(tmy)
    s = base_ss["superficies_bipv"][0]
    n_par = int(s.get("n_paralelo") or s["grupos"][0]["n_paralelo"])
    gid = (s.get("grupos") or [{"gid": "G1"}])[0].get("gid", "G1")
    if n_par < 2:
        pytest.skip("el escenario de referencia necesita 2 strings o más")
    uno, medio, cero = np.ones(8760), np.full(8760, 0.5), np.zeros(8760)

    def energia(ss):
        pr = construir_y_recalcular_proyecto_fisico(ss, tmy, lat=_LAT, lon=_LON, alt_m=_ALT_M)
        return pr["superficies"][s["nombre"]]["resultados_ac"]["E_ac_anual_kWh"]

    sin = energia(_session_state_realista(tmy))
    strings = {f"{gid}-S{k}": {"fraccion": uno if k == 1 else cero, "profundidad": medio if k == 1 else cero}
               for k in range(1, n_par + 1)}
    con = energia(_con_strings(_session_state_realista(tmy), strings))
    # Un string de n_par a media luz: se pierde ≈ la mitad de ese string.
    assert con == pytest.approx(sin * (1 - 0.5 / n_par), rel=0.03)
