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
        _p_ac_nom_kW = _f(r.get("Potencia AC nominal (kW)"))
        _p_dc_max_W  = _f(r.get("Potencia FV Max Recomendada (W)"))
        # P_ac_nom_W: columna directa > derivada de P_dc con factor 0.96 como fallback
        _p_ac_nom_W  = (_p_ac_nom_kW * 1000) if _p_ac_nom_kW else (
            _p_dc_max_W * 0.96 if _p_dc_max_W else None
        )
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
            "P_dc_max_W":        _p_dc_max_W,
            # ── Potencia AC nominal ───────────────────────────────────────────
            "P_ac_nom_kW":       _p_ac_nom_kW,   # desde columna "Potencia AC nominal (kW)"
            "P_ac_nom_W":        _p_ac_nom_W,    # alias en Watts (para Dimensionamiento.py)
            # ── Aliases para dimensionamiento.py y Dimensionamiento.py ───
            "Vmppt_activo_min":  _f(r.get("Tension Minima MPPT Activo (V)")),  # = V_mppt_activo
            "N_mppt":            _f(r.get("N Trackers")),                       # = n_trackers
            # ── Compatibilidad con baterías (#25) — columnas opcionales ──────
            "es_hibrido":       str(r.get("Inversor Híbrido (Si/No)", "")).strip().lower() == "si",
            "bat_voltaje_min":  _f(r.get("Voltaje Batería Min (V)")),
            "bat_voltaje_max":  _f(r.get("Voltaje Batería Max (V)")),
        }
    return inversores

cargar_catalogo_inv_excel = cargar_catalogo_inversores

def obtener_inversor_excel(nombre: str) -> dict:
    return cargar_catalogo_inversores().get(nombre, {})

def lista_inversores_excel() -> list:
    return sorted(cargar_catalogo_inversores().keys())


# ══════════════════════════════════════════════════════════════════════════════
# Escritura / edición / eliminación en el Excel
# ══════════════════════════════════════════════════════════════════════════════
# El archivo inversores_catalogo.xlsx tiene 2 filas de cabecera de título
# antes de la fila de encabezados de columna (header=2 en pd.read_excel →
# fila 3 de Excel en openpyxl).  Los datos empiezan en la fila 4.
_HEADER_ROW = 3   # 1-based row del encabezado de columnas en openpyxl
_DATA_START  = 4  # primera fila de datos

# Columna clave del catálogo de inversores
_KEY_COL = "Modelo"


def guardar_inversor_excel(datos: dict) -> str:
    """
    Agrega o actualiza un inversor en el Excel del catálogo.
    `datos` debe contener al menos la clave 'Modelo'.
    Retorna el nombre del inversor guardado e invalida el cache.
    """
    import openpyxl, datetime

    nombre = str(datos.get(_KEY_COL, "")).strip()
    if not nombre:
        raise ValueError("El campo 'Modelo' es obligatorio.")

    try:
        wb = openpyxl.load_workbook(_EXCEL)
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {_EXCEL}")

    if _SHEET not in wb.sheetnames:
        raise ValueError(f"La hoja '{_SHEET}' no existe en {_EXCEL}.")

    ws = wb[_SHEET]

    # Leer encabezados desde la fila de cabecera real (fila 3 del Excel)
    headers = [
        str(c.value).strip() if c.value else ""
        for c in ws[_HEADER_ROW]
    ]

    if _KEY_COL not in headers:
        raise ValueError(f"La hoja no tiene columna '{_KEY_COL}'.")

    col_key = headers.index(_KEY_COL) + 1  # 1-based

    # Buscar fila existente o agregar al final
    fila_destino = None
    for row in ws.iter_rows(min_row=_DATA_START):
        val = str(row[col_key - 1].value or "").strip()
        if val == nombre:
            fila_destino = row[0].row
            break
    if fila_destino is None:
        fila_destino = ws.max_row + 1

    # Escribir solo columnas que existen en el encabezado
    for col_nombre, valor in datos.items():
        if col_nombre in headers:
            col_idx = headers.index(col_nombre) + 1
            ws.cell(row=fila_destino, column=col_idx, value=valor)

    # Anotar fecha si existe la columna
    for meta_col in ("FechaIngreso", "Fecha_Ingreso", "Fecha"):
        if meta_col in headers:
            ws.cell(
                row=fila_destino,
                column=headers.index(meta_col) + 1,
                value=datetime.date.today().isoformat(),
            )
            break

    wb.save(_EXCEL)

    try:
        cargar_catalogo_inversores.clear()
    except Exception:
        pass

    return nombre


def eliminar_inversor_excel(nombre: str) -> bool:
    """
    Elimina la fila del inversor con Modelo == nombre.
    Retorna True si se eliminó, False si no se encontró.
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
    headers = [str(c.value).strip() if c.value else "" for c in ws[_HEADER_ROW]]

    if _KEY_COL not in headers:
        raise ValueError(f"La hoja no tiene columna '{_KEY_COL}'.")

    col_key = headers.index(_KEY_COL) + 1
    fila_borrar = None
    for row in ws.iter_rows(min_row=_DATA_START):
        if str(row[col_key - 1].value or "").strip() == nombre:
            fila_borrar = row[0].row
            break

    if fila_borrar is None:
        return False

    ws.delete_rows(fila_borrar)
    wb.save(_EXCEL)

    try:
        cargar_catalogo_inversores.clear()
    except Exception:
        pass

    return True


def actualizar_inversor_excel(nombre_original: str, datos: dict) -> str:
    """
    Actualiza los campos de un inversor existente (por nombre_original).
    Si datos contiene 'Modelo' distinto, también renombra la entrada.
    Retorna el nombre final guardado.
    """
    datos_completos = {_KEY_COL: nombre_original}
    datos_completos.update(datos)
    return guardar_inversor_excel(datos_completos)
