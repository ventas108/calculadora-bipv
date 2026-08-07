# -*- coding: utf-8 -*-
"""
Persistencia de resultados clave de Producción (#89).

Streamlit ata session_state a la pestaña del navegador: si el usuario abre
Financiero o Presupuesto en OTRA pestaña (o recarga tras un reinicio de PM2),
los resultados de Producción desaparecen y esas páginas caen al modo manual
con defaults de prueba que no corresponden al proyecto real.

Solución: al terminar la simulación, Producción guarda los resultados clave
en datos/proyecto_actual.json (el mismo archivo que ya usa la página Proyecto);
Financiero y Presupuesto los restauran al inicio si faltan en session_state.
"""
import json
import os

_DIR_DATOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos")
RUTA_PROYECTO_ACTUAL = os.path.join(_DIR_DATOS, "proyecto_actual.json")

# Claves de session_state que se persisten al terminar Producción
CLAVES_RESULTADOS = (
    "E_ac_anual_kWh", "E_dc_anual_kWh", "PR_sistema", "Y_f_kWh_kWp",
    "P_stc_kW_sistema", "N_paneles_final", "panel_nombre_final", "eta_inversor",
)


def _leer_json() -> dict:
    if not os.path.exists(RUTA_PROYECTO_ACTUAL):
        return {}
    try:
        with open(RUTA_PROYECTO_ACTUAL, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def guardar_resultados_produccion(session_state) -> bool:
    """Fusiona los resultados de Producción dentro de proyecto_actual.json.

    Escritura atómica (tmp + os.replace) para no corromper el archivo que
    también escribe la página Proyecto. Devuelve False si no pudo guardar.
    """
    try:
        data = _leer_json()
        resultados = {}
        for k in CLAVES_RESULTADOS:
            v = session_state.get(k)
            if v is not None:
                # normalizar numpy → tipos nativos
                try:
                    import numpy as np
                    if isinstance(v, np.integer):
                        v = int(v)
                    elif isinstance(v, np.floating):
                        v = float(v)
                except ImportError:
                    pass
                resultados[k] = v
        if not resultados:
            return False
        data["resultados_produccion"] = resultados
        os.makedirs(_DIR_DATOS, exist_ok=True)
        tmp = RUTA_PROYECTO_ACTUAL + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, RUTA_PROYECTO_ACTUAL)
        return True
    except OSError:
        return False


def restaurar_resultados_produccion(session_state) -> bool:
    """Restaura los resultados guardados si faltan en session_state.

    Solo escribe claves AUSENTES (no pisa datos vivos de la sesión) y NUNCA
    marca produccion_ok=True: los resultados restaurados sirven para que
    Financiero/Presupuesto no caigan al modo manual, pero la cadena de
    invalidación (#64/#120) sigue mandando — si el usuario cambia de ciudad,
    la página Proyecto borra también este archivo vía session_state.

    Devuelve True si restauró al menos E_ac o P_stc (para mostrar el banner).
    """
    # Si la sesión ya tiene producción viva, no tocar nada.
    if session_state.get("produccion_ok"):
        return False
    resultados = _leer_json().get("resultados_produccion") or {}
    if not isinstance(resultados, dict) or not resultados:
        return False
    restauro_clave = False
    for k in CLAVES_RESULTADOS:
        v = resultados.get(k)
        if v is None:
            continue
        if session_state.get(k) in (None, 0, 0.0, ""):
            session_state[k] = v
            if k in ("E_ac_anual_kWh", "P_stc_kW_sistema", "N_paneles_final"):
                restauro_clave = True
    return restauro_clave


def limpiar_resultados_produccion() -> None:
    """Borra los resultados persistidos (al cambiar de ciudad/proyecto)."""
    try:
        data = _leer_json()
        if "resultados_produccion" in data:
            del data["resultados_produccion"]
            tmp = RUTA_PROYECTO_ACTUAL + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, RUTA_PROYECTO_ACTUAL)
    except OSError:
        pass
