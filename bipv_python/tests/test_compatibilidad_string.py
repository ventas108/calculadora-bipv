import math

import pytest

from calculos.dimensionamiento import (
    evaluar_compatibilidad_string,
    evaluar_relacion_dc_ac,
    escalar_p_ac_nom_por_inversores,
    mapear_inversores_catalogo,
    optimizar_n_serie,
    resolver_n_strings_tracker,
    curva_electrica_temperatura,
    interpretar_curva_electrica,
    diseno_electrico_confirmado,
)
from datos.tecnologias_bipv import ASP_ST1_T40


def _eco_sna_12k() -> dict:
    return {
        "Vdc_max": 480,
        "Vmppt_min": 120,
        "Vmppt_max": 440,
        "Isc_max_tracker": 44,
        "n_trackers": 2,
        "n_strings_tracker": 1,
    }


def test_economico_sna_12k_detecta_tension_y_mppt_fuera_de_rango() -> None:
    resultado = evaluar_compatibilidad_string(
        ASP_ST1_T40,
        _eco_sna_12k(),
        N_serie=8,
        T_frio=-5.0,
        T_real=36.35,
        T_extremo=41.94,
        N_strings_tracker=1,
    )

    assert resultado["evaluable"] is True
    assert resultado["compatible"] is False
    assert resultado["Voc_frio"] == pytest.approx(1017.4, abs=1.0)
    # 666.0V, no 674.0V: calcular_vmp_string() usaba Tk_gamma (coef. de
    # Pmax) en vez de Tk_beta (coef. de Voc) -- corregido 25-ago-2026,
    # ver tests/test_validacion_vba.py::test_vmp_n8_vs_xlsm.
    assert resultado["Vmp_real"] == pytest.approx(666.0, abs=1.0)
    assert any("Voc en frío" in m for m in resultado["mensajes"])
    assert any("MPPT máximo" in m for m in resultado["mensajes"])


def test_configuracion_de_dos_modulos_es_electronicamente_valida_para_eco() -> None:
    resultado = evaluar_compatibilidad_string(
        ASP_ST1_T40,
        _eco_sna_12k(),
        N_serie=2,
        T_frio=-5.0,
        T_real=36.35,
        T_extremo=41.94,
        N_strings_tracker=1,
    )

    assert resultado["compatible"] is True
    assert resultado["mensajes"] == []


def test_mapeo_catalogo_no_ofrece_eco_para_n8() -> None:
    mapeo = mapear_inversores_catalogo(
        ASP_ST1_T40,
        {"ECO HIBRID SNA US 12K": _eco_sna_12k()},
        N_min=8,
        N_max=8,
        T_frio=-5.0,
        T_real=36.35,
        T_extremo=41.94,
        N_strings_tracker=1,
    )

    assert len(mapeo) == 1
    assert mapeo[0]["compatible"] is False
    assert mapeo[0]["estado"] == "🔴 No compatible"
    assert mapeo[0]["N_viables"] == "—"
    assert "Voc en frío" in mapeo[0]["motivo"]


def test_mapeo_catalogo_encuentra_n_viable_y_marca_ficha_incompleta() -> None:
    mapeo = mapear_inversores_catalogo(
        ASP_ST1_T40,
        {
            "ECO HIBRID SNA 12K": _eco_sna_12k(),
            "Ficha incompleta": {"Vdc_max": 1000},
        },
        N_min=2,
        N_max=8,
        T_frio=-5.0,
        T_real=36.35,
        T_extremo=41.94,
        N_strings_tracker=1,
    )

    por_modelo = {fila["modelo"]: fila for fila in mapeo}
    assert por_modelo["ECO HIBRID SNA 12K"]["compatible"] is True
    assert por_modelo["ECO HIBRID SNA 12K"]["N_string_recomendado"] == 3
    assert por_modelo["ECO HIBRID SNA 12K"]["N_viables"] == "2–3"
    assert por_modelo["Ficha incompleta"]["estado"] == "🟡 No evaluable"


def test_mapeo_catalogo_no_se_detiene_con_nan_en_contadores() -> None:
    mapeo = mapear_inversores_catalogo(
        ASP_ST1_T40,
        {
            "Ficha con NaN": {
                "Vdc_max": 1000,
                "Vmppt_min": 200,
                "Vmppt_max": 800,
                "Isc_max_tracker": 20,
                "n_trackers": math.nan,
                "n_strings_tracker": math.nan,
            }
        },
        N_min=2,
        N_max=3,
        N_strings_tracker=1,
    )

    assert len(mapeo) == 1
    assert mapeo[0]["estado"] == "🟡 No evaluable"
    assert mapeo[0]["trackers"] == 0
    assert mapeo[0]["strings_tracker"] == 0
    assert "trackers" in mapeo[0]["motivo"]


