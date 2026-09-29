# -*- coding: utf-8 -*-
"""Spec ``07-informes/unifilar-retie-bifacial-cruce`` (29-sep-2026).

⚡ Diagrama Unifilar y 📋 Ficha RETIE coherentes con 🔆 Motor Óptico bifacial,
🔀 Mismatch y el string que cruza superficies de 🗺️ Vista 3D:

- Corriente de diseño DC con la cara trasera (BNPI, IEC TS 60904-1-2:
  1000 W/m² frente + 135 W/m² atrás): Isc_BNPI = Isc × (1 + φ × 0.135).
  JAM66D46-720/LB (φ 0.80): 18.59 A → 20.60 A.
- Módulos donde están y cruce marcado en la topología.
- Cableado que de verdad aplica Producción.
"""
from pathlib import Path

import pytest

from calculos.corriente_bifacial import (
    BNPI_TRASERA_W_M2,
    factor_isc_bifacial,
    panel_para_corriente,
    phi_proyecto,
    phi_superficie,
)
from datos.tecnologias_bipv import MODULOS_BIPV

ROOT = Path(__file__).resolve().parents[1]
PAG20 = ROOT / "pages" / "20_⚡_Diagrama_Unifilar.py"
PAG21 = ROOT / "pages" / "21_📋_Ficha_Validacion_RETIE.py"
PAG5 = ROOT / "pages" / "5_🔀_Mismatch.py"
JAM = {"Isc_stc": 18.59, "Imp_stc": 17.48, "Voc_stc": 49.0, "Vmp_stc": 41.19,
       "Tk_beta": -0.25, "bifacialidad_pct": 80.0, "Pmax_stc": 720.0}
MONO = dict(JAM, bifacialidad_pct=0.0)
CFG = {"bifacialidad": 0.80, "altura_m": 1.0, "gcr": 0.4, "ancho_colector_m": 2.4}


# ── Criterio 1: la cuenta del JAM66D46-720/LB ────────────────────────────────
def test_factor_bnpi():
    assert BNPI_TRASERA_W_M2 == 135.0
    assert factor_isc_bifacial(0.80) == pytest.approx(1.108)
    assert factor_isc_bifacial(0.0) == 1.0
    assert factor_isc_bifacial(1.7) == pytest.approx(1.135)       # se recorta a 1
    p = panel_para_corriente(JAM, 0.80)
    assert p["Isc_stc"] == pytest.approx(20.598, abs=1e-3)
    assert p["Isc_stc_frontal"] == 18.59 and p["factor_bifacial"] == pytest.approx(1.108)
    assert p["Voc_stc"] == JAM["Voc_stc"] and p["Vmp_stc"] == JAM["Vmp_stc"]
    assert JAM["Isc_stc"] == 18.59                                 # no muta el original


def test_retie_isc_diseno_y_fusible():
    from calculos.ficha_validacion_retie import calcular_retie, construir_config_retie
    cfg = construir_config_retie(isc_a=18.59, factor_bifacial=factor_isc_bifacial(0.80),
                                 n_paneles=308, n_serie=28, potencia_w=720)
    calc = calcular_retie(cfg)
    assert calc["isc_bnpi_a"] == pytest.approx(20.6, abs=0.01)
    assert calc["isc_diseno_string_a"] == pytest.approx(25.7, abs=0.06)   # 20.60 × 1.25
    base = calcular_retie(construir_config_retie(isc_a=18.59, n_paneles=308, n_serie=28, potencia_w=720))
    assert base["isc_diseno_string_a"] == pytest.approx(23.2, abs=0.06)   # sin cambio


# ── Criterio 2 y 3: φ según el modelo, la fachada y el panel ─────────────────
def test_phi_proyecto():
    assert phi_proyecto({"bifacial_activo": True, "bifacial_cfg": CFG}, JAM) == (pytest.approx(0.8), "modelo")
    adosada = dict(CFG, factor_vista_trasera=0.0)
    assert phi_proyecto({"bifacial_activo": True, "bifacial_cfg": adosada}, JAM)[0] == 0.0
    assert phi_proyecto({}, JAM) == (pytest.approx(0.8), "panel")          # lado seguro
    assert phi_proyecto({}, MONO) == (0.0, "monofacial")


def test_phi_superficie_fachada_adosada_y_techo():
    est = {"bifacial_activo": True, "bifacial_cfg": CFG}
    techo = {"nombre": "Techo", "tilt_deg": 10}
    adosada = {"nombre": "F", "tilt_deg": 90, "montaje_fachada": "Adosada al muro (sellada)"}
    ventilada = {"nombre": "F", "tilt_deg": 90, "montaje_fachada": "Ventilada con superficie reflejante"}
    assert phi_superficie(techo, est, JAM)[0] == pytest.approx(0.8)
    assert phi_superficie(adosada, est, JAM)[0] == 0.0
    assert phi_superficie(ventilada, est, JAM)[0] == pytest.approx(0.8)
    apagado = dict(est, ms_bifacial_on=False)
    assert phi_superficie(techo, apagado, JAM) == (pytest.approx(0.8), "panel")
    assert phi_superficie(techo, {}, MONO) == (0.0, "monofacial")


