"""
Carga el catálogo de paneles desde paneles_catalogo.xlsx.
Filtra filas con Incluir=Si y datos eléctricos completos.
"""
import re, pathlib
import pandas as pd
import streamlit as st

_EXCEL   = pathlib.Path(__file__).parent / "paneles_catalogo.xlsx"
_SHEET   = "Paneles_Comparativa"
_COLS_REQ = ["Voc (V)","Isc (A)","Vmp (V)","Imp (A)","Pmax (W)",
             "Tk-beta Voc (%/C)","Tk-gamma Pmax (%/C)","NOCT (C)"]

def _area(nombre):
    m = re.search(r'\((\d+)x(\d+)mm\)', nombre)
    return int(m.group(1))*int(m.group(2))/1e6 if m else None

@st.cache_data(ttl=3600, show_spinner="Cargando catálogo…")
def cargar_catalogo_excel() -> dict:
    if not _EXCEL.exists():
        return {}
    df = pd.read_excel(_EXCEL, sheet_name=_SHEET, header=4)
    df.columns = df.columns.str.strip()
    df = df.replace("N/D", pd.NA)
    df = df[df["Incluir (Si/No)"].astype(str).str.strip().str.upper() == "SI"]
    for col in _COLS_REQ:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=_COLS_REQ).reset_index(drop=True)
    out = {}
    for _, r in df.iterrows():
        nom = str(r["Nombre panel"]).strip()
        nsa = r.get("NsA (n\u00d7Ns)")
        out[nom] = {
            "nombre":    nom,
            "fabricante": str(r.get("Fuente","")).strip(),
            "tecnologia": str(r.get("Tecnologia","CdTe")).strip(),
            "Voc_stc":  float(r["Voc (V)"]),
            "Isc_stc":  float(r["Isc (A)"]),
            "Vmp_stc":  float(r["Vmp (V)"]),
            "Imp_stc":  float(r["Imp (A)"]),
            "Pmax_stc": float(r["Pmax (W)"]),
            "Tk_beta":  float(r["Tk-beta Voc (%/C)"]),
            "Tk_alfa":  float(r.get("Tk-alfa Isc (%/C)") or 0),
            "Tk_gamma": float(r["Tk-gamma Pmax (%/C)"]),
            "NOCT":     float(r["NOCT (C)"]),
            "a_ref":    float(nsa) if pd.notna(nsa) else None,
            "I_L_ref":  None, "I_o_ref": None,
            "R_s":      None, "R_sh_ref": None,
            "area_m2":  _area(nom),
        }
    return out

def lista_paneles_excel():
    return list(cargar_catalogo_excel().keys())

def obtener_panel_excel(nombre):
    cat = cargar_catalogo_excel()
    if nombre not in cat:
        raise KeyError(f"Panel '{nombre}' no encontrado. Disponibles: {list(cat.keys())}")
    return cat[nombre]
