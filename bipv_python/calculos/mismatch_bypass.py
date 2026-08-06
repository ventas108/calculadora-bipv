"""
Modelo de bypass diodes para pérdida por sombra parcial en strings BIPV.

Cuando una fracción de módulos en un string queda sombreada, su Isc cae
por debajo del punto de operación del resto. Los bypass diodes se activan,
cortocircuitando esos módulos → se pierde toda su tensión Vmp, no solo
su irradiancia proporcional.  Esta pérdida es sistemáticamente mayor que
una simple reducción escalar de irradiancia.

Fuente de datos: CSV exportado por la Calculadora de Sombreado BIPV
(bipv.innovacionquimica.com.co) tras ejecutar «Cruzar Máscara + EPW».

Referencia: IEC 61724-1:2017 §7 · Deline et al. 2013 "A simplified model
of uniform shading in large photovoltaic arrays".
"""

from __future__ import annotations

import io

import numpy as np
import pandas as pd
import pvlib

from calculos.modelo_iv import obtener_constantes_tecnologia

# ── Constantes físicas ─────────────────────────────────────────────────────────
K_BOLTZMANN = 1.380649e-23
Q_ELECTRON  = 1.602176634e-19
T_REF_K     = 298.15
G_REF       = 1000.0


# ══════════════════════════════════════════════════════════════════════════════
# 1. SDM vectorizado (reutiliza misma lógica que produccion.py)
# ══════════════════════════════════════════════════════════════════════════════

