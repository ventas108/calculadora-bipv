# -*- coding: utf-8 -*-
"""
Persistencia de resultados clave de Producción (#89) — POR USUARIO.

Streamlit ata session_state a la pestaña del navegador: si el usuario abre
Financiero o Presupuesto en OTRA pestaña (o recarga tras un reinicio de PM2),
los resultados de Producción desaparecen y esas páginas caen al modo manual
con defaults de prueba que no corresponden al proyecto real.

Diseño (auditoría de seguridad):
- Cada usuario logueado tiene SU PROPIO archivo en datos/persistencia/ —
  nunca se comparten resultados entre cuentas del mismo servidor.
- Los resultados guardan una huella (ciudad + coordenadas): si al restaurar
  la sesión ya tiene otra ciudad/coordenadas, NO se restauran (datos de otro
  proyecto).
- Escritura atómica con tmp único por proceso (sin carreras de os.replace).
"""
import hashlib
import json
import os

_DIR_DATOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos")
DIR_PERSISTENCIA = os.path.join(_DIR_DATOS, "persistencia")

# Claves de session_state que se persisten al terminar Producción
CLAVES_RESULTADOS = (
    "E_ac_anual_kWh", "E_dc_anual_kWh", "PR_sistema", "Y_f_kWh_kWp",
    "P_stc_kW_sistema", "N_paneles_final", "panel_nombre_final", "eta_inversor",
)

# Huella del proyecto: si cambia, los resultados guardados NO aplican
CLAVES_HUELLA = ("ciudad", "lat_proyecto", "lon_proyecto")

UMBRAL_COORD = 0.0001  # mismo umbral de invalidación que Páginas 1 y 2


def _slug_usuario(usuario: str) -> str:
    """Nombre de archivo estable y anónimo por cuenta (no expone el correo)."""
    return hashlib.sha256((usuario or "").strip().lower().encode()).hexdigest()[:12]


def ruta_datos_usuario(nombre_base: str, usuario: str) -> str:
    """Ruta de un archivo de persistencia PRIVADO del usuario logueado."""
    return os.path.join(DIR_PERSISTENCIA, f"{_slug_usuario(usuario)}__{nombre_base}")


def _escribir_json_atomico(ruta: str, data: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        import uuid
        tmp = f"{ruta}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp"  # único por escritura
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, ruta)
        return True
    except OSError:
        return False


def _leer_json(ruta: str) -> dict:
    if not os.path.exists(ruta):
        return {}
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _ruta_resultados(usuario: str) -> str:
    return ruta_datos_usuario("resultados_produccion.json", usuario)


def guardar_resultados_produccion(session_state, usuario: str) -> bool:
    """Guarda los resultados de Producción del usuario, con huella de proyecto."""
    if not usuario:
        return False
    resultados = {}
    for k in CLAVES_RESULTADOS:
        v = session_state.get(k)
        if v is None:
            continue
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
    huella = {k: session_state.get(k) for k in CLAVES_HUELLA
              if session_state.get(k) is not None}
    return _escribir_json_atomico(
        _ruta_resultados(usuario),
        {"resultados": resultados, "huella": huella},
    )


def _huella_coincide(huella: dict, session_state) -> bool:
    """False solo si la sesión tiene OTRO proyecto (ciudad/coords distintas)."""
    if not isinstance(huella, dict):
        return True
    ciudad_ss = session_state.get("ciudad")
    if ciudad_ss and huella.get("ciudad") and ciudad_ss != huella["ciudad"]:
        return False
    for k in ("lat_proyecto", "lon_proyecto"):
        v_ss, v_h = session_state.get(k), huella.get(k)
        if v_ss is not None and v_h is not None:
            try:
                if abs(float(v_ss) - float(v_h)) > UMBRAL_COORD:
                    return False
            except (TypeError, ValueError):
                pass
    return True


def restaurar_resultados_produccion(session_state, usuario: str) -> bool:
    """Restaura los resultados del usuario si faltan en session_state.

    - Solo escribe claves AUSENTES (no pisa datos vivos).
    - NUNCA marca produccion_ok=True.
    - No restaura si la sesión ya trabaja con otra ciudad/coordenadas.
    Devuelve True si restauró al menos E_ac o P_stc (para el banner).
    """
    if not usuario or session_state.get("produccion_ok"):
        return False
    data = _leer_json(_ruta_resultados(usuario))
    resultados = data.get("resultados") or {}
    if not isinstance(resultados, dict) or not resultados:
        return False
    if not _huella_coincide(data.get("huella"), session_state):
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


# ── Selección de equipos (panel + inversor) por usuario — tarea #225 ─────────

def _ruta_seleccion_equipos(usuario: str) -> str:
    return ruta_datos_usuario("seleccion_equipos.json", usuario)


def guardar_seleccion_equipos(usuario: str, panel: str, inversor: str) -> bool:
    """Persiste el panel e inversor elegidos para restaurarlos en nuevas sesiones."""
    if not usuario or not (panel or inversor):
        return False
    return _escribir_json_atomico(
        _ruta_seleccion_equipos(usuario),
        {"panel": str(panel or ""), "inversor": str(inversor or "")},
    )


def cargar_seleccion_equipos(usuario: str) -> dict:
    """Devuelve {"panel": str, "inversor": str} persistidos (o dict vacío)."""
    if not usuario:
        return {}
    data = _leer_json(_ruta_seleccion_equipos(usuario))
    return {
        "panel": str(data.get("panel") or ""),
        "inversor": str(data.get("inversor") or ""),
    }


def limpiar_resultados_produccion(usuario: str) -> None:
    """Borra los resultados persistidos (cambio de ciudad/coords/proyecto)."""
    if not usuario:
        return
    try:
        ruta = _ruta_resultados(usuario)
        if os.path.exists(ruta):
            os.remove(ruta)
    except OSError:
        pass
