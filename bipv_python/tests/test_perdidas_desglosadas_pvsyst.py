# -*- coding: utf-8 -*-
"""`perdidas_desglosadas()` extendida con nombres estilo Loss Diagram de
PVsyst (1-sep-2026, pedido explícito del usuario tras analizar Kadir et al.
2023 -- ver DIAGNOSTICO_LOSS_DIAGRAM_PVSYST.md).

Los números de este archivo son sintéticos y redondos a propósito -- esto
prueba la ARITMÉTICA/bookkeeping de la función (que no cuente una pérdida
dos veces al insertar las filas IAM/soiling), no una afirmación física; la
física de IAM/soiling/SDM ya tiene su propia cobertura real en
test_motor_optico.py y test_modelo_iv.py."""
from calculos.produccion import perdidas_desglosadas


def _res_sintetico():
    return {
        "P_stc_kW":             10.0,
        "E_dc_anual_kWh":       8800.0,
        "perdida_temp_kWh":     300.0,
        "perdida_inv_kWh":      200.0,
        "E_ac_sin_recorte_kWh": 8600.0,
        "E_ac_anual_kWh":       8500.0,
        "perdida_clipping_kWh": 100.0,
        "horas_con_clipping":   50,
        "Tk_gamma_pct":         -0.214,
    }


def _motor_optico_summary_sintetico():
    return {
        "poa_optica_anual_kWh_m2":    950.0,   # POA bruta 1000 → post-IAM 950
        "poa_post_soil_anual_kWh_m2": 900.0,   # post-IAM 950 → post-soiling 900
        "perdida_iam_kWh_m2":         50.0,
        "perdida_soil_kWh_m2":        50.0,
        "f_iam_prom":  0.95,
        "f_soil_prom": 0.95,
    }


def test_sin_motor_optico_summary_queda_identica_a_la_tabla_original():
    # Compatibilidad hacia atrás: sin el resumen del Motor Óptico, la tabla
    # se comporta exactamente igual que antes de este cambio.
    df = perdidas_desglosadas(_res_sintetico(), poa_bruta_kWh_m2=1000.0)
    etapas = df["Etapa"].tolist()
    assert not any("①a" in e or "①b" in e for e in etapas)
    fila_sdm = df[df["Etapa"].str.startswith("②")].iloc[0]
    # Sin cascada óptica: el efecto SDM se mide contra la POA BRUTA completa.
    assert fila_sdm["Δ kWh"] == 8800.0 - 10000.0


def test_diccionario_vacio_de_motor_optico_se_comporta_como_sin_el():
    df_none  = perdidas_desglosadas(_res_sintetico(), 1000.0, None)
    df_vacio = perdidas_desglosadas(_res_sintetico(), 1000.0, {})
    assert df_none["Etapa"].tolist() == df_vacio["Etapa"].tolist()


def test_con_motor_optico_inserta_filas_iam_y_soiling():
    df = perdidas_desglosadas(
        _res_sintetico(), poa_bruta_kWh_m2=1000.0,
        motor_optico_summary=_motor_optico_summary_sintetico(),
    )
    etapas = df["Etapa"].tolist()
    assert any(e.startswith("①a") for e in etapas)
    assert any(e.startswith("①b") for e in etapas)

    fila_iam = df[df["Etapa"].str.startswith("①a")].iloc[0]
    assert fila_iam["kWh"] == 9500.0          # P_stc(10) × POA post-IAM(950)
    assert fila_iam["Δ kWh"] == -500.0        # -P_stc(10) × pérdida_iam(50)

    fila_soil = df[df["Etapa"].str.startswith("①b")].iloc[0]
    assert fila_soil["kWh"] == 9000.0         # P_stc(10) × POA post-soiling(900)
    assert fila_soil["Δ kWh"] == -500.0


def test_efecto_sdm_no_cuenta_iam_soiling_dos_veces():
    # El hueco que este cambio corrige: antes de esto, si alguien hubiera
    # sumado IAM+soiling+SDM comparando siempre contra la POA bruta, IAM y
    # soiling habrían quedado contados una vez en sus propias filas Y otra
    # vez escondidos dentro del delta de SDM (que ya venía con esas pérdidas
    # incluidas porque el SDM corre sobre la POA YA corregida).
    df = perdidas_desglosadas(
        _res_sintetico(), poa_bruta_kWh_m2=1000.0,
        motor_optico_summary=_motor_optico_summary_sintetico(),
    )
    fila_sdm = df[df["Etapa"].str.startswith("②")].iloc[0]
    # Referencia correcta: POA POST-soiling (900×10=9000), no la bruta (10000).
    assert fila_sdm["Δ kWh"] == 8800.0 - 9000.0
    assert fila_sdm["Δ kWh"] != 8800.0 - 10000.0  # el bug que se evita