# ══════════════════════════════════════════════════════════════════════════
# Bug real de auditoría (27-ago-2026): evaluar_compatibilidad_string usaba
# Vmppt_min (piso de arranque) en vez de Vmppt_activo_min (piso MPPT típico
# recomendado) cuando ambos existen en la ficha del inversor -- daba
# "compatible" para configuraciones que optimizar_n_serie() (validado
# contra el XLSM original) y comparador_inversores.filtrar_inversores_
# compatibles() ya rechazaban como FALLA/incompatible para la MISMA config.
# Encontrado ejecutando las 3 funciones con datos reales del proyecto
# Agrivoltaico Urabá (18 módulos JA Solar JAM66D46-720/LB en serie +
# Growatt MAX 100KTL3 LV): Vmp string = 720 V, entre Vmppt_min=200 V
# (pasaba) y Vmppt_activo_min=850 V (debía fallar).
# ══════════════════════════════════════════════════════════════════════════
def _growatt_max_100ktl3_lv() -> dict:
    return {
        "Vdc_max": 1500,
        "Vmppt_min": 200,
        "Vmppt_activo_min": 850,
        "Vmppt_max": 1300,
        "Isc_max_tracker": 32.5,
        "n_trackers": 10,
        "n_strings_tracker": 2,
    }


def _ja_solar_jam66d46_720lb() -> dict:
    return {"Voc_stc": 49.00, "Vmp_stc": 41.19, "Isc_stc": 18.59, "Tk_beta": -0.250}


def test_uraba_18_en_serie_usa_vmppt_activo_min_no_vmppt_min():
    # Con el bug (Vmppt_min=200 V como piso) esta config salía "compatible".
    # Con el fix (Vmppt_activo_min=850 V como piso) debe salir incompatible,
    # igual que optimizar_n_serie() y filtrar_inversores_compatibles().
    resultado = evaluar_compatibilidad_string(
        _ja_solar_jam66d46_720lb(),
        _growatt_max_100ktl3_lv(),
        N_serie=18,
        T_frio=-5.0, T_real=36.35, T_extremo=41.94,
        N_strings_tracker=1,
    )
    assert resultado["evaluable"] is True
    assert resultado["Vmp_real"] == pytest.approx(720.4, abs=1.0)
    assert resultado["compatible"] is False
    assert any("MPPT mínimo" in m and "850" in m for m in resultado["mensajes"])


def test_n_serie_suficiente_para_vmppt_activo_min_si_es_compatible():
    # N=22 es el mínimo real que deja Vmp por encima de 850 V tanto a
    # T_real (36.35°C) como a T_extremo (41.94°C) -- el simple
    # ceil(850/41.19)=21 de STC no alcanza porque a T_real/T_extremo el
    # Vmp ya bajó por el coeficiente de temperatura (Vmp(21,36.35°C)=840 V,
    # todavía < 850 V).
    resultado = evaluar_compatibilidad_string(
        _ja_solar_jam66d46_720lb(),
        _growatt_max_100ktl3_lv(),
        N_serie=22,
        T_frio=-5.0, T_real=36.35, T_extremo=41.94,
        N_strings_tracker=1,
    )
    assert not any("MPPT mínimo" in m for m in resultado["mensajes"])


def test_evaluar_compatibilidad_string_coincide_con_filtrar_inversores_compatibles():
    # Mismo config, mismas dos funciones que antes daban veredictos opuestos
    # -- ahora deben coincidir.
    from calculos.comparador_inversores import filtrar_inversores_compatibles

    panel = _ja_solar_jam66d46_720lb()
    inv = _growatt_max_100ktl3_lv()
    inv["P_ac_nom_W"] = 100_000
    inv["N_mppt"] = inv["n_trackers"]

    r1 = evaluar_compatibilidad_string(
        panel, inv, N_serie=18, T_frio=-5.0, T_real=36.35, T_extremo=41.94,
        N_strings_tracker=1,
    )
    df2 = filtrar_inversores_compatibles(panel, {"Growatt MAX 100KTL3 LV": inv}, N_serie=18)

    assert r1["compatible"] is False
    assert bool(df2.iloc[0]["compatible"]) is False


# ---------------------------------------------------------------------------
# curva_electrica_temperatura() -- gráfico de compatibilidad eléctrica para
# el Reporte PDF (pedido explícito del usuario, 30-ago-2026), equivalente al
# gráfico "Array behavior" de PVsyst. Casos anclados al proyecto real Urabá
# (N=18 histórico incompatible con el clima real, N=28 electricamente
# correcto -- ver DIAGNOSTICO_NSERIE_URABA_TEMPERATURA_REAL.md).
# ---------------------------------------------------------------------------


def test_curva_electrica_no_reimplementa_la_fisica_coincide_con_evaluar_compatibilidad():
    # La evaluación embebida debe ser BIT A BIT la misma que llamar
    # evaluar_compatibilidad_string() por separado -- es la garantía de que
    # el gráfico nunca puede mostrar un veredicto distinto al resto de la app.
    panel = _ja_solar_jam66d46_720lb()
    inv = _growatt_max_100ktl3_lv()
    directo = evaluar_compatibilidad_string(
        panel, inv, N_serie=18, T_frio=-5.0, T_real=36.35, T_extremo=41.94,
        N_strings_tracker=1,
    )
    r = curva_electrica_temperatura(
        panel, inv, N_serie=18, T_frio=-5.0, T_real=36.35, T_extremo=41.94,
        N_strings_tracker=1,
    )
    assert r["evaluacion"] == directo


