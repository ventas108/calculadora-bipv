"""
Módulo de pérdidas por mismatch y sombreado para sistemas BIPV.

Cubre:
  1. Sombreado de horizonte — obstáculos cercanos (edificios, árboles)
  2. Mismatch por orientación múltiple — fachadas distintas en el mismo string
  3. Pérdidas simples en cascada — fabricación, suciedad, cableado DC
  4. Cascada total de pérdidas → POA efectiva

Referencia mismatch orientación: PVsyst Technical Reference v7,
  "Electrical Mismatch Losses", σ²/(2μ²) — primera orden.
"""

import numpy as np
import pandas as pd
import pvlib

from calculos.solar import calcular_poa

# ── Calidad del módulo y mismatch (Spec 05/calidad-y-mismatch, 29-sep-2026) ──
# PVsyst separa «Module quality loss» (puede ser negativa: ganancia) y
# «Mismatch loss, modules and strings». La clave histórica `pct_mismatch_fab`
# queda para el mismatch; la calidad vive en CLAVE_CALIDAD_MODULO.
CLAVE_CALIDAD_MODULO = "pct_calidad_modulo"

# ── Horizonte hora a hora y cascada coherente (Spec 05/mismatch-horizonte-
# coherente, 29-sep-2026) ──────────────────────────────────────────────────
# Valores por defecto de los controles de 🔀 Mismatch, en un solo lugar.
# Producción NO los aplica si la página no se abrió (aplica 0 % y avisa).
DEFAULTS_MISMATCH = {
    "pct_calidad_modulo": 0.0,
    "pct_mismatch_fab": 1.0,
    "pct_soiling": 2.0,
    "pct_cableado": 1.5,
    "pct_cableado_ac": 0.0,
}
# Versión 2: el horizonte ya NO va dentro de factor_global_mismatch ni de
# factor_mismatch_sin_soiling; Producción lo aplica hora a hora. Un estado sin
# esta marca es de una versión anterior (su escalar sí trae el horizonte).
VERSION_MISMATCH = 2
CLAVE_VERSION_MISMATCH = "mismatch_version"


def pct_perdida_modulos(calidad, mismatch) -> float:
    """Pérdida combinada (%) de calidad y mismatch, aplicadas en cadena:
    (1 − (1 − c/100)(1 − m/100)) × 100. ``None`` cuenta como 0."""
    c = float(calidad or 0.0)
    m = float(mismatch or 0.0)
    return (1.0 - (1.0 - c / 100.0) * (1.0 - m / 100.0)) * 100.0


# ─── 1. Sombreado de horizonte ───────────────────────────────────────────────

def _interpolar_horizonte(puntos: list[tuple], az_query: np.ndarray) -> np.ndarray:
    """
    Interpola linealmente el perfil de horizonte definido por el usuario.

    puntos   : [(azimuth_deg, elevacion_deg), ...] — 0=Norte, 90=Este, 180=Sur, 270=Oeste
    az_query : array de azimuths a consultar (grados)
    Retorna  : array de elevaciones de horizonte para cada az_query
    """
    if not puntos:
        return np.zeros(len(az_query))

    pts  = sorted(puntos, key=lambda p: p[0])
    azs  = np.array([p[0] for p in pts], dtype=float)
    els  = np.array([p[1] for p in pts], dtype=float)

    # Extiende a -360 … +720 para interpolación circular
    az_ext = np.concatenate([azs - 360, azs, azs + 360])
    el_ext = np.tile(els, 3)

    return np.interp(az_query % 360, az_ext, el_ext)


