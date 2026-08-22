"""
Módulo financiero BIPV — Análisis Ley 1715 de 2014 (Colombia).

Beneficios fiscales modelados:
  Art. 11 — Deducción especial renta: 50% del CAPEX deducible de renta
  Art. 12 — Exclusión IVA: ahorro 19% sobre equipos calificados
  Art. 14 — Depreciación acelerada: hasta 5 años (20%/año vs 10 años estándar)

Métricas:
  TIR  — Tasa Interna de Retorno (IRR)
  VPN  — Valor Presente Neto (NPV)
  PRS  — Payback simple (años)
  PRD  — Payback descontado (años)
  LCOE — Levelized Cost of Energy (COP/kWh o USD/kWh)
"""

import numpy as np
from scipy.optimize import brentq


# ─── Piso de O&M por tamaño (#72) ────────────────────────────────────────────

def opex_minimo_anual_usd(kwp: float) -> float:
    """Costo mínimo realista de O&M anual (USD) según el tamaño del sistema.

    Misma política del Presupuesto paramétrico: un contrato de mantenimiento
    preventivo tiene un costo fijo mínimo (visitas + mano de obra) que la
    tarifa lineal USD/kWp subestima en proyectos medianos/grandes.
    Referencia: contrato básico BIPV/FV Colombia = USD 6.000–10.000/año.

    Returns:
        0.0 si kwp < 50; 5000.0 si 50 ≤ kwp < 300; 8000.0 si kwp ≥ 300.
    """
    if kwp >= 300:
        return 8_000.0
    if kwp >= 50:
        return 5_000.0
    return 0.0


# ─── Beneficios Ley 1715 ─────────────────────────────────────────────────────

def calcular_beneficios_ley_1715(
    capex_usd: float,
    fraccion_equipo: float = 0.65,   # fracción del CAPEX que corresponde a equipos (módulos + inversor)
    tasa_renta: float = 0.35,        # tasa impuesto renta corporativo Colombia 2024
    tipo_cambio: float = 4200.0,     # COP por USD
    tasa_descuento: float = 0.10,    # para VPN de depreciación acelerada
    vida_util_anos: int = 25,
) -> dict:
    """
    Cuantifica los beneficios fiscales de la Ley 1715/2014 (Colombia).

    Art. 11 — Deducción renta
        50% del valor de la inversión deducible de la base gravable de renta.
        Ahorro fiscal = 0.50 × CAPEX × tasa_renta
        Generalmente aplicable en el año 1 (o repartido en ≤5 años).

    Art. 12 — Exclusión IVA
        Los equipos para SRFNC están excluidos de IVA (Ley 1715/Art.12).
        Ahorro = IVA que NO se paga = 0.19 × CAPEX_equipos
        Supuesto: el CAPEX ingresado en la app es el precio SIN IVA (precio base del proyecto).
        Si el CAPEX ingresado YA incluye IVA, usar 0.19/1.19 en su lugar.

    Art. 14 — Depreciación acelerada
        5 años (20%/año) vs depreciación estándar 10 años (10%/año).
        Ahorro VPN = VPN(ahorro_deducción_adicional_años_1-5)
    """
    capex_cop = capex_usd * tipo_cambio

    # ── Art. 11 — Deducción renta ─────────────────────────────────────────────
    deduccion_base   = 0.50 * capex_cop         # 50% del CAPEX
    ahorro_renta_cop = deduccion_base * tasa_renta
    ahorro_renta_usd = ahorro_renta_cop / tipo_cambio

    # ── Art. 12 — IVA ────────────────────────────────────────────────────────
    capex_equipos_cop = fraccion_equipo * capex_cop
    ahorro_iva_cop    = capex_equipos_cop * 0.19   # 19% que NO se paga
    ahorro_iva_usd    = ahorro_iva_cop / tipo_cambio

    # ── Art. 14 — Depreciación acelerada ─────────────────────────────────────
    # Depreciación normal: 10%/año × CAPEX durante 10 años
    # Depreciación acelerada: 20%/año × CAPEX durante 5 años
    # Beneficio fiscal anual adicional = tasa_renta × (dep_acelerada - dep_normal)
    dep_normal_anual    = capex_cop / 10.0
    dep_acelerada_anual = capex_cop / 5.0
    dep_extra_anual     = dep_acelerada_anual - dep_normal_anual   # sólo años 1-5

    factores_vpn = np.array([(1 + tasa_descuento) ** (-t) for t in range(1, 6)])
    # En años 6-10: dep_normal sigue, dep_acelerada = 0 → diferencia negativa
    factores_vpn_neg = np.array([(1 + tasa_descuento) ** (-t) for t in range(6, 11)])

    ahorro_vpn_dep_cop = (tasa_renta * dep_extra_anual * factores_vpn.sum()
                          - tasa_renta * dep_normal_anual * factores_vpn_neg.sum())
    ahorro_vpn_dep_usd = ahorro_vpn_dep_cop / tipo_cambio

    # ── Total ─────────────────────────────────────────────────────────────────
    total_usd = ahorro_renta_usd + ahorro_iva_usd + max(ahorro_vpn_dep_usd, 0)
    total_cop = total_usd * tipo_cambio

    return {
        "ahorro_renta_usd":   round(ahorro_renta_usd, 0),
        "ahorro_iva_usd":     round(ahorro_iva_usd, 0),
        "ahorro_dep_vpn_usd": round(max(ahorro_vpn_dep_usd, 0), 0),
        "total_usd":          round(total_usd, 0),
        "total_cop":          round(total_cop, 0),
        "capex_neto_usd":     round(capex_usd - total_usd, 0),
        "pct_capex":          round(total_usd / capex_usd * 100, 1) if capex_usd > 0 else 0,
    }


