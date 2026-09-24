"""Frontera entre sombra por superficie y estado de la aplicacion."""
from __future__ import annotations
from collections.abc import Mapping
from typing import Any
import copy
import numpy as np
import pandas as pd
from calculos.adaptador_multisuperficie import _CLAVES_SUPERFICIE_REQUERIDAS
from calculos.produccion_vigencia import huella_horaria
from calculos.sombras_3d import ESTADOS_SOMBRA_ACEPTABLES, VERSION_ALGORITMO_FS_POR_SUPERFICIE
from calculos.transicion_multisuperficie import recalcular_agregados_proyecto, recalcular_etapa_inversor_bus, recalcular_fisica_superficie
from calculos.adaptador_multisuperficie import construir_proyecto_desde_session_state

_CAMPOS_SOMBRA = ("p_shade", "firma_sombra", "cobertura_sombra", "advertencias_sombra", "calidad_confianza_sombra", "estado_sombra")

def aplicar_sombra_a_superficies(superficies_bipv: list[dict], resultados_sombra: Mapping[str, Mapping[str, Any]]) -> list[dict]:
    nombres = {s.get("nombre") for s in superficies_bipv}
    huerfanos = set(resultados_sombra) - nombres
    if huerfanos:
        raise ValueError(f"resultados_sombra referencia superficies inexistentes: {sorted(huerfanos)}")
    salida = []
    for sup in superficies_bipv:
        nueva = copy.deepcopy(sup)
        datos = resultados_sombra.get(sup.get("nombre"))
        if datos is not None:
            estado = datos.get("estado_sombra", datos.get("estado", "calculado_completo"))
            nueva["estado_sombra"] = estado
            if estado not in ESTADOS_SOMBRA_ACEPTABLES:
                for campo in _CAMPOS_SOMBRA:
                    nueva.pop(campo, None)
                nueva["estado_sombra"] = estado
            else:
                nueva["p_shade"] = np.asarray(datos["p_shade"], dtype=float)
                nueva["firma_sombra"] = dict(datos["firma_sombra"])
                nueva["cobertura_sombra"] = dict(datos.get("cobertura", {}))
                nueva["advertencias_sombra"] = list(datos.get("advertencias", []))
                nueva["calidad_confianza_sombra"] = datos.get("calidad_confianza", "alta")
        salida.append(nueva)
    return salida


def preservar_o_invalidar_campos_fisicos(anterior: Mapping[str, Any] | None, editada: Mapping[str, Any]) -> dict:
    nueva = dict(editada)
    if anterior is None:
        return nueva
    for campo in ("n_serie", "n_paralelo", "inversor_id"):
        if campo not in nueva and campo in anterior:
            nueva[campo] = anterior[campo]
    entradas = ("tilt_deg", "azimuth_deg", "area_m2", "n_serie", "puntos_analisis", "malla_horizonte", "transparencia")
    cambio = any(anterior.get(c) != nueva.get(c) for c in entradas)
    if not cambio:
        for campo in _CAMPOS_SOMBRA:
            if campo in anterior and campo not in nueva:
                nueva[campo] = copy.deepcopy(anterior[campo])
    else:
        for campo in _CAMPOS_SOMBRA:
            nueva.pop(campo, None)
    # Spec 05/vigencia-poa-superficie: la firma de la POA sigue a la
    # superficie mientras no cambie su geometría ni su montaje.
    geometria_poa = ("tipo", "tilt_deg", "azimuth_deg", "area_m2", "montaje_fachada")
    if any(anterior.get(c) != nueva.get(c) for c in geometria_poa):
        nueva.pop("firma_poa", None)
    elif "firma_poa" in anterior and "firma_poa" not in nueva:
        nueva["firma_poa"] = anterior["firma_poa"]
    return nueva


def resumen_estado_fisico_superficies(superficies_bipv: list[dict]) -> list[dict]:
    salida = []
    for sup in superficies_bipv:
        if not sup.get("activa", True):
            continue
        faltantes = [c for c in _CLAVES_SUPERFICIE_REQUERIDAS if sup.get(c) is None]
        salida.append({"nombre": sup.get("nombre"), "lista": not faltantes, "campos_faltantes": faltantes})
    return salida