def calcular_sombreado_horizonte(
    lat: float,
    lon: float,
    alt_m: float,
    tmy: pd.DataFrame,
    poa: pd.DataFrame,
    puntos_horizonte: list[tuple],
) -> dict:
    """
    Calcula pérdidas anuales de POA por sombreado de horizonte.

    Parámetros
    ----------
    lat, lon, alt_m   : coordenadas del sitio
    tmy               : DataFrame TMY (índice DatetimeIndex UTC)
    poa               : DataFrame POA con columna 'poa_global'
    puntos_horizonte  : [(azimuth_Norte_deg, elev_obs_deg), ...]
                        Cada punto define la elevación del obstáculo
                        visible desde el array en ese azimuth.

    Retorna dict
    ────────────
    factor_sombra_anual    : fracción de energía POA perdida (0–1)
    energia_perdida_kWh_m2 : kWh/m² perdidos al año
    horas_sombreadas       : nº horas afectadas
    mascara_sombra         : pd.Series bool (True = hora sombreada)
    solar_pos              : DataFrame posiciones solares (para diagrama)
    """
    loc       = pvlib.location.Location(latitude=lat, longitude=lon, altitude=alt_m, tz="UTC")
    solar_pos = loc.get_solarposition(poa.index)
    solo_directa = "poa_direct" in poa.columns
    firma = firma_horizonte(puntos_horizonte, poa)

    if not puntos_horizonte:
        return dict(
            factor_sombra_anual    = 0.0,
            energia_perdida_kWh_m2 = 0.0,
            horas_sombreadas       = 0,
            mascara_sombra         = pd.Series(False, index=poa.index),
            factor_horario         = pd.Series(1.0, index=poa.index),
            solo_directa           = solo_directa,
            firma                  = firma,
            solar_pos              = solar_pos,
        )

    horizon_elev = _interpolar_horizonte(puntos_horizonte, solar_pos["azimuth"].values)

    sol_visible = solar_pos["apparent_elevation"].values > 0.0
    sombreado   = sol_visible & (solar_pos["apparent_elevation"].values < horizon_elev)
    mask        = pd.Series(sombreado, index=poa.index)

    # Spec 05/mismatch-horizonte-coherente: el obstáculo tapa la luz DIRECTA
    # de la cara frontal; la difusa y el aporte trasero siguen llegando.
    # Antes se quitaba toda la POA de esas horas (15° de horizonte: 1.85 %
    # en vez de 0.93 %).
    f_h              = factor_horizonte_horario(mask, poa)
    poa_g            = poa["poa_global"].clip(lower=0).to_numpy(dtype=float)
    energia_total    = poa_g.sum() / 1000.0
    energia_perdida  = float((poa_g * (1.0 - f_h)).sum()) / 1000.0
    factor           = energia_perdida / energia_total if energia_total > 0 else 0.0

    return dict(
        factor_sombra_anual    = round(factor, 4),
        energia_perdida_kWh_m2 = round(energia_perdida, 1),
        horas_sombreadas       = int(mask.sum()),
        mascara_sombra         = mask,
        factor_horario         = pd.Series(f_h, index=poa.index),
        solo_directa           = solo_directa,
        firma                  = firma,
        solar_pos              = solar_pos,
    )


def factor_horizonte_horario(mascara: pd.Series, poa: pd.DataFrame) -> np.ndarray:
    """Fracción de la POA global que queda en cada hora tras el horizonte.

    En las horas bloqueadas se quita la luz directa de la cara frontal
    (``poa_direct``); si la POA no la trae (p. ej. la combinada de varias
    superficies) se quita toda la POA de esa hora, como antes. 1.0 en las
    horas sin sombra y en las horas sin luz.
    """
    g = poa["poa_global"].clip(lower=0).to_numpy(dtype=float)
    m = np.asarray(mascara, dtype=bool)
    if len(m) != len(g):
        raise ValueError(f"La máscara del horizonte tiene {len(m)} horas y la POA {len(g)}.")
    if "poa_direct" in poa.columns:
        tapada = np.minimum(poa["poa_direct"].clip(lower=0).to_numpy(dtype=float), g)
    else:
        tapada = g
    with np.errstate(invalid="ignore", divide="ignore"):
        f = np.where(m & (g > 0), 1.0 - tapada / np.maximum(g, 1e-12), 1.0)
    return np.clip(f, 0.0, 1.0)


def firma_horizonte(puntos_horizonte: list[tuple], poa: pd.DataFrame) -> str:
    """Huella de los datos del horizonte: puntos (sin importar el orden) y POA.

    Si cambia cualquiera de los dos, el resultado guardado deja de valer y
    🔀 Mismatch lo recalcula solo.
    """
    pts = sorted((round(float(a), 3), round(float(e), 3)) for a, e in (puntos_horizonte or []))
    g = poa["poa_global"].to_numpy(dtype=float)
    d = poa["poa_direct"].to_numpy(dtype=float) if "poa_direct" in poa.columns else np.zeros(1)
    return f"{pts}|{len(g)}|{g.sum():.3f}|{d.sum():.3f}"


