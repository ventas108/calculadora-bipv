"""Topología eléctrica multi-superficie para ⚡ Diagrama Unifilar y 📋 Ficha RETIE.

Spec 07-informes/unifilar-retie-multisuperficie. Caso real del cliente
(28-sep-2026): INV-1 Sungrow SG5.0RT (2 MPPT, 1 entrada por MPPT, 18 A,
Vdc 1100 V, MPPT 160–1000 V), fachada ASP-ST1-T40 8 serie × 14 strings en el
MPPT 1 (caja combinadora) y techo SPR-E20-327 4 serie × 1 string en el MPPT 2.
Antes la Ficha RETIE validaba el panel y el inversor de 📐 Dimensionamiento y
el unifilar pedía a mano los módulos de cada superficie.
"""
import copy

import pytest

from calculos.diseno_electrico_multisup import validar_diseno_electrico
from calculos.topologia_electrica import (
    CLAVE_BATERIA_INVERSOR,
    CLAVE_OPTIMIZADORES,
    construir_topologia,
    topologia_desde_estado,
)
from datos.tecnologias_bipv import MODULOS_BIPV

ASP = "ASP-ST1-T40"
SPR = "SPR-E20-327 (E20-327NE-WHT-D)"
TEMPS = {"T_frio": 5.0, "T_real": 36.35, "T_extremo": 41.94, "origen": "proyecto"}
FICHA_SG5 = {"Vdc_max": 1100.0, "Vmppt_min": 160.0, "Vmppt_max": 1000.0, "N_mppt": 2,
             "n_strings_tracker": 1, "Isc_max_tracker": 18.0, "P_ac_nom_W": 5000.0}


def _inv(inv_id="INV-1", nombre="SG5.0RT", ficha=FICHA_SG5):
    return {"inversor_id": inv_id, "clase": "string", "origen_ficha": "proyecto", "nombre": nombre,
            "ficha": dict(ficha), "eta_inversor": 0.97, "P_ac_nom_W": ficha["P_ac_nom_W"]}


def _g(gid, inv, mppt, ns, np_):
    return {"gid": gid, "topologia": "string", "inversor_id": inv, "mppt": mppt,
            "n_serie": ns, "n_paralelo": np_}


def _cliente():
    sups = [
        {"uid": 1, "nombre": "Fachada principal", "tipo": "Fachada", "tilt_deg": 90, "azimuth_deg": 180,
         "area_m2": 97.3, "activa": True, "grupos": [_g("G1", "INV-1", 1, 8, 14)]},
        {"uid": 2, "nombre": "Techo 1", "tipo": "Techo", "tilt_deg": 10, "azimuth_deg": 180,
         "area_m2": 97.3, "activa": True, "grupos": [_g("G2", "INV-1", 2, 4, 1)]},
    ]
    paneles = {"Fachada principal": {"panel": dict(MODULOS_BIPV[ASP]), "nombre": ASP},
               "Techo 1": {"panel": dict(MODULOS_BIPV[SPR]), "nombre": SPR}}
    return sups, [_inv()], paneles


def _topo(sups=None, invs=None, paneles=None, **kw):
    s0, i0, p0 = _cliente()
    sups, invs, paneles = sups or s0, invs or i0, paneles or p0
    diag = validar_diseno_electrico(sups, invs, paneles, TEMPS)
    return construir_topologia(sups, invs, paneles, diag, **kw), diag


def test_cliente_una_rama_por_mppt_y_caja_combinadora_en_la_fachada():
    topo, diag = _topo()
    assert [i["inversor_id"] for i in topo["inversores"]] == ["INV-1"]
    ramas = topo["inversores"][0]["ramas"]
    assert [r["mppt"] for r in ramas] == [1, 2]
    fachada, techo = ramas
    assert fachada["caja_combinadora"] is True and techo["caja_combinadora"] is False
    assert fachada["strings"] == 14 and techo["strings"] == 1
    assert fachada["grupos"][0]["modulos"] == 112 and techo["grupos"][0]["modulos"] == 4
    assert fachada["grupos"][0]["panel"] == ASP and techo["grupos"][0]["panel"] == SPR
    # misma corriente de diseño que ⚡ Diseño eléctrico (14 × 0,80 × 1,25 = 14,0 A)
    assert fachada["isc_diseno_A"] == pytest.approx(14.0)
    assert fachada["isc_diseno_A"] == pytest.approx(diag["mppt"][0]["isc_total"])
    assert topo["n_modulos"] == 116
    assert topo["p_dc_kWp"] == pytest.approx((112 * 63.0 + 4 * 327.106) / 1000, rel=1e-6)
    assert topo["p_ac_kW"] == pytest.approx(5.0)
    assert [s["nombre"] for s in topo["superficies"]] == ["Fachada principal", "Techo 1"]
    assert topo["superficies"][0]["modulos"] == 112
    assert topo["sin_asignar"] == [] and topo["optimizadores"] is False and topo["bateria"] is None


