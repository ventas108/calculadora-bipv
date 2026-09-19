# -*- coding: utf-8 -*-
"""📊 Producción debe bloquear la simulación (y limpiar resultados
persistidos) cuando el diseño eléctrico confirmado en 📐 Dimensionamiento
quedó desactualizado (`diseno_electrico_confirmado()["vigente"] is False`),
no solo cuando `_compat_inversor_ok` es False.

Bug real (auditoría 18-sep-2026): `_compat_inversor_ok` se recalcula en esta
misma página con el panel/inversor EN VIVO (el usuario puede cambiarlos aquí
mismo, ver `st.session_state["inversor_nombre_dim"] = inversor_nombre`)
contra `N_serie`/`N_str_tr_usado` CONGELADOS del último diseño confirmado --
por lo tanto puede dar "compatible" por coincidencia aunque
`diseno_electrico_confirmado()["vigente"]` sea False. Antes de este fix, el
botón "▶️ Simular producción anual" solo miraba `_compat_inversor_ok`, así
que un diseño vencido con compatibilidad "casual" sí lograba persistir
`E_ac_anual_kWh`/`produccion_ok` -- exactamente lo que la alerta de vigencia
(`_diseno_cfg["aviso"]`) advertía que no debía pasar. Mismo patrón AST/
substring que el resto de tests de páginas de este repo."""
import ast
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAG_PRODUCCION = os.path.join(_ROOT, "pages", "6_📊_Produccion.py")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_pagina_produccion_tiene_sintaxis_valida():
    ast.parse(_leer(_PAG_PRODUCCION))


def test_pagina_produccion_bloquea_simulacion_si_diseno_no_vigente():
    src = _leer(_PAG_PRODUCCION)
    # El gate que limpia session_state y llama st.stop() debe activarse
    # también cuando el diseño confirmado no está vigente, no solo cuando
    # la compatibilidad eléctrica falla.
    assert 'if btn_sim and (not _compat_inversor_ok or not _diseno_cfg["vigente"]):' in src


def test_pagina_produccion_explica_bloqueo_por_diseno_vencido():
    src = _leer(_PAG_PRODUCCION)
    assert "quedó desactualizado" in src
    assert 'if not _diseno_cfg["vigente"]:' in src
