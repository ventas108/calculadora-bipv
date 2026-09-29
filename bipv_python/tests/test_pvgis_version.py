# -*- coding: utf-8 -*-
"""Spec ``02-recurso-solar/pvgis-5-3`` (29-sep-2026): elegir PVGIS 5.2 o 5.3.

PVsyst 8 descarga PVGIS 5.3; la app descargaba siempre 5.2. En Apartadó
(7.8830 / −76.6259) la app dio GHI 1,606 kWh/m² y PVsyst 1,683 (−4.6 %): la
diferencia es la base de datos, no el cálculo. Los proyectos guardados se
calcularon con 5.2 y deben seguir dando lo mismo.
"""
import ast
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculos import solar  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAG2 = os.path.join(_ROOT, "pages", "2_☀️_Recurso_Solar.py")
_PAG1 = os.path.join(_ROOT, "pages", "1_🏠_Proyecto.py")


def _json_pvgis(con_meta=True):
    horas = [
        {"time(UTC)": f"2012010{d}:1200", "G(h)": 800.0, "Gb(n)": 600.0,
         "Gd(h)": 200.0, "T2m": 27.0, "WS10m": 1.5, "SP": 101000.0, "RH": 80.0}
        for d in (1, 2, 3)
    ]
    data = {"outputs": {"tmy_hourly": horas}}
    if con_meta:
        data["outputs"]["months_selected"] = [
            {"month": m, "year": 2005 + m} for m in range(1, 13)
        ]
        data["inputs"] = {"meteo_data": {
            "radiation_db": "PVGIS-SARAH3", "meteo_db": "ERA5",
            "year_min": 2005, "year_max": 2023,
        }}
    return data


class _Resp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


@pytest.fixture
def pvgis_falso(monkeypatch):
    llamadas = []

    def _get(url, params=None, timeout=None):
        llamadas.append(url)
        return _Resp(_json_pvgis())

    monkeypatch.setattr(solar.requests, "get", _get)
    return llamadas


# ── Criterio 1: URL según la versión ─────────────────────────────────────────
def test_version_53_llama_al_servicio_53(pvgis_falso):
    solar.obtener_tmy_pvgis(7.883, -76.6259, version="5.3")
    assert pvgis_falso == ["https://re.jrc.ec.europa.eu/api/v5_3/tmy"]


def test_sin_version_sigue_llamando_a_52(pvgis_falso):
    solar.obtener_tmy_pvgis(7.883, -76.6259)
    assert pvgis_falso == ["https://re.jrc.ec.europa.eu/api/v5_2/tmy"]


def test_version_desconocida_es_error():
    with pytest.raises(ValueError):
        solar.url_tmy_pvgis("5.1")


# ── Criterio 2: metadatos en df.attrs ────────────────────────────────────────
def test_metadatos_quedan_en_attrs(pvgis_falso):
    df = solar.obtener_tmy_pvgis(7.883, -76.6259, version="5.3")
    meta = df.attrs["pvgis"]
    assert meta["version"] == "5.3"
    assert meta["radiation_db"] == "PVGIS-SARAH3"
    assert (meta["year_min"], meta["year_max"]) == (2005, 2023)
    assert meta["meses"][0] == (1, 2006) and len(meta["meses"]) == 12
    assert list(df.columns)[:3] == ["G_h", "Gb_n", "Gd_h"]


def test_metadatos_ausentes_no_rompen():
    meta = solar.metadatos_pvgis(_json_pvgis(con_meta=False), "5.2")
    assert meta["version"] == "5.2"
    assert meta["radiation_db"] is None and meta["meses"] == []


def test_texto_meses_tmy():
    meta = solar.metadatos_pvgis(_json_pvgis(), "5.3")
    texto = solar.texto_meses_tmy(meta)
    assert texto.startswith("Ene 2006 · Feb 2007")
    assert texto.endswith("Dic 2017")
    assert solar.texto_meses_tmy({"meses": []}) == ""


# ── Criterio 3: versión por defecto y de proyectos guardados ─────────────────
def test_proyecto_nuevo_usa_53():
    assert solar.version_pvgis_de_estado({}) == "5.3"
    assert solar.version_pvgis_de_estado({"pvgis_version": "5.2"}) == "5.2"
    assert solar.version_pvgis_de_estado({"pvgis_version": "9.9"}) == "5.3"


