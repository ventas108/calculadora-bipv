"""
Motor Óptico BIPV — Cascada de Correcciones Reales
===================================================
Implementa: IAM ASHRAE · Soiling estacional Colombia · Modelo térmico confinado

Portado y adaptado desde: client/src/lib/iamSoilingEngine.ts
Referencia científica:
  - IAM: ASHRAE 93-1986 / IEC 61853
  - Soiling: factores calibrados para Colombia (épocas seca/lluvia)
  - Térmico BIPV: NOCT + factor de confinamiento k_BIPV (IEA-PVPS T15)
"""
import numpy as np
import pandas as pd


# ─── Constantes y tablas de referencia ────────────────────────────────────────

# Soiling mensual Colombia — pérdida fraccional por mes (0‑1)
# Época seca Ene-Feb y Jun-Ago → mayor acumulación de polvo
# Temporada lluvia Abr-May y Sep-Nov → autolavado natural
SOILING_COLOMBIA: dict[int, float] = {
    1: 0.050,   # Enero    — seca, acumulación alta
    2: 0.060,   # Febrero  — pico de suciedad
    3: 0.040,   # Marzo    — inicio primera temporada lluvia
    4: 0.020,   # Abril    — primera temporada lluvia
    5: 0.020,   # Mayo     — primera temporada lluvia
    6: 0.040,   # Junio    — veranillo inter-andino
    7: 0.050,   # Julio    — mayor suciedad segundo semestre
    8: 0.060,   # Agosto   — pico suciedad
    9: 0.040,   # Septiembre — inicio segunda temporada lluvia
    10: 0.020,  # Octubre  — temporada lluvia
    11: 0.010,  # Noviembre — máxima precipitación, mínima suciedad
    12: 0.040,  # Diciembre — inicio época seca navideña
}

# Umbral viento como proxy de lluvia para activar autolavado (m/s)
AUTOLAVADO_UMBRAL_WS = 4.5
AUTOLAVADO_FACTOR    = 0.15   # soiling_real = soiling_base × 0.15 cuando hay "lluvia"

# b0 ASHRAE por tipo de vidrio fotovoltaico
B0_POR_VIDRIO = {
    "Vidrio estándar templado (b₀=0.05)":      0.05,
    "Vidrio BIPV semi-transparente (b₀=0.10)": 0.10,
    "Vidrio CdTe laminado (b₀=0.12)":          0.12,
    "Personalizado":                            None,
}

# Factor de confinamiento k_BIPV por tipo de montaje
K_BIPV_POR_MONTAJE = {
    "Ventilado libre (k=1.0) — espacio > 10 cm": 1.0,
    "Fachada confinada (k=1.3) — montaje típico": 1.3,
    "Sin ventilación (k=1.5) — sellado total":    1.5,
}


# ─── Funciones de cálculo (puras, vectorizadas) ────────────────────────────────

def iam_ashrae(aoi_deg: np.ndarray, b0: float) -> np.ndarray:
    """
    Factor IAM (Incidence Angle Modifier) según ASHRAE.

    f_IAM = max(0, 1 − b0 × (1/cos(AOI) − 1))

    Solo se aplica a la componente directa (DNI×cos(AOI)).
    La componente difusa no se modifica (ya es isotrópica/omnidireccional).

    Parameters
    ----------
    aoi_deg : array de ángulos de incidencia en grados
    b0      : coeficiente de reflexión ASHRAE del vidrio (típico 0.05-0.12)

    Returns
    -------
    array f_IAM en [0, 1]
    """
    aoi = np.asarray(aoi_deg, dtype=float)
    cos_aoi = np.cos(np.radians(aoi))
    # Reflexión total para AOI >= 85° o sol detrás del plano
    mask_total = (aoi >= 85.0) | (cos_aoi <= 1e-6)
    cos_safe = np.where(mask_total, 1.0, cos_aoi)
    f = 1.0 - b0 * (1.0 / cos_safe - 1.0)
    f = np.where(mask_total, 0.0, f)
    return np.clip(f, 0.0, 1.0)


def soiling_series(index: pd.DatetimeIndex,
                   tmy_df: pd.DataFrame | None = None,
                   factores: dict | None = None) -> np.ndarray:
    """
    Factor de pérdida por soiling horario (fracción 0-1 a descontar de POA).

    Aplica autolavado si velocidad de viento > umbral como proxy de lluvia.

    Parameters
    ----------
    index   : DatetimeIndex del TMY (8760 h)
    tmy_df  : DataFrame TMY con columna WS10m (m/s) — opcional
    factores: dict mes→fracción; si None usa SOILING_COLOMBIA

    Returns
    -------
    array de pérdida fraccional por soiling [0, 1]
    """
    cfg = factores if factores is not None else SOILING_COLOMBIA
    soil = np.array([cfg.get(m, 0.04) for m in index.month], dtype=float)

    if tmy_df is not None and "WS10m" in tmy_df.columns:
        ws = tmy_df["WS10m"].values
        autolavado = ws > AUTOLAVADO_UMBRAL_WS
        soil = np.where(autolavado, soil * AUTOLAVADO_FACTOR, soil)

    return soil


