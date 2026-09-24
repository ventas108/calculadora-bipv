"""Panel y strings del proyecto para el bypass y el MPPT por superficie.

Spec ``08-interfaz/panel-proyecto-bypass-mppt``: por defecto ambas secciones
de Vista 3D usan el panel del proyecto (📐 Dimensionamiento) y los strings
configurados en cada superficie; cualquier diferencia queda visible.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from calculos.modelo_iv import tiene_sdm_completo

PREFIJO_PANEL_PROYECTO = "Panel del proyecto"
ORIGEN_SUPERFICIE = "superficie"
ORIGEN_DIMENSIONAMIENTO = "dimensionamiento"
ORIGEN_ESTIMADO_AREA = "estimado_por_area"
ORIGENES_STRINGS = (ORIGEN_SUPERFICIE, ORIGEN_DIMENSIONAMIENTO, ORIGEN_ESTIMADO_AREA)
ETIQUETA_ORIGEN_STRINGS = {
    ORIGEN_SUPERFICIE: "configurado en la superficie",
    ORIGEN_DIMENSIONAMIENTO: "N serie de Dimensionamiento, paralelo por área",
    ORIGEN_ESTIMADO_AREA: "N serie de la superficie, paralelo por área",
}


def etiqueta_panel_proyecto(panel_nombre: str | None) -> str:
    return f"{PREFIJO_PANEL_PROYECTO} ({panel_nombre or 'sin nombre'})"


def opciones_panel_superficie(
    panel_dict: Mapping[str, Any] | None,
    panel_nombre: str | None,
    catalogo: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, dict], str | None]:
    """Opciones del selector de panel y aviso si el del proyecto no sirve.

    La primera opción es el panel del proyecto (esté o no en el catálogo)
    cuando tiene ficha SDM completa, porque el bypass y el MPPT resuelven el
    circuito con el SDM. Si no hay panel del proyecto o no tiene SDM, el aviso
    explica por qué hay que elegir uno del catálogo.
    """
    opciones: dict[str, dict] = {}
    aviso = None
    if isinstance(panel_dict, Mapping) and panel_dict:
        if tiene_sdm_completo(dict(panel_dict)):
            opciones[etiqueta_panel_proyecto(panel_nombre)] = dict(panel_dict)
        else:
            aviso = (
                f"El panel del proyecto ({panel_nombre or 'sin nombre'}) no tiene ficha "
                "SDM completa, que este cálculo necesita: elige un panel del catálogo."
            )
    else:
        aviso = (
            "No hay panel del proyecto (ejecuta 📐 Dimensionamiento): elige un panel "
            "del catálogo."
        )
    for nombre, panel in catalogo.items():
        if tiene_sdm_completo(dict(panel)):
            opciones[nombre] = dict(panel)
    return opciones, aviso


def es_panel_del_proyecto(opcion: str | None, panel_nombre: str | None) -> bool:
    """True si la opción elegida es el panel del proyecto (o su mismo modelo)."""
    if not opcion:
        return False
    return opcion.startswith(PREFIJO_PANEL_PROYECTO) or (
        bool(panel_nombre) and opcion == panel_nombre
    )


def _entero_positivo(valor: Any) -> int | None:
    if isinstance(valor, bool):
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    if not numero.is_integer() or numero < 1:
        return None
    return int(numero)


def strings_superficie(
    superficie: Mapping[str, Any],
    n_serie_dimensionamiento: Any,
    panel: Mapping[str, Any],
) -> dict[str, Any]:
    """``{"n_serie", "n_paralelo", "origen", "aviso"}`` de una superficie.

    Usa ``n_serie``/``n_paralelo`` de la superficie si ambos son enteros ≥ 1.
    Si falta el N serie se toma el de Dimensionamiento; si falta el paralelo se
    estima por área (módulos que caben ÷ N serie). Una estimación siempre
    trae aviso; sin ningún N serie válido se lanza ``ValueError``.
    """
    nombre = superficie.get("nombre", "?")
    n_serie = _entero_positivo(superficie.get("n_serie"))
    n_paralelo = _entero_positivo(superficie.get("n_paralelo"))
    if n_serie and n_paralelo:
        return {"n_serie": n_serie, "n_paralelo": n_paralelo,
                "origen": ORIGEN_SUPERFICIE, "aviso": None}
    origen = ORIGEN_ESTIMADO_AREA
    if not n_serie:
        n_serie = _entero_positivo(n_serie_dimensionamiento)
        origen = ORIGEN_DIMENSIONAMIENTO
        if not n_serie:
            raise ValueError(
                f"La superficie '{nombre}' no tiene N serie válido y tampoco hay N serie "
                "en 📐 Dimensionamiento: configúralo en ⚙️ Superficies BIPV."
            )
    area_panel = panel.get("area_m2")
    try:
        area_panel = float(area_panel)
    except (TypeError, ValueError):
        area_panel = 0.0
    if area_panel <= 0:
        raise ValueError(
            f"El panel elegido no trae su área: no se puede estimar el paralelo de "
            f"'{nombre}'. Configura N paralelo en ⚙️ Superficies BIPV."
        )
    n_modulos = max(1, int(float(superficie.get("area_m2", 0.0)) / area_panel))
    n_paralelo = max(1, round(n_modulos / n_serie))
    return {
        "n_serie": n_serie, "n_paralelo": n_paralelo, "origen": origen,
        "aviso": (
            f"'{nombre}': strings por estimación ({ETIQUETA_ORIGEN_STRINGS[origen]}); "
            "configura N serie y N paralelo en ⚙️ Superficies BIPV para usar los reales."
        ),
    }