# ── Criterio 4: Unifilar ─────────────────────────────────────────────────────
def test_unifilar_corriente_dc_con_factor():
    from calculos.diagrama_unifilar import calcular_perdida_ohmica
    inv = {"P_ac_nom_W": 100000}
    tramos = [{"nombre": "Granja", "longitud_m": 30, "calibre_mm2": 6, "n_paneles": 308}]
    base = calcular_perdida_ohmica(panel=JAM, inversor=inv, N_strings_tracker=1, tension_red_V=480,
                                   tramos_dc=tramos, n_paneles_total=308)
    bif = calcular_perdida_ohmica(panel=JAM, inversor=inv, N_strings_tracker=1, tension_red_V=480,
                                  tramos_dc=tramos, n_paneles_total=308, factor_bifacial=1.108)
    assert bif["corriente_dc_diseno_A"] == pytest.approx(base["corriente_dc_diseno_A"] * 1.108)
    assert bif["resistencia_dc_efectiva_ohm"] == base["resistencia_dc_efectiva_ohm"]   # R no cambia
    assert bif["factor_bifacial"] == 1.108


def test_paginas_pasan_el_factor():
    src20 = PAG20.read_text(encoding="utf-8")
    src21 = PAG21.read_text(encoding="utf-8")
    assert "factor_bifacial=_factor_bif_unif" in src20
    assert "factor_bifacial=_factor_bif_retie" in src21
    assert "Isc BNPI" in src21


# ── Criterio 5: ⚡ Diseño eléctrico de Vista 3D ──────────────────────────────
def _sups(montaje=None, cruce=None):
    g1 = {"gid": "G1", "topologia": "string", "inversor_id": "INV-1", "mppt": 1, "n_serie": 10, "n_paralelo": 2}
    if cruce:
        g1["cruce"] = cruce
    este = {"nombre": "Este", "uid": "u1", "tipo": "Techo", "tilt_deg": 10, "azimuth_deg": 90,
            "area_m2": 200.0, "activa": True, "grupos": [g1]}
    oeste = {"nombre": "Oeste", "uid": "u2", "tipo": "Techo", "tilt_deg": 10, "azimuth_deg": 270,
             "area_m2": 200.0, "activa": True,
             "grupos": [{"gid": "G1", "topologia": "string", "inversor_id": "INV-1", "mppt": 2,
                         "n_serie": 10, "n_paralelo": 1}]}
    return [este, oeste]


_INV = [{"inversor_id": "INV-1", "tipo": "", "eta_inversor": 0.97, "P_ac_nom_W": 15000.0,
         "nombre": "X", "origen_ficha": "manual",
         "ficha": {"Vdc_max": 1100, "Vmppt_min": 200, "Vmppt_max": 1000, "Isc_max_tracker": 40,
                   "n_trackers": 2, "n_strings_tracker": 2}}]
_TEMPS = {"T_frio": 20, "T_real": 55, "T_extremo": 64, "origen": "proyecto"}


def test_diseno_electrico_isc_con_factor():
    from calculos.diseno_electrico_multisup import validar_diseno_electrico
    paneles = {"Este": {"panel": JAM, "nombre": "JAM"}, "Oeste": {"panel": JAM, "nombre": "JAM"}}
    mono = {"Este": {"panel": MONO, "nombre": "JAM"}, "Oeste": {"panel": MONO, "nombre": "JAM"}}
    base = validar_diseno_electrico(_sups(), _INV, mono, _TEMPS)
    bif = validar_diseno_electrico(_sups(), _INV, paneles, _TEMPS, bifacial=(CFG, True))
    # sin datos del modelo, el panel bifacial usa su ficha (lado seguro) y avisa
    seguro = validar_diseno_electrico(_sups(), _INV, paneles, _TEMPS)
    assert {m["mppt"]: m["isc_total"] for m in seguro["mppt"]}[1] == pytest.approx(
        {m["mppt"]: m["isc_total"] for m in bif["mppt"]}[1])
    assert any("lado seguro" in a for a in seguro["avisos"])
    isc = {m["mppt"]: m["isc_total"] for m in base["mppt"]}
    isc_b = {m["mppt"]: m["isc_total"] for m in bif["mppt"]}
    assert isc_b[1] == pytest.approx(isc[1] * 1.108, rel=1e-6)
    grupo = next(g for g in bif["grupos"] if g["superficie"] == "Este")
    assert grupo["factor_bifacial"] == pytest.approx(1.108)