# ─── Flujo de caja ───────────────────────────────────────────────────────────

def calcular_flujo_caja(
    capex_usd: float,
    beneficios_1715_usd: float,
    e_ac_kWh_anual: float,
    tarifa_cop_kWh: float,
    tipo_cambio: float,
    tasa_escalacion_tarifa: float,   # % anual de aumento de la tarifa
    tasa_degradacion_pct: float,     # % anual de degradación del panel
    opex_pct_capex: float,           # % del CAPEX como O&M anual (año 1)
    n_anos: int = 25,
    beneficio_renta_ano: int = 1,    # año en que se aplica el beneficio art. 11
    tasa_escalacion_opex: float = 0.0,  # % anual de aumento del O&M (#177)
    frac_exportada: float = 0.0,
    tarifa_excedentes_cop_kWh: float | None = None,
) -> list[dict]:
    """
    Genera el flujo de caja anual del proyecto (USD).

    Año 0: -CAPEX + ahorro IVA + ahorro depreciación (si se negocia al inicio)
    Año 1: -CAPEX_NETO + ahorro_renta (Art. 11) + ingresos energía - OPEX
    Años 2-N: ingresos energía - OPEX

    frac_exportada : fracción (0.0-1.0) de la energía anual que se exporta/vende
        como excedente a la red (Res. CREG 174 de 2021) en vez de autoconsumirse.
        Se calcula típicamente en 🔋 Baterías y Balance como
        E_exportacion_anual_kWh / (E_autoconsumo_anual_kWh + E_exportacion_anual_kWh).
        0.0 (default) reproduce el comportamiento anterior: toda la energía se
        valora a tarifa_cop_kWh, sin distinguir autoconsumo de excedente.
    tarifa_excedentes_cop_kWh : tarifa de venta/remuneración de excedentes
        (típicamente menor que la tarifa de compra bajo Ley 1715/CREG 174).
        None (default) usa la misma tarifa_cop_kWh -- resultado idéntico al
        comportamiento anterior si frac_exportada también es 0.0.

    Retorna lista de dicts con: año, ingreso_kWh, ingreso_usd, opex_usd, flujo_usd,
    flujo_acum_usd, factor_descuento, flujo_desc_usd, flujo_desc_acum_usd
    """
    opex_anual_usd = capex_usd * opex_pct_capex / 100.0
    capex_neto_usd = capex_usd - beneficios_1715_usd   # CAPEX después de todos los beneficios
    frac_exportada = min(max(frac_exportada, 0.0), 1.0)
    tarifa_exced_base = (
        tarifa_excedentes_cop_kWh if tarifa_excedentes_cop_kWh is not None else tarifa_cop_kWh
    )

    flujos = []

    # ── Año 0 ─────────────────────────────────────────────────────────────────
    flujos.append({
        "año":               0,
        "produccion_kWh":    0.0,
        "autoconsumo_kWh":   0.0,
        "exportacion_kWh":   0.0,
        "ingreso_energia_usd": 0.0,
        "opex_usd":          0.0,
        "flujo_usd":         -capex_neto_usd,
        "flujo_acum_usd":    -capex_neto_usd,
    })

    flujo_acum = -capex_neto_usd

    for t in range(1, n_anos + 1):
        # Degradación acumulada
        factor_deg   = (1 - tasa_degradacion_pct / 100) ** (t - 1)
        prod_kWh     = e_ac_kWh_anual * factor_deg
        exportada_kWh    = prod_kWh * frac_exportada
        autoconsumo_kWh  = prod_kWh - exportada_kWh

        # Tarifas escaladas -- se asume la misma escalación para ambas (no hay
        # fuente separada de proyección de precio de excedentes en Colombia).
        tarifa_t_cop        = tarifa_cop_kWh   * (1 + tasa_escalacion_tarifa / 100) ** (t - 1)
        tarifa_exced_t_cop  = tarifa_exced_base * (1 + tasa_escalacion_tarifa / 100) ** (t - 1)
        ingreso_cop  = autoconsumo_kWh * tarifa_t_cop + exportada_kWh * tarifa_exced_t_cop
        ingreso_usd  = ingreso_cop / tipo_cambio

        # O&M escalado (#177): el mantenimiento sube con la inflación en USD.
        # Con tasa_escalacion_opex=0 se reproduce el comportamiento anterior
        # (O&M constante), que subestimaba costos tardíos e inflaba la TIR.
        opex_t_usd = opex_anual_usd * (1 + tasa_escalacion_opex / 100) ** (t - 1)
        flujo = ingreso_usd - opex_t_usd
        flujo_acum += flujo

        flujos.append({
            "año":               t,
            "produccion_kWh":    round(prod_kWh, 0),
            "autoconsumo_kWh":   round(autoconsumo_kWh, 0),
            "exportacion_kWh":   round(exportada_kWh, 0),
            "ingreso_energia_usd": round(ingreso_usd, 0),
            "opex_usd":          round(opex_t_usd, 0),
            "flujo_usd":         round(flujo, 0),
            "flujo_acum_usd":    round(flujo_acum, 0),
        })

    return flujos


