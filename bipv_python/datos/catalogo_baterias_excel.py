"""
Loader del catálogo de baterías desde el mismo Excel de inversores.
Lee la hoja 'Catalogo_Baterias' (o 'Baterias' / 'Storage' como fallback).
Si la hoja no existe devuelve {} sin error.

Robusto frente a:
  - Headers con saltos de línea (\n) → se normalizan a espacio
  - Título/leyenda en filas 1-3 → se detecta automáticamente la fila de headers
  - Variantes de nombres de columna (~30 alias mapeados)
"""
import pandas as pd
import streamlit as st

_EXCEL  = "/var/www/bipv/calculadora-bipv/bipv_python/datos/inversores_catalogo.xlsx"
_SHEETS = ["Catalogo_Baterias", "Baterias", "Storage"]

# ── Identificadores que confirman que una fila es el header real ──────────
_MODELO_ALIASES = {"modelo", "nombre", "model", "battery model", "bateria"}

# ── Mapa nombre-de-columna-Excel → clave interna ──────────────────────────
# Cubre variantes con/sin tildes, con/sin paréntesis, con espacios o guión bajo
_COL_MAP = {
    # Identificación
    "Modelo":                      "nombre",
    "modelo":                      "nombre",
    "Nombre":                      "nombre",
    "Battery Model":               "nombre",
    "Bateria":                     "nombre",
    # Fabricante
    "Fabricante":                  "fabricante",
    "Manufacturer":                "fabricante",
    "Marca":                       "fabricante",
    # Datos completos
    "Datos completos (Si/No)":     "_completos",
    "Datos Completos (Si/No)":     "_completos",
    "Datos Completos":             "_completos",
    "Completo":                    "_completos",
    "Complete":                    "_completos",
    # Energía / Capacidad
    "Capacidad (kWh)":             "capacidad_kWh",
    "Capacidad kWh":               "capacidad_kWh",
    "Capacidad_kWh":               "capacidad_kWh",
    "Energía Nominal (kWh)":       "capacidad_kWh",
    "Energia Nominal (kWh)":       "capacidad_kWh",
    "Energy (kWh)":                "capacidad_kWh",
    "Usable Capacity (kWh)":       "capacidad_kWh",
    # Potencia
    "Potencia Continua (kW)":      "potencia_kW",
    "Potencia kW":                 "potencia_kW",
    "Potencia_kW":                 "potencia_kW",
    "Potencia Max (kW)":           "potencia_kW",
    "Continuous Power (kW)":       "potencia_kW",
    "Max Power (kW)":              "potencia_kW",
    # Voltaje
    "Voltaje Nominal (V)":         "voltaje_V",
    "Voltaje V":                   "voltaje_V",
    "Voltaje_V":                   "voltaje_V",
    "Tensión Nominal (V)":         "voltaje_V",
    "Tension Nominal (V)":         "voltaje_V",
    "Nominal Voltage (V)":         "voltaje_V",
    # DoD
    "DoD (%)":                     "dod_pct",
    "DoD Máximo (%)":              "dod_pct",
    "DoD Maximo (%)":              "dod_pct",
    "DoD_pct":                     "dod_pct",
    "Profundidad Descarga (%)":    "dod_pct",
    "Depth of Discharge (%)":      "dod_pct",
    # Ciclos
    "Ciclos de Vida":              "ciclos_vida",
    "Ciclos Vida":                 "ciclos_vida",
    "Ciclos":                      "ciclos_vida",
    "Cycle Life":                  "ciclos_vida",
    "Cycles":                      "ciclos_vida",
    # Eficiencia
    "Eficiencia RTE (%)":          "eta_rte_pct",
    "Eficiencia (%)":              "eta_rte_pct",
    "Eficiencia_rte_pct":          "eta_rte_pct",
    "Rendimiento (%)":             "eta_rte_pct",
    "Round-trip Efficiency (%)":   "eta_rte_pct",
    "RTE (%)":                     "eta_rte_pct",
    # Tipo / Tecnología
    "Tecnología":                  "tipo",
    "Tecnologia":                  "tipo",
    "Tipo":                        "tipo",
    "Química":                     "tipo",
    "Quimica":                     "tipo",
    "Chemistry":                   "tipo",
    # Costo
    "Costo (USD)":                 "costo_usd",
    "Costo USD":                   "costo_usd",
    "Costo Batería":               "costo_usd",
    "Costo Bateria":               "costo_usd",
    "Precio (USD)":                "costo_usd",
    "Price (USD)":                 "costo_usd",
    # Garantía
    "Garantía (años)":             "garantia_anos",
    "Garantia (años)":             "garantia_anos",
    "Garantía (anos)":             "garantia_anos",
    "Garantia (anos)":             "garantia_anos",
    "Warranty (years)":            "garantia_anos",
    # Notas
    "Notas":                       "notas",
    "Observaciones":               "notas",
    "Notes":                       "notas",
}

