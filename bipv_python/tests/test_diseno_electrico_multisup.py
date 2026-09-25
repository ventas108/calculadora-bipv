"""Spec 03-dimensionamiento/diseno-electrico-multisuperficie — fase A1.

Modelo (inversor con ficha, grupos de strings con migración) y validación
eléctrica pura. La fase A1 no cambia ninguna energía.
"""
import ast
import copy
from pathlib import Path

import pytest

from calculos.diseno_electrico_multisup import (
    CLASES_SOPORTADAS,
    ORIGENES_FICHA,
    TOPOLOGIAS_SOPORTADAS,
    campos_legacy_desde_grupos,
    grupos_de_superficie,
    inversor_normalizado,
    normalizar_ficha_inversor,
    rango_n_serie,
    temperaturas_diseno,
    validar_diseno_electrico,
)
from datos.catalogo_inversores import INVERSORES
from datos.tecnologias_bipv import MODULOS_BIPV

_PAGINA = Path(__file__).resolve().parents[1] / "pages" / "9_🗺️_Vista_3D.py"
_ASP = MODULOS_BIPV["ASP-ST1-T40"]
_SPR = MODULOS_BIPV["SPR-E20-327 (E20-327NE-WHT-D)"]
# Ficha del ejemplo de la Spec (problema.md).
_FICHA = {"Vdc_max": 1000.0, "Vmppt_min": 200.0, "Vmppt_activo_min": 200.0,
          "Vmppt_max": 800.0, "I_max_tracker": 16.0, "Isc_max_tracker": 20.0,
          "N_mppt": 2, "n_strings_tracker": 4, "P_ac_nom_W": 10000.0}
_TEMPS = {"T_frio": 5.0, "T_real": 60.0, "T_extremo": 60.0, "origen": "proyecto"}


def _inv(inv_id="INV-1", **cambios):
    base = {"inversor_id": inv_id, "clase": "string", "origen_ficha": "catalogo",
            "nombre": "Ejemplo", "ficha": dict(_FICHA), "eta_inversor": 0.97,
            "P_ac_nom_W": 10000.0}
    base.update(cambios)
    return base


def _grupo(gid="G1", inversor_id="INV-1", mppt=1, n_serie=8, n_paralelo=2, **cambios):
    base = {"gid": gid, "topologia": "string", "inversor_id": inversor_id,
            "mppt": mppt, "n_serie": n_serie, "n_paralelo": n_paralelo}
    base.update(cambios)
    return base


def _sup(nombre="Fachada", uid=1, grupos=None, area=97.3, azimuth=180.0, tilt=90.0):
    return {"uid": uid, "nombre": nombre, "tipo": "Fachada", "tilt_deg": tilt,
            "azimuth_deg": azimuth, "area_m2": area, "activa": True,
            "grupos": grupos if grupos is not None else [_grupo()]}


def _paneles(**por_nombre):
    return {n: {"panel": dict(p), "nombre": p.get("nombre", n)} for n, p in por_nombre.items()}


def _diag(sups, invs, paneles, temps=_TEMPS):
    return validar_diseno_electrico(sups, invs, paneles, temps)


def _checks(item):
    return {c["nombre"]: c for c in item["checks"]}


# ── Modelo y migración ───────────────────────────────────────────────────────
def test_superficie_antigua_se_lee_como_un_grupo_g1():
    antigua = {"uid": 1, "nombre": "Sur", "inversor_id": "INV-1", "n_serie": 8, "n_paralelo": 3}
    antes = copy.deepcopy(antigua)
    assert grupos_de_superficie(antigua) == [
        {"gid": "G1", "topologia": "string", "inversor_id": "INV-1", "mppt": 1,
         "n_serie": 8, "n_paralelo": 3}]
    assert antigua == antes  # no muta


def test_superficie_sin_diseno_electrico_no_tiene_grupos():
    assert grupos_de_superficie({"uid": 1, "nombre": "Sur"}) == []


def test_grupos_explicitos_prevalecen_sobre_campos_antiguos():
    sup = {"uid": 1, "nombre": "Sur", "inversor_id": "X", "n_serie": 1, "n_paralelo": 1,
           "grupos": [_grupo(n_serie=10)]}
    assert grupos_de_superficie(sup)[0]["n_serie"] == 10


