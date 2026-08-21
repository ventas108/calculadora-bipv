# -*- coding: utf-8 -*-
"""Validación de calculos/compatibilidad_bateria.py (tarea #25) y de la
lectura de voltaje_min_V/voltaje_max_V en datos/catalogo_baterias_excel.py.

Contexto (2026-08-21): check_compatibilidad() solo comparaba el voltaje
NOMINAL de la batería contra la ventana que acepta el inversor. El Excel real
(datos/inversores_catalogo.xlsx, hoja Catalogo_Baterias) SÍ trae el rango
completo de operación (columnas "Voltaje Min (V)"/"Voltaje Max (V)", que
varía con el estado de carga) para los 26 modelos, pero el loader no las
reconocía -- una batería cuyo nominal cayera dentro del rango del inversor
pero cuyo mínimo a descarga profunda (o máximo a carga plena) cayera fuera se
habría marcado "ok" sin serlo. Ver scripts/test_compatibilidad_bateria.py
para el banco de regresión manual más amplio de este mismo módulo (no forma
parte de esta suite pytest -- es un script standalone, ver su docstring).
"""
import math
import sys
import types

from calculos.compatibilidad_bateria import check_compatibilidad


# ── Rango completo de operación vs. chequeo solo-nominal ────────────────────

def test_nominal_dentro_pero_minimo_real_fuera_de_rango_da_error():
    estado, msg = check_compatibilidad(
        {"voltaje_V": 614.4, "voltaje_min_V": 480, "voltaje_max_V": 700},
        {"es_hibrido": True, "bat_voltaje_min": 500, "bat_voltaje_max": 800},
        "Inversor Genérico X",
    )
    assert estado == "error"
    assert "mínimo" in msg.lower()
    assert "480" in msg and "500" in msg


def test_nominal_dentro_pero_maximo_real_fuera_de_rango_da_error():
    estado, msg = check_compatibilidad(
        {"voltaje_V": 614.4, "voltaje_min_V": 550, "voltaje_max_V": 820},
        {"es_hibrido": True, "bat_voltaje_min": 500, "bat_voltaje_max": 800},
        "Inversor Genérico X",
    )
    assert estado == "error"
    assert "máximo" in msg.lower()
    assert "820" in msg and "800" in msg


def test_rango_completo_dentro_de_ventana_da_ok_y_lo_dice_explicito():
    estado, msg = check_compatibilidad(
        {"voltaje_V": 614.4, "voltaje_min_V": 537.6, "voltaje_max_V": 691.2},
        {"es_hibrido": True, "bat_voltaje_min": 500, "bat_voltaje_max": 800},
        "Inversor Genérico X",
    )
    assert estado == "ok"
    # El mensaje debe dejar claro que se verificó el rango completo, no solo
    # el nominal -- transparencia sobre el rigor real del chequeo.
    assert "rango completo" in msg.lower()


def test_sin_voltaje_min_max_cae_al_chequeo_nominal_sin_romper_casos_previos():
    # Comportamiento preexistente (banco de regresión de scripts/) intacto
    # cuando el catálogo no trae el rango propio de la batería.
    estado, msg = check_compatibilidad(
        {"voltaje_V": 51.2},
        {"es_hibrido": True, "bat_voltaje_min": 40, "bat_voltaje_max": 60},
        "DEYE SUN-7.6K-SG01LP1",
    )
    assert estado == "ok"
    assert "solo el punto nominal" in msg or "no trae el rango" in msg


def test_rango_real_solo_parcialmente_provisto_no_activa_chequeo_riguroso():
    # Si solo viene voltaje_min_V (sin voltaje_max_V), no debe intentar un
    # chequeo a medias -- cae al comportamiento nominal preexistente.
    estado, msg = check_compatibilidad(
        {"voltaje_V": 614.4, "voltaje_min_V": 480},
        {"es_hibrido": True, "bat_voltaje_min": 500, "bat_voltaje_max": 800},
        "Inversor Genérico X",
    )
    assert estado == "ok"


# ── datos/catalogo_baterias_excel.py: mapeo de Voltaje Min/Max ──────────────
# El módulo real importa streamlit a nivel de módulo (para @st.cache_data),
# que no está instalado en este entorno de pruebas -- se inyecta un stub
# mínimo en sys.modules antes de importar, igual que
# tests/test_catalogo_inversores_real.py hace para su propio módulo Excel.

def _cargar_modulo_catalogo_baterias():
    if "streamlit" not in sys.modules:
        stub = types.ModuleType("streamlit")

        def _cache_data(*a, **k):
            def deco(f):
                f.clear = lambda: None
                return f
            return deco

        stub.cache_data = _cache_data
        sys.modules["streamlit"] = stub

    import datos.catalogo_baterias_excel as mod
    return mod


def test_col_map_reconoce_voltaje_min_y_max():
    mod = _cargar_modulo_catalogo_baterias()
    assert mod._COL_MAP_NORM.get(mod._clave_col("Voltaje Min (V)")) == "voltaje_min_V"
    assert mod._COL_MAP_NORM.get(mod._clave_col("Voltaje Max (V)")) == "voltaje_max_V"


def test_voltaje_min_max_son_claves_numericas():
    mod = _cargar_modulo_catalogo_baterias()
    assert "voltaje_min_V" in mod._NUM_KEYS
    assert "voltaje_max_V" in mod._NUM_KEYS


def test_catalogo_real_trae_voltaje_min_max_para_los_26_modelos():
    # Prueba end-to-end contra el Excel real del repo (no un mock) -- si el
    # dato de origen alguna vez deja de tener estas columnas, este test debe
    # notarlo en vez de que compatibilidad_bateria.py degrade en silencio al
    # chequeo solo-nominal.
    import os
    mod = _cargar_modulo_catalogo_baterias()
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mod._EXCEL = os.path.join(_root, "datos", "inversores_catalogo.xlsx")

    catalogo = mod.cargar_catalogo_baterias(_mtime=mod.excel_mtime())
    assert len(catalogo) == 26
    for nombre, bat in catalogo.items():
        assert bat.get("voltaje_min_V") is not None, f"{nombre} sin voltaje_min_V"
        assert bat.get("voltaje_max_V") is not None, f"{nombre} sin voltaje_max_V"
        assert bat["voltaje_min_V"] < bat["voltaje_V"] < bat["voltaje_max_V"], (
            f"{nombre}: el nominal debería caer entre el mínimo y el máximo reales"
        )
