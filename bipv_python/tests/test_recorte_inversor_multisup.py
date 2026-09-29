# -*- coding: utf-8 -*-
"""Spec ``05-perdidas-y-temperatura/recorte-inversor-multisuperficie`` (29-sep-2026).

En 🗺️ Vista 3D solo el modo físico recortaba la salida de cada inversor a su
potencia AC nominal. Los modos simplificado y bypass publicaban POA × área ×
η × PR sin ese límite: con un inversor chico (DC/AC alto) la energía salía
más alta de lo que el inversor deja pasar. Ahora el recorte se calcula hora a
hora por inversor (sumando sus grupos, incluso de superficies distintas) y
baja el PR de las superficies de ese inversor.
"""
from pathlib import Path

import numpy as np
import pytest

from calculos.cadena_perdidas_multisup import (
    cadena_superficies_estado,
    firma_cadena,
    parametros_cadena,
    pr_por_superficie,
    tabla_desglose,
)
from calculos.diseno_electrico_multisup import superficies_para_energia
from calculos.multi_superficie import calcular_poa_superficie, e_ac_total_multisup
from calculos.recorte_inversores_multisup import factores_recorte
from datos.tecnologias_bipv import MODULOS_BIPV
from tests.test_simulation_pipeline import _tmy_sintetico_offline

VISTA_3D = Path(__file__).resolve().parents[1] / "pages" / "9_🗺️_Vista_3D.py"
LAT, LON, ALT = 7.883, -76.6259, 44
SPR = "SPR-E20-327 (E20-327NE-WHT-D)"
PMAX = float(MODULOS_BIPV[SPR]["Pmax_stc"])


def _sup(nombre, uid, az, grupos, tilt=10):
    return {"nombre": nombre, "uid": uid, "tipo": "Cubierta", "tilt_deg": tilt, "azimuth_deg": az,
            "area_m2": 500.0, "activa": True, "grupos": grupos}


def _grupo(gid, inv, ns, npar, cruce=None):
    g = {"gid": gid, "topologia": "string", "inversor_id": inv, "mppt": 1,
         "n_serie": ns, "n_paralelo": npar}
    if cruce:
        g["cruce"] = cruce
    return g


def _inv(inv_id, p_ac_w, eta=0.97):
    return {"inversor_id": inv_id, "clase": "string", "origen_ficha": "manual", "nombre": inv_id,
            "ficha": {}, "eta_inversor": eta, "P_ac_nom_W": p_ac_w}


def _paneles():
    return {n: {"panel": dict(MODULOS_BIPV[SPR]), "nombre": SPR} for n in ("Este", "Oeste")}


def _proyecto(inv_oeste="INV-1", cruce=None):
    # 20 × 2 módulos en cada superficie → 40 × 327 W = 13,08 kWp por superficie
    este = _sup("Este", "u1", 90, [_grupo("G1", "INV-1", 20, 2, cruce)])
    oeste = _sup("Oeste", "u2", 270, [_grupo("G1", inv_oeste, 20, 2)])
    return [este, oeste]


@pytest.fixture(scope="module")
def tmy():
    return _tmy_sintetico_offline(LAT, LON, ALT)


@pytest.fixture(scope="module")
def poas(tmy):
    return {n: calcular_poa_superficie(tmy, LAT, LON, ALT, {"tilt_deg": 10, "azimuth_deg": az})
            for n, az in (("Este", 90), ("Oeste", 270))}


def _estado(tmy, poas, inversores):
    return {"tmy_df": tmy.set_axis(poas["Este"].index), "multisup_inversores": inversores}


def _cadena(tmy, poas, inversores, sups=None):
    sups = superficies_para_energia(sups or _proyecto(), _paneles())
    r, e = cadena_superficies_estado(_estado(tmy, poas, inversores), sups, poas, _paneles())
    assert not e
    return sups, r


# ── Criterio 1: la cadena trae el perfil horario de AC ─────────────────────────
def test_cadena_trae_perfil_ac_normalizado(tmy, poas):
    _, r = _cadena(tmy, poas, [_inv("INV-1", 1e9)])
    for n in ("Este", "Oeste"):
        perfil = np.asarray(r[n]["perfil_ac"], dtype=float)
        assert perfil.shape == (8760,)
        assert perfil.min() >= 0.0
        assert perfil.sum() == pytest.approx(1.0)


# ── Criterio 2: inversor grande → nada cambia ─────────────────────────────────
def test_inversor_grande_no_recorta_y_pr_identico(tmy, poas):
    _, r_sin = _cadena(tmy, poas, [_inv("INV-1", None)])
    _, r_big = _cadena(tmy, poas, [_inv("INV-1", 1e9)])
    for n in ("Este", "Oeste"):
        assert r_big[n]["pr"] == pytest.approx(r_sin[n]["pr"], rel=1e-12)
        assert r_big[n].get("f_recorte", 1.0) == 1.0
    assert "Recorte inversor" not in tabla_desglose(r_big)[0]