def test_proyecto_guardado_sin_version_usa_52():
    assert solar.version_pvgis_de_proyecto_guardado({}) == "5.2"
    assert solar.version_pvgis_de_proyecto_guardado({"pvgis_version": "5.3"}) == "5.3"
    assert solar.version_pvgis_de_proyecto_guardado({"pvgis_version": "x"}) == "5.2"


def test_cargar_proyecto_fija_la_version():
    with open(os.path.join(_ROOT, "calculos", "proyectos_manager.py"), encoding="utf-8") as f:
        src = f.read()
    cuerpo = src[src.index("def cargar_proyecto"):src.index("def eliminar_proyecto")]
    assert "version_pvgis_de_proyecto_guardado(estado)" in cuerpo


# ── Criterio 4: caché por versión ────────────────────────────────────────────
def test_sufijo_de_cache():
    assert solar.sufijo_cache_pvgis("5.2") == ""
    assert solar.sufijo_cache_pvgis("5.3") == "_pvgis53"


def _funciones_cache():
    """Carga las funciones de caché de la página 2 sin Streamlit."""
    with open(_PAG2, encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    nombres = {"_cache_path", "_tmy_cache_path"}
    nodos = [n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name in nombres]
    assert {n.name for n in nodos} == nombres
    ns = {"os": os, "_SOLAR_CACHE_DIR": "/tmp/solar_cache_test",
          "sufijo_cache_pvgis": solar.sufijo_cache_pvgis}
    exec(compile(ast.Module(body=nodos, type_ignores=[]), _PAG2, "exec"), ns)
    return ns["_cache_path"], ns["_tmy_cache_path"]


def test_nombres_de_cache_52_no_cambian_y_53_son_distintos():
    cache_path, tmy_path = _funciones_cache()
    base = "/tmp/solar_cache_test/"
    assert cache_path(7.883, -76.6259, 10, 180, 44) == \
        base + "solar_7.8830_-76.6259_t10_a180_h44.pkl"
    assert cache_path(7.883, -76.6259, 10, 180, 44, 0.20, "5.2") == \
        base + "solar_7.8830_-76.6259_t10_a180_h44.pkl"
    assert cache_path(7.883, -76.6259, 10, 180, 44, 0.30, "5.3") == \
        base + "solar_7.8830_-76.6259_t10_a180_h44_pvgis53_alb0.30.pkl"
    assert tmy_path(7.883, -76.6259) == base + "tmy_7.8830_-76.6259.pkl"
    assert tmy_path(7.883, -76.6259, "5.3") == base + "tmy_7.8830_-76.6259_pvgis53.pkl"


# ── Criterio 5: cambiar la versión invalida el recurso solar ─────────────────
def _tupla(ruta, nombre):
    with open(ruta, encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == nombre for t in nodo.targets
        ):
            return tuple(e.value for e in nodo.value.elts if isinstance(e, ast.Constant))
    raise AssertionError(nombre)


def test_guarda_de_version_en_las_listas_de_limpieza():
    assert "_solar_pvgis_guardada" in _tupla(_PAG2, "_GUARD_KEYS")
    assert "_solar_pvgis_guardada" in _tupla(_PAG1, "_KEYS_LIMPIAR_CIUDAD")


def test_pagina_2_detecta_el_cambio_de_version_y_usa_la_elegida():
    with open(_PAG2, encoding="utf-8") as f:
        src = f.read()
    assert "_drift_pvgis" in src
    assert "cargar_tmy(lat, lon, pvgis_version)" in src
    assert 'st.session_state["_solar_pvgis_guardada"] = pvgis_version' in src
    assert "PVGIS v5.2 —" not in src   # el rótulo fijo desaparece


# ── Criterio 6: manual del Asistente ─────────────────────────────────────────
@pytest.mark.parametrize("pregunta, texto", [
    ("que version de PVGIS usa la app y cual usa PVsyst", "La referencia estándar internacional descarga PVGIS 5.3"),
    ("por que la radiacion de la app no coincide con PVsyst en Apartado", "1,606"),
    ("por que los meses del año tipico TMY no coinciden con PVsyst", "año escogido para cada mes"),
])
def test_manual_explica_la_version_de_pvgis(pregunta, texto):
    from calculos.asistente import BaseConocimiento
    secciones = BaseConocimiento.cargar().buscar(pregunta, k=6)
    candidatas = [s for s in secciones if "PVGIS 5.2 o 5.3" in s["titulo"]]
    assert candidatas, [s["titulo"] for s in secciones]
    # El Asistente lee todas las subsecciones recuperadas, no solo la primera.
    assert texto in "\n".join(s["texto"] for s in candidatas)
