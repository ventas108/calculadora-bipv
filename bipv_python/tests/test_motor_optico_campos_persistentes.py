# -*- coding: utf-8 -*-
"""🔆 Motor Óptico: los campos no vuelven a su mínimo al cambiar de página (30-sep-2026).

Caso real (Urabá, después de desplegar el #93): el usuario puso NOCT 45 °C y
γ −0,29 %/°C con «Usar los de la ficha», guardó y al volver vio NOCT 35 y
γ −0,70 — los MÍNIMOS de los campos. Los campos usaban la misma clave para el
dato y el widget; Streamlit borra la clave de un widget al abrir otra página
o recargar, y el campo arrancaba en su mínimo. Mismo patrón que Financiero
(Spec 06/parametros-persistentes).
"""
import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

PAGINA = next((Path(__file__).resolve().parents[1] / "pages").glob("5b_*Motor_Optico.py"))
JAM = {"nombre": "JAM66D46-720/LB", "NOCT": 45.0, "gamma_mp": -0.29, "Tk_gamma": -0.29,
       "tecnologia": "Mono-c-Si", "transparencia_pct": 0}


_RECURSO = {}


def _recurso():
    """TMY y POA sintéticos (sin red), una sola vez por módulo de prueba."""
    if not _RECURSO:
        from calculos.solar import calcular_poa
        from tests.test_simulation_pipeline import _tmy_sintetico_offline
        tmy = _tmy_sintetico_offline(7.883, -76.626, 44)
        poa = calcular_poa(tmy, 7.883, -76.626, 44, 10, 180)
        _RECURSO.update(tmy_df=tmy, poa_df=poa, poa_anual_kWh_m2=float(poa["poa_global"].sum()) / 1000)
    return dict(_RECURSO)


def _abrir(**estado):
    at = AppTest.from_file(str(PAGINA), default_timeout=120)
    import calculos.auth as _auth
    _auth.requerir_login = lambda solo_admin=False: {"email": "t@t", "rol": "admin", "activo": True, "nombre": "T"}
    for k, v in {"panel_dict": JAM, "tipo_instalacion": "Granja fotovoltaica", "tilt_fachada": 10,
                 "azimuth_fachada": 180, "recurso_solar_ok": True, **_recurso(), **estado}.items():
        at.session_state[k] = v
    at.run()
    return at


def _campo(at, clave):
    return next(w for w in list(at.number_input) + list(at.slider) + list(at.selectbox) + list(at.checkbox)
                if w.key == f"_w_{clave}")


def _cambiar_de_pagina(at):
    """Lo que hace Streamlit al abrir otra página y volver: sobreviven los datos,
    no las claves de los widgets («_w_*»). Se abre la página de nuevo solo con eso."""
    datos = {k: v for k, v in at.session_state.filtered_state.items() if not k.startswith("_w_")}
    nueva = AppTest.from_file(str(PAGINA), default_timeout=120)
    for k, v in datos.items():
        nueva.session_state[k] = v
    nueva.run()
    return nueva


def test_noct_y_gamma_sobreviven_al_cambio_de_pagina():
    at = _abrir()
    assert _campo(at, "mo_noct").value == 45.0 and _campo(at, "mo_coef_temp").value == -0.29
    _campo(at, "mo_noct").set_value(47.0).run()
    _campo(at, "mo_coef_temp").set_value(-0.31).run()
    at = _cambiar_de_pagina(at)
    assert _campo(at, "mo_noct").value == 47.0            # antes volvía a 35 (el mínimo)
    assert _campo(at, "mo_coef_temp").value == -0.31      # antes volvía a −0,70
    assert at.session_state["mo_noct"] == 47.0            # así se guarda el proyecto
    assert at.session_state["mo_coef_temp"] == -0.31


def test_proyecto_abierto_muestra_lo_guardado():
    # «Cargar proyecto» escribe los datos y deja el panel como referencia (sin auto-llenado)
    at = _abrir(mo_panel_ref=JAM["nombre"], mo_noct=46.0, mo_coef_temp=-0.30,
                mo_f_iam_dif=0.93, mo_transparencia=10)
    assert _campo(at, "mo_noct").value == 46.0
    assert _campo(at, "mo_coef_temp").value == -0.30
    assert _campo(at, "mo_f_iam_dif").value == 0.93
    assert _campo(at, "mo_transparencia").value == 10


def test_sin_dato_usa_el_ultimo_calculo_y_no_el_minimo():
    at = _abrir(mo_panel_ref=JAM["nombre"], motor_optico_noct=45.0, motor_optico_coef_temp=-0.0029)
    assert _campo(at, "mo_noct").value == 45.0
    assert abs(_campo(at, "mo_coef_temp").value - (-0.29)) < 1e-9


def test_usar_los_de_la_ficha_actualiza_el_campo_y_el_dato():
    at = _abrir(mo_panel_ref=JAM["nombre"], mo_noct=35.0, mo_coef_temp=-0.70)
    boton = next(b for b in at.button if b.key == "mo_usar_ficha_termica")
    boton.click().run()
    assert _campo(at, "mo_noct").value == 45.0 and at.session_state["mo_noct"] == 45.0
    assert _campo(at, "mo_coef_temp").value == -0.29 and at.session_state["mo_coef_temp"] == -0.29
    at = _cambiar_de_pagina(at)
    assert _campo(at, "mo_noct").value == 45.0


def test_ningun_campo_usa_la_clave_del_dato_como_widget():
    src = PAGINA.read_text(encoding="utf-8")
    for clave in ("mo_noct", "mo_coef_temp", "mo_vidrio_sel", "mo_transparencia", "mo_montaje",
                  "mo_b0_custom", "mo_soiling_custom", "mo_k_soiling_vert", "mo_f_iam_dif"):
        assert not re.search(rf'key="{clave}"', src), clave


def test_manual_del_asistente_lo_explica():
    kb = (Path(__file__).resolve().parents[1] / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    seccion = kb[kb.index("## 99."):]
    for texto in ("35 °C", "−0,70", "mínimo", "Usar los de la ficha", "8 campos"):
        assert texto in seccion, texto
    assert "PVsyst" not in seccion
