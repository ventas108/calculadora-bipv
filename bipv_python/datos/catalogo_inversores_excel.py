"""
Carga el catálogo de inversores desde inversores_catalogo.xlsx.
Filtra filas con Datos completos=Si.
"""
import pathlib, re
import pandas as pd
import streamlit as st

_EXCEL  = pathlib.Path(__file__).parent / "inversores_catalogo.xlsx"
_SHEET  = "Catalogo_Inversores"
_COLS_REQ = [
    "Tension DC Maxima (V)", "Rango MPPT Min (V)", "Rango MPPT Max (V)",
    "N Trackers", "N Strings/Tracker",
    "Corriente Maxima Tracker (A)", "Corriente Cortocircuito Max Tracker (A)"
]

def _brand(archivo):
    s = str(archivo).strip()
    m = re.match(r'^([A-Za-z]+)', s)
    return m.group(1).title() if m else "Otro"

@st.cache_data(ttl=3600, show_spinner="Cargando inversores…")
def cargar_catalogo_inversores() -> dict:
    if not _EXCEL.exists():
        return {}
    df = pd.read_excel(_EXCEL, sheet_name=_SHEET, header=2)
    df.columns = df.columns.str.strip()
    df = df.replace("N/D", pd.NA)
    col_inc = [c for c in df.columns if "completos" in c.lower() or "incluir" in c.lower()]
    if col_inc:
        df = df[df[col_inc[0]].astype(str).str.strip().str.upper() == "SI"]
    for col in _COLS_REQ:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=[c for c in _COLS_REQ if c in df.columns]).reset_index(drop=True)
    out = {}
    for _, r in df.iterrows():
        modelo  = str(r.get("Modelo","")).strip()
        archivo = str(r.get("Archivo origen","")).strip()
        brand   = _brand(archivo)
        key     = f"{brand}-{modelo}".replace(" ","")
        out[key] = {
            "fabricante":        brand,
            "modelo":            modelo,
            "fuente":            archivo,
            "Vdc_max":           _f(r, "Tension DC Maxima (V)"),
            "Voc_arranque":      _f(r, "Tension Arranque (V)"),
            "Vmppt_min":         _f(r, "Rango MPPT Min (V)"),
            "Vmppt_max":         _f(r, "Rango MPPT Max (V)"),
            "Vmppt_activo_min":  _f(r, "Tension Minima MPPT Activo (V)"),
            "N_mppt":            _i(r, "N Trackers"),
            "N_strings_nativo":  _i(r, "N Strings/Tracker"),
            "I_max_tracker":     _f(r, "Corriente Maxima Tracker (A)"),
            "Isc_max_tracker":   _f(r, "Corriente Cortocircuito Max Tracker (A)"),
            "P_dc_max_W":        _f(r, "Potencia FV Max Recomendada (W)"),
            "P_ac_nom_W":        None,
            "eficiencia_max":    None,
        }
    return out

def _f(r, col):
    v = r.get(col)
    return float(v) if pd.notna(v) else None

def _i(r, col):
    v = r.get(col)
    return int(v) if pd.notna(v) else None

def lista_inversores_excel():
    return list(cargar_catalogo_inversores().keys())

def obtener_inversor_excel(nombre):
    cat = cargar_catalogo_inversores()
    if nombre not in cat:
        raise KeyError(f"Inversor '{nombre}' no encontrado. Disponibles: {list(cat.keys())}")
    return cat[nombre]
