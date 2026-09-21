"""Pruebas del adaptador puro session_state <-> proyecto multi-superficie
(recreado, ronda de recuperación 2026-09-21). Cubre bloqueo de sombra no
aceptable, validación de inversores conectada, y la ponderación por área de
poa_df_multisup (restaurada -- solo devolvía un resultado con exactamente 1
superficie tras la reconstrucción posterior al borrado accidental)."""
import numpy as np
import pandas as pd
import pytest

from calculos.adaptador_multisuperficie import (
    aplicar_proyecto_a_session_state,
    construir_proyecto_desde_session_state,
)

PANEL = {"nombre": "P", "NOCT": 45.0, "Pmax_stc": 300.0}
FIRMA_SOMBRA = {
    "geometria": {"tilt_deg": 90.0, "azimuth_deg": 90.0},
    "puntos_analisis": ["P1"], "malla_horizonte": "test",
    "tmy_fingerprint": "abc", "fuente": "test",
}


def _estado_superficie(**overrides):
    base = {
        "nombre": "Este", "tipo": "Fachada", "tilt_deg": 90.0, "azimuth_deg": 90.0,
        "area_m2": 20.0, "activa": True, "n_serie": 7, "n_paralelo": 2,
        "inversor_id": "INV-1", "p_shade": np.zeros(8760), "firma_sombra": FIRMA_SOMBRA,
    }
    base.update(overrides)
    return base


def _inversor(**overrides):
    base = {"inversor_id": "INV-1", "tipo": "dedicado", "eta_inversor": 0.97,
            "P_ac_nom_W": 4000.0, "ficha": {"Vdc_max": 1000.0}}
    base.update(overrides)
    return base


def _estado(superficies=None, inversores=None):
    return {
        "panel_dict": PANEL,
        "superficies_bipv": superficies if superficies is not None else [_estado_superficie()],
        "multisup_inversores": inversores if inversores is not None else [_inversor()],
    }


@pytest.mark.parametrize("campo", ["n_serie", "n_paralelo", "p_shade", "firma_sombra"])
def test_entrada_rechaza_campo_faltante_por_superficie(campo):
    estado = _estado()
    estado["superficies_bipv"][0][campo] = None
    with pytest.raises(ValueError, match="Este"):
        construir_proyecto_desde_session_state(estado)


def test_entrada_rechaza_superficie_sin_inversor_id():
    estado = _estado()
    estado["superficies_bipv"][0]["inversor_id"] = None
    with pytest.raises(ValueError, match="'Este'.*no tiene inversor asignado"):
        construir_proyecto_desde_session_state(estado)


def test_p_shade_fuera_de_rango_bloquea():
    estado = _estado()
    p = np.zeros(8760)
    p[0] = 1.5
    estado["superficies_bipv"][0]["p_shade"] = p
    with pytest.raises(ValueError, match="p_shade invalido"):
        construir_proyecto_desde_session_state(estado)


def test_p_shade_con_longitud_incorrecta_bloquea():
    estado = _estado()
    estado["superficies_bipv"][0]["p_shade"] = np.zeros(100)
    with pytest.raises(ValueError, match="8760"):
        construir_proyecto_desde_session_state(estado)


@pytest.mark.parametrize("estado_bloqueante", ["calculo_incompleto", "error_geometrico", "resolucion_insuficiente"])
def test_estado_sombra_no_aceptable_bloquea_aunque_p_shade_este_presente(estado_bloqueante):
    estado = _estado(superficies=[_estado_superficie(estado_sombra=estado_bloqueante)])
    with pytest.raises(ValueError, match=f"'Este'.*{estado_bloqueante}"):
        construir_proyecto_desde_session_state(estado)


def test_estado_sombra_aceptable_entra_al_adaptador():
    estado = _estado(superficies=[_estado_superficie(estado_sombra="calculado_completo")])
    proyecto = construir_proyecto_desde_session_state(estado)
    assert list(proyecto["superficies"]) == ["Este"]


def test_superficie_legacy_sin_estado_sombra_sigue_validandose_por_campos():
    estado = _estado()
    assert "estado_sombra" not in estado["superficies_bipv"][0]
    proyecto = construir_proyecto_desde_session_state(estado)
    assert list(proyecto["superficies"]) == ["Este"]


def test_entrada_construye_proyecto_sin_mutar_estado():
    estado = _estado()
    original = estado["superficies_bipv"][0].copy()
    proyecto = construir_proyecto_desde_session_state(estado)
    assert proyecto["schema_version"] == "bipv.transicion-multisuperficie.v1"
    assert proyecto["superficies"]["Este"]["inversor_id"] == "INV-1"
    assert estado["superficies_bipv"][0].keys() == original.keys()


# ── Inversores conectados al flujo real ──────────────────────────────────
def test_asignacion_invalida_bloquea_el_calculo_fisico():
    estado = _estado(superficies=[_estado_superficie(inversor_id="INV-FANTASMA")])
    with pytest.raises(ValueError, match="INV-FANTASMA"):
        construir_proyecto_desde_session_state(estado)


