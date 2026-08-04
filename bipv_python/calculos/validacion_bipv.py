"""
validacion_bipv.py — Chequeos de plausibilidad física para paneles BIPV.

Tarea #151: el modelo de producción asume que los parámetros eléctricos del
catálogo (Isc_stc, Pmax_stc) ya incluyen la transparencia τ del vidrio
(Isc_real = Isc_celda × (1−τ)). Si un panel se carga con valores "de celda
pura" (sin descontar τ), la producción queda sobreestimada EN SILENCIO.

El chequeo no necesita conocer la configuración de celdas: usa la eficiencia
implícita del área activa,

    η_módulo  = Pmax_stc / (área_m2 × 1000 W/m²)
    η_activa  = η_módulo / (1 − τ)

y la compara contra el máximo físicamente plausible de cada tecnología a STC.
Si η_activa supera ese techo, los parámetros eléctricos NO pueden incluir τ
(o el área/τ declarados son incorrectos). Si η_activa es absurdamente baja,
lo más probable es que τ se haya descontado DOS veces en los datos.

Referencia sana: ASP-ST1-T40 (CdTe, τ=40%) → η_módulo 8.75 %, η_activa 14.6 %.
"""
from __future__ import annotations

# Techo de eficiencia de ÁREA ACTIVA a STC por tecnología (%, generoso:
# récord comercial + margen). Fuente: NREL Best Research-Cell Efficiency
# (módulos comerciales quedan por debajo).
ETA_ACTIVA_MAX_PCT = {
    "CdTe":    19.0,
    "CIGS":    20.0,
    "Mono-Si": 24.5,
    "Poli-Si": 21.0,
    "a-Si":    12.0,
}
_ETA_MAX_DEFAULT = 24.5   # tecnología desconocida → techo más permisivo
_ETA_ACTIVA_MIN_PCT = 4.0  # por debajo, sospecha de τ descontada dos veces
_MARGEN = 1.05             # 5 % de tolerancia sobre el techo


def verificar_isc_transparencia(panel: dict) -> dict:
    """
    Verifica si los parámetros eléctricos del panel son coherentes con su
    transparencia τ declarada.

    Args:
        panel: dict del catálogo con (al menos) Pmax_stc, area_m2,
               transparencia_pct y opcionalmente tecnologia.

    Returns:
        {
          "estado": "ok" | "sospechoso_alto" | "sospechoso_bajo" | "sin_datos",
          "eta_modulo_pct":  float | None,   # eficiencia sobre área bruta
          "eta_activa_pct":  float | None,   # implícita sobre área activa
          "eta_max_pct":     float,          # techo usado para la tecnología
          "sobreestimacion_pct": float | None,  # exceso sobre el techo (solo alto)
          "mensaje": str,
        }
    """
    tecno = str(panel.get("tecnologia") or "").strip()
    eta_max = ETA_ACTIVA_MAX_PCT.get(tecno, _ETA_MAX_DEFAULT)

    try:
        pmax = float(panel.get("Pmax_stc") or 0)
        area = float(panel.get("area_m2") or 0)
        tau = float(panel.get("transparencia_pct") or 0) / 100.0
    except (TypeError, ValueError):
        pmax = area = 0.0
        tau = 0.0

    if pmax <= 0 or area <= 0:
        return {"estado": "sin_datos", "eta_modulo_pct": None,
                "eta_activa_pct": None, "eta_max_pct": eta_max,
                "sobreestimacion_pct": None,
                "mensaje": "Sin Pmax o área en la ficha — no se puede verificar τ."}
    if not (0.0 <= tau < 0.96):
        return {"estado": "sin_datos", "eta_modulo_pct": None,
                "eta_activa_pct": None, "eta_max_pct": eta_max,
                "sobreestimacion_pct": None,
                "mensaje": f"Transparencia fuera de rango ({tau*100:.0f}%)."}

    eta_mod = pmax / (area * 1000.0) * 100.0          # % sobre área bruta
    eta_act = eta_mod / (1.0 - tau)                    # % sobre área activa

    if eta_act > eta_max * _MARGEN:
        exceso = (eta_act / eta_max - 1.0) * 100.0
        return {
            "estado": "sospechoso_alto",
            "eta_modulo_pct": round(eta_mod, 2),
            "eta_activa_pct": round(eta_act, 2),
            "eta_max_pct": eta_max,
            "sobreestimacion_pct": round(exceso, 1),
            "mensaje": (
                f"La eficiencia implícita del área activa ({eta_act:.1f}%) supera el "
                f"máximo plausible para {tecno or 'esta tecnología'} ({eta_max:.1f}%). "
                f"Los parámetros eléctricos (Isc/Pmax) parecen de celda pura, SIN "
                f"descontar la transparencia τ={tau*100:.0f}% — la producción "
                f"quedaría sobreestimada (≈ +{exceso:.0f}% o más), o el área/τ de "
                f"la ficha son incorrectos."
            ),
        }

    if eta_act < _ETA_ACTIVA_MIN_PCT:
        return {
            "estado": "sospechoso_bajo",
            "eta_modulo_pct": round(eta_mod, 2),
            "eta_activa_pct": round(eta_act, 2),
            "eta_max_pct": eta_max,
            "sobreestimacion_pct": None,
            "mensaje": (
                f"La eficiencia implícita del área activa ({eta_act:.1f}%) es "
                f"anormalmente baja. Posible doble descuento de τ en los datos "
                f"del panel (producción subestimada) o Pmax/área incorrectos."
            ),
        }

    return {
        "estado": "ok",
        "eta_modulo_pct": round(eta_mod, 2),
        "eta_activa_pct": round(eta_act, 2),
        "eta_max_pct": eta_max,
        "sobreestimacion_pct": None,
        "mensaje": (
            f"Coherente: η módulo {eta_mod:.1f}% → η área activa {eta_act:.1f}% "
            f"(≤ {eta_max:.1f}% para {tecno or 'la tecnología'}). "
            f"El Isc/Pmax de la ficha ya incorporan τ={tau*100:.0f}%."
        ),
    }