def factor_termico_bipv(G_poa_optica: np.ndarray,
                        T_amb: np.ndarray,
                        noct: float = 45.0,
                        coef_temp: float = -0.0045,
                        k_bipv: float = 1.3) -> np.ndarray:
    """
    Factor multiplicativo de eficiencia por temperatura para fachada BIPV confinada.

    T_cell   = T_amb + G_poa_optica × (NOCT − 20) / 800 × k_bipv
    F_térm   = 1 + coef_temp × (T_cell − 25)

    Parameters
    ----------
    G_poa_optica : irradiancia POA óptica (W/m²) — después de IAM y soiling
    T_amb        : temperatura ambiente (°C) del TMY
    noct         : temperatura nominal de operación (°C); típico 45 estándar, 50 BIPV
    coef_temp    : coeficiente de temperatura en decimal/°C (ej. -0.0045 = -0.45%/°C)
    k_bipv       : factor de confinamiento (1.0 ventilado, 1.3 confinado, 1.5 sellado)

    Returns
    -------
    array F_térm — típicamente 0.85-1.0 para clima tropical
    """
    T_cell = T_amb + G_poa_optica * ((noct - 20.0) / 800.0) * k_bipv
    F = 1.0 + coef_temp * (T_cell - 25.0)
    return np.clip(F, 0.4, 1.1)  # límites físicos razonables


