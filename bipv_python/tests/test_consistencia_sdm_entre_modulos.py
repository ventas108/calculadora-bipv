# -*- coding: utf-8 -*-
"""Consistencia cruzada del SDM entre sus 5 implementaciones (2026-08-25).

Hallazgo de la auditoría del 25-ago-2026 (PR #38): el modelo Rsh exponencial
NO vivía en un solo lugar -- estaba copiado y pegado en calculos/modelo_iv.py,
produccion.py, produccion_iv.py, mismatch_bypass.py y mppt_combinado.py, y
las 5 copias tenían el MISMO bug (Rsh sin saturar). Se corrigió centralizando
la fórmula en calculos.modelo_iv.calcular_rsh_cdte() y haciendo que las otras
4 la llamen en vez de reimplementarla.

Este archivo es la salvaguarda para que esa clase de bug -- "una fórmula
física se corrige en un lugar pero no en sus copias" -- no pueda volver a
colarse en silencio: verifica que, para el MISMO panel/irradiancia/
temperatura, las 5 implementaciones den el MISMO resultado dentro de una
tolerancia numérica estrecha (no de calibración -- todas deberían coincidir
casi al bit, porque usan pvlib.pvsystem.singlediode(method='lambertw') con
los mismos parámetros derivados). Si en el futuro alguien cambia una de las
5 sin actualizar las demás, este test lo revienta de inmediato.

Extendido el 1-sep-2026 con XTP_50_17B (Poli-Si): el mismo modelo Rsh
exponencial CdTe se aplicaba SIN filtrar tecnología en las 5 implementaciones
-- bug real encontrado comparando contra PVsyst con este panel real (base de
datos original de PVsyst, verificado con un reporte real de simulación). El
panel CdTe (ASP_ST1_T40) sigue debiendo dar el mismo resultado exacto que
antes (el modelo exponencial SÍ le corresponde); el de silicio ahora debe
usar el Rsh estándar de pvlib en las 5 implementaciones por igual.
"""
import numpy as np
import pytest

from calculos.modelo_iv import resolver_curva_iv, trasladar_parametros_gt
from calculos.produccion import _calcular_pmax_vectorizado
from calculos.produccion_iv import _pmp_iv_vectorizado
from calculos.mismatch_bypass import _sdm_vectorizado
from calculos.mppt_combinado import _params_grupo
from calculos.modelo_jrc_huld import potencia_jrc
from datos.tecnologias_bipv import ASP_ST1_T40

# G >= 5 W/m² para evitar la zona de apagado nocturno (cada módulo la trata
# un poco distinto: <5 → 0 exacto), y una mezcla de irradiancias baja/media/
# alta/STC para cubrir el rango completo de la curva de Rsh saturada.
G_PRUEBA = np.array([50.0, 100.0, 300.0, 700.0, 1000.0])
T_PRUEBA = 25.0   # todas las funciones vectorizadas usan T uniforme aquí

# XTP 50-17B (Sun Tech Solar, Si-poly) -- panel REAL de la base de datos
# original de PVsyst, extraído de un reporte de simulación real corrido por
# el usuario (1-sep-2026). Parámetros SDM: mismo ajuste Batzelis on-demand
# que usa calculos.modelo_iv.estimar_sdm_desde_ficha() para cualquier panel
# real del catálogo Excel sin SDM precalibrado.
XTP_50_17B = {
    "nombre": "XTP 50-17B", "fabricante": "Sun Tech Solar", "tecnologia": "Poli-Si",
    "Voc_stc": 21.50, "Isc_stc": 3.300, "Vmp_stc": 17.30, "Imp_stc": 2.850,
    "Pmax_stc": 50.0, "Tk_beta": -0.34, "Tk_alfa": 0.04, "Tk_gamma": -0.45,
    "I_L_ref": 3.3280621683489193, "I_o_ref": 5.5322736788824886e-11,
    "R_s": 0.5247000612677759, "R_sh_ref": 61.70265179277618,
    "a_ref": 33.71514270005188, "N_s": 36, "gamma_ref": 33.71514270005188/36,
    "NOCT": 45.0,
}

_PANELES_PRUEBA = {"CdTe (ASP_ST1_T40)": ASP_ST1_T40, "Poli-Si (XTP_50_17B)": XTP_50_17B}


