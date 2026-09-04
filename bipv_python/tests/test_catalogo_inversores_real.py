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


# ── variable_inversor(): filtro de ficha completa (4-sep-2026) ─────────────
# Mismo patrón que variable_panel() (Pmax_stc/area_m2) -- agregado al
# investigar cómo importar en bloque el catálogo Sandia/CEC de NREL (2.343
# inversores reales, datos/agregar_inversores_cec_nrel.py): ese dataset no
# trae N_mppt ni corriente por tracker (son datos mecánicos, el modelo
# eléctrico Sandia no los necesita) -- sin este filtro, un inversor así
# entraría al optimizador de Fase 4 y calculos.dimensionamiento le asumiría
# N_mppt=1 por defecto (líneas 548/788), pudiendo recomendar un arreglo de
# strings basado en un dato inventado, no en la ficha real.

_CATALOGO_MIXTO_COMPLETITUD = {
    "Completo-A": {
        "nombre": "Completo-A", "Vdc_max": 1000.0, "Vmppt_max": 800.0,
        "Isc_max_tracker": 20.0, "N_mppt": 2.0,
    },
    "Completo-B": {
        "nombre": "Completo-B", "Vdc_max": 1100.0, "Vmppt_max": 900.0,
        "I_max_tracker": 18.0, "n_trackers": 4.0,
    },
    "SinTrackers": {
        "nombre": "SinTrackers", "Vdc_max": 1000.0, "Vmppt_max": 800.0,
        "Isc_max_tracker": 20.0,
        # sin N_mppt ni n_trackers -- exactamente el caso del import CEC/Sandia
    },
    "SinCorriente": {
        "nombre": "SinCorriente", "Vdc_max": 1000.0, "Vmppt_max": 800.0,
        "N_mppt": 2.0,
        # sin Isc_max_tracker ni I_max_tracker
    },
    "SinVmpptMax": {
        "nombre": "SinVmpptMax", "Vdc_max": 1000.0,
        "Isc_max_tracker": 20.0, "N_mppt": 2.0,
    },
}


def test_variable_inversor_excluye_fichas_sin_datos_mecanicos_completos(monkeypatch):
    monkeypatch.setitem(sys.modules, "datos.catalogo_inversores_excel", _modulo_excel_falso(_CATALOGO_MIXTO_COMPLETITUD))
    var = opt_vars.variable_inversor()
    assert set(var.opciones) == {"Completo-A", "Completo-B"}


def test_variable_inversor_con_catalogo_explicito_no_filtra():
    # Mismo contrato que variable_panel(): pasar un catálogo explícito
    # desactiva el filtro -- necesario para que
    # inversores_excluidos_por_ficha_incompleta() pueda ver las entradas
    # incompletas en vez de que ya vengan quitadas.
    var = opt_vars.variable_inversor(_CATALOGO_MIXTO_COMPLETITUD)
    assert set(var.opciones) == set(_CATALOGO_MIXTO_COMPLETITUD.keys())


def test_inversores_excluidos_por_ficha_incompleta_detecta_los_3_incompletos():
    from calculos.comparador_inversores import inversores_excluidos_por_ficha_incompleta
    excluidos = inversores_excluidos_por_ficha_incompleta(_CATALOGO_MIXTO_COMPLETITUD)
    assert set(excluidos) == {"SinTrackers", "SinCorriente", "SinVmpptMax"}


