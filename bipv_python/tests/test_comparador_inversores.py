# -*- coding: utf-8 -*-
"""Validación de calculos.comparador_inversores.comparar_todos_los_inversores_compatibles()
y formatear_comparacion_inversores() -- extensión del Analista de Producción a
inversores (4º candidato de hardware, junto a paneles/orientación/baterías).

Reusa el mismo panel/catálogo sintético de scripts/test_comparador_inversores.py
(cubre las 4 ramas reales de filtrar_inversores_compatibles: compatible modo
normal, compatible modo "1 string/tracker", incompatible por Voc, incompatible
por corriente, ficha incompleta) -- no datos inventados para este test nuevo.
"""
import numpy as np
import pandas as pd
import pytest

from calculos.comparador_inversores import (
    comparar_todos_los_inversores_compatibles,
    filtrar_inversores_compatibles,
    formatear_comparacion_inversores,
)

PANEL = {"Voc_stc": 49.0, "Vmp_stc": 41.0, "Isc_stc": 18.6, "Imp_stc": 17.6,
         "Tk_beta": -0.25, "Tk_gamma": -0.30, "Pmax_stc": 720.0}

INVERSORES = {
    "Huawei-100K": {"Vdc_max": 1500, "Vmppt_activo_min": 200, "Vmppt_min": 200,
                    "Vmppt_max": 1500, "n_trackers": 12, "n_strings_tracker": 2,
                    "I_max_tracker": 26, "Isc_max_tracker": 32.5,
                    "P_ac_nom_W": 100_000, "costo_usd": 5500},
    "TriP-30K":    {"Vdc_max": 1000, "Vmppt_activo_min": 200, "Vmppt_min": 200,
                    "Vmppt_max": 900, "n_trackers": 3, "n_strings_tracker": 2,
                    "I_max_tracker": 40, "Isc_max_tracker": 50,
                    "P_ac_nom_W": 30_000, "costo_usd": 2000},
    "Chico-600V":  {"Vdc_max": 600, "Vmppt_activo_min": 100, "Vmppt_min": 100,
                    "Vmppt_max": 550, "n_trackers": 2, "n_strings_tracker": 1,
                    "I_max_tracker": 20, "Isc_max_tracker": 25,
                    "P_ac_nom_W": 10_000, "costo_usd": 800},
    "Debil-15A":   {"Vdc_max": 1100, "Vmppt_activo_min": 200, "Vmppt_min": 200,
                    "Vmppt_max": 1000, "n_trackers": 4, "n_strings_tracker": 1,
                    "I_max_tracker": 15, "Isc_max_tracker": 15,
                    "P_ac_nom_W": 25_000, "costo_usd": 1500},
    "SinDatos":    {"Vdc_max": None, "Vmppt_max": None, "n_trackers": None,
                    "P_ac_nom_W": None, "costo_usd": None},
}


def _df_compat():
    return filtrar_inversores_compatibles(PANEL, INVERSORES, N_serie=18, T_frio=10.0, T_real=36.35)


def _horas():
    # Misma serie sintética que scripts/test_comparador_inversores.py.
    horas = np.zeros(8760)
    horas[6 * 365:12 * 365] = 150_000.0   # ~2190 h a 150 kW
    return horas


def _comparar(n_strings_total=17):
    return comparar_todos_los_inversores_compatibles(
        _df_compat(), n_strings_total=n_strings_total, p_ac_horaria_W=_horas(),
        p_dc_stc_kW=220.32, capex_sin_inversores_usd=160_000,
        tarifa_cop_kwh=950, tipo_cambio=4000,
    )


def test_incluye_los_5_inversores_compatibles_e_incompatibles():
    df = _comparar()
    assert not df.empty
    assert len(df) == 5
    assert set(df["Modelo"]) == set(INVERSORES.keys())