# ─── Métricas financieras ────────────────────────────────────────────────────

def _npv(tasa: float, flujos: list[float]) -> float:
    """VPN de una lista de flujos empezando en t=0."""
    return sum(f / (1 + tasa) ** t for t, f in enumerate(flujos))


def calcular_metricas(
    flujos: list[dict],
    tasa_descuento: float,
    capex_usd: float,
    e_ac_kWh_anual: float,
    tipo_cambio: float,
) -> dict:
    """
    Calcula TIR, VPN, Payback simple, Payback descontado y LCOE.
    """
    vals = [f["flujo_usd"] for f in flujos]

    # ── VPN ───────────────────────────────────────────────────────────────────
    vpn_usd = _npv(tasa_descuento, vals)
    vpn_cop = vpn_usd * tipo_cambio

    # ── TIR ───────────────────────────────────────────────────────────────────
    tir = None
    try:
        # Buscar TIR en rango -99% a 200%
        f_neg = _npv(-0.99, vals)
        f_pos = _npv(2.00,  vals)
        if f_neg * f_pos < 0:
            tir = brentq(_npv, -0.99, 2.00, args=(vals,), xtol=1e-8)
    except Exception:
        tir = None

    # ── Payback simple ────────────────────────────────────────────────────────
    payback_simple = None
    for f in flujos:
        if f["flujo_acum_usd"] >= 0:
            # Interpolación lineal entre año anterior y actual
            idx = flujos.index(f)
            if idx > 0:
                acum_prev = flujos[idx - 1]["flujo_acum_usd"]
                acum_curr = f["flujo_acum_usd"]
                payback_simple = idx - 1 + abs(acum_prev) / (acum_curr - acum_prev)
            break

    # ── Payback descontado ────────────────────────────────────────────────────
    flujo_desc_acum = 0
    payback_desc = None
    flujo_desc_acum_prev = 0
    for f in flujos:
        t   = f["año"]
        fdc = f["flujo_usd"] / (1 + tasa_descuento) ** t
        flujo_desc_acum_prev = flujo_desc_acum
        flujo_desc_acum      += fdc
        if flujo_desc_acum >= 0 and payback_desc is None and t > 0:
            payback_desc = t - 1 + abs(flujo_desc_acum_prev) / abs(fdc)

    # ── LCOE (USD/kWh) ────────────────────────────────────────────────────────
    # LCOE = VPN_costos / VPN_produccion
    n_anos      = max(f["año"] for f in flujos)
    vpn_costos  = capex_usd + sum(
        f["opex_usd"] / (1 + tasa_descuento) ** f["año"]
        for f in flujos if f["año"] > 0
    )
    vpn_prod_kWh = sum(
        f["produccion_kWh"] / (1 + tasa_descuento) ** f["año"]
        for f in flujos if f["año"] > 0
    )
    lcoe_usd_kWh = vpn_costos / vpn_prod_kWh if vpn_prod_kWh > 0 else 0
    lcoe_cop_kWh = lcoe_usd_kWh * tipo_cambio

    return {
        "vpn_usd":          round(vpn_usd, 0),
        "vpn_cop_millon":   round(vpn_cop / 1e6, 2),
        "tir_pct":          round(tir * 100, 2) if tir is not None else None,
        "payback_simple":   round(payback_simple, 1) if payback_simple else None,
        "payback_desc":     round(payback_desc, 1) if payback_desc else None,
        "lcoe_usd_kWh":     round(lcoe_usd_kWh, 4),
        "lcoe_cop_kWh":     round(lcoe_cop_kWh, 1),
        "vpn_positivo":     vpn_usd > 0,
    }