def test_curva_electrica_uraba_n18_muestra_incompatibilidad_real():
    # Caso real ya documentado: N=18 (17x18=306 módulos, diseño histórico)
    # reprueba el piso Vmppt_activo_min=850V con clima real de Urabá.
    r = curva_electrica_temperatura(
        _ja_solar_jam66d46_720lb(), _growatt_max_100ktl3_lv(), N_serie=18,
        T_frio=22.1, T_real=54.5, T_extremo=66.0, N_strings_tracker=1,
    )
    assert r["evaluacion"]["compatible"] is False
    assert r["vmppt_min"] == pytest.approx(850.0)
    assert r["vdc_max"] == pytest.approx(1500.0)
    # La curva de Vmp a la temperatura más caliente debe caer bajo el piso
    # MPPT -- es justo lo que el gráfico tiene que poder mostrar visualmente.
    assert min(r["vmp_curva"]) < r["vmppt_min"]


def test_curva_electrica_uraba_n28_es_compatible():
    # N=28 -- el valor eléctricamente correcto encontrado en esta misma
    # auditoría para el clima real de Urabá.
    r = curva_electrica_temperatura(
        _ja_solar_jam66d46_720lb(), _growatt_max_100ktl3_lv(), N_serie=28,
        T_frio=22.1, T_real=54.5, T_extremo=66.0, N_strings_tracker=1,
    )
    assert r["evaluacion"]["compatible"] is True
    assert min(r["vmp_curva"]) >= r["vmppt_min"]
    assert max(r["voc_curva"]) <= r["vdc_max"]


def test_curva_electrica_temps_van_de_menor_a_mayor_y_cubren_las_3_de_diseno():
    r = curva_electrica_temperatura(
        _ja_solar_jam66d46_720lb(), _growatt_max_100ktl3_lv(), N_serie=28,
        T_frio=22.1, T_real=54.5, T_extremo=66.0, N_strings_tracker=1,
        n_puntos=10,
    )
    temps = r["temps"]
    assert temps == sorted(temps)
    assert temps[0] == pytest.approx(22.1)
    assert temps[-1] == pytest.approx(66.0)
    assert len(temps) == len(r["voc_curva"]) == len(r["vmp_curva"]) == 10


def test_curva_electrica_sin_limites_del_inversor_devuelve_none_no_cero():
    # Un inversor sin Vdc_max publicado no debe dibujar una banda falsa en 0.
    r = curva_electrica_temperatura(
        _ja_solar_jam66d46_720lb(), {}, N_serie=18,
        T_frio=-5.0, T_real=36.35, T_extremo=41.94,
    )
    assert r["vdc_max"] is None
    assert r["vmppt_min"] is None
    assert r["vmppt_max"] is None


# ---------------------------------------------------------------------------
# interpretar_curva_electrica() -- interpretación en lenguaje natural del
# gráfico, adaptada al caso real del proyecto (pedido explícito del usuario,
# 30-ago-2026, para visibilizarla en 📊 Producción). Mismos fixtures Urabá.
# ---------------------------------------------------------------------------


def test_interpretacion_uraba_n18_marca_critico_en_vmp_extremo():
    r = curva_electrica_temperatura(
        _ja_solar_jam66d46_720lb(), _growatt_max_100ktl3_lv(), N_serie=18,
        T_frio=22.1, T_real=54.5, T_extremo=66.0, N_strings_tracker=1,
    )
    puntos = interpretar_curva_electrica(r)
    por_punto = {p["punto"]: p for p in puntos}
    assert por_punto["Vmp extremo (calor)"]["nivel"] == "critico"
    assert "MPPT" in por_punto["Vmp extremo (calor)"]["texto"]
    # Debe interpretar los 3 puntos, no solo el que falla.
    assert set(por_punto) == {"Voc frío", "Vmp real", "Vmp extremo (calor)"}


def test_interpretacion_uraba_n28_no_marca_ningun_punto_critico():
    r = curva_electrica_temperatura(
        _ja_solar_jam66d46_720lb(), _growatt_max_100ktl3_lv(), N_serie=28,
        T_frio=22.1, T_real=54.5, T_extremo=66.0, N_strings_tracker=1,
    )
    puntos = interpretar_curva_electrica(r)
    assert all(p["nivel"] != "critico" for p in puntos)


def test_interpretacion_sin_limites_del_inversor_no_genera_puntos():
    r = curva_electrica_temperatura(
        _ja_solar_jam66d46_720lb(), {}, N_serie=18,
        T_frio=-5.0, T_real=36.35, T_extremo=41.94,
    )
    assert interpretar_curva_electrica(r) == []