# Claves numéricas internas
_NUM_KEYS = {"capacidad_kWh", "potencia_kW", "voltaje_V",
             "dod_pct", "ciclos_vida", "eta_rte_pct",
             "costo_usd", "garantia_anos"}


def _f(val, default=None):
    """Convierte a float; devuelve default para None, NaN o no-numérico."""
    try:
        import math
        v = float(val)
        return default if math.isnan(v) else v
    except Exception:
        return default


def _normalizar_col(nombre: str) -> str:
    """Normaliza un nombre de columna: strip + colapsar saltos de línea a espacio."""
    return " ".join(str(nombre).strip().split())


def _detectar_header(df_raw: pd.DataFrame) -> pd.DataFrame | None:
    """
    Recibe el DataFrame leído con header=0 (fila 0 = títulos del archivo).
    Busca entre las primeras 5 filas cuál contiene 'Modelo' (o alias) en alguna celda.
    Devuelve el DataFrame releyendo con el header correcto, o None si no lo encuentra.
    """
    # Intentar primero con header=0 ya normalizado
    cols0 = [_normalizar_col(c) for c in df_raw.columns]
    if any(c.lower() in _MODELO_ALIASES for c in cols0):
        df_raw.columns = cols0
        return df_raw

    # Buscar en filas de datos (el header real está en fila 1, 2, 3…)
    for i, row in df_raw.head(5).iterrows():
        for val in row.values:
            if str(val).strip().lower() in _MODELO_ALIASES:
                return None  # señal para releer con header=i+1
    return None


