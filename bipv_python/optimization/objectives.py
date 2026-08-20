"""
Optimization Contract — Fase 3, Paso 3: qué se puede maximizar/minimizar.

Registro NOMBRADO de objetivos técnicos y financieros — no funciones sueltas
dispersas, para que un optimizador (Fase 4) o un agente puedan preguntar "qué
objetivos existen" y "en qué dirección es mejor" sin tener que leer el código
de simulation/. Cada objetivo lee de las propiedades que SimulationResult y
FinancialResult ya exponen (Fase 2) — este módulo no recalcula nada.

También cierra un hueco real del contrato: SimulationResult no produce un
CAPEX (solo dimensiona y produce energía), y FinancialConfiguration.capex_usd
no es exógeno — depende del candidato técnico. estimar_capex_parametrico_usd()
es el puente explícito usando calculos.presupuesto.calcular_parametrico()
(Fase 1) para que "optimizar NPV" sea de verdad ejecutable de punta a punta,
no solo una definición en el papel.
"""
from dataclasses import dataclass
from typing import Callable, Literal

from calculos import presupuesto as presupuesto_calc
from simulation.schemas import FinancialResult, SimulationResult

Direccion = Literal["max", "min"]


@dataclass(frozen=True)
class Objective:
    nombre: str
    direccion: Direccion
    unidad: str
    descripcion: str
    extractor: Callable[[SimulationResult, FinancialResult | None], float | None]


def _requiere_financiero(fn):
    def envoltura(sim, fin):
        return None if fin is None else fn(sim, fin)
    return envoltura


OBJETIVOS: dict[str, Objective] = {
    "energia_anual": Objective(
        "energia_anual", "max", "kWh/año",
        "Energía AC anual producida.",
        lambda sim, fin: sim.E_ac_anual_kWh,
    ),
    "pr": Objective(
        "pr", "max", "fracción",
        "Performance Ratio IEC 61724 (incluye pérdidas de cascada y temperatura).",
        lambda sim, fin: sim.PR,
    ),
    "capacidad_instalada": Objective(
        "capacidad_instalada", "max", "kWp",
        "Potencia DC instalada — no es un objetivo en sí, pero es la base de comparación por kWp.",
        lambda sim, fin: sim.P_dc_stc_kW,
    ),
    "npv": Objective(
        "npv", "max", "USD",
        "Valor Presente Neto del proyecto.",
        _requiere_financiero(lambda sim, fin: fin.npv_usd),
    ),
    "irr": Objective(
        "irr", "max", "%",
        "Tasa Interna de Retorno. None si el flujo de caja no tiene solución real (ver calculos.financiero._npv).",
        _requiere_financiero(lambda sim, fin: fin.irr_pct),
    ),
    "payback_simple": Objective(
        "payback_simple", "min", "años",
        "Payback simple. None si el proyecto no recupera la inversión dentro de n_anos.",
        _requiere_financiero(lambda sim, fin: fin.payback_simple_anos),
    ),
    "lcoe": Objective(
        "lcoe", "min", "USD/kWh",
        "Costo nivelado de energía.",
        _requiere_financiero(lambda sim, fin: fin.metricas["lcoe_usd_kWh"]),
    ),
}


def extraer_objetivos(
    sim: SimulationResult,
    fin: FinancialResult | None = None,
) -> dict[str, float | None]:
    """
    Evalúa todos los objetivos registrados sobre un resultado ya simulado.
    Los objetivos financieros quedan en None si no se pasa `fin` — no se
    inventan valores ni se lanza una excepción por no tener CAPEX todavía.
    """
    return {nombre: obj.extractor(sim, fin) for nombre, obj in OBJETIVOS.items()}


def estimar_capex_parametrico_usd(
    sim: SimulationResult,
    tipo_instalacion: str,
    escenario: str = "Base",
    zona: str = "Bogotá / Sabana",
) -> float:
    """
    Puente entre el resultado TÉCNICO (kWp dimensionado) y un CAPEX evaluable
    financieramente, usando la estimación paramétrica de calculos/presupuesto.py
    (Fase 1) — NO reemplaza una cotización real ni el presupuesto detallado;
    es lo que ya usa hoy la pestaña "Estimación Rápida" de 8_💼_Presupuesto.py.

    tipo_instalacion : una clave de calculos.presupuesto.BENCH
                        ("Granja FV campo" | "Techo industrial" | "BIPV fachada/pérgola")
    escenario         : "Optimista" | "Base" | "Conservador"
    zona              : una clave de calculos.presupuesto.ZONA_FACTOR
    """
    resultado = presupuesto_calc.calcular_parametrico(
        sim.P_dc_stc_kW, tipo_instalacion, escenario, zona,
    )
    return resultado["capex_total"]
