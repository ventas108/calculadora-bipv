# -*- coding: utf-8 -*-
"""Potencia AC nominal de los inversores del catálogo (26-sep-2026).

Encontrado al corregir el Growatt MID15KTL3-X: el catálogo estimaba la
potencia AC como 96 % de la «Potencia FV máx. recomendada» (22.500 W →
21.600 W, cuando la ficha dice 15.000 W) y la relación DC/AC salía 0,79 🟡
en vez de 1,13 🟢. Regla: la potencia AC solo viene de la ficha; si falta,
no se inventa y la app lo dice.
"""
import os

import pandas as pd
import pytest

from calculos.potencia_ac_inversor import (
    MENSAJE_SIN_POTENCIA_AC,
    error_potencia_ac,
    inversores_sin_potencia_ac,
    potencia_ac_requerida,
    potencia_ac_w,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_la_potencia_ac_viene_solo_de_la_ficha():
    assert potencia_ac_w(15.0) == 15000.0
    assert potencia_ac_w(None) is None
    assert potencia_ac_w(0) is None
    assert potencia_ac_w(float("nan")) is None


@pytest.mark.parametrize("arq", ["Inversor de red monofásico", "Inversor de red trifásico",
                                 "Híbrido / Off-grid", "Otro"])
def test_obligatoria_salvo_cargador_off_grid(arq):
    assert potencia_ac_requerida(arq)
    assert "Potencia AC nominal" in error_potencia_ac(arq, 0)
    assert error_potencia_ac(arq, 15.0) is None


def test_cargador_off_grid_puro_no_la_exige():
    assert not potencia_ac_requerida("Cargador off-grid puro")
    assert error_potencia_ac("Cargador off-grid puro", 0) is None


def test_lista_de_inversores_sin_potencia_ac():
    cat = {"A": {"nombre": "A", "P_ac_nom_W": 15000.0}, "B": {"nombre": "B", "P_ac_nom_W": None},
           "C": {"nombre": "C"}}
    assert inversores_sin_potencia_ac(cat) == ["B", "C"]


def test_mensaje_explica_donde_completarla():
    assert "Catálogo Inversores PDF" in MENSAJE_SIN_POTENCIA_AC
    assert "P AC nominal (kW)" in MENSAJE_SIN_POTENCIA_AC


def test_cargador_del_catalogo_no_estima_la_potencia_ac(tmp_path, monkeypatch):
    import datos.catalogo_inversores_excel as cat_mod
    ruta = tmp_path / "inv.xlsx"
    filas = pd.DataFrame([
        {"Modelo": "CON-FICHA", "Potencia AC nominal (kW)": 15.0, "Potencia FV Max Recomendada (W)": 22500},
        {"Modelo": "SIN-FICHA", "Potencia AC nominal (kW)": None, "Potencia FV Max Recomendada (W)": 22500},
    ])
    with pd.ExcelWriter(ruta) as w:
        filas.to_excel(w, sheet_name=cat_mod._SHEET, startrow=2, index=False)
    monkeypatch.setattr(cat_mod, "_EXCEL", str(ruta))
    cat_mod.cargar_catalogo_inversores.clear()
    cat = cat_mod.cargar_catalogo_inversores()
    cat_mod.cargar_catalogo_inversores.clear()
    assert cat["CON-FICHA"]["P_ac_nom_W"] == 15000.0
    assert cat["SIN-FICHA"]["P_ac_nom_W"] is None      # antes: 21.600 W inventados
    assert cat["SIN-FICHA"]["P_dc_max_W"] == 22500


def test_extractor_lee_la_potencia_ac_aunque_haya_p_fv_max():
    from calculos.pdf_inversor_extractor import _extraer_potencia_ac_kw
    texto = ("Max. recommended PV power 22500W\nRated AC output power 15000W\n"
             "Max. AC apparent power 16600VA")
    assert _extraer_potencia_ac_kw(texto) == 15.0
    assert _extraer_potencia_ac_kw("Potencia nominal CA 5 kW") == 5.0
    assert _extraer_potencia_ac_kw("sin datos") is None


def _pagina(nombre):
    with open(os.path.join(_ROOT, "pages", nombre), encoding="utf-8") as f:
        return f.read()


def test_formulario_pide_y_guarda_la_potencia_ac():
    src = _pagina("15_🔌_Catálogo_Inversores_PDF.py")
    assert '"Potencia AC nominal (kW)"' in src
    assert "error_potencia_ac(" in src
    # también editable en la tabla para completar los inversores antiguos
    assert "tabla_edicion(" in src and "inversores_sin_potencia_ac(" in src
    from calculos.edicion_catalogo_inversores import COLUMNAS_EDICION
    assert COLUMNAS_EDICION["P_ac_nom_kW"] == ("P AC nominal (kW)", "Potencia AC nominal (kW)")


def test_vista_3d_explica_donde_completar_la_potencia_ac():
    src = open(os.path.join(_ROOT, "calculos", "diseno_electrico_multisup.py"), encoding="utf-8").read()
    assert "MENSAJE_SIN_POTENCIA_AC" in src


_FICHA_MULTIMODELO = """Datasheet            MID 15KTL3-X   MID 17KTL3-X   MID 20KTL3-X
Max. recommended PV power 22500W  25500W  30000W
Rated AC output power     15000W         17000W         20000W
Max. AC apparent power    16600VA        18800VA        22000VA
"""


def test_extractor_lee_la_potencia_ac_de_cada_modelo():
    from calculos.pdf_inversor_extractor import _extract_multimodel_values
    r = _extract_multimodel_values(_FICHA_MULTIMODELO)
    assert [v["P_ac_nom_kW"] for v in r["por_modelo"].values()] == [15.0, 17.0, 20.0]


def test_sin_un_valor_por_modelo_no_se_adivina():
    from calculos.pdf_inversor_extractor import _extract_multimodel_values
    r = _extract_multimodel_values(_FICHA_MULTIMODELO.replace("17000W         20000W", ""))
    assert all(v["P_ac_nom_kW"] is None for v in r["por_modelo"].values())
