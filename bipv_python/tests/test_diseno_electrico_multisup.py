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
    d = _diag([_sup(grupos=[_grupo(n_serie=6, n_paralelo=5)])], [_inv()], _paneles(Fachada=_ASP))
    assert _checks(d["mppt"][0])["Strings ≤ entradas del MPPT"]["estado"] == "rojo"


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
