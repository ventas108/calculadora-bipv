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
        if not nombre or len(nombre) < 5: continue  # filtra entradas basura/prueba (ej. "yaya")
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
            # ── Aliases para dimensionamiento.py ─────────────────────────
            "Voc_stc":  Voc,                          # = Voc_STC  del Excel
            "Vmp_stc":  Vmp,                          # = Vmp_STC  del Excel
            "Isc_stc":  Isc,                          # = Isc_STC  del Excel
            "Tk_beta":  _f(r.get("CoefVoc_C")),       # coef. temp. Voc  (%/°C)
            "Tk_gamma": _f(r.get("CoefT_C")),         # coef. temp. Pmax (%/°C)
            "I_L_ref": None, "I_o_ref": None,
            "R_s": None, "R_sh_ref": None,
        }
    return paneles

def guardar_panel_excel(datos: dict) -> str:
    """
    Agrega o actualiza un panel en el Excel del catálogo.
    Retorna el nombre del panel guardado.
    Invalida el cache de st.cache_data para que el próximo cargar_catalogo_paneles() lea el nuevo panel.
    """
    import openpyxl, datetime

    nombre = str(datos.get("TipoPanel", "")).strip()
    if not nombre:
        raise ValueError("El campo TipoPanel (nombre del modelo) es obligatorio.")

    try:
        wb = openpyxl.load_workbook(_EXCEL)
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {_EXCEL}")

    if _SHEET not in wb.sheetnames:
        raise ValueError(f"La hoja '{_SHEET}' no existe en {_EXCEL}.")

    ws = wb[_SHEET]

    # Leer encabezados de la primera fila
    headers = [str(c.value).strip() if c.value else "" for c in ws[1]]

    # Comprobar si ya existe una fila con ese nombre (actualizar) o agregar
    fila_existente = None
    col_tipo = None
    try:
        col_tipo = headers.index("TipoPanel") + 1   # 1-based
    except ValueError:
        raise ValueError("La hoja no tiene columna 'TipoPanel'.")

    for row in ws.iter_rows(min_row=2):
        if str(row[col_tipo - 1].value or "").strip() == nombre:
            fila_existente = row[0].row
            break

    if fila_existente is None:
        fila_existente = ws.max_row + 1

    # Escribir datos — solo columnas que existen en el encabezado
    for col_nombre, valor in datos.items():
        if col_nombre in headers:
            col_idx = headers.index(col_nombre) + 1
            ws.cell(row=fila_existente, column=col_idx, value=valor)

    # Anotar fecha de ingreso si hay columna
    for meta_col in ("FechaIngreso", "Fecha_Ingreso", "Fecha"):
        if meta_col in headers:
            ws.cell(
                row=fila_existente,
                column=headers.index(meta_col) + 1,
                value=datetime.date.today().isoformat()
            )
            break

    wb.save(_EXCEL)

    # Invalidar cache para que la próxima carga refleje el nuevo panel
    try:
        cargar_catalogo_paneles.clear()
    except Exception:
        pass

    return nombre


def eliminar_panel_excel(nombre: str) -> bool:
    """
    Elimina la fila del panel con TipoPanel == nombre del Excel.
    Retorna True si se eliminó, False si no se encontró.
    Invalida el cache.
    """
    import openpyxl

    nombre = nombre.strip()
    if not nombre:
        raise ValueError("Nombre vacío.")

    try:
        wb = openpyxl.load_workbook(_EXCEL)
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {_EXCEL}")

    if _SHEET not in wb.sheetnames:
        raise ValueError(f"La hoja '{_SHEET}' no existe.")

    ws = wb[_SHEET]
    headers = [str(c.value).strip() if c.value else "" for c in ws[1]]
    try:
        col_tipo = headers.index("TipoPanel") + 1
    except ValueError:
        raise ValueError("La hoja no tiene columna 'TipoPanel'.")

    fila_borrar = None
    for row in ws.iter_rows(min_row=2):
        if str(row[col_tipo - 1].value or "").strip() == nombre:
            fila_borrar = row[0].row
            break

    if fila_borrar is None:
        return False

    ws.delete_rows(fila_borrar)
    wb.save(_EXCEL)

    try:
        cargar_catalogo_paneles.clear()
    except Exception:
        pass

    return True


def actualizar_panel_excel(nombre_original: str, datos: dict) -> str:
    """
    Actualiza los campos de un panel existente (por nombre_original).
    Si datos contiene 'TipoPanel' distinto, también renombra el panel.
    Retorna el nombre final guardado.
    """
    datos_completos = {"TipoPanel": nombre_original}
    datos_completos.update(datos)
    return guardar_panel_excel(datos_completos)


def obtener_panel_excel(nombre: str) -> dict:
    return cargar_catalogo_paneles().get(nombre, {})

def lista_paneles_excel() -> list:
    return sorted(cargar_catalogo_paneles().keys())

# Alias de compatibilidad con Dimensionamiento.py
cargar_catalogo_excel = cargar_catalogo_paneles