# ── Criterio 6: topología con cruce y módulos físicos ────────────────────────
def test_topologia_cruce_y_modulos_fisicos():
    from calculos.topologia_electrica import topologia_desde_estado
    estado = {"multisup_activo": True, "superficies_bipv": _sups(cruce={"uid": "u2", "modulos": 4}),
              "multisup_inversores": _INV, "bifacial_activo": True, "bifacial_cfg": CFG,
              "panel_dict": JAM, "panel_nombre_dim": "JAM",
              "T_min_diseno": 20, "T_cel_realista": 55, "T_cel_extremo": 64}
    topo = topologia_desde_estado(estado)
    g = next(g for inv in topo["inversores"] for r in inv["ramas"] for g in r["grupos"]
             if g["superficie"] == "Este")
    assert "4 de 10 módulos en «Oeste»" in g["cruce_texto"]
    assert g["isc_stc_A"] == pytest.approx(18.59 * 1.108, abs=1e-3)
    assert g["isc_frontal_A"] == 18.59
    sup = {s["nombre"]: s for s in topo["superficies"]}
    assert sup["Este"]["modulos_fisicos"] == 12 and sup["Oeste"]["modulos_fisicos"] == 18
    assert sup["Este"]["modulos"] == 20                                    # eléctricos, como antes


def test_ficha_retie_muestra_modulos_fisicos_y_fusible_bnpi():
    from calculos.ficha_validacion_retie import _lineas_multisuperficie, validar_retie_multisuperficie
    from calculos.topologia_electrica import topologia_desde_estado
    estado = {"multisup_activo": True, "superficies_bipv": _sups(cruce={"uid": "u2", "modulos": 4}),
              "multisup_inversores": _INV, "bifacial_activo": True, "bifacial_cfg": CFG,
              "panel_dict": JAM, "panel_nombre_dim": "JAM",
              "T_min_diseno": 20, "T_cel_realista": 55, "T_cel_extremo": 64}
    topo = topologia_desde_estado(estado)
    calc = {"potencia_dc_kwp": 21.6, "por_inversor": []}
    campo = _lineas_multisuperficie(topo, calc, 480)["campo"]
    assert any(l.startswith("Este: 12 mód. (20 en sus strings)") for l in campo), campo
    # caja combinadora forzada: el fusible cita el Isc BNPI
    topo["inversores"][0]["ramas"][0]["caja_combinadora"] = True
    checks = validar_retie_multisuperficie(topo, topo["diagnostico"], calc)
    caja = next(c for c in checks if c["titulo"].startswith("Caja combinadora"))
    assert "Isc BNPI (bifacial) 20,60 A" in caja["detalle"]
    assert "32,18 A" in caja["detalle"]


def test_unifilar_rotula_el_cruce():
    from calculos.diagrama_unifilar import _lineas_rama
    rama = {"grupos": [{"superficie": "Este", "gid": "G1", "n_serie": 10, "n_paralelo": 2,
                        "modulos": 20, "panel": "JAM", "cruce_texto": "4 de 10 módulos en «Oeste»"}]}
    assert any("cruza" in l and "Oeste" in l for l in _lineas_rama(rama, False))


# ── Criterio 7: cableado ─────────────────────────────────────────────────────
def test_mismatch_avisa_cableado_del_unifilar():
    src = PAG5.read_text(encoding="utf-8")
    assert 'st.session_state.get("perdida_ohmica_unifilar")' in src
    assert "Producción usa el cálculo real de ⚡ Diagrama Unifilar" in src


def test_unifilar_multisup_muestra_el_cableado_real():
    src = PAG20.read_text(encoding="utf-8")
    assert "cables DC 1,5 % de 🔀 Mismatch" not in src
    assert "st.session_state.get('pct_cableado_dc'" in src


# ── Criterio 8: manual ───────────────────────────────────────────────────────
@pytest.mark.parametrize("pregunta, texto", [
    ("cuanto sube el isc del panel bifacial JAM66D46 en la ficha retie y el fusible", "20,60 A"),
    ("que es la corriente bnpi de un panel bifacial para el fusible", "135 W/m²"),
])
def test_manual(pregunta, texto):
    from calculos.asistente import BaseConocimiento
    secciones = BaseConocimiento.cargar().buscar(pregunta, k=6)
    candidatas = [s for s in secciones if "corriente bifacial" in s["titulo"].lower()]
    assert candidatas, [s["titulo"] for s in secciones]
    assert texto in "\n".join(s["texto"] for s in candidatas)
