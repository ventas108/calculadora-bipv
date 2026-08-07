"""
proyectos_manager.py — Gestión de múltiples proyectos BIPV
===========================================================
Permite guardar, cargar, listar y eliminar proyectos.
Cada proyecto se almacena como un archivo JSON en datos/proyectos/.

Uso:
    from calculos.proyectos_manager import (
        listar_proyectos, guardar_proyecto_actual,
        cargar_proyecto, eliminar_proyecto,
    )
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import uuid
import datetime
from typing import Any

import streamlit as st

# ── Directorio de proyectos ───────────────────────────────────────────────────
_DIR_BASE     = os.path.join(os.path.dirname(__file__), "..", "datos")
DIR_PROYECTOS = os.path.join(_DIR_BASE, "proyectos")

# ── Claves que NUNCA se serializan (no-JSON, muy grandes o irrelevantes) ──────
_CLAVES_EXCLUIR: set[str] = {
    # DataFrames pesados
    "tmy_df", "poa_df", "poa_efectiva_df", "df_mensual_produccion",
    "df_diagnostico_real", "df_fs_raw", "horizonte_df", "balance_mensual_df",
    "poa_directa_df", "poa_difusa_df",
    # Dicts con arrays numpy / resultados de cálculo pesados
    "res_produccion", "res_sombra", "res_mismatch_or",
    "cascada_mismatch", "bypass_result", "motor_optico_summary",
    "res_motor_optico",
    # Objetos de batería
    "bateria_dim",
    # Estado interno de Streamlit
    "proyecto_cargado_desde_disco",
    # Presupuesto: DataFrames editables grandes (se regeneran al abrir Presupuesto)
    "ss_materiales_df", "ss_mano_df", "ss_fv_df",
    "ss_inversor_df", "ss_blando_df", "ss_opex_df",
    "insumos_df", "insumos_template_df",
}

# Prefijos de claves temporales que se omiten siempre
_PREFIJOS_TEMP = ("_", "FormSubmitter:", "btn_")


# ── Encoder JSON tolerante a tipos NumPy/Pandas ───────────────────────────────
class _SafeEncoder(json.JSONEncoder):
    def default(self, obj: Any):
        # NumPy scalars
        try:
            import numpy as np
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.bool_):
                return bool(obj)
            if isinstance(obj, np.ndarray):
                # Arrays pequeños (ej: coordenadas) → lista; grandes → omitir
                if obj.size <= 100:
                    return obj.tolist()
                return None   # omitido por el caller
        except ImportError:
            pass
        # Pandas DataFrame / Series → omitir
        try:
            import pandas as pd
            if isinstance(obj, (pd.DataFrame, pd.Series)):
                return None
        except ImportError:
            pass
        # datetime
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return None   # omitir en lugar de lanzar error


def _es_serializable(v: Any) -> bool:
    """Devuelve True si el valor puede guardarse en JSON sin error."""
    try:
        import pandas as pd
        if isinstance(v, (pd.DataFrame, pd.Series)):
            return False
    except ImportError:
        pass
    try:
        import numpy as np
        if isinstance(v, np.ndarray) and v.size > 100:
            return False
    except ImportError:
        pass
    # Diccionarios con DataFrames anidados
    if isinstance(v, dict):
        try:
            json.dumps(v, cls=_SafeEncoder)
            return True
        except Exception:
            return False
    return True


# ── Slug de nombre de proyecto → nombre de archivo ────────────────────────────
def nombre_a_slug(nombre: str) -> str:
    """'Edificio Centro Bogotá' → 'edificio_centro_bogota'."""
    s = nombre.lower().strip()
    # Transliterar acentos básicos
    for src, dst in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),
                     ("ñ","n"),("ü","u"),("à","a"),("â","a"),("ê","e"),
                     ("î","i"),("ô","o"),("û","u")]:
        s = s.replace(src, dst)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s or "proyecto"


# ── Propiedad por usuario ─────────────────────────────────────────────────────
# Cada proyecto pertenece a la cuenta que lo guardó: el archivo se llama
# <hash12_del_correo>__<slug>.json (mismo esquema que datos/persistencia/).
# Los archivos "legacy" sin prefijo (anteriores al multiusuario) solo son
# visibles para administradores y se migran a su cuenta al volver a guardarlos.

def _hash_usuario(usuario: str) -> str:
    return hashlib.sha256((usuario or "").strip().lower().encode()).hexdigest()[:12]


def _usuario_sesion() -> str:
    return str(st.session_state.get("auth_email", "") or "")


def _es_admin() -> bool:
    try:
        from calculos.auth import usuario_actual
        u = usuario_actual(st)
        return bool(u and u.get("rol") == "admin")
    except Exception:
        return False


def _slug_valido(slug: str) -> bool:
    """Solo nombres de archivo planos — nunca rutas."""
    return bool(slug) and re.fullmatch(r"[a-z0-9_]+(?:__[a-z0-9_]+)?", slug) is not None


def _slug_autorizado(slug: str) -> bool:
    """El usuario solo toca sus propios archivos; legacy solo para admin."""
    if not _slug_valido(slug):
        return False
    if "__" in slug:
        return slug.split("__", 1)[0] == _hash_usuario(_usuario_sesion())
    return _es_admin()   # legacy sin prefijo


def _ruta_proyecto(slug: str) -> str:
    return os.path.join(DIR_PROYECTOS, f"{slug}.json")


# ── API pública ───────────────────────────────────────────────────────────────

def listar_proyectos() -> list[dict]:
    """
    Devuelve lista de dicts con metadata de proyectos guardados, ordenada
    por fecha de guardado descendente.
    Cada dict: {slug, nombre, guardado, ciudad, area_m2, e_ac_kWh, archivo}
    """
    os.makedirs(DIR_PROYECTOS, exist_ok=True)
    proyectos: list[dict] = []
    _mi_hash  = _hash_usuario(_usuario_sesion())
    _admin    = _es_admin()
    for fname in os.listdir(DIR_PROYECTOS):
        if not fname.endswith(".json"):
            continue
        _slug_f = fname[:-5]
        # Aislamiento por usuario: solo mis proyectos; legacy solo para admin
        if "__" in _slug_f:
            if _slug_f.split("__", 1)[0] != _mi_hash:
                continue
        elif not _admin:
            continue
        ruta = os.path.join(DIR_PROYECTOS, fname)
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
            meta = data.get("_meta", {})
            proyectos.append({
                "slug":     fname[:-5],
                "nombre":   meta.get("nombre", fname[:-5]),
                "guardado": meta.get("guardado", ""),
                "ciudad":   meta.get("ciudad", "—"),
                "area_m2":  meta.get("area_m2", 0.0),
                "e_ac_kWh": meta.get("e_ac_kWh", 0.0),
                "archivo":  ruta,
                "legacy":   "__" not in _slug_f,
            })
        except Exception:
            pass
    proyectos.sort(key=lambda x: x["guardado"], reverse=True)
    return proyectos


def guardar_proyecto_actual(nombre: str | None = None) -> str:
    """
    Serializa el session_state actual (claves seguras) a disco.
    Devuelve el slug del archivo guardado.
    """
    nombre = nombre or st.session_state.get("nombre_proyecto", "Proyecto BIPV")
    # Siempre con prefijo del propietario: nadie más lo verá ni podrá borrarlo
    slug   = f"{_hash_usuario(_usuario_sesion())}__{nombre_a_slug(nombre)}"
    os.makedirs(DIR_PROYECTOS, exist_ok=True)

    estado: dict = {}
    for k, v in st.session_state.items():
        # Omitir claves excluidas o temporales
        if k in _CLAVES_EXCLUIR:
            continue
        if any(k.startswith(p) for p in _PREFIJOS_TEMP):
            continue
        if not _es_serializable(v):
            continue
        # Intentar serializar — si falla, omitir silenciosamente
        try:
            json.dumps(v, cls=_SafeEncoder)
            estado[k] = v
        except Exception:
            pass

    # Normalizar tipos numpy a Python nativo antes de escribir
    estado_limpio = json.loads(json.dumps(estado, cls=_SafeEncoder))

    meta = {
        "nombre":   nombre,
        "propietario": _hash_usuario(_usuario_sesion()),
        "guardado": datetime.datetime.now().isoformat(timespec="seconds"),
        "ciudad":   st.session_state.get("tmy_ciudad",
                        st.session_state.get("ciudad", "—")),
        "area_m2":  float(st.session_state.get("area_fachada_m2", 0.0)),
        "e_ac_kWh": float(st.session_state.get("E_ac_anual_kWh", 0.0)),
    }

    payload = {"_meta": meta, "estado": estado_limpio}
    ruta = _ruta_proyecto(slug)
    # Escritura atómica: nunca dejar un JSON a medias si el proceso muere
    tmp = f"{ruta}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ruta)

    return slug


def cargar_proyecto(slug: str) -> str:
    """
    Carga un proyecto guardado en session_state.
    Las claves excluidas (DataFrames, results) quedan en None / no existen,
    forzando al usuario a re-ejecutar esos pasos.
    Devuelve el nombre del proyecto cargado.
    """
    if not _slug_autorizado(slug):
        raise PermissionError("Este proyecto no pertenece a tu cuenta.")
    ruta = _ruta_proyecto(slug)
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"Proyecto no encontrado: {ruta}")

    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)

    estado: dict = data.get("estado", {})
    meta:   dict = data.get("_meta", {})

    # Limpiar claves computadas que podrían estar desactualizadas tras la carga
    _claves_reset = {
        # Resultados de cómputo pesado — se invalidan para forzar re-ejecución
        # #127: recurso_solar_ok TAMBIÉN se resetea — tmy_df/poa_df nunca se
        # guardan en el JSON (DataFrames pesados); si el flag revive en True,
        # Producción intenta leer un tmy_df que no existe y falla en silencio.
        "recurso_solar_ok",
        "produccion_ok", "financiero_ok", "bypass_ok",
        "motor_optico_ok", "mismatch_ok", "balance_ok", "bateria_ok",
        # DataFrames — se limpian para evitar KeyError en páginas
        "df_mensual_produccion", "df_diagnostico_real", "df_fs_raw",
        "horizonte_df", "balance_mensual_df", "tmy_df", "poa_df",
        "res_produccion", "res_sombra", "bypass_result", "cascada_mismatch",
        "motor_optico_summary",
    }
    for k in _claves_reset:
        st.session_state.pop(k, None)

    # Marcar para que _cargar_proyecto() no sobreescriba al navegar de regreso
    st.session_state["proyecto_cargado_desde_disco"] = True

    # #89 — invalidar los resultados de Producción persistidos a disco: son del
    # proyecto ANTERIOR; si sobreviven, otra pestaña los "restauraría" aquí.
    try:
        from calculos.persistencia_resultados import limpiar_resultados_produccion
        limpiar_resultados_produccion(st.session_state.get("auth_email", ""))
    except Exception:
        pass

    # Cargar estado guardado (sobrescribe valores actuales)
    for k, v in estado.items():
        st.session_state[k] = v

    # #127 — CRÍTICO: volver a limpiar DESPUÉS de volcar el estado. El JSON
    # guardado contiene los flags *_ok (p.ej. recurso_solar_ok=True) y el bucle
    # anterior los revive, pero los DataFrames de los que dependen NO se
    # guardan. Sin esta segunda pasada, el banner de pasos pendientes no avisa
    # y Producción falla con un tmy_df inexistente.
    for k in _claves_reset:
        st.session_state.pop(k, None)

    # Nota: ☀️ Recurso Solar tiene auto-restore desde el caché de disco (#61) —
    # si las coordenadas del proyecto coinciden, se revalida al abrir la página
    # sin volver a descargar de PVGIS.

    return meta.get("nombre", slug)


def eliminar_proyecto(slug: str) -> bool:
    """Elimina el archivo de proyecto. Devuelve True si lo eliminó.

    Solo el propietario (o un admin, para archivos legacy) puede borrar.
    """
    if not _slug_autorizado(slug):
        return False
    ruta = _ruta_proyecto(slug)
    if os.path.exists(ruta):
        os.remove(ruta)
        return True
    return False
