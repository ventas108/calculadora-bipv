# -*- coding: utf-8 -*-
"""Prueba D8 en producción (26-sep-2026): al cargar un proyecto con
multi-superficie y abrir ☀️ Recurso Solar, el TMY se restaura desde el caché
de disco, se publica la multi-superficie y la página hace ``st.rerun()``.
El mensaje «📂 Estado multi-superficie restaurado…» se escribía ANTES del
rerun (y su marca se borraba), así que el usuario nunca lo veía.

Regla: antes de un ``st.rerun()`` no se muestra ni se consume la marca; el
mensaje se muestra en la ejecución siguiente (rama «resultado previo»).
Mismo patrón de fuente que ``test_pvwatts_persistencia_pagina.py``.
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAG = os.path.join(_ROOT, "pages", "2_☀️_Recurso_Solar.py")


def _src():
    with open(_PAG, encoding="utf-8") as f:
        return f.read()


def _bloque_auto_restore(src):
    ini = src.index("# ── Auto-restaurar desde caché de disco")
    fin = src.index("st.rerun()", ini)
    return src[ini:fin]


def test_auto_restore_no_consume_el_mensaje_antes_del_rerun():
    bloque = _bloque_auto_restore(_src())
    assert "_intentar_restaurar_multisuperficie(" in bloque
    assert "_mostrar_resultado_restauracion_multisuperficie(" not in bloque
    assert "st.info(" not in bloque


def test_rama_resultado_previo_muestra_la_restauracion_y_el_cache():
    src = _src()
    ini = src.index('elif st.session_state.get("recurso_solar_ok")')
    bloque = src[ini:src.index("\nelse:", ini)]
    assert "_mostrar_resultado_restauracion_multisuperficie()" in bloque
    assert "_solar_cache_msg" in bloque


def test_mensaje_de_cache_caduca_con_el_proyecto():
    ruta = os.path.join(_ROOT, "calculos", "proyectos_manager.py")
    with open(ruta, encoding="utf-8") as f:
        assert '"_solar_cache_msg"' in f.read()