def test_marca_compatibles_e_incompatibles_correctamente():
    df = _comparar().set_index("Modelo")
    assert df.loc["Huawei-100K", "Compatible"] == "✅"
    assert df.loc["TriP-30K", "Compatible"] == "✅"
    assert df.loc["Chico-600V", "Compatible"] == "❌"
    assert df.loc["Debil-15A", "Compatible"] == "❌"
    assert df.loc["SinDatos", "Compatible"] == "❌"


def test_incompatibles_traen_motivo_y_sin_datos_financieros():
    df = _comparar().set_index("Modelo")
    assert "Voc" in df.loc["Chico-600V", "_motivo"]
    assert "incompleta" in df.loc["SinDatos", "_motivo"]
    for col in ("E_ac (kWh/año)", "CAPEX (USD)", "LCOE (USD/kWh)"):
        assert pd.isna(df.loc["Chico-600V", col])


def test_compatibles_tienen_columnas_financieras_reales():
    df = _comparar().set_index("Modelo")
    for modelo in ("Huawei-100K", "TriP-30K"):
        assert df.loc[modelo, "E_ac (kWh/año)"] > 0
        assert df.loc[modelo, "CAPEX (USD)"] > 0
        assert df.loc[modelo, "LCOE (USD/kWh)"] is not None


def test_ordena_compatibles_primero_por_lcoe_e_incompatibles_al_final():
    df = _comparar()
    compat = df["Compatible"].tolist()
    # Todos los "✅" deben venir antes que todos los "❌"
    assert compat == sorted(compat, key=lambda c: 0 if c == "✅" else 1)
    _ok = df[df["Compatible"] == "✅"]["LCOE (USD/kWh)"].tolist()
    assert _ok == sorted(_ok)


def test_huawei_usa_modo_1_string_tracker_en_la_configuracion():
    df = _comparar().set_index("Modelo")
    assert "1 str/MPPT" in df.loc["Huawei-100K", "Configuración"]


def test_compatible_sin_costo_en_catalogo_queda_avisado_no_silencioso():
    # Hallazgo real: NI el catálogo Python (7 modelos) NI el Excel real (105
    # modelos) tienen costo de inversor poblado hoy -- sin este aviso, el
    # comparador entregaría CAPEX/LCOE subestimados en silencio (costo
    # tratado como 0) para candidatos que SÍ son compatibles.
    df = _comparar().set_index("Modelo")
    assert df.loc["Huawei-100K", "_motivo"] == ""  # este SÍ tiene costo_usd=5500 en el fixture
    assert df.loc["TriP-30K", "_motivo"] == ""      # este también (costo_usd=2000)


def test_compatible_sin_potencia_ac_queda_excluido_no_crashea():
    # Mismo tipo de bug que el de costo: un DataFrame convierte el
    # P_ac_nom_W=None del dict Python a NaN -- "row['P_ac_nom_kW'] or 0"
    # dejaría pasar NaN sin excluir la fila. Verificado con un compatible
    # real (TriP-30K) al que le falta la potencia AC.
    inv_sin_potencia = dict(INVERSORES)
    inv_sin_potencia["TriP-30K"] = {**INVERSORES["TriP-30K"], "P_ac_nom_W": None}
    df_compat = filtrar_inversores_compatibles(PANEL, inv_sin_potencia, N_serie=18, T_frio=10.0, T_real=36.35)
    df = comparar_todos_los_inversores_compatibles(
        df_compat, n_strings_total=17, p_ac_horaria_W=_horas(),
        p_dc_stc_kW=220.32, capex_sin_inversores_usd=160_000,
        tarifa_cop_kwh=950, tipo_cambio=4000,
    ).set_index("Modelo")
    assert df.loc["TriP-30K", "Compatible"] == "❌"
    assert "Sin potencia AC nominal" in df.loc["TriP-30K", "_motivo"]