# ─── Comparativo sin / con Ley 1715 ─────────────────────────────────────────

def comparativo_ley_1715(
    capex_usd: float,
    e_ac_kWh_anual: float,
    tarifa_cop_kWh: float,
    tipo_cambio: float,
    tasa_descuento: float,
    tasa_escalacion: float,
    tasa_degradacion: float,
    opex_pct: float,
    n_anos: int,
    beneficios_1715: dict,
    tasa_escalacion_opex: float = 0.0,  # % anual de aumento del O&M (#177)
    frac_exportada: float = 0.0,
    tarifa_excedentes_cop_kWh: float | None = None,
) -> dict:
    """
    Calcula métricas SIN y CON beneficios Ley 1715 para comparación.

    frac_exportada / tarifa_excedentes_cop_kWh: ver calcular_flujo_caja().
    Se aplican igual en ambos escenarios (sin/con Ley 1715) -- solo afectan
    el CAPEX neto, no la valoración de la energía.
    """
    # Sin Ley 1715 — CAPEX completo
    flujos_sin = calcular_flujo_caja(
        capex_usd          = capex_usd,
        beneficios_1715_usd= 0.0,
        e_ac_kWh_anual     = e_ac_kWh_anual,
        tarifa_cop_kWh     = tarifa_cop_kWh,
        tipo_cambio        = tipo_cambio,
        tasa_escalacion_tarifa = tasa_escalacion,
        tasa_degradacion_pct   = tasa_degradacion,
        opex_pct_capex     = opex_pct,
        n_anos             = n_anos,
        tasa_escalacion_opex = tasa_escalacion_opex,
        frac_exportada     = frac_exportada,
        tarifa_excedentes_cop_kWh = tarifa_excedentes_cop_kWh,
    )
    met_sin = calcular_metricas(flujos_sin, tasa_descuento, capex_usd,
                                e_ac_kWh_anual, tipo_cambio)

    # Con Ley 1715 — CAPEX neto
    flujos_con = calcular_flujo_caja(
        capex_usd          = capex_usd,
        beneficios_1715_usd= beneficios_1715["total_usd"],
        e_ac_kWh_anual     = e_ac_kWh_anual,
        tarifa_cop_kWh     = tarifa_cop_kWh,
        tipo_cambio        = tipo_cambio,
        tasa_escalacion_tarifa = tasa_escalacion,
        tasa_degradacion_pct   = tasa_degradacion,
        opex_pct_capex     = opex_pct,
        n_anos             = n_anos,
        tasa_escalacion_opex = tasa_escalacion_opex,
        frac_exportada     = frac_exportada,
        tarifa_excedentes_cop_kWh = tarifa_excedentes_cop_kWh,
    )
    met_con = calcular_metricas(flujos_con, tasa_descuento, capex_usd,
                                e_ac_kWh_anual, tipo_cambio)

    return {
        "sin": {"flujos": flujos_sin, "metricas": met_sin},
        "con": {"flujos": flujos_con, "metricas": met_con},
    }