def test_campos_antiguos_espejo_del_grupo_unico():
    assert campos_legacy_desde_grupos([_grupo(n_serie=9, n_paralelo=4)]) == {
        "inversor_id": "INV-1", "n_serie": 9, "n_paralelo": 4}
    assert campos_legacy_desde_grupos([]) == {"inversor_id": None, "n_serie": None, "n_paralelo": None}


def test_inversor_antiguo_se_lee_como_manual():
    inv = inversor_normalizado({"inversor_id": "INV-1", "eta_inversor": 0.97,
                                "P_ac_nom_W": 5000.0, "ficha": {}})
    assert inv["origen_ficha"] == "manual" and inv["clase"] == "string"
    assert set(ORIGENES_FICHA) == {"proyecto", "catalogo", "manual"}
    assert TOPOLOGIAS_SOPORTADAS == ("string",) and CLASES_SOPORTADAS == ("string",)


def test_normalizar_ficha_de_ambos_catalogos():
    interno = normalizar_ficha_inversor(INVERSORES["Growatt-MID15KTL3-X"])
    assert interno["Vdc_max"] == 1100 and interno["N_mppt"] == 2
    assert interno["Vmppt_activo_min"] == 580 and interno["P_ac_nom_W"] == 15000
    assert interno["eficiencia_max"] == INVERSORES["Growatt-MID15KTL3-X"]["eficiencia_max"]
    excel = normalizar_ficha_inversor({"Vdc_max": 1000, "Vmppt_min": 200, "Vmppt_max": 800,
                                       "n_trackers": 3, "n_strings_tracker": 2,
                                       "I_max_tracker": 13, "P_ac_nom_W": 8000})
    assert excel["N_mppt"] == 3 and excel["n_strings_tracker"] == 2
    assert excel["Vmppt_activo_min"] == 200  # sin dato activo: el mínimo MPPT


# ── Temperaturas y rango de N serie ──────────────────────────────────────────
def test_temperaturas_del_proyecto_o_por_defecto_con_aviso():
    t = temperaturas_diseno({"T_min_diseno": 5.0, "T_cel_realista": 55.0, "T_cel_extremo": 65.0})
    assert (t["T_frio"], t["T_real"], t["T_extremo"], t["origen"]) == (5.0, 55.0, 65.0, "proyecto")
    d = temperaturas_diseno({})
    assert d["origen"] == "por_defecto" and d["T_frio"] == -5.0


def test_rango_n_serie_del_ejemplo_de_la_spec():
    assert rango_n_serie(_ASP, _FICHA, _TEMPS) == (3, 8)
    assert rango_n_serie(_SPR, _FICHA, _TEMPS) == (5, 14)


def test_rango_n_serie_sin_ficha_completa_es_none():
    assert rango_n_serie(_SPR, {"Vdc_max": 1000.0}, _TEMPS) is None


# ── Validación por grupo ─────────────────────────────────────────────────────
def test_grupo_valido_en_verde_con_formula_y_fuente():
    d = _diag([_sup(grupos=[_grupo(n_serie=12, n_paralelo=2)])], [_inv()], _paneles(Fachada=_SPR))
    g = d["grupos"][0]
    assert g["estado"] == "verde" and g["rango_n_serie"] == (5, 14)
    voc = _checks(g)["Voc en frío ≤ Vdc máximo"]
    assert voc["valor"] == pytest.approx(12 * 68.4, abs=1) and voc["limite"] == 1000.0
    assert "T mín" in voc["formula"] and voc["fuente"]


def test_criterio_a1_voc_en_frio_supera_vdc():
    d = _diag([_sup(grupos=[_grupo(n_serie=20, n_paralelo=1)])], [_inv()], _paneles(Fachada=_SPR))
    g = d["grupos"][0]
    assert g["estado"] == "rojo" and d["estado_global"] == "rojo"
    assert any("1369" in b or "1.369" in b for b in d["bloqueos"])


def test_vmp_bajo_la_ventana_mppt_es_rojo():
    d = _diag([_sup(grupos=[_grupo(n_serie=2, n_paralelo=1)])], [_inv()], _paneles(Fachada=_ASP))
    assert d["grupos"][0]["estado"] == "rojo"


