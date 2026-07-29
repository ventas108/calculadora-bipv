"""Loader Catalogo_Inversores con costos y semáforo de completitud."""
import pandas as pd
import streamlit as st

_EXCEL = "/var/www/bipv/calculadora-bipv/bipv_python/datos/inversores_catalogo.xlsx"
_SHEET = "Catalogo_Inversores"

def _f(val, default=None):
    try:    return float(val)
    except: return default

@st.cache_data(ttl=3600)
def cargar_catalogo_inversores() -> dict:
    df = pd.read_excel(_EXCEL, sheet_name=_SHEET, header=2)
    df.columns = [str(c).strip() for c in df.columns]
    inversores = {}
    for _, r in df.iterrows():
        modelo = str(r.get("Modelo", "")).strip()
        if not modelo or modelo.lower() in ("", "nan"):
            continue
        completo = str(r.get("Datos completos (Si/No)", "")).strip().lower() == "si"
        costo = _f(r.get("Costo Inversor"))
        inversores[modelo] = {
            "nombre":            modelo,
            "datos_completos":   completo,
            "costo_usd":         costo if (costo and costo > 0) else None,
            "Vdc_max":           _f(r.get("Tension DC Maxima (V)")),
            "V_arranque":        _f(r.get("Tension Arranque (V)")),
            "Vmppt_min":         _f(r.get("Rango MPPT Min (V)")),
            "Vmppt_max":         _f(r.get("Rango MPPT Max (V)")),
            "V_mppt_activo":     _f(r.get("Tension Minima MPPT Activo (V)")),
            "n_trackers":        _f(r.get("N Trackers")),
            "n_strings_tracker": _f(r.get("N Strings/Tracker")),
            "I_max_tracker":     _f(r.get("Corriente Maxima Tracker (A)")),
            "Isc_max_tracker":   _f(r.get("Corriente Cortocircuito Max Tracker (A)")),
            "P_dc_max_W":        _f(r.get("Potencia FV Max Recomendada (W)")),
            # ── Aliases para dimensionamiento.py y Dimensionamiento.py ───
            "Vmppt_activo_min":  _f(r.get("Tension Minima MPPT Activo (V)")),  # = V_mppt_activo
            "N_mppt":            _f(r.get("N Trackers")),                       # = n_trackers
        }
    return inversores

cargar_catalogo_inv_excel = cargar_catalogo_inversores

def obtener_inversor_excel(nombre: str) -> dict:
    return cargar_catalogo_inversores().get(nombre, {})

def lista_inversores_excel() -> list:
    return sorted(cargar_catalogo_inversores().keys())
