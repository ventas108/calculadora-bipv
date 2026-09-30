# -*- coding: utf-8 -*-
"""Campos ligados a su dato: no vuelven a su mínimo ni a su valor por defecto (30-sep-2026).

Auditoría tras el bug del Motor Óptico (NOCT 35 °C y γ −0,70 %/°C al volver
a la página): el mismo patrón —la clave del dato usada como clave del
widget— estaba en 📐 Dimensionamiento («N_str_tr»: volvía a 1), 🔀 Mismatch
(«bypass_n_series», «bypass_n_parallel», «bypass_panel»: volvían al valor por
defecto) y 📊 Producción («produccion_usar_iv»: el modo Motor IV se apagaba).
Streamlit borra la clave de un widget al abrir otra página o recargar.
"""
import glob
import os
import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

from calculos.campos_editor import campo_ligado

RAIZ = Path(__file__).resolve().parents[1]


def _app():
    import streamlit as st
    from calculos.campos_editor import campo_ligado as _cl
    if st.session_state.get("pagina", "a") == "a":
        _cl(st.session_state, st.number_input, "Strings por tracker", "N_str_tr", 3, min_value=1)
        _cl(st.session_state, st.selectbox, "Panel", "bypass_panel", "A", options=["A", "B", "C"])
        _cl(st.session_state, st.toggle, "Motor IV", "produccion_usar_iv", False)
    else:
        st.write("otra página")


def test_los_valores_sobreviven_al_cambio_de_pagina():
    at = AppTest.from_function(_app)
    at.run()
    at.number_input[0].set_value(4).run()
    at.selectbox[0].set_value("C").run()
    at.toggle[0].set_value(True).run()
    at.session_state["pagina"] = "b"
    at.run()
    assert at.session_state["N_str_tr"] == 4                 # así se guarda el proyecto
    assert at.session_state["bypass_panel"] == "C"
    assert at.session_state["produccion_usar_iv"] is True
    at.session_state["pagina"] = "a"
    at.run()
    assert at.number_input[0].value == 4                     # antes: 1 (el mínimo)
    assert at.selectbox[0].value == "C"                      # antes: el de por defecto
    assert at.toggle[0].value is True                        # antes: apagado


def test_un_cambio_del_dato_desde_fuera_actualiza_el_campo():
    at = AppTest.from_function(_app)
    at.run()
    at.session_state["N_str_tr"] = 6                         # p. ej. «Cargar proyecto» o un recálculo
    at.run()
    assert at.number_input[0].value == 6
    at.number_input[0].set_value(5).run()
    at.number_input[0].set_value(7).run()
    assert at.session_state["N_str_tr"] == 7


def test_rango_y_opciones():
    estado = {"x": 99, "p": "Z"}

    def _widget(etiqueta, key, **kw):
        return estado[key]

    assert campo_ligado(estado, _widget, "x", "x", 5, min_value=1, max_value=30) == 30
    assert campo_ligado(estado, _widget, "p", "p", "A", options=["A", "B"]) == "A"
    assert campo_ligado(estado, _widget, "n", "n", 3, min_value=1) == 3


# ── Guardas en el código ────────────────────────────────────────────────────
PAGINAS = sorted(glob.glob(str(RAIZ / "pages" / "*.py")))
CALCULOS = sorted(glob.glob(str(RAIZ / "calculos" / "*.py")))
_WIDGET = re.compile(
    r"st\.(number_input|slider|selectbox|checkbox|radio|text_input|select_slider|toggle|date_input|multiselect)"
    r"\((?:[^()]|\([^()]*\))*?key=[\"']([A-Za-z0-9_]+)[\"']", re.S)


def test_los_tres_campos_de_la_auditoria_usan_su_dato():
    for patron, claves in (("4_*Dimensionamiento.py", ("N_str_tr",)),
                           ("5_*Mismatch.py", ("bypass_n_series", "bypass_n_parallel", "bypass_panel")),
                           ("6_*Produccion.py", ("produccion_usar_iv",))):
        src = next((RAIZ / "pages").glob(patron)).read_text(encoding="utf-8")
        for clave in claves:
            assert not re.search(rf'key=["\']{clave}["\']', src), clave
            assert f'"{clave}"' in src and "campo_ligado(" in src, clave


def test_ninguna_pagina_usa_como_widget_un_dato_que_leen_otros_modulos():
    """Guarda general: si otra página o un cálculo lee la clave, el widget no puede usarla."""
    widgets = {}
    for p in PAGINAS:
        for m in _WIDGET.finditer(Path(p).read_text(encoding="utf-8")):
            if not m.group(2).startswith("_"):
                widgets.setdefault(m.group(2), set()).add(os.path.basename(p))
    choques = []
    for clave, duenos in widgets.items():
        for f in PAGINAS + CALCULOS:
            if os.path.basename(f) in duenos:
                continue
            if re.search(r"[\"']%s[\"']" % re.escape(clave), Path(f).read_text(encoding="utf-8")):
                choques.append((clave, sorted(duenos), os.path.basename(f)))
    assert choques == [], choques


def test_manual_del_asistente_lo_explica():
    kb = (RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    seccion = kb[kb.index("## 100."):]
    for texto in ("N_strings por tracker", "Motor IV", "Strings en paralelo", "todas las páginas"):
        assert texto in seccion, texto
    assert "PVsyst" not in seccion