@pytest.mark.parametrize("nombre_panel,panel", _PANELES_PRUEBA.items())
def test_pmax_identico_entre_modelo_iv_produccion_produccion_iv_y_bypass(nombre_panel, panel):
    # CdTe (2-sep-2026, ver DIAGNOSTICO_JRC_HULD_PRIMARIO_CDTE.md): produccion.py
    # deliberadamente YA NO usa el SDM para CdTe -- usa JRC/Huld como motor
    # primario de energía (evidencia real: correlación con PVsyst 8.1.5). Este
    # test verifica esa divergencia INTENCIONAL para produccion.py, y sigue
    # exigiendo igualdad exacta para produccion_iv.py/mismatch_bypass.py, que
    # necesitan la curva I-V completa y siguen exclusivamente en el SDM.
    T_arr = np.full_like(G_PRUEBA, T_PRUEBA)
    pmax_modelo_iv = np.array([
        resolver_curva_iv(float(g), T_PRUEBA, panel, n_puntos=0)["Pmax"]
        for g in G_PRUEBA
    ])
    pmax_produccion    = _calcular_pmax_vectorizado(G_PRUEBA, T_arr, panel)
    pmax_produccion_iv = _pmp_iv_vectorizado(G_PRUEBA, T_arr, panel)
    pmax_bypass, _, _, _ = _sdm_vectorizado(G_PRUEBA, T_arr, panel)

    if nombre_panel == "CdTe (ASP_ST1_T40)":
        pmax_jrc = potencia_jrc(G_PRUEBA, T_arr, float(panel["Pmax_stc"]), tecnologia="CdTe")
        np.testing.assert_allclose(pmax_produccion, pmax_jrc, rtol=1e-9,
                                   err_msg="produccion.py CdTe diverge de JRC/Huld (motor primario esperado)")
    else:
        np.testing.assert_allclose(pmax_produccion, pmax_modelo_iv, rtol=1e-6,
                                   err_msg=f"produccion.py diverge de modelo_iv.py ({nombre_panel})")
    np.testing.assert_allclose(pmax_produccion_iv, pmax_modelo_iv, rtol=1e-6,
                               err_msg=f"produccion_iv.py diverge de modelo_iv.py ({nombre_panel})")
    np.testing.assert_allclose(pmax_bypass, pmax_modelo_iv, rtol=1e-6,
                               err_msg=f"mismatch_bypass.py diverge de modelo_iv.py ({nombre_panel})")


@pytest.mark.parametrize("nombre_panel,panel", _PANELES_PRUEBA.items())
def test_parametros_sdm_identicos_entre_modelo_iv_y_mppt_combinado(nombre_panel, panel):
    # _params_grupo() con N_serie=1, N_paralelo=1 debe reducirse EXACTO a
    # los parámetros de un solo módulo (sin escalar) -- mismos que
    # trasladar_parametros_gt() para el mismo G/T/panel.
    for g in G_PRUEBA:
        I_L_ref, I_o_ref, R_s_ref, R_sh_ref, nNsVth_ref = trasladar_parametros_gt(
            float(g), T_PRUEBA, panel)
        I_L_g, I_o_g, R_s_g, R_sh_g, nNsVth_g, _d2mutau_g, _NsVbi_g = _params_grupo(
            np.array([g]), np.array([T_PRUEBA]), panel, n_serie=1, n_paralelo=1)

        assert I_L_g[0]    == pytest.approx(I_L_ref, rel=1e-6), nombre_panel
        assert I_o_g[0]    == pytest.approx(I_o_ref, rel=1e-6), nombre_panel
        assert R_s_g[0]    == pytest.approx(R_s_ref, rel=1e-6), nombre_panel
        assert R_sh_g[0]   == pytest.approx(R_sh_ref, rel=1e-6), nombre_panel
        assert nNsVth_g[0] == pytest.approx(nNsVth_ref, rel=1e-6), nombre_panel


def test_las_5_implementaciones_centralizan_en_trasladar_parametros_gt():
    # Salvaguarda directa contra el bug original ("una fórmula física se
    # corrige en un lugar pero no en sus copias"): desde la migración al
    # motor PVsyst v6 (2-sep-2026, ver DIAGNOSTICO_MOTOR_PVSYST.md), las 4
    # implementaciones fuera de modelo_iv.py NO reimplementan la llamada a
    # calcparams_pvsyst. Este test falla de inmediato si alguna vuelve a
    # traer su propia copia de la fórmula.
    #
    # Centralización adicional (2-sep-2026, ver
    # DIAGNOSTICO_RECOMBINACION_CDTE.md): produccion.py y produccion_iv.py
    # solo necesitan Pmax, así que llaman a
    # calculos.modelo_iv.calcular_pmax_vectorizado() (que internamente llama
    # trasladar_parametros_gt() Y decide si usar bishop88_mpp para el
    # término de recombinación PVsyst/Merten 1998). mismatch_bypass.py y
    # mppt_combinado.py necesitan el tuple completo (I_L, I_o, Rs, Rsh,
    # nNsVth) para su propia lógica (bypass diodes / malla MPPT
    # compartido), así que siguen llamando trasladar_parametros_gt()
    # directo.
    import inspect

    import calculos.produccion as produccion
    import calculos.produccion_iv as produccion_iv
    import calculos.mismatch_bypass as mismatch_bypass
    import calculos.mppt_combinado as mppt_combinado

    assert produccion.calcular_pmax_vectorizado is not None
    assert produccion_iv.calcular_pmax_vectorizado is not None
    assert mismatch_bypass.trasladar_parametros_gt is not None
    assert mppt_combinado.trasladar_parametros_gt is not None

    for modulo in (produccion, produccion_iv, mismatch_bypass, mppt_combinado):
        fuente = inspect.getsource(modulo)
        assert "calcparams_pvsyst" not in fuente, (
            f"{modulo.__name__} parece llamar a calcparams_pvsyst() por su "
            "cuenta en vez de usar trasladar_parametros_gt() -- eso es "
            "exactamente el bug original (fórmula duplicada en 5 lugares)."
        )
        assert "calcparams_desoto" not in fuente, (
            f"{modulo.__name__} todavía usa el motor De Soto 2006 -- "
            "debería centralizar en trasladar_parametros_gt() (PVsyst v6)."
        )


