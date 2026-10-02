# -*- coding: utf-8 -*-
"""Spec 01-datos-proyecto/cache-catalogo-paneles (2-oct-2026).

El PR #107 insertó la función auxiliar ``_texto_celda`` justo debajo del
``@st.cache_data`` de ``cargar_catalogo_paneles``: la caché quedó en la
función pequeña y el catálogo (3.138 paneles) se releía del Excel en cada
clic (5-9 s en Motor IV, Dimensionamiento, Producción y Financiero).
"""
import ast
from pathlib import Path

import datos.catalogo_paneles_excel as cpe

_RAIZ = Path(__file__).resolve().parents[1]


def test_el_catalogo_de_paneles_esta_en_cache():
    assert hasattr(cpe.cargar_catalogo_paneles, "clear")       # envuelta por st.cache_data
    assert not hasattr(cpe._texto_celda, "clear")              # la auxiliar no


def test_ningun_cargador_de_catalogo_pierde_su_cache():
    """Guardia: en datos/, toda función pública ``cargar_catalogo*`` tiene
    caché (``.clear``), directa o por una función interna con el mtime."""
    import importlib
    faltan = []
    for ruta in (_RAIZ / "datos").glob("catalogo_*.py"):
        nombres = [f.name for f in ast.parse(ruta.read_text(encoding="utf-8")).body
                   if isinstance(f, ast.FunctionDef) and f.name.startswith("cargar_catalogo")]
        if not nombres:
            continue
        mod = importlib.import_module(f"datos.{ruta.stem}")
        faltan += [f"{ruta.name}:{n}" for n in nombres if not hasattr(getattr(mod, n), "clear")]
    assert not faltan, faltan


def test_segunda_carga_inmediata():
    import time
    cpe.cargar_catalogo_paneles()
    t = time.time()
    cpe.cargar_catalogo_paneles()
    assert time.time() - t < 0.5
