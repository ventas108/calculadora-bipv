"""Adaptadores puros entre session_state y el proyecto fisico."""
from __future__ import annotations
from collections.abc import Mapping, MutableMapping
from typing import Any
import numpy as np
import pandas as pd
from calculos.inversores_multisuperficie import validar_inversores_y_asignaciones, aplicar_tipos_derivados
from calculos.sombras_3d import ESTADOS_SOMBRA_ACEPTABLES
from calculos.transicion_multisuperficie import inversor_nuevo, proyecto_nuevo, superficie_nueva

_HORAS_ANIO = 8760
_CLAVES_SUPERFICIE_REQUERIDAS = ("n_serie", "n_paralelo", "inversor_id", "p_shade", "firma_sombra")


def construir_proyecto_desde_session_state(session_state: Mapping[str, Any]) -> dict:
    superficies = [s for s in (session_state.get("superficies_bipv") or []) if s.get("activa", True)]
    if not superficies:
        raise ValueError("No hay superficies BIPV activas para el modo fisico.")
    panel = session_state.get("panel_dict")
    if not isinstance(panel, Mapping):
        raise ValueError("Falta 'panel_dict' global para el modo fisico.")
    inversores_ss = session_state.get("multisup_inversores")
    if not isinstance(inversores_ss, list) or not inversores_ss:
        raise ValueError("Falta 'multisup_inversores'.")
    validacion = validar_inversores_y_asignaciones(superficies, inversores_ss)
    if not validacion["ok"]:
        raise ValueError("Configuracion multi-superficie invalida: " + "; ".join(validacion["errores"]))
    inversores_ss = aplicar_tipos_derivados(inversores_ss, validacion["tipos_derivados"])
    inversores = [inversor_nuevo(str(i["inversor_id"]), i["tipo"], float(i["eta_inversor"]), i.get("P_ac_nom_W"), dict(i.get("ficha") or i.get("inversor") or {})) for i in inversores_ss]
    salida = []
    for entrada in superficies:
        nombre = str(entrada.get("nombre", "")).strip()
        if not nombre:
            raise ValueError("Cada superficie activa debe tener nombre.")
        estado = entrada.get("estado_sombra") or entrada.get("cobertura_sombra", {}).get("estado")
        if estado and estado not in ESTADOS_SOMBRA_ACEPTABLES:
            raise ValueError(f"La superficie '{nombre}' tiene sombra en estado '{estado}'. Recalcula antes de continuar.")
        for campo in _CLAVES_SUPERFICIE_REQUERIDAS:
            if entrada.get(campo) is None:
                raise ValueError(f"La superficie '{nombre}' no puede entrar al modo fisico: falta '{campo}'.")
        sombra = np.asarray(entrada["p_shade"], dtype=float)
        if sombra.shape != (_HORAS_ANIO,) or not np.isfinite(sombra).all() or ((sombra < 0) | (sombra > 1)).any():
            raise ValueError(f"La superficie '{nombre}' tiene p_shade invalido; se requieren 8760 valores entre 0 y 1.")
        sup = superficie_nueva(nombre, str(entrada.get("tipo", "Fachada")), float(entrada.get("tilt_deg", 90)), float(entrada.get("azimuth_deg", 180)), float(entrada.get("area_m2", 0)), dict(panel), int(entrada["n_serie"]), int(entrada["n_paralelo"]), str(entrada["inversor_id"]), sombra, float(entrada.get("albedo", 0.2)), entrada.get("bifacial"), float(entrada.get("k_bipv", 1.0)))
        sup["_firma_sombra"] = dict(entrada["firma_sombra"])
        salida.append(sup)
    return proyecto_nuevo(inversores, salida)


def aplicar_proyecto_a_session_state(
    proyecto: Mapping[str, Any],
    session_state: MutableMapping[str, Any],
    *,
    confirmar_reemplazo: bool = True,
) -> dict:
    """Publica el proyecto físico con origen ``fisico`` (publicación única).

    Delega en ``publicar_energia_multisuperficie``: valida todo antes de
    escribir. ``confirmar_reemplazo=False`` deja que la página pida
    confirmación cuando la energía vigente viene de otro origen.
    """
    from calculos.publicacion_multisuperficie import ORIGEN_FISICO, publicar_energia_multisuperficie

    agregados = proyecto.get("agregados")
    if not isinstance(agregados, Mapping):
        raise ValueError("El proyecto no tiene agregados calculados.")
    desglose = []
    for nombre, sup in proyecto["superficies"].items():
        dc, ac = sup.get("resultados_dc") or {}, sup.get("resultados_ac") or {}
        if "E_ac_anual_kWh" not in ac or "poa_anual_kWh_m2" not in dc:
            raise ValueError(f"La superficie '{nombre}' no tiene resultados completos.")
        desglose.append({"nombre": nombre, "tipo": sup.get("tipo"), "area_m2": sup.get("area_m2"), "e_ac_kWh": ac["E_ac_anual_kWh"], "poa_kWh_m2": dc["poa_anual_kWh_m2"]})
    return publicar_energia_multisuperficie(
        session_state,
        origen=ORIGEN_FISICO,
        e_ac_total=agregados["E_ac_total_kWh"],
        desglose=desglose,
        poa_ponderada=_poa_ponderada(proyecto),
        area_total=agregados["area_total_m2"],
        proyecto_fisico=proyecto,
        confirmar_reemplazo=confirmar_reemplazo,
    )


def _poa_ponderada(proyecto: Mapping[str, Any]) -> pd.DataFrame | None:
    """Promedio de ``poa_global`` ponderado por área entre TODAS las
    superficies del proyecto -- contrato del Director
    (``CodeSpecs/05-perdidas-y-temperatura/transicion-multisuperficie/
    diseno.md``): ``poa_df_multisup`` = "ponderación por área de poa_df por
    superficie". Restaurado (auditoría 2026-09-21, ronda de recuperación): la
    reconstrucción posterior al borrado accidental solo devolvía un
    resultado cuando exactamente UNA superficie tenía ``poa_df`` -- con 2+
    superficies (el caso normal de un proyecto multi-superficie) siempre
    daba ``None``, perdiendo la agregación para los 8 consumidores que la
    leen."""
    filas, pesos = [], []
    for sup in proyecto["superficies"].values():
        poa_df = sup.get("poa_df")
        if not isinstance(poa_df, pd.DataFrame) or "poa_global" not in poa_df.columns:
            continue
        filas.append(poa_df["poa_global"].astype(float))
        pesos.append(float(sup.get("area_m2", 0.0)))
    if not filas or sum(pesos) <= 0:
        return None
    datos = np.vstack([serie.to_numpy() for serie in filas])
    return pd.DataFrame(
        {"poa_global": np.average(datos, axis=0, weights=np.asarray(pesos))},
        index=filas[0].index,
    )