def aplicar_factor_horario(poa: pd.DataFrame, factor) -> pd.DataFrame:
    """Copia de ``poa`` con ``poa_global × factor`` hora a hora.

    En bifacial la pérdida sale de la cara frontal: ``poa_front`` baja lo
    mismo que ``poa_global`` y el aporte trasero (global − front) no cambia.
    """
    salida = poa.copy()
    if factor is None:
        return salida
    f = np.asarray(factor, dtype=float)
    g = salida["poa_global"].to_numpy(dtype=float)
    nueva = g * f
    salida["poa_global"] = nueva
    if "poa_front" in salida.columns:
        salida["poa_front"] = np.clip(salida["poa_front"].to_numpy(dtype=float) - (g - nueva), 0.0, None)
    return salida


def publicar_cascada_mismatch(estado, *, poa_anual: float, pct_soiling: float, motor_ok: bool) -> list[dict]:
    """Arma la cascada visible de 🔀 Mismatch y publica lo que usa Producción.

    Visible: POA bruta → horizonte (solo luz directa) → mismatch de
    orientación → suciedad (0 y «la aplica 🔆 Motor Óptico» si está activo).
    Publicado para Producción (versión 2): ``factor_global_mismatch``
    (orientación + suciedad) y ``factor_mismatch_sin_soiling`` (orientación),
    los dos SIN horizonte, que Producción aplica hora a hora.
    """
    sombra = estado.get("res_sombra") or {}
    fs = float(sombra.get("factor_sombra_anual", 0.0) or 0.0) if estado.get("sombra_ok") else 0.0
    mm_or = float((estado.get("res_mismatch_or") or {}).get("factor_mismatch_pct", 0.0) or 0.0)
    soil = float(pct_soiling or 0.0)

    visible = cascada_perdidas(poa_anual, fs, mm_or, 0.0, 0.0 if motor_ok else soil, 0.0)
    nombres = {
        "Sombreado horizonte": "Sombreado horizonte (solo luz directa)",
        "Suciedad (Soiling)": ("Suciedad (la aplica 🔆 Motor Óptico)" if motor_ok else "Suciedad (Soiling)"),
    }
    visible = [dict(r, etapa=nombres.get(r["etapa"], r["etapa"])) for r in visible
               if r["etapa"] not in ("Mismatch fabricación", "Cableado DC")]

    estado["cascada_mismatch"] = visible
    estado["poa_efectiva_kWh_m2"] = round(visible[-1]["energia"], 1)
    estado["factor_global_mismatch"] = factor_global_perdidas(
        cascada_perdidas(poa_anual, 0.0, mm_or, 0.0, soil, 0.0))
    estado["factor_mismatch_sin_soiling"] = calcular_factor_mismatch_sin_soiling(0.0, mm_or)
    estado["factor_sombra_anual"] = fs
    estado["factor_mismatch_or_pct"] = mm_or
    estado["pct_soiling_cascada"] = soil
    estado[CLAVE_VERSION_MISMATCH] = VERSION_MISMATCH
    estado["cascada_ok"] = True
    estado["mismatch_ok"] = True
    return visible


