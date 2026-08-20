"""
Optimization Contract — Fase 3, Paso 4: perfiles de inversionista.

Un mismo candidato técnico puede ser "óptimo" para un inversionista y no
para otro — depende de qué mínimos exige. InvestorProfile es ese contrato;
optimization/bankability.py lo evalúa contra un FinancialResult real.

Los tres presets de abajo son puntos de partida EDITABLES, no un estándar de
mercado documentado (a diferencia de las constantes físicas/regulatorias de
calculos/, que sí citan fuente — UPME, IDEAM, IPCC...). No existe hoy una
referencia única de "IRR mínimo de mercado para BIPV en Colombia"; estos
números están para arrancar una conversación con el inversionista real y
ajustarse, no para tratarse como verdad de catálogo.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class InvestorProfile:
    nombre: str
    minimum_irr_pct: float | None = None
    maximum_payback_anos: float | None = None
    minimum_npv_usd: float | None = None
    maximum_capex_usd: float | None = None
    descripcion: str = ""

    # Deliberadamente NO incluye minimum_dscr: no existe todavía un modelo
    # de financiamiento con deuda en calculos/financiero.py (confirmado en
    # la auditoría de Fase 1). Agregar un campo DSCR sin poder calcularlo
    # sería fabricar un criterio que nunca se evalúa — peor que no tenerlo.


PERFIL_CONSERVADOR = InvestorProfile(
    nombre="Conservador",
    minimum_irr_pct=12.0,
    maximum_payback_anos=8.0,
    minimum_npv_usd=0.0,
    descripcion=(
        "Prioriza payback corto y margen de seguridad sobre retorno máximo. "
        "Punto de partida editable, no un benchmark de mercado."
    ),
)

PERFIL_BALANCEADO = InvestorProfile(
    nombre="Balanceado",
    minimum_irr_pct=15.0,
    maximum_payback_anos=6.0,
    minimum_npv_usd=0.0,
    descripcion="Equilibrio entre retorno y plazo de recuperación. Punto de partida editable.",
)

PERFIL_CRECIMIENTO = InvestorProfile(
    nombre="Crecimiento",
    minimum_irr_pct=20.0,
    maximum_payback_anos=5.0,
    minimum_npv_usd=0.0,
    descripcion="Exige mayor retorno, tolera menos margen. Punto de partida editable.",
)

PERFILES_PRESET: dict[str, InvestorProfile] = {
    p.nombre: p for p in (PERFIL_CONSERVADOR, PERFIL_BALANCEADO, PERFIL_CRECIMIENTO)
}
