"""
Módulo B-6 / B-7 — Dimensionado de baterías y balance energético mensual BIPV.

B-6: dimensionar_bateria()      → tamaño, N baterías, costos, vida estimada
B-7: balance_mensual()          → DataFrame producción vs consumo mes a mes
     balance_horario()          → balance hora a hora (resolución horaria)
     clasificar_energia()       → clase A+/A/B/C/D + color semáforo
     metricas_balance()         → KPIs consolidados del balance

Clasificación (fracción solar = % del consumo cubierto por solar):
    A+  ≥ 90 %  — Edificio casi autónomo / Net Zero
    A   75–89 % — Alta autosuficiencia
    B   50–74 % — Autosuficiencia media
    C   25–49 % — Autosuficiencia básica
    D   < 25 %  — Alta dependencia de red
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# Perfiles de carga típicos Colombia (distribución mensual normalizada)
# Fuente: UPME 2022 — Demanda mensual normalizada por tipo de uso
# ─────────────────────────────────────────────────────────────────────────────
PERFILES_TIPICOS = {
    "Residencial (casa/apto)": [
        0.082, 0.075, 0.082, 0.082, 0.085, 0.084,
        0.086, 0.086, 0.084, 0.085, 0.082, 0.087,
    ],
    "Comercial (oficinas/tiendas)": [
        0.087, 0.080, 0.088, 0.086, 0.086, 0.082,
        0.082, 0.082, 0.086, 0.087, 0.086, 0.068,
    ],
    "Industrial (manufactura)": [
        0.086, 0.079, 0.087, 0.085, 0.087, 0.083,
        0.083, 0.085, 0.085, 0.087, 0.085, 0.068,
    ],
    "Institucional (hospitales/colegios)": [
        0.085, 0.078, 0.086, 0.085, 0.086, 0.083,
        0.076, 0.076, 0.086, 0.086, 0.086, 0.087,
    ],
    "Uniforme (12 meses iguales)": [1/12] * 12,
}

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

DIAS_MES = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# ─────────────────────────────────────────────────────────────────────────────
# Perfiles de carga HORARIOS típicos Colombia (pesos por hora 0–23)
# Fuente: CREG/XM — Demanda típica horaria normalizada por tipo de uso.
# Los pesos se normalizan internamente (suma = 1 sobre 24h) de modo que
# multiplicando por el consumo diario (kWh/día) se obtiene el consumo por hora.
# ─────────────────────────────────────────────────────────────────────────────
_PERFILES_HORARIOS_RAW: dict[str, list[float]] = {
    # Oficinas/comercio: pico 9–18 h, casi nulo de noche
    "Oficina / Comercio": [
        2, 2, 2, 2, 2, 3, 5, 8, 10, 10, 10, 9,
        7, 9, 10, 10, 9, 7, 5, 3, 2, 2, 2, 2,
    ],
    # Residencial: pico matutino (6–8 h) y vespertino (17–21 h)
    "Residencial": [
        2, 2, 2, 2, 2, 3, 6, 7, 6, 4, 4, 5,
        6, 4, 4, 5, 6, 8, 9, 9, 8, 7, 5, 3,
    ],
    # Industria/manufactura: turno diurno 6–18 h, mínimo nocturno
    "Industrial": [
        2, 2, 2, 2, 2, 3, 8, 10, 10, 10, 10, 10,
        9, 10, 10, 10, 10, 9, 7, 5, 4, 3, 2, 2,
    ],
    # Hospital: relativamente plano las 24 h con ligero pico diurno
    "Hospital / Institucional": [
        5, 5, 5, 5, 5, 5, 6, 7, 8, 8, 8, 8,
        7, 7, 8, 8, 8, 7, 6, 6, 6, 5, 5, 5,
    ],
}

def _normalizar_perfil_horario(pesos: list[float]) -> list[float]:
    """Normaliza los pesos para que sumen 1.0 (fracción del consumo diario por hora)."""
    total = sum(pesos)
    return [p / total for p in pesos]

PERFILES_HORARIOS: dict[str, list[float]] = {
    nombre: _normalizar_perfil_horario(pesos)
    for nombre, pesos in _PERFILES_HORARIOS_RAW.items()
}

# Clasificación energética
_CLASES = [
    (90, "A+", "🟢", "#2ecc71", "Edificio casi autónomo / Net Zero"),
    (75, "A",  "🟢", "#27ae60", "Alta autosuficiencia energética"),
    (50, "B",  "🟡", "#f39c12", "Autosuficiencia media"),
    (25, "C",  "🟠", "#e67e22", "Autosuficiencia básica"),
    ( 0, "D",  "🔴", "#e74c3c", "Alta dependencia de la red eléctrica"),
]


# ─────────────────────────────────────────────────────────────────────────────
# B-6: Dimensionado de baterías
# ─────────────────────────────────────────────────────────────────────────────

def dimensionar_bateria(
    bateria: dict,
    E_consumo_diario_kWh: float,
    autonomia_h: float,
) -> dict:
    """
    Calcula número de unidades, capacidad instalada, DoD real y vida estimada.

    Parameters
    ----------
    bateria              : dict del catálogo (capacidad_kWh, dod_pct, ciclos_vida, etc.)
    E_consumo_diario_kWh : consumo diario promedio del edificio en kWh
    autonomia_h          : horas de autonomía deseadas (1–48 h)

    Returns
    -------
    dict con claves: N_baterias, C_instalada_kWh, C_util_kWh, dod_real_pct,
                     vida_estimada_anos, costo_total_usd, advertencias
    """
    cap_unit  = bateria.get("capacidad_kWh") or 0
    dod_max   = (bateria.get("dod_pct")    or 80.0) / 100.0
    eta_rte   = (bateria.get("eta_rte_pct") or 95.0) / 100.0
    ciclos    = bateria.get("ciclos_vida")  or 3000
    costo_u   = bateria.get("costo_usd")   or None

    advertencias = []

    if cap_unit <= 0:
        return {"error": "Batería sin capacidad definida en catálogo"}

    # Energía necesaria para la autonomía solicitada (considerando eficiencia RTE)
    E_necesaria_kWh = E_consumo_diario_kWh * (autonomia_h / 24.0) / eta_rte

    # Capacidad bruta requerida (descontando DoD)
    C_bruta_req = E_necesaria_kWh / dod_max

    # Número de baterías (redondear arriba)
    N_baterias = max(1, math.ceil(C_bruta_req / cap_unit))

    C_instalada = N_baterias * cap_unit
    C_util      = C_instalada * dod_max * eta_rte  # kWh realmente aprovechables

    # DoD real con las N baterías seleccionadas
    dod_real = (E_necesaria_kWh / C_instalada) * 100.0
    dod_real = min(dod_real, (bateria.get("dod_pct") or 80.0))

    # Vida estimada: asumiendo 1 ciclo/día promedio × factor DoD
    # Ciclos_garanizados se dan a DoD nominal; ajustar por DoD real
    factor_dod = (dod_real / 100.0) / max(dod_max, 0.01)
    ciclos_equiv = ciclos / max(factor_dod, 0.1)
    vida_anos = round(ciclos_equiv / 365.0, 1)

    if dod_real > (bateria.get("dod_pct") or 80.0):
        advertencias.append(
            f"DoD real ({dod_real:.1f}%) supera el límite del fabricante "
            f"({bateria.get('dod_pct',80)}%). Aumentar número de baterías."
        )
    if vida_anos < 5:
        advertencias.append(
            "Vida estimada < 5 años. Revisar autonomía solicitada o seleccionar "
            "batería de mayor capacidad."
        )

    costo_total = (N_baterias * costo_u) if costo_u else None

    return {
        "N_baterias":         N_baterias,
        "cap_unitaria_kWh":   round(cap_unit, 2),
        "C_instalada_kWh":    round(C_instalada, 2),
        "C_util_kWh":         round(C_util, 2),
        "dod_real_pct":       round(dod_real, 1),
        "dod_max_pct":        bateria.get("dod_pct", 80.0),
        "eta_rte_pct":        (bateria.get("eta_rte_pct") or 95.0),
        "ciclos_vida":        ciclos,
        "vida_estimada_anos": vida_anos,
        "costo_total_usd":    round(costo_total, 0) if costo_total else None,
        "costo_unitario_usd": costo_u,
        "advertencias":       advertencias,
    }


# ─────────────────────────────────────────────────────────────────────────────
# B-7: Balance energético mensual
# ─────────────────────────────────────────────────────────────────────────────

def distribuir_consumo_anual(
    consumo_anual_kWh: float,
    perfil: str = "Uniforme (12 meses iguales)",
) -> list[float]:
    """Distribuye un consumo anual en 12 valores mensuales según perfil típico."""
    pesos = PERFILES_TIPICOS.get(perfil, PERFILES_TIPICOS["Uniforme (12 meses iguales)"])
    return [round(consumo_anual_kWh * p, 1) for p in pesos]


def balance_mensual(
    df_mensual_prod: pd.DataFrame,
    consumo_mensual_kWh: list[float],
    bateria_dim: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Calcula el balance energético mes a mes.

    Parameters
    ----------
    df_mensual_prod   : DataFrame de Producción con columna 'E_ac_kWh' (o similar)
                        índice puede ser entero 0-11 o nombre de mes
    consumo_mensual_kWh : lista de 12 valores de consumo mensual [kWh]
    bateria_dim       : dict de dimensionar_bateria() o None si no hay batería

    Returns
    -------
    DataFrame con 12 filas y columnas:
        mes, E_solar_kWh, E_consumo_kWh,
        autoconsumo_directo_kWh, excedente_kWh, deficit_kWh,
        E_bateria_cargada_kWh, E_bateria_descargada_kWh,
        autoconsumo_total_kWh, deficit_neto_kWh,
        fraccion_solar_pct, exportacion_kWh
    """
    # ── Normalizar columna de producción ────────────────────────────────────
    # produccion.py genera columnas con espacios y tildes: "E_ac (kWh)", etc.
    prod_col = None
    for c in ["E_ac (kWh)", "E_ac_kWh", "E_ac", "e_ac_kWh", "Eac_kWh", "kWh_ac"]:
        if c in df_mensual_prod.columns:
            prod_col = c
            break
    if prod_col is None:
        # intentar cualquier columna numérica que no sea índice
        num_cols = df_mensual_prod.select_dtypes(include=[np.number]).columns.tolist()
        prod_col = num_cols[0] if num_cols else None

    if prod_col is None:
        raise ValueError("df_mensual_prod no tiene columna de producción AC reconocible")

    E_solar = df_mensual_prod[prod_col].values[:12].astype(float)

    # Asegurar 12 valores
    if len(consumo_mensual_kWh) < 12:
        consumo_mensual_kWh = list(consumo_mensual_kWh) + [0.0] * (12 - len(consumo_mensual_kWh))
    E_cons = np.array(consumo_mensual_kWh[:12], dtype=float)

    # ── Sin batería ──────────────────────────────────────────────────────────
    autoconsumo_dir = np.minimum(E_solar, E_cons)
    excedente       = np.maximum(E_solar - E_cons, 0.0)
    deficit         = np.maximum(E_cons - E_solar, 0.0)

    # ── Con batería ─────────────────────────────────────────────────────────
    if bateria_dim and bateria_dim.get("C_util_kWh", 0) > 0:
        C_util    = bateria_dim["C_util_kWh"]   # kWh aprovechables por ciclo
        eta_rte   = (bateria_dim.get("eta_rte_pct", 95.0)) / 100.0
        bat_cargada    = np.zeros(12)
        bat_descargada = np.zeros(12)
        for m in range(12):
            dias = DIAS_MES[m]
            # Capacidad mensual almacenable (C_util × ciclos_mes × eta)
            cap_mensual = C_util * dias
            # Se carga con el excedente solar (limitado por cap mensual)
            # Nota: C_util ya incluye el factor eta_rte aplicado en dimensionar_bateria().
            # No multiplicar de nuevo para evitar doble conteo de pérdidas RTE.
            bat_cargada[m]    = min(excedente[m], cap_mensual)
            # Se descarga para cubrir déficit (limitado por lo que se cargó)
            bat_descargada[m] = min(deficit[m], bat_cargada[m])
    else:
        bat_cargada    = np.zeros(12)
        bat_descargada = np.zeros(12)

    autoconsumo_total = autoconsumo_dir + bat_descargada
    deficit_neto      = deficit - bat_descargada
    exportacion       = excedente - bat_cargada  # sobrante después de cargar batería

    fraccion_solar    = np.where(E_cons > 0, autoconsumo_total / E_cons * 100, 0.0)

    df = pd.DataFrame({
        "mes":                        MESES,
        "dias":                       DIAS_MES,
        "E_solar_kWh":                np.round(E_solar, 1),
        "E_consumo_kWh":              np.round(E_cons,  1),
        "autoconsumo_directo_kWh":    np.round(autoconsumo_dir, 1),
        "excedente_kWh":              np.round(excedente, 1),
        "deficit_kWh":                np.round(deficit, 1),
        "E_bateria_cargada_kWh":      np.round(bat_cargada, 1),
        "E_bateria_descargada_kWh":   np.round(bat_descargada, 1),
        "autoconsumo_total_kWh":      np.round(autoconsumo_total, 1),
        "deficit_neto_kWh":           np.round(deficit_neto, 1),
        "exportacion_kWh":            np.round(np.maximum(exportacion, 0), 1),
        "fraccion_solar_pct":         np.round(fraccion_solar, 1),
    })
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Métricas anuales del balance
# ─────────────────────────────────────────────────────────────────────────────

