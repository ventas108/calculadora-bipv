# -*- coding: utf-8 -*-
"""Spec 08-interfaz/ruta-proyecto (2-oct-2026).

El usuario: «cuando se marque el tipo de instalación y haya dudas, que se
visualice pictográficamente (los módulos aguas abajo) el paso a paso». Tras
desplegar el PR #111 (solo el manual) esperaba verlo en 🏠 Proyecto.
"""
from pathlib import Path

import pandas as pd
import pytest

from calculos.ruta_proyecto import (
    RUTA_BIPV, RUTA_GRANJA, estado_ruta, html_ruta, resumen, ruta_de, siguiente,
)

_RAIZ = Path(__file__).resolve().parents[1]
_GEO = {"gcr": 0.398, "altura_m": 2.63, "ancho_colector_m": 2.626}


def _claves(ruta):
    return [p.clave for p in ruta]


def test_rutas_en_el_orden_del_manual():
    g = _claves(RUTA_GRANJA)
    assert g.index("sol_1") < g.index("dim") < g.index("granja") < g.index("sol_2") < g.index("optico")
    for ruta in (_claves(RUTA_GRANJA), _claves(RUTA_BIPV)):
        assert ruta.index("unifilar") < ruta.index("produccion")
        assert ruta.index("presupuesto") < ruta.index("financiero")
        assert ruta[0] == "proyecto" and ruta[-1] == "reporte"
    assert "granja" not in _claves(RUTA_BIPV) and "vista3d" not in _claves(RUTA_GRANJA)
    assert ruta_de("Granja fotovoltaica") is RUTA_GRANJA and ruta_de("Fachada BIPV") is RUTA_BIPV
    assert ruta_de(None) is RUTA_BIPV


def test_las_paginas_existen():
    for p in {p.pagina for p in RUTA_BIPV + RUTA_GRANJA}:
        assert (_RAIZ / p).exists(), p


def test_proyecto_nuevo_siguiente_es_recurso_solar():
    pasos = estado_ruta("Fachada BIPV", {"tipo_instalacion": "Fachada BIPV"})
    assert pasos[0]["estado"] == "listo"
    sig = siguiente(pasos)
    assert sig["clave"] == "sol" and sig["estado"] == "siguiente"
    assert {x["estado"] for x in pasos if x["clave"] in ("sketchup", "motor_iv", "vista3d", "baterias")} == {"opcional"}
    assert next(x for x in pasos if x["clave"] == "retie")["estado"] == "verificacion"


def test_granja_segunda_pasada_de_recurso_solar():
    base = {"tipo_instalacion": "Granja fotovoltaica", "tmy_df": object(), "poa_df": pd.DataFrame(),
            "inversor_dict_dim": {}, "N_serie": 20, "filas_energia": dict(_GEO)}
    # Geometría enviada pero la POA se calculó sin ella: 🟠 en la 2.ª pasada.
    pasos = estado_ruta("Granja fotovoltaica", {**base, "poa_geometria_filas": None})
    sol2 = next(x for x in pasos if x["clave"] == "sol_2")
    assert sol2["estado"] == "desactualizado" and "geometría" in sol2["motivo"]
    assert siguiente(pasos)["clave"] == "sol_2"
    # Recalculada con la geometría del campo: ✅ y sigue el Motor Óptico.
    pasos = estado_ruta("Granja fotovoltaica", {**base, "poa_geometria_filas": dict(_GEO)})
    assert next(x for x in pasos if x["clave"] == "sol_2")["estado"] == "listo"
    assert siguiente(pasos)["clave"] == "optico"


def test_produccion_desactualizada_por_la_revision_del_reporte():
    estado = {"tipo_instalacion": "Granja fotovoltaica", "E_ac_anual_kWh": 604_195.0,
              "res_produccion": {"perdida_ohmica_dc_modo": "calculado"},
              "produccion_n_inversores": 3, "reparto_strings_inversores": [7, 7, 7, 7]}
    pasos = estado_ruta("Granja fotovoltaica", estado)
    prod = next(x for x in pasos if x["clave"] == "produccion")
    assert prod["estado"] == "desactualizado" and "inversores" in prod["motivo"]
    assert siguiente(pasos)["clave"] == "sol_1"            # primero lo que falta antes


def test_granja_sin_cables_reales_siguiente_es_unifilar():
    geo = dict(_GEO)
    estado = {"tipo_instalacion": "Granja fotovoltaica", "tmy_df": 1, "poa_df": pd.DataFrame(),
              "inversor_dict_dim": {}, "N_serie": 20, "filas_energia": geo, "poa_geometria_filas": geo,
              "motor_optico_ok": True, "pct_mismatch_fab": 2.0, "E_ac_anual_kWh": 606_522.0,
              "res_produccion": {"perdida_ohmica_dc_modo": "manual"}, "granja_electrico_cfg": {"x": 1},
              "co2_anual_t": 76.4}
    pasos = estado_ruta("Granja fotovoltaica", estado)
    co2 = next(x for x in pasos if x["clave"] == "co2")
    assert co2["estado"] == "desactualizado" and "Producción" in co2["motivo"]   # aguas abajo
    assert next(x for x in pasos if x["clave"] == "produccion")["estado"] == "desactualizado"
    sig = siguiente(pasos)
    assert sig["clave"] == "unifilar" and sig["estado"] == "siguiente"


def test_html_y_resumen():
    pasos = estado_ruta("Fachada BIPV", {"tipo_instalacion": "Fachada BIPV"})
    h = html_ruta(pasos)
    assert h.count('class="ruta-paso"') == len(RUTA_BIPV) and "flex-wrap:wrap" in h
    assert "▶️" in h and "✅" in h and "1. Proyecto" in h
    assert resumen(pasos).startswith("1 de ")


def test_proyecto_muestra_la_ruta():
    src = (_RAIZ / "pages" / "1_🏠_Proyecto.py").read_text(encoding="utf-8")
    assert "estado_ruta(" in src and "html_ruta(" in src and "🧭 Ruta del proyecto" in src
    assert src.index("html_ruta(") > src.index('"Tipo de instalación"')


def test_manual_del_asistente_seccion_121():
    kb = (_RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    i = kb.index("## 121.")
    s = kb[i:kb.find("\n## ", i + 5) if kb.find("\n## ", i + 5) > 0 else None]
    for t in ("Ruta del proyecto", "✅", "🟠", "▶️", "⚪", "🔎", "Tipo de instalación", "119"):
        assert t in s, t
    assert i < kb.rindex("Calculadora BIPV — Innovación Química")
    assert "PVsyst" not in s and "pendiente" not in s