def test_calidad_y_mismatch_iguales_en_los_dos_motores():
    """Spec 05/calidad-y-mismatch (29-sep-2026): la «Calidad del módulo» y el
    «Mismatch» se aplican en cadena, Pmax × (1 − calidad) × (1 − mismatch), y
    los dos motores de Producción deben quitar la misma fracción de la energía
    DC y reportar lo mismo (caso Apartadó: 3.00 % y 2.10 % de PVsyst)."""
    import pandas as pd

    from calculos.produccion import simular_produccion_anual
    from calculos.produccion_iv import simular_produccion_iv

    index = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    sol = (index.hour >= 6) & (index.hour < 18)
    tmy = pd.DataFrame({"T2m": np.full(8760, 20.0)}, index=index)
    poa = pd.DataFrame({"poa_global": np.where(sol, 700.0, 0.0)}, index=index)
    kw = dict(tmy=tmy, poa_base=poa, panel=ASP_ST1_T40, N_paneles=40,
              eta_inversor=0.975, factor_pr_mismatch=1.0)
    for motor in (simular_produccion_anual, simular_produccion_iv):
        base = motor(**kw)
        r = motor(**kw, pct_calidad_modulo=3.0, pct_mismatch_fab=2.1)
        fraccion = r["E_dc_anual_kWh"] / base["E_dc_anual_kWh"]
        assert fraccion == pytest.approx(0.97 * 0.979, rel=1e-3), motor.__name__
        assert r["pct_calidad_modulo_aplicado"] == 3.0
        assert r["pct_mismatch_fab_aplicado"] == 2.1


def test_loss_diagram_igual_desde_los_dos_motores_y_sin_nombre_de_referencia():
    """El Loss Diagram de 📊 Producción (`perdidas_desglosadas`) debe tener las
    mismas filas y reconciliar hasta E_dc con el resultado de cualquiera de los
    dos motores, y sus notas no nombran el software de referencia (Spec
    08-interfaz/sin-nombre-referencia, 29-sep-2026)."""
    import pandas as pd

    from calculos.produccion import perdidas_desglosadas, simular_produccion_anual
    from calculos.produccion_iv import simular_produccion_iv
    from calculos.texto_referencia import menciona_referencia

    index = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    sol = (index.hour >= 6) & (index.hour < 18)
    tmy = pd.DataFrame({"T2m": np.full(8760, 20.0)}, index=index)
    poa = pd.DataFrame({"poa_global": np.where(sol, 700.0, 0.0)}, index=index)
    kw = dict(tmy=tmy, poa_base=poa, panel=ASP_ST1_T40, N_paneles=40, eta_inversor=0.975,
              factor_pr_mismatch=1.0, pct_calidad_modulo=3.0, pct_mismatch_fab=2.1,
              pct_cableado_dc=1.0)
    tablas = [perdidas_desglosadas(m(**kw), poa_bruta_kWh_m2=2555.0).to_dict("records")
              for m in (simular_produccion_anual, simular_produccion_iv)]
    assert [f["Etapa"] for f in tablas[0]] == [f["Etapa"] for f in tablas[1]]
    for tabla in tablas:
        e_dc = next(f["kWh"] for f in tabla if f["Etapa"].startswith("③"))
        assert next(f["kWh"] for f in tabla if f["Etapa"].startswith("②d")) == e_dc
        assert not [f["Nota"] for f in tabla if menciona_referencia(f["Nota"])]


