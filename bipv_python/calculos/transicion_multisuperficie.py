# -*- coding: utf-8 -*-
"""
transicion_multisuperficie.py — Transición transaccional de configuración
para proyectos BIPV multi-superficie (orientación/inclinación/inversor).

Alcance de esta Spec (ver informe de entrega): ÚNICAMENTE la transición
transaccional -- no crea un motor óptico nuevo, no reemplaza
`calculos.mismatch_bypass.simular_bypass_horario` ni `calculos.solar.
calcular_poa`, y no toca IAM/soiling (Motor Óptico, página 5b) ni el
comparador de orientación. Orquesta esas piezas EXISTENTES sobre un estado
de proyecto multi-superficie explícito (no `st.session_state`, que solo
modela UN escenario a la vez -- ver CodeSpecs/05-perdidas-y-temperatura/
conservacion-optica-inversor/problema.md, que deja esto fuera de su alcance).

Modelo de datos
----------------
``proyecto`` es un dict puro (serializable), NUNCA un `st.session_state`:

    {
      "schema_version": "bipv.transicion-multisuperficie.v1",
      "inversores": {
          "<inversor_id>": {
              "inversor_id": str,
              "tipo": "dedicado" | "compartido",
              "P_ac_nom_W": float | None,
              "eta_inversor": float,
              "inversor": dict,           # ficha del catálogo (Vdc_max, Vmppt_*, ...)
          },
      },
      "superficies": {
          "<nombre>": {
              "nombre": str,
              "tipo": str,                # Fachada | Techo | Pérgola | Marquesina
              "tilt_deg": float,
              "azimuth_deg": float,
              "area_m2": float,
              "albedo": float,
              "bifacial": dict | None,
              "panel": dict,              # ficha SDM (MODULOS_BIPV)
              "n_serie": int,
              "n_paralelo": int,
              "inversor_id": str,
              "k_bipv": float,
              "p_shade": np.ndarray | None,   # FS_geometrico horario (8760,)
              "poa_df": pd.DataFrame | None,
              "resultados_dc": dict | None,   # de simular_bypass_horario
              "resultados_ac": dict | None,   # etapa inversor (por superficie)
              "huellas": dict,            # ver HUELLAS_CLAVES
          },
      },
      "resultados_bus": {"<inversor_id>": {...}},
      "agregados": {...} | None,
    }

Todas las funciones de transición devuelven una COPIA candidata (nunca mutan
el ``proyecto`` recibido) y, ante cualquier falla, devuelven el ``proyecto``
ORIGINAL sin cambios (regla 6: no se publica estado parcial).
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any, Mapping

import numpy as np
import pandas as pd

from calculos.dimensionamiento import evaluar_compatibilidad_string, evaluar_relacion_dc_ac
from calculos.mismatch_bypass import simular_bypass_horario
from calculos.multi_superficie import calcular_poa_superficie
from calculos.produccion_vigencia import fingerprint_mapping, huella_horaria_opcional

SCHEMA_VERSION = "bipv.transicion-multisuperficie.v1"
_HORAS_ANIO = 8760

# Claves de geometría que una transición de orientación/inclinación puede
# tocar. Cualquier otra clave (panel, n_serie, n_paralelo, inversor_id) queda
# fuera de ``geometria_nueva`` a propósito -- ver transicion_cambiar_geometria.
_CLAVES_GEOMETRIA = ("tilt_deg", "azimuth_deg", "area_m2", "albedo", "bifacial")

HUELLAS_CLAVES = (
    "geometria", "sombra", "poa", "panel", "inversor",
    "resultados_dc", "resultados_ac",
)


# ══════════════════════════════════════════════════════════════════════════
# 1. Huellas (fingerprints) -- regla 7
# ══════════════════════════════════════════════════════════════════════════
def calcular_huellas(superficie: Mapping[str, Any]) -> dict[str, str | None]:
    """Huellas de geometría, sombra, POA, panel, inversor y resultados.

    Reutiliza EXACTAMENTE las primitivas canónicas ya existentes en
    ``calculos.produccion_vigencia`` (``fingerprint_mapping`` para
    dicts/escalares, ``huella_horaria_opcional`` para series horarias
    ligadas a su índice de tiempo) -- el mismo módulo que ya usa Producción
    para ``produccion_run_signature_v1``/``bypass_run_signature_v1``. NO se
    reimplementa un segundo esquema de huellas: eso violaría la regla de
    "no calcular la misma magnitud de forma distinta" del Director
    (ver CodeSpecs/00-director/mapa-dependencias.md).

    ``huella_horaria_opcional`` exige un índice temporal real (no basta con
    los valores en bruto: dos series con los mismos números en horas
    distintas deben producir huellas distintas) -- por eso esta función
    solo puede firmar sombra/POA/resultados una vez que la superficie tiene
    ``_indice_horario`` (fijado por ``recalcular_fisica_superficie`` a
    partir de ``poa_df.index``). Antes de ese primer cálculo, esas tres
    huellas son ``None`` -- distinguible de "ya calculado y coincide".

    Pura: no consulta el proyecto ni ningún estado externo, solo el dict de
    la superficie. Se recalcula después de cada recomputo físico o de etapa
    de inversor -- es lo único que las pruebas usan para verificar qué
    cambió y qué se conservó exactamente (reglas 1, 2, 3 y 7).
    """
    indice = superficie.get("_indice_horario")
    poa_df = superficie.get("poa_df")
    poa_vals = poa_df["poa_global"].to_numpy() if isinstance(poa_df, pd.DataFrame) and not poa_df.empty else None

    resultados_dc = superficie.get("resultados_dc")
    dc_vals = resultados_dc.get("P_dc_kW") if resultados_dc else None

    resultados_ac = superficie.get("resultados_ac")
    ac_vals = resultados_ac.get("P_ac_kW") if resultados_ac else None

    con_indice = indice is not None
    return {
        "geometria": fingerprint_mapping({k: superficie.get(k) for k in _CLAVES_GEOMETRIA}),
        "sombra": huella_horaria_opcional(indice, superficie.get("p_shade")) if con_indice else None,
        "poa": huella_horaria_opcional(indice, poa_vals) if con_indice else None,
        "panel": fingerprint_mapping(superficie.get("panel")),
        "inversor": fingerprint_mapping({"inversor_id": superficie.get("inversor_id")}),
        "resultados_dc": huella_horaria_opcional(indice, dc_vals) if con_indice else None,
        "resultados_ac": huella_horaria_opcional(indice, ac_vals) if con_indice else None,
    }


# ══════════════════════════════════════════════════════════════════════════
# 2. Constructores
# ══════════════════════════════════════════════════════════════════════════
def _validar_serie_horaria(nombre: str, valores) -> np.ndarray:
    arr = np.asarray(valores, dtype=float)
    if arr.ndim != 1 or arr.shape[0] != _HORAS_ANIO:
        raise ValueError(
            f"{nombre} debe ser una serie horaria de {_HORAS_ANIO} valores; "
            f"se recibieron {arr.shape}."
        )
    if not np.isfinite(arr).all():
        raise ValueError(f"{nombre} contiene NaN o infinitos.")
    return arr


def _validar_p_shade(valores) -> np.ndarray:
    arr = _validar_serie_horaria("p_shade", valores)
    if (arr < 0.0).any() or (arr > 1.0).any():
        raise ValueError(
            "p_shade tiene valores fuera de [0, 1]; FS_geometrico debe ser "
            "0 = sin sombra … 1 = sombra total."
        )
    return arr


def superficie_nueva(
    nombre: str,
    tipo: str,
    tilt_deg: float,
    azimuth_deg: float,
    area_m2: float,
    panel: dict,
    n_serie: int,
    n_paralelo: int,
    inversor_id: str,
    p_shade: np.ndarray,
    albedo: float = 0.20,
    bifacial: dict | None = None,
    k_bipv: float = 1.0,
) -> dict:
    """Crea una superficie SIN resultados físicos todavía (estado inicial).

    Debe pasar por ``recalcular_fisica_superficie`` (y luego por
    ``recalcular_etapa_inversor_bus``) antes de tener POA/producción válidas.
    """
    sup = {
        "nombre": nombre,
        "tipo": tipo,
        "tilt_deg": float(tilt_deg),
        "azimuth_deg": float(azimuth_deg),
        "area_m2": float(area_m2),
        "albedo": float(albedo),
        "bifacial": bifacial,
        "panel": dict(panel),
        "n_serie": int(n_serie),
        "n_paralelo": int(n_paralelo),
        "inversor_id": inversor_id,
        "k_bipv": float(k_bipv),
        "p_shade": _validar_p_shade(p_shade),
        "poa_df": None,
        "resultados_dc": None,
        "resultados_ac": None,
    }
    sup["huellas"] = calcular_huellas(sup)
    return sup


def inversor_nuevo(
    inversor_id: str,
    tipo: str,
    eta_inversor: float,
    P_ac_nom_W: float | None,
    inversor: dict | None = None,
) -> dict:
    if tipo not in ("dedicado", "compartido"):
        raise ValueError(f"tipo de inversor no soportado: {tipo!r}")
    return {
        "inversor_id": inversor_id,
        "tipo": tipo,
        "eta_inversor": float(eta_inversor),
        "P_ac_nom_W": float(P_ac_nom_W) if P_ac_nom_W else None,
        "inversor": dict(inversor or {}),
    }


def proyecto_nuevo(inversores: list[dict], superficies: list[dict]) -> dict:
    proy = {
        "schema_version": SCHEMA_VERSION,
        "inversores": {inv["inversor_id"]: inv for inv in inversores},
        "superficies": {sup["nombre"]: sup for sup in superficies},
        "resultados_bus": {},
        "agregados": None,
    }
    ids_usados = {sup["inversor_id"] for sup in superficies}
    faltantes = ids_usados - set(proy["inversores"])
    if faltantes:
        raise ValueError(f"Superficies referencian inversores inexistentes: {faltantes}")
    return proy


# ══════════════════════════════════════════════════════════════════════════
# 3. Recomputo físico por superficie (geometría → POA → sombra → producción DC)
# ══════════════════════════════════════════════════════════════════════════
def recalcular_fisica_superficie(
    superficie: Mapping[str, Any],
    tmy: pd.DataFrame,
    lat: float,
    lon: float,
    alt_m: float,
) -> dict:
    """Recalcula POA (geometría real, pvlib) y producción DC con sombra/bypass.

    Usa EXCLUSIVAMENTE los motores físicos existentes -- nunca una
    multiplicación simplificada de POA (regla 8):
      - ``calculos.multi_superficie.calcular_poa_superficie`` (envuelve
        ``calculos.solar.calcular_poa``, pvlib real) para la geometría.
      - ``calculos.mismatch_bypass.simular_bypass_horario`` para el SDM,
        la temperatura de celda (NOCT + k_bipv) y el modelo de bypass diodes
        activado por sombra parcial.

    No toca el inversor: no aplica eficiencia ni recorte (Pnom) -- eso es
    ``recalcular_etapa_inversor_bus``, deliberadamente separado para que
    cambiar SOLO el inversor pueda reutilizar este resultado sin recalcularlo
    (regla 3: conserva geometría, sombras, POA e IAM).

    Devuelve una COPIA nueva de la superficie; no muta el argumento.
    """
    panel = superficie.get("panel") or {}
    if "NOCT" not in panel:
        raise ValueError(
            f"Panel de la superficie '{superficie.get('nombre')}' no declara "
            "NOCT; no se usan defaults silenciosos (mismo criterio que "
            "calculos.ejecutor_escenarios)."
        )
    if not isinstance(tmy, pd.DataFrame) or "T2m" not in tmy.columns:
        raise ValueError("El TMY debe ser un DataFrame con columna T2m.")
    if len(tmy.index) != _HORAS_ANIO:
        raise ValueError("El TMY debe tener exactamente 8760 registros horarios.")

    p_shade = _validar_p_shade(superficie["p_shade"])
    t_amb = _validar_serie_horaria("T2m", tmy["T2m"].to_numpy(dtype=float))

    poa_df = calcular_poa_superficie(
        tmy, lat, lon, alt_m, superficie,
        albedo=superficie.get("albedo", 0.20),
        bifacial=superficie.get("bifacial"),
    )
    if poa_df is None or poa_df.empty or "poa_global" not in poa_df.columns:
        raise ValueError(
            f"calcular_poa_superficie no produjo POA válida para "
            f"'{superficie.get('nombre')}' (geometría/TMY inconsistentes)."
        )
    G_eff = _validar_serie_horaria("poa_global", poa_df["poa_global"].to_numpy())

    bypass = simular_bypass_horario(
        G_eff=G_eff,
        T_amb=t_amb,
        p_shade=p_shade,
        N_series=int(superficie["n_serie"]),
        N_parallel=int(superficie["n_paralelo"]),
        panel=dict(panel),
        NOCT=float(panel["NOCT"]),
        k_bipv=float(superficie.get("k_bipv", 1.0)),
    )

    nueva = copy.deepcopy(dict(superficie))
    nueva["p_shade"] = p_shade
    nueva["poa_df"] = poa_df
    nueva["_indice_horario"] = poa_df.index
    nueva["resultados_dc"] = {
        "P_dc_kW": np.asarray(bypass["P_dc_kW"], dtype=float),
        "P_bypass_loss_kW": np.asarray(bypass["P_bypass_loss_kW"], dtype=float),
        "kwh_bypass_anual": bypass["kwh_bypass_anual"],
        "horas_bypass": bypass["horas_bypass"],
        "horas_sombra": bypass["horas_sombra"],
        "E_dc_anual_kWh": round(float(np.sum(bypass["P_dc_kW"])), 1),
        "poa_anual_kWh_m2": round(float(G_eff.sum()) / 1000.0, 2),
    }
    # La etapa de inversor queda obsoleta -- se recalcula aparte
    # (recalcular_etapa_inversor_bus), nunca se reutiliza un P_ac de la POA
    # anterior.
    nueva["resultados_ac"] = None
    nueva["huellas"] = calcular_huellas(nueva)
    return nueva


# ══════════════════════════════════════════════════════════════════════════
# 4. Etapa de inversor (compatibilidad + clipping, dedicado o compartido)
# ══════════════════════════════════════════════════════════════════════════
def recalcular_etapa_inversor_bus(proyecto: Mapping[str, Any], inversor_id: str) -> dict:
    """Recalcula compatibilidad eléctrica, clipping y producción AC de un bus.

    Un inversor "dedicado" es, en este modelo, un bus con exactamente una
    superficie asignada -- usa el MISMO código que uno "compartido" (regla
    4 y 5 se resuelven con una sola implementación): se suma la potencia DC
    horaria de TODAS las superficies del bus (1 o más) y el límite AC del
    inversor (``P_ac_nom_W``) se aplica UNA SOLA VEZ sobre esa suma, nunca
    superficie por superficie.

    No toca ``resultados_dc`` de ninguna superficie (regla 3: la POA y la
    sombra no cambian al cambiar de inversor). Devuelve una COPIA del
    proyecto; no muta el argumento.
    """
    proy = copy.deepcopy(dict(proyecto))
    if inversor_id not in proy["inversores"]:
        raise ValueError(f"Inversor desconocido: {inversor_id!r}")
    inversor_cfg = proy["inversores"][inversor_id]
    eta = float(inversor_cfg["eta_inversor"])
    if not 0.0 < eta <= 1.0:
        raise ValueError(f"eta_inversor fuera de rango (0, 1]: {eta!r}")
    P_ac_nom_W = inversor_cfg.get("P_ac_nom_W")

    nombres_bus = [
        nombre for nombre, sup in proy["superficies"].items()
        if sup.get("inversor_id") == inversor_id
    ]
    if not nombres_bus:
        raise ValueError(f"Ninguna superficie está asignada al inversor {inversor_id!r}.")
    if inversor_cfg["tipo"] == "dedicado" and len(nombres_bus) != 1:
        raise ValueError(
            f"Inversor {inversor_id!r} está marcado 'dedicado' pero tiene "
            f"{len(nombres_bus)} superficies asignadas; un dedicado es exactamente 1."
        )

    P_dc_por_superficie: dict[str, np.ndarray] = {}
    for nombre in nombres_bus:
        sup = proy["superficies"][nombre]
        resultados_dc = sup.get("resultados_dc")
        if not resultados_dc or "P_dc_kW" not in resultados_dc:
            raise ValueError(
                f"Superficie '{nombre}' no tiene producción DC calculada "
                "-- ejecuta recalcular_fisica_superficie() antes de la etapa "
                "de inversor."
            )
        P_dc_por_superficie[nombre] = _validar_serie_horaria(
            f"P_dc_kW[{nombre}]", resultados_dc["P_dc_kW"]
        )

    # ── Suma horaria del bus ANTES de recortar (regla 5) ──────────────────
    P_dc_bus_kW = np.sum(np.stack(list(P_dc_por_superficie.values())), axis=0)
    P_ac_sin_recorte_kW = P_dc_bus_kW * eta
    if P_ac_nom_W:
        P_ac_kW = np.minimum(P_ac_sin_recorte_kW, P_ac_nom_W / 1000.0)
    else:
        P_ac_kW = P_ac_sin_recorte_kW
    clipping_kW = P_ac_sin_recorte_kW - P_ac_kW

    resultado_bus = {
        "inversor_id": inversor_id,
        "tipo": inversor_cfg["tipo"],
        "superficies": list(nombres_bus),
        "E_dc_anual_kWh": round(float(P_dc_bus_kW.sum()), 1),
        "E_ac_anual_kWh": round(float(P_ac_kW.sum()), 1),
        "perdida_clipping_kWh": round(float(clipping_kW.sum()), 1),
        "horas_con_clipping": int(np.sum(clipping_kW > 1e-6)),
        "P_ac_nom_W": P_ac_nom_W,
        "eta_inversor": eta,
    }

    # ── Reparto proporcional a cada superficie (para reportes/finanzas
    #    por superficie) -- share = su P_dc / P_dc del bus, hora a hora,
    #    aplicado sobre P_ac_kW ya recortada. Con un bus dedicado (1
    #    superficie) el share es exactamente 1.0 en toda hora con DC>0. ────
    P_dc_bus_seguro = np.where(P_dc_bus_kW > 1e-9, P_dc_bus_kW, np.nan)
    for nombre in nombres_bus:
        sup = proy["superficies"][nombre]
        panel = sup["panel"]
        share = np.nan_to_num(P_dc_por_superficie[nombre] / P_dc_bus_seguro, nan=0.0)
        P_ac_superficie_kW = P_ac_kW * share

        # Spec 03/diseno-electrico-multisuperficie (fase A2): con las
        # temperaturas de diseño del proyecto si el proyecto las trae.
        temps = proy.get("temperaturas_diseno") or {}
        compat = evaluar_compatibilidad_string(
            panel=panel, inversor=inversor_cfg.get("inversor", {}),
            N_serie=int(sup["n_serie"]),
            **({"T_frio": float(temps["T_frio"]), "T_real": float(temps["T_real"]),
                "T_extremo": float(temps["T_extremo"])} if temps else {}),
        )
        P_dc_stc_kW = float(panel.get("Pmax_stc", 0.0)) * int(sup["n_serie"]) * int(sup["n_paralelo"]) / 1000.0
        relacion_dc_ac = evaluar_relacion_dc_ac(P_dc_stc_kW, P_ac_nom_W)

        sup["resultados_ac"] = {
            "P_ac_kW": np.asarray(P_ac_superficie_kW, dtype=float),
            "E_ac_anual_kWh": round(float(P_ac_superficie_kW.sum()), 1),
            "share_bus_anual": round(float(np.nansum(P_dc_por_superficie[nombre]) / max(P_dc_bus_kW.sum(), 1e-9)), 4),
            "compatibilidad_electrica": compat,
            "relacion_dc_ac": relacion_dc_ac,
            "P_dc_stc_kW": round(P_dc_stc_kW, 3),
        }
        sup["huellas"] = calcular_huellas(sup)
        proy["superficies"][nombre] = sup

    proy["resultados_bus"][inversor_id] = resultado_bus
    return proy


def recalcular_agregados_proyecto(proyecto: Mapping[str, Any]) -> dict:
    """Suma de todos los buses -- energía y área totales del proyecto."""
    e_ac_total = sum(b["E_ac_anual_kWh"] for b in proyecto["resultados_bus"].values())
    e_dc_total = sum(b["E_dc_anual_kWh"] for b in proyecto["resultados_bus"].values())
    area_total = sum(float(s["area_m2"]) for s in proyecto["superficies"].values())
    return {
        "E_ac_total_kWh": round(e_ac_total, 1),
        "E_dc_total_kWh": round(e_dc_total, 1),
        "area_total_m2": round(area_total, 1),
        "n_superficies": len(proyecto["superficies"]),
        "n_inversores": len(proyecto["inversores"]),
        "huella": fingerprint_mapping({
            nombre: sup["huellas"] for nombre, sup in sorted(proyecto["superficies"].items())
        }),
    }


# ══════════════════════════════════════════════════════════════════════════
# 5. Verificación de invariantes (regla 1, 2, 3: qué se conserva)
# ══════════════════════════════════════════════════════════════════════════
def _huellas_proyecto(proyecto: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    return {nombre: dict(sup["huellas"]) for nombre, sup in proyecto["superficies"].items()}


def _verificar_conservacion(
    huellas_antes: Mapping[str, Mapping[str, str]],
    proyecto_despues: Mapping[str, Any],
    *,
    superficies_pueden_cambiar: set[str],
    claves_que_deben_conservarse: tuple[str, ...],
) -> None:
    """Lanza ValueError si una superficie fuera del alcance de la transición
    cambió, o si una superficie dentro del alcance perdió una huella que la
    regla exige conservar (p. ej. POA al cambiar solo el inversor)."""
    for nombre, huellas_antes_sup in huellas_antes.items():
        sup_despues = proyecto_despues["superficies"].get(nombre)
        if sup_despues is None:
            raise ValueError(f"La superficie '{nombre}' desapareció durante la transición.")
        huellas_despues_sup = sup_despues["huellas"]
        if nombre not in superficies_pueden_cambiar:
            if huellas_antes_sup != huellas_despues_sup:
                raise ValueError(
                    f"La superficie '{nombre}' cambió sin estar en el alcance "
                    "de la transición -- se aborta para no publicar un "
                    "estado con identidad de superficies corrompida."
                )
            continue
        for clave in claves_que_deben_conservarse:
            if huellas_antes_sup[clave] != huellas_despues_sup[clave]:
                raise ValueError(
                    f"La superficie '{nombre}' cambió su huella de "
                    f"'{clave}', que esta transición debía conservar."
                )


# ══════════════════════════════════════════════════════════════════════════
# 6. Transiciones transaccionales (reglas 1, 2, 3, 6)
# ══════════════════════════════════════════════════════════════════════════
def transicion_cambiar_geometria(
    proyecto: Mapping[str, Any],
    nombre_superficie: str,
    geometria_nueva: Mapping[str, Any],
    p_shade_nuevo,
    tmy: pd.DataFrame,
    lat: float,
    lon: float,
    alt_m: float,
) -> dict:
    """Cambia orientación/inclinación (y/o área/albedo/bifacial) de UNA
    superficie, conservando panel, strings, inversor y las demás superficies.

    ``geometria_nueva`` solo puede tocar ``_CLAVES_GEOMETRIA``; cualquier otra
    clave (panel, n_serie, n_paralelo, inversor_id) se rechaza explícitamente
    -- esta transición no cambia identidad eléctrica.

    ``p_shade_nuevo`` es OBLIGATORIO: cambiar tilt/azimuth cambia el horizonte
    real que ve la superficie, así que esta función nunca reutiliza en
    silencio la sombra de la geometría anterior -- el caller debe recalcular
    la máscara de sombreado (motor de sombras 3D / horizonte) para la nueva
    geometría y pasarla aquí. No inventar geometría de sombra en este módulo.

    Devuelve
    --------
    dict con ``ok`` (bool). Si ``ok`` es True: ``proyecto`` (candidato nuevo),
    ``recalculado`` (lista de claves), ``conservado`` (lista de superficies
    intactas). Si ``ok`` es False: ``proyecto`` es el ORIGINAL sin cambios y
    ``error`` describe el motivo (regla 6: rollback completo).
    """
    if nombre_superficie not in proyecto["superficies"]:
        return {"ok": False, "proyecto": proyecto, "error": f"Superficie desconocida: {nombre_superficie!r}"}

    claves_invalidas = set(geometria_nueva) - set(_CLAVES_GEOMETRIA)
    if claves_invalidas:
        return {
            "ok": False, "proyecto": proyecto,
            "error": f"geometria_nueva no puede tocar: {sorted(claves_invalidas)}",
        }

    huellas_antes = _huellas_proyecto(proyecto)
    candidato = copy.deepcopy(dict(proyecto))
    try:
        sup = candidato["superficies"][nombre_superficie]
        sup.update(dict(geometria_nueva))
        sup["p_shade"] = _validar_p_shade(p_shade_nuevo)

        nueva_sup = recalcular_fisica_superficie(sup, tmy, lat, lon, alt_m)
        candidato["superficies"][nombre_superficie] = nueva_sup

        inversor_id = nueva_sup["inversor_id"]
        candidato = recalcular_etapa_inversor_bus(candidato, inversor_id)
        candidato["agregados"] = recalcular_agregados_proyecto(candidato)

        bus_afectado = set(candidato["resultados_bus"][inversor_id]["superficies"])
        _verificar_conservacion(
            huellas_antes, candidato,
            superficies_pueden_cambiar=bus_afectado,
            claves_que_deben_conservarse=(),  # dentro del bus SÍ cambia todo
        )
    except Exception as exc:  # noqa: BLE001 -- frontera transaccional explícita
        return {"ok": False, "proyecto": proyecto, "error": str(exc)}

    otras = [n for n in proyecto["superficies"] if n not in candidato["resultados_bus"][nueva_sup["inversor_id"]]["superficies"]]
    return {
        "ok": True,
        "proyecto": candidato,
        "recalculado": [nombre_superficie, f"bus:{inversor_id}", "agregados"],
        "conservado": otras,
    }


def transicion_cambiar_inversor(
    proyecto: Mapping[str, Any],
    inversor_id: str,
    inversor_nuevo_cfg: Mapping[str, Any],
) -> dict:
    """Cambia la configuración de UN inversor (dedicado o bus compartido),
    conservando geometría, sombras, POA e IAM de TODAS las superficies.

    ``inversor_nuevo_cfg`` puede traer ``eta_inversor``, ``P_ac_nom_W``,
    ``tipo`` y/o ``inversor`` (ficha del catálogo); las claves ausentes
    conservan el valor anterior del inversor.

    Recalcula compatibilidad eléctrica, clipping, producción AC y agregados
    del proyecto para el bus afectado. NUNCA vuelve a llamar
    ``recalcular_fisica_superficie`` -- si esta función necesitara tocar
    ``resultados_dc``, se considera un error de programación y debe fallar
    (ver verificación de conservación más abajo), no degradar en silencio a
    recalcular la física completa.
    """
    if inversor_id not in proyecto["inversores"]:
        return {"ok": False, "proyecto": proyecto, "error": f"Inversor desconocido: {inversor_id!r}"}

    huellas_antes = _huellas_proyecto(proyecto)
    candidato = copy.deepcopy(dict(proyecto))
    try:
        candidato["inversores"][inversor_id] = {
            **candidato["inversores"][inversor_id],
            **{k: v for k, v in inversor_nuevo_cfg.items() if k != "inversor_id"},
        }
        candidato = recalcular_etapa_inversor_bus(candidato, inversor_id)
        candidato["agregados"] = recalcular_agregados_proyecto(candidato)

        bus_afectado = set(candidato["resultados_bus"][inversor_id]["superficies"])
        # Dentro del bus afectado, geometría/sombra/POA/panel/resultados_dc
        # deben conservarse EXACTOS -- solo cambian inversor y resultados_ac.
        _verificar_conservacion(
            huellas_antes, candidato,
            superficies_pueden_cambiar=bus_afectado,
            claves_que_deben_conservarse=("geometria", "sombra", "poa", "panel", "resultados_dc"),
        )
        # Fuera del bus afectado, nada debe cambiar en absoluto.
        _verificar_conservacion(
            {k: v for k, v in huellas_antes.items() if k not in bus_afectado},
            candidato,
            superficies_pueden_cambiar=set(),
            claves_que_deben_conservarse=(),
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "proyecto": proyecto, "error": str(exc)}

    return {
        "ok": True,
        "proyecto": candidato,
        "recalculado": [f"bus:{inversor_id}", "agregados"],
        "conservado": [n for n in proyecto["superficies"] if n not in bus_afectado],
        "informes_obsoletos": True,
        "financiero_co2_obsoletos": True,
    }


# ══════════════════════════════════════════════════════════════════════════
# 7. Puente a Finanzas/CO₂ existentes (no reemplaza esos motores)
# ══════════════════════════════════════════════════════════════════════════
def recalcular_financiero_co2(agregados: Mapping[str, Any], parametros_financieros: Mapping[str, Any], parametros_co2: Mapping[str, Any]) -> dict:
    """Reejecuta Financiero y CO₂ EXISTENTES con la energía agregada nueva.

    No reimplementa esos motores: llama ``calculos.financiero.
    calcular_flujo_caja`` + ``calcular_metricas`` y ``calculos.co2.
    emisiones_evitadas`` con los mismos parámetros de negocio que ya usa la
    app, sustituyendo únicamente ``e_ac_kWh_anual`` por
    ``agregados['E_ac_total_kWh']``.
    """
    from calculos import co2 as co2_mod
    from calculos.financiero import calcular_flujo_caja, calcular_metricas

    e_ac_total = float(agregados["E_ac_total_kWh"])
    tasa_descuento = parametros_financieros["tasa_descuento"]
    kwargs_flujo = {k: v for k, v in parametros_financieros.items() if k != "tasa_descuento"}
    flujos = calcular_flujo_caja(e_ac_kWh_anual=e_ac_total, **kwargs_flujo)
    metricas = calcular_metricas(
        flujos=flujos,
        tasa_descuento=tasa_descuento,
        capex_usd=parametros_financieros["capex_usd"],
        e_ac_kWh_anual=e_ac_total,
        tipo_cambio=parametros_financieros["tipo_cambio"],
    )
    _, e_ac_anual_array = co2_mod.produccion_anual_con_degradacion(
        e_ac=e_ac_total,
        tasa_deg_pct=parametros_co2.get(
            "tasa_degradacion_pct", parametros_financieros.get("tasa_degradacion_pct", 0.5)
        ),
        n_anos=parametros_co2.get("n_anos", parametros_financieros.get("n_anos", 25)),
    )
    co2_resultado = co2_mod.emisiones_evitadas(
        e_ac=e_ac_total,
        e_ac_anual=e_ac_anual_array,
        factor_activo=parametros_co2["factor_activo"],
        factor_promedio=parametros_co2["factor_promedio"],
        factor_marginal=parametros_co2["factor_marginal"],
    )
    return {"flujos": flujos, "metricas": metricas, "co2": co2_resultado, "E_ac_total_kWh": e_ac_total}
