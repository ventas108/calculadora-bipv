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


def formato_strings(n_serie: int, n_paralelo: int) -> str:
    """Formato único para mostrar strings: «8 serie × 17 paralelo».

    Evita que una leyenda diga «17×8s» y la tabla «8 × 17» para el mismo dato.
    """
    return f"{int(n_serie)} serie × {int(n_paralelo)} paralelo"


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
    panel_es_del_proyecto: bool = True,
) -> dict[str, Any]:
    """``{"n_serie", "n_paralelo", "origen", "aviso"}`` de una superficie.

    Usa ``n_serie``/``n_paralelo`` de la superficie si ambos son enteros ≥ 1.
    Si falta el N serie se toma el de Dimensionamiento; si falta el paralelo se
    estima por área (módulos que caben ÷ N serie). Una estimación siempre
    trae aviso; sin ningún N serie válido se lanza ``ValueError``.

    El N serie de Dimensionamiento se dimensionó para el panel del proyecto:
    con ``panel_es_del_proyecto=False`` (Spec ``05/panel-por-superficie``) no
    se usa de respaldo y la superficie debe traer su propio N serie.
    """
    nombre = superficie.get("nombre", "?")
    grupos = superficie.get("grupos")
    if isinstance(grupos, list) and len(grupos) > 1:
        raise ValueError(
            f"La superficie '{nombre}' tiene {len(grupos)} grupos de strings: este cálculo "
            "trabaja con un solo string por superficie. Usa strings_grupos_superficie."
        )
    n_serie = _entero_positivo(superficie.get("n_serie"))
    n_paralelo = _entero_positivo(superficie.get("n_paralelo"))
    if n_serie and n_paralelo:
        return {"n_serie": n_serie, "n_paralelo": n_paralelo,
                "origen": ORIGEN_SUPERFICIE, "aviso": None}
    origen = ORIGEN_ESTIMADO_AREA
    if not n_serie:
        if not panel_es_del_proyecto:
            raise ValueError(
                f"La superficie '{nombre}' usa un panel distinto al del proyecto y no tiene "
                "N serie propio: el de 📐 Dimensionamiento es para otro panel. Configúralo "
                "en ⚙️ Superficies BIPV › 🔌 Inversores por superficie."
            )
        n_serie = _entero_positivo(n_serie_dimensionamiento)
        origen = ORIGEN_DIMENSIONAMIENTO
        if not n_serie:
            raise ValueError(
                f"La superficie '{nombre}' no tiene N serie válido y tampoco hay N serie "
                "en 📐 Dimensionamiento: configúralo en ⚙️ Superficies BIPV."
            )
    from calculos.panel_superficie import area_modulo

    area_panel = area_modulo(panel) or 0.0
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


def strings_grupos_superficie(
    superficie: Mapping[str, Any],
    n_serie_dimensionamiento: Any,
    panel: Mapping[str, Any],
    panel_es_del_proyecto: bool = True,
) -> list[dict[str, Any]]:
    """Strings de cada grupo de la superficie (Spec
    ``03/diseno-electrico-multisuperficie``, fase A2).

    ``[{"gid", "n_serie", "n_paralelo", "modulos", "origen", "aviso"}]``.
    Con un grupo o ninguno equivale a :func:`strings_superficie` (``gid``
    ``G1``). Con varios, cada grupo debe traer N serie y N paralelo enteros
    ≥ 1: no se estima nada, porque repartir el área entre grupos sería
    inventar el diseño; si falta alguno se lanza ``ValueError`` nombrando el
    grupo.
    """
    grupos = superficie.get("grupos")
    if not (isinstance(grupos, list) and len(grupos) > 1):
        uno = dict(superficie)
        if isinstance(grupos, list) and len(grupos) == 1:
            uno.update(n_serie=grupos[0].get("n_serie"), n_paralelo=grupos[0].get("n_paralelo"))
        uno.pop("grupos", None)
        r = strings_superficie(uno, n_serie_dimensionamiento, panel, panel_es_del_proyecto)
        gid = grupos[0].get("gid", "G1") if isinstance(grupos, list) and grupos else "G1"
        return [{"gid": gid, **r, "modulos": r["n_serie"] * r["n_paralelo"]}]
    nombre = superficie.get("nombre", "?")
    salida = []
    for i, g in enumerate(grupos, start=1):
        gid = g.get("gid") or f"G{i}"
        n_s, n_p = _entero_positivo(g.get("n_serie")), _entero_positivo(g.get("n_paralelo"))
        if not (n_s and n_p):
            raise ValueError(
                f"La superficie '{nombre}' ({gid}) no tiene N serie y N paralelo válidos. "
                "Con varios grupos cada uno necesita los suyos: configúralos en "
                "⚙️ Superficies BIPV › 🔌 Inversores por superficie."
            )
        salida.append({"gid": gid, "n_serie": n_s, "n_paralelo": n_p, "modulos": n_s * n_p,
                       "origen": ORIGEN_SUPERFICIE, "aviso": None})
    return salida


def perdida_ponderada_por_modulos(resultados: list[Mapping[str, Any]]) -> float:
    """Pérdida (%) de la superficie a partir de la de cada grupo, ponderada
    por sus módulos: ``Σ pct_g × módulos_g / Σ módulos_g``.

    Todos los grupos de una superficie ven la misma POA y la misma sombra, así
    que la energía de cada uno es proporcional a sus módulos.
    """
    total = sum(int(r["modulos"]) for r in resultados)
    if total <= 0:
        raise ValueError("Sin módulos para ponderar la pérdida de la superficie.")
    return sum(float(r["pct"]) * int(r["modulos"]) for r in resultados) / total
