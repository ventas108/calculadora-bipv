# -*- coding: utf-8 -*-
"""
Degradación no lineal — curva real de garantía del fabricante (7-sep-2026).

Contexto: `calculos/financiero.py::calcular_flujo_caja()` aplicaba SOLO un
decaimiento geométrico con una tasa fija de %/año (`(1 - tasa/100)**(t-1)`).
Es el único punto real de cálculo en toda la app -- los otros ~25 archivos
que mencionan "degradación" solo reenvían ese mismo parámetro, no duplican
la fórmula.

En la realidad casi ninguna ficha de garantía es una tasa fija plana:
- La inmensa mayoría de fabricantes Tier 1 (JinkoSolar, JA Solar, Trina,
  Canadian, LONGi, etc.) publican una curva de DOS TRAMOS ("linear power
  warranty"): una caída inicial en el año 1 por LID (light-induced
  degradation, típico 1-3%), y luego una tasa lineal constante los años
  2-25 (típico 0,35-0,55%/año) hasta un piso garantizado en el año 25
  (típico 84-87,4%).
- Un puñado de fabricantes (algunos CdTe/First Solar, algunos premium)
  publican en cambio una tabla año-por-año completa, genuinamente no
  lineal -- PVsyst permite cargar esa curva directamente.

Este módulo agrega esos 2 modelos reales SIN romper el modelo geométrico
existente: `resolver_factor_degradacion()` con `config=None` (o
`config={"modo": "geometrica", ...}`) da EXACTAMENTE el mismo resultado
que la fórmula original -- retrocompatibilidad total, cero cambio para
cualquier proyecto ya calculado.

Nunca inventa: si el modo pedido no tiene datos suficientes (por ejemplo,
"curva_fabricante" sin que el panel tenga esos campos en el catálogo), cae
al modo geométrico con la tasa manual existente y lo señala explícitamente
en el resultado -- mismo principio de "nunca fallback silencioso sin
avisar" que ya usa `calculos/incertidumbre_p90.py::elegir_sigma_irr()`.
"""
from __future__ import annotations

MODOS_VALIDOS = ("geometrica", "curva_fabricante", "tabla_fabricante", "medida_campo")


def factor_geometrico(anio: int, tasa_pct: float) -> float:
    """Modelo ACTUAL (histórico): decaimiento geométrico con tasa fija.

    anio=1 -> factor=1.0 (sin degradación en el primer año de operación,
    igual que el comportamiento original de calcular_flujo_caja()).
    """
    return (1 - tasa_pct / 100.0) ** (anio - 1)


def factor_curva_fabricante(anio: int, caida_anio1_pct: float, tasa_lineal_pct_anio: float) -> float:
    """Modelo de garantía de 2 tramos (el caso real más común en fichas Tier 1).

    Año 1: caída inicial única por LID (light-induced degradation).
    Años 2+: tasa lineal constante aplicada sobre el nivel post-LID.

    anio=1 -> factor = 1 - caida_anio1_pct/100
    anio=N (N>=2) -> factor = (1 - caida_anio1_pct/100) - tasa_lineal_pct_anio/100 * (N-1)
    """
    nivel_post_lid = 1 - caida_anio1_pct / 100.0
    if anio <= 1:
        return nivel_post_lid
    return nivel_post_lid - (tasa_lineal_pct_anio / 100.0) * (anio - 1)


