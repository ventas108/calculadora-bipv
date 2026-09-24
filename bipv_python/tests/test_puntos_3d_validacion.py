"""Spec 08-interfaz/puntos-3d-validacion.

Vista 3D interpretaba los puntos 3D en la propia página: una línea con otro
número de valores o con coma decimal (`8,5;0;2`) se descartaba en silencio,
los puntos dentro del volumen solo se detectaban al calcular y los puntos se
guardaban por NOMBRE de superficie.
"""
import ast
from pathlib import Path

import pytest
import trimesh

from calculos.puntos_3d import (
    migrar_puntos_por_uid,
    parsear_puntos_3d,
    previsualizar_puntos,
    puntos_por_nombre,
)

_PAGINA = Path(__file__).resolve().parents[1] / "pages" / "9_🗺️_Vista_3D.py"


# ── Parser ───────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("linea, esperado", [
    ("8,0,2", (8.0, 0.0, 2.0)),
    ("8.5,0,2", (8.5, 0.0, 2.0)),
    ("8;0;2", (8.0, 0.0, 2.0)),
    ("8,5;0;2", (8.5, 0.0, 2.0)),
    ("  -3.25 , 4 , 0.5  ", (-3.25, 4.0, 0.5)),
    ("1,5 ; -2,75 ; 10", (1.5, -2.75, 10.0)),
])
def test_lineas_validas(linea, esperado):
    puntos, errores = parsear_puntos_3d(linea, "Sur")
    assert errores == []
    assert [(p["x"], p["y"], p["z"]) for p in puntos] == [esperado]
    assert puntos[0]["nombre"] == "Sur-P1" and puntos[0]["fachada"] == "Sur"


@pytest.mark.parametrize("linea, fragmento", [
    ("8,5,0,2", "3 valores"),
    ("8,0", "3 valores"),
    ("8,a,2", "no numérico"),
    ("8;0", "3 valores"),
    ("8,5;0,5,1;2", "no numérico"),
    ("nan,0,2", "finito"),
    ("8,inf,2", "finito"),
    ("8 0 2", "3 valores"),
])
def test_lineas_con_error_nunca_se_descartan(linea, fragmento):
    puntos, errores = parsear_puntos_3d(f"1,1,1\n{linea}\n2,2,2", "Sur")
    assert len(puntos) == 2
    assert [p["nombre"] for p in puntos] == ["Sur-P1", "Sur-P2"]
    assert len(errores) == 1
    assert errores[0]["linea"] == 2 and errores[0]["texto"] == linea.strip()
    assert fragmento in errores[0]["motivo"]


def test_lineas_vacias_se_ignoran_sin_error():
    puntos, errores = parsear_puntos_3d("\n  \n1,2,3\n\n4;5;6\n", "Techo")
    assert errores == [] and len(puntos) == 2


def test_coma_decimal_sin_punto_y_coma_sugiere_separador():
    _, errores = parsear_puntos_3d("8,5,0,2", "Sur")
    assert ";" in errores[0]["motivo"]


# ── Vista previa geométrica (misma validar_puntos del motor) ────────────────
@pytest.fixture(scope="module")
def caja():
    # Cubo de 10 m con la cara x = 5 m hacia el Este.
    return trimesh.creation.box(extents=(10.0, 10.0, 10.0))


def _punto(x):
    return [{"nombre": "Sur-P1", "fachada": "Sur", "x": x, "y": 0.0, "z": 0.0}]


def test_vista_previa_punto_dentro(caja):
    avisos = previsualizar_puntos(caja, _punto(0.0))
    assert any("DENTRO" in a for a in avisos)


def test_vista_previa_punto_a_5_cm(caja):
    avisos = previsualizar_puntos(caja, _punto(5.05))
    assert any("5 cm" in a for a in avisos)


def test_vista_previa_punto_a_30_cm_es_valido(caja):
    assert previsualizar_puntos(caja, _punto(5.30)) == []


def test_vista_previa_sin_malla_o_sin_puntos():
    assert previsualizar_puntos(None, _punto(0.0)) == []
    assert previsualizar_puntos(trimesh.creation.box(), []) == []


# ── Asociación por uid ───────────────────────────────────────────────────────
_SUPS = [{"uid": 1, "nombre": "Sur"}, {"uid": 2, "nombre": "Techo"}]


def test_migracion_desde_nombres():
    antiguo = {"Sur": [{"x": 1}], "Borrada": [{"x": 2}], 2: [{"x": 3}]}
    migrado, avisos = migrar_puntos_por_uid(antiguo, _SUPS)
    assert migrado == {1: [{"x": 1}], 2: [{"x": 3}]}
    assert len(avisos) == 1 and "Borrada" in avisos[0]


def test_migracion_desde_json_con_uid_en_texto():
    migrado, avisos = migrar_puntos_por_uid({"1": [{"x": 1}]}, _SUPS)
    assert migrado == {1: [{"x": 1}]} and avisos == []


def test_migracion_idempotente_y_sin_mutar():
    antiguo = {"Sur": [{"x": 1}]}
    copia = dict(antiguo)
    migrado, _ = migrar_puntos_por_uid(antiguo, _SUPS)
    assert antiguo == copia
    assert migrar_puntos_por_uid(migrado, _SUPS) == (migrado, [])


def test_renombrar_conserva_puntos_y_el_motor_recibe_nombres():
    puntos = {1: [{"x": 1}], 2: [{"x": 2}]}
    renombradas = [{"uid": 1, "nombre": "Fachada Sur", "activa": True},
                   {"uid": 2, "nombre": "Techo", "activa": False}]
    assert puntos_por_nombre(puntos, renombradas) == {"Fachada Sur": [{"x": 1}]}


# ── Página ───────────────────────────────────────────────────────────────────
def test_pagina_usa_el_parser_y_bloquea_el_boton_con_errores():
    src = _PAGINA.read_text(encoding="utf-8")
    assert "parsear_puntos_3d(" in src
    assert "previsualizar_puntos(" in src
    assert "migrar_puntos_por_uid(" in src
    assert "except ValueError:\n                        pass" not in src
    arbol = ast.parse(src)
    asignacion = next(
        n for n in ast.walk(arbol)
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "_sombra_lista" for t in n.targets)
    )
    assert "_errores_puntos" in ast.unparse(asignacion.value)