def factores_mismatch_produccion(estado, poa: pd.DataFrame, motor_ok: bool) -> dict:
    """Lo que 📊 Producción aplica de 🔀 Mismatch.

    Retorna ``factor_escalar`` (sobre la irradiancia de todas las horas),
    ``factor_horario`` (np.ndarray o None: horizonte hora a hora y, en
    bifacial sin Motor Óptico, la corrección para que la suciedad no toque la
    cara trasera), ``legado`` y ``avisos`` (textos para el usuario).
    """
    avisos: list[str] = []
    if not estado.get("mismatch_ok"):
        return {"factor_escalar": 1.0, "factor_horario": None, "legado": False, "avisos": avisos}
    clave = "factor_mismatch_sin_soiling" if motor_ok else "factor_global_mismatch"
    escalar = float(estado.get(clave, 1.0) or 1.0)

    if estado.get(CLAVE_VERSION_MISMATCH) != VERSION_MISMATCH:
        if float(estado.get("factor_sombra_anual") or 0.0) > 0:
            avisos.append(
                "🔀 Mismatch se calculó con una versión anterior: el horizonte va como un factor "
                "anual sobre toda la irradiancia. Abre 🔀 Mismatch para recalcularlo hora a hora "
                "y solo sobre la luz directa."
            )
        return {"factor_escalar": escalar, "factor_horario": None, "legado": True, "avisos": avisos}

    g = poa["poa_global"].clip(lower=0).to_numpy(dtype=float)
    f = np.ones(len(g))
    sombra = estado.get("res_sombra") or {}
    mascara = sombra.get("mascara_sombra")
    if estado.get("sombra_ok") and isinstance(mascara, pd.Series) and mascara.any():
        alineada = mascara.reindex(poa.index) if len(mascara) == len(poa.index) else None
        if alineada is None or alineada.isna().any():
            avisos.append(
                "⚠️ El horizonte de 🔀 Mismatch se calculó con otras horas: no se aplicó. "
                "Abre 🔀 Mismatch para recalcularlo con la POA actual."
            )
        else:
            f = f * factor_horizonte_horario(alineada.astype(bool), poa)

    soil = float(estado.get("pct_soiling_cascada", 0.0) or 0.0) / 100.0
    if not motor_ok and soil > 0 and "poa_front" in poa.columns and soil < 1:
        # La suciedad actúa sobre la cara frontal que QUEDA después del
        # horizonte (front − luz directa tapada): así el resultado es
        # exactamente POA − horizonte − suciedad × frontal restante.
        g_h = g * f
        front = poa["poa_front"].clip(lower=0).to_numpy(dtype=float) - (g - g_h)
        with np.errstate(invalid="ignore", divide="ignore"):
            frac = np.where(g_h > 0, np.clip(front / np.maximum(g_h, 1e-12), 0.0, 1.0), 1.0)
        f = f * (1.0 - soil * frac) / (1.0 - soil)

    horario = None if np.allclose(f, 1.0, rtol=0, atol=1e-12) else f
    return {"factor_escalar": escalar, "factor_horario": horario, "legado": False, "avisos": avisos}


# ─── 2. Mismatch por orientación múltiple ───────────────────────────────────

def calcular_mismatch_orientacion(
    tmy: pd.DataFrame,
    lat: float,
    lon: float,
    alt_m: float,
    configuraciones: list[dict],
) -> dict:
    """
    Pérdidas de mismatch cuando módulos de distintas orientaciones están
    conectados en el mismo string (BIPV esquinas, fachadas múltiples).

    configuraciones : [
        {"azimuth": 0,  "tilt": 90, "fraccion": 0.60, "label": "Norte"},
        {"azimuth": 90, "tilt": 90, "fraccion": 0.40, "label": "Este"},
    ]

    Modelo (PVsyst aprox. 1er orden):
        LM = σ²_poa / (2 · μ²_poa)
    donde σ² es la varianza ponderada de POA anual entre orientaciones.

    Retorna dict con POA por orientación y factor de mismatch.
    """
    poa_res = []
    for cfg in configuraciones:
        poa      = calcular_poa(tmy, lat, lon, alt_m, cfg["tilt"], cfg["azimuth"])
        poa_anual = poa["poa_global"].sum() / 1000.0
        poa_res.append({
            "label":   cfg.get("label", f"Az{cfg['azimuth']}°/{cfg['tilt']}°"),
            "azimuth": cfg["azimuth"],
            "tilt":    cfg["tilt"],
            "fraccion": cfg["fraccion"],
            "poa_anual": round(poa_anual, 1),
        })

    fracs    = np.array([p["fraccion"]  for p in poa_res])
    poa_vals = np.array([p["poa_anual"] for p in poa_res])

    poa_medio = float(np.sum(fracs * poa_vals))

    if len(poa_res) < 2 or poa_medio == 0:
        return dict(
            poas                   = poa_res,
            factor_mismatch_pct    = 0.0,
            energia_ideal_kWh_m2   = round(poa_medio, 1),
            energia_perdida_kWh_m2 = 0.0,
        )

    variance        = float(np.sum(fracs * (poa_vals - poa_medio) ** 2))
    mismatch_pct    = (variance / (2 * poa_medio ** 2)) * 100
    energia_perdida = poa_medio * mismatch_pct / 100.0

    return dict(
        poas                   = poa_res,
        factor_mismatch_pct    = round(mismatch_pct, 2),
        energia_ideal_kWh_m2   = round(poa_medio, 1),
        energia_perdida_kWh_m2 = round(energia_perdida, 1),
    )


