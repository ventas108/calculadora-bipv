# -*- coding: utf-8 -*-
"""Spec 05-perdidas-y-temperatura/columnas-a-medida (3-oct-2026).

Fachadas con columnas de módulos entre ventanas: la separación cambia de una
columna a otra (La Salle SO: huecos de 1,1 m a 9,15 m). El generador acepta
la posición de cada columna, medida desde la esquina hasta el borde izquierdo
de la columna, vista desde afuera.
"""
from pathlib import Path

import numpy as np
import pytest

from calculos.puntos_modulo import generar_puntos_modulos, parsear_posiciones, vectores_superficie

_W, _H = 1.046, 1.690
_RAIZ = Path(__file__).resolve().parents[1]


def test_centros_con_posiciones_a_medida():
    pts = generar_puntos_modulos("Sur", 90.0, 180.0, (0, 0, 0), filas=1, columnas=3, largo_m=_H, ancho_m=_W,
                                 posiciones_columnas_m=[0.0, 1.1, 3.43])
    assert [round(p["x"], 6) for p in pts] == [0.523, 1.623, 3.953]
    assert [p["columna"] for p in pts] == [1, 2, 3]


@pytest.mark.parametrize("tilt, az", [(90.0, 250.5), (20.0, 162.0)])
def test_igual_a_generar_cada_columna_por_separado(tilt, az):
    esquina = np.array([4.0, -3.0, 0.5])
    pos = [0.0, 1.1, 3.43, 11.35, 12.45]
    _, u, _ = vectores_superficie(tilt, az)
    juntos = generar_puntos_modulos("S", tilt, az, esquina, 4, len(pos), _H, _W, separacion_v_m=0.044,
                                    posiciones_columnas_m=pos)
    for c, d in enumerate(pos, 1):
        sola = generar_puntos_modulos("S", tilt, az, esquina + u * d, 4, 1, _H, _W, separacion_v_m=0.044)
        mias = [p for p in juntos if p["columna"] == c]
        for a, b in zip(mias, sola):
            assert np.allclose([a["x"], a["y"], a["z"]], [b["x"], b["y"], b["z"]], atol=1e-12)


def test_strings_por_columna_con_posiciones_a_medida():
    pts = generar_puntos_modulos("S", 90, 180, (0, 0, 0), 21, 3, _H, _W, posiciones_columnas_m=[0, 2.4, 9.3],
                                 grupos=[{"gid": "G1", "n_serie": 21, "n_paralelo": 3}])
    assert {p["string"] for p in pts if p["columna"] == 2} == {"G1-S2"}


@pytest.mark.parametrize("pos, motivo", [
    ([0.0, 1.1], "3 columnas"),
    ([0.0, 0.5, 3.0], "se solapan"),
    ([0.0, 3.0, 2.0], "orden"),
    ([-0.2, 1.1, 3.0], "negativa"),
])
def test_validaciones_de_posiciones(pos, motivo):
    with pytest.raises(ValueError, match=motivo):
        generar_puntos_modulos("S", 90, 180, (0, 0, 0), 1, 3, _H, _W, posiciones_columnas_m=pos)


def test_parsear_posiciones_con_coma_decimal():
    assert parsear_posiciones("0; 1,1; 3,43") == [0.0, 1.1, 3.43]
    assert parsear_posiciones("0 1.1 3.43") == [0.0, 1.1, 3.43]
    assert parsear_posiciones("  ") is None
    with pytest.raises(ValueError, match="«x2»"):
        parsear_posiciones("0; x2")


def test_la_pagina_genera_columnas_a_medida():
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
    uid = at.session_state["superficies_bipv"][0]["uid"]          # Este: 7 en serie × 2 strings
    at.number_input(key=f"gen_f_{uid}").set_value(7)
    at.number_input(key=f"gen_c_{uid}").set_value(2)
    at.text_input(key=f"gen_pos_{uid}").set_value("0; 4,5")
    at.button(key=f"gen_btn_{uid}").click().run()
    assert not at.exception, [e.value for e in at.exception]
    filas = [list(map(float, l.split(","))) for l in at.session_state[f"multisup_puntos_{uid}"].splitlines()]
    ys = sorted({round(f[1], 3) for f in filas})            # fachada este: las columnas avanzan hacia el norte
    assert len(filas) == 14 and ys[1] - ys[0] == pytest.approx(4.5, abs=1e-3)
    # Posiciones que no coinciden con las columnas: error claro, sin tocar los puntos.
    at.text_input(key=f"gen_pos_{uid}").set_value("0; 4,5; 9")
    at.button(key=f"gen_btn_{uid}").click().run()
    assert any("3 posiciones" in e.value for e in at.error)


def test_guia_y_manual():
    from calculos.guia_vista_3d import guia_markdown
    assert "posición de cada columna" in guia_markdown()
    kb = (_RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    i = kb.index("## 127.")
    s = kb[i:kb.find("\n## ", i + 5) if kb.find("\n## ", i + 5) > 0 else None]
    for t in ("posición de cada columna", "borde izquierdo", "La Salle", "0; 1,1", "🧮 Generar puntos"):
        assert t in s, t
    assert i < kb.rindex("Calculadora BIPV — Innovación Química")
    for p in ("PV" + "syst", "PV" + "·SOL", "PV" + " SOL", "PV" + "SOL", "pendi" + "ente"):
        assert p not in s, p
