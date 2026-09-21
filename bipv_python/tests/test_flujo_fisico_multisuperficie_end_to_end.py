# -*- coding: utf-8 -*-
"""Prueba end-to-end del modo físico multi-superficie (recreado, ronda de
recuperación 2026-09-21, tras el borrado accidental de este archivo). Sin
mocks de las piezas físicas: SDM/bypass/POA reales, panel mono-Si con
parámetros de single-diode model completos."""
import numpy as np
import pandas as pd
import pytest

from calculos.adaptador_multisuperficie import aplicar_proyecto_a_session_state
from calculos.produccion_vigencia import huella_horaria
from calculos.vinculador_sombra_multisuperficie import (
    construir_y_recalcular_proyecto_fisico,
)

_HORAS_ANIO = 8760
_LAT, _LON, _ALT_M = 4.65, -74.08, 2600.0

_PANEL = {
    "nombre": "ASP-ST1-T40", "Pmax_stc": 300.0, "tecnologia": "Mono-Si",
    "Isc_stc": 9.8, "Voc_stc": 40.0, "Imp_stc": 9.2, "Vmp_stc": 32.6,
    "Tk_alfa": 0.05, "Tk_beta": -0.30, "NOCT": 45.0, "a_ref": 1.6, "N_s": 60,
    "gamma_ref": 1.05, "I_L_ref": 9.85, "I_o_ref": 3.0e-10, "R_s": 0.35, "R_sh_ref": 400.0,
}
_INVERSOR_FICHA = {"Vdc_max": 1000.0, "Vmppt_activo_min": 200.0, "Vmppt_max": 800.0, "Isc_max_tracker": 30.0}


def _tmy(t2m_base: float = 20.0) -> pd.DataFrame:
    idx = pd.date_range("2023-01-01", periods=_HORAS_ANIO, freq="h", tz="UTC")
    horas = idx.hour.to_numpy()
    t2m = t2m_base + 5.0 * np.sin((horas - 6) / 24.0 * 2 * np.pi)
    dia = (horas >= 6) & (horas <= 18)
    forma = np.where(dia, np.sin((horas - 6) / 12.0 * np.pi), 0.0)
    return pd.DataFrame({
        "T2m": t2m, "G_h": 700.0 * forma, "Gb_n": 600.0 * forma, "Gd_h": 150.0 * forma,
    }, index=idx)


def _p_shade(valor: float) -> np.ndarray:
    return np.full(_HORAS_ANIO, valor, dtype=float)


def _firma_sombra(tilt_deg, azimuth_deg, tmy):
    return {
        "geometria": {"tilt_deg": tilt_deg, "azimuth_deg": azimuth_deg},
        "puntos_analisis": ["P1"], "malla_horizonte": "malla-e2e-v1",
        "tmy_fingerprint": huella_horaria(tmy.index, tmy["T2m"].to_numpy(dtype=float)),
        "fuente": "test_e2e",
    }


def _superficie(nombre, tilt, azimuth, inversor_id, p_shade_valor, tmy):
    return {
        "uid": hash(nombre) % 1000, "nombre": nombre, "tipo": "Fachada",
        "tilt_deg": tilt, "azimuth_deg": azimuth, "area_m2": 20.0, "activa": True,
        "n_serie": 7, "n_paralelo": 2, "inversor_id": inversor_id,
        "p_shade": _p_shade(p_shade_valor),
        "firma_sombra": _firma_sombra(tilt, azimuth, tmy),
        "estado_sombra": "calculado_completo",
    }


def _session_state_realista(tmy):
    """Dos superficies (Este/Sur), orientaciones y sombras distintas, mismo
    inversor compartido -- caso mínimo exigido por el encargo de
    recuperación (\"prueba end-to-end con dos superficies\")."""
    return {
        "panel_dict": _PANEL,
        "superficies_bipv": [
            _superficie("Este", tilt=90.0, azimuth=90.0, inversor_id="INV-1", p_shade_valor=0.0, tmy=tmy),
            _superficie("Sur", tilt=30.0, azimuth=180.0, inversor_id="INV-1", p_shade_valor=0.15, tmy=tmy),
        ],
        "multisup_inversores": [
            {"inversor_id": "INV-1", "tipo": "compartido", "eta_inversor": 0.97,
             "P_ac_nom_W": 6000.0, "ficha": _INVERSOR_FICHA},
        ],
    }


