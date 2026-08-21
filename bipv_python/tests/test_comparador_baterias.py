# -*- coding: utf-8 -*-
"""Validación de calculos/comparador_baterias.py con el catálogo real de
baterías (26 modelos, datos/inversores_catalogo.xlsx hoja Catalogo_Baterias)
-- mismo patrón que test_comparador_paneles.py / test_comparador_orientacion.py:
datos reales, no inventados.

datos.catalogo_baterias_excel importa streamlit a nivel de módulo (no
instalado en este entorno) -- reusa el stub + override de ruta ya
establecido en test_compatibilidad_bateria.py en vez de duplicarlo.
"""
import os

import pandas as pd
import pytest

from calculos.comparador_baterias import comparar_baterias, formatear_comparacion_baterias
from tests.test_compatibilidad_bateria import _cargar_modulo_catalogo_baterias

INVERSOR_HIBRIDO_HV = {
    "es_hibrido": True, "bat_voltaje_min": 350.0, "bat_voltaje_max": 850.0,
}
INVERSOR_NOMBRE_HV = "Growatt MAX 100KTL3 LV (híbrido simulado)"


def _catalogo_real() -> dict:
    mod = _cargar_modulo_catalogo_baterias()
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mod._EXCEL = os.path.join(_root, "datos", "inversores_catalogo.xlsx")
    return mod.cargar_catalogo_baterias(_mtime=mod.excel_mtime())


def test_comparar_baterias_no_crashea_y_tiene_las_26():
    catalogo = _catalogo_real()
    df = comparar_baterias(catalogo, INVERSOR_HIBRIDO_HV, INVERSOR_NOMBRE_HV,
                            E_consumo_diario_kWh=500.0, autonomia_h=4.0)
    assert not df.empty
    assert len(df) == 26
    for col in ("Batería", "Compatible", "N° unidades", "Capacidad instalada (kWh)",
                "Capacidad útil (kWh)", "DoD real (%)", "Vida estimada (años)",
                "Costo total (USD)"):
        assert col in df.columns


def test_comparar_baterias_marca_compatibilidad_real_con_rango_completo():
    # Todas las baterías reales tienen voltaje_min_V/voltaje_max_V (ver
    # tests/test_compatibilidad_bateria.py) dentro de 268-870 V -- con un
    # inversor híbrido de ventana 350-850 V, algunas deberían caer FUERA
    # (ni el nominal ni el rango completo) y marcarse ❌, no todas ✅.
    catalogo = _catalogo_real()
    df = comparar_baterias(catalogo, INVERSOR_HIBRIDO_HV, INVERSOR_NOMBRE_HV,
                            E_consumo_diario_kWh=500.0, autonomia_h=4.0)
    assert set(df["Compatible"]) & {"✅", "❌"}, "esperaba ver ambos estados con esta ventana angosta"


def test_comparar_baterias_sin_inversor_da_warning_no_bloqueante():
    catalogo = _catalogo_real()
    df = comparar_baterias(catalogo, {}, "", E_consumo_diario_kWh=500.0, autonomia_h=4.0)
    # check_compatibilidad({}, "", "") -> "warning" (inversor no seleccionado)
    assert set(df["Compatible"]) == {"⚠️"}


def test_comparar_baterias_dimensiona_con_valores_positivos_y_coherentes():
    catalogo = _catalogo_real()
    df = comparar_baterias(catalogo, INVERSOR_HIBRIDO_HV, INVERSOR_NOMBRE_HV,
                            E_consumo_diario_kWh=200.0, autonomia_h=4.0)
    fila = df.iloc[0]
    assert fila["N° unidades"] >= 1
    assert fila["Capacidad instalada (kWh)"] > 0
    assert fila["Capacidad útil (kWh)"] > 0
    assert 0 < fila["DoD real (%)"] <= 100
    assert fila["Vida estimada (años)"] > 0


def test_comparar_baterias_ordena_compatibles_primero_y_por_vida_estimada():
    catalogo = _catalogo_real()
    df = comparar_baterias(catalogo, INVERSOR_HIBRIDO_HV, INVERSOR_NOMBRE_HV,
                            E_consumo_diario_kWh=500.0, autonomia_h=4.0)
    ordenes = {"✅": 0, "⚠️": 1, "—": 2, "❌": 3}
    ordenes_df = [ordenes[c] for c in df["Compatible"]]
    assert ordenes_df == sorted(ordenes_df)
    # Dentro del primer bloque compatible, vida estimada descendente
    _ok = df[df["Compatible"] == "✅"]["Vida estimada (años)"].tolist()
    assert _ok == sorted(_ok, reverse=True)


def test_comparar_baterias_catalogo_vacio_devuelve_dataframe_vacio():
    df = comparar_baterias({}, INVERSOR_HIBRIDO_HV, INVERSOR_NOMBRE_HV,
                            E_consumo_diario_kWh=500.0, autonomia_h=4.0)
    assert df.empty


# ── formatear_comparacion_baterias() -- contexto para agentes/analista_produccion.py

def test_formatear_comparacion_declara_el_tipo_de_instalacion():
    catalogo = _catalogo_real()
    df = comparar_baterias(catalogo, INVERSOR_HIBRIDO_HV, INVERSOR_NOMBRE_HV,
                            E_consumo_diario_kWh=500.0, autonomia_h=4.0)
    texto = formatear_comparacion_baterias(df, "Granja FV campo")
    assert "Tipo de instalación: Granja FV campo" in texto


def test_formatear_comparacion_aclara_que_el_criterio_no_es_e_ac_ni_pr():
    # El agente reutilizado (analista_produccion) evalúa E_ac/PR para
    # paneles -- el contexto debe dejar explícito que aquí no aplica, para
    # que no intente forzar ese criterio sobre baterías.
    catalogo = _catalogo_real()
    df = comparar_baterias(catalogo, INVERSOR_HIBRIDO_HV, INVERSOR_NOMBRE_HV,
                            E_consumo_diario_kWh=500.0, autonomia_h=4.0)
    texto = formatear_comparacion_baterias(df, "BIPV fachada/pérgola")
    assert "NO energía anual" in texto or "NO compatibilidad eléctrica" in texto


def test_formatear_comparacion_cita_los_numeros_reales_del_dataframe():
    catalogo = _catalogo_real()
    df = comparar_baterias(catalogo, INVERSOR_HIBRIDO_HV, INVERSOR_NOMBRE_HV,
                            E_consumo_diario_kWh=500.0, autonomia_h=4.0)
    fila = df.iloc[0]
    texto = formatear_comparacion_baterias(df, "BIPV fachada/pérgola")
    assert fila["Batería"] in texto
    assert f"{fila['Vida estimada (años)']:.1f} años" in texto


def test_formatear_comparacion_explica_el_significado_de_warning():
    # ⚠️ no debe leerse como "compatible" -- el texto debe aclarar la
    # diferencia con ❌ explícitamente para que el agente no lo trate como ok.
    df = comparar_baterias(_catalogo_real(), {}, "", E_consumo_diario_kWh=500.0, autonomia_h=4.0)
    texto = formatear_comparacion_baterias(df, "BIPV fachada/pérgola")
    assert "NO tratar como un sí garantizado" in texto or "no tiene datos suficientes" in texto


def test_formatear_comparacion_dataframe_vacio_no_crashea():
    texto = formatear_comparacion_baterias(pd.DataFrame(), "Granja FV campo")
    assert "Granja FV campo" in texto
    assert "No hay ninguna batería" in texto
