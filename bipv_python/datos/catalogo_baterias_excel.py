"""
Loader del catálogo de baterías desde el mismo Excel de inversores.
Lee la hoja 'Catalogo_Baterias' (o 'Baterias' como fallback).
Si la hoja no existe devuelve {} sin error.
"""
import pandas as pd
import streamlit as st

_EXCEL  = "/var/www/bipv/calculadora-bipv/bipv_python/datos/inversores_catalogo.xlsx"
_SHEETS = ["Catalogo_Baterias", "Baterias", "Storage"]

# ── mapeo de nombres de columna → clave interna ────────────────────────────
_COL_MAP = {
    # Identificación
    "Modelo":                      "nombre",
    "modelo":                      "nombre",
    "Nombre":                      "nombre",
    # Datos completos
    "Datos completos (Si/No)":     "_completos",
    "Datos Completos":             "_completos",
    "Completo":                    "_completos",
    # Energía
    "Capacidad (kWh)":             "capacidad_kWh",
    "Capacidad kWh":               "capacidad_kWh",
    "Capacidad_kWh":               "capacidad_kWh",
    "Energía Nominal (kWh)":       "capacidad_kWh",
    # Potencia
    "Potencia Continua (kW)":      "potencia_kW",
    "Potencia kW":                 "potencia_kW",
    "Potencia_kW":                 "potencia_kW",
    "Potencia Max (kW)":           "potencia_kW",
    # Voltaje
    "Voltaje Nominal (V)":         "voltaje_V",
    "Voltaje V":                   "voltaje_V",
    "Voltaje_V":                   "voltaje_V",
    "Tensión Nominal (V)":         "voltaje_V",
    # DoD
    "DoD Máximo (%)":              "dod_pct",
    "DoD (%)":                     "dod_pct",
    "DoD_pct":                     "dod_pct",
    "Profundidad Descarga (%)":    "dod_pct",
    # Ciclos
    "Ciclos de Vida":              "ciclos_vida",
    "Ciclos Vida":                 "ciclos_vida",
    "Ciclos":                      "ciclos_vida",
    # Eficiencia
    "Eficiencia RTE (%)":          "eta_rte_pct",
    "Eficiencia (%)":              "eta_rte_pct",
    "Eficiencia_rte_pct":          "eta_rte_pct",
    "Rendimiento (%)":             "eta_rte_pct",
    # Tipo
    "Tecnología":                  "tipo",
    "Tipo":                        "tipo",
    "Química":                     "tipo",
    # Costo
    "Costo (USD)":                 "costo_usd",
    "Costo USD":                   "costo_usd",
    "Costo Batería":               "costo_usd",
    "Precio (USD)":                "costo_usd",
    # Garantía
    "Garantía (años)":             "garantia_anos",
    "Garantia (años)":             "garantia_anos",
    # Notas
    "Notas":                       "notas",
    "Observaciones":               "notas",
}

def _f(val, default=None):
    try:    return float(val)
    except: return default


@st.cache_data(ttl=3600)
def cargar_catalogo_baterias() -> dict:
    """Devuelve dict {nombre: {...}} con los parámetros de cada batería."""
    xl = None
    try:
        xl = pd.ExcelFile(_EXCEL, engine="openpyxl")
    except Exception:
        return {}

    sheet_found = None
    for sh in _SHEETS:
        if sh in xl.sheet_names:
            sheet_found = sh
            break
    if sheet_found is None:
        return {}

    try:
        # Intentar con header en fila 0; si el modelo es NaN en muchas filas,
        # reintentar con header=2 (mismo patrón que inversores)
        df = pd.read_excel(_EXCEL, sheet_name=sheet_found, header=0, engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]

        # Si la primera columna parece numérica (índice), intentar con header=2
        primera_col = df.columns[0]
        if primera_col.isdigit() or primera_col.lower() in ("unnamed: 0", "0", "1"):
            df = pd.read_excel(_EXCEL, sheet_name=sheet_found, header=2, engine="openpyxl")
            df.columns = [str(c).strip() for c in df.columns]
    except Exception:
        return {}

    baterias = {}
    for _, r in df.iterrows():
        # Obtener nombre usando el mapa de columnas
        nombre = None
        for col_excel, col_int in _COL_MAP.items():
            if col_int == "nombre" and col_excel in df.columns:
                val = str(r.get(col_excel, "")).strip()
                if val and val.lower() not in ("nan", ""):
                    nombre = val
                    break
        if not nombre:
            continue

        entry = {"nombre": nombre}

        # Mapear todas las columnas conocidas
        for col_excel, col_int in _COL_MAP.items():
            if col_int in ("nombre", "_completos"):
                continue
            if col_excel in df.columns:
                raw = r.get(col_excel)
                if col_int in ("capacidad_kWh", "potencia_kW", "voltaje_V",
                               "dod_pct", "ciclos_vida", "eta_rte_pct",
                               "costo_usd", "garantia_anos"):
                    entry[col_int] = _f(raw)
                else:
                    entry[col_int] = str(raw).strip() if raw and str(raw).strip() != "nan" else None

        # Completitud
        completo_raw = None
        for col_excel, col_int in _COL_MAP.items():
            if col_int == "_completos" and col_excel in df.columns:
                completo_raw = str(r.get(col_excel, "")).strip().lower()
                break
        entry["datos_completos"] = (completo_raw == "si")

        # Defaults seguros
        entry.setdefault("dod_pct",    80.0)
        entry.setdefault("eta_rte_pct", 95.0)
        entry.setdefault("tipo",       "LFP")

        baterias[nombre] = entry

    return baterias


def obtener_bateria(nombre: str) -> dict:
    return cargar_catalogo_baterias().get(nombre, {})


def lista_baterias() -> list:
    return sorted(cargar_catalogo_baterias().keys())