# ---------------------------------------------------------------------------
# evaluar_relacion_dc_ac() -- aviso homólogo a "Proporción Pnom" de PVsyst.
# Casos anclados a proyectos reales ya validados este mismo repo, incluyendo
# una captura real de PVsyst 8.1.5 (Teusaquillo) -- ver docstring de la
# función en calculos/dimensionamiento.py para el detalle completo.
# ---------------------------------------------------------------------------


def test_relacion_dc_ac_teusaquillo_coincide_con_pantallazo_real_pvsyst():
    # Proyecto real Teusaquillo: 128 módulos ASP-ST1-T40 (8.064 kWp) +
    # Growatt MID15KTL3-X (15 kW CA). PVsyst 8.1.5 muestra en su propia
    # UI "Proporción Pnom: 0.538" y el aviso rojo "La potencia del inversor
    # está muy sobredimensionada" -- confirmado idéntico aquí.
    resultado = evaluar_relacion_dc_ac(P_dc_stc_kW=8.064, P_ac_nom_W=15_000)

    assert resultado["evaluable"] is True
    assert resultado["ratio"] == pytest.approx(0.538, abs=0.001)
    assert resultado["estado"] == "muy_sobredimensionado"
    assert resultado["nivel"] == "🔴"
    # El mensaje cita el % de uso REAL de esta corrida (54%), no una frase
    # fija tipo "menos de tres cuartos" -- pedido explicito del usuario
    # (29-ago-2026) tras notar que el mensaje decia siempre lo mismo sin
    # importar si el ratio real era 0.54, 0.20 o 0.13.
    assert "54%" in resultado["mensaje"]


def test_relacion_dc_ac_mensaje_muestra_porcentaje_real_no_frase_fija():
    # Dos ratios distintos, ambos "muy_sobredimensionado" (<0.75) -- el
    # mensaje debe reflejar CADA porcentaje real, no un texto identico.
    r1 = evaluar_relacion_dc_ac(P_dc_stc_kW=1.76, P_ac_nom_W=8_640)   # ratio 0.204
    r2 = evaluar_relacion_dc_ac(P_dc_stc_kW=16.63, P_ac_nom_W=129_600)  # ratio 0.128

    assert "20%" in r1["mensaje"]
    assert "13%" in r2["mensaje"]
    assert r1["mensaje"] != r2["mensaje"]


def test_relacion_dc_ac_uraba_sobredimensionado_pero_no_critico():
    # Proyecto real Urabá: 220.32 kWp + 2x Growatt MAX 100KTL3 LV
    # (249.6 kW CA total) -- ratio 0.883, por debajo del rango típico
    # (0.95-1.35) pero no en el rango "muy sobredimensionado" (<0.75).
    resultado = evaluar_relacion_dc_ac(P_dc_stc_kW=220.32, P_ac_nom_W=249_600)

    assert resultado["evaluable"] is True
    assert resultado["ratio"] == pytest.approx(0.883, abs=0.001)
    assert resultado["estado"] == "sobredimensionado"
    assert resultado["nivel"] == "🟠"


def test_relacion_dc_ac_rango_optimo_no_genera_alerta():
    resultado = evaluar_relacion_dc_ac(P_dc_stc_kW=13.0, P_ac_nom_W=10_000)  # ratio 1.30

    assert resultado["evaluable"] is True
    assert resultado["estado"] == "optimo"
    assert resultado["nivel"] == "🟢"


def test_relacion_dc_ac_muy_alto_sugiere_revisar_clipping():
    resultado = evaluar_relacion_dc_ac(P_dc_stc_kW=18.0, P_ac_nom_W=10_000)  # ratio 1.80

    assert resultado["evaluable"] is True
    assert resultado["estado"] == "muy_alto"
    assert resultado["nivel"] == "🔴"
    assert "clipping" in resultado["mensaje"].lower() or "recorte" in resultado["mensaje"].lower()


def test_relacion_dc_ac_sin_potencia_ac_nominal_no_es_evaluable():
    assert evaluar_relacion_dc_ac(P_dc_stc_kW=10.0, P_ac_nom_W=None)["evaluable"] is False
    assert evaluar_relacion_dc_ac(P_dc_stc_kW=10.0, P_ac_nom_W=0)["evaluable"] is False


# ---------------------------------------------------------------------------
# resolver_n_strings_tracker() -- dos mecanismos posibles, comparacion
# honesta pedida por el usuario contra como lo hace PVsyst (29-ago-2026).
# Mecanismo "catalogo" (default, N_total_cadenas=0): antes N_strings/tracker
# quedaba fijo en 1 (default duro de pages/4) sin importar el inversor
# seleccionado, lo que llevo a un calculo real erroneo con el proyecto
# Teusaquillo (16 paneles/inversor en vez de 128, "necesitas 8 inversores"
# en vez de 1). Mecanismo "total" (N_total_cadenas>0): replica el mecanismo
# real de PVsyst -- el usuario declara el total de cadenas del generador y
# se reparte entre los trackers/MPPT del inversor. Ver docstring de la
# funcion en calculos/dimensionamiento.py para el detalle completo.
# ---------------------------------------------------------------------------


