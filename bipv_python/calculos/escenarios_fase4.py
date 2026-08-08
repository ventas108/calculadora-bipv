"""Definición trazable de escenarios para la Fase 4 de comparación.

Este módulo solo define escenarios y sus invariantes. No calcula POA,
energía, pérdidas ni recuperación: esos cálculos pertenecen a la siguiente
etapa y deben consumir este contrato sin cambiar sus supuestos.
"""
from __future__ import annotations

from typing import Any


SCENARIO_SCHEMA_VERSION = "bipv.scenarios.v1"
SCENARIO_IDS = ("referencia", "actual", "optimizada")


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
    politica = definicion.get("politica_fuentes_actual", {})
    fuentes = politica.get("fuentes_declaradas", [])
    if not fuentes:
        raise ValueError("La situación actual no tiene fuentes declaradas.")
    if len(fuentes) > 1 and politica.get("no_sumar_dos_veces") is not True:
        raise ValueError("Las fuentes múltiples deben impedir doble conteo.")