# ─── 3. Cascada de pérdidas ──────────────────────────────────────────────────

def cascada_perdidas(
    poa_bruta_kWh_m2:       float,
    factor_sombra:          float,   # fracción (0–1)
    factor_mismatch_orient: float,   # porcentaje (0–100)
    pct_mismatch_fab:       float,   # porcentaje (0–100)
    pct_soiling:            float,   # porcentaje (0–100)
    pct_cableado:           float,   # porcentaje (0–100)
) -> list[dict]:
    """
    Cascada de pérdidas POA → POA efectiva.
    Retorna lista de dicts lista para gráfico waterfall.

    Columnas: etapa, energia (kWh/m²), perdida (kWh/m²), pct_perdida
    """
    etapas = []

    def _paso(nombre, energia_in, factor_perdida_frac):
        perdida   = energia_in * factor_perdida_frac
        energia   = energia_in - perdida
        pct_total = perdida / poa_bruta_kWh_m2 * 100 if poa_bruta_kWh_m2 > 0 else 0
        etapas.append({
            "etapa":     nombre,
            "energia":   round(energia, 2),
            "perdida":   round(perdida, 2),
            "pct_total": round(pct_total, 2),
        })
        return energia

    etapas.append({
        "etapa":     "POA bruta",
        "energia":   round(poa_bruta_kWh_m2, 2),
        "perdida":   0.0,
        "pct_total": 0.0,
    })

    e = poa_bruta_kWh_m2
    e = _paso("Sombreado horizonte",    e, factor_sombra)
    e = _paso("Mismatch orientación",   e, factor_mismatch_orient / 100)
    e = _paso("Mismatch fabricación",   e, pct_mismatch_fab / 100)
    e = _paso("Suciedad (Soiling)",     e, pct_soiling / 100)
    e = _paso("Cableado DC",            e, pct_cableado / 100)

    etapas.append({
        "etapa":     "POA efectiva final",
        "energia":   round(e, 2),
        "perdida":   0.0,
        "pct_total": 0.0,
    })

    return etapas


def factor_global_perdidas(cascada: list[dict]) -> float:
    """Factor de rendimiento global = POA_efectiva / POA_bruta."""
    bruta   = next(r["energia"] for r in cascada if r["etapa"] == "POA bruta")
    efectiva = next(r["energia"] for r in cascada if r["etapa"] == "POA efectiva final")
    return round(efectiva / bruta, 4) if bruta > 0 else 0.0


def calcular_factor_mismatch_sin_soiling(
    factor_sombra_anual: float | None,
    factor_mismatch_or_pct: float | None,
) -> float:
    """
    Factor de pérdidas de Mismatch SIN soiling -- solo sombra de horizonte y
    mismatch de orientación (produccion-codespec Fase 1, "Soiling único").

    Motor Óptico ya incorpora IAM + soiling dentro de poa_sin_termico_df; si
    Producción, con Motor Óptico activo, multiplicara además por
    factor_global_mismatch (que sí incluye soiling -- ver cascada_perdidas()
    arriba), el soiling se aplicaría dos veces. Producción debe usar ESTE
    factor en ese caso; factor_global_mismatch se conserva para cuando Motor
    Óptico está inactivo (comportamiento histórico, sin cambios).

    Fórmula exacta: (1 - factor_sombra_anual) * (1 - factor_mismatch_or_pct / 100),
    limitada a [0, 1]. Una entrada ausente (None) equivale a pérdida cero
    para ese término -- factor_sombra_anual=None se trata como 0 (sin
    sombra) y factor_mismatch_or_pct=None como 0 (sin mismatch de
    orientación), nunca como "sin dato disponible, aplicar 100%".
    """
    fs = float(factor_sombra_anual) if factor_sombra_anual is not None else 0.0
    fm = float(factor_mismatch_or_pct) if factor_mismatch_or_pct is not None else 0.0
    factor = (1.0 - fs) * (1.0 - fm / 100.0)
    return round(min(1.0, max(0.0, factor)), 4)