def test_porcentaje_de_e_ref_sigue_normalizado_contra_la_bruta():
    # El % de cada fila debe seguir siendo relativo al total original
    # (equivalente al "% of GlobHor" que usa PVsyst en su propio diagrama),
    # no al sub-total de la etapa anterior.
    df = perdidas_desglosadas(
        _res_sintetico(), poa_bruta_kWh_m2=1000.0,
        motor_optico_summary=_motor_optico_summary_sintetico(),
    )
    fila_iam = df[df["Etapa"].str.startswith("①a")].iloc[0]
    assert fila_iam["% de E_ref"] == 5.0   # 500 / 10000 × 100


def _res_sintetico_con_split_temp():
    res = _res_sintetico()
    # Con motor_optico_summary sintético, ref_sdm (POA post-IAM+soiling) =
    # P_stc(10) × 900 = 9000. E_dc_a_T25_kWh entre ese punto y E_dc_anual
    # (8800) simula un caso real: pequeña pérdida de linealidad a baja luz
    # Y pérdida neta de temperatura (clima cálido) -- ambas negativas aquí,
    # pero la aritmética es la misma con signos mixtos (clima frío = ganancia).
    res["E_dc_a_T25_kWh"] = 8950.0
    return res


def test_sin_e_dc_a_t25_no_inserta_filas_de_split_irradiancia_temperatura():
    df = perdidas_desglosadas(
        _res_sintetico(), 1000.0, _motor_optico_summary_sintetico(),
    )
    etapas = df["Etapa"].tolist()
    assert not any(e.startswith("②a") or e.startswith("②b") for e in etapas)


def test_con_e_dc_a_t25_inserta_filas_2a_2b_con_valores_correctos():
    df = perdidas_desglosadas(
        _res_sintetico_con_split_temp(), 1000.0, _motor_optico_summary_sintetico(),
    )
    fila_irr = df[df["Etapa"].str.startswith("②a")].iloc[0]
    assert fila_irr["kWh"] == 8950.0
    assert fila_irr["Δ kWh"] == 8950.0 - 9000.0   # ref_sdm = P_stc(10) × 900

    fila_temp = df[df["Etapa"].str.startswith("②b")].iloc[0]
    assert fila_temp["kWh"] == 8800.0
    assert fila_temp["Δ kWh"] == 8800.0 - 8950.0


def test_2a_mas_2b_reconcilian_exacto_con_el_delta_de_la_fila_2():
    # La descomposición no puede perder ni inventar energía: la suma de los
    # dos deltas nuevos debe dar EXACTO el delta ya existente de la fila ②.
    df = perdidas_desglosadas(
        _res_sintetico_con_split_temp(), 1000.0, _motor_optico_summary_sintetico(),
    )
    delta_2  = df[df["Etapa"].str.startswith("②") & ~df["Etapa"].str.startswith("②a")
                  & ~df["Etapa"].str.startswith("②b")]["Δ kWh"].iloc[0]
    delta_2a = df[df["Etapa"].str.startswith("②a")]["Δ kWh"].iloc[0]
    delta_2b = df[df["Etapa"].str.startswith("②b")]["Δ kWh"].iloc[0]
    assert delta_2a + delta_2b == delta_2


def test_split_funciona_tambien_sin_motor_optico_summary():
    # El split irradiancia/temperatura es independiente del split IAM/soiling
    # -- debe funcionar aunque Motor Óptico no haya corrido (ref_sdm = bruta).
    res = _res_sintetico()
    res["E_dc_a_T25_kWh"] = 9700.0   # entre ref_dc(10000) y E_dc_anual(8800)
    df = perdidas_desglosadas(res, poa_bruta_kWh_m2=1000.0)
    fila_irr = df[df["Etapa"].str.startswith("②a")].iloc[0]
    assert fila_irr["Δ kWh"] == 9700.0 - 10000.0


def test_produccion_iv_tambien_expone_e_dc_a_t25_kwh():
    # calculos.produccion_iv debe exponer el mismo campo que
    # calculos.produccion, para que la tabla se pueda desglosar sin importar
    # si Producción corrió en modo SDM simple o Motor IV.
    import inspect
    import calculos.produccion_iv as produccion_iv
    src = inspect.getsource(produccion_iv.simular_produccion_iv)
    assert '"E_dc_a_T25_kWh"' in src


def test_tabla_final_sigue_llegando_al_mismo_e_ac_con_o_sin_desglose():
    # El desglose es solo de presentación -- el resultado final (E_ac) no
    # puede cambiar según se pase o no el resumen del Motor Óptico.
    res = _res_sintetico()
    df_con    = perdidas_desglosadas(res, 1000.0, _motor_optico_summary_sintetico())
    df_sin    = perdidas_desglosadas(res, 1000.0, None)
    fila_con  = df_con[df_con["Etapa"].str.startswith("⑤")].iloc[0]
    fila_sin  = df_sin[df_sin["Etapa"].str.startswith("⑤")].iloc[0]
    assert fila_con["kWh"] == fila_sin["kWh"] == res["E_ac_anual_kWh"]
