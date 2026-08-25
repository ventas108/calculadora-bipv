"""
Catálogo de tecnologías BIPV — SolTech Energy LaTam y otras.
Parámetros SDM extraídos del XLSM auditado (De Soto 2006).
"""

# ──────────────────────────────────────────────────────────────────────────────
# Constantes tecnológicas por familia (ObtenerConstantesTecnologia del VBA)
# Fuente: Mod_ModeloDiodo + Mermoud 2005 + De Soto 2006
# ──────────────────────────────────────────────────────────────────────────────
CONSTANTES_TECNOLOGIA = {
    "CdTe": {
        "Eg_ref":    1.50,     # eV — band gap CdTe a 300K (Luque & Hegedus 2011)
        "dEgdT":    -0.0002,   # eV/K — Mermoud 2005 Tabla 1
        "c_Rsh":     5.5,      # — exponente Rsh exponencial (Mermoud 2005)
        "n_mediana": 1.094,    # — factor idealidad mediana CdTe (CEC/NREL NCL)
    },
    "CIGS": {
        "Eg_ref":    1.15,
        "dEgdT":    -0.0002,
        "c_Rsh":     4.0,
        "n_mediana": 1.35,
    },
    "Mono-Si": {
        "Eg_ref":    1.121,
        "dEgdT":    -0.0002677,
        "c_Rsh":     5.5,
        "n_mediana": 1.05,
    },
    "Poli-Si": {
        "Eg_ref":    1.121,
        "dEgdT":    -0.0002677,
        "c_Rsh":     5.5,
        "n_mediana": 1.10,
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Panel principal del proyecto: ASP-ST1-T40 (SolTech Energy LaTam, CdTe)
# Ficha: Ficha_Tec_Vidrios_FV_SolTech_1200x600.pdf
# SDM: calibrado en hoja FF_vs_Irradiancia del XLSM (De Soto 2006)
# Validación: FF_max = 76.28% @ G=200 W/m² (Batzner et al. 2001 ✓)
# ──────────────────────────────────────────────────────────────────────────────
ASP_ST1_T40 = {
    "nombre":       "ASP-ST1-T40",
    "fabricante":   "SolTech Energy LaTam",
    "tecnologia":   "CdTe",
    "transparencia_pct": 40,
    "descripcion":  "Vidrio fotovoltaico CdTe semitransparente 40% — BIPV fachada",

    # ── Parámetros STC (1000 W/m², 25°C) ──────────────────────────────────
    "Voc_stc":  116.0,   # V
    "Vmp_stc":   86.4,   # V
    "Isc_stc":    0.80,  # A
    "Imp_stc":    0.70,  # A
    "Pmax_stc":  63.0,   # W
    "FF_stc":    63.0 / (116.0 * 0.80),  # 0.679

    # ── Coeficientes de temperatura ────────────────────────────────────────
    "Tk_beta":  -0.321,  # %/°C — Voc
    "Tk_alfa":  +0.060,  # %/°C — Isc
    "Tk_gamma": -0.214,  # %/°C — Pmax

    # ── Modelo De Soto 2006 — parámetros SDM calibrados (STC) ─────────────
    # Fuente: hoja FF_vs_Irradiancia del XLSM auditado
    "I_L_ref":   0.8152,     # A   — fotocorriente de referencia
    "I_o_ref":   1.35e-13,   # A   — corriente de saturación
    "R_s":      25.5090,     # Ω   — resistencia serie (módulo completo)
    "R_sh_ref": 1340.6,      # Ω   — Rsh en STC (referencia del modelo exponencial saturado)
    "R_sh_0":   18450.0,     # Ω   — Rsh al que satura la curva a muy baja irradiancia
                             #       (G→0). Calibrado por ajuste minimax contra los 10
                             #       puntos de la hoja FF_vs_Irradiancia del XLSM auditado
                             #       (25-ago-2026): error máximo residual ~4.9% (antes de
                             #       este parámetro, la fórmula sin saturar llegaba a 12.6%
                             #       de error y con la forma de curva invertida). Ver
                             #       calculos.modelo_iv.calcular_rsh_cdte() para el detalle.
    "a_ref":     154.0,      # n×Ns adimensional (Ns=141, n=1.094)

    # ── Temperatura nominal ────────────────────────────────────────────────
    "NOCT":     45.0,    # °C

    # ── Dimensiones ───────────────────────────────────────────────────────
    "largo_mm": 1200,
    "ancho_mm":  600,
    "area_m2":   0.72,
}


# ──────────────────────────────────────────────────────────────────────────────
# Familia completa ASP-ST1 (misma Voc/Vmp/Ns/a_ref -- Isc/Pmax varían con
# transparencia).
#
# Pmax_stc/Imp_stc (2026-08-21): antes None (fichas incompletas, excluidas por
# variable_panel() de todo barrido/comparador). Se completan con los valores
# REALES de datos/paneles_catalogo.xlsx (hoja Catalogo_Paneles_FV, filas
# SolTech ST1, Confianza=high) -- el T40 ahí coincide exactamente (63.0 W,
# 0.700 A) con el valor ya calibrado arriba, confirma que es la misma fuente.
# Ese Excel alimenta 📐 Dimensionamiento / 📋 Catálogo Paneles, pero NUNCA a
# 🧩 Comparador de Paneles (que solo lee este archivo) -- dos catálogos
# desconectados en el código; de ahí que estos datos reales llevaran tiempo
# sin usarse aquí.
#
# I_L_ref (fotocorriente SDM) SÍ se escala por variante -- proporcional al
# Isc_stc real de cada una, con el mismo ratio I_L_ref/Isc_stc que ya tiene
# T40 calibrado (0.8152/0.80 ≈ 1.019). Sin este escalado, las 6 variantes
# heredarían la fotocorriente calibrada para el Isc de T40 (0.80 A) --
# subestimando la energía real de T10 (Isc=1.19 A, 48% más corriente) y
# sobreestimando la de T70 (Isc=0.40 A, 50% menos) en la simulación física
# completa (run_bipv_simulation), aunque el Pmax_stc "de placa" se viera
# correcto en una tabla STC.
#
# I_o_ref/R_s/R_sh_ref/a_ref/NOCT NO se re-derivan por variante -- se
# conservan los del T40, calibrados por ajuste de curva contra la hoja
# FF_vs_Irradiancia del XLSM (validado contra Batzner et al. 2001). Es una
# aproximación razonada, no una calibración SDM independiente por variante:
# el Excel deriva su propio a_ref por fórmula (Ns=223, n=0.879 → NsA=196.1),
# marcado explícitamente "NOCT ESTIMADO... NO es dato de fabricante" -- se
# prefiere aquí el valor curve-fit y validado del T40 sobre esa estimación.
# ──────────────────────────────────────────────────────────────────────────────
_RATIO_IL_ISC_T40 = ASP_ST1_T40["I_L_ref"] / ASP_ST1_T40["Isc_stc"]   # ≈ 1.019


def _variante_asp_st1(transparencia_pct: int, isc_stc: float, pmax_stc: float, imp_stc: float) -> dict:
    return {
        **ASP_ST1_T40,
        "nombre": f"ASP-ST1-T{transparencia_pct}",
        "transparencia_pct": transparencia_pct,
        "Isc_stc": isc_stc,
        "Imp_stc": imp_stc,
        "Pmax_stc": pmax_stc,
        "FF_stc": pmax_stc / (ASP_ST1_T40["Voc_stc"] * isc_stc),
        "I_L_ref": round(isc_stc * _RATIO_IL_ISC_T40, 4),
    }


FAMILIA_ASP_ST1 = {
    "ASP-ST1-T10": _variante_asp_st1(10, 1.19, 94.0, 1.050),
    "ASP-ST1-T20": _variante_asp_st1(20, 1.07, 84.0, 0.940),
    "ASP-ST1-T30": _variante_asp_st1(30, 0.93, 73.0, 0.810),
    "ASP-ST1-T40": ASP_ST1_T40,
    "ASP-ST1-T50": _variante_asp_st1(50, 0.66, 52.0, 0.580),
    "ASP-ST1-T60": _variante_asp_st1(60, 0.53, 42.0, 0.470),
    "ASP-ST1-T70": _variante_asp_st1(70, 0.40, 31.0, 0.352),
}

# Catálogo unificado
MODULOS_BIPV = {**FAMILIA_ASP_ST1}


def obtener_panel(nombre: str) -> dict:
    if nombre not in MODULOS_BIPV:
        raise KeyError(f"Panel '{nombre}' no encontrado. Disponibles: {list(MODULOS_BIPV.keys())}")
    return MODULOS_BIPV[nombre]
