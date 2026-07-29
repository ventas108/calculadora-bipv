"""Loader Catalogo_Paneles_FV — estructura unificada con costos y parámetros IV."""
import re
import pandas as pd
import streamlit as st

_EXCEL = "/var/www/bipv/calculadora-bipv/bipv_python/datos/paneles_catalogo.xlsx"
_SHEET = "Catalogo_Paneles_FV"

def _f(val, default=None):
    try:    return float(val)
    except: return default

def _parse_area(dims):
    if not dims or str(dims).strip() in ('', 'N/D', 'Variable'):
        return None
    m = re.search(r'(\d+)\s*[xX×]\s*(\d+)', str(dims))
    return round(float(m.group(1)) * float(m.group(2)) / 1e6, 4) if m else None

@st.cache_data(ttl=3600)
def cargar_catalogo_paneles() -> dict:
    df = pd.read_excel(_EXCEL, sheet_name=_SHEET, header=0)
    df.columns = [str(c).strip() for c in df.columns]
    paneles = {}
    for _, r in df.iterrows():
        pmax = _f(r.get("PmaxWp"))
        if not pmax or pmax <= 0:
            continue
        Voc = _f(r.get("Voc_STC"))
        Isc = _f(r.get("Isc_STC"))
        if Voc is not None and Voc < 10:   continue
        if Isc is not None and Isc > 100:  continue
        nombre = str(r.get("TipoPanel", "")).strip()
        if not nombre: continue
        Vmp = _f(r.get("Vmp_STC"))
        Imp = _f(r.get("Imp_STC"))
        costo = _f(r.get("CostoUSD"))
        paneles[nombre] = {
            "nombre":            nombre,
            "marca":             str(r.get("Marca", "")).strip(),
            "tecnologia":        str(r.get("Tecnologia", r.get("Tecnología", ""))).strip(),
            "Pmax_stc":          pmax,
            "dimensiones_mm":    str(r.get("DimensionesMM", "")).strip(),
            "area_m2":           _parse_area(r.get("DimensionesMM")),
            "costo_usd":         costo if (costo and costo > 0) else None,
            "NOCT":              _f(r.get("NOCT_C")),
            "beta_mp":           _f(r.get("CoefT_C")),
            "CoefVoc_C":         _f(r.get("CoefVoc_C")),
            "transparencia_pct": _f(r.get("TransparenciaPct"), 0),
            "Voc": Voc, "Vmp": Vmp,
            "Isc": Isc, "Imp": Imp,
            "N_s":         _f(r.get("Ns (Celdas Serie)")),
            "n_idealidad": _f(r.get("n (Factor Idealidad)")),
            "NsA":         _f(r.get("NsA = n × Ns")),
            "fuente_NsA":  str(r.get("Fuente NsA", "")).strip(),
            "confianza":   str(r.get("Confianza", "")).strip(),
            "notas":       str(r.get("Notas", "")).strip(),
            "I_sc_ref": Isc, "V_oc_ref": Voc,
            "I_mp_ref": Imp, "V_mp_ref": Vmp,
            "alpha_sc": None, "beta_oc": _f(r.get("CoefVoc_C")),
            "gamma_mp": _f(r.get("CoefT_C")),
            "I_L_ref": None, "I_o_ref": None,
            "R_s": None, "R_sh_ref": None,
        }
    return paneles

def obtener_panel_excel(nombre: str) -> dict:
    return cargar_catalogo_paneles().get(nombre, {})

def lista_paneles_excel() -> list:
    return sorted(cargar_catalogo_paneles().keys())
