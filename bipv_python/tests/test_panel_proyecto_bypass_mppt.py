"""Spec 08-interfaz/panel-proyecto-bypass-mppt.

El bypass y el MPPT por superficie de Vista 3D arrancaban con el panel
«ASP-ST1-T40» y 8 módulos en serie, ajenos al proyecto: si el usuario no los
cambiaba, la energía publicada por el bypass se calculaba con otro panel.
"""
import ast
from pathlib import Path

import pytest

from calculos.strings_superficie import (
    ORIGEN_DIMENSIONAMIENTO,
    ORIGEN_ESTIMADO_AREA,
    ORIGEN_SUPERFICIE,
    ORIGENES_STRINGS,
    es_panel_del_proyecto,
    opciones_panel_superficie,
    strings_superficie,
)
from datos.tecnologias_bipv import MODULOS_BIPV

_PAGINA = Path(__file__).resolve().parents[1] / "pages" / "9_🗺️_Vista_3D.py"
_EN_CATALOGO = "ASP-ST1-T40"


def _panel_fuera_de_catalogo(**cambios):
    panel = {**MODULOS_BIPV[_EN_CATALOGO], "modelo": "Excel-BIPV-300"}
    panel.update(cambios)
    return panel


# ── Panel por defecto ────────────────────────────────────────────────────────
def test_panel_del_proyecto_en_catalogo_es_la_primera_opcion():
    opciones, aviso = opciones_panel_superficie(MODULOS_BIPV[_EN_CATALOGO], _EN_CATALOGO, MODULOS_BIPV)
    etiquetas = list(opciones)
    assert aviso is None
    assert etiquetas[0] == f"Panel del proyecto ({_EN_CATALOGO})"
    assert opciones[etiquetas[0]] == MODULOS_BIPV[_EN_CATALOGO]
    assert set(etiquetas[1:]) == set(MODULOS_BIPV)


def test_panel_del_proyecto_fuera_de_catalogo_se_puede_usar():
    panel = _panel_fuera_de_catalogo()
    opciones, aviso = opciones_panel_superficie(panel, "Excel-BIPV-300", MODULOS_BIPV)
    assert aviso is None
    assert opciones["Panel del proyecto (Excel-BIPV-300)"] == panel


@pytest.mark.parametrize("panel, nombre, fragmento", [
    (None, None, "Dimensionamiento"),
    ({}, "", "Dimensionamiento"),
    (_panel_fuera_de_catalogo(I_L_ref=None), "Excel-BIPV-300", "SDM"),
])
def test_sin_panel_o_sin_sdm_exige_elegir_del_catalogo(panel, nombre, fragmento):
    opciones, aviso = opciones_panel_superficie(panel, nombre, MODULOS_BIPV)
    assert fragmento in aviso
    assert not any(e.startswith("Panel del proyecto") for e in opciones)
    assert set(opciones) == set(MODULOS_BIPV)


def test_es_panel_del_proyecto():
    assert es_panel_del_proyecto("Panel del proyecto (X)", "X")
    assert es_panel_del_proyecto(_EN_CATALOGO, _EN_CATALOGO)  # mismo modelo desde el catálogo
    assert not es_panel_del_proyecto(_EN_CATALOGO, "Excel-BIPV-300")
    assert not es_panel_del_proyecto(None, "X")


# ── Strings por superficie ───────────────────────────────────────────────────
_PANEL = {**MODULOS_BIPV[_EN_CATALOGO], "area_m2": 2.0}


def test_strings_configurados_en_la_superficie():
    r = strings_superficie({"nombre": "Sur", "n_serie": 10, "n_paralelo": 3, "area_m2": 50}, 8, _PANEL)
    assert (r["n_serie"], r["n_paralelo"], r["origen"]) == (10, 3, ORIGEN_SUPERFICIE)
    assert r["aviso"] is None


