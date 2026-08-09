"""Pruebas del ejecutor reproducible de escenarios (Fase 1 del plan #216)."""
import numpy as np
import pandas as pd
import pytest

from calculos.ejecutor_escenarios import (
    RESULTADOS_SCHEMA_VERSION,
    ejecutar_escenarios,
)
from calculos.escenarios_fase4 import (
    capturar_base_comparacion,
    construir_definicion_escenarios,
)
from tests.test_escenarios_fase4 import _estado_base

# Panel c-Si 60 celdas con SDM calibrado típico (valores físicamente plausibles).
_PANEL_SDM = {
    "nombre": "ASP-ST1-T40",
    "Pmax_stc": 300.0,
    "tecnologia": "Mono-Si",
    "Isc_stc": 9.8,
    "Voc_stc": 40.0,
    "Imp_stc": 9.2,
    "Vmp_stc": 32.6,
    "Tk_alfa": 0.05,
    "NOCT": 45.0,
    "a_ref": 1.6,
    "I_L_ref": 9.85,
    "I_o_ref": 3.0e-10,
    "R_s": 0.35,
    "R_sh_ref": 400.0,
}


def _estado_con_panel_sdm():
    state = _estado_base()
    state["panel_dict"] = dict(_PANEL_SDM)
    return state


def _definicion_con_base(state):
    definicion = construir_definicion_escenarios(
        nombre_proyecto="Teusaquillo",
        fuente_horizonte=False,
        fuente_sketchup=True,
        tipo_optimizacion="paneles",
        panel_nombre=state["panel_nombre_dim"],
        inversor_nombre=state["inversor_nombre_dim"],
    )
    definicion["base_comparacion"] = capturar_base_comparacion(state)
    return definicion


def _df_fs(fs: float) -> pd.DataFrame:
    """FS geométrico constante en horas diurnas de los días 21 de cada mes."""
    filas = [
        {"mes": mes, "dia": 21, "hora": hora, "FS_geometrico": fs}
        for mes in range(1, 13)
        for hora in range(8, 17)
    ]
    return pd.DataFrame(filas)


def _poa_diurna(idx) -> np.ndarray:
    horas = idx.hour.to_numpy()
    return np.where((horas >= 6) & (horas <= 18), 450.0, 0.0)


def _ejecutar(state, definicion, *, df_opt=None):
    return ejecutar_escenarios(
        definicion=definicion,
        base_estado_actual=capturar_base_comparacion(state),
        tmy=state["tmy_df"],
        poa_global=_poa_diurna(state["tmy_df"].index),
        panel=state["panel_dict"],
        n_serie=state["N_serie"],
        n_paralelo=state["N_paneles_dim"] // state["N_serie"],
        eta_inversor=state["eta_inversor"],
        df_fs_actual=_df_fs(0.5),
        df_fs_optimizada=df_opt,
    )


def test_ejecuta_referencia_y_actual_con_optimizada_pendiente():
    state = _estado_con_panel_sdm()
    definicion = _definicion_con_base(state)
    resultados = _ejecutar(state, definicion)

    assert resultados["schema_version"] == RESULTADOS_SCHEMA_VERSION
    assert resultados["base_id"] == definicion["base_comparacion"]["base_id"]
    ref = resultados["referencia"]
    act = resultados["actual"]
    assert ref["estado"] == act["estado"] == "calculado"
    assert ref["E_AC_anual_kWh"] > 0
    # La sombra geométrica solo puede reducir energía, nunca aumentarla.
    assert act["E_AC_anual_kWh"] < ref["E_AC_anual_kWh"]
    # E_AC = E_DC × eta (sin factores ocultos).
    assert ref["E_AC_anual_kWh"] == pytest.approx(
        ref["E_DC_anual_kWh"] * state["eta_inversor"], abs=0.1
    )
    assert resultados["optimizada"]["estado"] == "pendiente_parametros"
    assert "E_AC_anual_kWh" not in resultados["optimizada"]


def test_reproducibilidad_misma_base_mismos_resultados():
    state = _estado_con_panel_sdm()
    definicion = _definicion_con_base(state)
    r1 = _ejecutar(state, definicion)
    r2 = _ejecutar(state, definicion)
    assert r1 == r2


def test_optimizada_con_menos_sombra_recupera_energia():
    state = _estado_con_panel_sdm()
    definicion = _definicion_con_base(state)
    resultados = _ejecutar(state, definicion, df_opt=_df_fs(0.1))
    ref = resultados["referencia"]["E_AC_anual_kWh"]
    act = resultados["actual"]["E_AC_anual_kWh"]
    opt = resultados["optimizada"]["E_AC_anual_kWh"]
    assert act < opt <= ref
    assert resultados["optimizada"]["fuente_p_shade"] == "fs_geometrico_optimizado"


