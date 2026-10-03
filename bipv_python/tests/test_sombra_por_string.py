# -*- coding: utf-8 -*-
"""Spec 05-perdidas-y-temperatura/sombra-por-string (3-oct-2026).

La sombra de cada superficie era el promedio de sus puntos de análisis y el
bypass la usaba a la vez como fracción de módulos sombreados y como
profundidad de la sombra. Con sombra parcial de balcones (un módulo de un
string totalmente a la sombra), la pérdida salía casi nula. Caso de
validación: fachadas de la Torre 5 (La Salle), 0,28 % frente a ≈ 3,7 % de la
app estándar de referencia.
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


def _tmy_utc():
    idx = pd.date_range("2023-01-01", periods=8760, freq="h", tz="UTC")
    return pd.DataFrame({"T2m": np.full(8760, 20.0)}, index=idx)


def _fs_un_punto_a_la_sombra(malla, puntos, lat, lon, indice_tmy, transparencia):
    """Hora 10: el primer punto con sombra total, los demás al sol."""
    ts = indice_tmy[10].tz_convert("UTC").isoformat().replace("+00:00", "Z")
    return pd.DataFrame({"timestamp_utc": [ts] * len(puntos),
                         "FS_geometrico": [1.0] + [0.0] * (len(puntos) - 1),
                         "Punto": [p["nombre"] for p in puntos]})


def test_cada_superficie_trae_fraccion_y_profundidad(monkeypatch):
    monkeypatch.setattr(sombras_3d, "calcular_fs_horario", _fs_un_punto_a_la_sombra)
    puntos = {"SO": [{"nombre": f"P{i}", "fachada": "SO", "x": 9.0, "y": float(i), "z": 2.0} for i in range(4)]}
    r = calcular_fs_horario_por_superficie(
        trimesh.creation.box(extents=[2.0, 2.0, 2.0]), puntos, 4.65, -74.08, _tmy_utc(),
        {"SO": {"tilt_deg": 90.0, "azimuth_deg": 249.0}}, malla_horizonte="box")["SO"]
    assert r["p_shade"][10] == pytest.approx(0.25)                # el promedio no cambia
    assert r["fraccion_modulos_sombra"][10] == pytest.approx(0.25)
    assert r["profundidad_sombra"][10] == pytest.approx(1.0)
    assert r["fraccion_modulos_sombra"][11] == 0 and r["profundidad_sombra"][11] == 0


def test_viajan_con_la_superficie_y_caducan_con_la_sombra():
    sup = {"nombre": "SO"}
    res = {"SO": {"p_shade": np.zeros(8760), "firma_sombra": {"tmy_fingerprint": "x"},
                  "fraccion_modulos_sombra": np.full(8760, 0.1), "profundidad_sombra": np.full(8760, 0.9),
                  "estado_sombra": "calculado_completo"}}
    [con] = aplicar_sombra_a_superficies([sup], res)
    assert con["fraccion_modulos_sombra"][0] == 0.1 and con["profundidad_sombra"][0] == 0.9
    [sin] = invalidar_sombra_por_cambio_tmy([con], _tmy_utc())          # otro TMY
    assert "fraccion_modulos_sombra" not in sin and "profundidad_sombra" not in sin


def test_se_guardan_con_el_proyecto():
    sup = {"uid": "u1", "nombre": "SO", "tipo": "Fachada", "area_m2": 10.0, "tilt_deg": 90.0,
           "azimuth_deg": 249.0, "fraccion_modulos_sombra": [0.1], "profundidad_sombra": [0.9]}
    guardada = _superficie_input(sup)
    assert guardada["fraccion_modulos_sombra"] == [0.1] and guardada["profundidad_sombra"] == [0.9]


def test_el_modo_fisico_pierde_mas_con_un_modulo_entero_a_la_sombra():
    tmy = _tmy()
    base = _session_state_realista(tmy)
    sup0 = base["superficies_bipv"][0]
    n = int(sup0["n_serie"])
    sol = np.asarray(sup0["p_shade"]) >= 0                           # todas las horas
    frac = np.where(sol, 1 / n, 0.0)

    def energia(con_campos):
        ss = _session_state_realista(tmy)
        s = ss["superficies_bipv"][0]
        s["p_shade"] = frac.copy()
        if con_campos:
            s["fraccion_modulos_sombra"] = frac.copy()
            s["profundidad_sombra"] = np.where(sol, 1.0, 0.0)
        pr = construir_y_recalcular_proyecto_fisico(ss, tmy, lat=_LAT, lon=_LON, alt_m=_ALT_M)
        return pr["superficies"][s["nombre"]]["resultados_ac"]["E_ac_anual_kWh"]

    promedio, por_string = energia(False), energia(True)
    assert por_string < promedio * 0.97                # el módulo sombreado deja de producir


def test_manual_del_asistente_seccion_123():
    kb = (_RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    i = kb.index("## 123.")
    s = kb[i:kb.find("\n## ", i + 5) if kb.find("\n## ", i + 5) > 0 else None]
    for t in ("string", "bypass", "un punto por módulo", "La Salle", "Vista 3D"):
        assert t in s, t
    assert i < kb.rindex("Calculadora BIPV — Innovación Química")
    # Los nombres comerciales se arman por partes para que no aparezcan en el repositorio.
    for prohibido in ("PV" + "syst", "PV" + "·SOL", "PV" + " SOL", "PV" + "SOL", "pendi" + "ente"):
        assert prohibido not in s, prohibido


def test_string_entero_a_media_sombra_produce_la_mitad_y_no_cero():
    from calculos.mismatch_bypass import simular_bypass_horario
    from datos.tecnologias_bipv import ASP_ST1_T40
    sol = (np.arange(8760) % 24 >= 7) & (np.arange(8760) % 24 < 17)
    g = np.where(sol, 700.0, 0.0)
    kw = dict(G_eff=g, T_amb=np.full(8760, 20.0), N_series=18, N_parallel=1, panel=ASP_ST1_T40)
    r = simular_bypass_horario(p_shade=np.where(sol, 1.0, 0.0),
                               profundidad_sombra=np.where(sol, 0.5, 0.0), **kw)
    assert 40 < r["pct_bypass_anual"] < 60          # todos a 350 W/m²: ≈ la mitad


def test_con_un_solo_punto_se_mantiene_el_promedio(monkeypatch):
    monkeypatch.setattr(sombras_3d, "calcular_fs_horario", _fs_un_punto_a_la_sombra)
    puntos = {"SO": [{"nombre": "P0", "fachada": "SO", "x": 9.0, "y": 0.0, "z": 2.0}]}
    r = calcular_fs_horario_por_superficie(
        trimesh.creation.box(extents=[2.0, 2.0, 2.0]), puntos, 4.65, -74.08, _tmy_utc(),
        {"SO": {"tilt_deg": 90.0, "azimuth_deg": 249.0}}, malla_horizonte="box")["SO"]
    assert r["p_shade"][10] == pytest.approx(1.0)
    assert r["fraccion_modulos_sombra"] is None and r["profundidad_sombra"] is None
    [sup] = aplicar_sombra_a_superficies([{"nombre": "SO", "profundidad_sombra": np.ones(8760)}],
                                         {"SO": {**r, "estado_sombra": "calculado_completo"}})
    assert "profundidad_sombra" not in sup          # el dato viejo no se queda