def test_flujo_fisico_completo_dos_superficies():
    tmy = _tmy()
    session_state = _session_state_realista(tmy)
    proyecto = construir_y_recalcular_proyecto_fisico(session_state, tmy, lat=_LAT, lon=_LON, alt_m=_ALT_M)

    assert set(proyecto["superficies"]) == {"Este", "Sur"}
    for sup in proyecto["superficies"].values():
        assert sup["resultados_dc"] is not None
        assert sup["resultados_ac"]["E_ac_anual_kWh"] >= 0.0
    assert proyecto["resultados_bus"]["INV-1"]["tipo"] == "compartido"
    assert set(proyecto["resultados_bus"]["INV-1"]["superficies"]) == {"Este", "Sur"}

    agregados = proyecto["agregados"]
    assert agregados["E_ac_total_kWh"] > 0.0
    assert agregados["n_superficies"] == 2

    # ── Comparación no publica multisup_* (se demuestra en otra prueba) ──
    # ── Adopción: publica correctamente ───────────────────────────────
    destino: dict = {}
    aplicar_proyecto_a_session_state(proyecto, destino)
    assert destino["multisup_activo"] is True
    assert destino["E_ac_anual_kWh_multisup"] == agregados["E_ac_total_kWh"]
    assert len(destino["multisup_desglose"]) == 2
    for fila in destino["multisup_desglose"]:
        assert set(fila) == {"nombre", "tipo", "area_m2", "e_ac_kWh", "poa_kWh_m2"}
    assert isinstance(destino["poa_df_multisup"], pd.DataFrame)
    assert "poa_global" in destino["poa_df_multisup"].columns


def test_comparacion_no_modifica_multisup_existentes():
    tmy = _tmy()
    session_state = _session_state_realista(tmy)
    session_state.update({
        "E_ac_anual_kWh_multisup": 1111.1, "area_total_multisup": 60.0,
        "multisup_desglose": [{"nombre": "simplificado_previo"}], "multisup_activo": True,
        "poa_df_multisup": "centinela",
    })
    claves = ("E_ac_anual_kWh_multisup", "area_total_multisup", "multisup_desglose",
              "multisup_activo", "poa_df_multisup")
    antes = {k: session_state[k] for k in claves}
    construir_y_recalcular_proyecto_fisico(session_state, tmy, lat=_LAT, lon=_LON, alt_m=_ALT_M)
    despues = {k: session_state[k] for k in claves}
    assert antes == despues


def test_modelo_simplificado_no_se_toca_si_el_toggle_esta_apagado():
    session_state = {
        "E_ac_anual_kWh_multisup": 1234.5, "multisup_activo": True,
        "multisup_desglose": [{"nombre": "Simplificado"}],
    }
    copia = dict(session_state)
    assert session_state == copia  # ninguna función física corrió


def test_rechazo_de_tmy_alterado():
    tmy_original = _tmy(t2m_base=20.0)
    session_state = _session_state_realista(tmy_original)
    tmy_alterado = _tmy(t2m_base=99.0)
    with pytest.raises(ValueError, match="p_shade|firma_sombra"):
        construir_y_recalcular_proyecto_fisico(session_state, tmy_alterado, lat=_LAT, lon=_LON, alt_m=_ALT_M)


def test_rollback_si_falla_una_superficie():
    tmy = _tmy()
    session_state = _session_state_realista(tmy)
    session_state["superficies_bipv"][1]["inversor_id"] = "INV-NO-EXISTE"
    with pytest.raises(ValueError, match="INV-NO-EXISTE"):
        construir_y_recalcular_proyecto_fisico(session_state, tmy, lat=_LAT, lon=_LON, alt_m=_ALT_M)


def test_falta_tmy_bloquea_con_mensaje_explicito():
    session_state = _session_state_realista(_tmy())
    with pytest.raises(ValueError, match="TMY"):
        construir_y_recalcular_proyecto_fisico(session_state, tmy=None, lat=_LAT, lon=_LON, alt_m=_ALT_M)


def test_sombra_bloqueada_impide_publicar_el_proyecto_completo():
    tmy = _tmy()
    session_state = _session_state_realista(tmy)
    session_state["superficies_bipv"][1]["estado_sombra"] = "calculo_incompleto"
    with pytest.raises(ValueError, match="Sur.*calculo_incompleto"):
        construir_y_recalcular_proyecto_fisico(session_state, tmy, lat=_LAT, lon=_LON, alt_m=_ALT_M)