def test_inversores_excluidos_por_ficha_incompleta_refleja_el_catalogo_real():
    # Actualizado 4-sep-2026, mismo día, sesión posterior: el import masivo
    # CEC/Sandia (2.343 inversores sin datos mecánicos, ver comentario que
    # tenía este test antes) resultó impráctico en producción -- ficha sin
    # datos mecánicos + catálogo 23x más grande volvía lento e inútil el
    # selector de 📐 Dimensionamiento (2.455 opciones, la inmensa mayoría no
    # evaluables). Se limpió el catálogo real (datos/inversores_catalogo.xlsx)
    # a las 111 filas con "Datos completos"="Si" -- ver DIAGNOSTICO_TZ_TMY_
    # SCRIPTS_URABA.md / progreso.md de esa sesión para el detalle completo.
    #
    # De esos 111, 3 siguen sin pasar ESTE filtro más estricto (Vdc_max +
    # Vmppt_max + Isc/I_max_tracker + N_mppt/n_trackers): POWEST-1KVA-12V,
    # POWEST-3KVA-24V, LSP 100K -- estaban marcados "Si" en el Excel pero de
    # todas formas les falta un campo de este subconjunto. Woodward IDS
    # SOLO 500 (el 4to que aparecía en la lista anterior) ya no está en el
    # catálogo: tenía "Datos completos"="No" y se eliminó en la misma
    # limpieza -- recuperable desde el historial de git si se decide
    # completar su ficha y reincorporarlo.
    from calculos.comparador_inversores import inversores_excluidos_por_ficha_incompleta
    excluidos = inversores_excluidos_por_ficha_incompleta()
    assert set(excluidos) == {"POWEST-1KVA-12V", "POWEST-3KVA-24V", "LSP 100K"}


# ── catalogo_inversores_excel: desambiguación de clave por colisión real ───
# Bug real encontrado 4-sep-2026 durante el import CEC: 19 modelos del
# dataset comparten el mismo string "Modelo" bajo 2 fabricantes distintos
# (rebadge/OEM real, ej. "MIN 10000TL-XH-US {240V}") -- el diccionario se
# armaba con "Modelo" a secas como clave, así que un fabricante pisaba al
# otro en silencio (2.343 filas escritas al Excel, solo 2.324 sobrevivían
# en el dict). Corregido: desambiguación con "Modelo [Marca]" SOLO cuando
# hay colisión real -- este test usa el Excel real de fixtures, no un mock,
# porque el bug vivía en la lectura del propio archivo (pd.read_excel +
# construcción del dict), no en una función aislada mockeable.

def test_cargar_catalogo_inversores_desambigua_modelos_duplicados_entre_marcas():
    import openpyxl
    import tempfile
    import os
    from datos.catalogo_inversores_excel import cargar_catalogo_inversores as _cargar_real

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Catalogo_Inversores"
    ws.append(["placeholder fila 1"])
    ws.append(["placeholder fila 2"])
    ws.append([
        "Datos completos (Si/No)", "Modelo", "Costo Inversor ", "Archivo origen",
        "Tension DC Maxima (V)", "Tension Arranque (V)", "Rango MPPT Min (V)",
        "Rango MPPT Max (V)", "Tension Minima MPPT Activo (V)", "N Trackers",
        "N Strings/Tracker", "Corriente Maxima Tracker (A)",
        "Corriente Cortocircuito Max Tracker (A)", "Potencia FV Max Recomendada (W)",
        "Potencia AC nominal (kW)", "Marca",
    ])
    # Mismo "Modelo" bajo 2 marcas distintas -- el caso real encontrado.
    ws.append(["Si", "MISMO-MODELO", 100, "test", 1000, 200, 100, 900, 300, 2, 1, 20, 25, 5000, 5.0, "MarcaA"])
    ws.append(["Si", "MISMO-MODELO", 200, "test", 1100, 250, 150, 950, 350, 4, 1, 18, 22, 6000, 6.0, "MarcaB"])
    # Un tercer modelo sin colisión -- su clave NO debe cambiar.
    ws.append(["Si", "UNICO", 300, "test", 900, 180, 90, 800, 250, 1, 1, 15, 18, 4000, 4.0, "MarcaC"])

    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "inversores_test.xlsx")
        wb.save(ruta)
        import datos.catalogo_inversores_excel as mod
        _orig_excel = mod._EXCEL
        mod._EXCEL = ruta
        try:
            _cargar_real.clear()
            cat = _cargar_real()
        finally:
            mod._EXCEL = _orig_excel
            _cargar_real.clear()

    assert "MISMO-MODELO [MarcaA]" in cat
    assert "MISMO-MODELO [MarcaB]" in cat
    assert cat["MISMO-MODELO [MarcaA]"]["costo_usd"] == 100
    assert cat["MISMO-MODELO [MarcaB]"]["costo_usd"] == 200
    # El modelo sin colisión conserva su clave simple, sin sufijo de marca.
    assert "UNICO" in cat
    assert len(cat) == 3
