"""
Contratos de datos de la Fase 2 (auditoría → Blueprint de extracción):
BIPVConfiguration / SimulationResult y FinancialConfiguration /
FinancialResult son las entradas y salidas explícitas de
run_bipv_simulation() y run_financial_simulation() — el equivalente
programático a lo que hoy solo existe disperso en 323 claves de
st.session_state.

v1 — alcance deliberadamente acotado (ver simulation/bipv_simulator.py):
UNA sola superficie/orientación, sombreado por horizonte editable (NO
ray-casting 3D), sin bypass de diodos, sin bifacial, sin multi-superficie.
Esos casos siguen viviendo solo en las páginas Streamlit hasta que se
amplíe este contrato — no se han tocado en esta fase.

dataclasses en vez de Pydantic a propósito: es el mínimo necesario para
tener un contrato tipado y sin ambigüedad; Pydantic (validación de
esquema, JSON schema para tool-calling de agentes) es una decisión de
una fase posterior, cuando exista una capa de IA real que la necesite.
"""
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class BIPVConfiguration:
    """Entrada de run_bipv_simulation() — una superficie BIPV."""

    # ── Ubicación ──────────────────────────────────────────────────────
    lat: float
    lon: float
    alt_m: float

    # ── Geometría / orientación de la superficie ─────────────────────────
    tilt: float
    azimuth: float
    area_m2: float
    albedo: float = 0.20
    # [(azimuth_Norte_deg, elevacion_obstaculo_deg), ...] — igual formato
    # que calculos.mismatch.calcular_sombreado_horizonte.
    puntos_horizonte: list[tuple[float, float]] = field(default_factory=list)

    # ── Sistema PV ─────────────────────────────────────────────────────
    panel: dict = field(default_factory=dict)   # dict del catálogo MODULOS_BIPV
    N_serie: int = 1
    N_strings_tracker: int = 1
    N_mppt: int = 1
    eta_inversor: float = 0.97
    k_bipv: float = 1.3   # confinamiento térmico BIPV (IEA-PVPS T15); 1.0=ventilado libre

    # ── Pérdidas de cascada además del sombreado de horizonte (%, 0–100) ──
    pct_mismatch_fab: float = 2.0
    pct_soiling: float = 2.0
    pct_cableado: float = 1.5


@dataclass
class SimulationResult:
    """Salida de run_bipv_simulation()."""

    tmy: pd.DataFrame
    poa: pd.DataFrame
    sombreado: dict          # calculos.mismatch.calcular_sombreado_horizonte()
    cascada: list[dict]      # calculos.mismatch.cascada_perdidas()
    factor_pr_mismatch: float
    dim: dict                # calculos.dimensionamiento.dimensionar_sistema()
    produccion: dict         # calculos.produccion.simular_produccion_anual()

    @property
    def E_ac_anual_kWh(self) -> float:
        return self.produccion["E_ac_anual_kWh"]

    @property
    def PR(self) -> float:
        return self.produccion["PR"]

    @property
    def P_dc_stc_kW(self) -> float:
        return self.dim["P_dc_stc_kW"]


# ─────────────────────────────────────────────────────────────────────────
# Multi-superficie — ampliación del alcance v1 (una sola superficie).
#
# Decisión de diseño: cada superficie se simula con el MISMO motor riguroso
# (SDM De Soto 2006 vía calculos.produccion) que la superficie única de
# run_bipv_simulation(), NO con el atajo e_ac = POA × área × eta_panel × PR
# que usa hoy calculos/multi_superficie.py (y por lo tanto 9_Vista_3D.py).
# Ese atajo es más rápido pero menos preciso; usarlo aquí habría reproducido
# exactamente el tipo de "resultado distinto según qué código lo calculó"
# que se corrigió en la unificación de geometría solar (Fase 1). Cuando
# haga falta la versión rápida (para exploración masiva del optimizador),
# se puede envolver como modelo sustituto — pero explícitamente, no por
# duplicación silenciosa.
#
# Fuera de alcance a propósito (igual que en BIPVConfiguration): MPPT
# compartido entre superficies de distinta orientación conectadas al mismo
# inversor (ver calculos/mppt_combinado.py — es un fenómeno eléctrico
# específico, con su propio modelo SDM combinado). v1 asume que cada
# superficie tiene su propio canal MPPT/inversor independiente — la
# arquitectura BIPV más común.
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class SuperficieBIPV:
    """Una superficie física dentro de un proyecto multi-superficie.

    `config` reutiliza BIPVConfiguration completo; lat/lon/alt_m de esa
    config se ignoran y se sobreescriben con la ubicación del proyecto
    (todas las superficies están en el mismo sitio) — ver
    run_bipv_simulation_multisuperficie().
    """
    nombre: str
    config: "BIPVConfiguration"
    tipo: str = "Fachada"   # informativo: Fachada | Techo | Pérgola | Marquesina
    activa: bool = True