def factor_tabla_fabricante(anio: int, tabla_anio_pct: dict[int, float]) -> float:
    """Interpolación lineal entre los puntos de garantía publicados por el
    fabricante (para los pocos casos con tabla año-por-año completa, no un
    modelo de 2 tramos). `tabla_anio_pct` = {año: % de potencia garantizada
    en ese año, ej. {1: 98.0, 10: 91.0, 25: 84.8}}.

    Devuelve el punto exacto si `anio` está en la tabla. Fuera del rango
    de la tabla, se extrapola con el último tramo conocido (nunca inventa
    un modelo distinto al que el propio fabricante definió).
    """
    if not tabla_anio_pct:
        raise ValueError("tabla_anio_pct vacía -- no hay datos de garantía para interpolar")

    anios_ordenados = sorted(tabla_anio_pct.keys())

    if anio in tabla_anio_pct:
        return tabla_anio_pct[anio] / 100.0

    if anio <= anios_ordenados[0]:
        a0, a1 = anios_ordenados[0], anios_ordenados[min(1, len(anios_ordenados) - 1)]
    elif anio >= anios_ordenados[-1]:
        a0, a1 = anios_ordenados[max(-2, -len(anios_ordenados))], anios_ordenados[-1]
    else:
        a0 = max(a for a in anios_ordenados if a < anio)
        a1 = min(a for a in anios_ordenados if a > anio)

    if a0 == a1:
        return tabla_anio_pct[a0] / 100.0

    p0, p1 = tabla_anio_pct[a0], tabla_anio_pct[a1]
    frac = (anio - a0) / (a1 - a0)
    return (p0 + frac * (p1 - p0)) / 100.0


def resolver_factor_degradacion(anio: int, config: dict | None) -> dict:
    """Despachador único de los 4 modos de degradación.

    config = None -> comportamiento histórico exacto (requiere que el
    llamador incluya "tasa_pct" si quiere un modo distinto de 0%).
    config = {"modo": "geometrica", "tasa_pct": float}
    config = {"modo": "curva_fabricante", "caida_anio1_pct": float, "tasa_lineal_pct_anio": float}
    config = {"modo": "tabla_fabricante", "tabla_anio_pct": dict[int, float]}
    config = {"modo": "medida_campo", "tasa_pct": float}  -- reutiliza el
        modelo geométrico con la tasa medida en campo (session_state
        "tasa_degradacion_calculada" en 📊 Producción), no un modelo nuevo.

    Retorna {"factor": float, "modo_usado": str, "fallback": bool} --
    "fallback"=True cuando el modo pedido no tenía datos suficientes y se
    usó geométrica con tasa_pct (o 0.0 si tampoco había tasa) en su lugar,
    para que el llamador pueda avisar al usuario en vez de fallar en
    silencio.
    """
    if not config:
        return {"factor": 1.0, "modo_usado": "geometrica", "fallback": False}

    modo = config.get("modo", "geometrica")

    if modo == "geometrica" or modo == "medida_campo":
        tasa = config.get("tasa_pct", 0.0)
        return {"factor": factor_geometrico(anio, tasa), "modo_usado": modo, "fallback": False}

    if modo == "curva_fabricante":
        caida = config.get("caida_anio1_pct")
        tasa_lineal = config.get("tasa_lineal_pct_anio")
        if caida is None or tasa_lineal is None:
            tasa_fallback = config.get("tasa_pct", 0.0)
            return {
                "factor": factor_geometrico(anio, tasa_fallback),
                "modo_usado": "geometrica",
                "fallback": True,
            }
        return {
            "factor": factor_curva_fabricante(anio, caida, tasa_lineal),
            "modo_usado": "curva_fabricante",
            "fallback": False,
        }

    if modo == "tabla_fabricante":
        tabla = config.get("tabla_anio_pct")
        if not tabla:
            tasa_fallback = config.get("tasa_pct", 0.0)
            return {
                "factor": factor_geometrico(anio, tasa_fallback),
                "modo_usado": "geometrica",
                "fallback": True,
            }
        return {
            "factor": factor_tabla_fabricante(anio, tabla),
            "modo_usado": "tabla_fabricante",
            "fallback": False,
        }

    # Modo desconocido -- nunca inventa un comportamiento nuevo, cae a
    # geométrica con lo que haya disponible.
    tasa_fallback = config.get("tasa_pct", 0.0)
    return {
        "factor": factor_geometrico(anio, tasa_fallback),
        "modo_usado": "geometrica",
        "fallback": True,
    }