def cascada_optica(
    tmy_df: pd.DataFrame,
    poa_df: pd.DataFrame,
    b0: float = 0.05,
    noct: float = 45.0,
    coef_temp: float = -0.0045,
    k_bipv: float = 1.3,
    soiling_config: dict | None = None,
) -> tuple[pd.DataFrame, dict]:
    """
    Aplica la cascada completa IAM → Soiling → Térmico al TMY de 8760 h.

    La corrección por transparencia (η_adj = η_base × (1-τ)) NO se aplica
    aquí porque pertenece al modelo eléctrico (Dimensionamiento); la τ solo
    afecta la eficiencia STC, no la irradiancia.

    Parameters
    ----------
    tmy_df  : DataFrame 8760h con columnas G_h, Gb_n, Gd_h, T2m, WS10m
    poa_df  : DataFrame 8760h de calcular_poa() — columnas poa_global, poa_direct, …
    b0      : coeficiente ASHRAE del vidrio
    noct    : temperatura nominal de operación (°C)
    coef_temp: coeficiente térmico en decimal/°C (ej. -0.0045)
    k_bipv  : factor de confinamiento térmico
    soiling_config: dict mes→fracción opcional; si None usa SOILING_COLOMBIA

    Returns
    -------
    result_df : DataFrame 8760h con columnas de cada etapa de la cascada
    summary   : dict con resumen anual/mensual y factores promedio
    """
    idx = tmy_df.index

    # ── Componentes POA ───────────────────────────────────────────────────────
    poa_bruta   = poa_df["poa_global"].values.copy()

    # poa_direct = componente directa (DNI×cos AOI) ya calculada por pvlib
    if "poa_direct" in poa_df.columns:
        poa_dir = poa_df["poa_direct"].values.copy()
    else:
        # Fallback: estima directa como fracción de la global
        poa_dir = poa_bruta * np.where(tmy_df["Gb_n"].values > 1, 0.75, 0.0)

    # poa_difusa = sky + ground (no afectada por IAM)
    if "poa_sky_diffuse" in poa_df.columns:
        poa_dif = (poa_df["poa_sky_diffuse"].fillna(0).values
                   + poa_df.get("poa_ground_diffuse", pd.Series(0, index=idx)).fillna(0).values)
    elif "poa_diffuse" in poa_df.columns:
        poa_dif = poa_df["poa_diffuse"].fillna(0).values
    else:
        poa_dif = poa_bruta - poa_dir

    # ── AOI desde DNI y poa_direct ────────────────────────────────────────────
    # cos(AOI) = poa_direct / DNI  (relación exacta por definición)
    dni = tmy_df["Gb_n"].values
    with np.errstate(invalid="ignore", divide="ignore"):
        cos_aoi = np.where(dni > 2.0, poa_dir / np.maximum(dni, 1.0), 0.0)
    cos_aoi = np.clip(cos_aoi, 0.0, 1.0)
    aoi_deg = np.degrees(np.arccos(cos_aoi))
    aoi_deg = np.where(dni <= 2.0, 90.0, aoi_deg)   # noche/nuboso → reflexión total

    # ── 1. IAM ASHRAE ─────────────────────────────────────────────────────────
    f_iam        = iam_ashrae(aoi_deg, b0)
    poa_dir_neta = poa_dir * f_iam
    poa_optica   = poa_dir_neta + poa_dif            # POA después de reflexión geométrica
    perd_iam     = poa_dir - poa_dir_neta             # pérdida por reflexión (W/m²)

    # ── 2. Soiling estacional Colombia ────────────────────────────────────────
    f_soil       = soiling_series(idx, tmy_df, soiling_config)
    poa_post_soil = poa_optica * (1.0 - f_soil)
    perd_soil    = poa_optica * f_soil

    # ── 3. Modelo térmico BIPV confinado ──────────────────────────────────────
    T_amb = (tmy_df["T2m"].values
             if "T2m" in tmy_df.columns
             else np.full(len(idx), 22.0))
    f_term = factor_termico_bipv(poa_optica, T_amb, noct, coef_temp, k_bipv)

    # La corrección térmica actúa como factor sobre la eficiencia de conversión,
    # lo que equivale a escalar la POA efectiva (energia aprovechable).
    poa_efectiva = np.maximum(poa_post_soil * f_term, 0.0)
    perd_term    = np.maximum(poa_post_soil - poa_post_soil * f_term, 0.0)

    # ── DataFrame resultado horario ───────────────────────────────────────────
    result_df = pd.DataFrame({
        "poa_bruta":      poa_bruta,
        "poa_optica":     poa_optica,
        "poa_post_soil":  poa_post_soil,
        "poa_efectiva":   poa_efectiva,   # ← usar como poa_global en downstream
        "f_iam":          f_iam,
        "aoi_deg":        aoi_deg,
        "f_soil":         f_soil,
        "f_term":         f_term,
        "perdida_iam":    np.maximum(perd_iam, 0.0),
        "perdida_soil":   np.maximum(perd_soil, 0.0),
        "perdida_term":   perd_term,
    }, index=idx)

    # ── Resumen anual ─────────────────────────────────────────────────────────
    escala = 1 / 1000.0  # W/m² × h → kWh/m²
    bruta_a   = float(result_df["poa_bruta"].sum()     * escala)
    optica_a  = float(result_df["poa_optica"].sum()    * escala)
    post_s_a  = float(result_df["poa_post_soil"].sum() * escala)
    efectiva_a = float(result_df["poa_efectiva"].sum() * escala)
    p_iam_a   = float(result_df["perdida_iam"].sum()   * escala)
    p_soil_a  = float(result_df["perdida_soil"].sum()  * escala)
    p_term_a  = float(result_df["perdida_term"].sum()  * escala)

    # Factores medios (solo horas con sol)
    mask_sol = poa_bruta > 10
    f_iam_mean  = float(f_iam[mask_sol].mean())   if mask_sol.any() else 0.0
    f_soil_mean = float(f_soil.mean())
    f_term_mean = float(f_term[mask_sol].mean())  if mask_sol.any() else 1.0

    # Factor global de degradación
    factor_global = efectiva_a / bruta_a if bruta_a > 0 else 0.0

    # Resumen mensual (kWh/m²/mes)
    meses_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    monthly_raw = result_df[["poa_bruta", "poa_efectiva",
                              "perdida_iam", "perdida_soil", "perdida_term"]
                            ].resample("ME").sum() * escala
    monthly_raw.index = meses_es

    summary: dict = {
        # Energías anuales
        "poa_bruta_anual_kWh_m2":     round(bruta_a, 1),
        "poa_optica_anual_kWh_m2":    round(optica_a, 1),
        "poa_post_soil_anual_kWh_m2": round(post_s_a, 1),
        "poa_efectiva_anual_kWh_m2":  round(efectiva_a, 1),
        # Pérdidas anuales
        "perdida_iam_kWh_m2":         round(p_iam_a, 1),
        "perdida_soil_kWh_m2":        round(p_soil_a, 1),
        "perdida_term_kWh_m2":        round(p_term_a, 1),
        "perdida_total_kWh_m2":       round(p_iam_a + p_soil_a + p_term_a, 1),
        # Factores promedio (horas con sol)
        "f_iam_prom":                 round(f_iam_mean, 4),
        "f_soil_prom":                round(1.0 - f_soil_mean, 4),
        "f_term_prom":                round(f_term_mean, 4),
        "factor_global":              round(factor_global, 4),
        # Parámetros usados
        "b0":       b0,
        "noct":     noct,
        "coef_temp": coef_temp,
        "k_bipv":   k_bipv,
        # Tablas mensuales
        "monthly":  monthly_raw,
    }

    return result_df, summary
