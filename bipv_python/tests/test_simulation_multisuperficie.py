# -*- coding: utf-8 -*-
"""
Validación de la ampliación a multi-superficie de run_bipv_simulation()
(Fase 2, después de la auditoría del caso base de una sola superficie).

Reusa el TMY sintético offline y las coordenadas de test_simulation_pipeline.py
(mismo sitio: Bogotá) para no duplicar la construcción del fixture.
"""
import dataclasses

import pytest

from simulation.schemas import (
    BIPVConfiguration,
    SuperficieBIPV,
    ProyectoMultiSuperficie,
)
from simulation.bipv_simulator import run_bipv_simulation, run_bipv_simulation_multisuperficie
from simulation.financial_simulator import run_financial_simulation
from simulation.schemas import FinancialConfiguration

from tests.test_simulation_pipeline import (
    _tmy_sintetico_offline,
    _config_base,
    LAT, LON, ALT_M,
)
from datos.tecnologias_bipv import ASP_ST1_T40


@pytest.fixture(scope="module")
def tmy_bogota():
    return _tmy_sintetico_offline(LAT, LON, ALT_M)


def _superficie(nombre, tilt, azimuth, area_m2=30.0, activa=True, **overrides):
    base = _config_base()
    cfg = dataclasses.replace(
        base, tilt=tilt, azimuth=azimuth, area_m2=area_m2,
        N_serie=6, N_strings_tracker=2, N_mppt=1,
        **overrides,
    )
    return SuperficieBIPV(nombre=nombre, config=cfg, tipo="Fachada", activa=activa)


def _proyecto_dos_superficies(activa_techo=True):
    return ProyectoMultiSuperficie(
        lat=LAT, lon=LON, alt_m=ALT_M,
        superficies=[
            _superficie("Fachada Sur", tilt=90, azimuth=180, area_m2=40.0),
            _superficie("Techo", tilt=10, azimuth=180, area_m2=25.0, activa=activa_techo),
        ],
    )


def test_multisuperficie_agrega_correctamente_contra_calculo_independiente(tmy_bogota):
    proyecto = _proyecto_dos_superficies()
    r = run_bipv_simulation_multisuperficie(proyecto, tmy=tmy_bogota)

    assert set(r.resultados_por_superficie.keys()) == {"Fachada Sur", "Techo"}

    # Cross-check: correr cada superficie por separado con run_bipv_simulation
    # (el mismo tmy) y comparar contra lo que agregó el multi-superficie —
    # no basta con "no truena", tiene que sumar exactamente lo mismo.
    esperado_fachada = run_bipv_simulation(proyecto.superficies[0].config, tmy=tmy_bogota)
    esperado_techo = run_bipv_simulation(
        dataclasses.replace(proyecto.superficies[1].config, lat=LAT, lon=LON, alt_m=ALT_M),
        tmy=tmy_bogota,
    )

    assert r.resultados_por_superficie["Fachada Sur"].E_ac_anual_kWh == pytest.approx(
        esperado_fachada.E_ac_anual_kWh
    )
    assert r.resultados_por_superficie["Techo"].E_ac_anual_kWh == pytest.approx(
        esperado_techo.E_ac_anual_kWh
    )
    assert r.E_ac_anual_kWh == pytest.approx(
        esperado_fachada.E_ac_anual_kWh + esperado_techo.E_ac_anual_kWh
    )
    assert r.P_dc_stc_kW == pytest.approx(
        esperado_fachada.P_dc_stc_kW + esperado_techo.P_dc_stc_kW
    )
    assert r.area_total_m2 == pytest.approx(40.0 + 25.0)

    # PR ponderado debe caer entre el menor y el mayor PR individual.
    pr_min = min(esperado_fachada.PR, esperado_techo.PR)
    pr_max = max(esperado_fachada.PR, esperado_techo.PR)
    assert pr_min - 1e-9 <= r.PR_ponderado <= pr_max + 1e-9


def test_superficie_inactiva_se_excluye_del_calculo_pero_no_se_pierde(tmy_bogota):
    proyecto = _proyecto_dos_superficies(activa_techo=False)
    r = run_bipv_simulation_multisuperficie(proyecto, tmy=tmy_bogota)

    assert set(r.resultados_por_superficie.keys()) == {"Fachada Sur"}
    assert len(r.superficies) == 2   # trazabilidad: la inactiva sigue listada
    assert r.area_total_m2 == pytest.approx(40.0)   # solo la activa cuenta


def test_sin_superficies_activas_lanza_error(tmy_bogota):
    proyecto = ProyectoMultiSuperficie(
        lat=LAT, lon=LON, alt_m=ALT_M,
        superficies=[_superficie("Techo", tilt=10, azimuth=180, activa=False)],
    )
    with pytest.raises(ValueError, match="ninguna superficie activa"):
        run_bipv_simulation_multisuperficie(proyecto, tmy=tmy_bogota)


def test_nombres_duplicados_entre_activas_lanza_error(tmy_bogota):
    proyecto = ProyectoMultiSuperficie(
        lat=LAT, lon=LON, alt_m=ALT_M,
        superficies=[
            _superficie("Fachada", tilt=90, azimuth=180),
            _superficie("Fachada", tilt=90, azimuth=90),   # mismo nombre, activa
        ],
    )
    with pytest.raises(ValueError, match="duplicados"):
        run_bipv_simulation_multisuperficie(proyecto, tmy=tmy_bogota)


def test_lat_lon_alt_de_la_superficie_se_ignoran_a_favor_del_proyecto(tmy_bogota):
    # Si alguien arma una SuperficieBIPV con una config que trae otra
    # ubicación (copy-paste de otro proyecto, por ejemplo), el resultado
    # debe usar la ubicación del proyecto, no la de la superficie.
    base = _config_base()
    cfg_otra_ubicacion = dataclasses.replace(base, lat=999.0, lon=999.0, alt_m=999.0)
    proyecto = ProyectoMultiSuperficie(
        lat=LAT, lon=LON, alt_m=ALT_M,
        superficies=[SuperficieBIPV(nombre="X", config=cfg_otra_ubicacion)],
    )
    r = run_bipv_simulation_multisuperficie(proyecto, tmy=tmy_bogota)
    assert r.resultados_por_superficie["X"].E_ac_anual_kWh > 0   # no explota ni usa lat=999


def test_run_financial_simulation_funciona_sobre_multisuperficie_por_duck_typing(tmy_bogota):
    proyecto = _proyecto_dos_superficies()
    energy = run_bipv_simulation_multisuperficie(proyecto, tmy=tmy_bogota)

    fin = run_financial_simulation(energy, FinancialConfiguration(
        capex_usd=energy.P_dc_stc_kW * 1000 * 1.5,
        tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    ))
    assert fin.metricas["vpn_usd"] is not None
    assert len(fin.flujos) == 26   # n_anos=25 default + año 0