def test_strings_desde_dimensionamiento_con_paralelo_por_area():
    r = strings_superficie({"nombre": "Sur", "area_m2": 60.0}, 10, _PANEL)
    assert (r["n_serie"], r["n_paralelo"], r["origen"]) == (10, 3, ORIGEN_DIMENSIONAMIENTO)
    assert "estimación" in r["aviso"]


def test_strings_serie_de_superficie_y_paralelo_estimado():
    r = strings_superficie({"nombre": "Sur", "n_serie": 12, "area_m2": 72.0}, 10, _PANEL)
    assert (r["n_serie"], r["n_paralelo"], r["origen"]) == (12, 3, ORIGEN_ESTIMADO_AREA)
    assert "estimación" in r["aviso"]


@pytest.mark.parametrize("sup", [
    {"nombre": "Sur", "n_serie": "ocho", "n_paralelo": 2, "area_m2": 48.0},
    {"nombre": "Sur", "n_serie": 0, "n_paralelo": 2, "area_m2": 48.0},
    {"nombre": "Sur", "n_serie": 8.5, "n_paralelo": 2, "area_m2": 48.0},
])
def test_valores_no_validos_usan_respaldo_con_aviso(sup):
    r = strings_superficie(sup, 10, _PANEL)
    assert r["origen"] != ORIGEN_SUPERFICIE and r["n_serie"] == 10 and r["aviso"]


def test_sin_ningun_n_serie_no_inventa_valores():
    with pytest.raises(ValueError, match="N serie"):
        strings_superficie({"nombre": "Sur", "area_m2": 48.0}, None, _PANEL)


def test_paralelo_por_area_exige_area_del_panel():
    # Spec 05/panel-por-superficie: sin area_m2 el área sale de largo × ancho;
    # sin ninguno de los dos no se puede estimar.
    sin_area = {k: v for k, v in _PANEL.items() if k not in ("area_m2", "largo_mm", "ancho_mm")}
    with pytest.raises(ValueError, match="área"):
        strings_superficie({"nombre": "Sur", "n_serie": 8, "area_m2": 48.0}, 8, sin_area)


def test_origenes_cerrados():
    assert set(ORIGENES_STRINGS) == {"superficie", "dimensionamiento", "estimado_por_area"}


# ── Página ───────────────────────────────────────────────────────────────────
def test_selectores_ya_no_fijan_un_panel_del_catalogo():
    src = _PAGINA.read_text(encoding="utf-8")
    arbol = ast.parse(src)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call) and ast.unparse(nodo.func).endswith("selectbox"):
            for kw in nodo.keywords:
                if kw.arg == "index":
                    assert "ASP-ST1-T40" not in ast.unparse(kw.value)
    # Spec 05/panel-por-superficie: el panel se elige en cada superficie; el
    # bypass y el MPPT ya no tienen un selector común de panel.
    assert "ms_bp_panel_sel" not in src and "ms_mppt_panel_sel" not in src
    assert 'key=f"spanel_{_uid}"' in src
    # Fase A2 (Spec 03/diseno-electrico-multisuperficie): el bypass usa los strings por grupo.
    assert src.count("strings_superficie(") >= 1 and src.count("strings_grupos_superficie(") >= 1
    assert 'key="ms_bp_nseries"' not in src and 'key="ms_mppt_nser"' not in src


# ── Formato único de strings (reportado en producción 24-sep-2026) ──────────
def test_formato_strings_explicito():
    from calculos.strings_superficie import formato_strings
    assert formato_strings(8, 17) == "8 serie × 17 paralelo"


def test_pagina_usa_un_solo_formato_de_strings():
    src = _PAGINA.read_text(encoding="utf-8")
    assert src.count("formato_strings(") >= 4  # dos leyendas, tabla del bypass, tabla del MPPT
    assert "×{r['n_serie']}s" not in src and "×{d['n_serie']}s" not in src
    assert "{_str_sp_bp['n_serie']} × {_str_sp_bp['n_paralelo']}" not in src
