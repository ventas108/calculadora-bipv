# -*- coding: utf-8 -*-
"""
Ancla real: los 4 inversores Sungrow SG5.0/7.0/8.0/10RT (4-sep-2026) deben
estar en el catálogo real, con ficha MECÁNICA completa (a diferencia del
import masivo CEC/Sandia de 2.343 modelos sin ella) y disponibles de
inmediato en el optimizador de Fase 4. Ver
datos/agregar_inversores_sungrow_ficha_real.py y
DIAGNOSTICO_CATALOGO_INVERSORES_CEC_NREL.md.

Fuente: ficha oficial real Sungrow (info-support.sungrowpower.com, dominio
propio del fabricante) -- elegido por presencia real confirmada en
Colombia (~1.5 GW ya instalados, distribuidor oficial Bemco).
"""
import pytest

from datos.catalogo_inversores_excel import cargar_catalogo_inversores
from optimization.variables import variable_inversor
from calculos.comparador_inversores import (
    filtrar_inversores_compatibles,
    inversores_excluidos_por_ficha_incompleta,
)
from datos.tecnologias_bipv import ASP_ST1_T40

_MODELOS = ["SG5.0RT", "SG7.0RT", "SG8.0RT", "SG10RT"]


def test_los_4_sungrow_estan_en_el_catalogo_real():
    cat = cargar_catalogo_inversores()
    faltan = [m for m in _MODELOS if m not in cat]
    assert not faltan, f"faltan en inversores_catalogo.xlsx: {faltan}"


def test_los_4_sungrow_tienen_ficha_completa_y_valores_reales():
    cat = cargar_catalogo_inversores()
    for m in _MODELOS:
        inv = cat[m]
        assert inv["datos_completos"] is True, f"{m}: debe quedar 'Datos completos'=Si"
        # Comunes a los 4, exactos de la ficha oficial (página 2, tabla
        # "Type designation").
        assert inv["Vdc_max"] == 1100.0
        assert inv["Vmppt_min"] == 160.0
        assert inv["Vmppt_max"] == 1000.0
        assert inv["n_trackers"] == 2.0
        assert inv["marca"] == "Sungrow"
        assert inv["es_hibrido"] is False
        # Valor conservador elegido a propósito (ver docstring del script
        # de import): el MPPT real es asimétrico (2 strings/25A en MPPT1,
        # 1 string/12.5A en MPPT2) -- se usa el más restrictivo para no
        # sobreestimar la capacidad real en el chequeo automático.
        assert inv["n_strings_tracker"] == 1.0
        assert inv["I_max_tracker"] == pytest.approx(12.5)
        assert inv["Isc_max_tracker"] == pytest.approx(18.0)

    # Potencias reales, distintas por modelo (verificadas contra la ficha).
    assert cat["SG5.0RT"]["P_ac_nom_W"] == 5000.0
    assert cat["SG7.0RT"]["P_ac_nom_W"] == 6999.0
    assert cat["SG8.0RT"]["P_ac_nom_W"] == 8000.0
    assert cat["SG10RT"]["P_ac_nom_W"] == 10000.0
    assert cat["SG5.0RT"]["P_dc_max_W"] == 7500.0
    assert cat["SG10RT"]["P_dc_max_W"] == 15000.0


def test_los_4_sungrow_quedan_disponibles_en_el_optimizador_de_fase4():
    var = variable_inversor()
    faltan = [m for m in _MODELOS if m not in var.opciones]
    assert not faltan, f"variable_inversor() excluye modelos con ficha completa: {faltan}"

    excluidos = inversores_excluidos_por_ficha_incompleta()
    for m in _MODELOS:
        assert m not in excluidos


def test_sg5_0rt_evalua_compatible_contra_un_string_real():
    cat = cargar_catalogo_inversores()
    inv = cat["SG5.0RT"]
    df = filtrar_inversores_compatibles(ASP_ST1_T40, {"SG5.0RT": inv}, N_serie=8)
    fila = df.iloc[0]
    assert fila["compatible"] is True or bool(fila["compatible"]) is True, fila.get("motivo")
    assert fila["strings_max"] == 2  # N_mppt=2 x n_strings_tracker=1
