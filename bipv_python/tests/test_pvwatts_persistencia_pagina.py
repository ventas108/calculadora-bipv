# -*- coding: utf-8 -*-
"""
Fix real (6-sep-2026, auditoría pedida por el usuario): el aviso de
verificación cruzada PVGIS vs PVWatts (ya construido y probado el
4-sep-2026 en calculos/pvwatts_crosscheck.py) nunca se guardaba en
session_state -- solo aparecía en la misma ejecución del script donde se
presionaba "Descargar TMY", y desaparecía al recargar la página, cambiar de
pestaña, o restaurar desde caché, aunque la POA mostrada siguiera siendo la
misma. Tampoco llegaba nunca al Reporte PDF.

Mismo patrón AST/substring que el resto de tests de páginas de este repo
(ver test_pagina_produccion_loss_diagram.py) -- las páginas de Streamlit
requieren sesión/login para ejecutarse de verdad, así que se verifica la
estructura del código fuente en vez de correr la página completa.
"""
import ast
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAG_RECURSO_SOLAR = os.path.join(_ROOT, "pages", "2_☀️_Recurso_Solar.py")
_PAG_REPORTE_PDF = os.path.join(_ROOT, "pages", "10_📄_Reporte_PDF.py")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_paginas_tienen_sintaxis_valida():
    ast.parse(_leer(_PAG_RECURSO_SOLAR))
    ast.parse(_leer(_PAG_REPORTE_PDF))


def test_recurso_solar_persiste_el_resultado_de_pvwatts():
    src = _leer(_PAG_RECURSO_SOLAR)
    assert 'st.session_state["pvwatts_cross_check"] = {' in src


def test_recurso_solar_reusa_el_helper_en_ambas_ramas():
    # El helper debe llamarse tanto justo después de calcular (rama
    # if _descarga_btn) como al restaurar un resultado ya calculado (rama
    # elif recurso_solar_ok) -- si solo aparece una vez, el bug de
    # "desaparece al recargar" sigue vivo.
    src = _leer(_PAG_RECURSO_SOLAR)
    assert src.count("_mostrar_banner_pvwatts(") >= 2


def test_recurso_solar_valida_ciudad_y_orientacion_antes_de_reusar_pvwatts():
    # La rama de restauración no debe mostrar un resultado de PVWatts de
    # OTRA ciudad/orientación como si fuera el vigente.
    src = _leer(_PAG_RECURSO_SOLAR)
    idx_elif = src.index("elif st.session_state.get(\"recurso_solar_ok\")")
    bloque = src[idx_elif:idx_elif + 1500]
    assert 'tmy_ciudad") == ciudad' in bloque
    assert "tilt_fachada" in bloque
    assert "azimuth_fachada" in bloque


def test_pvwatts_cross_check_esta_en_las_2_listas_de_invalidacion():
    # Debe caducar junto con poa_df cuando cambian coordenadas (Proyecto) o
    # geometría (Recurso Solar) -- si no, quedaría mostrando una comparación
    # de un sitio/orientación distinto al vigente.
    src_recurso = _leer(_PAG_RECURSO_SOLAR)
    idx = src_recurso.index("_SOLAR_SS_KEYS = (")
    bloque = src_recurso[idx:idx + 600]
    assert '"pvwatts_cross_check"' in bloque

    ruta_invalidacion = os.path.join(_ROOT, "calculos", "invalidacion.py")
    src_inv = _leer(ruta_invalidacion)
    idx2 = src_inv.index("KEYS_RECURSO_SOLAR_POA = (")
    bloque2 = src_inv[idx2:idx2 + 500]
    assert '"pvwatts_cross_check"' in bloque2


def test_reporte_pdf_incluye_la_verificacion_cruzada_pvwatts():
    src = _leer(_PAG_REPORTE_PDF)
    assert 'st.session_state.get("pvwatts_cross_check")' in src
    assert "POA PVWatts (NREL/NLR)" in src


def test_reporte_pdf_valida_ciudad_y_orientacion_antes_de_incluir_pvwatts():
    # Mismo principio que la página: no mostrar en el informe una
    # comparación que no corresponde a la corrida vigente del reporte.
    src = _leer(_PAG_REPORTE_PDF)
    idx = src.index('_pvwatts_pdf = st.session_state.get("pvwatts_cross_check")')
    bloque = src[idx:idx + 500]
    assert 'tmy_ciudad") == st.session_state.get("tmy_ciudad")' in bloque
    assert 'tilt_fachada") == st.session_state.get("tilt_fachada")' in bloque