def test_bypass_no_cuenta_de_nuevo_las_horas_de_horizonte():
    """Spec 05/mismatch-horizonte-coherente (29-sep-2026): en las horas con el
    sol detrás del horizonte Producción ya quitó la luz directa; el bypass
    (mismo SDM) no debe restar nada más en esas horas y debe dar exactamente
    lo mismo en las demás. Antes el horizonte entraba como sombra TOTAL."""
    import pandas as pd

    from calculos.mismatch_bypass import excluir_horas_horizonte, simular_bypass_horario

    index = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    sol = (index.hour >= 6) & (index.hour < 18)
    g = np.where(sol, 700.0, 0.0)
    t = np.full(8760, 25.0)
    fs3d = pd.Series(np.where(sol, 0.3, 0.0), index=index)
    horizonte = pd.Series((index.hour == 6) | (index.hour == 17), index=index)
    p_final, info = excluir_horas_horizonte(fs3d, horizonte)
    kw = dict(G_eff=g, T_amb=t, N_series=8, N_parallel=2, panel=ASP_ST1_T40)
    con = simular_bypass_horario(p_shade=p_final.to_numpy(), **kw)
    sin_horas_h = simular_bypass_horario(
        p_shade=np.where(horizonte.to_numpy(), 0.0, fs3d.to_numpy()), **kw)
    viejo = simular_bypass_horario(
        p_shade=np.maximum(fs3d.to_numpy(), horizonte.to_numpy().astype(float)), **kw)
    assert info["horas_excluidas"] == 2 * 365
    assert con["kwh_bypass_anual"] == sin_horas_h["kwh_bypass_anual"]
    assert con["kwh_bypass_anual"] < viejo["kwh_bypass_anual"]


def test_los_dos_motores_reportan_el_mismo_gamma_de_ficha():
    """Spec 04/presentacion-recorte-gamma (29-sep-2026): los dos motores
    devuelven el γ de la ficha para la nota del balance; es solo un dato
    mostrado y debe ser el mismo γ que usa el SDM de la ficha."""
    import pandas as pd

    from calculos.produccion import simular_produccion_anual
    from calculos.produccion_iv import simular_produccion_iv

    index = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    sol = (index.hour >= 6) & (index.hour < 18)
    tmy = pd.DataFrame({"T2m": np.full(8760, 20.0)}, index=index)
    poa = pd.DataFrame({"poa_global": np.where(sol, 600.0, 0.0)}, index=index)
    kw = dict(tmy=tmy, poa_base=poa, panel=ASP_ST1_T40, N_paneles=16,
              eta_inversor=0.975, factor_pr_mismatch=1.0)
    g_anual = simular_produccion_anual(**kw)["Tk_gamma_pct"]
    g_iv = simular_produccion_iv(**kw)["Tk_gamma_pct"]
    assert g_anual == g_iv == pytest.approx(ASP_ST1_T40["Tk_gamma"])
@pytest.mark.parametrize("n_str_tr, fijado", [(1, 0), (2, 0), (2, 2), (1, 3)])
def test_dimensionamiento_y_produccion_cuentan_igual_los_inversores(n_str_tr, fijado):
    """Spec 03/inversores-del-proyecto (29-sep-2026), caso Apartadó del informe
    de la referencia estándar internacional: 308 módulos (11 × 28), Growatt
    MAX 100KTL3 LV (10 MPPT, 100 kW AC). 📐 Dimensionamiento redondeaba hacia
    arriba y 📊 Producción al más cercano; ahora los dos dan la misma
    cantidad, y con 2 fijados la relación DC/AC es la de la referencia (1,11)."""
    from calculos.dimensionamiento import escalar_p_ac_nom_por_inversores, proyecto_completo

    panel = {"area_m2": 3.107, "Pmax_stc": 720.0}
    pc = proyecto_completo(panel, 957.0, 28, n_str_tr, 10, N_total_cadenas=11,
                           P_ac_nom_W=100_000.0, N_inversores_fijado=fijado)
    prod = escalar_p_ac_nom_por_inversores(pc["N_paneles"], 28, n_str_tr, 10, 100_000.0,
                                           n_inversores_fijado=fijado)
    assert prod["n_inversores"] == pc["N_inversores"]
    if fijado == 2:
        assert pc["dcac"]["ratio"] == pytest.approx(221.76 / 200.0, abs=0.005)


@pytest.mark.parametrize("ratio, nivel", [(0.97, "🟠"), (1.00, "🟢"), (1.35, "🟢"), (1.36, "🟠")])
def test_mensaje_dc_ac_dice_el_rango_que_usa_el_calculo(ratio, nivel):
    """Spec 05/recorte-inversor-multisuperficie (29-sep-2026): el mensaje decía
    «rango típico 0.95–1.35» pero el cálculo pone 🟢 desde 1,00; una relación
    de 0,97 salía 🟠 «por debajo de 0.95–1.35». Texto y límite deben coincidir."""
    from calculos.dimensionamiento import evaluar_relacion_dc_ac

    r = evaluar_relacion_dc_ac(ratio * 100.0, 100_000.0)
    assert r["nivel"] == nivel
    assert "0.95" not in r["mensaje"]
    if ratio < 1.36:
        assert "1.00–1.35" in r["mensaje"]
