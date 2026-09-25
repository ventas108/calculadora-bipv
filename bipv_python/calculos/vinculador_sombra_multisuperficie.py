"""Frontera entre sombra por superficie y estado de la aplicacion."""
from __future__ import annotations
from collections.abc import Mapping
from typing import Any
import copy
import numpy as np
import pandas as pd
from calculos.adaptador_multisuperficie import _CLAVES_SUPERFICIE_REQUERIDAS
from calculos.produccion_vigencia import huella_horaria
from calculos.sombras_3d import (
    ESTADO_CALCULADO_COMPLETO,
    ESTADO_CALCULO_INCOMPLETO,
    ESTADO_ERROR_GEOMETRICO,
    ESTADO_SOMBRA_CERO_CALCULADA,
    ESTADOS_SOMBRA_ACEPTABLES,
    VERSION_ALGORITMO_FS_POR_SUPERFICIE,
)
from calculos.transicion_multisuperficie import recalcular_agregados_proyecto, recalcular_etapa_inversor_bus, recalcular_fisica_superficie
from calculos.adaptador_multisuperficie import construir_proyecto_desde_session_state

_CAMPOS_SOMBRA = ("p_shade", "firma_sombra", "cobertura_sombra", "advertencias_sombra", "calidad_confianza_sombra", "estado_sombra")
# Spec 08-interfaz/estado-sombra-superficie: en un estado no aceptable solo se
# retira la sombra horaria; el estado, las advertencias y la calidad quedan
# para explicar el motivo en la página.
_CAMPOS_SOMBRA_HORARIA = ("p_shade", "firma_sombra", "cobertura_sombra")
_MOTIVOS_SOMBRA = ("sombra_invalidada_motivo", "sombra_bloqueo_motivo")
_ETIQUETA_CAMPO = {
    "tilt_deg": "tilt", "azimuth_deg": "azimuth", "area_m2": "área",
    "n_serie": "N serie", "puntos_analisis": "puntos de análisis",
    "malla_horizonte": "malla de sombra", "transparencia": "transparencia",
}

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
            for campo in _MOTIVOS_SOMBRA:
                nueva.pop(campo, None)
            if estado not in ESTADOS_SOMBRA_ACEPTABLES:
                for campo in _CAMPOS_SOMBRA_HORARIA:
                    nueva.pop(campo, None)
                nueva["advertencias_sombra"] = list(datos.get("advertencias", []))
                nueva["calidad_confianza_sombra"] = datos.get("calidad_confianza", "baja")
            else:
                nueva["p_shade"] = np.asarray(datos["p_shade"], dtype=float)
                nueva["firma_sombra"] = dict(datos["firma_sombra"])
                nueva["cobertura_sombra"] = dict(datos.get("cobertura", {}))
                nueva["advertencias_sombra"] = list(datos.get("advertencias", []))
                nueva["calidad_confianza_sombra"] = datos.get("calidad_confianza", "alta")
        salida.append(nueva)
    return salida


def _n_serie_grupos(sup: Mapping[str, Any]) -> tuple:
    grupos = sup.get("grupos")
    if not isinstance(grupos, list):
        return ()
    return tuple(g.get("n_serie") for g in grupos if isinstance(g, Mapping))


