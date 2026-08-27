import math

import pytest

from calculos.dimensionamiento import (
    evaluar_compatibilidad_string,
    mapear_inversores_catalogo,
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