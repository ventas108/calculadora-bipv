# -*- coding: utf-8 -*-
"""Tareas #124/#127 — al cargar un proyecto, los flags *_ok NO deben revivir.

proyectos_manager importa streamlit (no disponible localmente), así que se
verifica vía AST sobre el código real, igual que test_invalidacion_ciudad.py:
1. "recurso_solar_ok" está en _claves_reset (#127).
2. Dentro de cargar_proyecto hay una limpieza de _claves_reset DESPUÉS del
   bucle que vuelca el estado guardado (si solo se limpia antes, el JSON
   revive los flags y el banner de #124 no avisa).

Reescrito 25-ago-2026 (auditoría CI): la versión anterior no eran tests de
pytest reales -- ejecutaba los checks a nivel de módulo y terminaba con
sys.exit(), lo que rompía la COLECCIÓN de pytest con un INTERNALERROR
(SystemExit durante el import) en vez de reportar un fallo normal. Por eso
este archivo llevaba semanas excluido con --ignore en cada corrida de la
suite -- exactamente el tipo de "alarma silenciada" que no queremos repetir.
"""
import ast
import os

RUTA = os.path.join(os.path.dirname(__file__), "..", "calculos", "proyectos_manager.py")


def _fn_cargar_proyecto() -> ast.FunctionDef:
    tree = ast.parse(open(RUTA, encoding="utf-8").read())
    return next(n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name == "cargar_proyecto")


def _claves_reset(fn: ast.FunctionDef) -> set | None:
    for n in ast.walk(fn):
        if isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "_claves_reset" for t in n.targets):
            return {ast.literal_eval(e) for e in n.value.elts}
    return None


def _linea_volcado_y_limpiezas(fn: ast.FunctionDef) -> tuple[int | None, list[int]]:
    linea_volcado = None
    lineas_limpieza = []
    for n in ast.walk(fn):
        if isinstance(n, ast.For):
            src = ast.dump(n.iter)
            if "estado" in src and "items" in src:
                linea_volcado = n.lineno
            if isinstance(n.iter, ast.Name) and n.iter.id == "_claves_reset":
                lineas_limpieza.append(n.lineno)
    return linea_volcado, lineas_limpieza


def test_127_recurso_solar_ok_en_claves_reset():
    claves = _claves_reset(_fn_cargar_proyecto())
    assert claves is not None and "recurso_solar_ok" in claves


def test_124_flags_de_simulacion_en_claves_reset():
    claves = _claves_reset(_fn_cargar_proyecto())
    assert claves is not None and {"produccion_ok", "financiero_ok"} <= claves


def test_127_existe_volcado_del_estado_guardado():
    linea_volcado, _ = _linea_volcado_y_limpiezas(_fn_cargar_proyecto())
    assert linea_volcado is not None


def test_127_hay_limpieza_de_flags_despues_del_volcado():
    # Si la limpieza ocurre ANTES del volcado del JSON guardado, los flags
    # *_ok reviven con el estado viejo y el banner de #124 nunca avisa.
    linea_volcado, lineas_limpieza = _linea_volcado_y_limpiezas(_fn_cargar_proyecto())
    assert linea_volcado is not None and any(l > linea_volcado for l in lineas_limpieza)