# ── Criterio 3: inversor chico → recorte exacto hora a hora ───────────────────
def test_inversor_chico_recorta_exacto_hora_a_hora(tmy, poas):
    sups, r_sin = _cadena(tmy, poas, [_inv("INV-1", None)])
    p_ac = 12_000.0  # 26,16 kWp de paneles → DC/AC 2,18
    _, r = _cadena(tmy, poas, [_inv("INV-1", p_ac)])
    # Lo esperado a mano: potencia AC horaria de cada superficie, suma, recorte
    total = np.zeros(8760)
    e_sin = {}
    for s in sups:
        n = s["nombre"]
        e = r_sin[n]["poa_bruta_kWh_m2"] * s["modulos"] * PMAX / 1000.0 * r_sin[n]["pr"]
        e_sin[n] = e
        total += e * np.asarray(r_sin[n]["perfil_ac"], dtype=float)
    esperado_total = np.minimum(total, p_ac / 1000.0).sum()
    e_con = {s["nombre"]: r_sin[s["nombre"]]["poa_bruta_kWh_m2"] * s["modulos"] * PMAX / 1000.0
             * r[s["nombre"]]["pr"] for s in sups}
    assert sum(e_con.values()) == pytest.approx(esperado_total, rel=1e-9)
    assert sum(e_sin.values()) - sum(e_con.values()) > 0.05 * sum(e_sin.values())
    for n in ("Este", "Oeste"):
        assert 0.0 < r[n]["f_recorte"] < 1.0
        assert r[n]["recorte_kWh"] == pytest.approx(e_sin[n] - e_con[n], rel=1e-9)
    filas = {f["Superficie"]: f for f in tabla_desglose(r)}
    assert "Recorte inversor" in filas["Este"]


# ── Criterio 4: cada inversor recorta solo lo suyo ────────────────────────────
def test_dos_inversores_solo_recorta_el_chico(tmy, poas):
    invs = [_inv("INV-1", 5_000.0), _inv("INV-2", 1e9)]
    _, r = _cadena(tmy, poas, invs, _proyecto(inv_oeste="INV-2"))
    assert r["Este"]["f_recorte"] < 1.0
    assert r["Oeste"].get("f_recorte", 1.0) == 1.0


# ── Criterio 5: string que cruza → su recorte se reparte en las dos ───────────
def test_string_que_cruza_reparte_el_recorte(tmy, poas):
    invs = [_inv("INV-1", 3_000.0), _inv("INV-2", 1e9)]
    sups = _proyecto(inv_oeste="INV-2", cruce={"uid": "u2", "modulos": 10})
    _, r = _cadena(tmy, poas, invs, sups)
    # Este (INV-1) tiene 10 × 2 módulos en Oeste: los dos pierden por INV-1
    assert r["Este"]["f_recorte"] < 1.0
    assert r["Oeste"]["f_recorte"] < 1.0
    assert r["Oeste"]["f_recorte"] > r["Este"]["f_recorte"]


# ── Criterio 6: resumen por inversor para la pantalla ─────────────────────────
def test_resumen_por_inversor(tmy, poas):
    sups, r_sin = _cadena(tmy, poas, [_inv("INV-1", None)])
    res = factores_recorte(sups, r_sin, _paneles(), [_inv("INV-1", 12_000.0)])
    inv = res["inversores"][0]
    assert inv["inversor_id"] == "INV-1"
    assert inv["recorte_kWh"] > 0 and inv["horas"] > 0
    assert inv["pct"] == pytest.approx(inv["recorte_kWh"] / inv["e_sin_recorte_kWh"] * 100)
    total_sup = sum(d["recorte_kWh"] for d in res["superficies"].values())
    assert total_sup == pytest.approx(inv["recorte_kWh"], rel=1e-9)


def test_inversor_sin_potencia_ac_no_recorta():
    res = factores_recorte([], {}, {}, [_inv("INV-1", None)])
    assert res["superficies"] == {}
    assert res["inversores"] == [] or res["inversores"][0]["recorte_kWh"] == 0.0


# ── Criterio 7: la energía publicada baja exactamente eso ─────────────────────
def test_energia_publicada_simplificado(tmy, poas):
    sups, r_sin = _cadena(tmy, poas, [_inv("INV-1", None)])
    _, r = _cadena(tmy, poas, [_inv("INV-1", 12_000.0)])
    etas = {n: PMAX / (MODULOS_BIPV[SPR]["area_m2"] * 1000.0) for n in ("Este", "Oeste")}
    e_sin = e_ac_total_multisup(poas, sups, etas, pr_por_superficie(r_sin))
    e_con = e_ac_total_multisup(poas, sups, etas, pr_por_superficie(r))
    recorte = sum(r[n]["recorte_kWh"] for n in ("Este", "Oeste"))
    assert e_sin["e_ac_total_kWh"] - e_con["e_ac_total_kWh"] == pytest.approx(recorte, abs=1.0)


# ── Criterio 8: la firma de la cadena ve el cambio de potencia AC ─────────────
def test_firma_cambia_con_la_potencia_ac_y_sin_inversores_no():
    p = parametros_cadena({})
    sups = _proyecto()
    a = firma_cadena(p, sups, [_inv("INV-1", 12_000.0)])
    b = firma_cadena(p, sups, [_inv("INV-1", 20_000.0)])
    assert a != b
    assert firma_cadena(p, sups) == firma_cadena(p, sups, [_inv("INV-1", None)])


# ── Criterio 9: la página lo muestra ──────────────────────────────────────────
def test_pagina_muestra_recorte_por_inversor():
    src = VISTA_3D.read_text(encoding="utf-8")
    assert "recorte_por_inversor(" in src and "tabla_recorte(" in src
    assert "Recorte por inversor" in src
