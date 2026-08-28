# -*- coding: utf-8 -*-
"""Validación de optimization.variables._catalogo_inversores_real() y su uso
en variable_inversor() / scenario_generator._resolver_categoricas_de_catalogo().

Contexto (2026-08-21): hasta ahora variable_inversor() usaba por defecto solo
datos.catalogo_inversores.INVERSORES (7 modelos hardcodeados), aunque el
catálogo real editable desde 🔌 Catálogo Inversores (datos/inversores_catalogo.xlsx,
vía datos.catalogo_inversores_excel.cargar_catalogo_inversores()) tiene 105
modelos reales -- mismo patrón de "catálogos desconectados" que ya se corrigió
para paneles. Diferencia real entre las dos fuentes que hay que manejar sin
inventar datos: el Excel no trae "eficiencia_max" (el datasheet fuente no lo
reporta) ni un campo "modelo" propio (solo "nombre").

datos.catalogo_inversores_excel importa streamlit a nivel de módulo (para
@st.cache_data) -- estos tests inyectan un módulo falso en sys.modules antes
de que _catalogo_inversores_real() haga su import perezoso, en vez de
importar el módulo real. Esto es deliberado incluso cuando streamlit SÍ está
instalado (como en este entorno, verificado 28-ago-2026): permite probar
catálogos controlados (con/sin eficiencia_max, vacío, etc.) sin depender del
contenido real y cambiante de inversores_catalogo.xlsx (105 modelos, ninguno
con eficiencia_max real -- el datasheet fuente no la reporta).

Nota histórica: hasta el 27-ago-2026, `_EXCEL` en catalogo_inversores_excel.py
estaba hardcodeado solo a la ruta del servidor (sin el mismo fallback local
que catalogo_paneles_excel.py sí tenía) -- en cualquier entorno de desarrollo,
cargar_catalogo_inversores() fallaba con FileNotFoundError y
_catalogo_inversores_real() caía en silencio al Python (INVERSORES, 7
modelos). Corregido 28-ago-2026: algunos tests de este archivo dependían sin
saberlo de ese fallback "por accidente de entorno" en vez de por mock
explícito -- ver test_resolver_sincroniza_eta_inversor_cuando_si_hay_dato_real.
"""
import sys
import types

import pytest

import optimization.variables as opt_vars
from datos.catalogo_inversores import INVERSORES
from optimization.scenario_generator import _resolver_categoricas_de_catalogo


def _modulo_excel_falso(catalogo: dict | None = None, lanza: bool = False):
    """Construye un módulo falso con la misma API pública que
    datos.catalogo_inversores_excel, sin importar streamlit de verdad."""
    mod = types.ModuleType("datos.catalogo_inversores_excel")
    if lanza:
        def _cargar():
            raise RuntimeError("Excel no disponible (simulado)")
    else:
        def _cargar():
            return catalogo if catalogo is not None else {}
    mod.cargar_catalogo_inversores = _cargar
    return mod


# Forma real que devuelve cargar_catalogo_inversores() (ver
# datos/catalogo_inversores_excel.py): sin "modelo" propio, sin
# "eficiencia_max" -- el datasheet fuente de los 105 modelos no la reporta.
_CATALOGO_EXCEL_FALSO = {
    "MID 15KTL3-X": {
        "nombre": "MID 15KTL3-X", "Vdc_max": 1100.0, "Vmppt_min": 200.0,
        "Vmppt_max": 1000.0, "Vmppt_activo_min": 580.0, "N_mppt": 2.0,
        "I_max_tracker": 27.0, "Isc_max_tracker": 33.8, "P_dc_max_W": 22500.0,
        "P_ac_nom_W": 21600.0,
    },
    "SOLIS-60K": {
        "nombre": "SOLIS-60K", "Vdc_max": 1100.0, "Vmppt_min": 200.0,
        "Vmppt_max": 1000.0, "Vmppt_activo_min": 500.0, "N_mppt": 4.0,
        "I_max_tracker": 26.0, "Isc_max_tracker": 32.0, "P_dc_max_W": 66000.0,
        "P_ac_nom_W": 60000.0,
    },
}


def test_prefiere_excel_cuando_esta_disponible(monkeypatch):
    monkeypatch.setitem(sys.modules, "datos.catalogo_inversores_excel", _modulo_excel_falso(_CATALOGO_EXCEL_FALSO))
    cat = opt_vars._catalogo_inversores_real()
    assert set(cat.keys()) == set(_CATALOGO_EXCEL_FALSO.keys())


def test_agrega_alias_modelo_cuando_falta():
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setitem(sys.modules, "datos.catalogo_inversores_excel", _modulo_excel_falso(_CATALOGO_EXCEL_FALSO))
        cat = opt_vars._catalogo_inversores_real()
        assert cat["MID 15KTL3-X"]["modelo"] == "MID 15KTL3-X"
        assert cat["SOLIS-60K"]["modelo"] == "SOLIS-60K"
    finally:
        monkeypatch.undo()


def test_no_pisa_modelo_si_ya_existe(monkeypatch):
    catalogo = {"X": {"nombre": "X", "modelo": "X-real-de-placa"}}
    monkeypatch.setitem(sys.modules, "datos.catalogo_inversores_excel", _modulo_excel_falso(catalogo))
    cat = opt_vars._catalogo_inversores_real()
    assert cat["X"]["modelo"] == "X-real-de-placa"


def test_cae_a_python_si_excel_vacio(monkeypatch):
    monkeypatch.setitem(sys.modules, "datos.catalogo_inversores_excel", _modulo_excel_falso({}))
    cat = opt_vars._catalogo_inversores_real()
    assert cat == INVERSORES