def invalidar_sombra_por_cambio_tmy(superficies_bipv: list[dict], tmy: pd.DataFrame) -> list[dict]:
    """Retira p_shade/firma_sombra de toda superficie cuya firma fue calculada
    contra un TMY distinto del vigente -- el TMY es una entrada GLOBAL del
    proyecto, no por superficie, así que se audita en lote aquí, no en
    preservar_o_invalidar_campos_fisicos (que solo ve una superficie a la
    vez). Compara contra la MISMA huella que calcula
    calculos.sombras_3d.calcular_fs_horario_por_superficie
    (huella_horaria(tmy.index, tmy["T2m"])) -- no se reimplementa una
    segunda fórmula. Restaurado (auditoría 2026-09-21, ronda de
    recuperación): esta función había quedado como no-op tras la
    reconstrucción posterior al borrado accidental.
    """
    if not isinstance(tmy, pd.DataFrame) or "T2m" not in tmy.columns:
        raise ValueError("tmy debe ser un DataFrame con columna T2m real.")
    tmy_fp_actual = huella_horaria(pd.DatetimeIndex(tmy.index), tmy["T2m"].to_numpy(dtype=float))
    salida = []
    for sup in superficies_bipv:
        firma = sup.get("firma_sombra")
        if isinstance(firma, Mapping) and firma.get("tmy_fingerprint") != tmy_fp_actual:
            nueva = dict(sup)
            for campo in _CAMPOS_SOMBRA:
                nueva.pop(campo, None)
            nueva["sombra_bloqueo_motivo"] = (
                f"La superficie '{sup.get('nombre')}' tenía sombra calculada "
                "contra un TMY distinto del vigente -- recalcula la sombra "
                "con el TMY actual antes de usar el modo físico."
            )
            salida.append(nueva)
        else:
            salida.append(dict(sup))
    return salida


def invalidar_sombra_por_version_algoritmo(superficies_bipv: list[dict]) -> list[dict]:
    """Retira p_shade/firma_sombra de toda superficie cuya sombra calculó
    ``sombras_3d`` con una versión de algoritmo distinta de la vigente.

    Spec 05/sombra-cara-trasera: las sombras v1 contaban como sombra total
    las horas con el sol detrás del plano del módulo; restaurarlas desde la
    persistencia metería esa pérdida falsa en Producción. Solo aplica a
    firmas de ``sombras_3d`` (fuente/proveedor): sombras de otras fuentes no
    dependen de este algoritmo y se conservan.
    """
    salida = []
    for sup in superficies_bipv:
        firma = sup.get("firma_sombra")
        de_sombras_3d = isinstance(firma, Mapping) and "sombras_3d" in (
            firma.get("fuente"), firma.get("proveedor"),
        )
        if de_sombras_3d and firma.get("version_algoritmo") != VERSION_ALGORITMO_FS_POR_SUPERFICIE:
            nueva = dict(sup)
            for campo in _CAMPOS_SOMBRA:
                nueva.pop(campo, None)
            nueva["sombra_bloqueo_motivo"] = (
                f"La superficie '{sup.get('nombre')}' tenía sombra calculada con "
                f"un algoritmo anterior ({firma.get('version_algoritmo') or 'sin versión'}) "
                "que contaba horas con el sol detrás del módulo -- recalcula la "
                "sombra antes de usar el modo físico."
            )
            salida.append(nueva)
        else:
            salida.append(dict(sup))
    return salida


def construir_y_recalcular_proyecto_fisico(session_state: Mapping[str, Any], tmy: pd.DataFrame, lat: float, lon: float, alt_m: float) -> dict:
    if not isinstance(tmy, pd.DataFrame) or "T2m" not in tmy.columns:
        raise ValueError(
            "Falta el TMY de Recurso Solar (DataFrame con columna T2m real) "
            "-- no se puede construir ni recalcular el proyecto físico sin él."
        )
    # Auditoría 2026-09-21, ronda de recuperación: esta invalidación por TMY
    # se había perdido tras el borrado accidental -- sin ella, una sombra
    # calculada contra un TMY viejo se aceptaba en silencio.
    superficies_frescas = invalidar_sombra_por_cambio_tmy(
        list(session_state.get("superficies_bipv") or []), tmy,
    )
    superficies_frescas = invalidar_sombra_por_version_algoritmo(superficies_frescas)
    session_state_fresco = dict(session_state)
    session_state_fresco["superficies_bipv"] = superficies_frescas

    proyecto = construir_proyecto_desde_session_state(session_state_fresco)
    for nombre, sup in list(proyecto["superficies"].items()):
        proyecto["superficies"][nombre] = recalcular_fisica_superficie(sup, tmy, lat, lon, alt_m)
    for inv_id in proyecto["inversores"]:
        proyecto = recalcular_etapa_inversor_bus(proyecto, inv_id)
    proyecto["agregados"] = recalcular_agregados_proyecto(proyecto)
    return proyecto
