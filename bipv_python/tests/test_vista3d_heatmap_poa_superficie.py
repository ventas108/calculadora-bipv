"""Spec 08-interfaz/heatmap-poa-superficie.

El mapa de calor POA hora × mes de Vista 3D elegía la serie con
``poa_superficies.get(nombre) or poa_df``. Cuando ya se había calculado el POA
por superficie, ese valor es un DataFrame y ``or`` evalúa su verdad, lo que
pandas prohíbe: ``ValueError: The truth value of a DataFrame is ambiguous`` y
Streamlit corta la página.
"""
import ast
from pathlib import Path

import pandas as pd
import pytest

_PAGINA = Path(__file__).resolve().parents[1] / "pages" / "9_🗺️_Vista_3D.py"
_CLAVES_DATAFRAME = ("poa_superficies", "poa_df")


def _nombres_dataframe(arbol: ast.AST) -> set[str]:
    """Variables asignadas desde las claves de session_state que guardan DataFrames."""
    nombres = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Assign) and any(
            clave in ast.unparse(nodo.value) for clave in _CLAVES_DATAFRAME
        ):
            nombres.update(t.id for t in nodo.targets if isinstance(t, ast.Name))
    return nombres


def test_vista3d_no_evalua_la_verdad_de_series_poa():
    arbol = ast.parse(_PAGINA.read_text(encoding="utf-8"))
    nombres = _nombres_dataframe(arbol)
    culpables = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.BoolOp) and isinstance(nodo.op, ast.Or):
            operandos = [ast.unparse(v) for v in nodo.values]
            if any(
                any(clave in texto for clave in _CLAVES_DATAFRAME)
                or texto in nombres
                for texto in operandos
            ):
                culpables.append(f"línea {nodo.lineno}: {' or '.join(operandos)}")
    assert not culpables, (
        "Un `or` sobre series POA evalúa la verdad de un DataFrame "
        "(ValueError en pandas): " + "; ".join(culpables)
    )


def test_la_seleccion_de_serie_con_is_none_funciona_con_dataframes():
    """El patrón corregido no evalúa la verdad del DataFrame."""
    poa_sup = pd.DataFrame({"poa_global": [1.0, 2.0]})
    poa_general = pd.DataFrame({"poa_global": [9.0, 9.0]})

    with pytest.raises(ValueError, match="ambiguous"):
        _ = {"Sur": poa_sup}.get("Sur") or poa_general

    for superficies, esperado in (({"Sur": poa_sup}, poa_sup), ({}, poa_general)):
        elegido = superficies.get("Sur")
        if elegido is None:
            elegido = poa_general
        assert elegido is esperado


def test_mapa_de_calor_indica_de_donde_salen_sus_valores():
    """Reportado en producción 24-sep-2026: sin POA vigente de la superficie,
    el mapa usaba en silencio la POA general de ☀️ Recurso Solar (orientación
    del proyecto) o un valor fijo de 300 W/m², con el título de la superficie."""
    src = _PAGINA.read_text(encoding="utf-8")
    inicio = src.index("Solo POA vigente de la superficie")
    bloque = src[inicio:inicio + 3000]
    assert "_fuente_hm" in bloque
    assert "POA vigente de esta superficie" in bloque
    assert "POA general de ☀️ Recurso Solar" in bloque
    assert "estimación fija de 300 W/m²" in bloque
    assert "TEXTO_MOTIVO_POA" in bloque