def test_inversor_manual_sin_ficha_queda_no_validado():
    inv = _inv(origen_ficha="manual", ficha={}, nombre="")
    d = _diag([_sup(grupos=[_grupo(n_serie=6, n_paralelo=1)])], [inv], _paneles(Fachada=_ASP))
    g = d["grupos"][0]
    assert g["estado"] == "amarillo" and any("no validado" in a for a in d["avisos"])


@pytest.mark.parametrize("grupo, fragmento", [
    (_grupo(inversor_id="NO-EXISTE"), "no existe"),
    (_grupo(inversor_id=None), "sin inversor"),
    (_grupo(n_serie=0), "N serie"),
    (_grupo(mppt=0), "MPPT"),
    (_grupo(topologia="microinversor"), "no soportada"),
])
def test_grupo_incompleto_o_no_soportado_es_rojo(grupo, fragmento):
    d = _diag([_sup(grupos=[grupo])], [_inv()], _paneles(Fachada=_ASP))
    assert d["grupos"][0]["estado"] == "rojo"
    assert any(fragmento in b for b in d["bloqueos"])


def test_superficie_activa_sin_grupos_es_rojo():
    d = _diag([_sup(grupos=[])], [_inv()], _paneles(Fachada=_ASP))
    assert d["estado_global"] == "rojo" and any("sin diseño eléctrico" in b for b in d["bloqueos"])


def test_superficie_sin_panel_utilizable_es_rojo():
    d = _diag([_sup()], [_inv()], {})
    assert d["grupos"][0]["estado"] == "rojo"


# ── Validación por MPPT ──────────────────────────────────────────────────────
def test_corriente_del_mppt_suma_los_strings():
    # SPR: 6,46 A × 1,25 = 8,08 A por string; 3 strings = 24,2 A > 20 A.
    d = _diag([_sup(grupos=[_grupo(n_serie=12, n_paralelo=3)])], [_inv(ficha={**_FICHA, "n_strings_tracker": 8})],
              _paneles(Fachada=_SPR))
    m = d["mppt"][0]
    assert m["estado"] == "rojo" and m["isc_total"] == pytest.approx(3 * 6.46 * 1.25, abs=0.01)


def test_strings_por_entrada_del_mppt():
    # Fase A2: más strings que entradas pero la corriente cabe (5 × 0,8 × 1,25
    # = 5 A de 20 A) → 🟡 caja combinadora, no 🔴.
    d = _diag([_sup(grupos=[_grupo(n_serie=6, n_paralelo=5)])], [_inv()], _paneles(Fachada=_ASP))
    assert _checks(d["mppt"][0])["Strings ≤ entradas del MPPT"]["estado"] == "amarillo"
    assert d["mppt"][0]["caja_combinadora"]


def test_dos_paneles_en_el_mismo_mppt_es_rojo():
    sups = [_sup("Fachada", 1, [_grupo(n_serie=6, n_paralelo=1)]),
            _sup("Techo", 2, [_grupo(n_serie=12, n_paralelo=1)], tilt=10.0)]
    d = _diag(sups, [_inv()], _paneles(Fachada=_ASP, Techo=_SPR))
    assert d["mppt"][0]["estado"] == "rojo"
    assert any("paneles distintos" in b for b in d["bloqueos"])


def test_orientaciones_distintas_en_un_mppt_es_amarillo():
    sups = [_sup("Este", 1, [_grupo(n_serie=6, n_paralelo=1)], azimuth=90.0),
            _sup("Oeste", 2, [_grupo(n_serie=6, n_paralelo=1)], azimuth=270.0)]
    d = _diag(sups, [_inv()], _paneles(Este=_ASP, Oeste=_ASP))
    m = d["mppt"][0]
    assert m["estado"] == "amarillo" and "sección 6" in " ".join(d["avisos"])


# ── Validación por inversor ──────────────────────────────────────────────────
def test_mppt_inexistente_en_el_inversor_es_rojo():
    d = _diag([_sup(grupos=[_grupo(mppt=3, n_serie=6, n_paralelo=1)])], [_inv()], _paneles(Fachada=_ASP))
    assert d["inversores"][0]["estado"] == "rojo"