def test_n_strings_tracker_autocalcula_desde_el_catalogo_al_elegir_inversor():
    # Growatt MID15KTL3-X real (proyecto Teusaquillo): 8 strings/tracker.
    inversor = {"n_strings_tracker": 8}
    session_state: dict = {}

    r = resolver_n_strings_tracker(inversor, "Growatt MID15KTL3-X", session_state)

    assert r["valor"] == 8
    assert r["sugerido"] == 8
    assert r["fuente"] == "catalogo"
    assert r["recalculado"] is True
    assert session_state["N_str_tr"] == 8


def test_n_strings_tracker_respeta_ajuste_manual_del_mismo_inversor():
    inversor = {"n_strings_tracker": 8}
    session_state: dict = {}
    resolver_n_strings_tracker(inversor, "Growatt MID15KTL3-X", session_state)

    # El usuario ajusta a mano (ej. combinadora real con menos strings)
    session_state["N_str_tr"] = 4

    # Mismo inversor en el siguiente rerun -> no debe pisar el ajuste manual
    r = resolver_n_strings_tracker(inversor, "Growatt MID15KTL3-X", session_state)

    assert r["valor"] == 4
    assert r["sugerido"] == 8  # la formula sigue sugiriendo 8 -- permite avisar del ajuste
    assert r["recalculado"] is False


def test_n_strings_tracker_resetea_al_cambiar_de_inversor():
    # El generico "MID 15KTL3-X" (sin marca) tiene solo 1 string/tracker en
    # el catalogo real -- caso real que causo la confusion original: quedaba
    # en 8 (arrastrado del Growatt) en vez de resetear al valor de este otro
    # inversor.
    growatt = {"n_strings_tracker": 8}
    generico = {"n_strings_tracker": 1}
    session_state: dict = {}
    resolver_n_strings_tracker(growatt, "Growatt MID15KTL3-X", session_state)
    session_state["N_str_tr"] = 4  # ajuste manual que no debe sobrevivir el cambio

    r = resolver_n_strings_tracker(generico, "MID 15KTL3-X", session_state)

    assert r["valor"] == 1
    assert r["recalculado"] is True
    assert session_state["N_str_tr_fuente_ref"] == ("catalogo", "MID 15KTL3-X")


def test_n_strings_tracker_sin_dato_en_catalogo_cae_a_1():
    inversor: dict = {}  # ficha incompleta, sin "n_strings_tracker"
    session_state: dict = {}

    r = resolver_n_strings_tracker(inversor, "Inversor sin ficha completa", session_state)

    assert r["valor"] == 1
    assert r["recalculado"] is True


def test_n_strings_tracker_mecanismo_total_replica_pvsyst():
    # Mismo caso real Teusaquillo, pero declarando el TOTAL como en PVsyst
    # (16 cadenas, 2 trackers) en vez de partir de la capacidad del catalogo.
    inversor = {"n_strings_tracker": 8, "n_trackers": 2}
    session_state: dict = {}

    r = resolver_n_strings_tracker(
        inversor, "Growatt MID15KTL3-X", session_state, N_total_cadenas=16
    )

    assert r["fuente"] == "total"
    assert r["n_trackers"] == 2
    assert r["valor"] == 8  # 16 / 2 -- coincide con el mecanismo "catalogo" en este caso
    assert r["recalculado"] is True


def test_n_strings_tracker_mecanismo_total_redondea_hacia_arriba():
    # PVsyst tambien tendria que resolver un reparto no exacto -- 17 cadenas
    # entre 2 trackers no da entero; ceil() es la unica division que no deja
    # cadenas sin asignar.
    inversor = {"n_trackers": 2}
    session_state: dict = {}

    r = resolver_n_strings_tracker(inversor, "Inversor X", session_state, N_total_cadenas=17)

    assert r["valor"] == 9  # ceil(17/2)


def test_n_strings_tracker_total_tiene_prioridad_sobre_catalogo():
    # Si el usuario declara un total, debe ganar sobre la capacidad maxima
    # del catalogo aunque sean distintos -- es la eleccion explicita del
    # usuario, el mecanismo real de PVsyst.
    inversor = {"n_strings_tracker": 8, "n_trackers": 2}
    session_state: dict = {}

    r = resolver_n_strings_tracker(
        inversor, "Growatt MID15KTL3-X", session_state, N_total_cadenas=10
    )

    assert r["fuente"] == "total"
    assert r["valor"] == 5  # ceil(10/2), NO el 8 del catalogo


def test_n_strings_tracker_volver_a_0_regresa_al_mecanismo_catalogo():
    inversor = {"n_strings_tracker": 8, "n_trackers": 2}
    session_state: dict = {}
    resolver_n_strings_tracker(inversor, "Growatt MID15KTL3-X", session_state, N_total_cadenas=10)

    # El usuario borra el total declarado (vuelve a 0) -- debe volver al
    # mecanismo de catalogo, no quedarse pegado en el ultimo total.
    r = resolver_n_strings_tracker(inversor, "Growatt MID15KTL3-X", session_state, N_total_cadenas=0)

    assert r["fuente"] == "catalogo"
    assert r["valor"] == 8
    assert r["recalculado"] is True