def preservar_o_invalidar_campos_fisicos(anterior: Mapping[str, Any] | None, editada: Mapping[str, Any]) -> dict:
    nueva = dict(editada)
    if anterior is None:
        return nueva
    # Fase A2 (Spec 03/diseno-electrico-multisuperficie): los grupos de
    # strings viajan con la superficie; el editor los reescribe después.
    for campo in ("n_serie", "n_paralelo", "inversor_id", "grupos"):
        if campo not in nueva and campo in anterior:
            nueva[campo] = copy.deepcopy(anterior[campo])
    entradas = ("tilt_deg", "azimuth_deg", "area_m2", "n_serie", "puntos_analisis", "malla_horizonte", "transparencia")
    cambiados = [c for c in entradas if anterior.get(c) != nueva.get(c)]
    if _n_serie_grupos(anterior) != _n_serie_grupos(nueva) and "n_serie" not in cambiados:
        cambiados.append("n_serie")
    if not cambiados:
        for campo in _CAMPOS_SOMBRA + ("sombra_invalidada_motivo",):
            if campo in anterior and campo not in nueva:
                nueva[campo] = copy.deepcopy(anterior[campo])
    else:
        for campo in _CAMPOS_SOMBRA:
            nueva.pop(campo, None)
        # Spec 08-interfaz/estado-sombra-superficie: el motivo queda visible.
        if any(c in anterior for c in _CAMPOS_SOMBRA) or "sombra_invalidada_motivo" in anterior:
            nueva["sombra_invalidada_motivo"] = "cambió " + ", ".join(
                _ETIQUETA_CAMPO.get(c, c) for c in cambiados
            )
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
        # Fase A2 de la Spec 03/diseno-electrico-multisuperficie: n_serie,
        # n_paralelo e inversor_id se revisan en cada grupo de strings.
        from calculos.diseno_electrico_multisup import grupos_de_superficie

        grupos = grupos_de_superficie(sup)
        faltantes = [c for c in ("p_shade", "firma_sombra") if sup.get(c) is None]
        if not grupos:
            faltantes = ["n_serie", "n_paralelo", "inversor_id"] + faltantes
        for campo in ("n_serie", "n_paralelo", "inversor_id"):
            if grupos and any(g.get(campo) is None for g in grupos):
                faltantes.insert(0, campo)
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


# ── Diagnóstico de sombra por superficie (Spec 08-interfaz/estado-sombra-superficie)
ESTADO_SIN_CALCULAR = "sin_calcular"
ESTADO_INVALIDADA_TMY = "invalidada_tmy"
ESTADO_INVALIDADA_VERSION = "invalidada_version"
ESTADO_INVALIDADA_GEOMETRIA = "invalidada_geometria"
ESTADOS_DIAGNOSTICO_SOMBRA = (
    ESTADO_CALCULADO_COMPLETO, ESTADO_SOMBRA_CERO_CALCULADA,
    ESTADO_CALCULO_INCOMPLETO, ESTADO_ERROR_GEOMETRICO, ESTADO_SIN_CALCULAR,
    ESTADO_INVALIDADA_TMY, ESTADO_INVALIDADA_VERSION, ESTADO_INVALIDADA_GEOMETRIA,
)
_RECALCULAR = "pulsa «🌳 Calcular sombra de todas las superficies»"
_ACCION_SOMBRA = {
    ESTADO_CALCULADO_COMPLETO: "Lista para el modo físico.",
    ESTADO_SOMBRA_CERO_CALCULADA: "Lista para el modo físico (sin sombra en las horas con sol).",
    ESTADO_CALCULO_INCOMPLETO: f"Revisa la malla y los puntos y {_RECALCULAR}.",
    ESTADO_ERROR_GEOMETRICO: (
        "Corrige los puntos indicados (20–50 cm por delante de la superficie, "
        f"fuera del volumen) y {_RECALCULAR}."
    ),
    ESTADO_SIN_CALCULAR: f"Escribe sus puntos 3D y {_RECALCULAR}.",
    ESTADO_INVALIDADA_TMY: f"Recalcula: {_RECALCULAR} con el TMY actual.",
    ESTADO_INVALIDADA_VERSION: f"Recalcula con el algoritmo vigente: {_RECALCULAR}.",
    ESTADO_INVALIDADA_GEOMETRIA: f"Recalcula con la geometría nueva: {_RECALCULAR}.",
}


def _problema_sombra_horaria(sup: Mapping[str, Any]) -> str | None:
    """Mismas reglas de sombra que ``construir_proyecto_desde_session_state``."""
    if sup.get("p_shade") is None or sup.get("firma_sombra") is None:
        return "no tiene sombra horaria calculada"
    try:
        sombra = np.asarray(sup["p_shade"], dtype=float)
    except (TypeError, ValueError):
        return "la sombra horaria guardada no es numérica"
    if sombra.shape != (8760,) or not np.isfinite(sombra).all() or ((sombra < 0) | (sombra > 1)).any():
        return "la sombra horaria guardada no tiene 8760 valores entre 0 y 1"
    return None


