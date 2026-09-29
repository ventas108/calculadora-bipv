"""Cadena de pérdidas de cada superficie del sistema multi-superficie.

Spec ``CodeSpecs/05-perdidas-y-temperatura/cadena-perdidas-multisuperficie``.

Hasta el 27-sep-2026 la energía de 🗺️ Vista 3D era POA × área × η × 0,78: el
0,78 no lo escribía ninguna página (hallazgo H2) y lo calculado en 🔆 Motor
Óptico y 🔀 Mismatch no llegaba a Financiero. Aquí el PR de cada superficie
sale de la misma física que usa 📊 Producción, con la geometría, el panel y
el montaje de esa superficie:

    PR = f_iam · f_suciedad · f_térmico · f_mismatch_fab · f_cable_dc
         · f_cable_ac · η_inversor · f_sombra_horizonte

- Óptica: ``motor_optico.cascada_optica`` con la POA de la superficie
  (IAM directa + difusa y suciedad; la suciedad vertical usa
  ``k_soiling_vert`` solo si la superficie es vertical).
- Temperatura, poca luz, mismatch, cables e inversor: el MISMO motor de
  📊 Producción (``produccion.simular_produccion_anual``, SDM del panel = 🔬
  Motor IV, T celda NOCT + ``k_bipv`` del montaje de la superficie) con la POA
  óptica de la superficie. Así el simplificado coincide con Producción para la
  misma geometría. Una fórmula lineal con γ sobreestimaba 11 % una fachada
  vertical de CdTe (rinde menos con poca luz); solo se usa si el panel no
  tiene SDM completo, y se avisa.
- Transparencia: NO se aplica; η de la superficie ya es η de módulo
  (Pmax / área del módulo), así que contarla sería doble conteo.
- Eléctricas: los porcentajes de 🔀 Mismatch (o sus valores por defecto).
- Sombra de horizonte: ``factor_sombra_anual`` de 🔀 Mismatch, solo en el
  origen simplificado (bypass y físico ya modelan su sombra).
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from calculos.mismatch import pct_perdida_modulos
from calculos.motor_optico import K_BIPV_POR_MONTAJE, SOILING_COLOMBIA, cascada_optica

VERSION_CADENA = "cadena_perdidas_v1"
CLAVE_PUBLICACION = "multisup_cadena_perdidas"

# Montaje térmico por defecto de cada tipo de superficie de Vista 3D (mismo
# criterio que motor_optico.indice_montaje_default para los tipos de proyecto).
K_BIPV_POR_TIPO = {"Fachada": 1.3, "Techo": 1.0, "Pérgola": 1.15, "Marquesina": 1.15}
MONTAJE_AUTOMATICO = "Automático según el tipo de superficie"
OPCIONES_MONTAJE = [MONTAJE_AUTOMATICO] + list(K_BIPV_POR_MONTAJE)

# Vidrio por defecto según la tecnología del panel (motor_optico.B0_POR_VIDRIO).
B0_CDTE = 0.12
B0_ESTANDAR = 0.05
F_IAM_DIF_DEFECTO = 0.95
K_SOILING_VERT_DEFECTO = 0.65
TILT_VERTICAL = 75.0

# Valores por defecto de los campos de 🔀 Mismatch (mismas cifras que sus sliders).
PCT_MISMATCH_FAB_DEFECTO = 1.0
PCT_CABLE_DC_DEFECTO = 1.5
PCT_CABLE_AC_DEFECTO = 0.0


def k_bipv_superficie(superficie: Mapping[str, Any]) -> float:
    """``k_bipv`` elegido para la superficie, o el de su tipo."""
    montaje = superficie.get("k_bipv_montaje")
    if montaje in K_BIPV_POR_MONTAJE:
        return float(K_BIPV_POR_MONTAJE[montaje])
    return float(K_BIPV_POR_TIPO.get(str(superficie.get("tipo")), 1.0))


def _num(valor: Any, defecto: float) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return defecto
    return numero if np.isfinite(numero) else defecto


def parametros_cadena(estado: Mapping[str, Any]) -> dict:
    """Parámetros comunes de la cadena y de dónde salen."""
    motor_ok = bool(estado.get("motor_optico_ok"))
    mismatch_ok = bool(estado.get("mismatch_ok"))
    soiling = estado.get("motor_optico_soiling_config") if motor_ok else None
    return {
        "motor_optico": motor_ok,
        "mo_panel_ref": estado.get("mo_panel_ref") if motor_ok else None,
        "mo_b0": _num(estado.get("motor_optico_b0"), B0_ESTANDAR) if motor_ok else None,
        "f_iam_dif": _num(estado.get("motor_optico_f_iam_dif"), F_IAM_DIF_DEFECTO) if motor_ok else F_IAM_DIF_DEFECTO,
        "soiling_config": dict(soiling) if isinstance(soiling, Mapping) else dict(SOILING_COLOMBIA),
        "k_soiling_vert": _num(estado.get("motor_optico_k_soil_vert"), K_SOILING_VERT_DEFECTO) if motor_ok else K_SOILING_VERT_DEFECTO,
        "mismatch": mismatch_ok,
        # Calidad del módulo + mismatch combinados (Spec 05/calidad-y-mismatch).
        "pct_mismatch_fab": pct_perdida_modulos(
            _num(estado.get("pct_calidad_modulo"), 0.0),
            _num(estado.get("pct_mismatch_fab"), PCT_MISMATCH_FAB_DEFECTO),
        ),
        "pct_cable_dc": _num(estado.get("pct_cableado_dc"), PCT_CABLE_DC_DEFECTO),
        "pct_cable_ac": _num(estado.get("pct_cableado_ac"), PCT_CABLE_AC_DEFECTO),
        "f_sombra_horizonte": (1.0 - _num(estado.get("factor_sombra_anual"), 0.0)) if mismatch_ok else 1.0,
    }


def b0_superficie(panel: Mapping[str, Any], nombre_panel: str | None, parametros: Mapping[str, Any]) -> float:
    """b0 del vidrio: el de 🔆 Motor Óptico si se corrió con este panel; si no, por tecnología."""
    if parametros.get("mo_b0") is not None and nombre_panel and nombre_panel == parametros.get("mo_panel_ref"):
        return float(parametros["mo_b0"])
    return B0_CDTE if "cdte" in str(panel.get("tecnologia", "")).lower() else B0_ESTANDAR


def _factor(numerador: float, denominador: float) -> float:
    return float(numerador / denominador) if denominador > 0 else 1.0


def cadena_superficie(poa_df: pd.DataFrame, tmy_df: pd.DataFrame, panel: Mapping[str, Any], *,
                      nombre_panel: str | None, tilt_deg: float, k_bipv: float,
                      eta_inversor: float, parametros: Mapping[str, Any],
                      aplicar_horizonte: bool = True, n_modulos: int = 1) -> dict:
    """Factores de pérdida y PR de una superficie (8760 h)."""
    if poa_df is None or poa_df.empty or "poa_global" not in poa_df.columns:
        raise ValueError("La superficie no tiene POA horaria.")
    if tmy_df is None or "T2m" not in getattr(tmy_df, "columns", []):
        raise ValueError("Falta el TMY con temperatura (T2m) de ☀️ Recurso Solar.")
    if "NOCT" not in panel or panel.get("Tk_gamma") is None:
        raise ValueError("El panel no declara NOCT y coeficiente de temperatura (γ).")
    if not 0.0 < eta_inversor <= 1.0:
        raise ValueError(f"η del inversor fuera de (0, 1]: {eta_inversor!r}")
    n_modulos = max(int(n_modulos or 1), 1)

    vertical = float(tilt_deg) >= TILT_VERTICAL
    b0 = b0_superficie(panel, nombre_panel, parametros)
    if len(tmy_df.index) != len(poa_df.index):
        raise ValueError("El TMY y la POA de la superficie no tienen las mismas horas.")
    tmy = tmy_df.copy()
    tmy.index = poa_df.index
    res, _ = cascada_optica(
        tmy, poa_df, b0=b0, noct=float(panel["NOCT"]),
        coef_temp=float(panel["Tk_gamma"]) / 100.0, k_bipv=float(k_bipv),
        soiling_config=parametros["soiling_config"], f_iam_dif=float(parametros["f_iam_dif"]),
        transparencia=0.0, k_soiling_vert=float(parametros["k_soiling_vert"]) if vertical else 1.0,
    )
    bruta = float(res["poa_bruta"].sum())
    optica = float(res["poa_optica"].sum())
    post_soil = float(res["poa_post_soil"].sum())
    post_term = float(res["poa_post_term"].sum())
    f_iam = _factor(optica, bruta)
    f_soiling = _factor(post_soil, optica)
    f_termico = _factor(post_term, post_soil)
    f_mismatch = 1.0 - float(parametros["pct_mismatch_fab"]) / 100.0
    f_cables = (1.0 - float(parametros["pct_cable_dc"]) / 100.0) * (1.0 - float(parametros["pct_cable_ac"]) / 100.0)
    f_sombra = float(parametros["f_sombra_horizonte"]) if aplicar_horizonte else 1.0
    from calculos.produccion import panel_tiene_sdm_completo, simular_produccion_anual
    modelo = "SDM" if panel_tiene_sdm_completo(dict(panel)) else "gamma_lineal"
    if modelo == "SDM":
        poa_st = poa_df.copy()
        poa_st["poa_global"] = res["poa_post_soil"].to_numpy(dtype=float)
        prod = simular_produccion_anual(
            tmy, poa_st, dict(panel), n_modulos, float(eta_inversor), f_sombra,
            k_bipv=float(k_bipv), poa_bruta_kWh_m2=bruta / 1000.0,
            pct_mismatch_fab=float(parametros["pct_mismatch_fab"]),
            pct_cableado_dc=float(parametros["pct_cable_dc"]),
            pct_cableado_ac=float(parametros["pct_cable_ac"]),
        )
        base = bruta / 1000.0 * n_modulos * float(panel["Pmax_stc"]) / 1000.0
        pr = float(prod["E_ac_anual_kWh"]) / base if base > 0 else 0.0
        resto = f_iam * f_soiling * f_mismatch * f_cables * float(eta_inversor) * f_sombra
        f_termico = pr / resto if resto > 0 else 1.0     # temperatura y poca luz (SDM)
    else:
        pr = f_iam * f_soiling * f_termico * f_mismatch * f_cables * float(eta_inversor) * f_sombra
    for nombre, valor in (("f_iam", f_iam), ("f_soiling", f_soiling), ("f_termico", f_termico),
                          ("f_mismatch", f_mismatch), ("f_cables", f_cables), ("f_sombra", f_sombra),
                          ("PR", pr)):
        if not 0.0 < valor <= 1.0 + 1e-9:
            raise ValueError(f"{nombre} fuera de (0, 1]: {valor:.4f}")
    return {
        "b0": b0, "k_bipv": float(k_bipv), "vertical": vertical, "modelo": modelo,
        "f_iam": f_iam, "f_soiling": f_soiling, "f_termico": f_termico,
        "f_mismatch": f_mismatch, "f_cables": f_cables, "eta_inversor": float(eta_inversor),
        "f_sombra": f_sombra, "pr": pr,
        "poa_bruta_kWh_m2": bruta / 1000.0,
        "poa_sin_termico": res["poa_post_soil"],
    }


def eta_inversor_superficie(superficie: Mapping[str, Any], inversores: list[Mapping[str, Any]]) -> float:
    """η de los inversores de la superficie, ponderada por módulos de cada grupo."""
    etas = {str(i.get("inversor_id")): _num(i.get("eta_inversor"), 0.97) for i in inversores or []}
    grupos = superficie.get("grupos") or []
    total = peso = 0.0
    for g in grupos:
        n = max(int(g.get("n_serie") or 0) * int(g.get("n_paralelo") or 0), 0)
        eta = etas.get(str(g.get("inversor_id")))
        if n and eta:
            total += n * eta
            peso += n
    if peso > 0:
        return total / peso
    return float(np.mean(list(etas.values()))) if etas else 0.97


def firma_cadena(parametros: Mapping[str, Any], superficies: list[Mapping[str, Any]]) -> str:
    """Huella de lo que decide la cadena: si cambia, la energía publicada quedó vieja."""
    datos = {
        "version": VERSION_CADENA,
        "parametros": {k: v for k, v in parametros.items()},
        "superficies": sorted(
            (str(s.get("nombre")), k_bipv_superficie(s), str(s.get("tipo")))
            for s in superficies if s.get("activa", True)
        ),
    }
    # Solo si hay strings que cruzan: las firmas guardadas sin cruces no cambian.
    from calculos.cruce_superficies import cruces_del_proyecto
    cruces = cruces_del_proyecto(list(superficies))
    if cruces:
        datos["cruces"] = cruces
    return hashlib.sha256(json.dumps(datos, sort_keys=True, default=str).encode("utf-8")).hexdigest()


CLAVE_CACHE = "_cadena_perdidas_cache"


def _huella_entrada(poa_df: pd.DataFrame, tmy_df: pd.DataFrame, *partes: Any) -> str:
    h = hashlib.sha256()
    for col in ("poa_global", "poa_direct", "poa_sky_diffuse", "poa_ground_diffuse"):
        if col in poa_df.columns:
            h.update(np.ascontiguousarray(poa_df[col].to_numpy(dtype=float)).tobytes())
    h.update(np.ascontiguousarray(tmy_df["T2m"].to_numpy(dtype=float)).tobytes())
    h.update(json.dumps(partes, sort_keys=True, default=str).encode("utf-8"))
    return h.hexdigest()


def cadena_superficies_estado(estado: Mapping[str, Any], superficies_energia: list[Mapping[str, Any]],
                              poas: Mapping[str, pd.DataFrame], paneles: Mapping[str, Mapping[str, Any]],
                              *, aplicar_horizonte: bool = True) -> tuple[dict, dict]:
    """``({nombre: resultado}, {nombre: error})`` para las superficies con POA y panel."""
    parametros = parametros_cadena(estado)
    tmy = estado.get("tmy_df")
    inversores = list(estado.get("multisup_inversores") or [])
    resultados, errores = {}, {}
    for sup in superficies_energia:
        nombre = sup["nombre"]
        poa = poas.get(nombre)
        info = paneles.get(nombre)
        if poa is None or info is None:
            continue
        try:
            argumentos = dict(
                nombre_panel=info.get("nombre"), tilt_deg=float(sup["tilt_deg"]),
                k_bipv=k_bipv_superficie(sup), eta_inversor=eta_inversor_superficie(sup, inversores),
                parametros=parametros, aplicar_horizonte=aplicar_horizonte,
                n_modulos=int(sup.get("modulos") or 1),
            )
            clave = _huella_entrada(poa, tmy, dict(info["panel"]), argumentos)
            cache = estado.get(CLAVE_CACHE) if isinstance(estado, dict) or hasattr(estado, "__setitem__") else None
            if not isinstance(cache, dict):
                cache = {}
                try:
                    estado[CLAVE_CACHE] = cache
                except TypeError:
                    pass
            if clave not in cache:
                if len(cache) > 64:
                    cache.clear()
                cache[clave] = cadena_superficie(poa, tmy, dict(info["panel"]), **argumentos)
            resultados[nombre] = cache[clave]
        except (ValueError, KeyError, TypeError) as error:
            errores[nombre] = str(error)
    # Strings que cruzan a otra superficie (Spec 05/string-cruza-superficies):
    # la pérdida en serie del string, hora a hora con diodos de bypass, baja
    # el PR de sus módulos en las dos superficies. Sin cruces no cambia nada.
    from calculos.cruce_superficies import factores_cruce
    for nombre, f in factores_cruce(superficies_energia, poas).items():
        if f.get("error"):
            errores[nombre] = f["error"]
            resultados.pop(nombre, None)
            continue
        if nombre in resultados:
            r = dict(resultados[nombre])
            r["pr"] = float(r["pr"]) * f["f_cruce"]
            r["f_cruce"] = f["f_cruce"]
            r["cruce_detalle"] = f["detalle"]
            resultados[nombre] = r
    return resultados, errores


def pr_por_superficie(resultados: Mapping[str, Mapping[str, Any]]) -> dict[str, float]:
    return {nombre: float(r["pr"]) for nombre, r in resultados.items()}


def tabla_desglose(resultados: Mapping[str, Mapping[str, Any]]) -> list[dict]:
    """Filas para mostrar de dónde sale el PR de cada superficie."""
    filas = []
    for nombre, r in resultados.items():
        filas.append({
            "Superficie": nombre,
            "IAM (ángulo)": f"{(1 - r['f_iam']) * 100:.1f} %",
            "Suciedad": f"{(1 - r['f_soiling']) * 100:.1f} %",
            ("Temperatura y poca luz (SDM)" if r.get("modelo") == "SDM" else "Temperatura (γ lineal)"):
                f"{(1 - r['f_termico']) * 100:.1f} % (k_BIPV {r['k_bipv']:.2f})",
            "Mismatch": f"{(1 - r['f_mismatch']) * 100:.1f} %",
            "Cables": f"{(1 - r['f_cables']) * 100:.1f} %",
            "Inversor": f"{(1 - r['eta_inversor']) * 100:.1f} %",
            "Sombra horizonte": f"{(1 - r['f_sombra']) * 100:.1f} %",
            **({"String que cruza": f"{(1 - r['f_cruce']) * 100:.1f} %"} if "f_cruce" in r else {}),
            "PR": f"{r['pr']:.3f}",
        })
    return filas


def aviso_origen_parametros(parametros: Mapping[str, Any]) -> str | None:
    """Texto que dice qué parámetros son valores por defecto."""
    faltan = []
    if not parametros.get("motor_optico"):
        faltan.append("la óptica usa valores por defecto (vidrio según la tecnología del panel, "
                      "suciedad de Colombia): corre 🔆 Motor Óptico para ajustarla")
    if not parametros.get("mismatch"):
        faltan.append("mismatch de fabricación y cables usan los valores por defecto de 🔀 Mismatch "
                      "(1 % y 1,5 %) y no hay sombra de horizonte: corre 🔀 Mismatch para ajustarlos")
    return ("ℹ️ Cadena de pérdidas: " + "; ".join(faltan) + ".") if faltan else None


def registro_publicacion(estado: Mapping[str, Any], resultados: Mapping[str, Mapping[str, Any]],
                         superficies: list[Mapping[str, Any]]) -> dict:
    """Lo que se guarda junto a la energía publicada."""
    return {
        "version": VERSION_CADENA,
        "firma": firma_cadena(parametros_cadena(estado), superficies),
        "pr": {n: round(float(r["pr"]), 5) for n, r in resultados.items()},
    }


def aviso_cadena_vencida(estado: Mapping[str, Any]) -> str | None:
    """Aviso si la energía multi-superficie publicada no usa la cadena vigente."""
    if not estado.get("multisup_activo"):
        return None
    registro = estado.get(CLAVE_PUBLICACION)
    if not isinstance(registro, Mapping) or registro.get("version") != VERSION_CADENA:
        return ("⚠️ La energía multi-superficie se publicó con la versión anterior (PR fijo "
                "0,78, sin 🔆 Motor Óptico ni 🔀 Mismatch). Vuelve a publicarla en 🗺️ Vista 3D "
                "› Integrar para usar la cadena de pérdidas de cada superficie.")
    superficies = [s for s in estado.get("superficies_bipv") or [] if s.get("activa", True)]
    if registro.get("firma") != firma_cadena(parametros_cadena(estado), superficies):
        return ("⚠️ Cambiaron los parámetros de pérdidas (🔆 Motor Óptico, 🔀 Mismatch o el "
                "montaje de una superficie) después de publicar la energía. Vuelve a publicarla "
                "en 🗺️ Vista 3D › Integrar.")
    return None


def cadena_optica_fisico(superficie: Mapping[str, Any], panel: Mapping[str, Any],
                         parametros: Mapping[str, Any]) -> dict:
    """Parámetros ópticos que el modo físico aplica a la POA de la superficie."""
    vertical = float(superficie.get("tilt_deg", 90)) >= TILT_VERTICAL
    return {
        "b0": b0_superficie(panel, superficie.get("panel_nombre"), parametros),
        "f_iam_dif": float(parametros["f_iam_dif"]),
        "soiling_config": {int(m): float(v) for m, v in parametros["soiling_config"].items()},
        "k_soiling_vert": float(parametros["k_soiling_vert"]) if vertical else 1.0,
    }


def poa_optica_fisico(tmy_df: pd.DataFrame, poa_df: pd.DataFrame, panel: Mapping[str, Any],
                      k_bipv: float, cadena_optica: Mapping[str, Any]) -> np.ndarray:
    """POA con IAM + suciedad (sin térmico: el SDM aplica la temperatura)."""
    tmy = tmy_df.copy()
    tmy.index = poa_df.index
    res, _ = cascada_optica(
        tmy, poa_df, b0=float(cadena_optica["b0"]), noct=float(panel["NOCT"]),
        k_bipv=float(k_bipv),
        soiling_config={int(m): float(v) for m, v in cadena_optica["soiling_config"].items()},
        f_iam_dif=float(cadena_optica["f_iam_dif"]), transparencia=0.0,
        k_soiling_vert=float(cadena_optica["k_soiling_vert"]),
    )
    return np.maximum(res["poa_post_soil"].to_numpy(dtype=float), 0.0)