@st.cache_data(ttl=3600)
def cargar_catalogo_baterias() -> dict:
    """
    Devuelve dict {nombre: {...}} con los parámetros de cada batería.
    Robusto frente a formatos de Excel con título en filas superiores.
    """
    try:
        xl = pd.ExcelFile(_EXCEL, engine="openpyxl")
    except Exception:
        return {}

    sheet_found = next((s for s in _SHEETS if s in xl.sheet_names), None)
    if sheet_found is None:
        return {}

    # ── Detectar fila de encabezados probando header=0..4 ─────────────────
    df = None
    for h in range(5):
        try:
            df_cand = pd.read_excel(_EXCEL, sheet_name=sheet_found,
                                    header=h, engine="openpyxl")
            cols = [_normalizar_col(c) for c in df_cand.columns]
            if any(c.lower() in _MODELO_ALIASES for c in cols):
                df_cand.columns = cols
                df = df_cand
                break
        except Exception:
            continue

    if df is None:
        return {}

    # ── Parsear filas ──────────────────────────────────────────────────────
    baterias = {}
    for _, r in df.iterrows():
        # Buscar nombre del modelo
        nombre = None
        for col_excel, col_int in _COL_MAP.items():
            if col_int == "nombre" and col_excel in df.columns:
                val = str(r.get(col_excel, "")).strip()
                if val and val.lower() not in ("nan", ""):
                    nombre = val
                    break
        if not nombre:
            continue
        # Ignorar filas que parezcan ser encabezados o notas
        if nombre.lower() in _MODELO_ALIASES:
            continue
        if nombre.startswith("⚠") or nombre.startswith("*") or len(nombre) > 60:
            continue

        entry = {"nombre": nombre}

        # Mapear todas las columnas reconocidas
        for col_excel, col_int in _COL_MAP.items():
            if col_int in ("nombre", "_completos"):
                continue
            if col_excel not in df.columns:
                continue
            raw = r.get(col_excel)
            if col_int in _NUM_KEYS:
                v = _f(raw)
                if v is not None:
                    entry[col_int] = v
            else:
                s = str(raw).strip() if raw is not None and str(raw).strip() != "nan" else None
                if s:
                    entry.setdefault(col_int, s)   # primer alias gana

        # Completitud
        completo_raw = ""
        for col_excel, col_int in _COL_MAP.items():
            if col_int == "_completos" and col_excel in df.columns:
                completo_raw = str(r.get(col_excel, "")).strip().lower()
                break
        entry["datos_completos"] = (completo_raw == "si")

        # ── Defaults seguros para cálculo ─────────────────────────────────
        # Solo aplican si el dato NO viene en la ficha
        if not entry.get("dod_pct"):
            entry["dod_pct"] = 80.0      # DoD conservador por defecto
        if not entry.get("eta_rte_pct"):
            entry["eta_rte_pct"] = 95.0  # RTE típico LFP
        if not entry.get("tipo"):
            entry["tipo"] = "LFP"
        if not entry.get("ciclos_vida"):
            entry["ciclos_vida"] = 3000  # ciclos mínimo conservador

        baterias[nombre] = entry

    return baterias


def obtener_bateria(nombre: str) -> dict:
    return cargar_catalogo_baterias().get(nombre, {})


def lista_baterias() -> list:
    return sorted(cargar_catalogo_baterias().keys())


def diagnostico_catalogo() -> dict:
    """
    Diagnóstico del catálogo: detecta columnas no reconocidas, modelos incompletos, etc.
    Útil para debugging desde la página 11 o desde consola.
    """
    try:
        xl = pd.ExcelFile(_EXCEL, engine="openpyxl")
    except Exception as e:
        return {"error": f"No se pudo abrir el Excel: {e}", "hojas": []}

    info = {"hojas_disponibles": xl.sheet_names}

    sheet_found = next((s for s in _SHEETS if s in xl.sheet_names), None)
    if not sheet_found:
        info["estado"] = f"Hoja no encontrada. Se buscó: {_SHEETS}"
        return info

    info["hoja_usada"] = sheet_found
    cat = cargar_catalogo_baterias()
    info["modelos_cargados"] = len(cat)
    info["nombres"] = list(cat.keys())

    campos_criticos = ["capacidad_kWh", "dod_pct", "ciclos_vida", "eta_rte_pct"]
    incompletos = []
    for nombre, b in cat.items():
        falt = [c for c in campos_criticos if not b.get(c)]
        if falt or not b.get("datos_completos"):
            incompletos.append({"modelo": nombre, "campos_faltantes": falt,
                                "datos_completos": b.get("datos_completos")})
    info["modelos_incompletos"] = incompletos

    # Columnas del Excel que no están en _COL_MAP
    for h in range(5):
        try:
            df_cand = pd.read_excel(_EXCEL, sheet_name=sheet_found,
                                    header=h, engine="openpyxl")
            cols = [_normalizar_col(c) for c in df_cand.columns]
            if any(c.lower() in _MODELO_ALIASES for c in cols):
                mapeadas   = set(_COL_MAP.keys())
                no_mapeadas = [c for c in cols if c not in mapeadas
                               and c.lower() not in _MODELO_ALIASES
                               and "unnamed" not in c.lower()]
                info["columnas_no_mapeadas"] = no_mapeadas
                break
        except Exception:
            continue

    return info
