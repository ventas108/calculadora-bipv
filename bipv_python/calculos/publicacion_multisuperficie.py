"""Publicación única de la energía multi-superficie.

Spec ``05-perdidas-y-temperatura/publicacion-energia-multisuperficie``.

Financiero, Baterías, CO₂, Reporte y Unifilar leen la energía de Vista 3D
de las mismas claves (``E_ac_anual_kWh_multisup``, ``multisup_desglose``,
``poa_df_multisup``, ``area_total_multisup``, ``multisup_activo``). Esas
claves solo se escriben aquí, juntas y con su origen:

- ``simplificado``: η·PR por superficie (botón «Usar sistema multi-superficie»).
- ``bypass_csv``: bypass por superficie con el CSV de sombreado.
- ``fisico``: modelo SDM + bypass + buses de inversor adoptado.

Cada publicación valida primero y escribe después (todo o nada). Reemplazar
un origen distinto al vigente exige ``confirmar_reemplazo=True``.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, MutableMapping
from typing import Any

import numpy as np
import pandas as pd

ORIGEN_SIMPLIFICADO = "simplificado"
ORIGEN_BYPASS_CSV = "bypass_csv"
ORIGEN_FISICO = "fisico"
ORIGEN_DESCONOCIDO = "desconocido"
ORIGENES = (ORIGEN_SIMPLIFICADO, ORIGEN_BYPASS_CSV, ORIGEN_FISICO)

ETIQUETA_ORIGEN = {
    ORIGEN_SIMPLIFICADO: "simplificado (η·PR por superficie)",
    ORIGEN_BYPASS_CSV: "bypass por superficie con CSV de sombreado",
    ORIGEN_FISICO: "modelo físico SDM + bypass + inversores",
    ORIGEN_DESCONOCIDO: "origen desconocido (sesión anterior a esta versión)",
}

CLAVES_ENERGIA = (
    "E_ac_anual_kWh_multisup", "multisup_desglose", "poa_df_multisup",
    "area_total_multisup", "multisup_activo", "multisup_origen",
    # Spec 03/diseno-electrico-multisuperficie (fase A2): estado del diseño
    # eléctrico con el que se publicó (resumen_estado_electrico).
    "multisup_estado_electrico",
)
CLAVES_SOLO_FISICO = ("_multisup_proyecto_fisico", "multisup_perdida_bus_kWh")
CLAVES_PUBLICACION = CLAVES_ENERGIA + CLAVES_SOLO_FISICO

TOLERANCIA_ENERGIA_KWH = 0.1
TOLERANCIA_AREA_M2 = 0.1
_HORAS_ANIO = 8760
_CAMPOS_DESGLOSE = ("nombre", "tipo", "area_m2", "e_ac_kWh", "poa_kWh_m2")


def origen_vigente(session_state: Mapping[str, Any]) -> str | None:
    """Origen de la energía publicada; ``None`` si no hay publicación activa.

    Una sesión activa sin ``multisup_origen`` (anterior a esta Spec) se
    reporta como ``desconocido``.
    """
    if not session_state.get("multisup_activo", False):
        return None
    origen = session_state.get("multisup_origen")
    return origen if origen in ORIGENES else ORIGEN_DESCONOCIDO


def _finito(valor: Any, nombre: str) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{nombre} no es numérico: {valor!r}.") from None
    if not math.isfinite(numero):
        raise ValueError(f"{nombre} no es un número finito.")
    return numero


def _validar_desglose(desglose: Any) -> list[dict]:
    if not isinstance(desglose, list) or not desglose:
        raise ValueError("El desglose por superficie está vacío.")
    salida, nombres = [], set()
    for fila in desglose:
        if not isinstance(fila, Mapping):
            raise ValueError("Cada fila del desglose debe ser un diccionario.")
        faltantes = [c for c in _CAMPOS_DESGLOSE if c not in fila]
        if faltantes:
            raise ValueError(f"Fila del desglose incompleta; faltan: {', '.join(faltantes)}.")
        nombre = str(fila["nombre"])
        if nombre in nombres:
            raise ValueError(f"La superficie '{nombre}' aparece dos veces en el desglose.")
        nombres.add(nombre)
        area = _finito(fila["area_m2"], f"area_m2 de '{nombre}'")
        if area <= 0:
            raise ValueError(f"La superficie '{nombre}' tiene área no positiva.")
        _finito(fila["e_ac_kWh"], f"e_ac_kWh de '{nombre}'")
        _finito(fila["poa_kWh_m2"], f"poa_kWh_m2 de '{nombre}'")
        salida.append(dict(fila))
    return salida


def _validar_poa(poa: Any) -> pd.DataFrame:
    if not isinstance(poa, pd.DataFrame) or poa.empty or "poa_global" not in poa.columns:
        raise ValueError("Falta la POA ponderada (DataFrame con columna 'poa_global').")
    if len(poa) != _HORAS_ANIO:
        raise ValueError(f"La POA ponderada debe tener 8760 horas; tiene {len(poa)}.")
    if not np.isfinite(poa["poa_global"].to_numpy(dtype=float)).all():
        raise ValueError("La POA ponderada contiene valores no finitos.")
    return poa.copy()


def preparar_publicacion(
    *,
    origen: str,
    e_ac_total: float,
    desglose: list[dict],
    poa_ponderada: pd.DataFrame,
    area_total: float,
    proyecto_fisico: Mapping[str, Any] | None = None,
    estado_electrico: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Valida los invariantes y retorna las claves a publicar, sin escribir."""
    if origen not in ORIGENES:
        raise ValueError(f"El origen '{origen}' no pertenece a {ORIGENES}.")
    total = _finito(e_ac_total, "E_ac total")
    if total < 0:
        raise ValueError("E_ac total negativo.")
    area = _finito(area_total, "Área total")
    filas = _validar_desglose(desglose)
    suma_area = sum(float(f["area_m2"]) for f in filas)
    if abs(suma_area - area) > TOLERANCIA_AREA_M2:
        raise ValueError(
            f"El área del desglose ({suma_area:.1f} m²) no coincide con el área total "
            f"({area:.1f} m²)."
        )
    suma_energia = sum(float(f["e_ac_kWh"]) for f in filas)
    candidato: dict[str, Any] = {
        "E_ac_anual_kWh_multisup": total,
        "multisup_desglose": filas,
        "poa_df_multisup": _validar_poa(poa_ponderada),
        "area_total_multisup": area,
        "multisup_activo": True,
        "multisup_origen": origen,
    }
    if estado_electrico is not None:
        candidato["multisup_estado_electrico"] = dict(estado_electrico)
    if origen == ORIGEN_FISICO:
        if not isinstance(proyecto_fisico, Mapping):
            raise ValueError("El origen 'fisico' exige el proyecto físico calculado.")
        # El total físico es la suma de los buses de inversor: incluye el
        # recorte de inversores compartidos que el desglose por superficie no ve.
        candidato["multisup_perdida_bus_kWh"] = round(suma_energia - total, 1)
        candidato["_multisup_proyecto_fisico"] = dict(proyecto_fisico)
    else:
        if proyecto_fisico is not None:
            raise ValueError("Solo el origen 'fisico' publica un proyecto físico.")
        if abs(suma_energia - total) > TOLERANCIA_ENERGIA_KWH:
            raise ValueError(
                f"El desglose suma {suma_energia:,.1f} kWh y el total publicado es "
                f"{total:,.1f} kWh."
            )
    return candidato