def test_relacion_dc_ac_suma_todo_el_inversor():
    sups = [_sup("A", 1, [_grupo(mppt=1, n_serie=12, n_paralelo=2)], tilt=10.0),
            _sup("B", 2, [_grupo(mppt=2, n_serie=12, n_paralelo=2)], tilt=10.0)]
    d = _diag(sups, [_inv(P_ac_nom_W=10000.0)], _paneles(A=_SPR, B=_SPR))
    inv = d["inversores"][0]
    assert inv["P_dc_stc_kW"] == pytest.approx(48 * 327.106 / 1000, abs=0.01)
    assert inv["relacion_dc_ac"]["ratio"] == pytest.approx(inv["P_dc_stc_kW"] * 1000 / 10000, abs=0.01)
    assert inv["mppt_usados"] == 2 and inv["mppt_disponibles"] == 2


def test_eficiencia_del_inversor_obligatoria():
    d = _diag([_sup(grupos=[_grupo(n_serie=6, n_paralelo=1)])], [_inv(eta_inversor=None)], _paneles(Fachada=_ASP))
    assert d["inversores"][0]["estado"] == "rojo"


# ── Validación por superficie ────────────────────────────────────────────────
def test_modulos_que_no_caben_en_el_area_es_rojo():
    # 8 × 20 = 160 módulos × 0,72 m² = 115,2 m² > 97,3 m².
    d = _diag([_sup(grupos=[_grupo(n_serie=8, n_paralelo=20)])], [_inv(ficha={**_FICHA, "n_strings_tracker": 30, "Isc_max_tracker": 50})],
              _paneles(Fachada=_ASP))
    s = d["superficies"][0]
    assert s["estado"] == "rojo" and s["cobertura_pct"] == pytest.approx(115.2 / 97.3 * 100, abs=0.1)


def test_poca_cobertura_es_amarillo_y_da_area_instalada():
    d = _diag([_sup(grupos=[_grupo(n_serie=6, n_paralelo=2)])], [_inv()], _paneles(Fachada=_ASP))
    s = d["superficies"][0]
    assert s["estado"] == "amarillo" and s["area_instalada_m2"] == pytest.approx(12 * 0.72)


def test_temperaturas_por_defecto_generan_aviso():
    d = _diag([_sup(grupos=[_grupo(n_serie=6, n_paralelo=1)])], [_inv()], _paneles(Fachada=_ASP),
              temps={"T_frio": -5.0, "T_real": 36.35, "T_extremo": 41.94, "origen": "por_defecto"})
    assert any("temperaturas" in a.lower() for a in d["avisos"])


def test_inactivas_fuera_y_no_muta():
    sups = [_sup(), {**_sup("Off", 2), "activa": False}]
    invs = [_inv()]
    antes = copy.deepcopy((sups, invs))
    d = _diag(sups, invs, _paneles(Fachada=_ASP))
    assert [g["superficie"] for g in d["grupos"]] == ["Fachada"]
    assert (sups, invs) == antes


# ── Página ───────────────────────────────────────────────────────────────────
def test_pagina_muestra_la_tabla_de_diseno_electrico():
    src = _PAGINA.read_text(encoding="utf-8")
    assert "validar_diseno_electrico(" in src and "Diseño eléctrico" in src
    assert 'key=f"ms_sup_mppt_{' in src and 'key=f"ms_inv_ficha_{' in src
    arbol = ast.parse(src)
    assert any(isinstance(n, ast.Call) and ast.unparse(n.func) == "rango_n_serie" for n in ast.walk(arbol))



# ── Fase A2 ──────────────────────────────────────────────────────────────────
_SG5 = {"Vdc_max": 1100.0, "Vmppt_min": 160.0, "Vmppt_activo_min": 160.0, "Vmppt_max": 1000.0,
        "Isc_max_tracker": 18.0, "N_mppt": 2, "n_strings_tracker": 1, "P_ac_nom_W": 5000.0}


