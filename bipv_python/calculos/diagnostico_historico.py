"""
Histórico de diagnósticos por proyecto (tarea #98).

Persiste cada diagnóstico de la página 13 como un registro compacto en
datos/diagnosticos/<slug>.json, para poder graficar la evolución del sistema
(PR, PI, degradación, semáforo) a lo largo del tiempo y saber si mejora o
empeora entre visitas.

Formato del archivo: lista JSON de registros, orden cronológico de guardado.
Cada registro es un dict plano (solo tipos JSON-seguros).
"""

import json
import os

from calculos.proyectos_manager import nombre_a_slug

_HIST_DIR = os.path.join(os.path.dirname(__file__), "..", "datos", "diagnosticos")


def _ruta_historico(nombre_proyecto: str) -> str:
    slug = nombre_a_slug(nombre_proyecto or "diagnostico-general")
    return os.path.join(_HIST_DIR, f"{slug}.json")


def cargar_historico(nombre_proyecto: str) -> list:
    """Lista de registros del proyecto (vacía si no hay o el archivo está corrupto)."""
    ruta = _ruta_historico(nombre_proyecto)
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def guardar_registro(nombre_proyecto: str, registro: dict) -> tuple:
    """
    Anexa un registro al histórico del proyecto.

    Retorna (ok: bool, historico: list). ok=False si el disco falló — el
    llamador debe avisar al usuario (no silenciar, misma política que el
    caché del recurso solar).
    """
    historico = cargar_historico(nombre_proyecto)
    historico.append(registro)
    ruta = _ruta_historico(nombre_proyecto)
    try:
        os.makedirs(_HIST_DIR, exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(historico, f, ensure_ascii=False, indent=1)
        return True, historico
    except OSError:
        return False, historico


def eliminar_registro(nombre_proyecto: str, indice: int) -> list:
    """Elimina el registro `indice` (0-based) y reescribe el archivo."""
    historico = cargar_historico(nombre_proyecto)
    if 0 <= indice < len(historico):
        historico.pop(indice)
        try:
            os.makedirs(_HIST_DIR, exist_ok=True)
            with open(_ruta_historico(nombre_proyecto), "w", encoding="utf-8") as f:
                json.dump(historico, f, ensure_ascii=False, indent=1)
        except OSError:
            pass
    return historico
