# -*- coding: utf-8 -*-
"""Spec 05-perdidas-y-temperatura/puntos-automaticos-por-modulo (3-oct-2026).

La app genera un punto de análisis por módulo, en metros, separado de la
fachada por la normal de la superficie y asignado a su string. Antes los
puntos se escribían a mano (milímetros, puntos dentro del edificio, un solo
punto) y todos los strings de una superficie recibían la misma sombra.
"""
import math

import numpy as np
import pytest

from calculos.puntos_modulo import (
    etiquetar_strings, generar_puntos_modulos, texto_puntos, vectores_superficie,
)

_W, _H = 1.046, 1.690           # módulo 1.046 × 1.690 m


def _plano(p, esquina, n):
    return float(np.dot(np.array([p["x"], p["y"], p["z"]]) - np.array(esquina), n))


# ── Geometría ─────────────────────────────────────────────────────────────
def test_fachada_sur_centros_exactos():
    pts = generar_puntos_modulos("Sur", 90.0, 180.0, (0.0, 0.0, 0.0), filas=1, columnas=3,
                                 largo_m=_H, ancho_m=_W, separacion_h_m=0.02, separacion_v_m=0.02,
                                 separacion_fachada_m=0.30)
    assert [round(p["x"], 6) for p in pts] == [0.523, 1.589, 2.655]
    assert all(p["y"] == pytest.approx(-0.30, abs=1e-12) for p in pts)     # 0,3 m hacia el sur
    assert all(p["z"] == pytest.approx(_H / 2, abs=1e-12) for p in pts)
    assert all(p["tilt_deg"] == 90.0 and p["azimuth_deg"] == 180.0 for p in pts)


def test_fachada_este_avanza_hacia_el_norte_y_sale_al_este():
    n, u, v = vectores_superficie(90.0, 90.0)
    assert np.allclose(n, [1, 0, 0]) and np.allclose(u, [0, 1, 0]) and np.allclose(v, [0, 0, 1])
    pts = generar_puntos_modulos("Este", 90.0, 90.0, (10.0, 5.0, 3.0), filas=2, columnas=1,
                                 largo_m=_H, ancho_m=_W, separacion_v_m=0.0)
    assert [round(p["x"], 6) for p in pts] == [10.3, 10.3]
    assert [round(p["z"], 6) for p in pts] == [round(3 + _H / 2, 6), round(3 + 1.5 * _H, 6)]


@pytest.mark.parametrize("tilt, az", [(10.0, 180.0), (30.0, 249.0), (0.0, 162.0), (90.0, 162.0)])
def test_todos_los_puntos_a_la_distancia_pedida_del_plano(tilt, az):
    esquina = (3.0, -2.0, 12.0)
    n, u, v = vectores_superficie(tilt, az)
    assert abs(np.dot(n, u)) < 1e-12 and abs(np.dot(n, v)) < 1e-12 and abs(np.dot(u, v)) < 1e-12
    assert np.linalg.norm(n) == pytest.approx(1) and np.linalg.norm(u) == pytest.approx(1)
    pts = generar_puntos_modulos("S", tilt, az, esquina, filas=3, columnas=4, largo_m=_H, ancho_m=_W,
                                 separacion_fachada_m=0.25)
    for p in pts:
        assert _plano(p, esquina, n) == pytest.approx(0.25, abs=1e-9)
    # v apunta cuesta arriba (o es vertical)
    assert v[2] >= -1e-12


def test_orientacion_horizontal_intercambia_lados():
    vert = generar_puntos_modulos("S", 90.0, 180.0, (0, 0, 0), 1, 2, _H, _W, separacion_h_m=0.0)
    hor = generar_puntos_modulos("S", 90.0, 180.0, (0, 0, 0), 1, 2, _H, _W, orientacion="horizontal",
                                 separacion_h_m=0.0)
    assert vert[1]["x"] - vert[0]["x"] == pytest.approx(_W)
    assert hor[1]["x"] - hor[0]["x"] == pytest.approx(_H)
    assert hor[0]["z"] == pytest.approx(_W / 2)


# ── Strings ───────────────────────────────────────────────────────────────
def test_cableado_por_columnas_y_por_filas():
    g = [{"gid": "G1", "n_serie": 2, "n_paralelo": 3}]
    col = generar_puntos_modulos("S", 90, 180, (0, 0, 0), 2, 3, _H, _W, grupos=g, cableado="columnas")
    assert {(p["fila"], p["columna"]): p["string"] for p in col} == {
        (1, 1): "G1-S1", (2, 1): "G1-S1", (1, 2): "G1-S2", (2, 2): "G1-S2", (1, 3): "G1-S3", (2, 3): "G1-S3"}
    g2 = [{"gid": "G1", "n_serie": 3, "n_paralelo": 1}, {"gid": "G2", "n_serie": 3, "n_paralelo": 1}]
    fil = generar_puntos_modulos("S", 90, 180, (0, 0, 0), 2, 3, _H, _W, grupos=g2, cableado="filas")
    assert {p["string"] for p in fil if p["fila"] == 1} == {"G1-S1"}
    assert {p["string"] for p in fil if p["fila"] == 2} == {"G2-S1"}
    assert sorted(p["posicion"] for p in fil if p["string"] == "G2-S1") == [1, 2, 3]
    assert len({p["nombre"] for p in fil}) == 6


