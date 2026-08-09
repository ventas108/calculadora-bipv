"""Definición trazable de escenarios para la Fase 4 de comparación.

Este módulo solo define escenarios y sus invariantes. No calcula POA,
energía, pérdidas ni recuperación: esos cálculos pertenecen a la siguiente
etapa y deben consumir este contrato sin cambiar sus supuestos.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any
from collections.abc import Mapping

import pandas as pd


SCENARIO_SCHEMA_VERSION = "bipv.scenarios.v1"
BASE_SCHEMA_VERSION = "bipv.comparison-base.v1"
SCENARIO_IDS = ("referencia", "actual", "optimizada")
BASE_COMPONENTS = (
    "ubicacion",
    "tmy",
    "timestamps_utc",
    "poa_base",
    "fachadas_y_puntos",
    "panel",
    "configuracion_electrica",
    "temperatura_y_modelo_optico",
    "agregacion",
)


def _canonico(value: Any) -> Any:
    """Convierte valores de sesión a una representación hashable y estable."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        return round(value, 12)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {
            str(key): _canonico(val)
            for key, val in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonico(item) for item in value]
    try:
        return _canonico(value.item())
    except (AttributeError, TypeError, ValueError):
        return str(value)


def _huella(value: Any) -> str:
    payload = json.dumps(
        _canonico(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _huella_dataframe(frame: Any) -> str | None:
    if not isinstance(frame, pd.DataFrame):
        return None
    work = frame.copy()
    if isinstance(work.index, pd.DatetimeIndex) and work.index.tz is not None:
        work.index = work.index.tz_convert("UTC")
    try:
        raw = pd.util.hash_pandas_object(work, index=True).values.tobytes()
        metadata = {
            "columns": [str(column) for column in work.columns],
            "dtypes": [str(dtype) for dtype in work.dtypes],
            "rows": len(work),
            "values_hash": hashlib.sha256(raw).hexdigest(),
        }
        return _huella(metadata)
    except (TypeError, ValueError):
        return None


def _timestamps_utc(frame: Any) -> dict[str, Any]:
    if not isinstance(frame, pd.DataFrame) or not isinstance(
        frame.index, pd.DatetimeIndex
    ):
        return {"valido": False, "motivo": "Se requiere un DatetimeIndex."}
    if frame.index.tz is None:
        return {"valido": False, "motivo": "El índice horario no tiene zona horaria."}
    idx = frame.index.tz_convert("UTC")
    valores = [stamp.isoformat() for stamp in idx]
    return {
        "valido": True,
        "zona_horaria": "UTC",
        "n": len(idx),
        "inicio": valores[0] if valores else None,
        "fin": valores[-1] if valores else None,
        "huella": _huella(valores),
    }


def _buscar_columna(frame: pd.DataFrame, aliases: tuple[str, ...]) -> str | None:
    normalizadas = {
        "".join(char for char in str(column).lower() if char.isalnum()): column
        for column in frame.columns
    }
    for alias in aliases:
        encontrada = normalizadas.get(
            "".join(char for char in alias.lower() if char.isalnum())
        )
        if encontrada is not None:
            return encontrada
    return None


def _extraer_puntos(frame: Any) -> list[dict[str, Any]]:
    """Extrae solo identidad de fachada/punto y coordenadas disponibles."""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return []
    col_punto = _buscar_columna(frame, ("Punto", "point", "nombre"))
    if col_punto is None:
        # Variantes de encabezado como "Punto de análisis" o "point_id";
        # exigir sufijo conocido para no capturar coordenadas ("Punto X").
        _sufijos_ok = ("", "deanalisis", "deanálisis", "analisis", "análisis", "id")
        for column in frame.columns:
            normalizada = "".join(
                char for char in str(column).lower() if char.isalnum()
            )
            for prefijo in ("punto", "point"):
                if normalizada.startswith(prefijo) and normalizada[len(prefijo):] in _sufijos_ok:
                    col_punto = column
                    break
            if col_punto is not None:
                break
    col_fachada = _buscar_columna(
        frame, ("Fachada", "fachada", "facade", "obstaculo", "obstacle")
    )
    if col_fachada is None:
        return []
    col_fila = _buscar_columna(frame, ("fila", "row"))
    if col_punto is None:
        # El CSV no trae columna de punto explícita: derivar una identidad
        # determinista (fila si existe; si no, la propia fachada). Congelado
        # y verificación en vivo usan esta misma función, así que la
        # comparación sigue siendo consistente.
        col_punto = col_fila or col_fachada
    columnas_coord = {
        "x_m": _buscar_columna(frame, ("x (m)", "x_m", "x")),
        "y_m": _buscar_columna(frame, ("y (m)", "y_m", "y")),
        "z_m": _buscar_columna(frame, ("z (m)", "z_m", "z")),
    }
    registros = []
    for _, row in frame.iterrows():
        registro = {
            "punto": _canonico(row[col_punto]),
            "fachada": _canonico(row[col_fachada]),
        }
        for salida, columna in columnas_coord.items():
            if columna is not None:
                registro[salida] = _canonico(row[columna])
        registros.append(registro)
    return sorted(
        {
            json.dumps(registro, ensure_ascii=False, sort_keys=True): registro
            for registro in registros
        }.values(),
        key=lambda registro: json.dumps(registro, sort_keys=True),
    )


def _primer_valor(state: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = state.get(key)
        if value is not None and value != "":
            return value
    return None


def capturar_base_comparacion(state: Mapping[str, Any]) -> dict[str, Any]:
    """Captura la base efectiva de comparación a partir del estado actual.

    La función no inventa defaults: si una entrada necesaria no está disponible,
    la base queda marcada como incompleta y no puede usarse para comparar.
    """
    tmy = state.get("tmy_df")
    poa = state.get("poa_df")
    timestamps = _timestamps_utc(tmy)

    lat = _primer_valor(state, "_solar_lat_guardada", "lat_proyecto")
    lon = _primer_valor(state, "_solar_lon_guardada", "lon_proyecto")
    alt = _primer_valor(state, "_solar_alt_guardada", "alt_proyecto")
    ubicacion_valor = {
        "latitud": lat,
        "longitud": lon,
        "altitud_m": alt,
        "ciudad": state.get("tmy_ciudad", state.get("ciudad")),
    }

    puntos = _extraer_puntos(state.get("sk_puntos_df"))
    if not puntos:
        puntos = _extraer_puntos(state.get("df_fs_raw"))
    df_fs = state.get("df_fs_raw")
    if isinstance(df_fs, pd.DataFrame) and not puntos:
        puntos = _extraer_puntos(df_fs)
    fachadas_y_puntos = {
        "registros": puntos,
        "fuente_identidad": (
            "sk_puntos_df" if state.get("sk_puntos_df") is not None else "df_fs_raw"
        ),
    }

    panel = state.get("panel_dict")
    panel_nombre = _primer_valor(state, "panel_nombre_final", "panel_nombre_dim")
    inversor = state.get("inversor_dict_dim")
    inversor_nombre = state.get("inversor_nombre_dim")
    n_paneles = _primer_valor(state, "N_paneles_final", "N_paneles_dim")
    configuracion_electrica = {
        "panel_nombre": panel_nombre,
        "inversor_nombre": inversor_nombre,
        "N_paneles": n_paneles,
        # N_serie se escribe al cargar un inversor compatible; en una sesión
        # nueva puede no existir aún — usar el N del bloque bypass como
        # respaldo (es el que realmente se simula).
        "N_serie": _primer_valor(
            state, "N_serie", "bypass_n_series", "bypass_n_series_usado"
        ),
        # Preferir el valor persistido como resultado; el widget de
        # Dimensionamiento nace con valor 1, así que 1 es el respaldo fiel.
        # El widget vivo manda; el resultado persistido es solo respaldo
        # para sesiones restauradas donde el widget aún no se renderizó.
        "N_strings_tracker": _primer_valor(state, "N_str_tr", "N_str_tr_usado")
        or 1,
        "eta_inversor": state.get("eta_inversor"),
    }

    optical_keys = (
        "motor_optico_b0",
        "motor_optico_tau",
        "motor_optico_k_bipv",
        "motor_optico_noct",
        "motor_optico_coef_temp",
        "motor_optico_f_iam_dif",
        "motor_optico_k_soil_vert",
    )
    optical_parameters = {key: state.get(key) for key in optical_keys}
    # Preferir el flag persistido como resultado al ejecutar el Motor Óptico;
    # las keys de widget (mo_soiling_custom, mo_soil_*) desaparecen tras F5.
    _soiling_custom = _primer_valor(
        state, "motor_optico_soiling_custom", "mo_soiling_custom"
    )
    if _soiling_custom is None and state.get("motor_optico_ok"):
        # Motor ejecutado sin flag registrado → se aplicó el soiling
        # estacional estándar (custom=False).
        _soiling_custom = False
    optical_parameters["soiling_personalizado"] = _soiling_custom
    if _soiling_custom:
        _soiling_config = state.get("motor_optico_soiling_config")
        if isinstance(_soiling_config, dict) and _soiling_config:
            optical_parameters["soiling_mensual"] = {
                f"mes_{month}": _soiling_config.get(month)
                for month in range(1, 13)
            }
        else:
            optical_parameters["soiling_mensual"] = {
                f"mes_{month}": state.get(f"mo_soil_{month - 1}")
                for month in range(1, 13)
            }
    optical = {
        "modelo_optico": "cascada_optica",
        "modelo_temperatura": "temperatura_celda_noct",
        "fuente_temperatura_ambiente": "tmy_df.T2m",
        "ejecutado": bool(state.get("motor_optico_ok")),
        "parametros": optical_parameters,
    }

    componentes = {
        "ubicacion": {
            "valor": ubicacion_valor,
            "huella": _huella(ubicacion_valor),
        },
        "tmy": {
            "valor": {
                "ciudad": state.get("tmy_ciudad", state.get("ciudad")),
                "huella": _huella_dataframe(tmy),
                "columnas": [str(column) for column in tmy.columns]
                if isinstance(tmy, pd.DataFrame)
                else [],
            },
            "huella": _huella(
                {
                    "tmy": _huella_dataframe(tmy),
                    "timestamps": timestamps.get("huella"),
                }
            ),
        },
        "timestamps_utc": {
            "valor": timestamps,
            "huella": _huella(timestamps),
        },
        "poa_base": {
            "valor": {
                "huella": _huella_dataframe(poa),
                "fachada_azimuth": state.get("azimuth_fachada"),
                "fachada_tilt": state.get("tilt_fachada"),
            },
            "huella": _huella(
                {
                    "poa": _huella_dataframe(poa),
                    "azimuth": state.get("azimuth_fachada"),
                    "tilt": state.get("tilt_fachada"),
                }
            ),
        },
        "fachadas_y_puntos": {
            "valor": fachadas_y_puntos,
            "huella": _huella(fachadas_y_puntos),
        },
        "panel": {
            "valor": {"nombre": panel_nombre, "ficha": panel},
            "huella": _huella({"nombre": panel_nombre, "ficha": panel}),
        },
        "configuracion_electrica": {
            "valor": {
                "configuracion": configuracion_electrica,
                "ficha_inversor": inversor,
            },
            "huella": _huella(
                {
                    "configuracion": configuracion_electrica,
                    "ficha_inversor": inversor,
                }
            ),
        },
        "temperatura_y_modelo_optico": {
            "valor": optical,
            "huella": _huella(optical),
        },
        "agregacion": {
            "valor": {
                "horaria": "8760 registros UTC; suma directa de cada hora",
                "mensual": "mes calendario UTC; suma horaria; sin interpolación",
                "anual": "suma directa de las 8760 horas; no reconstruir desde promedios",
                "poa_ponderada": "sum(metrica × POA) / sum(POA)",
            },
            "huella": _huella(
                {
                    "horaria": "8760 registros UTC; suma directa de cada hora",
                    "mensual": "mes calendario UTC; suma horaria; sin interpolación",
                    "anual": "suma directa de las 8760 horas; no reconstruir desde promedios",
                    "poa_ponderada": "sum(metrica × POA) / sum(POA)",
                }
            ),
        },
    }

    missing = []
    if lat is None or lon is None or alt is None:
        missing.append("ubicación completa (latitud, longitud y altitud)")
    if not isinstance(tmy, pd.DataFrame):
        missing.append("TMY")
    if not timestamps.get("valido") or timestamps.get("n") != 8760:
        missing.append("timestamps UTC horarios completos (8760)")
    if not isinstance(poa, pd.DataFrame):
        missing.append("POA base")
    if not puntos:
        _detalles_fuentes = []
        for nombre_fuente in ("sk_puntos_df", "df_fs_raw"):
            frame_fuente = state.get(nombre_fuente)
            if isinstance(frame_fuente, pd.DataFrame):
                _detalles_fuentes.append(
                    f"{nombre_fuente} con columnas: "
                    + ", ".join(str(c) for c in frame_fuente.columns)
                )
        detalle = (
            " (revisadas: " + "; ".join(_detalles_fuentes) + ")"
            if _detalles_fuentes
            else " (no hay CSV de sombreado cargado ni puntos de SketchUp en la sesión)"
        )
        missing.append("fachadas y puntos de análisis" + detalle)
    if panel is None or panel_nombre is None:
        missing.append("panel seleccionado")
    if inversor is None or inversor_nombre is None:
        missing.append("inversor seleccionado")
    _elec_faltan = [
        key for key, value in configuracion_electrica.items() if value is None
    ]
    if _elec_faltan:
        missing.append(
            "configuración eléctrica completa (faltan: "
            + ", ".join(_elec_faltan)
            + ")"
        )
    optical_missing = [
        key for key, value in optical_parameters.items()
        if value is None
    ]
    # Los parámetros se guardan al ejecutar Motor Óptico; no se usan defaults.
    if not optical["ejecutado"]:
        missing.append("Motor Óptico ejecutado con parámetros congelados")
    elif optical_missing:
        missing.append(
            "parámetros completos del Motor Óptico (faltan: "
            + ", ".join(optical_missing)
            + ")"
        )
    base_id = _huella(
        {component: data["huella"] for component, data in componentes.items()}
    )
    return {
        "schema_version": BASE_SCHEMA_VERSION,
        "lista_para_comparar": not missing,
        "faltantes": missing,
        "base_id": base_id,
        "componentes": componentes,
    }


def validar_base_comparacion(base: dict[str, Any]) -> None:
    """Falla si la base no está completa o si su huella fue alterada."""
    if base.get("schema_version") != BASE_SCHEMA_VERSION:
        raise ValueError("Versión de contrato de base de comparación inválida.")
    componentes = base.get("componentes", {})
    if set(componentes) != set(BASE_COMPONENTS):
        raise ValueError("La base no contiene todos los componentes obligatorios.")
    faltantes = base.get("faltantes", [])
    if faltantes or base.get("lista_para_comparar") is not True:
        raise ValueError("Base de comparación incompleta: " + "; ".join(faltantes))
    esperado = _huella(
        {component: componentes[component]["huella"] for component in BASE_COMPONENTS}
    )
    if base.get("base_id") != esperado:
        raise ValueError("La huella de la base de comparación no coincide.")


def comparar_bases(base_referencia: dict[str, Any], base_candidata: dict[str, Any]) -> None:
    """Garantiza que dos escenarios usan exactamente una misma base."""
    validar_base_comparacion(base_referencia)
    validar_base_comparacion(base_candidata)
    if base_referencia["base_id"] != base_candidata["base_id"]:
        diferencias = [
            component
            for component in BASE_COMPONENTS
            if base_referencia["componentes"][component]["huella"]
            != base_candidata["componentes"][component]["huella"]
        ]
        raise ValueError(
            "Los escenarios no comparten la misma base; difieren en: "
            + ", ".join(diferencias)
        )


def construir_definicion_escenarios(
    *,
    nombre_proyecto: str,
    fuente_horizonte: bool,
    fuente_sketchup: bool,
    tipo_optimizacion: str = "paneles",
    panel_nombre: str | None = None,
    inversor_nombre: str | None = None,
) -> dict[str, Any]:
    """Construye el contrato inicial de escenarios sin ejecutar simulaciones."""
    nombre = str(nombre_proyecto or "").strip()
    if not nombre:
        raise ValueError("El nombre del proyecto no puede estar vacío.")
    if not fuente_horizonte and not fuente_sketchup:
        raise ValueError(
            "La situación actual debe declarar al menos una fuente de sombreado."
        )
    if tipo_optimizacion not in {"paneles", "obstaculos", "ambos", "por_definir"}:
        raise ValueError(f"Tipo de optimización no soportado: {tipo_optimizacion!r}")

    fuentes_actual = []
    if fuente_horizonte:
        fuentes_actual.append("horizonte")
    if fuente_sketchup:
        fuentes_actual.append("sketchup")

    return {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "fase": 4,
        "nombre_proyecto": nombre,
        "estado": "definicion_inicial",
        "invariantes": {
            "misma_ubicacion": True,
            "mismo_tmy": True,
            "mismos_timestamps_utc": True,
            "mismas_fachadas_y_puntos": True,
            "mismo_panel": panel_nombre,
            "mismo_inversor": inversor_nombre,
            "misma_configuracion_electrica": True,
            "no_mezclar_fs_climatico_con_fs_geometrico": True,
        },
        "politica_fuentes_actual": {
            "fuentes_declaradas": fuentes_actual,
            "no_sumar_dos_veces": True,
            "reconciliacion_requerida": len(fuentes_actual) > 1,
            "descripcion": (
                "Horizonte y SketchUp se conservarán como fuentes trazables; "
                "antes de comparar se reconciliarán para evitar doble conteo."
                if len(fuentes_actual) > 1
                else "Se usará la única fuente de sombreado declarada."
            ),
        },
        "escenarios": {
            "referencia": {
                "id": "referencia",
                "nombre": "Referencia sin obstáculos",
                "estado": "definido",
                "fs_geometrico": "cero",
                "fuentes_sombra": [],
                "cambio_permitido": "ninguno; solo se elimina la sombra geométrica",
            },
            "actual": {
                "id": "actual",
                "nombre": "Situación actual",
                "estado": (
                    "definido_reconciliacion_pendiente"
                    if len(fuentes_actual) > 1
                    else "definido"
                ),
                "fs_geometrico": "fuente_actual_reconciliada",
                "fuentes_sombra": fuentes_actual,
                "cambio_permitido": "ninguno",
            },
            "optimizada": {
                "id": "optimizada",
                "nombre": "Alternativa optimizada",
                "estado": "pendiente_parametros",
                "fs_geometrico": "nueva_distribucion_paneles",
                "fuentes_sombra": fuentes_actual,
                "tipo_optimizacion": tipo_optimizacion,
                "cambio_permitido": (
                    "ubicación, separación o distribución de paneles; "
                    "sin cambiar panel, TMY, ubicación ni inversor"
                ),
            },
        },
    }


def validar_definicion_escenarios(definicion: dict[str, Any]) -> None:
    """Valida el contrato mínimo antes de persistirlo o simularlo."""
    if definicion.get("schema_version") != SCENARIO_SCHEMA_VERSION:
        raise ValueError("Versión de contrato de escenarios inválida.")
    escenarios = definicion.get("escenarios")
    if not isinstance(escenarios, dict) or set(escenarios) != set(SCENARIO_IDS):
        raise ValueError("La definición debe contener referencia, actual y optimizada.")
    invariantes = definicion.get("invariantes")
    if not isinstance(invariantes, dict):
        raise ValueError("Faltan invariantes de comparación.")
    for clave in (
        "misma_ubicacion",
        "mismo_tmy",
        "mismos_timestamps_utc",
        "mismas_fachadas_y_puntos",
        "misma_configuracion_electrica",
    ):
        if invariantes.get(clave) is not True:
            raise ValueError(f"La invariante {clave!r} debe ser True.")
    if "base_comparacion" in definicion:
        base = definicion["base_comparacion"]
        if not isinstance(base, dict):
            raise ValueError("La base de comparación debe ser un diccionario.")
        # La definición puede guardarse como borrador para mostrar faltantes,
        # pero una comparación solo puede consumir una base lista.
        if base.get("lista_para_comparar") is True:
            validar_base_comparacion(base)
    politica = definicion.get("politica_fuentes_actual", {})
    fuentes = politica.get("fuentes_declaradas", [])
    if not fuentes:
        raise ValueError("La situación actual no tiene fuentes declaradas.")
    if len(fuentes) > 1 and politica.get("no_sumar_dos_veces") is not True:
        raise ValueError("Las fuentes múltiples deben impedir doble conteo.")