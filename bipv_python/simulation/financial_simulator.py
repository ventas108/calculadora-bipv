"""
Función maestra del motor financiero — Fase 2 del blueprint de extracción.

run_financial_simulation() consume el SimulationResult de
run_bipv_simulation() (nunca vuelve a tocar física) y encadena
calculos/financiero.py exactamente como lo hace 7_💰_Financiero.py hoy.
"""
from calculos import financiero

from simulation.schemas import FinancialConfiguration, FinancialResult
from simulation.bipv_simulator import SimulationResult


def run_financial_simulation(
    energy: SimulationResult,
    fin: FinancialConfiguration,
) -> FinancialResult:
    e_ac_kWh_anual = energy.E_ac_anual_kWh

    beneficios_1715 = None
    beneficios_usd = 0.0
    if fin.aplicar_ley_1715:
        beneficios_1715 = financiero.calcular_beneficios_ley_1715(
            fin.capex_usd,
            fin.fraccion_equipo_1715,
            fin.tasa_renta_1715,
            fin.tipo_cambio,
            fin.tasa_descuento,
            fin.n_anos,
        )
        beneficios_usd = beneficios_1715["total_usd"]

    flujos = financiero.calcular_flujo_caja(
        fin.capex_usd,
        beneficios_usd,
        e_ac_kWh_anual,
        fin.tarifa_cop_kWh,
        fin.tipo_cambio,
        fin.tasa_escalacion_tarifa,
        fin.tasa_degradacion_pct,
        fin.opex_pct_capex,
        fin.n_anos,
        tasa_escalacion_opex=fin.tasa_escalacion_opex,
    )

    metricas = financiero.calcular_metricas(
        flujos, fin.tasa_descuento, fin.capex_usd, e_ac_kWh_anual, fin.tipo_cambio,
    )

    return FinancialResult(
        beneficios_1715=beneficios_1715,
        flujos=flujos,
        metricas=metricas,
    )
