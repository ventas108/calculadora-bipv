"""
Función maestra del motor financiero — Fase 2 del blueprint de extracción.

run_financial_simulation() consume el SimulationResult de
run_bipv_simulation() (nunca vuelve a tocar física) y encadena
calculos/financiero.py exactamente como lo hace 7_💰_Financiero.py hoy.
"""
from calculos import financiero
from datos.ciudades_colombia import LEY_1715

from simulation.schemas import FinancialConfiguration, FinancialResult
from simulation.bipv_simulator import SimulationResult


def run_financial_simulation(
    energy: SimulationResult,
    fin: FinancialConfiguration,
) -> FinancialResult:
    e_ac_kWh_anual = energy.E_ac_anual_kWh

    beneficios_1715 = None
    beneficios_usd = 0.0
    advertencia_ley_1715 = None
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

        # Umbral regulatorio real de "autoconsumo a pequeña escala" (Colombia,
        # dato ya existente en datos.ciudades_colombia.LEY_1715 pero sin usar
        # en ningún cálculo hasta ahora -- hallazgo del 28-ago-2026). No se
        # bloquea ni se recalculan los beneficios con otro régimen (esta app
        # no modela el régimen de gran escala) -- solo se advierte, para que
        # el proyecto se revise con un asesor tributario/regulatorio antes de
        # presentar estos beneficios como definitivos.
        _umbral_kW = LEY_1715["potencia_maxima_autoconsumo_kW"]
        if energy.P_dc_stc_kW > _umbral_kW:
            advertencia_ley_1715 = (
                f"Proyecto de {energy.P_dc_stc_kW:,.0f} kW DC supera el umbral de "
                f"{_umbral_kW:,.0f} kW de autoconsumo a pequeña escala (Ley 1715). "
                "Los beneficios fiscales mostrados se calcularon con el mismo modelo "
                "de autoconsumo -- el régimen real para generación a gran escala puede "
                "ser distinto. Verifica con un asesor tributario/regulatorio antes de "
                "usar estas cifras como definitivas."
            )

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
        advertencia_ley_1715=advertencia_ley_1715,
    )
