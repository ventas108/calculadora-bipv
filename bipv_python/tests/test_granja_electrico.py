# -*- coding: utf-8 -*-
"""Spec ``07-informes/granja-electrico-bloques`` (granja FV fase 5, 30-sep-2026).

Strings por fila, bloques por inversor, largo de cables y caída de tensión
desde la geometría del campo; alimenta ⚡ Diagrama Unifilar (un tramo DC por
string) y 📋 Ficha RETIE. Caso Apartadó: 308 × JAM66D46-720/LB, 11 strings
de 28, 2 inversores de 100 kW (reparto 6 + 5).
"""
import math
from pathlib import Path

import pytest

from calculos.diagrama_unifilar import _resistividad_cobre, calcular_perdida_ohmica
from calculos.granja_electrico import (
    LIMITE_CAIDA_PCT,
    armar_strings,
    avisos_bloques,
    checks_retie,
    diseno_desde_estado,
    disenar_bloques,
    tramos_para_unifilar,
)
from calculos.granja_fv import GEOMETRIA_DEFECTO, calcular_campo, dimensiones_modulo

PAGINAS = Path(__file__).resolve().parents[1] / "pages"
JAM = {"nombre": "JA Solar JAM66D46-720/LB", "dimensiones_mm": "2384x1303x33 mm", "area_m2": 3.1064,
       "Pmax_stc": 720.0, "Imp_stc": 17.48, "Vmp_stc": 41.19, "Isc_stc": 18.59, "Voc_stc": 49.0}
GEO = {"tilt_deg": 10.0, "azimut_deg": 180.0, "ancho_terreno_m": 80.0, "largo_terreno_m": 30.0,
       "modulos_pendiente": 2, "orientacion": "horizontal", "modulos_por_mesa": 31, "mesas_por_fila": 1,
       "pasillo_m": 3.0, "pitch_m": 6.60, "altura_libre_m": 2.4}
RHO = _resistividad_cobre(45.0)


def _campo(**kw):
    g = {**GEOMETRIA_DEFECTO, **GEO, **kw}
    return calcular_campo(g, dimensiones_modulo(JAM), 308, pmax_w=720.0)


def _dis(**kw):
    return disenar_bloques(_campo(), JAM, 28, [6, 5], 100_000.0, **kw)


# ── Strings por fila ─────────────────────────────────────────────────────────
def test_apartado_11_strings_completos():
    a = armar_strings(_campo(), 28)
    assert len(a["strings"]) == 11 and a["sobrantes"] == 0
    # 62 módulos por fila no es múltiplo de 28: hay strings que siguen en la fila siguiente
    assert a["cruzan"] == 4


def test_fila_multiplo_de_la_serie_no_cruza():
    c = calcular_campo({**GEOMETRIA_DEFECTO, **GEO, "modulos_por_mesa": 28}, dimensiones_modulo(JAM), 280,
                       pmax_w=720.0)
    a = armar_strings(c, 28)
    assert a["cruzan"] == 0 and len(a["strings"]) == 10
    assert set(a["por_fila"].values()) == {2}


def test_strings_sobrantes():
    a = armar_strings(_campo(), 30)
    assert a["sobrantes"] == 308 - 10 * 30


# ── Bloques ──────────────────────────────────────────────────────────────────
def test_bloques_con_el_reparto_de_dimensionamiento():
    d = _dis()
    assert d["reparto"] == [6, 5]
    assert [b["strings"] for b in d["bloques"]] == [6, 5]
    assert [b["modulos"] for b in d["bloques"]] == [168, 140]
    assert {s["inversor"] for s in d["strings"][:6]} == {1} and {s["inversor"] for s in d["strings"][6:]} == {2}


def test_reparto_invalido_se_reparte_parejo():
    d = disenar_bloques(_campo(), JAM, 28, [10, 10], 100_000.0)
    assert d["reparto"] == [6, 5]


# ── Cables y caída de tensión ────────────────────────────────────────────────
def test_caida_dc_con_la_formula():
    d = _dis(calibre_dc_mm2=6.0)
    s = max(d["strings"], key=lambda x: x["longitud_dc_m"])
    esperada = 200.0 * s["longitud_dc_m"] * RHO * 17.48 / (6.0 * 28 * 41.19)
    assert s["caida_dc_pct"] == pytest.approx(esperada, abs=1e-3)
    assert d["caida_dc_max_pct"] == pytest.approx(esperada, abs=1e-3)


def test_caida_ac_trifasica():
    d = _dis(calibre_ac_mm2=70.0, tension_ac_v=400.0)
    b = d["bloques"][1]
    i = 100_000.0 / (math.sqrt(3) * 400.0)
    assert b["corriente_ac_a"] == pytest.approx(i, abs=0.1)
    assert b["caida_ac_pct"] == pytest.approx(100 * math.sqrt(3) * b["longitud_ac_m"] * RHO * i / (70 * 400), abs=1e-3)


