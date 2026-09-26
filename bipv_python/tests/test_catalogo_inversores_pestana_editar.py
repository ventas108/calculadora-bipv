# -*- coding: utf-8 -*-
"""📋 Catálogo Paneles y 🔌 Catálogo Inversores PDF: la pestaña ✏️ Editar /
Eliminar debe verse aunque no se haya subido ningún PDF (26-sep-2026).

La pestaña ➕ Agregar desde PDF terminaba con ``st.stop()`` cuando aún no
había archivo, y ``st.stop()`` detiene la página entera: la pestaña de
edición quedaba en blanco y no se podía corregir ningún inversor ni panel.
"""
import ast
import glob
import os

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAGINAS = {
    "15_🔌_Catálogo_Inversores_PDF.py": ("btn_guardar_inv", "btn_inv_borrar"),
    "14_📋_Catálogo_Paneles.py": ("btn_guardar_edicion",),
}


def _arbol(nombre):
    with open(os.path.join(_ROOT, "pages", nombre), encoding="utf-8") as f:
        return ast.parse(f.read())


def _llama_stop(nodo):
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr == "stop" for n in ast.walk(nodo))


@pytest.mark.parametrize("nombre", sorted(_PAGINAS))
def test_pestana_agregar_no_usa_st_stop(nombre):
    fn = next(n for n in _arbol(nombre).body if isinstance(n, ast.FunctionDef)
              and n.name == "_pestana_agregar_desde_pdf")
    assert not _llama_stop(fn)


def test_ninguna_pestana_que_no_sea_la_ultima_usa_st_stop():
    """Guardia para todas las páginas: un ``st.stop()`` dentro de una pestaña
    que no es la última deja en blanco las pestañas siguientes."""
    malas = []
    for ruta in glob.glob(os.path.join(_ROOT, "pages", "*.py")):
        cuerpo = ast.parse(open(ruta, encoding="utf-8").read()).body
        bloques = [n for n in cuerpo if isinstance(n, ast.With)]
        for w in bloques[:-1]:
            if _llama_stop(w):
                malas.append(f"{os.path.basename(ruta)}:{w.lineno}")
    assert not malas, malas


@pytest.mark.parametrize("nombre", sorted(_PAGINAS))
def test_pestana_editar_se_ve_sin_subir_pdf(nombre, monkeypatch):
    AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
    import calculos.auth as auth
    monkeypatch.setattr(auth, "requerir_login",
                        lambda solo_admin=False: {"email": "t@t", "rol": "admin", "activo": True})
    at = AppTest.from_file(os.path.join(_ROOT, "pages", nombre), default_timeout=120).run()
    assert not at.exception
    claves = {b.key for b in at.button}
    for clave in _PAGINAS[nombre]:
        assert clave in claves, f"falta el botón {clave}"