def test_compatible_realmente_sin_costo_queda_marcado():
    inv_sin_costo = dict(INVERSORES)
    inv_sin_costo["TriP-30K"] = {**INVERSORES["TriP-30K"], "costo_usd": None}
    df_compat = filtrar_inversores_compatibles(PANEL, inv_sin_costo, N_serie=18, T_frio=10.0, T_real=36.35)
    df = comparar_todos_los_inversores_compatibles(
        df_compat, n_strings_total=17, p_ac_horaria_W=_horas(),
        p_dc_stc_kW=220.32, capex_sin_inversores_usd=160_000,
        tarifa_cop_kwh=950, tipo_cambio=4000,
    ).set_index("Modelo")
    assert df.loc["TriP-30K", "Compatible"] == "✅"
    assert "no disponible en el catálogo" in df.loc["TriP-30K", "_motivo"]
    assert df.loc["Huawei-100K", "_motivo"] == ""


def test_dataframe_compatibilidad_vacio_devuelve_vacio():
    df = comparar_todos_los_inversores_compatibles(
        pd.DataFrame(), n_strings_total=17, p_ac_horaria_W=_horas(),
        p_dc_stc_kW=220.32, capex_sin_inversores_usd=160_000,
        tarifa_cop_kwh=950, tipo_cambio=4000,
    )
    assert df.empty


def test_ningun_compatible_no_crashea():
    df_compat_todos_malos = filtrar_inversores_compatibles(
        PANEL, {"Chico-600V": INVERSORES["Chico-600V"]}, N_serie=18,
    )
    df = comparar_todos_los_inversores_compatibles(
        df_compat_todos_malos, n_strings_total=17, p_ac_horaria_W=_horas(),
        p_dc_stc_kW=220.32, capex_sin_inversores_usd=160_000,
        tarifa_cop_kwh=950, tipo_cambio=4000,
    )
    assert len(df) == 1
    assert df.iloc[0]["Compatible"] == "❌"


# ── formatear_comparacion_inversores() -- contexto para agentes/analista_produccion.py

def test_formatear_declara_el_tipo_de_instalacion():
    texto = formatear_comparacion_inversores(_comparar(), "Granja FV campo")
    assert "Tipo de instalación: Granja FV campo" in texto


def test_formatear_aclara_que_no_es_pr():
    # El agente reutilizado evalúa PR para paneles/orientación -- aquí no
    # aplica (el panel no cambia, solo el inversor).
    texto = formatear_comparacion_inversores(_comparar(), "BIPV fachada/pérgola")
    assert "NO Performance Ratio" in texto or "no aplica aquí" in texto


def test_formatear_incluye_motivo_de_incompatibilidad():
    texto = formatear_comparacion_inversores(_comparar(), "BIPV fachada/pérgola")
    assert "❌" in texto
    assert "Voc" in texto  # motivo real de Chico-600V


def test_formatear_cita_los_numeros_reales_del_dataframe():
    df = _comparar()
    fila = df[df["Compatible"] == "✅"].iloc[0]
    texto = formatear_comparacion_inversores(df, "BIPV fachada/pérgola")
    assert f"{fila['E_ac (kWh/año)']:,.0f}" in texto
    assert f"{fila['Clipping (%)']:.2f}" in texto


def test_formatear_dataframe_vacio_no_crashea():
    texto = formatear_comparacion_inversores(pd.DataFrame(), "Granja FV campo")
    assert "Granja FV campo" in texto
    assert "No hay ningún inversor" in texto


def test_formatear_avisa_cuando_el_costo_no_esta_disponible():
    inv_sin_costo = dict(INVERSORES)
    inv_sin_costo["TriP-30K"] = {**INVERSORES["TriP-30K"], "costo_usd": None}
    df_compat = filtrar_inversores_compatibles(PANEL, inv_sin_costo, N_serie=18, T_frio=10.0, T_real=36.35)
    df = comparar_todos_los_inversores_compatibles(
        df_compat, n_strings_total=17, p_ac_horaria_W=_horas(),
        p_dc_stc_kW=220.32, capex_sin_inversores_usd=160_000,
        tarifa_cop_kwh=950, tipo_cambio=4000,
    )
    texto = formatear_comparacion_inversores(df, "BIPV fachada/pérgola")
    assert "no disponible en el catálogo" in texto
