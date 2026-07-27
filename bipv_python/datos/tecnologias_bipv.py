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
    "R_sh_ref": 1340.6,      # Ω   — Rsh base (para modelo exponencial CdTe)
    "a_ref":     154.0,      # n×Ns adimensional (Ns=141, n=1.094)

    # ── Temperatura nominal ────────────────────────────────────────────────
    "NOCT":     45.0,    # °C

    # ── Dimensiones ───────────────────────────────────────────────────────
    "largo_mm": 1200,
    "ancho_mm":  600,
    "area_m2":   0.72,
}


# ──────────────────────────────────────────────────────────────────────────────
# Familia completa ASP-ST1 (misma Voc/Vmp, Isc varía con transparencia)
# ──────────────────────────────────────────────────────────────────────────────
FAMILIA_ASP_ST1 = {
    "ASP-ST1-T10": {**ASP_ST1_T40, "nombre": "ASP-ST1-T10", "transparencia_pct": 10,
                    "Isc_stc": 1.19, "Imp_stc": None, "Pmax_stc": None},
    "ASP-ST1-T20": {**ASP_ST1_T40, "nombre": "ASP-ST1-T20", "transparencia_pct": 20,
                    "Isc_stc": 1.07, "Imp_stc": None, "Pmax_stc": None},
    "ASP-ST1-T30": {**ASP_ST1_T40, "nombre": "ASP-ST1-T30", "transparencia_pct": 30,
                    "Isc_stc": 0.93, "Imp_stc": None, "Pmax_stc": None},
    "ASP-ST1-T40": ASP_ST1_T40,
    "ASP-ST1-T50": {**ASP_ST1_T40, "nombre": "ASP-ST1-T50", "transparencia_pct": 50,
                    "Isc_stc": 0.66, "Imp_stc": None, "Pmax_stc": None},
    "ASP-ST1-T60": {**ASP_ST1_T40, "nombre": "ASP-ST1-T60", "transparencia_pct": 60,
                    "Isc_stc": 0.53, "Imp_stc": None, "Pmax_stc": None},
    "ASP-ST1-T70": {**ASP_ST1_T40, "nombre": "ASP-ST1-T70", "transparencia_pct": 70,
                    "Isc_stc": 0.40, "Imp_stc": None, "Pmax_stc": None},
}

# Catálogo unificado
MODULOS_BIPV = {**FAMILIA_ASP_ST1}


def obtener_panel(nombre: str) -> dict:
    if nombre not in MODULOS_BIPV:
        raise KeyError(f"Panel '{nombre}' no encontrado. Disponibles: {list(MODULOS_BIPV.keys())}")
    return MODULOS_BIPV[nombre]