@dataclass
class ProyectoMultiSuperficie:
    """Entrada de run_bipv_simulation_multisuperficie()."""

    lat: float
    lon: float
    alt_m: float
    superficies: list[SuperficieBIPV] = field(default_factory=list)


@dataclass
class MultiSurfaceSimulationResult:
    """Salida de run_bipv_simulation_multisuperficie().

    Expone las mismas propiedades que SimulationResult (E_ac_anual_kWh,
    P_dc_stc_kW) para que run_financial_simulation() funcione sin cambios
    sobre un proyecto multi-superficie — duck typing intencional, no
    herencia, para no forzar un solo tipo de "resultado de energía".
    """

    tmy: pd.DataFrame
    resultados_por_superficie: dict[str, SimulationResult]
    superficies: list[SuperficieBIPV]   # incluye inactivas, para trazabilidad

    @property
    def E_ac_anual_kWh(self) -> float:
        return sum(r.E_ac_anual_kWh for r in self.resultados_por_superficie.values())

    @property
    def P_dc_stc_kW(self) -> float:
        return sum(r.P_dc_stc_kW for r in self.resultados_por_superficie.values())

    @property
    def area_total_m2(self) -> float:
        return sum(
            s.config.area_m2 for s in self.superficies
            if s.activa and s.nombre in self.resultados_por_superficie
        )

    @property
    def PR_ponderado(self) -> float:
        """PR ponderado por energía DC de cada superficie — evita que una
        superficie pequeña con PR atípico distorsione el promedio simple."""
        resultados = list(self.resultados_por_superficie.values())
        e_dc_total = sum(r.produccion["E_dc_anual_kWh"] for r in resultados)
        if e_dc_total <= 0:
            return 0.0
        return sum(r.PR * r.produccion["E_dc_anual_kWh"] for r in resultados) / e_dc_total


@dataclass
class FinancialConfiguration:
    """Entrada de run_financial_simulation()."""

    capex_usd: float
    tarifa_cop_kWh: float
    tipo_cambio: float
    tasa_descuento: float = 0.10
    tasa_escalacion_tarifa: float = 3.0   # %/año
    tasa_degradacion_pct: float = 0.5     # %/año
    opex_pct_capex: float = 1.5           # % CAPEX/año (año 1)
    tasa_escalacion_opex: float = 0.0     # %/año
    n_anos: int = 25
    aplicar_ley_1715: bool = True
    fraccion_equipo_1715: float = 0.65
    tasa_renta_1715: float = 0.35


@dataclass
class FinancialResult:
    """Salida de run_financial_simulation()."""

    beneficios_1715: dict | None   # None si aplicar_ley_1715=False
    flujos: list[dict]             # calculos.financiero.calcular_flujo_caja()
    metricas: dict                 # calculos.financiero.calcular_metricas()

    @property
    def npv_usd(self) -> float:
        return self.metricas["vpn_usd"]

    @property
    def irr_pct(self) -> float | None:
        return self.metricas["tir_pct"]

    @property
    def payback_simple_anos(self) -> float | None:
        return self.metricas["payback_simple"]
