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
import tempfile

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
    ok = _escribir_atomico(_ruta_historico(nombre_proyecto), historico)
    return ok, historico


def _escribir_atomico(ruta: str, historico: list) -> bool:
    """
    Escribe el JSON vía archivo temporal + os.replace: un corte a mitad de
    escritura nunca deja el histórico truncado (que cargar_historico trataría
    como vacío y el siguiente guardado sobrescribiría todo).
    """
    try:
        os.makedirs(_HIST_DIR, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=_HIST_DIR, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(historico, f, ensure_ascii=False, indent=1)
            os.replace(tmp, ruta)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        return True
    except OSError:
        return False


def eliminar_registro(nombre_proyecto: str, indice: int) -> tuple:
    """
    Elimina el registro `indice` (0-based) y reescribe el archivo.

    Retorna (ok: bool, historico: list). ok=False si el disco falló.
    """
    historico = cargar_historico(nombre_proyecto)
    if not (0 <= indice < len(historico)):
        return True, historico
    historico.pop(indice)
    ok = _escribir_atomico(_ruta_historico(nombre_proyecto), historico)
    return ok, historico