@pytest.mark.parametrize("n_par, estado, caja", [(1, "verde", False), (17, "amarillo", True), (19, "rojo", False)])
def test_criterio_a2_caja_combinadora(n_par, estado, caja):
    # SG5.0RT (1 entrada, 18 A) con strings ASP-ST1-T40 de 0,8 A × 1,25 = 1,0 A.
    sup = _sup(grupos=[_grupo(n_serie=8, n_paralelo=n_par)], area=500.0)
    d = _diag([sup], [_inv(ficha=dict(_SG5), P_ac_nom_W=5000.0)], _paneles(Fachada=_ASP))
    m = d["mppt"][0]
    assert _checks(m)["Strings ≤ entradas del MPPT"]["estado"] == estado
    assert m["caja_combinadora"] is caja
    assert d["inversores"][0]["cajas_combinadoras"] == (1 if caja else 0)
    if estado == "amarillo":
        assert any("caja combinadora" in a and "17.0 A de 18.0 A" in a for a in d["avisos"])
    if estado == "rojo":
        assert any("ni con caja combinadora" in b and "19.0 A > límite 18.0 A" in b for b in d["bloqueos"])


@pytest.mark.parametrize("n_serie, n_par, fragmento", [
    (8, 1, "más grande que los paneles"),      # 0,50 kW / 5 kW
])
def test_dc_ac_nunca_es_rojo_y_se_explica(n_serie, n_par, fragmento):
    d = _diag([_sup(grupos=[_grupo(n_serie=n_serie, n_paralelo=n_par)])],
              [_inv(ficha=dict(_SG5), P_ac_nom_W=5000.0)], _paneles(Fachada=_ASP))
    inv = d["inversores"][0]
    assert _checks(inv)["Relación DC/AC"]["estado"] == "amarillo"
    assert inv["estado"] != "rojo"
    assert any(fragmento in a and "1,00 y 1,35" in a for a in d["avisos"])


def test_dc_ac_alto_explica_el_recorte():
    # 16 × 2 SPR = 10,47 kW en un inversor de 5 kW → DC/AC 2,09.
    sup = _sup(grupos=[_grupo(n_serie=16, n_paralelo=2)], tilt=10.0)
    d = _diag([sup], [_inv(ficha={**_SG5, "n_strings_tracker": 2, "Isc_max_tracker": 20.0},
                           P_ac_nom_W=5000.0)], _paneles(Fachada=_SPR))
    assert _checks(d["inversores"][0])["Relación DC/AC"]["estado"] == "amarillo"
    assert any("clipping" in a for a in d["avisos"])


def test_inversor_sin_grupos_no_evalua_dc_ac():
    d = _diag([_sup(grupos=[_grupo(n_serie=8, n_paralelo=1)])],
              [_inv(ficha=dict(_SG5)), _inv("INV-2", ficha=dict(_SG5))], _paneles(Fachada=_ASP))
    inv2 = next(i for i in d["inversores"] if i["inversor_id"] == "INV-2")
    assert "Relación DC/AC" not in _checks(inv2) and inv2["estado"] == "amarillo"


def test_cada_color_de_la_tabla_tiene_su_mensaje():
    # Caso de la prueba en producción: paneles distintos en un MPPT, strings
    # de más, Vmp bajo, DC/AC bajo y un inversor sin grupos.
    sups = [_sup("Fachada principal", 1, [_grupo(n_serie=1, n_paralelo=1)]),
            _sup("Techo 1", 2, [_grupo(n_serie=2, n_paralelo=1)], tilt=10.0)]
    d = _diag(sups, [_inv(ficha=dict(_SG5)), _inv("INV-2", ficha=dict(_SG5))],
              _paneles(**{"Fachada principal": _ASP, "Techo 1": _SPR}))
    etiquetas = {
        "grupo": lambda x: f"«{x['superficie']} · {x['gid']}»",
        "mppt": lambda x: f"«{x['inversor_id']} · MPPT {x['mppt']}»",
        "inversores": lambda x: f"«{x['inversor_id']}»",
        "superficies": lambda x: f"«{x['superficie']}»",
    }
    for clave, etq in (("grupos", etiquetas["grupo"]), ("mppt", etiquetas["mppt"]),
                       ("inversores", etiquetas["inversores"]), ("superficies", etiquetas["superficies"])):
        for item in d[clave]:
            for c in item["checks"]:
                if c["estado"] == "rojo":
                    assert any(b.startswith(etq(item)) for b in d["bloqueos"]), (clave, c)
                if c["estado"] == "amarillo":
                    assert any(a.startswith(etq(item)) for a in d["avisos"]), (clave, c)