# ---------------------------------------------------------------------------
# alerta_margen -- armoniza evaluar_compatibilidad_string()/
# mapear_inversores_catalogo() con el margen de seguridad del 7,5% que
# optimizar_n_serie()/semaforo() ya aplicaban. Caso real que expuso la
# inconsistencia (29-ago-2026): TriP 6K-HV con el panel real (Isc=1.19A),
# N_strings_tracker=2, T_frio=5.0 (Bogota real) -- N=8 da Voc frio 987,6V
# contra un Vdc_max de 1000V (margen real 1,24%, muy por debajo del 7,5%
# minimo). El "Mapeo de inversores"/"Prorrateo preliminar" recomendaba N=8
# ("compatible", sin margen), mientras que el boton principal "Optimizar N
# paneles/string" elegia N=7 (con margen) -- mismo inversor real, dos
# recomendaciones distintas. Ver docstring de evaluar_compatibilidad_string()
# para el detalle completo.
# ---------------------------------------------------------------------------


def _trip_6k_hv() -> dict:
    return {
        "Vdc_max": 1000,
        "Vmppt_min": 200,
        "Vmppt_activo_min": 200,
        "Vmppt_max": 900,
        "Isc_max_tracker": 25,
        "n_trackers": 2,
        "n_strings_tracker": 2,
    }


def test_alerta_margen_marca_n8_muy_cerca_del_limite_sin_cambiar_compatible():
    # ASP_ST1_T40 (fixture del repo) puede tener otro Isc/Voc que el panel
    # real del catalogo Excel -- se ancla directamente a los voltajes, no al
    # panel, para no depender de qué fixture se use.
    resultado = evaluar_compatibilidad_string(
        ASP_ST1_T40, _trip_6k_hv(), N_serie=8,
        T_frio=5.0, T_real=36.35, T_extremo=41.94,
        N_strings_tracker=2,
    )

    assert resultado["Voc_frio"] == pytest.approx(987.6, abs=1.0)
    # El dato clave: compatible=True NO cambia (retrocompatibilidad total con
    # cualquier proyecto ya validado, ej. Urabá) -- alerta_margen es aparte.
    assert resultado["compatible"] is True
    assert resultado["alerta_margen"] is True


def test_alerta_margen_no_se_activa_con_margen_comodo():
    # N=6 tiene mucho margen (Voc frio ~763V contra 1000V, margen >7,5%).
    resultado = evaluar_compatibilidad_string(
        ASP_ST1_T40, _trip_6k_hv(), N_serie=6,
        T_frio=5.0, T_real=36.35, T_extremo=41.94,
        N_strings_tracker=2,
    )

    assert resultado["compatible"] is True
    assert resultado["alerta_margen"] is False


def test_mapeo_prefiere_n_sin_alerta_de_margen_sobre_n_mas_alto():
    # El caso real: N=8 es "compatible" pero con alerta_margen; N=7 es
    # compatible y seguro. El mapeo debe recomendar N=7, coincidiendo con lo
    # que optimizar_n_serie() elegiría para el mismo inversor real.
    mapeo = mapear_inversores_catalogo(
        ASP_ST1_T40,
        {"TriP 6K-HV": _trip_6k_hv()},
        N_min=6, N_max=8,
        T_frio=5.0, T_real=36.35, T_extremo=41.94,
        N_strings_tracker=2,
    )

    assert mapeo[0]["N_string_recomendado"] == 7
    # N=8 sigue apareciendo como viable (compatible=True) -- no desaparece,
    # solo deja de ser el "recomendado".
    assert mapeo[0]["N_viables"] == "6–8"


# ---------------------------------------------------------------------------
# optimizar_n_serie() con N_min > N_max -- crash real reproducido (29-ago-2026)
# cambiando de Growatt MAX 100KTL3 LV (N_min_elec=21 con el panel JA Solar
# JAM66D46-720/LB real de Urabá) a SOLIS-60K en pages/4_Dimensionamiento.py:
# el N_min_scan quedaba pegado en 21 (el max() de la pagina nunca lo baja al
# cambiar de inversor), mientras N_max_scan seguia en su default (20).
# optimizar_n_serie(N_min=21, N_max=20) recorre un range() vacio y retorna
# [] -- pd.DataFrame([]) sale sin columnas, y el .style.map(subset=[...])
# de la pagina revienta con KeyError, tumbando la pagina con un traceback
# crudo para el usuario. La pagina ahora tiene un guard explicito (if not
# resultados: st.error(...); st.stop()) Y ya no deja que N_min quede pegado
# al cambiar de inversor -- este test ancla el comportamiento de la funcion
# pura que hizo evidente el bug real.
# ---------------------------------------------------------------------------