def test_mas_calibre_menos_caida_y_mas_holgura_mas_cable():
    assert _dis(calibre_dc_mm2=10.0)["caida_dc_max_pct"] < _dis(calibre_dc_mm2=4.0)["caida_dc_max_pct"]
    assert _dis(holgura=0.20)["dc_total_m"] > _dis(holgura=0.0)["dc_total_m"]


def test_inversor_al_centro_acorta_el_dc():
    assert _dis(ubicacion_inversor="centro")["dc_total_m"] < _dis(ubicacion_inversor="cabecera")["dc_total_m"]


def test_punto_de_conexion_lejano_alarga_el_ac():
    assert _dis(punto_conexion="atras_derecha")["ac_total_m"] > _dis(punto_conexion="frente_izquierda")["ac_total_m"]


# ── Unifilar: un tramo por string, misma resistencia ─────────────────────────
def test_tramos_para_unifilar_dan_la_misma_resistencia():
    d = _dis()
    tramos = tramos_para_unifilar(d)
    assert len(tramos) == 11 and all(t["n_paneles"] == 28 for t in tramos)
    r = calcular_perdida_ohmica(panel=JAM, inversor={"P_ac_nom_W": 100_000}, N_strings_tracker=1,
                                n_inversores=2, tension_red_V=400, tramos_dc=tramos, n_paneles_total=308)
    assert r["resistencia_dc_efectiva_ohm"] * 1000 == pytest.approx(d["resistencia_dc_efectiva_mohm"], abs=0.01)
    assert 0.2 < d["perdida_dc_stc_pct"] < 1.5          # referencia: 1,5 % a STC por defecto


# ── Avisos y RETIE ───────────────────────────────────────────────────────────
def _niveles(lst):
    return {a["id"]: a["nivel"] for a in lst}


def test_avisos_de_apartado():
    niv = _niveles(avisos_bloques(_dis(), 308))
    assert niv == {"strings_completos": "🟢", "cruzan_filas": "🟠", "caida_dc_max_pct": "🟢",
                   "caida_ac_max_pct": "🟢"}


def test_caida_alta_y_modulos_incompletos():
    d = _dis(calibre_dc_mm2=1.5, calibre_ac_mm2=1.5, holgura=0.5)
    niv = _niveles(avisos_bloques(d, 310))
    assert niv["strings_completos"] == "🔴"
    assert niv["caida_dc_max_pct"] == "🟠" and d["caida_dc_max_pct"] > LIMITE_CAIDA_PCT
    assert niv["caida_ac_max_pct"] == "🟠"


def test_checks_retie_en_su_formato():
    ch = checks_retie({**_dis(), "modulos_proyecto": 308})
    assert {c["nivel"] for c in ch} <= {"OK", "PENDIENTE", "ERROR"}
    assert any(c["titulo"] == "Granja: caída de tensión DC" and c["nivel"] == "OK" for c in ch)
    assert any(c["titulo"] == "Granja: strings que cruzan filas" and c["nivel"] == "PENDIENTE" for c in ch)


def test_diseno_desde_estado():
    estado = {"granja_fv": GEO, "panel_dict": JAM, "N_serie": 28, "N_paneles_final": 308,
              "reparto_strings_inversores": [6, 5], "inversor_dict_dim": {"P_ac_nom_W": 100_000.0},
              "tilt_fachada": 10, "azimuth_fachada": 180,
              "granja_electrico_cfg": {"calibre_dc_mm2": 4.0}}
    d = diseno_desde_estado(estado)
    assert d["n_strings"] == 11 and d["calibre_dc_mm2"] == 4.0 and d["modulos_proyecto"] == 308
    assert diseno_desde_estado({**estado, "N_serie": 0}) is None
    assert diseno_desde_estado({k: v for k, v in estado.items() if k != "granja_fv"}) is None


# ── Páginas y manual ─────────────────────────────────────────────────────────
def _fuente(patron):
    return next(PAGINAS.glob(patron)).read_text(encoding="utf-8")


def test_paginas_usan_el_mismo_diseno():
    g = _fuente("9b_*Granja_FV.py")
    assert "diseno_desde_estado(" in g and "avisos_bloques(" in g and "granja_electrico_cfg" in g
    u = _fuente("20_*Diagrama_Unifilar.py")
    assert "tramos_para_unifilar(" in u and "Usar los cables de 🌾 Granja FV" in u
    r = _fuente("21_*RETIE.py")
    assert "checks_retie(" in r
    for src in (u, r):
        assert '"Granja fotovoltaica"' in src


def test_manual_del_asistente_lo_explica():
    kb = (Path(__file__).resolve().parents[1] / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    seccion = kb[kb.index("## 97."):]
    for texto in ("strings", "6 + 5", "caída de tensión", "3 %", "Usar los cables de 🌾 Granja FV",
                  "1,5 %", "NTC 2050"):
        assert texto in seccion, texto
    assert "PVsyst" not in seccion