def metricas_balance(df: pd.DataFrame) -> dict:
    """KPIs anuales a partir del DataFrame de balance_mensual()."""
    E_solar     = df["E_solar_kWh"].sum()
    E_cons      = df["E_consumo_kWh"].sum()
    E_ac_total  = df["autoconsumo_total_kWh"].sum()
    E_export    = df["exportacion_kWh"].sum()
    E_deficit   = df["deficit_neto_kWh"].sum()
    E_bat_desc  = df["E_bateria_descargada_kWh"].sum()

    fraccion_solar   = (E_ac_total / E_cons * 100) if E_cons > 0 else 0.0
    autoconsumo_rate = (E_ac_total / E_solar * 100) if E_solar > 0 else 0.0
    cobertura_neta   = ((E_solar - E_export) / E_cons * 100) if E_cons > 0 else 0.0

    return {
        "E_solar_anual_kWh":        round(E_solar, 0),
        "E_consumo_anual_kWh":      round(E_cons, 0),
        "E_autoconsumo_anual_kWh":  round(E_ac_total, 0),
        "E_exportacion_anual_kWh":  round(E_export, 0),
        "E_deficit_anual_kWh":      round(E_deficit, 0),
        "E_bateria_total_kWh":      round(E_bat_desc, 0),
        "fraccion_solar_pct":       round(fraccion_solar, 1),
        "tasa_autoconsumo_pct":     round(autoconsumo_rate, 1),
        "cobertura_neta_pct":       round(cobertura_neta, 1),
        "ratio_solar_consumo":      round(E_solar / E_cons, 3) if E_cons > 0 else 0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# B-7b: Balance energético HORARIO (resolución hora a hora)
# ─────────────────────────────────────────────────────────────────────────────

def balance_horario(
    df_horario_prod: pd.DataFrame,
    consumo_anual_kWh: float,
    perfil_tipo: str = "Residencial",
    bateria_dim: Optional[dict] = None,
) -> dict:
    """
    Balance energético hora a hora usando el perfil de 24 h normalizado.

    Parameters
    ----------
    df_horario_prod  : DataFrame horario de producción con columna "P_ac_kW"
                       e índice DatetimeIndex (8 760 filas típicas).
    consumo_anual_kWh: Consumo anual total del edificio (kWh/año).
    perfil_tipo      : Clave de PERFILES_HORARIOS ("Residencial", "Oficina /
                       Comercio", "Industrial", "Hospital / Institucional").
    bateria_dim      : dict de dimensionar_bateria() o None si no hay batería.

    Returns
    -------
    dict con claves:
        df_balance_horario  : DataFrame 8760 filas — balance hora a hora
        df_balance_mensual  : DataFrame 12 filas — mismo esquema que balance_mensual()
        df_perfil_diario    : DataFrame 24 filas — producción y consumo promedio por hora
        metricas            : dict de metricas_balance() aplicado al df mensual
        perfil_normalizado  : lista de 24 pesos usada
    """
    # ── Columna de producción ────────────────────────────────────────────────
    prod_col = None
    for c in ["P_ac_kW", "E_ac_kWh", "P_ac", "p_ac_kW"]:
        if c in df_horario_prod.columns:
            prod_col = c
            break
    if prod_col is None:
        num_cols = df_horario_prod.select_dtypes(include=[np.number]).columns.tolist()
        prod_col = num_cols[0] if num_cols else None
    if prod_col is None:
        raise ValueError("df_horario_prod no tiene columna de potencia AC reconocible")

    # ── Índice horario ────────────────────────────────────────────────────────
    idx = df_horario_prod.index
    if not isinstance(idx, pd.DatetimeIndex):
        raise ValueError("df_horario_prod requiere DatetimeIndex")

    E_solar_h = df_horario_prod[prod_col].values.astype(float)   # kWh por hora

    # ── Consumo horario desde perfil normalizado ──────────────────────────────
    perfil_24h = PERFILES_HORARIOS.get(perfil_tipo,
                                       PERFILES_HORARIOS["Residencial"])
    consumo_diario = consumo_anual_kWh / 365.0
    # Fracción horaria del día según el perfil; misma forma que idx para
    # alinear perfectamente con la serie de producción.
    horas = idx.hour.values
    E_consumo_h = consumo_diario * np.array([perfil_24h[h] for h in horas])

    # ── Autoconsumo directo sin batería ────────────────────────────────────────
    autoconsumo_dir_h = np.minimum(E_solar_h, E_consumo_h)
    excedente_h       = np.maximum(E_solar_h - E_consumo_h, 0.0)
    deficit_h         = np.maximum(E_consumo_h - E_solar_h, 0.0)

    # ── Simulación de batería hora a hora ────────────────────────────────────
    N_h = len(E_solar_h)
    bat_cargada_h    = np.zeros(N_h)
    bat_descargada_h = np.zeros(N_h)
    soc_h            = np.zeros(N_h)   # State of Charge [kWh]

    if bateria_dim and bateria_dim.get("C_util_kWh", 0) > 0:
        C_util  = float(bateria_dim["C_util_kWh"])
        eta_rte = float(bateria_dim.get("eta_rte_pct", 95.0)) / 100.0
        # Eficiencias unidireccionales simétricas (sqrt del round-trip)
        eta_c = math.sqrt(eta_rte)   # eficiencia de carga
        eta_d = math.sqrt(eta_rte)   # eficiencia de descarga

        soc = 0.0   # comienza vacía
        for h in range(N_h):
            exc = excedente_h[h]
            def_ = deficit_h[h]

            # Carga: el excedente va a la batería (pérdida en el proceso de carga)
            energia_a_almacenar = min(exc * eta_c, C_util - soc)
            soc += energia_a_almacenar
            bat_cargada_h[h] = energia_a_almacenar

            # Descarga: la batería entrega al edificio (pérdida en descarga)
            energia_disponible = soc * eta_d          # kWh que puede entregar
            descarga = min(def_, energia_disponible)
            soc -= (descarga / eta_d) if eta_d > 0 else descarga   # quitar del SoC
            soc = max(soc, 0.0)
            bat_descargada_h[h] = descarga

            soc_h[h] = soc

    autoconsumo_total_h = autoconsumo_dir_h + bat_descargada_h
    deficit_neto_h      = deficit_h - bat_descargada_h
    exportacion_h       = np.maximum(excedente_h - bat_cargada_h, 0.0)

    # ── DataFrame horario ─────────────────────────────────────────────────────
    df_bal_h = pd.DataFrame({
        "E_solar_kWh":              np.round(E_solar_h, 4),
        "E_consumo_kWh":            np.round(E_consumo_h, 4),
        "autoconsumo_directo_kWh":  np.round(autoconsumo_dir_h, 4),
        "excedente_kWh":            np.round(excedente_h, 4),
        "deficit_kWh":              np.round(deficit_h, 4),
        "E_bateria_cargada_kWh":    np.round(bat_cargada_h, 4),
        "E_bateria_descargada_kWh": np.round(bat_descargada_h, 4),
        "autoconsumo_total_kWh":    np.round(autoconsumo_total_h, 4),
        "deficit_neto_kWh":         np.round(deficit_neto_h, 4),
        "exportacion_kWh":          np.round(exportacion_h, 4),
        "soc_kWh":                  np.round(soc_h, 4),
    }, index=idx)

    # ── Agregación mensual (mismo esquema que balance_mensual) ────────────────
    meses_num_a_es = {
        1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
        7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic",
    }
    df_m = df_bal_h.resample("ME").sum().copy()
    df_m["mes"]  = [meses_num_a_es[m] for m in df_m.index.month]
    df_m["dias"] = df_m.index.days_in_month.values
    E_sol_m  = df_m["E_solar_kWh"].values
    E_con_m  = df_m["E_consumo_kWh"].values
    frac_sol = np.where(E_con_m > 0, df_m["autoconsumo_total_kWh"].values / E_con_m * 100, 0.0)
    df_m["fraccion_solar_pct"] = np.round(frac_sol, 1)

    # Reordenar columnas para coincidir con balance_mensual()
    cols_orden = [
        "mes", "dias", "E_solar_kWh", "E_consumo_kWh",
        "autoconsumo_directo_kWh", "excedente_kWh", "deficit_kWh",
        "E_bateria_cargada_kWh", "E_bateria_descargada_kWh",
        "autoconsumo_total_kWh", "deficit_neto_kWh",
        "exportacion_kWh", "fraccion_solar_pct",
    ]
    df_bal_mensual = df_m[[c for c in cols_orden if c in df_m.columns]].copy()
    df_bal_mensual = df_bal_mensual.reset_index(drop=True)
    # Redondear a 1 decimal igual que balance_mensual()
    for col in ["E_solar_kWh","E_consumo_kWh","autoconsumo_directo_kWh",
                "excedente_kWh","deficit_kWh","E_bateria_cargada_kWh",
                "E_bateria_descargada_kWh","autoconsumo_total_kWh",
                "deficit_neto_kWh","exportacion_kWh"]:
        if col in df_bal_mensual.columns:
            df_bal_mensual[col] = df_bal_mensual[col].round(1)

    # ── Perfil diario promedio (24 h) ─────────────────────────────────────────
    df_bal_h["hora"] = df_bal_h.index.hour
    df_perfil = df_bal_h.groupby("hora")[
        ["E_solar_kWh", "E_consumo_kWh", "autoconsumo_total_kWh",
         "deficit_neto_kWh", "exportacion_kWh"]
    ].mean().reset_index()
    df_perfil.columns = ["hora", "solar_prom_kWh", "consumo_prom_kWh",
                          "autoconsumo_prom_kWh", "deficit_prom_kWh",
                          "exportacion_prom_kWh"]

    metr = metricas_balance(df_bal_mensual)

    return {
        "df_balance_horario":  df_bal_h,
        "df_balance_mensual":  df_bal_mensual,
        "df_perfil_diario":    df_perfil,
        "metricas":            metr,
        "perfil_normalizado":  perfil_24h,
        "perfil_tipo":         perfil_tipo,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Clasificación A+/A/B/C/D
# ─────────────────────────────────────────────────────────────────────────────

def clasificar_energia(fraccion_solar_pct: float) -> dict:
    """
    Devuelve la clase energética basada en fracción solar (% del consumo cubierto).

    Returns dict: clase, emoji, color_hex, descripcion, fraccion_solar_pct, umbral
    """
    for umbral, clase, emoji, color, descripcion in _CLASES:
        if fraccion_solar_pct >= umbral:
            return {
                "clase":              clase,
                "emoji":              emoji,
                "color_hex":          color,
                "descripcion":        descripcion,
                "fraccion_solar_pct": round(fraccion_solar_pct, 1),
                "umbral_min_pct":     umbral,
            }
    # Fallback
    return clasificar_energia(0.0)


def tabla_clasificaciones() -> pd.DataFrame:
    """Devuelve la tabla completa de rangos de clasificación."""
    filas = []
    umbrales = [90, 75, 50, 25, 0]
    topes    = [100, 90, 75, 50, 25]
    for i, (umbral, clase, emoji, color, desc) in enumerate(_CLASES):
        filas.append({
            "Clase":           f"{emoji} {clase}",
            "Fracción solar":  f"≥ {umbral}%" if umbral > 0 else f"< {topes[i]}%",
            "Descripción":     desc,
        })
    return pd.DataFrame(filas)