def test_resumen_del_estado():
    from calculos.diseno_electrico_multisup import resumen_estado_electrico
    d = _diag([_sup(grupos=[_grupo(n_serie=20, n_paralelo=1)])], [_inv()], _paneles(Fachada=_SPR))
    r = resumen_estado_electrico(d)
    assert r["estado"] == "rojo" and r["n_bloqueos"] >= 1 and r["texto"].startswith("🔴")


# ── Área instalada ───────────────────────────────────────────────────────────
def test_area_de_energia_con_y_sin_grupos():
    from calculos.diseno_electrico_multisup import area_energia_superficie, superficies_para_energia
    con = area_energia_superficie(_sup(grupos=[_grupo(n_serie=8, n_paralelo=16)]), _ASP)
    assert con["origen"] == "instalada" and con["area_m2"] == pytest.approx(128 * 0.72)
    sin = area_energia_superficie({"uid": 1, "nombre": "F", "area_m2": 50.0}, _ASP)
    assert sin["origen"] == "superficie" and sin["area_m2"] == 50.0
    recortada = area_energia_superficie(_sup(grupos=[_grupo(n_serie=8, n_paralelo=20)]), _ASP)
    assert recortada["origen"] == "instalada_recortada" and recortada["area_m2"] == 97.3
    sups = [_sup(grupos=[_grupo(n_serie=8, n_paralelo=2), _grupo("G2", n_serie=8, n_paralelo=1, mppt=2)])]
    copia = superficies_para_energia(sups, _paneles(Fachada=_ASP))[0]
    assert copia["area_m2"] == pytest.approx(24 * 0.72) and copia["area_superficie_m2"] == 97.3
    assert sups[0]["area_m2"] == 97.3  # no muta


# ── Invalidación por cambio eléctrico ────────────────────────────────────────
def _estado_publicado():
    from calculos.panel_superficie import KEYS_RESULTADOS_PANEL
    estado = {
        "superficies_bipv": [_sup("Fachada", 1, [_grupo(n_serie=8, n_paralelo=2)], ),
                             _sup("Techo", 2, [_grupo(n_serie=12, n_paralelo=1, mppt=2)])],
        "multisup_inversores": [_inv()],
        "E_ac_anual_kWh_multisup": 1.0, "multisup_activo": True, "multisup_origen": "simplificado",
        "poa_superficies": {1: "poa"},
    }
    estado["superficies_bipv"][0]["firma_poa"] = "poa-1"
    for clave in KEYS_RESULTADOS_PANEL:
        estado[clave] = "x"
    return estado


@pytest.mark.parametrize("cambio", ["n_serie", "mppt", "grupo_nuevo", "eta", "ficha"])
def test_cambio_electrico_retira_energia_y_conserva_poa(cambio):
    from calculos.diseno_electrico_multisup import invalidar_por_cambio_electrico
    estado = _estado_publicado()
    assert invalidar_por_cambio_electrico(estado) == []
    if cambio == "n_serie":
        estado["superficies_bipv"][0]["grupos"][0]["n_serie"] = 7
    elif cambio == "mppt":
        estado["superficies_bipv"][1]["grupos"][0]["mppt"] = 1
    elif cambio == "grupo_nuevo":
        estado["superficies_bipv"][0]["grupos"].append(_grupo("G2", n_serie=8, n_paralelo=1, mppt=2))
    elif cambio == "eta":
        estado["multisup_inversores"][0]["eta_inversor"] = 0.96
    else:
        estado["multisup_inversores"][0]["ficha"] = {**_FICHA, "Vdc_max": 1100.0}
    retiradas = invalidar_por_cambio_electrico(estado)
    assert "multisup_activo" in retiradas and "multisup_activo" not in estado
    assert estado["poa_superficies"] == {1: "poa"}
    assert estado["superficies_bipv"][0]["firma_poa"] == "poa-1"