def test_cae_a_python_si_excel_lanza_excepcion(monkeypatch):
    monkeypatch.setitem(sys.modules, "datos.catalogo_inversores_excel", _modulo_excel_falso(lanza=True))
    cat = opt_vars._catalogo_inversores_real()
    assert cat == INVERSORES


def test_cae_a_python_si_el_modulo_excel_no_se_puede_importar():
    # Simula streamlit ausente bloqueando el import a propósito (streamlit SÍ
    # está instalado en este entorno, verificado 28-ago-2026) -- confirma que
    # el fallback no rompe nada en un entorno donde streamlit de verdad falte
    # (p.ej. un venv más minimalista), sin depender de que este entorno
    # particular lo tenga o no lo tenga instalado.
    import builtins
    real_import = builtins.__import__

    def _import_bloqueando_streamlit(name, *args, **kwargs):
        if name == "streamlit" or name.startswith("streamlit."):
            raise ModuleNotFoundError("streamlit bloqueado en este test")
        return real_import(name, *args, **kwargs)

    mp = pytest.MonkeyPatch()
    try:
        sys.modules.pop("datos.catalogo_inversores_excel", None)
        mp.setattr(builtins, "__import__", _import_bloqueando_streamlit)
        cat = opt_vars._catalogo_inversores_real()
        assert cat == INVERSORES
    finally:
        mp.undo()


def test_variable_inversor_usa_el_catalogo_excel_cuando_esta_disponible(monkeypatch):
    monkeypatch.setitem(sys.modules, "datos.catalogo_inversores_excel", _modulo_excel_falso(_CATALOGO_EXCEL_FALSO))
    var = opt_vars.variable_inversor()
    assert set(var.opciones) == set(_CATALOGO_EXCEL_FALSO.keys())


def test_variable_inversor_respeta_catalogo_explicito_sin_tocar_el_real():
    # Un catalogo explícito (p.ej. un subconjunto de pruebas) sigue teniendo
    # prioridad -- _catalogo_inversores_real() solo se usa cuando catalogo=None.
    catalogo_explicito = {"SoloUno": {"modelo": "SoloUno"}}
    var = opt_vars.variable_inversor(catalogo_explicito)
    assert var.opciones == ("SoloUno",)


# ── scenario_generator._resolver_categoricas_de_catalogo() ─────────────────

def test_resolver_no_sincroniza_eta_inversor_sin_dato_real_de_eficiencia(monkeypatch):
    # Hallazgo real: el catálogo Excel no trae eficiencia_max -- sincronizar
    # eta_inversor con un dato que no existe reventaría con KeyError (antes
    # de este fix) o, peor, se rellenaría con un valor inventado. El
    # candidato debe conservar el eta_inversor que ya traía config_base.
    monkeypatch.setitem(sys.modules, "datos.catalogo_inversores_excel", _modulo_excel_falso(_CATALOGO_EXCEL_FALSO))
    resuelto = _resolver_categoricas_de_catalogo({"inversor": "SOLIS-60K"})
    assert "eta_inversor" not in resuelto
    assert resuelto["inversor"]["modelo"] == "SOLIS-60K"


def test_resolver_sincroniza_eta_inversor_cuando_si_hay_dato_real(monkeypatch):
    # Antes (hasta 27-ago-2026) este test no necesitaba mock: la ruta del
    # Excel estaba hardcodeada solo al servidor (sin el fallback local que sí
    # tenía catalogo_paneles_excel.py), así que en este entorno de pruebas
    # cargar_catalogo_inversores() siempre fallaba y _catalogo_inversores_real()
    # caía en silencio al Python (INVERSORES, con eficiencia_max) -- "camino
    # normal" por accidente de entorno, no por diseño. Corregido el fallback
    # de ruta el 28-ago-2026 (mismo patrón que ya tenía el de paneles): ahora
    # el Excel real (105 modelos) SÍ carga aquí, y NINGUNO de esos 105 trae
    # eficiencia_max (el datasheet fuente no la reporta). El caso "sí hay dato
    # real" solo puede probarse con un catálogo controlado -- mismo patrón que
    # el resto de los tests de este archivo, no un accidente de entorno.
    catalogo_con_eficiencia = {
        "MID 15KTL3-X": {"nombre": "MID 15KTL3-X", "modelo": "MID15KTL3-X", "eficiencia_max": 0.985},
    }
    monkeypatch.setitem(sys.modules, "datos.catalogo_inversores_excel", _modulo_excel_falso(catalogo_con_eficiencia))
    resuelto = _resolver_categoricas_de_catalogo({"inversor": "MID 15KTL3-X"})
    assert resuelto["eta_inversor"] == pytest.approx(0.985)
    assert resuelto["inversor"]["modelo"] == "MID15KTL3-X"


def test_resolver_usa_el_mismo_catalogo_que_ofrecio_las_opciones(monkeypatch):
    # Regresión directa del bug que este fix evita: si variable_inversor()
    # sortea una clave del catálogo Excel (105) pero el resolver buscara en
    # el Python (7), reventaría con KeyError para el 94% de las claves.
    monkeypatch.setitem(sys.modules, "datos.catalogo_inversores_excel", _modulo_excel_falso(_CATALOGO_EXCEL_FALSO))
    var = opt_vars.variable_inversor()
    for clave in var.opciones:
        resuelto = _resolver_categoricas_de_catalogo({"inversor": clave})
        assert resuelto["inversor"]["nombre"] == clave