def test_optimizar_n_serie_con_n_min_mayor_a_n_max_retorna_lista_vacia():
    panel_ja_solar = {
        "Voc_stc": 49.00, "Vmp_stc": 41.19, "Isc_stc": 18.59, "Tk_beta": -0.250,
    }
    solis_60k = {
        "Vdc_max": 1100, "Vmppt_min": 180, "Vmppt_activo_min": 180,
        "Vmppt_max": 1000, "Isc_max_tracker": 50,
        "n_trackers": 4, "n_strings_tracker": 1,
    }

    # N_min=21 es el minimo electrico real del Growatt MAX 100KTL3 LV con
    # este panel (ceil(850/41.19)=21) -- pegado por error al cambiar a un
    # inversor distinto (SOLIS-60K) cuyo N_max_scan seguia en el default 20.
    resultados = optimizar_n_serie(panel_ja_solar, solis_60k, N_min=21, N_max=20)

    assert resultados == []


# ---------------------------------------------------------------------------
# escalar_p_ac_nom_por_inversores() -- bug real en 📊 Producción (29-ago-2026,
# proyecto Urabá): esa pagina toma N_paneles del "Proyecto completo" (varios
# inversores) pero comparaba/recortaba contra la potencia CA de UN SOLO
# inversor, sin escalar. Caso real: 840 paneles (604.8 kWp, 3x Growatt MAX
# 100KTL3 LV, N_serie=28, N_strings_tracker=1, 10 trackers) daba DC/AC=4.85
# en vez de 1.61.
# ---------------------------------------------------------------------------


def test_escalar_p_ac_nom_caso_real_uraba_840_paneles_3_inversores():
    r = escalar_p_ac_nom_por_inversores(
        N_paneles=840, N_serie=28, N_strings_tracker=1, n_trackers=10,
        P_ac_nom_W_unidad=124_800,
    )

    assert r["paneles_por_inversor"] == 280
    assert r["n_inversores"] == 3
    assert r["p_ac_nom_w_total"] == pytest.approx(374_400)

    # El DC/AC con el total escalado debe coincidir con el ratio por-inversor
    # (604.8/124.8 == 1814.4/374.4), no con el 4.85 que daba el bug.
    dcac = evaluar_relacion_dc_ac(P_dc_stc_kW=840 * 0.720, P_ac_nom_W=r["p_ac_nom_w_total"])
    assert dcac["ratio"] == pytest.approx(1.615, abs=0.01)


def test_escalar_p_ac_nom_un_solo_inversor_no_cambia_nada():
    # Proyecto de un solo inversor (280 paneles) -- retrocompatible, mismo
    # comportamiento que sin escalar.
    r = escalar_p_ac_nom_por_inversores(
        N_paneles=280, N_serie=28, N_strings_tracker=1, n_trackers=10,
        P_ac_nom_W_unidad=124_800,
    )

    assert r["n_inversores"] == 1
    assert r["p_ac_nom_w_total"] == pytest.approx(124_800)


def test_escalar_p_ac_nom_sin_config_de_string_retorna_1_inversor():
    # N_serie=None (todavia no se corrio Optimizar N paneles/string) -- no
    # se puede derivar inversores, cae a 1 en vez de reventar.
    r = escalar_p_ac_nom_por_inversores(
        N_paneles=840, N_serie=None, N_strings_tracker=1, n_trackers=10,
        P_ac_nom_W_unidad=124_800,
    )

    assert r["n_inversores"] == 1
    assert r["paneles_por_inversor"] == 0
    assert r["p_ac_nom_w_total"] == pytest.approx(124_800)


def test_escalar_p_ac_nom_sin_potencia_ac_retorna_none():
    r = escalar_p_ac_nom_por_inversores(
        N_paneles=840, N_serie=28, N_strings_tracker=1, n_trackers=10,
        P_ac_nom_W_unidad=None,
    )

    assert r["p_ac_nom_w_total"] is None

# ---------------------------------------------------------------------------
# diseno_electrico_confirmado() -- fuente única del diseño CONFIRMADO
# (31-ago-2026, "blindaje" pedido por el usuario tras encontrar que
# Producción leía el widget en vivo de N_strings/tracker en vez del valor
# confirmado -- el mismo caso real de Teusaquillo, con el widget "en vivo"
# desviado del confirmado, sirve de ancla aquí).
# ---------------------------------------------------------------------------


def test_diseno_confirmado_usa_n_str_tr_usado_no_el_widget_en_vivo():
    # Caso real Teusaquillo: Dimensionamiento confirmó N_str_tr_usado=8,
    # pero el widget en vivo N_str_tr había vuelto a caer en 1 -- el
    # diseño confirmado debe ignorar el widget y devolver 8.
    estado = {"N_serie": 8, "N_str_tr": 1, "N_str_tr_usado": 8}
    resultado = diseno_electrico_confirmado(estado)
    assert resultado["N_strings_tracker"] == 8
    assert resultado["N_serie"] == 8