@pytest.mark.parametrize("cambio", ["agregar", "eliminar", "desactivar", "renombrar"])
def test_cambios_de_superficie_no_son_cambio_electrico(cambio):
    from calculos.diseno_electrico_multisup import invalidar_por_cambio_electrico
    estado = _estado_publicado()
    invalidar_por_cambio_electrico(estado)
    sups = estado["superficies_bipv"]
    if cambio == "agregar":
        sups.append(_sup("Pérgola", 3, [_grupo(n_serie=8, n_paralelo=1)]))
    elif cambio == "eliminar":
        sups.pop()
    elif cambio == "desactivar":
        sups[1]["activa"] = False
    else:
        sups[1]["nombre"] = "Cubierta"
    assert invalidar_por_cambio_electrico(estado) == [] and estado["multisup_activo"]


# ── Strings de distinto largo en el mismo MPPT (antes de A3, 25-sep-2026) ──
def _dos_grupos(ns1, ns2, mppt2=1, np1=1, np2=1):
    sup = _sup(grupos=[_grupo("G1", n_serie=ns1, n_paralelo=np1),
                       _grupo("G2", mppt=mppt2, n_serie=ns2, n_paralelo=np2)], area=500.0)
    return _diag([sup], [_inv(ficha=dict(_SG5), P_ac_nom_W=5000.0)], _paneles(Fachada=_ASP))


def test_strings_de_distinto_largo_en_el_mismo_mppt_es_rojo():
    d = _dos_grupos(8, 6)
    m = d["mppt"][0]
    c = _checks(m)["Mismo N serie en el MPPT"]
    assert c["estado"] == "rojo" and c["valor"] == "6 y 8" and c["unidad"] == "módulos"
    assert m["estado"] == "rojo" and d["estado_global"] == "rojo"
    bloqueo = next(b for b in d["bloqueos"] if "distinto largo" in b)
    # Explicación para quien aprende: qué pasa, con qué valores y cómo arreglarlo.
    assert "«INV-1 · MPPT 1»: strings de distinto largo en el mismo MPPT" in bloqueo
    assert "Fachada · G1: 8 módulos" in bloqueo and "Fachada · G2: 6 módulos" in bloqueo
    assert "mismo voltaje" in bloqueo and "mismo N serie" in bloqueo and "MPPT distintos" in bloqueo


def test_mismo_largo_en_el_mppt_es_verde():
    c = _checks(_dos_grupos(8, 8)["mppt"][0])["Mismo N serie en el MPPT"]
    assert c["estado"] == "verde" and c["valor"] == "8"
    assert not any("distinto largo" in b for b in _dos_grupos(8, 8)["bloqueos"])


def test_distinto_largo_en_mppt_distintos_esta_bien():
    d = _dos_grupos(8, 6, mppt2=2)
    assert not any("distinto largo" in b for b in d["bloqueos"])
    assert all(_checks(m)["Mismo N serie en el MPPT"]["estado"] == "verde" for m in d["mppt"])


def test_distinto_largo_entre_superficies_en_el_mismo_mppt():
    a = _sup("Fachada", uid=1, grupos=[_grupo("G1", n_serie=8, n_paralelo=1)], area=500.0)
    b = _sup("Techo", uid=2, grupos=[_grupo("G1", n_serie=7, n_paralelo=1)], area=500.0)
    d = _diag([a, b], [_inv(ficha=dict(_SG5), P_ac_nom_W=5000.0)], _paneles(Fachada=_ASP, Techo=_ASP))
    bloqueo = next(b for b in d["bloqueos"] if "distinto largo" in b)
    assert "Fachada · G1: 8 módulos" in bloqueo and "Techo · G1: 7 módulos" in bloqueo


def test_n_serie_vacio_no_da_falso_rojo_de_largo():
    # Un grupo aún sin N serie ya tiene su propio 🔴; no debe sumar el de largo.
    d = _dos_grupos(8, None)
    assert not any("distinto largo" in b for b in d["bloqueos"])


def test_pagina_explica_el_largo_de_los_strings():
    src = _PAGINA.read_text(encoding="utf-8")
    assert "Mismo N serie en el MPPT" in src and "\"N serie de los strings\"" in src