def diagnostico_sombra_superficies(superficies_bipv: list[dict], tmy: pd.DataFrame | None) -> list[dict]:
    """Estado de la sombra de cada superficie activa, de solo lectura.

    Aplica las mismas invalidaciones que ``construir_y_recalcular_proyecto_fisico``
    (TMY, versión del algoritmo) y las mismas validaciones de sombra que el
    modo físico, sin considerar la configuración eléctrica. ``utilizable`` es
    True si y solo si el modo físico aceptaría la sombra de la superficie.
    """
    activas = [copy.deepcopy(s) for s in superficies_bipv if s.get("activa", True)]
    if isinstance(tmy, pd.DataFrame) and "T2m" in tmy.columns:
        tras_tmy = invalidar_sombra_por_cambio_tmy(activas, tmy)
    else:
        tras_tmy = []
        for sup in activas:
            nueva = dict(sup)
            if nueva.get("p_shade") is not None or nueva.get("firma_sombra") is not None:
                for campo in _CAMPOS_SOMBRA:
                    nueva.pop(campo, None)
                nueva["sombra_bloqueo_motivo"] = "No hay TMY vigente para verificar la sombra."
            tras_tmy.append(nueva)
    tras_version = invalidar_sombra_por_version_algoritmo(tras_tmy)

    salida = []
    for original, sup_tmy, sup in zip(activas, tras_tmy, tras_version):
        cobertura = original.get("cobertura_sombra") or {}
        firma = original.get("firma_sombra") if isinstance(original.get("firma_sombra"), Mapping) else {}
        diag = {
            "nombre": original.get("nombre"),
            "horas_con_sol_calculadas": cobertura.get("horas_con_sol_calculadas"),
            "calidad": original.get("calidad_confianza_sombra"),
            "n_puntos": len(firma.get("puntos_analisis") or []) or None,
        }
        advertencias = [str(a).removeprefix("error_geometrico: ") for a in original.get("advertencias_sombra") or []]
        if "sombra_bloqueo_motivo" in sup_tmy and "sombra_bloqueo_motivo" not in original:
            estado, motivo = ESTADO_INVALIDADA_TMY, (
                "La sombra se calculó con otro TMY o ubicación."
                if isinstance(tmy, pd.DataFrame) else "No hay TMY vigente para verificar la sombra."
            )
        elif "sombra_bloqueo_motivo" in sup and "sombra_bloqueo_motivo" not in sup_tmy:
            estado = ESTADO_INVALIDADA_VERSION
            motivo = (
                f"La sombra se calculó con un algoritmo anterior "
                f"({firma.get('version_algoritmo') or 'sin versión'}) que contaba horas "
                "con el sol detrás del módulo."
            )
        else:
            estado_motor = sup.get("estado_sombra") or cobertura.get("estado")
            problema = _problema_sombra_horaria(sup)
            if estado_motor and estado_motor not in ESTADOS_SOMBRA_ACEPTABLES:
                estado = estado_motor
                motivo = "; ".join(advertencias) or f"El cálculo terminó en estado «{estado_motor}»."
            elif problema is None:
                estado = estado_motor or ESTADO_CALCULADO_COMPLETO
                motivo = "Sombra calculada con el TMY y el algoritmo vigentes."
            elif sup.get("p_shade") is None and sup.get("firma_sombra") is None:
                if original.get("sombra_invalidada_motivo"):
                    estado = ESTADO_INVALIDADA_GEOMETRIA
                    motivo = f"Se retiró la sombra porque {original['sombra_invalidada_motivo']}."
                else:
                    estado, motivo = ESTADO_SIN_CALCULAR, "Todavía no se calculó la sombra."
            else:
                estado, motivo = ESTADO_CALCULO_INCOMPLETO, f"La superficie {problema}."
        utilizable = estado in ESTADOS_SOMBRA_ACEPTABLES and _problema_sombra_horaria(sup) is None
        accion = _ACCION_SOMBRA.get(estado, f"Revisa las advertencias y {_RECALCULAR}.")
        if estado == ESTADO_INVALIDADA_TMY and not isinstance(tmy, pd.DataFrame):
            accion = f"Calcula ☀️ Recurso Solar y luego {_RECALCULAR}."
        salida.append({**diag, "estado": estado, "utilizable": utilizable,
                       "motivo": motivo, "accion": accion})
    return salida