def test_tipo_manual_incorrecto_se_corrige_segun_el_contrato():
    estado = _estado(inversores=[_inversor(tipo="compartido")])  # 1 sola superficie
    proyecto = construir_proyecto_desde_session_state(estado)
    assert proyecto["inversores"]["INV-1"]["tipo"] == "dedicado"


def test_inversor_huerfano_bloquea():
    estado = _estado(inversores=[_inversor(inversor_id="INV-1"), _inversor(inversor_id="INV-HUERFANO")])
    with pytest.raises(ValueError, match="INV-HUERFANO.*no tiene ninguna superficie"):
        construir_proyecto_desde_session_state(estado)


def test_una_superficie_valida_y_otra_invalida_no_publica_nada():
    estado = _estado(superficies=[
        _estado_superficie(nombre="Este", inversor_id="INV-1"),
        _estado_superficie(nombre="Oeste", inversor_id=None),
    ])
    with pytest.raises(ValueError):
        construir_proyecto_desde_session_state(estado)


def test_dos_superficies_mismo_inversor_derivan_compartido():
    estado = _estado(
        superficies=[
            _estado_superficie(nombre="Este", inversor_id="INV-1"),
            _estado_superficie(nombre="Oeste", inversor_id="INV-1"),
        ],
        inversores=[_inversor(tipo="dedicado")],  # tipo manual incorrecto, se corrige
    )
    proyecto = construir_proyecto_desde_session_state(estado)
    assert set(proyecto["superficies"]) == {"Este", "Oeste"}
    assert proyecto["inversores"]["INV-1"]["tipo"] == "compartido"


# ── aplicar_proyecto_a_session_state: poa_df_multisup ponderado ─────────
def test_salida_publica_misma_forma_multisup_y_poa_ponderada():
    indice = pd.date_range("2023-01-01", periods=8760, freq="h", tz="UTC")
    poa = pd.DataFrame({"poa_global": np.full(8760, 500.0)}, index=indice)
    proyecto = {
        "superficies": {"Este": {
            "nombre": "Este", "tipo": "Fachada", "area_m2": 20.0, "poa_df": poa,
            "resultados_dc": {"poa_anual_kWh_m2": 1000.0},
            "resultados_ac": {"E_ac_anual_kWh": 2000.0},
        }},
        "agregados": {"E_ac_total_kWh": 2000.0, "area_total_m2": 20.0},
    }
    session_state = {}
    aplicar_proyecto_a_session_state(proyecto, session_state)
    assert session_state["multisup_activo"] is True
    np.testing.assert_allclose(session_state["poa_df_multisup"]["poa_global"], 500.0)


def test_poa_ponderada_con_dos_o_mas_superficies_no_es_none():
    """Regresión: la reconstrucción posterior al borrado solo daba un
    resultado cuando exactamente UNA superficie tenía poa_df -- con 2+
    (el caso normal) siempre daba None. Verificado con la fórmula real:
    promedio ponderado por área."""
    indice = pd.date_range("2023-01-01", periods=8760, freq="h", tz="UTC")
    poa_a = pd.DataFrame({"poa_global": np.full(8760, 400.0)}, index=indice)
    poa_b = pd.DataFrame({"poa_global": np.full(8760, 800.0)}, index=indice)
    proyecto = {
        "superficies": {
            "A": {"nombre": "A", "tipo": "Fachada", "area_m2": 10.0, "poa_df": poa_a,
                  "resultados_dc": {"poa_anual_kWh_m2": 1000.0}, "resultados_ac": {"E_ac_anual_kWh": 1000.0}},
            "B": {"nombre": "B", "tipo": "Techo", "area_m2": 30.0, "poa_df": poa_b,
                  "resultados_dc": {"poa_anual_kWh_m2": 2000.0}, "resultados_ac": {"E_ac_anual_kWh": 3000.0}},
        },
        "agregados": {"E_ac_total_kWh": 4000.0, "area_total_m2": 40.0},
    }
    session_state = {}
    aplicar_proyecto_a_session_state(proyecto, session_state)
    assert session_state["poa_df_multisup"] is not None
    # Ponderado por área: (10*400 + 30*800) / 40 = 700
    np.testing.assert_allclose(session_state["poa_df_multisup"]["poa_global"], 700.0)


def test_salida_no_publica_estado_si_faltan_resultados():
    proyecto = {
        "superficies": {"Este": {"tipo": "Fachada", "area_m2": 20.0}},
        "agregados": {"E_ac_total_kWh": 2000.0, "area_total_m2": 20.0},
    }
    session_state = {"multisup_activo": False}
    with pytest.raises(ValueError, match="resultados completos"):
        aplicar_proyecto_a_session_state(proyecto, session_state)
    assert session_state == {"multisup_activo": False}
