# -*- coding: utf-8 -*-
"""Spec ``05-perdidas-y-temperatura/string-cruza-superficies`` (29-sep-2026).

En 🗺️ Vista 3D un string que cruza una esquina (parte en la fachada Este y
parte en la Oeste) no se podía declarar: se modelaba como dos strings y no se
restaba su pérdida en serie (≈ 14.9 % en Apartadó con 50/50). Cada prueba
termina en lo que publica la energía multi-superficie.
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
from calculos.cruce_superficies import (
    cruces_del_proyecto,
    factores_cruce,
    modulos_fisicos_por_superficie,
    perdida_cruce,
    validar_cruces,
)
from calculos.diseno_electrico_multisup import (
    firma_diseno_electrico,
    superficies_para_energia,
)
from calculos.mismatch import perdida_string_bypass
from calculos.multi_superficie import calcular_poa_superficie, e_ac_total_multisup
from datos.tecnologias_bipv import MODULOS_BIPV
from tests.test_simulation_pipeline import _tmy_sintetico_offline

VISTA_3D = Path(__file__).resolve().parents[1] / "pages" / "9_🗺️_Vista_3D.py"
LAT, LON, ALT = 7.883, -76.6259, 44
SPR = "SPR-E20-327 (E20-327NE-WHT-D)"
ASP = "ASP-ST1-T40"


def _sup(nombre, uid, az, grupos, tilt=90, area=100.0, activa=True):
    return {"nombre": nombre, "uid": uid, "tipo": "Fachada", "tilt_deg": tilt, "azimuth_deg": az,
            "area_m2": area, "activa": activa, "grupos": grupos}


def _grupo(gid, ns, npar, cruce=None):
    g = {"gid": gid, "topologia": "string", "inversor_id": "INV-1", "mppt": 1,
         "n_serie": ns, "n_paralelo": npar}
    if cruce:
        g["cruce"] = cruce
    return g


def _proyecto(k=5, cruce=True):
    este = _sup("Este", "u1", 90, [_grupo("G1", 10, 2, {"uid": "u2", "modulos": k} if cruce else None),
                                   _grupo("G2", 10, 1)])
    oeste = _sup("Oeste", "u2", 270, [_grupo("G1", 10, 1)])
    return [este, oeste]


def _paneles(panel_oeste=SPR):
    return {"Este": {"panel": dict(MODULOS_BIPV[SPR]), "nombre": SPR},
            "Oeste": {"panel": dict(MODULOS_BIPV[panel_oeste]), "nombre": panel_oeste}}


@pytest.fixture(scope="module")
def tmy():
    return _tmy_sintetico_offline(LAT, LON, ALT)


@pytest.fixture(scope="module")
def poas(tmy):
    return {n: calcular_poa_superficie(tmy, LAT, LON, ALT, {"tilt_deg": 90, "azimuth_deg": az})
            for n, az in (("Este", 90), ("Oeste", 270))}


# ── Criterio 1: los módulos se cuentan donde están ───────────────────────────
def test_modulos_fisicos():
    sups = _proyecto(k=4)
    m = modulos_fisicos_por_superficie(sups)
    assert m == {"Este": (10 - 4) * 2 + 10, "Oeste": 10 + 4 * 2}
    assert sum(m.values()) == 10 * 2 + 10 + 10          # el total no cambia
    c = cruces_del_proyecto(sups)
    assert c == [{"origen": "Este", "gid": "G1", "destino": "Oeste", "uid_destino": "u2",
                  "n_serie": 10, "n_paralelo": 2, "k": 4}]


def test_superficies_para_energia_usa_modulos_fisicos():
    s = superficies_para_energia(_proyecto(k=4), _paneles())
    area = MODULOS_BIPV[SPR].get("area_m2")
    por = {x["nombre"]: x for x in s}
    assert por["Este"]["modulos"] == 22 and por["Oeste"]["modulos"] == 18
    if area:
        assert por["Oeste"]["area_m2"] == pytest.approx(18 * area, abs=1e-3)


# ── Criterio 2: pérdida del string (modelo de la Spec B) ─────────────────────
def test_perdida_cruce_este_oeste(poas):
    r = perdida_cruce(poas["Este"], poas["Oeste"], 10, 5)
    ideal, string = perdida_string_bypass(
        [poas["Este"]["poa_global"].to_numpy(), poas["Oeste"]["poa_global"].to_numpy()], [0.5, 0.5])
    assert r["perdida_pct"] == pytest.approx((1 - string.sum() / ideal.sum()) * 100, abs=1e-6)
    assert 13.0 < r["perdida_pct"] < 17.0
    assert len(r["factor_horario"]) == 8760


# ── Criterio 3: PR de cada superficie ────────────────────────────────────────
def test_factores_por_superficie(poas):
    sups = superficies_para_energia(_proyecto(k=5), _paneles())
    f = factores_cruce(sups, poas)
    L = perdida_cruce(poas["Este"], poas["Oeste"], 10, 5)["perdida_pct"] / 100
    # Este: 10 módulos del string cruzado (5 × 2) de 20 en total
    assert f["Este"]["f_cruce"] == pytest.approx(1 - L * 10 / 20, abs=1e-9)
    # Oeste: 10 módulos del string cruzado (5 × 2) de 20 en total
    assert f["Oeste"]["f_cruce"] == pytest.approx(1 - L * 10 / 20, abs=1e-9)
    assert f["Este"]["detalle"][0]["perdida_pct"] == pytest.approx(L * 100)


def _sin_cruce_mismos_modulos(sups):
    """Las mismas superficies (mismos módulos físicos y área) sin el cruce."""
    return [dict(s, grupos=[{k: v for k, v in g.items() if k != "cruce"} for g in s["grupos"]])
            for s in sups]


def _estado(tmy, poas):
    return {"tmy_df": tmy.set_axis(poas["Este"].index), "multisup_inversores": []}


def test_cadena_aplica_el_cruce_y_sin_cruce_igual(tmy, poas):
    est = _estado(tmy, poas)
    con = superficies_para_energia(_proyecto(k=5), _paneles())
    sin = _sin_cruce_mismos_modulos(con)
    r_con, e1 = cadena_superficies_estado(est, con, poas, _paneles())
    r_sin, e2 = cadena_superficies_estado(est, sin, poas, _paneles())
    assert not e1 and not e2
    assert "f_cruce" not in r_sin["Este"]
    f = factores_cruce(con, poas)
    for n in ("Este", "Oeste"):
        assert r_con[n]["f_cruce"] == pytest.approx(f[n]["f_cruce"])
        assert r_con[n]["pr"] == pytest.approx(r_sin[n]["pr"] * f[n]["f_cruce"], rel=1e-9)
    filas = {f_["Superficie"]: f_ for f_ in tabla_desglose(r_con)}
    assert "String que cruza" in filas["Este"]


# ── Criterio 4: la energía publicada baja exactamente eso ───────────────────
def test_punta_a_punta_energia_publicada(tmy, poas):
    est = _estado(tmy, poas)
    con = superficies_para_energia(_proyecto(k=5), _paneles())
    sin = _sin_cruce_mismos_modulos(con)
    etas = {"Este": 0.20, "Oeste": 0.20}
    r_con, _ = cadena_superficies_estado(est, con, poas, _paneles())
    r_sin, _ = cadena_superficies_estado(est, sin, poas, _paneles())
    e_con = e_ac_total_multisup(poas, con, etas, pr_por_superficie(r_con))
    e_sin = e_ac_total_multisup(poas, sin, etas, pr_por_superficie(r_sin))
    por_con = {d["nombre"]: d["e_ac_kWh"] for d in e_con["desglose"]}
    por_sin = {d["nombre"]: d["e_ac_kWh"] for d in e_sin["desglose"]}
    f = factores_cruce(con, poas)
    # Mismos módulos y área: la energía de cada superficie baja exactamente f_cruce
    for n in ("Este", "Oeste"):
        assert por_con[n] == pytest.approx(por_sin[n] * f[n]["f_cruce"], abs=0.2)
    assert e_con["e_ac_total_kWh"] < e_sin["e_ac_total_kWh"]
    # y el área sigue a los módulos: Oeste pasa de 10 a 20 módulos
    antes = {x["nombre"]: x for x in superficies_para_energia(_proyecto(cruce=False), _paneles())}
    assert {x["nombre"]: x["modulos"] for x in con} == {"Este": 20, "Oeste": 20}
    assert antes["Oeste"]["modulos"] == 10


# ── Criterio 5: validación ───────────────────────────────────────────────────
@pytest.mark.parametrize("cruce, texto", [
    ({"uid": "u9", "modulos": 5}, "no existe"),
    ({"uid": "u1", "modulos": 5}, "misma superficie"),
    ({"uid": "u2", "modulos": 0}, "entre 1 y 9"),
    ({"uid": "u2", "modulos": 10}, "entre 1 y 9"),
])
def test_validacion_bloquea(cruce, texto):
    sups = _proyecto()
    sups[0]["grupos"][0]["cruce"] = cruce
    bloqueos, _ = validar_cruces(sups, _paneles())
    assert any(texto in b for b in bloqueos), bloqueos


def test_validacion_superficie_inactiva_y_panel_distinto():
    sups = _proyecto()
    sups[1]["activa"] = False
    assert any("no está activa" in b for b in validar_cruces(sups, _paneles())[0])
    bloqueos, _ = validar_cruces(_proyecto(), _paneles(panel_oeste=ASP))
    assert any("mismo panel" in b for b in bloqueos)


def test_validacion_ok_y_aviso():
    bloqueos, avisos = validar_cruces(_proyecto(), _paneles())
    assert not bloqueos and any("cruza" in a for a in avisos)


def test_diseno_electrico_incluye_los_cruces():
    from calculos.diseno_electrico_multisup import validar_diseno_electrico
    sups = _proyecto()
    sups[0]["grupos"][0]["cruce"] = {"uid": "u9", "modulos": 5}
    d = validar_diseno_electrico(sups, [], _paneles(), {"T_frio": 20, "T_real": 55, "T_extremo": 64,
                                                        "origen": "proyecto"})
    assert any("no existe" in b for b in d["bloqueos"])


# ── Criterio 6: modo físico y sección 6 ──────────────────────────────────────
def test_modo_fisico_no_se_prepara_con_cruces():
    from calculos.adaptador_multisuperficie import construir_proyecto_desde_session_state
    estado = {"superficies_bipv": _proyecto(), "multisup_inversores": [
        {"inversor_id": "INV-1", "tipo": "string", "eta_inversor": 0.97, "P_ac_nom_W": 10000}]}
    with pytest.raises(ValueError, match="cruza"):
        construir_proyecto_desde_session_state(estado)


def test_seccion_6_excluye_cruces():
    src = VISTA_3D.read_text(encoding="utf-8")
    assert "tiene_cruce(s)" in src


# ── Criterio 7: firmas sin cruces no cambian ─────────────────────────────────
def test_firmas_sin_cruce_iguales():
    sin = _proyecto(cruce=False)
    p = parametros_cadena({})
    assert firma_cadena(p, sin) == firma_cadena(p, [dict(s) for s in sin])
    assert firma_cadena(p, _proyecto()) != firma_cadena(p, sin)
    assert firma_diseno_electrico(_proyecto(), []) != firma_diseno_electrico(sin, [])


# ── Criterio 8: editor ───────────────────────────────────────────────────────
def test_editor_de_grupos_declara_el_cruce():
    src = VISTA_3D.read_text(encoding="utf-8")
    assert "🔀 Este string cruza a otra superficie" in src
    assert '"cruce": _cruce_ui' in src


def test_el_cruce_se_guarda_con_el_proyecto():
    from calculos.persistencia_multisuperficie import _superficie_input
    guardada = _superficie_input(_proyecto(k=4)[0])
    assert guardada["grupos"][0]["cruce"] == {"uid": "u2", "modulos": 4}


# ── Criterio 9: manual ───────────────────────────────────────────────────────
@pytest.mark.parametrize("pregunta, texto", [
    ("como declaro en vista 3d un string que cruza la esquina entre dos fachadas", "Este string cruza a otra superficie"),
    ("que pasa con la energia si un string cruza dos superficies en vista 3d", "14,9 %"),
])
def test_manual(pregunta, texto):
    from calculos.asistente import BaseConocimiento
    secciones = BaseConocimiento.cargar().buscar(pregunta, k=6)
    candidatas = [s for s in secciones if "string que cruza dos superficies" in s["titulo"].lower()]
    assert candidatas, [s["titulo"] for s in secciones]
    assert texto in "\n".join(s["texto"] for s in candidatas)
