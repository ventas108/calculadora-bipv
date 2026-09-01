# -*- coding: utf-8 -*-
"""Diagrama Unifilar — integración en la página (Fase 4, 27-ago-2026).

Mismo patrón que test_pagina_ledger_auditoria.py: se audita el código
fuente vía AST/substring en vez de ejecutar Streamlit (más rápido, y no
depende de una sesión autenticada para llegar al código que nos interesa).
"""
import ast
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAG_UNIFILAR = os.path.join(_ROOT, "pages", "20_⚡_Diagrama_Unifilar.py")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_pagina_unifilar_tiene_sintaxis_valida():
    ast.parse(_leer(_PAG_UNIFILAR))


def test_pagina_unifilar_requiere_login():
    src = _leer(_PAG_UNIFILAR)
    assert "requerir_login()" in src


def test_pagina_unifilar_importa_el_ledger():
    src = _leer(_PAG_UNIFILAR)
    assert "from calculos import ledger_auditoria" in src


def test_pagina_unifilar_sella_con_tipo_diagrama_unifilar():
    src = _leer(_PAG_UNIFILAR)
    assert '"diagrama_unifilar"' in src
    assert "Sellar en el Ledger de Auditoría" in src


def test_pagina_unifilar_advierte_que_no_es_documento_certificado():
    # Limite declarado del modulo (ver calculos/diagrama_unifilar.py) debe
    # seguir visible en la UI, no solo en el docstring del modulo.
    src = _leer(_PAG_UNIFILAR)
    assert "No es un documento certificado" in src


def test_pagina_unifilar_auto_llena_bateria_y_multisuperficie():
    src = _leer(_PAG_UNIFILAR)
    assert "bateria_ok" in src
    assert "multisup_activo" in src
    assert "multisup_desglose" in src


def test_pagina_unifilar_reverifica_compatibilidad_bateria_en_vivo():
    # Hueco #2 (31-ago-2026): `bateria_ok` es una foto fija del inversor que
    # estaba seleccionado cuando se dio clic en "Dimensionar batería" en
    # 🔋 Baterías y Balance -- si el usuario cambia de inversor después en
    # 📐 Dimensionamiento, ese flag queda obsoleto y el diagrama afirmaba
    # "verificado" sin volver a comprobar nada. Corrección: re-correr
    # check_compatibilidad() aquí mismo, contra el inversor actual.
    src = _leer(_PAG_UNIFILAR)
    assert "from calculos.compatibilidad_bateria import check_compatibilidad" in src
    assert "check_compatibilidad(\n        bateria_dict, inversor_dict, inversor_nombre\n    )" in src
    # La leyenda vieja afirmaba la verificación de forma incondicional citando
    # a la página 11 -- ya no debe estar: el resultado ahora depende de la
    # re-verificación en vivo hecha aquí mismo, no de lo que se hizo en 🔋.
    assert "ver ⚙️ Compatibilidad en" not in src


def test_pagina_unifilar_advierte_si_bateria_actual_no_es_compatible():
    src = _leer(_PAG_UNIFILAR)
    assert '_compat_estado_vivo == "error"' in src
    assert "no está " in src
    assert "verificada** con los datos actuales" in src


def test_pagina_unifilar_expone_detalle_retie():
    # Contenido extraído (27-ago-2026) del script RETIE que aportó el
    # usuario -- protecciones detalladas, equipotencialidad, notas y
    # pendientes, pasados al config universal (no hardcodeados).
    src = _leer(_PAG_UNIFILAR)
    assert "equipotencialidad=equipotencialidad_val" in src
    assert "detalle_proteccion_dc=detalle_dc_val" in src
    assert "detalle_proteccion_ac=detalle_ac_val" in src
    assert "notas_retie=notas_retie_val" in src
    assert "pendientes_retie=pendientes_retie_val" in src
