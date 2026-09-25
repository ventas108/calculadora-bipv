"""Panel fotovoltaico de cada superficie en Vista 3D multi-superficie.

Spec ``05-perdidas-y-temperatura/panel-por-superficie``: cada superficie
declara su panel (por defecto el del proyecto, de 📐 Dimensionamiento) y todos
los cálculos de Vista 3D usan el de esa superficie. La eficiencia de la
energía simplificada sale del panel (Pmax / área del módulo), nunca de un
valor fijo.

Campos en cada superficie de ``superficies_bipv``:

- ``panel_origen``: ``"proyecto"`` (o ausente) o ``"catalogo"``;
- ``panel_nombre`` y ``panel_ficha``: solo con origen ``catalogo``. La ficha
  es una copia del panel elegido, para que un proyecto guardado no dependa de
  cambios posteriores del catálogo.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, MutableMapping
from typing import Any

from calculos.produccion_vigencia import fingerprint_mapping

ORIGEN_PANEL_PROYECTO = "proyecto"
ORIGEN_PANEL_CATALOGO = "catalogo"
ORIGENES_PANEL = (ORIGEN_PANEL_PROYECTO, ORIGEN_PANEL_CATALOGO)
CAMPOS_PANEL_SUPERFICIE = ("panel_origen", "panel_nombre", "panel_ficha")

CLAVE_FIRMA_PANELES = "_multisup_firma_paneles"
# Resultados de Vista 3D calculados con los paneles de las superficies.
KEYS_RESULTADOS_PANEL = (
    "bypass_multisup_ok", "bypass_multisup_resultados",
    "mppt_comb_resultado", "mppt_comb_asig", "mppt_comb_ok", "mppt_comb_panel",
    # Comparación simplificado vs físico calculada con los paneles anteriores.
    "multisup_proyecto_fisico_candidato",
)


class PanelSuperficieError(ValueError):
    """La superficie no tiene un panel utilizable para el cálculo pedido."""


def _numero_positivo(valor: Any) -> float | None:
    if isinstance(valor, bool):
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return numero if math.isfinite(numero) and numero > 0 else None


def area_modulo(panel: Mapping[str, Any]) -> float | None:
    """Área de un módulo en m²: ``area_m2`` o, si falta, largo × ancho."""
    area = _numero_positivo(panel.get("area_m2"))
    if area:
        return area
    largo = _numero_positivo(panel.get("largo_mm"))
    ancho = _numero_positivo(panel.get("ancho_mm"))
    if largo and ancho:
        return largo * ancho / 1e6
    return None


def eficiencia_panel(panel: Mapping[str, Any], nombre: str | None = None) -> float:
    """η en STC (fracción): Pmax_stc / (área del módulo × 1000 W/m²)."""
    etiqueta = nombre or panel.get("nombre") or panel.get("modelo") or "sin nombre"
    pmax = _numero_positivo(panel.get("Pmax_stc"))
    area = area_modulo(panel)
    if not pmax or not area:
        raise PanelSuperficieError(
            f"El panel {etiqueta} no trae potencia (Pmax) o área del módulo: no se "
            "puede calcular su eficiencia."
        )
    eta = pmax / (area * 1000.0)
    if not 0.0 < eta < 1.0:
        raise PanelSuperficieError(
            f"El panel {etiqueta} da una eficiencia de {eta * 100:.1f} % "
            f"({pmax:g} W en {area:g} m²): revisa su ficha."
        )
    return eta


def origen_panel(superficie: Mapping[str, Any]) -> str:
    origen = superficie.get("panel_origen") or ORIGEN_PANEL_PROYECTO
    if origen not in ORIGENES_PANEL:
        raise PanelSuperficieError(
            f"La superficie '{superficie.get('nombre', '?')}' tiene un origen de panel "
            f"desconocido: {origen!r}."
        )
    return origen


def panel_de_superficie(
    superficie: Mapping[str, Any],
    panel_dict: Mapping[str, Any] | None,
    panel_nombre_dim: str | None,
) -> dict[str, Any]:
    """``{"panel", "nombre", "origen", "es_proyecto"}`` de una superficie.

    ``es_proyecto`` también es True si se eligió del catálogo el mismo modelo
    que el proyecto.
    """
    nombre_sup = superficie.get("nombre", "?")
    origen = origen_panel(superficie)
    if origen == ORIGEN_PANEL_PROYECTO:
        if not isinstance(panel_dict, Mapping) or not panel_dict:
            raise PanelSuperficieError(
                f"La superficie '{nombre_sup}' usa el panel del proyecto y no hay panel "
                "del proyecto: ejecuta 📐 Dimensionamiento o elige un panel del catálogo."
            )
        return {"panel": dict(panel_dict), "nombre": panel_nombre_dim or "sin nombre",
                "origen": origen, "es_proyecto": True}
    ficha = superficie.get("panel_ficha")
    nombre = superficie.get("panel_nombre")
    if not isinstance(ficha, Mapping) or not ficha or not nombre:
        raise PanelSuperficieError(
            f"La superficie '{nombre_sup}' no tiene la ficha de su panel del catálogo: "
            "vuelve a elegirlo en ⚙️ Superficies BIPV."
        )
    return {"panel": dict(ficha), "nombre": str(nombre), "origen": origen,
            "es_proyecto": bool(panel_nombre_dim) and nombre == panel_nombre_dim}


def firma_panel_superficie(
    superficie: Mapping[str, Any],
    panel_dict: Mapping[str, Any] | None,
    panel_nombre_dim: str | None,
) -> str:
    """Huella del panel que usa la superficie (o de su error, si no tiene)."""
    try:
        datos = panel_de_superficie(superficie, panel_dict, panel_nombre_dim)
    except PanelSuperficieError as error:
        return fingerprint_mapping({"error": str(error)})
    return fingerprint_mapping({"nombre": datos["nombre"], "panel": datos["panel"]})


def firma_paneles_superficies(
    superficies: list[Mapping[str, Any]],
    panel_dict: Mapping[str, Any] | None,
    panel_nombre_dim: str | None,
) -> dict[str, str]:
    """Huella del panel de cada superficie activa, por ``uid``."""
    return {
        str(s.get("uid", s.get("nombre"))): firma_panel_superficie(s, panel_dict, panel_nombre_dim)
        for s in superficies if s.get("activa", True)
    }


def eficiencias_superficies(
    superficies: list[Mapping[str, Any]],
    panel_dict: Mapping[str, Any] | None,
    panel_nombre_dim: str | None,
) -> tuple[dict[str, float], dict[str, dict], dict[str, str]]:
    """``(etas, paneles, errores)`` por nombre de superficie activa.

    ``paneles[nombre]`` trae el resultado de ``panel_de_superficie`` más su
    ``eta``. Una superficie sin panel utilizable queda solo en ``errores``.
    """
    etas: dict[str, float] = {}
    paneles: dict[str, dict] = {}
    errores: dict[str, str] = {}
    for sup in superficies:
        if not sup.get("activa", True):
            continue
        nombre = sup["nombre"]
        try:
            datos = panel_de_superficie(sup, panel_dict, panel_nombre_dim)
            eta = eficiencia_panel(datos["panel"], datos["nombre"])
        except PanelSuperficieError as error:
            errores[nombre] = str(error)
            continue
        etas[nombre] = eta
        paneles[nombre] = {**datos, "eta": eta}
    return etas, paneles, errores


def eficiencias_superficies_estado(
    session_state: Mapping[str, Any],
) -> tuple[dict[str, float], dict[str, dict], dict[str, str]]:
    return eficiencias_superficies(
        list(session_state.get("superficies_bipv") or []),
        session_state.get("panel_dict"), session_state.get("panel_nombre_dim"),
    )


def invalidar_por_cambio_panel(session_state: MutableMapping[str, Any]) -> list[str]:
    """Retira lo calculado con otros paneles si cambió el de alguna superficie.

    Compara, superficie por superficie (``uid``), la huella actual del panel
    con la registrada. La primera vez solo la registra. Agregar, eliminar,
    desactivar o renombrar superficies no es un cambio de panel. Si el panel
    de alguna superficie que ya existía cambió, retira la energía
    publicada y los resultados de bypass, MPPT y modo físico; la POA y la
    sombra no dependen del panel y se conservan. Retorna las claves retiradas.
    """
    from calculos.publicacion_multisuperficie import (
        registrar_motivo_retiro, retirar_energia_multisuperficie,
    )

    actual = firma_paneles_superficies(
        list(session_state.get("superficies_bipv") or []),
        session_state.get("panel_dict"), session_state.get("panel_nombre_dim"),
    )
    anterior = session_state.get(CLAVE_FIRMA_PANELES)
    session_state[CLAVE_FIRMA_PANELES] = actual
    if not isinstance(anterior, Mapping):
        return []
    cambiados = {uid for uid in anterior.keys() & actual.keys() if anterior[uid] != actual[uid]}
    if not cambiados:
        return []
    retiradas = retirar_energia_multisuperficie(session_state)
    registrar_motivo_retiro(session_state, retiradas, "cambió el panel", cambiados)
    for clave in KEYS_RESULTADOS_PANEL:
        if clave in session_state:
            session_state.pop(clave, None)
            retiradas.append(clave)
    return retiradas


def seleccion_panel(
    opcion: str | None,
    etiqueta_proyecto: str,
    catalogo: Mapping[str, Mapping[str, Any]],
    superficie: Mapping[str, Any],
    calibrar=None,
) -> dict[str, Any]:
    """Campos de panel de la superficie según la opción del selector.

    Si el modelo del catálogo no cambió, se conserva la ficha guardada (el
    catálogo pudo cambiar después). ``calibrar`` completa el SDM del panel
    (``resolver_panel_calibrado``); por defecto no se modifica.
    """
    if opcion is None or opcion == etiqueta_proyecto:
        return {"panel_origen": ORIGEN_PANEL_PROYECTO}
    if (
        superficie.get("panel_origen") == ORIGEN_PANEL_CATALOGO
        and superficie.get("panel_nombre") == opcion
        and isinstance(superficie.get("panel_ficha"), Mapping)
    ):
        ficha = dict(superficie["panel_ficha"])
    else:
        if opcion not in catalogo:
            raise PanelSuperficieError(f"El panel {opcion} no está en el catálogo.")
        ficha = dict(catalogo[opcion])
        if calibrar is not None:
            try:
                ficha = dict(calibrar(ficha))
            except (ValueError, TypeError, KeyError) as error:
                raise PanelSuperficieError(
                    f"El panel {opcion} no se pudo preparar para el cálculo: {error}"
                ) from error
    return {"panel_origen": ORIGEN_PANEL_CATALOGO, "panel_nombre": opcion, "panel_ficha": ficha}


def opcion_panel_actual(superficie: Mapping[str, Any], etiqueta_proyecto: str) -> str:
    if superficie.get("panel_origen") == ORIGEN_PANEL_CATALOGO and superficie.get("panel_nombre"):
        return str(superficie["panel_nombre"])
    return etiqueta_proyecto