def test_diseno_confirmado_default_1_sin_diseno_confirmado_todavia():
    # Dimensionamiento nunca se corrió en esta sesión -- ni N_serie ni
    # N_str_tr_usado existen. No debe inventar un valor del widget en vivo.
    estado = {}
    resultado = diseno_electrico_confirmado(estado)
    assert resultado["N_strings_tracker"] == 1
    assert resultado["N_serie"] is None


def test_diseno_confirmado_ignora_n_str_tr_aunque_no_haya_usado():
    # Si por algún motivo solo existe el widget en vivo (sin _usado todavía
    # confirmado), el diseño confirmado debe caer al default (1), NUNCA
    # tomar el valor del widget -- es justo el bug que se corrigió.
    estado = {"N_serie": 8, "N_str_tr": 8}
    resultado = diseno_electrico_confirmado(estado)
    assert resultado["N_strings_tracker"] == 1


# ---------------------------------------------------------------------------
# diseno_electrico_confirmado() -- alerta de vigencia (31-ago-2026, "construye
# esa alerta con el mismo rigor"): panel_dict/inversor_dict_dim se actualizan
# solos al cambiar la selección en Dimensionamiento, pero N_serie/N_str_tr_usado
# solo se actualizan al re-confirmar. Diseñado para NUNCA dar falso positivo:
# solo avisa si hay evidencia POSITIVA (una referencia guardada que ya no
# coincide con la selección actual), nunca por la sola ausencia de referencia.
# ---------------------------------------------------------------------------


def test_diseno_confirmado_vigente_cuando_panel_e_inversor_no_cambiaron():
    estado = {
        "N_serie": 8, "N_str_tr_usado": 8,
        "N_serie_panel_ref": "ASP-ST1-T40", "N_serie_inversor_ref": "Growatt MID15KTL3-X",
        "panel_nombre_dim": "ASP-ST1-T40", "inversor_nombre_dim": "Growatt MID15KTL3-X",
    }
    resultado = diseno_electrico_confirmado(estado)
    assert resultado["vigente"] is True
    assert resultado["aviso"] is None
    assert resultado["panel_confirmado"] == "ASP-ST1-T40"
    assert resultado["inversor_confirmado"] == "Growatt MID15KTL3-X"


def test_diseno_confirmado_avisa_si_panel_cambio_sin_reconfirmar():
    # El usuario confirmó con ASP-ST1-T40 y luego, sin volver a oprimir
    # "Optimizar N paneles/string", cambió el panel en vivo a otro distinto.
    estado = {
        "N_serie": 8, "N_str_tr_usado": 8,
        "N_serie_panel_ref": "ASP-ST1-T40", "N_serie_inversor_ref": "Growatt MID15KTL3-X",
        "panel_nombre_dim": "EINNOVA ESM-620M", "inversor_nombre_dim": "Growatt MID15KTL3-X",
    }
    resultado = diseno_electrico_confirmado(estado)
    assert resultado["vigente"] is False
    assert resultado["aviso"] is not None
    assert "ASP-ST1-T40" in resultado["aviso"]
    assert "Dimensionamiento" in resultado["aviso"]


def test_diseno_confirmado_avisa_si_inversor_cambio_sin_reconfirmar():
    estado = {
        "N_serie": 8, "N_str_tr_usado": 8,
        "N_serie_panel_ref": "ASP-ST1-T40", "N_serie_inversor_ref": "Growatt MID15KTL3-X",
        "panel_nombre_dim": "ASP-ST1-T40", "inversor_nombre_dim": "SOLIS-60K",
    }
    resultado = diseno_electrico_confirmado(estado)
    assert resultado["vigente"] is False
    assert resultado["aviso"] is not None
    assert "Growatt MID15KTL3-X" in resultado["aviso"]


def test_diseno_confirmado_sin_referencia_historica_no_inventa_alarma():
    # Proyecto guardado ANTES de que existieran N_serie_panel_ref/
    # N_serie_inversor_ref (o cualquier caso donde nunca se escribieron):
    # no hay forma de saber si el panel/inversor cambió, así que NO debe
    # avisar -- vigente=True por diseño, nunca una alarma sin evidencia.
    estado = {
        "N_serie": 8, "N_str_tr_usado": 8,
        "panel_nombre_dim": "ASP-ST1-T40", "inversor_nombre_dim": "Growatt MID15KTL3-X",
    }
    resultado = diseno_electrico_confirmado(estado)
    assert resultado["vigente"] is True
    assert resultado["aviso"] is None


def test_diseno_confirmado_sin_diseno_confirmado_todavia_no_avisa():
    # Dimensionamiento nunca se corrió (N_serie ausente) -- no hay diseño
    # que pueda quedar desactualizado, así que tampoco hay aviso.
    estado = {"panel_nombre_dim": "ASP-ST1-T40", "inversor_nombre_dim": "Growatt MID15KTL3-X"}
    resultado = diseno_electrico_confirmado(estado)
    assert resultado["N_serie"] is None
    assert resultado["vigente"] is True
    assert resultado["aviso"] is None