def _sdm_vectorizado(
    G: np.ndarray,
    T_cel: np.ndarray,
    panel: dict,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Pmp, Isc, Imp, Vmp por módulo para arrays G y T_cel.
    Usa SDM De Soto 2006 + Rsh exponencial CdTe Mermoud 2005.
    Idéntico al modelo de produccion.py para consistencia.
    """
    constantes  = obtener_constantes_tecnologia(panel["tecnologia"])
    Vt_ref      = K_BOLTZMANN * T_REF_K / Q_ELECTRON
    nNsVth_ref  = panel["a_ref"] * Vt_ref

    G_safe = np.where(G > 0, G, 1.0)
    R_sh   = (panel["R_sh_ref"]
              * np.exp(-constantes["c_Rsh"] * (G_safe / G_REF - 1.0))
              + panel.get("R_sh_base", 0.0))

    I_L, I_o, R_s, _, nNsVth = pvlib.pvsystem.calcparams_desoto(
        effective_irradiance = G,
        temp_cell            = T_cel,
        alpha_sc             = panel["Tk_alfa"] / 100.0 * float(panel.get("Isc_stc") or panel.get("Isc") or 1.0),
        a_ref                = nNsVth_ref,
        I_L_ref              = panel["I_L_ref"],
        I_o_ref              = panel["I_o_ref"],
        R_sh_ref             = panel["R_sh_ref"],
        R_s                  = panel["R_s"],
        EgRef                = constantes["Eg_ref"],
        dEgdT                = constantes["dEgdT"],
        irrad_ref            = G_REF,
        temp_ref             = 25.0,
    )

    res = pvlib.pvsystem.singlediode(
        photocurrent       = I_L,
        saturation_current = I_o,
        resistance_series  = R_s,
        resistance_shunt   = R_sh,
        nNsVth             = nNsVth,
        method             = "lambertw",
    )

    Pmp = np.array(res["p_mp"], dtype=float)
    Isc = np.array(res["i_sc"], dtype=float)
    Imp = np.array(res["i_mp"], dtype=float)
    Vmp = np.array(res["v_mp"], dtype=float)

    # Apagar módulos con irradiancia mínima
    low = G < 5.0
    Pmp[low] = Isc[low] = Imp[low] = Vmp[low] = 0.0

    return Pmp, Isc, Imp, Vmp


# ══════════════════════════════════════════════════════════════════════════════
# 2. Simulación horaria con bypass diodes
# ══════════════════════════════════════════════════════════════════════════════

def simular_bypass_horario(
    G_eff: np.ndarray | pd.Series,
    T_amb: np.ndarray | pd.Series,
    p_shade: np.ndarray | pd.Series,
    N_series: int,
    N_parallel: int,
    panel: dict,
    NOCT: float | None = None,
    umbral_shade: float = 0.05,
) -> dict:
    """
    Simulación hora a hora del array con bypass diodes activados por sombra parcial.

    Parámetros
    ----------
    G_eff        : irradiancia efectiva W/m² (post-óptico) — 8760 horas
    T_amb        : temperatura ambiente °C
    p_shade      : fracción de módulos sombreados [0–1] por hora
                   (del CSV de la Calculadora de Sombreado)
    N_series     : módulos en serie por string
    N_parallel   : strings en paralelo
    panel        : dict del catálogo MODULOS_BIPV (SDM parameters)
    NOCT         : temperatura nominal de operación °C; si None usa panel["NOCT"]
    umbral_shade : FS mínimo para tratar como sombra activa (filtra ruido)

    Física del modelo
    -----------------
    Para cada hora con p_shade > umbral:
      · n_shade módulos reciben G_shade = G_eff × (1 – p_shade)
      · n_clear módulos reciben G_clear = G_eff
      · Bypass activa si Isc_shade < Imp_clear
           → P_string = n_clear × Pmp_clear  (módulos sombreados en cortocircuito)
      · Sin bypass (mismatch moderado):
           → P_string = n_shade × Pmp_shade + n_clear × Vmp_clear × min(Isc_shade, Imp_clear)
    La pérdida por bypass = P_dc_uniforme – P_dc_bypass por hora.

    Retorna dict
    ────────────
    P_dc_kW            : array 8760 potencia DC con bypass (kW)
    P_bypass_loss_kW   : array 8760 pérdida adicional por bypass vs modelo uniforme (kW)
    P_dc_uniforme_kW   : array 8760 potencia DC sin corrección bypass (referencia)
    horas_bypass       : horas/año con bypass activo
    horas_sombra       : horas/año con sombra activa (p_shade > umbral)
    kwh_bypass_anual   : kWh/año adicionales perdidos por bypass diodes
    pct_bypass_anual   : % de la producción DC perdida por bypass
    df_mensual_bypass  : DataFrame mensual con energías y horas de bypass
    """
    G_eff   = np.asarray(G_eff,   dtype=float)
    T_amb   = np.asarray(T_amb,   dtype=float)
    p_shade = np.asarray(p_shade, dtype=float)
    n       = len(G_eff)

    NOCT_val = float(NOCT if NOCT is not None else panel.get("NOCT", 45.0))
    T_cel    = T_amb + (NOCT_val - 20.0) / 800.0 * G_eff

    # ── Referencia: producción uniforme (sin corrección bypass) ───────────────
    Pmp_full, _, _, _ = _sdm_vectorizado(G_eff, T_cel, panel)
    P_dc_uniforme_W   = Pmp_full * N_series * N_parallel   # W

    P_dc_W        = P_dc_uniforme_W.copy()
    P_bypass_W    = np.zeros(n, dtype=float)

    # ── Horas con sombra activa ───────────────────────────────────────────────
    shade_mask = (p_shade > umbral_shade) & (G_eff > 5.0)
    horas_sombra = int(shade_mask.sum())

    if horas_sombra > 0:
        idx = np.where(shade_mask)[0]

        G_s   = G_eff[idx]
        T_s   = T_cel[idx]
        ps    = p_shade[idx]

        G_shade = G_s * (1.0 - ps)   # irradiancia sobre módulos sombreados
        G_clear = G_s                  # irradiancia sobre módulos iluminados

        # SDM para los dos grupos
        Pmp_sh, Isc_sh, Imp_sh, Vmp_sh = _sdm_vectorizado(G_shade, T_s, panel)
        Pmp_cl, Isc_cl, Imp_cl, Vmp_cl = _sdm_vectorizado(G_clear, T_s, panel)

        # Número (fraccional) de módulos por grupo en cada string
        n_shade = ps        * N_series   # fracción sombreada
        n_clear = (1.0 - ps) * N_series  # fracción iluminada

        # ── Condición de bypass ────────────────────────────────────────────────
        # Bypass activa cuando el módulo sombreado no puede suministrar Imp_clear
        bypass = Isc_sh < Imp_cl

        # ── Potencia del string con bypass activo ──────────────────────────────
        # Módulos sombreados en cortocircuito → solo los iluminados producen
        P_string_bypass = n_clear * Pmp_cl   # W por string

        # ── Potencia del string SIN bypass (mismatch moderado) ─────────────────
        # Corriente del string limitada al mínimo de los dos grupos
        I_str = np.minimum(Isc_sh, Imp_cl)
        # Módulos iluminados forzados a operar en I_str (por debajo de Imp)
        # Módulos sombreados operan cerca de su Pmp
        P_string_mismatch = n_shade * Pmp_sh + n_clear * Vmp_cl * I_str

        P_string = np.where(bypass, P_string_bypass, P_string_mismatch)
        P_string = np.maximum(P_string, 0.0)

        P_dc_array_s    = P_string * N_parallel                   # W — con bypass
        P_dc_uniforme_s = Pmp_full[idx] * N_series * N_parallel   # W — sin corrección

        P_dc_W[idx]     = P_dc_array_s
        P_bypass_W[idx] = np.maximum(P_dc_uniforme_s - P_dc_array_s, 0.0)

    # kW
    P_dc_kW         = P_dc_W        / 1000.0
    P_bypass_kW     = P_bypass_W    / 1000.0
    P_uniforme_kW   = P_dc_uniforme_W / 1000.0

    kwh_bypass       = float(P_bypass_kW.sum())
    kwh_uniforme     = float(P_uniforme_kW.sum())
    pct_bypass       = (kwh_bypass / kwh_uniforme * 100) if kwh_uniforme > 0 else 0.0
    horas_bypass     = int((P_bypass_W > 0).sum())

    # ── Resumen mensual ────────────────────────────────────────────────────────
    meses_es = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
    idx_t = pd.date_range("2001-01-01", periods=n, freq="h")
    df_by = pd.DataFrame({
        "E_dc_bypass_kWh":   P_dc_kW,
        "Pérdida_bypass_kWh": P_bypass_kW,
        "p_shade_mean":      np.asarray(p_shade, dtype=float),
        "bypass_activo":     (P_bypass_W > 0).astype(float),
        "sombra_activa":     shade_mask.astype(float),
    }, index=idx_t)

    df_m = df_by.resample("ME").agg({
        "E_dc_bypass_kWh":    "sum",
        "Pérdida_bypass_kWh": "sum",
        "p_shade_mean":       "mean",
        "bypass_activo":      "sum",
        "sombra_activa":      "sum",
    })
    df_m.columns = [
        "E_dc con bypass (kWh)",
        "Pérdida bypass (kWh)",
        "FS medio mensual",
        "Horas bypass activo",
        "Horas con sombra",
    ]
    df_m.index = [meses_es[m] for m in df_m.index.month]

    return {
        "P_dc_kW":           P_dc_kW,
        "P_bypass_loss_kW":  P_bypass_kW,
        "P_dc_uniforme_kW":  P_uniforme_kW,
        "horas_bypass":      horas_bypass,
        "horas_sombra":      horas_sombra,
        "kwh_bypass_anual":  round(kwh_bypass, 1),
        "pct_bypass_anual":  round(pct_bypass, 2),
        "kwh_dc_uniforme":   round(kwh_uniforme, 1),
        "df_mensual_bypass": df_m,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 3. Parser CSV de la Calculadora de Sombreado
# ══════════════════════════════════════════════════════════════════════════════

def cargar_csv_fs(archivo) -> tuple[pd.DataFrame, dict]:
    """
    Parsea el CSV exportado por la Calculadora de Sombreado
    (bipv.innovacionquimica.com.co / botón «Cruzar Máscara + EPW»).

    Formato estándar mínimo:
        Mes, Dia, Hora, FS

    Formato extendido (post-cruce EPW):
        Evento, Mes, Dia, Hora, Altura Solar (deg), Acimut Solar (deg),
        Obstaculo, FS_geometrico, FS_climatico, FS, Situacion

    Retorna
    -------
    (df, meta) donde:
    · df  : DataFrame con columnas [mes, dia, hora, FS] · FS ∈ [0,1] · 0=sin sombra
    · meta: dict con información sobre la fuente del FS usado:
        - "col_original"  : nombre de columna del CSV que se usó
        - "tipo"          : "geometrico" | "combinado" | "basico"
        - "descripcion"   : texto explicativo para mostrar en la UI
        - "advertencias"  : lista de strings con advertencias (puede ser vacía)

    PRIORIDAD DE COLUMNAS (razón física):
        FS_geometrico > FS (combinado) > cualquier columna FS disponible

    Los bypass diodes solo se activan por obstáculos físicos (sombra geométrica).
    Las nubes (FS_climatico) reducen la irradiancia uniformemente en todo el array
    → nunca activan bypass diodes. Usar el FS combinado (max(geom, clim)) sobreestima
    las pérdidas en días nublados. Ref: Deline et al. 2013, Eq. 3.
    """
    if hasattr(archivo, "read"):
        raw = archivo.read()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        df_raw = pd.read_csv(io.StringIO(raw))
    else:
        df_raw = pd.read_csv(archivo)

    # Normalizar nombres
    df_raw.columns = [str(c).strip() for c in df_raw.columns]

    # ── Mapear todas las columnas FS por separado ──────────────────────────────
    col_mes: str | None  = None
    col_dia: str | None  = None
    col_hora: str | None = None
    col_fs_geom: str | None     = None   # FS_geometrico — obstáculos físicos
    col_fs_clim: str | None     = None   # FS_climatico  — nubes (NO para bypass)
    col_fs_combined: str | None = None   # FS            — max(geom, clim) o básico

    for c in df_raw.columns:
        cl = c.lower().replace(" ", "_").replace("á", "a").replace("í", "i").replace("é", "e")
        if col_mes  is None and cl in ("mes", "month"):
            col_mes = c
        elif col_dia  is None and cl in ("dia", "day"):
            col_dia = c
        elif col_hora is None and cl in ("hora", "hour", "hora_utc"):
            col_hora = c
        elif col_fs_geom is None and ("fs_geometrico" in cl or "fs_geometrica" in cl):
            col_fs_geom = c
        elif col_fs_clim is None and ("fs_climatico" in cl or "fs_climatica" in cl):
            col_fs_clim = c
        elif col_fs_combined is None and cl in ("fs", "factor_sombreado", "shading_factor", "fs_combined"):
            col_fs_combined = c

    # Extraer columna de fachada — priorizar columna 'Fachada' limpia sobre 'Obstaculo'
    col_fachada: str | None = None
    col_fachada_clean: str | None = None   # columna dedicada "Fachada"
    col_obstaculo: str | None = None       # columna "Obstaculo" (fachada embebida)
    for c in df_raw.columns:
        cl = c.lower().replace(" ", "_")
        if cl in ("fachada", "facade"):
            col_fachada_clean = c
        elif cl in ("obstaculo", "obstacle"):
            col_obstaculo = c
    col_fachada = col_fachada_clean or col_obstaculo  # Fachada limpia tiene prioridad

    # ── Elegir columna FS con prioridad explícita ──────────────────────────────
    advertencias: list[str] = []

    if col_fs_geom is not None:
        # ✅ MEJOR OPCIÓN: solo sombra geométrica por obstáculos físicos
        col_fs_elegida = col_fs_geom
        tipo_fs        = "geometrico"
        descripcion_fs = (
            f"✅ Usando **{col_fs_geom}** — sombra por obstáculos físicos únicamente. "
            "Las nubes (FS_climático) se excluyen porque no activan bypass diodes."
        )
    elif col_fs_combined is not None:
        # ⚠️ SEGUNDA OPCIÓN: FS combinado (max(geom, clim))
        col_fs_elegida = col_fs_combined
        tipo_fs        = "combinado"
        descripcion_fs = (
            f"⚠️ Usando **{col_fs_combined}** (FS combinado = max(geom, clim)). "
            "El resultado puede sobreestimar bypass en días nublados porque incluye FS_climático. "
            "Para mayor precisión, usa el CSV del flujo «Cruzar Máscara + EPW» que incluye FS_geometrico."
        )
        advertencias.append(
            "CSV sin columna FS_geometrico — se usa el FS combinado. "
            "Los días nublados pueden aparecer con bypass activo de forma artificial."
        )
    else:
        # ❌ Sin ninguna columna FS válida
        raise ValueError(
            "CSV de sombreado: no se encontró ninguna columna de Factor de Sombreado.\n"
            f"Columnas presentes: {list(df_raw.columns)}\n"
            "Se esperan columnas como: FS_geometrico, FS, factor_sombreado"
        )

    # Verificar columnas obligatorias de tiempo
    faltan_tiempo = [n for n, v in [("mes", col_mes), ("dia", col_dia), ("hora", col_hora)] if v is None]
    if faltan_tiempo:
        raise ValueError(
            f"CSV de sombreado: columnas de tiempo no encontradas → {faltan_tiempo}.\n"
            f"Columnas presentes: {list(df_raw.columns)}"
        )

    # ── Construir DataFrame limpio ─────────────────────────────────────────────
    cols_leer = [col_mes, col_dia, col_hora, col_fs_elegida]
    if col_fachada and col_fachada not in cols_leer:
        cols_leer.append(col_fachada)

    df = df_raw[cols_leer].copy()
    rename: dict[str, str] = {
        col_mes:         "mes",
        col_dia:         "dia",
        col_hora:        "hora",
        col_fs_elegida:  "FS",
    }
    if col_fachada and col_fachada not in rename:
        rename[col_fachada] = "fachada"
    df = df.rename(columns=rename)

    df = df.dropna(subset=["mes", "dia", "hora"])

    # La calculadora web exporta el mes como texto ("Mar", "Dic", "Ene"…):
    # aceptar nombres/abreviaturas en español e inglés además de números.
    _MESES = {
        "ene": 1, "jan": 1, "feb": 2, "mar": 3, "abr": 4, "apr": 4,
        "may": 5, "jun": 6, "jul": 7, "ago": 8, "aug": 8,
        "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12, "dec": 12,
    }

    def _parse_mes(v: object) -> int:
        s = str(v).strip().lower()
        try:
            return int(float(s))
        except (ValueError, TypeError):
            pass
        m = _MESES.get(s[:3])
        if m is None:
            raise ValueError(f"Mes no reconocido en el CSV: '{v}'")
        return m

    df["mes"] = df["mes"].apply(_parse_mes)
    df["dia"] = df["dia"].astype(int)

    def _parse_hora(v: object) -> int:
        s = str(v).strip()
        if ":" in s:
            return int(s.split(":")[0])
        try:
            return int(float(s))
        except (ValueError, TypeError):
            return 0

    df["hora"] = df["hora"].apply(_parse_hora)
    df["FS"]   = pd.to_numeric(df["FS"], errors="coerce").fillna(0.0).clip(0.0, 1.0)

    # ── #32 Detección de convención FS (transmitancia vs p_shade) ─────────────
    # Solo aplica cuando NO tenemos FS_geometrico (que siempre es p_shade)
    convencion_probable = "p_shade"
    inversion_detectada = False
    if tipo_fs != "geometrico" and len(df) > 20:
        pct_near_1 = float((df["FS"] > 0.90).mean())
        pct_near_0 = float((df["FS"] < 0.10).mean())
        # Señal de transmitancia: la mayoría de horas sin sombra tendrán FS ≈ 1.0
        # Señal de p_shade:       la mayoría de horas sin sombra tendrán FS ≈ 0.0
        if pct_near_1 > 0.55 and pct_near_1 > pct_near_0 * 3:
            convencion_probable = "transmitancia"
            inversion_detectada = True
            advertencias.append(
                f"🔴 FORMATO POSIBLEMENTE INVERTIDO: el {pct_near_1*100:.0f}% de los valores FS "
                "son > 0.90. El CSV parece estar en **formato transmitancia** "
                "(1 = sin sombra, 0 = sombra total), pero el modelo bypass necesita "
                "**formato p_shade** (0 = sin sombra, 1 = sombra total). "
                "Este CSV probablemente fue exportado desde los 'Puntos manuales' de la "
                "calculadora, no desde 'Cruzar Máscara + EPW'. "
                "Activa la opción **'Invertir FS (1 − FS)'** para corregirlo."
            )

    # ── #33 Fachadas disponibles ───────────────────────────────────────────────
    fachadas_disponibles: list[str] = []
    if "fachada" in df.columns:
        fachadas_unicas = [str(f) for f in df["fachada"].dropna().unique()]
        fachadas_disponibles = sorted(fachadas_unicas)
        if len(fachadas_unicas) > 1:
            advertencias.append(
                f"El CSV contiene **{len(fachadas_unicas)} fachadas/obstáculos** distintos: "
                f"{', '.join(fachadas_unicas[:4])}{'…' if len(fachadas_unicas) > 4 else ''}. "
                "Selecciona la fachada de tu array en el selector de abajo."
            )

    meta: dict = {
        "col_original":        col_fs_elegida,
        "tipo":                tipo_fs,
        "descripcion":         descripcion_fs,
        "advertencias":        advertencias,
        "col_fs_geom":         col_fs_geom,
        "col_fs_clim":         col_fs_clim,
        "col_fs_combined":     col_fs_combined,
        # #32
        "convencion_probable": convencion_probable,
        "inversion_detectada": inversion_detectada,
        # #33
        "fachadas_disponibles": fachadas_disponibles,
        "tiene_fachada_col":    "fachada" in df.columns,
    }

    # Retornar df con fachada cuando esté disponible (para filtrado en UI)
    cols_out = ["mes", "dia", "hora", "FS"]
    if "fachada" in df.columns:
        cols_out.append("fachada")
    return df[cols_out].copy(), meta


# ══════════════════════════════════════════════════════════════════════════════
# 4. Alinear FS con el TMY (8760 horas)
# ══════════════════════════════════════════════════════════════════════════════

def alinear_fs_con_tmy(
    df_fs: pd.DataFrame,
    tmy_index: pd.DatetimeIndex,
    modo: str = "mensual",
) -> pd.Series:
    """
    Convierte el DataFrame de FS (mes/dia/hora) en una Serie horaria alineada
    con el TMY (8760 horas).

    Parámetros
    ----------
    df_fs     : DataFrame con columnas [mes, dia, hora, FS]
    tmy_index : DatetimeIndex del TMY (8760 timestamps)
    modo      : "mensual" (recomendado) | "exacto"

        "exacto"  — join por (mes, dia, hora). Solo los días críticos del CSV
                    tienen FS > 0. El resto del año queda FS = 0.
                    Cobertura típica: ~60–150 horas/año (< 2% del TMY).

        "mensual" — join por (mes, hora). El patrón horario del día crítico
                    se replica a todos los días del mismo mes.
                    Razonamiento: la geometría solar cambia poco dentro de
                    un mes; el día crítico (ej. 21 de marzo) es representativo
                    de todo el mes de marzo.
                    Cobertura típica: ~2 000–3 500 horas/año.

    Retorna pd.Series (índice = tmy_index, valores FS ∈ [0, 1], nombre="p_shade")
    """
    if modo == "mensual":
        # Promediar FS por (mes, hora) — replica el patrón a todos los días del mes
        df_agg = (df_fs.groupby(["mes", "hora"])["FS"]
                  .mean()
                  .reset_index()
                  .rename(columns={"FS": "FS_mean"}))

        tmy_df = pd.DataFrame({
            "mes":  tmy_index.month,
            "hora": tmy_index.hour,
        }, index=tmy_index)

        merged = tmy_df.merge(df_agg, on=["mes", "hora"], how="left")
    else:
        # "exacto": solo los timestamps que aparecen en el CSV
        df_agg = (df_fs.groupby(["mes", "dia", "hora"])["FS"]
                  .mean()
                  .reset_index()
                  .rename(columns={"FS": "FS_mean"}))

        tmy_df = pd.DataFrame({
            "mes":  tmy_index.month,
            "dia":  tmy_index.day,
            "hora": tmy_index.hour,
        }, index=tmy_index)

        merged = tmy_df.merge(df_agg, on=["mes", "dia", "hora"], how="left")

    merged.index = tmy_index
    merged["FS_mean"] = merged["FS_mean"].fillna(0.0)

    return pd.Series(merged["FS_mean"].values, index=tmy_index, name="p_shade")


def cobertura_csv(
    df_fs: pd.DataFrame,
    tmy_index: pd.DatetimeIndex,
) -> dict:
    """
    Calcula estadísticas de cobertura del CSV para ambos modos de alineación.

    Retorna dict con:
        n_exacto     : horas TMY con match exacto (mes, dia, hora)
        pct_exacto   : porcentaje de cobertura exacta
        n_mensual    : horas TMY con match mensual (mes, hora)
        pct_mensual  : porcentaje de cobertura mensual
        n_tmy        : total horas en TMY
        dias_criticos: lista de días únicos en el CSV [(mes, dia), ...]
        meses_cubiertos: lista de meses con al menos un día crítico
    """
    n_tmy = len(tmy_index)

    # ── Cobertura exacta ────────────────────────────────────────────────────
    df_ex = df_fs.groupby(["mes", "dia", "hora"])["FS"].mean().reset_index()
    tmy_ex = pd.DataFrame({
        "mes": tmy_index.month, "dia": tmy_index.day, "hora": tmy_index.hour,
    }, index=tmy_index)
    n_exacto = int(tmy_ex.merge(df_ex, on=["mes", "dia", "hora"], how="left")["FS"].notna().sum())

    # ── Cobertura mensual ───────────────────────────────────────────────────
    df_men = df_fs.groupby(["mes", "hora"])["FS"].mean().reset_index()
    tmy_men = pd.DataFrame({"mes": tmy_index.month, "hora": tmy_index.hour}, index=tmy_index)
    n_mensual = int(tmy_men.merge(df_men, on=["mes", "hora"], how="left")["FS"].notna().sum())

    # ── Días y meses cubiertos ──────────────────────────────────────────────
    dias_criticos = sorted(
        df_fs[["mes", "dia"]].drop_duplicates().apply(tuple, axis=1).tolist()
    )
    meses_cubiertos = sorted(df_fs["mes"].unique().tolist())

    return {
        "n_exacto":        n_exacto,
        "pct_exacto":      round(n_exacto / n_tmy * 100, 1),
        "n_mensual":       n_mensual,
        "pct_mensual":     round(n_mensual / n_tmy * 100, 1),
        "n_tmy":           n_tmy,
        "dias_criticos":   dias_criticos,
        "meses_cubiertos": meses_cubiertos,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 5. Helper: estadísticas del CSV cargado
# ══════════════════════════════════════════════════════════════════════════════

def estadisticas_fs(df_fs: pd.DataFrame) -> dict:
    """
    Estadísticas rápidas del DataFrame de FS para mostrar en la UI.

    Retorna dict con:
        n_puntos        : número de Puntos de Análisis distintos
        n_timestamps    : número de timestamps únicos
        fs_medio        : FS medio global
        fs_max          : FS máximo
        horas_fs_gt0    : horas con FS > 0
        horas_fs_gt50   : horas con FS > 0.5
        df_mensual_fs   : DataFrame con FS medio por mes
    """
    n_puntos    = df_fs.groupby(["mes", "dia", "hora"]).ngroups   # timestamps únicos
    # "Puntos" puede inferirse si hay obstaculo/evento column, si no = 1
    # Simplemente contar registros por timestamp
    registros_por_ts = df_fs.groupby(["mes", "dia", "hora"])["FS"].count()
    n_puntos_analisis = int(registros_por_ts.max()) if len(registros_por_ts) > 0 else 1

    fs_medio  = float(df_fs["FS"].mean())
    fs_max    = float(df_fs["FS"].max())

    df_agg = (df_fs.groupby(["mes", "dia", "hora"])["FS"].mean().reset_index())
    horas_fs_gt0  = int((df_agg["FS"] > 0.0).sum())
    horas_fs_gt50 = int((df_agg["FS"] > 0.5).sum())

    # FS medio por mes
    meses_es = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
    df_m = df_agg.groupby("mes")["FS"].mean().reset_index()
    df_m["Mes"]     = df_m["mes"].map(meses_es)
    df_m["FS medio"] = df_m["FS"].round(3)
    df_m = df_m[["Mes", "FS medio"]]

    return {
        "n_puntos_analisis": n_puntos_analisis,
        "n_timestamps":      int(len(df_agg)),
        "fs_medio":          round(fs_medio, 3),
        "fs_max":            round(fs_max, 3),
        "horas_fs_gt0":      horas_fs_gt0,
        "horas_fs_gt50":     horas_fs_gt50,
        "df_mensual_fs":     df_m,
    }