def publicar_energia_multisuperficie(
    session_state: MutableMapping[str, Any],
    *,
    origen: str,
    e_ac_total: float,
    desglose: list[dict],
    poa_ponderada: pd.DataFrame,
    area_total: float,
    proyecto_fisico: Mapping[str, Any] | None = None,
    confirmar_reemplazo: bool = False,
    estado_electrico: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Publica la energía multi-superficie de forma atómica.

    Retorna ``{"publicado", "requiere_confirmacion", "origen_vigente"}``.
    Datos incoherentes ⇒ ``ValueError`` sin escribir nada. Si ya hay energía
    publicada de otro origen y no se confirmó el reemplazo, no escribe y
    pide confirmación.
    """
    candidato = preparar_publicacion(
        origen=origen, e_ac_total=e_ac_total, desglose=desglose,
        poa_ponderada=poa_ponderada, area_total=area_total,
        proyecto_fisico=proyecto_fisico, estado_electrico=estado_electrico,
    )
    vigente = origen_vigente(session_state)
    if vigente is not None and vigente != origen and not confirmar_reemplazo:
        return {"publicado": False, "requiere_confirmacion": True, "origen_vigente": vigente}
    for clave in CLAVES_SOLO_FISICO + ("multisup_estado_electrico",):
        if clave not in candidato:
            session_state.pop(clave, None)
    session_state.update(candidato)
    return {"publicado": True, "requiere_confirmacion": False, "origen_vigente": origen}


def retirar_energia_multisuperficie(session_state: MutableMapping[str, Any]) -> list[str]:
    """Retira toda la publicación (botón «✖ Desactivar»). Idempotente."""
    retiradas = [c for c in CLAVES_PUBLICACION if c in session_state]
    for clave in retiradas:
        session_state.pop(clave, None)
    return retiradas


def resultados_multisuperficie_a_guardar(session_state: Mapping[str, Any]) -> dict[str, Any]:
    """Resultados que viajan en el payload firmado al guardar el proyecto.

    El proyecto físico solo viaja si la energía publicada es de origen
    ``fisico``: un guardado nunca combina un proyecto físico con energía de
    otro origen.
    """
    resultados = {
        clave: session_state[clave]
        for clave in (
            "E_ac_anual_kWh_multisup", "area_total_multisup",
            "multisup_desglose", "poa_df_multisup", "multisup_origen",
            "multisup_estado_electrico",
        )
        if clave in session_state
    }
    if (
        session_state.get("multisup_origen") == ORIGEN_FISICO
        and session_state.get("_multisup_proyecto_fisico") is not None
    ):
        resultados["proyecto_fisico"] = session_state["_multisup_proyecto_fisico"]
        if "multisup_perdida_bus_kWh" in session_state:
            resultados["multisup_perdida_bus_kWh"] = session_state["multisup_perdida_bus_kWh"]
    return resultados


def aviso_estado_electrico(session_state: Mapping[str, Any]) -> tuple[str, str] | None:
    """``(nivel, texto)`` del diseño eléctrico con que se publicó la energía.

    ``nivel`` es ``"error"`` (🔴), ``"warning"`` (🟡) o ``"caption"`` (🟢)
    para que Vista 3D, Financiero, Baterías y CO₂ lo muestren igual.
    ``None`` si no hay publicación activa o no registró el estado (p. ej.
    una sesión anterior a la fase A2).
    """
    if not session_state.get("multisup_activo"):
        return None
    estado = session_state.get("multisup_estado_electrico")
    if not isinstance(estado, Mapping) or not estado.get("texto"):
        return None
    nivel = {"rojo": "error", "amarillo": "warning"}.get(estado.get("estado"), "caption")
    return nivel, f"Energía publicada con {estado['texto']}"
