# -*- coding: utf-8 -*-
"""Spec ``03-dimensionamiento/comparador-inversores-completo`` (1-oct-2026).

Revisión del ⚖️ Comparador de Inversores pedida por el usuario con la Granja
Apartadó (308 × JAM66D46-720/LB, Growatt MAX 100KTL3 LV corregido a su ficha:
1.100 V, MPPT 180–1.000 V, 10 MPPT, 40 A):

1. Solo revisaba el Vmp a la temperatura de trabajo, no a la extrema.
2. No usaba la revisión de la ficha del inversor.
3. Comparaba todos los inversores con el MISMO N en serie.
4. No mostraba el margen de Voc ni si los módulos se reparten exactos.
5. Sin precios daba TIR/LCOE que no eran comparables.
6. «Adoptar» no guardaba strings por MPPT ni el reparto: en modo
   «1 string por MPPT» Dimensionamiento volvía a 2 (46,5 A > 40 A).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from calculos.comparador_inversores import (
    comparar_mejores, estado_adopcion, filtrar_inversores_compatibles, mejor_n_por_inversor,
)
from calculos.dimensionamiento import resolver_n_strings_tracker

RAIZ = Path(__file__).resolve().parents[1]
PAGINA = next((RAIZ / "pages").glob("4b_*Comparador_Inversores.py"))
JAM = {"nombre": "JAM66D46-720/LB", "Pmax_stc": 720.0, "Voc_stc": 49.0, "Vmp_stc": 41.19, "Isc_stc": 18.59,
       "Imp_stc": 17.48, "Tk_beta": -0.25, "Tk_gamma": -0.29, "area_m2": 3.1064}
GROWATT = {"nombre": "Growatt MAX 100KTL3 LV", "Vdc_max": 1100.0, "Vmppt_min": 180.0, "Vmppt_max": 1000.0,
           "Vmppt_activo_min": 600.0, "n_trackers": 10, "n_strings_tracker": 2, "I_max_tracker": 32.0,
           "Isc_max_tracker": 40.0, "P_ac_nom_W": 100_000.0}
X1500 = {"nombre": "X1500", "Vdc_max": 1500.0, "Vmppt_min": 500.0, "Vmppt_max": 1300.0, "Vmppt_activo_min": 600.0,
         "n_trackers": 12, "n_strings_tracker": 2, "I_max_tracker": 30.0, "Isc_max_tracker": 40.0,
         "P_ac_nom_W": 100_000.0}
T = dict(T_frio=20.9, T_real=54.2)


def _fila(df, modelo):
    return df[df["modelo"] == modelo].iloc[0]


# ── 1 y 2: Vmp extremo y ficha ───────────────────────────────────────────────
def test_vmp_a_temperatura_extrema():
    justo = {**GROWATT, "nombre": "Justo", "Vmppt_activo_min": 830.0}   # Vmp 840 V real, 819 V extremo
    antes = filtrar_inversores_compatibles(JAM, {"Justo": justo}, 22, **T)
    assert bool(_fila(antes, "Justo")["compatible"])
    ahora = filtrar_inversores_compatibles(JAM, {"Justo": justo}, 22, **T, T_extremo=63.6)
    assert not bool(_fila(ahora, "Justo")["compatible"])
    assert "T extrema" in _fila(ahora, "Justo")["motivo"]


def test_ficha_contradictoria_y_margen_de_voc():
    mal = {**GROWATT, "nombre": "Mal", "Vmppt_max": 1200.0}            # MPPT por encima de 1.100 V
    lv = {**GROWATT, "Vdc_max": 1500.0, "Vmppt_max": 1300.0}            # el dato viejo del catálogo
    df = filtrar_inversores_compatibles(JAM, {"Mal": mal, "LV": lv, "OK": GROWATT}, 22, **T, T_extremo=63.6)
    assert not bool(_fila(df, "Mal")["compatible"]) and "Ficha contradictoria" in _fila(df, "Mal")["motivo"]
    assert bool(_fila(df, "LV")["compatible"]) and "🟠" in _fila(df, "LV")["ficha"]
    assert _fila(df, "OK")["ficha"] == "" and _fila(df, "OK")["margen_voc_pct"] == 1.0


# ── 3 y 4: mejor N por inversor ──────────────────────────────────────────────
def test_mejor_n_para_cada_inversor():
    df = mejor_n_por_inversor(JAM, {"G": GROWATT, "X": X1500}, 308, **T, T_extremo=63.6)
    g, x = _fila(df, "G"), _fila(df, "X")
    assert (g["N_serie"], g["strings"], g["sobrantes"], g["unidades"]) == (22, 14, 0, 2)
    assert g["reparto"] == [7, 7] and g["strings_por_tracker"] == 1 and g["nivel_voc"] == "🟠"
    assert g["dc_ac"] == 1.11
    # 1.500 V: strings de 28 y 2 unidades por la relación DC/AC (las entradas pedirían 1)
    assert (x["N_serie"], x["strings"], x["unidades"], x["unidades_por_entradas"]) == (28, 11, 2, 1)
    assert x["reparto"] == [6, 5] and x["nivel_voc"] == "🟢"


def test_sin_n_compatible_explica_el_motivo():
    chico = {**GROWATT, "nombre": "Chico", "Vdc_max": 300.0, "Vmppt_max": 250.0, "Vmppt_activo_min": 100.0}
    df = mejor_n_por_inversor(JAM, {"Chico": chico}, 308, **T, n_min=10)
    assert not bool(_fila(df, "Chico")["compatible"]) and "Voc" in _fila(df, "Chico")["motivo"]


# ── 5: precios ───────────────────────────────────────────────────────────────
def test_sin_precio_no_hay_tir_ni_lcoe():
    df = mejor_n_por_inversor(JAM, {"G": GROWATT, "X": X1500}, 310, **T, T_extremo=63.6)
    pac = np.clip(np.sin(np.linspace(0, np.pi * 365, 8760)), 0, None) * 180_000.0
    cmp = comparar_mejores(df, pac, 310, {"G": 4300.0}, 150_000.0, 950.0, 3900.0)
    g, x = (cmp[cmp["Modelo"] == m].iloc[0] for m in ("G", "X"))
    assert g["Precio"] == "cotización" and g["LCOE (USD/kWh)"] > 0 and g["CAPEX (USD)"] == 158_600
    assert x["Precio"] == "sin precio" and pd.isna(x["LCOE (USD/kWh)"]) and pd.isna(x["TIR (%)"])
    # 310 no se reparte exacto con ningún N: gana el margen de Voc (21 en serie, 14
    # strings = 294 módulos) y la energía se escala por los módulos usados
    assert (g["N en serie"], g["Módulos"]) == (21, 294)
    assert abs(g["E_ac (kWh/año)"] - pac.sum() / 1000 * 294 / 310) < 1.0
    assert cmp.iloc[0]["Modelo"] == "G"


# ── 6: adopción completa ─────────────────────────────────────────────────────
def test_adoptar_deja_dimensionamiento_igual():
    fila = _fila(mejor_n_por_inversor(JAM, {"G": GROWATT}, 308, **T, T_extremo=63.6), "G").to_dict()
    e = {"N_total_cadenas_proyecto": 11, "N_str_tr": 2, "N_str_tr_usado": 2,
         "N_str_tr_fuente_ref": ("total", "G", 11, 10), "reparto_strings_inversores": [6, 5]}
    e.update(estado_adopcion(fila, GROWATT, "JAM66D46-720/LB"))
    assert e["N_serie"] == 22 and e["N_str_tr_usado"] == 1 and e["reparto_strings_inversores"] == [7, 7]
    assert e["N_inversores_proyecto"] == 2 and e["N_inversores_proyecto_ref"] == "G"
    # 📐 Dimensionamiento resuelve los strings por MPPT con el total adoptado y respeta 1
    r = resolver_n_strings_tracker(GROWATT, "G", e, N_total_cadenas=e["N_total_cadenas_proyecto"])
    assert r["valor"] == 1 and not r["recalculado"]


def test_la_pagina_usa_la_adopcion_completa():
    src = PAGINA.read_text(encoding="utf-8")
    assert src.count("estado_adopcion(") == 2
    assert "T_extremo=T_extremo" in src


def test_pagina_muestra_la_mejor_configuracion():
    import calculos.auth as _auth
    import calculos.trm_utils as _trm
    _auth.requerir_login = lambda solo_admin=False: {"email": "t@t", "rol": "admin", "activo": True, "nombre": "T"}
    pac = np.clip(np.sin(np.linspace(0, np.pi * 365, 8760)), 0, None) * 180.0
    at = AppTest.from_file(str(PAGINA), default_timeout=120)
    for k, v in {"panel_dict": JAM, "panel_nombre_dim": JAM["nombre"], "N_serie": 22, "N_paneles_final": 308,
                 "N_paneles_dim": 308, "T_min_diseno": 20.9, "T_cel_realista": 54.2, "T_cel_extremo": 63.6,
                 "res_produccion": {"df_horario": pd.DataFrame({"P_ac_sin_recorte_kW": pac}),
                                    "E_ac_anual_kWh": float(pac.sum()), "P_stc_kW": 221.76},
                 _trm._KEY_VALOR: 3900.0, _trm._KEY_FUENTE: "manual"}.items():
        at.session_state[k] = v
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("Mejor configuración para cada inversor" in s.value for s in at.subheader)
    assert any(n.label.startswith("T. de celda extrema") for n in at.number_input)


def test_manual_del_asistente_lo_explica():
    kb = (RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    seccion = kb[kb.index("## 104."):]
    for texto in ("Mejor configuración para cada inversor", "temperatura extrema", "precio", "1 string por MPPT",
                  "Adoptar", "22"):
        assert texto in seccion, texto
    assert "PVsyst" not in seccion