def test_rechaza_estado_que_difiere_de_la_base_congelada():
    state = _estado_con_panel_sdm()
    definicion = _definicion_con_base(state)
    state_drift = _estado_con_panel_sdm()
    state_drift["eta_inversor"] = 0.90  # cambia la configuración eléctrica
    with pytest.raises(ValueError, match="no comparten la misma base"):
        ejecutar_escenarios(
            definicion=definicion,
            base_estado_actual=capturar_base_comparacion(state_drift),
            tmy=state["tmy_df"],
            poa_global=_poa_diurna(state["tmy_df"].index),
            panel=state["panel_dict"],
            n_serie=state["N_serie"],
            n_paralelo=state["N_paneles_dim"] // state["N_serie"],
            eta_inversor=state["eta_inversor"],
            df_fs_actual=_df_fs(0.5),
        )


def test_rechaza_base_incompleta():
    state = _estado_con_panel_sdm()
    state.pop("tmy_ciudad", None)
    state.pop("inversor_dict_dim")
    definicion = _definicion_con_base(state)
    with pytest.raises(ValueError, match="incompleta"):
        _ejecutar(state, definicion)


def test_rechaza_series_no_horarias():
    state = _estado_con_panel_sdm()
    definicion = _definicion_con_base(state)
    with pytest.raises(ValueError, match="8760"):
        ejecutar_escenarios(
            definicion=definicion,
            base_estado_actual=capturar_base_comparacion(state),
            tmy=state["tmy_df"],
            poa_global=np.full(100, 450.0),
            panel=state["panel_dict"],
            n_serie=state["N_serie"],
            n_paralelo=state["N_paneles_dim"] // state["N_serie"],
            eta_inversor=state["eta_inversor"],
            df_fs_actual=_df_fs(0.5),
        )


def test_rechaza_panel_distinto_al_congelado():
    state = _estado_con_panel_sdm()
    definicion = _definicion_con_base(state)
    otro_panel = dict(_PANEL_SDM, nombre="OTRO-PANEL-X")
    with pytest.raises(ValueError, match="no coincide con el"):
        ejecutar_escenarios(
            definicion=definicion,
            base_estado_actual=capturar_base_comparacion(state),
            tmy=state["tmy_df"],
            poa_global=_poa_diurna(state["tmy_df"].index),
            panel=otro_panel,
            n_serie=state["N_serie"],
            n_paralelo=state["N_paneles_dim"] // state["N_serie"],
            eta_inversor=state["eta_inversor"],
            df_fs_actual=_df_fs(0.5),
        )


def test_rechaza_configuracion_electrica_distinta_a_la_congelada():
    state = _estado_con_panel_sdm()
    definicion = _definicion_con_base(state)
    with pytest.raises(ValueError, match="N_serie"):
        ejecutar_escenarios(
            definicion=definicion,
            base_estado_actual=capturar_base_comparacion(state),
            tmy=state["tmy_df"],
            poa_global=_poa_diurna(state["tmy_df"].index),
            panel=state["panel_dict"],
            n_serie=state["N_serie"] + 1,
            n_paralelo=state["N_paneles_dim"] // state["N_serie"],
            eta_inversor=state["eta_inversor"],
            df_fs_actual=_df_fs(0.5),
        )


def test_rechaza_poa_no_finita():
    state = _estado_con_panel_sdm()
    definicion = _definicion_con_base(state)
    poa = _poa_diurna(state["tmy_df"].index).astype(float)
    poa[100] = np.inf
    with pytest.raises(ValueError, match="infinitos"):
        ejecutar_escenarios(
            definicion=definicion,
            base_estado_actual=capturar_base_comparacion(state),
            tmy=state["tmy_df"],
            poa_global=poa,
            panel=state["panel_dict"],
            n_serie=state["N_serie"],
            n_paralelo=state["N_paneles_dim"] // state["N_serie"],
            eta_inversor=state["eta_inversor"],
            df_fs_actual=_df_fs(0.5),
        )


def test_rechaza_fs_fuera_de_rango():
    state = _estado_con_panel_sdm()
    definicion = _definicion_con_base(state)
    with pytest.raises(ValueError, match=r"\[0, 1\]|entre 0 y 1|fuera"):
        ejecutar_escenarios(
            definicion=definicion,
            base_estado_actual=capturar_base_comparacion(state),
            tmy=state["tmy_df"],
            poa_global=_poa_diurna(state["tmy_df"].index),
            panel=state["panel_dict"],
            n_serie=state["N_serie"],
            n_paralelo=state["N_paneles_dim"] // state["N_serie"],
            eta_inversor=state["eta_inversor"],
            df_fs_actual=_df_fs(1.5),
        )


def test_rechaza_panel_sin_noct():
    state = _estado_con_panel_sdm()
    state["panel_dict"] = {
        k: v for k, v in _PANEL_SDM.items() if k != "NOCT"
    }
    definicion = _definicion_con_base(state)
    with pytest.raises(ValueError, match="NOCT"):
        _ejecutar(state, definicion)