@pytest.mark.parametrize("kw, motivo", [
    (dict(filas=2, columnas=3, grupos=[{"gid": "G1", "n_serie": 4, "n_paralelo": 1}]), "6 módulos"),
    (dict(filas=0, columnas=3), "filas"),
    (dict(filas=1, columnas=1, separacion_fachada_m=0.05), "0,10 m"),
    (dict(filas=1, columnas=1, largo_m=1690.0), "metros"),
    (dict(filas=1, columnas=1, cableado="diagonal"), "cableado"),
])
def test_validaciones_estrictas(kw, motivo):
    base = dict(nombre_superficie="S", tilt_deg=90.0, azimuth_deg=180.0, esquina=(0, 0, 0),
                largo_m=_H, ancho_m=_W)
    base.update(kw)
    with pytest.raises(ValueError, match=motivo):
        generar_puntos_modulos(**base)


# ── Texto y etiquetado ────────────────────────────────────────────────────
def test_texto_en_metros_al_milimetro_y_etiquetado_por_orden():
    g = [{"gid": "G1", "n_serie": 2, "n_paralelo": 1}]
    pts = generar_puntos_modulos("S", 90, 180, (0, 0, 0), 1, 2, _H, _W, grupos=g)
    texto = texto_puntos(pts)
    assert texto.splitlines()[0] == "0.523,-0.300,0.845"
    parseados = [{"nombre": f"S-P{i}", "x": 0.0, "y": 0.0, "z": 0.0} for i in range(2)]
    meta = {"texto": texto, "strings": [p["string"] for p in pts]}
    assert [p["string"] for p in etiquetar_strings(parseados, texto, meta)] == ["G1-S1", "G1-S1"]
    # Si el usuario edita el texto, no se inventa la asignación.
    assert all("string" not in p for p in etiquetar_strings(parseados, texto + "\n1,1,1", meta))
    assert all("string" not in p for p in etiquetar_strings(parseados, texto, None))


# ── Página Vista 3D (AppTest) ─────────────────────────────────────────────
def test_la_pagina_genera_los_puntos_y_los_asigna_a_sus_strings():
    from streamlit.testing.v1 import AppTest
    import calculos.auth as _auth
    from tests.test_flujo_fisico_multisuperficie_end_to_end import _session_state_realista, _tmy

    _auth.requerir_login = lambda solo_admin=False: {"email": "t@t", "rol": "admin", "activo": True, "nombre": "T"}
    at = AppTest.from_file("pages/9_🗺️_Vista_3D.py", default_timeout=300)
    tmy = _tmy()
    for k, v in {**_session_state_realista(tmy), "tmy_df": tmy, "ciudad": "Bogotá",
                 "recurso_solar_ok": True}.items():
        at.session_state[k] = v
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    uid = at.session_state["superficies_bipv"][0]["uid"]          # Este: 7 en serie × 2 strings
    at.number_input(key=f"gen_f_{uid}").set_value(2)
    at.number_input(key=f"gen_c_{uid}").set_value(7)
    at.button(key=f"gen_btn_{uid}").click().run()
    assert not at.exception, [e.value for e in at.exception]
    texto = at.session_state[f"multisup_puntos_{uid}"]
    assert len(texto.splitlines()) == 14
    assert at.session_state[f"multisup_puntos_meta_{uid}"]["strings"].count("G1-S1") == 7
    assert any("14 puntos asignados a 2 strings" in c.value for c in at.caption)
    # Con 3 filas × 7 columnas (21 módulos) no cuadra con 14 módulos: error claro.
    at.number_input(key=f"gen_f_{uid}").set_value(3)
    at.button(key=f"gen_btn_{uid}").click().run()
    assert any("21 módulos" in e.value and "14" in e.value for e in at.error)


def test_la_guia_y_el_manual_explican_el_generador():
    from pathlib import Path
    from calculos.guia_vista_3d import guia_markdown
    texto = guia_markdown()
    assert "🧮 Generar puntos" in texto and "esquina" in texto
    raiz = Path(__file__).resolve().parents[1]
    kb = (raiz / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    i = kb.index("## 126.")
    s = kb[i:kb.find("\n## ", i + 5) if kb.find("\n## ", i + 5) > 0 else None]
    for t in ("🧮 Generar puntos", "esquina", "inferior izquierda", "string", "metros", "filas", "columnas",
              "La Salle", "Calcular sombra"):
        assert t in s, t
    assert i < kb.rindex("Calculadora BIPV — Innovación Química")
    for p in ("PV" + "syst", "PV" + "·SOL", "PV" + " SOL", "PV" + "SOL", "pendi" + "ente"):
        assert p not in s, p
