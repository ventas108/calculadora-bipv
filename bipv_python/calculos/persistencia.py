"""
persistencia.py — Persistencia ligera del proyecto entre sesiones/pestañas
==========================================================================
Reúne dos mecanismos de persistencia a disco (JSON en ``datos/``) que permiten
que el usuario NO pierda su trabajo al recargar la página, abrir otra pestaña
del navegador o cuando PM2 reinicia el proceso:

1. ``proyecto_actual.json`` — mismo archivo que gestiona 🏠 Proyecto. Aquí
   solo se AÑADEN/actualizan claves puntuales (E_ac, kWp, N_paneles, consumo…)
   sin pisar el resto del contenido. Patrón "merge-update".

2. ``presupuesto_guardado.json`` — DataFrames editados del 💼 Presupuesto
   (Perfilería, Mano de Obra, Sistema FV, Inversor). Serializados como listas
   de registros para reconstruir el DataFrame al recargar.

TODAS las escrituras son ATÓMICAS (tmp + os.replace), igual que
``calculos/pagos.py`` — un reinicio de PM2 a mitad de escritura nunca deja un
JSON corrupto a medias.

Este módulo NO importa streamlit: es lógica pura, verificable con pruebas de
roundtrip (guardar → cargar) usando dicts que simulan session_state.
"""
from __future__ import annotations

import json
import os
from typing import Any

# ── Rutas de los archivos de persistencia ─────────────────────────────────────
_DIR_DATOS = os.path.join(os.path.dirname(__file__), "..", "datos")
PROYECTO_ACTUAL_FILE   = os.path.join(_DIR_DATOS, "proyecto_actual.json")
PRESUPUESTO_GUARDADO_FILE = os.path.join(_DIR_DATOS, "presupuesto_guardado.json")


# ── Escritura atómica genérica (tmp + os.replace, igual que pagos.py) ─────────
def _escribir_json_atomico(ruta: str, datos: Any) -> None:
    """Escribe ``datos`` como JSON de forma atómica: primero a un .tmp y luego
    os.replace() — nunca deja el archivo destino corrupto a medias."""
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ruta)


# ══════════════════════════════════════════════════════════════════════════════
# 1) proyecto_actual.json — merge-update de claves puntuales (#89, #94)
# ══════════════════════════════════════════════════════════════════════════════
def leer_proyecto_actual() -> dict:
    """Devuelve el contenido de proyecto_actual.json (o {} si no existe)."""
    if os.path.exists(PROYECTO_ACTUAL_FILE):
        try:
            with open(PROYECTO_ACTUAL_FILE, "r", encoding="utf-8") as f:
                datos = json.load(f)
            if isinstance(datos, dict):
                return datos
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def actualizar_proyecto_actual(nuevos: dict) -> dict:
    """Fusiona ``nuevos`` en proyecto_actual.json (sin pisar el resto de claves)
    y guarda de forma atómica. Devuelve el dict resultante ya en disco.

    Los valores None se omiten para no sobreescribir con vacío datos válidos.
    """
    actual = leer_proyecto_actual()
    for k, v in nuevos.items():
        if v is None:
            continue
        actual[k] = v
    _escribir_json_atomico(PROYECTO_ACTUAL_FILE, actual)
    return actual


# ══════════════════════════════════════════════════════════════════════════════
# 2) presupuesto_guardado.json — DataFrames editables del Presupuesto (#114)
# ══════════════════════════════════════════════════════════════════════════════
# Claves de las 4 secciones editables que se persisten. Coinciden con el estado
# session_state["df_sec_{key}"] de la página 8_💼_Presupuesto.py.
SECCIONES_PRESUPUESTO = ("perfileria", "mano_obra", "sistema_fv", "inversor")

# Columnas esperadas de cada DataFrame de sección.
_COLS_PRESUPUESTO = ["Activo", "Descripcion", "Ref", "Cantidad", "Unidad", "USD_un"]


def guardar_presupuesto_secciones(secciones: dict) -> None:
    """Persiste las secciones editables del Presupuesto de forma atómica.

    ``secciones`` es un dict {key: list_de_registros}, donde cada registro es un
    dict con las columnas de ``_COLS_PRESUPUESTO``. Se aceptan también valores
    que ya sean listas de dicts (p.ej. df.to_dict("records")).
    """
    payload: dict = {}
    for key in SECCIONES_PRESUPUESTO:
        if key not in secciones:
            continue
        registros = secciones[key]
        # Normalizar a lista de dicts serializables (sin objetos numpy/pandas)
        limpio = []
        for r in registros:
            fila = {
                "Activo":      bool(r.get("Activo", True)),
                "Descripcion": str(r.get("Descripcion", "") or ""),
                "Ref":         str(r.get("Ref", "") or ""),
                "Cantidad":    float(r.get("Cantidad", 0) or 0),
                "Unidad":      str(r.get("Unidad", "") or ""),
                "USD_un":      float(r.get("USD_un", 0) or 0),
            }
            limpio.append(fila)
        payload[key] = limpio
    _escribir_json_atomico(PRESUPUESTO_GUARDADO_FILE, payload)


def cargar_presupuesto_secciones() -> dict:
    """Carga las secciones editables del Presupuesto desde disco.

    Devuelve {key: list_de_registros} solo para las secciones presentes en el
    archivo. Si el archivo no existe o está corrupto, devuelve {}.
    """
    if not os.path.exists(PRESUPUESTO_GUARDADO_FILE):
        return {}
    try:
        with open(PRESUPUESTO_GUARDADO_FILE, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(datos, dict):
        return {}
    resultado: dict = {}
    for key in SECCIONES_PRESUPUESTO:
        registros = datos.get(key)
        if isinstance(registros, list):
            resultado[key] = registros
    return resultado


def existe_presupuesto_guardado() -> bool:
    """True si hay un presupuesto guardado en disco."""
    return os.path.exists(PRESUPUESTO_GUARDADO_FILE)


def eliminar_presupuesto_guardado() -> bool:
    """Elimina el archivo de presupuesto guardado (restaurar plantilla).
    Devuelve True si existía y se eliminó."""
    if os.path.exists(PRESUPUESTO_GUARDADO_FILE):
        os.remove(PRESUPUESTO_GUARDADO_FILE)
        return True
    return False