def test_grupo_sin_inversor_valido_va_a_sin_asignar():
    sups, invs, paneles = _cliente()
    sups[1]["grupos"] = [_g("G2", "INV-9", 2, 4, 1)]
    topo, _ = _topo(sups, invs, paneles)
    assert [r["mppt"] for r in topo["inversores"][0]["ramas"]] == [1]
    assert topo["sin_asignar"] == ["Techo 1 · G2"]
    assert topo["n_modulos"] == 112


def test_varios_inversores_cada_uno_con_sus_ramas_y_potencia():
    sups, invs, paneles = _cliente()
    sups[1]["grupos"] = [_g("G2", "INV-2", 1, 4, 1)]
    ficha2 = dict(FICHA_SG5, P_ac_nom_W=3000.0)
    topo, _ = _topo(sups, [_inv(), _inv("INV-2", "SG3.0RT", ficha2)], paneles)
    assert [(i["inversor_id"], len(i["ramas"])) for i in topo["inversores"]] == [("INV-1", 1), ("INV-2", 1)]
    assert [i["p_ac_kW"] for i in topo["inversores"]] == [5.0, 3.0]
    assert topo["p_ac_kW"] == pytest.approx(8.0)
    assert topo["inversores"][1]["p_dc_kWp"] == pytest.approx(4 * 327.106 / 1000, rel=1e-6)


def test_inversor_sin_grupos_no_aparece_en_el_diagrama():
    sups, invs, paneles = _cliente()
    topo, _ = _topo(sups, [_inv(), _inv("INV-2", "SG3.0RT")], paneles)
    assert [i["inversor_id"] for i in topo["inversores"]] == ["INV-1"]


def test_bateria_en_el_inversor_elegido_o_en_el_primero():
    sups, invs, paneles = _cliente()
    sups[1]["grupos"] = [_g("G2", "INV-2", 1, 4, 1)]
    dos = [_inv(), _inv("INV-2", "SPH 5000TL3 BH-UP")]
    bat = {"nombre": "ARK 5kWh", "cantidad": 2, "capacidad_kWh_unidad": 5.1, "inversor_id": "INV-2"}
    topo, _ = _topo(sups, dos, paneles, bateria=bat)
    assert topo["bateria"]["inversor_id"] == "INV-2" and topo["bateria"]["inversor_reasignado"] is False
    assert topo["bateria"]["capacidad_total_kWh"] == pytest.approx(10.2)
    assert [i["bateria"] for i in topo["inversores"]] == [False, True]
    topo2, _ = _topo(sups, dos, paneles, bateria=dict(bat, inversor_id="INV-7"))
    assert topo2["bateria"]["inversor_id"] == "INV-1" and topo2["bateria"]["inversor_reasignado"] is True


def test_optimizadores_se_marcan_en_toda_la_topologia():
    topo, _ = _topo(optimizadores=True)
    assert topo["optimizadores"] is True


def test_no_muta_las_entradas():
    sups, invs, paneles = _cliente()
    antes = copy.deepcopy((sups, invs))
    _topo(sups, invs, paneles, optimizadores=True)
    assert (sups, invs) == antes


def _estado_cliente(**extra):
    sups, invs, _ = _cliente()
    estado = {"multisup_activo": True, "superficies_bipv": sups, "multisup_inversores": invs,
              "panel_dict": dict(MODULOS_BIPV[ASP]), "panel_nombre_dim": ASP,
              "T_min_diseno": 5.0, "T_cel_realista": 36.35, "T_cel_extremo": 41.94}
    sups[1].update({"panel_origen": "catalogo", "panel_nombre": SPR, "panel_ficha": dict(MODULOS_BIPV[SPR])})
    estado.update(extra)
    return estado


def test_topologia_desde_estado_lee_opciones_y_bateria():
    assert topologia_desde_estado({}) is None
    assert topologia_desde_estado(_estado_cliente(multisup_activo=False)) is None
    sin_grupos = _estado_cliente()
    for s in sin_grupos["superficies_bipv"]:
        s["grupos"] = []
    assert topologia_desde_estado(sin_grupos) is None

    topo = topologia_desde_estado(_estado_cliente())
    assert topo["n_modulos"] == 116 and topo["optimizadores"] is False and topo["bateria"] is None
    assert topo["diagnostico"]["mppt"][0]["caja_combinadora"] is True

    estado = _estado_cliente(**{CLAVE_OPTIMIZADORES: True, CLAVE_BATERIA_INVERSOR: "INV-1",
                                "bateria_ok": True, "bateria_nombre": "ARK 5kWh",
                                "bateria_dict": {"capacidad_kWh": 5.1},
                                "bateria_dim": {"N_baterias": 2, "cap_unitaria_kWh": 5.1}})
    topo = topologia_desde_estado(estado)
    assert topo["optimizadores"] is True
    assert topo["bateria"]["nombre"] == "ARK 5kWh" and topo["bateria"]["cantidad"] == 2
