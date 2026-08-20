"""
Función maestra del motor físico BIPV — Fase 2 del blueprint de extracción.

run_bipv_simulation(config) es el primer punto de entrada programático real:
antes de esto, "correr una simulación" significaba clickear 5-6 páginas
Streamlit en orden y dejar que mutaran st.session_state entre sí. Este
módulo encadena los mismos módulos de calculos/ que esas páginas ya usan
(no reimplementa nada), en el orden real de dependencias documentado en
calculos/invalidacion.py: ubicación → TMY/POA → sombreado horizonte →
cascada de pérdidas → dimensionamiento → producción.

v1 — alcance (ver docstring de simulation/schemas.py):
    UNA superficie, sombreado por horizonte editable, sin bypass de
    diodos, sin bifacial, sin multi-superficie, sin ray-casting 3D.
    Ampliar esto es trabajo de una fase posterior — no de este commit.
"""
import pandas as pd

from calculos import dimensionamiento
from calculos import mismatch
from calculos import produccion as produccion_calc
from calculos import solar

from simulation.schemas import BIPVConfiguration, SimulationResult


def run_bipv_simulation(
    config: BIPVConfiguration,
    tmy: pd.DataFrame | None = None,
) -> SimulationResult:
    """
    Ejecuta el pipeline físico completo para UNA configuración BIPV.

    tmy : si se pasa, se reutiliza en vez de descargar de PVGIS. Es el
          parámetro pensado para cuando esta función se llama muchas veces
          sobre el MISMO sitio (p.ej. desde un optimizador explorando
          decenas de configuraciones de tilt/azimuth/panel) — el TMY no
          cambia entre esas llamadas, solo la geometría/sistema PV.
    """
    if tmy is None:
        tmy = solar.obtener_tmy_pvgis(config.lat, config.lon)

    poa = solar.calcular_poa(
        tmy, config.lat, config.lon, config.alt_m,
        config.tilt, config.azimuth, config.albedo,
    )

    sombreado = mismatch.calcular_sombreado_horizonte(
        config.lat, config.lon, config.alt_m, tmy, poa, config.puntos_horizonte,
    )

    poa_bruta_kWh_m2 = float(poa["poa_global"].clip(lower=0).sum() / 1000.0)
    cascada = mismatch.cascada_perdidas(
        poa_bruta_kWh_m2,
        sombreado["factor_sombra_anual"],
        0.0,   # factor_mismatch_orient: v1 es una sola orientación → 0%
        config.pct_mismatch_fab,
        config.pct_soiling,
        config.pct_cableado,
    )
    factor_pr_mismatch = mismatch.factor_global_perdidas(cascada)

    dim = dimensionamiento.dimensionar_sistema(
        config.panel, config.area_m2, config.N_serie,
        config.N_strings_tracker, config.N_mppt,
    )

    prod = produccion_calc.simular_produccion_anual(
        tmy, poa, config.panel, dim["N_paneles"], config.eta_inversor,
        factor_pr_mismatch, dim["P_dc_stc_kW"], config.k_bipv,
    )

    return SimulationResult(
        tmy=tmy,
        poa=poa,
        sombreado=sombreado,
        cascada=cascada,
        factor_pr_mismatch=factor_pr_mismatch,
        dim=dim,
        produccion=prod,
    )
