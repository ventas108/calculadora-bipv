"""Payload canonico y firmas para persistencia multi-superficie.

Este modulo no conoce Streamlit ni escribe session_state. La restauracion
transaccional se construira encima de estas primitivas despues de validar el
contrato con pruebas focales.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from collections.abc import Mapping, MutableMapping
from typing import Any

import numpy as np
import pandas as pd

from calculos.panel_superficie import ORIGEN_PANEL_PROYECTO, ORIGENES_PANEL
from calculos.produccion_vigencia import fingerprint_mapping, huella_horaria

SCHEMA_VERSION = 1
PAYLOAD_KIND = "bipv_multisuperficie"
_HORAS_ANIO = 8760


class PayloadMultisuperficieError(ValueError):
    """Payload ausente, incompleto o no serializable de forma segura."""


@dataclass(frozen=True)
class ResultadoValidacion:
    ok: bool
    errores: tuple[str, ...] = ()
    firma_global: str | None = None

    def __bool__(self) -> bool:
        return self.ok


def _canonico(valor: Any) -> Any:
    """Convierte valores de calculo a tipos JSON deterministas."""
    if valor is None or isinstance(valor, (str, bool, int)):
        return valor
    if isinstance(valor, (float, np.floating)):
        valor = float(valor)
        if not np.isfinite(valor):
            raise PayloadMultisuperficieError("El payload contiene NaN o infinito.")
        return valor
    if isinstance(valor, np.integer):
        return int(valor)
    if isinstance(valor, np.ndarray):
        return {
            "__bipv_type__": "ndarray",
            "data": [_canonico(v) for v in valor.tolist()],
        }
    if isinstance(valor, pd.Timestamp):
        return valor.isoformat()
    if isinstance(valor, pd.DatetimeIndex):
        return [_canonico(v) for v in valor]
    if isinstance(valor, pd.DataFrame):
        return {
            "__bipv_type__": "dataframe",
            "columns": [str(c) for c in valor.columns],
            "index": [_canonico(v) for v in valor.index],
            "data": [[_canonico(v) for v in fila] for fila in valor.to_numpy().tolist()],
        }
    if isinstance(valor, pd.Series):
        return {
            "__bipv_type__": "series",
            "name": str(valor.name) if valor.name is not None else None,
            "index": [_canonico(v) for v in valor.index],
            "data": [_canonico(v) for v in valor.to_numpy().tolist()],
        }
    if isinstance(valor, Mapping):
        return {str(k): _canonico(valor[k]) for k in sorted(valor, key=str)}
    if isinstance(valor, (list, tuple)):
        return [_canonico(v) for v in valor]
    raise PayloadMultisuperficieError(
        f"Tipo no serializable en payload multi-superficie: {type(valor).__name__}."
    )


def _serializar(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        _canonico(payload), ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sin_firma_global(payload: Mapping[str, Any]) -> dict[str, Any]:
    copia = dict(payload)
    copia.pop("payload_signature", None)
    return copia


def _restaurar_dataframe(valor: Any) -> Any:
    return _restaurar_canonico(valor)


def _restaurar_canonico(valor: Any) -> Any:
    if isinstance(valor, Mapping):
        tipo = valor.get("__bipv_type__")
        if tipo == "ndarray":
            return np.asarray([_restaurar_canonico(v) for v in valor["data"]])
        if tipo == "dataframe":
            frame = pd.DataFrame(
                [[_restaurar_canonico(v) for v in fila] for fila in valor["data"]],
                columns=valor["columns"],
            )
            frame.index = pd.to_datetime(valor["index"], errors="raise")
            return frame
        if tipo == "series":
            serie = pd.Series(
                [_restaurar_canonico(v) for v in valor["data"]],
                name=valor.get("name"),
            )
            serie.index = pd.to_datetime(valor["index"], errors="raise")
            return serie
        return {str(k): _restaurar_canonico(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_restaurar_canonico(v) for v in valor]
    return valor


def firmar_payload_multisuperficie(payload: Mapping[str, Any]) -> str:
    """Firma el payload sin incluir su propio campo de firma."""
    if not isinstance(payload, Mapping):
        raise PayloadMultisuperficieError("El payload debe ser un mapping.")
    return hashlib.sha256(_serializar(_sin_firma_global(payload))).hexdigest()


def _tmy_fingerprint(tmy: Any) -> str:
    if not isinstance(tmy, pd.DataFrame) or "T2m" not in tmy.columns:
        raise PayloadMultisuperficieError("Falta TMY real con columna 'T2m'.")
    return huella_horaria(tmy.index, tmy["T2m"].to_numpy(dtype=float))


def _superficie_input(superficie: Mapping[str, Any]) -> dict[str, Any]:
    requeridos = (
        "uid", "nombre", "tipo", "area_m2", "tilt_deg", "azimuth_deg",
        "n_serie", "n_paralelo", "inversor_id", "p_shade", "firma_sombra",
    )
    faltantes = [campo for campo in requeridos if campo not in superficie]
    if faltantes:
        raise PayloadMultisuperficieError(
            f"Superficie incompleta; faltan: {', '.join(faltantes)}."
        )
    salida = {campo: superficie[campo] for campo in requeridos}
    for campo in (
        "n_serie", "n_paralelo", "inversor_id", "p_shade", "firma_sombra",
        "firma_poa", "estado_sombra", "cobertura_sombra", "puntos_analisis",
        "malla_horizonte", "motor_optico_vigente",
        # Spec 05/panel-por-superficie: panel de cada superficie. Ausentes en
        # proyectos anteriores, que cargan con el panel del proyecto.
        "panel_origen", "panel_nombre", "panel_ficha",
    ):
        if campo in superficie:
            salida[campo] = superficie[campo]
    origen = salida.get("panel_origen")
    if origen is not None and origen not in ORIGENES_PANEL:
        raise PayloadMultisuperficieError(
            f"Origen de panel desconocido en superficie '{salida['uid']}': {origen!r}."
        )
    return salida


def construir_payload_multisuperficie(
    session_state: Mapping[str, Any], resultados: Mapping[str, Any]
) -> dict[str, Any]:
    """Construye el payload canonico sin mutar el estado recibido."""
    if not session_state.get("multisup_activo", False):
        raise PayloadMultisuperficieError(
            "No se puede persistir payload fisico sin multisup_activo=True."
        )
    superficies = [
        _superficie_input(s)
        for s in (session_state.get("superficies_bipv") or [])
        if s.get("activa", True)
    ]
    if not superficies:
        raise PayloadMultisuperficieError("No hay superficies activas para persistir.")
    tmy = session_state.get("tmy_df")
    tmy_fingerprint = _tmy_fingerprint(tmy)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "payload_kind": PAYLOAD_KIND,
        "inputs": {
            "project_identity": {
                "ciudad": session_state.get("ciudad"),
                "lat_proyecto": session_state.get("lat_proyecto"),
                "lon_proyecto": session_state.get("lon_proyecto"),
                "alt_proyecto": session_state.get("alt_proyecto"),
            },
            "tmy": {
                "provider": session_state.get("tmy_provider") or session_state.get("fuente_tmy"),
                "tmy_fingerprint": tmy_fingerprint,
                "index": [_canonico(v) for v in tmy.index],
            },
            "surfaces": superficies,
            "electrical": {
                "panel": session_state.get("panel_dict"),
                "inversores": session_state.get("multisup_inversores"),
                "asignaciones": {
                    str(s["uid"]): s.get("inversor_id") for s in superficies
                },
            },
        },
        "results": resultados,
        "validity": {
            "tmy_fingerprint": tmy_fingerprint,
            "firma_sombra": {
                str(s["uid"]): s.get("firma_sombra") for s in superficies
            },
            "firma_poa": {
                str(s["uid"]): s.get("firma_poa") for s in superficies
            },
        },
        "provider_metadata": {
            "tmy_provider": session_state.get("tmy_provider") or session_state.get("fuente_tmy"),
            "shadow_provider": session_state.get("proveedor_sombra"),
            "poa_provider": session_state.get("proveedor_poa", "pvlib"),
        },
    }
    payload["payload_signature"] = firmar_payload_multisuperficie(payload)
    return _canonico(payload)


def _panel_canonico(superficie: Mapping[str, Any]) -> Any:
    origen = superficie.get("panel_origen") or ORIGEN_PANEL_PROYECTO
    if origen == ORIGEN_PANEL_PROYECTO:
        return ORIGEN_PANEL_PROYECTO
    return _canonico({
        "panel_nombre": superficie.get("panel_nombre"),
        "panel_ficha": superficie.get("panel_ficha"),
    })


def _comparar_contexto(payload: Mapping[str, Any], contexto: Mapping[str, Any]) -> list[str]:
    errores: list[str] = []
    entradas = payload["inputs"]
    tmy_actual = contexto.get("tmy_df")
    if tmy_actual is not None:
        try:
            esperado = entradas["tmy"]["tmy_fingerprint"]
            if _tmy_fingerprint(tmy_actual) != esperado:
                errores.append("TMY diferente al firmado.")
        except (KeyError, TypeError, ValueError, PayloadMultisuperficieError):
            errores.append("TMY actual no es valido para verificar el payload.")
    superficies_actuales = contexto.get("superficies_bipv")
    if superficies_actuales is not None:
        esperadas = {str(s["uid"]): s for s in entradas["surfaces"]}
        actuales = {
            str(s.get("uid")): s for s in superficies_actuales if s.get("activa", True)
        }
        if set(esperadas) != set(actuales):
            errores.append("Las superficies activas no coinciden con el payload.")
        for uid in esperadas.keys() & actuales.keys():
            for campo in ("area_m2", "tilt_deg", "azimuth_deg"):
                if actuales[uid].get(campo) != esperadas[uid].get(campo):
                    errores.append(f"Geometria diferente en superficie '{uid}'.")
                    break
            for campo in ("firma_sombra", "firma_poa", "inversor_id", "n_serie", "n_paralelo"):
                if campo in esperadas[uid] and actuales[uid].get(campo) != esperadas[uid].get(campo):
                    errores.append(f"{campo} diferente en superficie '{uid}'.")
            if _panel_canonico(actuales[uid]) != _panel_canonico(esperadas[uid]):
                errores.append(f"Panel diferente en superficie '{uid}'.")
        # El panel del proyecto solo importa si alguna superficie lo sigue.
        usa_panel_proyecto = any(
            (s.get("panel_origen") or ORIGEN_PANEL_PROYECTO) == ORIGEN_PANEL_PROYECTO
            for s in entradas["surfaces"]
        )
        panel_actual = contexto.get("panel_dict")
        panel_guardado = entradas["electrical"].get("panel")
        if (
            usa_panel_proyecto and panel_actual is not None
            and _canonico(panel_actual) != _canonico(panel_guardado)
        ):
            errores.append("Panel diferente al firmado.")
        inversores_actuales = contexto.get("multisup_inversores")
        if inversores_actuales is not None and _canonico(inversores_actuales) != _canonico(entradas["electrical"].get("inversores")):
            errores.append("Configuracion de inversores diferente al firmado.")
    return errores


def validar_payload_multisuperficie(
    payload: Mapping[str, Any], contexto_actual: Mapping[str, Any] | None = None
) -> ResultadoValidacion:
    """Valida estructura, firma global y, si existe, contexto actual."""
    errores: list[str] = []
    if not isinstance(payload, Mapping):
        return ResultadoValidacion(False, ("El payload no es un mapping.",))
    if payload.get("schema_version") != SCHEMA_VERSION:
        errores.append("Version de schema no soportada.")
    if payload.get("payload_kind") != PAYLOAD_KIND:
        errores.append("Tipo de payload no soportado.")
    for campo in ("inputs", "results", "validity", "provider_metadata", "payload_signature"):
        if campo not in payload:
            errores.append(f"Falta campo obligatorio '{campo}'.")
    firma = payload.get("payload_signature")
    if not errores and firma != firmar_payload_multisuperficie(payload):
        errores.append("Firma global alterada o invalida.")
    if not errores:
        try:
            entradas = payload["inputs"]
            if not entradas["surfaces"] or not entradas["tmy"]["tmy_fingerprint"]:
                errores.append("Payload incompleto: faltan superficies o TMY firmado.")
            for superficie in entradas["surfaces"]:
                _superficie_input(superficie)
            uids_superficies = {str(s["uid"]) for s in entradas["surfaces"]}
            asignaciones = entradas["electrical"]["asignaciones"]
            if set(asignaciones) != uids_superficies:
                errores.append(
                    "Las asignaciones de inversor no coinciden con las superficies del payload."
                )
            ids_inversores = {
                str(i.get("inversor_id"))
                for i in (entradas["electrical"].get("inversores") or [])
            }
            for superficie in entradas["surfaces"]:
                inv_id = str(superficie.get("inversor_id"))
                if inv_id not in ids_inversores:
                    errores.append(
                        f"Inversor '{inv_id}' inexistente para superficie "
                        f"'{superficie.get('uid')}'."
                    )
        except (KeyError, TypeError, PayloadMultisuperficieError) as exc:
            errores.append(f"Payload incompleto: {exc}")
    if not errores and contexto_actual is not None:
        errores.extend(_comparar_contexto(payload, contexto_actual))
    return ResultadoValidacion(not errores, tuple(errores), firma if not errores else None)


def restaurar_multisuperficie(
    payload: Mapping[str, Any],
    session_state: MutableMapping[str, Any],
    contexto_actual: Mapping[str, Any] | None = None,
) -> ResultadoValidacion:
    """Valida y publica el estado multi-superficie de forma todo-o-nada.

    ``results.session_state`` es el unico bloque de resultados que puede
    publicar claves; solo acepta nombres ``multisup_*``. El candidato se
    construye completamente antes de tocar el mapping recibido.
    """
    validacion = validar_payload_multisuperficie(payload, contexto_actual)
    if not validacion:
        return validacion
    try:
        entradas = payload["inputs"]
        superficies = []
        for superficie in entradas["surfaces"]:
            restaurada = _restaurar_canonico(superficie)
            restaurada["activa"] = True
            restaurada["p_shade"] = np.asarray(restaurada["p_shade"], dtype=float)
            superficies.append(restaurada)
        inversores = _restaurar_canonico(entradas["electrical"]["inversores"])
        resultados = payload["results"].get("session_state", {})
        if not isinstance(resultados, Mapping):
            return ResultadoValidacion(
                False, ("results.session_state debe ser un mapping.",)
            )
        claves_resultado_permitidas = {
            "E_ac_anual_kWh_multisup", "area_total_multisup",
            "multisup_desglose", "poa_df_multisup",
            "multisup_origen", "multisup_perdida_bus_kWh",
        }
        resultados_permitidos = {
            str(clave): (
                _restaurar_dataframe(valor)
                if str(clave) == "poa_df_multisup"
                else _canonico(valor)
            )
            for clave, valor in resultados.items()
            if str(clave) in claves_resultado_permitidas
        }
        candidato = {
            "superficies_bipv": superficies,
            "multisup_inversores": inversores,
            "multisup_activo": True,
            **resultados_permitidos,
        }
        if "proyecto_fisico" in resultados:
            candidato["_multisup_proyecto_fisico"] = _restaurar_canonico(
                resultados["proyecto_fisico"]
            )
            # Proyectos guardados antes de multisup_origen: un proyecto
            # físico en el payload solo pudo venir de «Adoptar cálculo físico».
            candidato["multisup_origen"] = "fisico"
        elif candidato.get("multisup_origen") == "fisico":
            return ResultadoValidacion(
                False, ("El payload declara origen 'fisico' sin proyecto físico.",)
            )
    except (KeyError, TypeError, ValueError, PayloadMultisuperficieError) as exc:
        return ResultadoValidacion(False, (f"No se pudo preparar restauracion: {exc}",))

    # Todas las conversiones y validaciones terminaron: una sola publicación.
    session_state.update(candidato)
    return validacion


# Re-export the existing helper used by callers that need a stable fingerprint.
__all__ = [
    "SCHEMA_VERSION", "PAYLOAD_KIND", "PayloadMultisuperficieError",
    "ResultadoValidacion", "construir_payload_multisuperficie",
    "firmar_payload_multisuperficie", "validar_payload_multisuperficie",
    "restaurar_multisuperficie",
    "fingerprint_mapping",
]
