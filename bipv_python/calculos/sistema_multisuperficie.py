"""Sistema multi-superficie publicado: potencia, módulos y reparto mensual.

Spec ``06-analisis-financiero/sistema-multisuperficie`` (H-D5). Se calcula en
el mismo momento y del mismo diseño que la energía publicada, para que
Financiero, Baterías y CO₂ nunca mezclen la energía de 🗺️ Vista 3D con la
potencia o los módulos del sistema de superficie única.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import pandas as pd

CLAVE_SISTEMA = "multisup_sistema"
TOLERANCIA_MENSUAL_KWH = 0.5
REPARTO_MENSUAL = "poa_superficie"


def _pmax_w(panel: Mapping[str, Any], nombre_sup: str) -> float:
    try:
        pmax = float(panel.get("Pmax_stc"))
    except (TypeError, ValueError):
        pmax = float("nan")
    if not math.isfinite(pmax) or pmax <= 0:
        raise ValueError(f"El panel de '{nombre_sup}' no trae su potencia (Pmax_stc).")
    return pmax


def _costo(panel: Mapping[str, Any]) -> float | None:
    try:
        costo = float(panel.get("costo_usd"))
    except (TypeError, ValueError):
        return None
    return costo if math.isfinite(costo) and costo > 0 else None


def reparto_mensual(e_anual_kWh: float, poa_df: pd.DataFrame | None, nombre: str) -> list[float]:
    """Reparte la energía anual de una superficie según su POA mensual."""
    from calculos.multi_superficie import poa_mensual_superficie

    if not isinstance(poa_df, pd.DataFrame) or poa_df.empty or "poa_global" not in poa_df.columns:
        raise ValueError(f"Falta la POA de '{nombre}' para repartir su energía por mes.")
    meses = poa_mensual_superficie(poa_df)
    total = sum(meses)
    if total <= 0:
        raise ValueError(f"La POA de '{nombre}' es cero: no se puede repartir por mes.")
    return [float(e_anual_kWh) * m / total for m in meses]


def resumen_sistema_multisuperficie(
    superficies: list[Mapping[str, Any]],
    paneles: Mapping[str, Mapping[str, Any]],
    desglose: list[Mapping[str, Any]],
    poa_por_superficie: Mapping[str, pd.DataFrame],
) -> dict:
    """``multisup_sistema`` de las superficies del desglose publicado.

    ``paneles`` es ``{nombre: {"panel", "nombre"}}`` (``paneles_superficies_estado``).
    Una superficie sin grupos de strings deja ``completo = False``: su
    potencia no se conoce y no se estima.
    """
    from calculos.diseno_electrico_multisup import modulos_de_superficie

    por_nombre = {s.get("nombre"): s for s in superficies}
    por_panel: dict[str, dict] = {}
    sin_grupos: list[str] = []
    mensual = [0.0] * 12
    total_e = 0.0
    for fila in desglose:
        nombre = fila["nombre"]
        sup = por_nombre.get(nombre)
        if sup is None:
            raise ValueError(f"La superficie '{nombre}' del desglose no existe.")
        for i, v in enumerate(reparto_mensual(fila["e_ac_kWh"], poa_por_superficie.get(nombre), nombre)):
            mensual[i] += v
        total_e += float(fila["e_ac_kWh"])
        modulos = modulos_de_superficie(sup)
        if not modulos:
            sin_grupos.append(nombre)
            continue
        info = paneles.get(nombre)
        if not info:
            raise ValueError(f"La superficie '{nombre}' no tiene panel utilizable.")
        pmax = _pmax_w(info["panel"], nombre)
        ref = str(info.get("nombre") or "sin nombre")
        item = por_panel.setdefault(ref, {"panel": ref, "modulos": 0, "P_dc_stc_kW": 0.0,
                                          "costo_usd": _costo(info["panel"])})
        item["modulos"] += modulos
        item["P_dc_stc_kW"] += modulos * pmax / 1000.0
    for item in por_panel.values():
        item["P_dc_stc_kW"] = round(item["P_dc_stc_kW"], 4)
    if abs(sum(mensual) - total_e) > TOLERANCIA_MENSUAL_KWH:
        raise ValueError("El reparto mensual no suma la energía anual del desglose.")
    return {
        "P_dc_stc_kW": round(sum(i["P_dc_stc_kW"] for i in por_panel.values()), 4),
        "n_modulos": int(sum(i["modulos"] for i in por_panel.values())),
        "por_panel": list(por_panel.values()),
        "completo": not sin_grupos,
        "superficies_sin_grupos": sin_grupos,
        "mensual_kWh": [round(v, 3) for v in mensual],
        "reparto_mensual": REPARTO_MENSUAL,
    }


def validar_sistema(sistema: Any, e_desglose_kWh: float) -> dict:
    """Invariantes de ``multisup_sistema``: el reparto mensual suma la energía
    del desglose (en origen físico el total publicado es la suma de buses, con
    recorte, y el desglose no lo incluye)."""
    if not isinstance(sistema, Mapping):
        raise ValueError("multisup_sistema debe ser un diccionario.")
    mensual = sistema.get("mensual_kWh")
    if not isinstance(mensual, (list, tuple)) or len(mensual) != 12:
        raise ValueError("multisup_sistema necesita 12 valores mensuales.")
    valores = [float(v) for v in mensual]
    if not all(math.isfinite(v) and v >= 0 for v in valores):
        raise ValueError("El reparto mensual tiene valores no válidos.")
    if abs(sum(valores) - float(e_desglose_kWh)) > TOLERANCIA_MENSUAL_KWH:
        raise ValueError(
            f"El reparto mensual suma {sum(valores):,.1f} kWh y el desglose "
            f"{float(e_desglose_kWh):,.1f} kWh."
        )
    if float(sistema.get("P_dc_stc_kW", -1)) < 0 or int(sistema.get("n_modulos", -1)) < 0:
        raise ValueError("Potencia o módulos negativos en multisup_sistema.")
    if sistema.get("completo") and int(sistema["n_modulos"]) <= 0:
        raise ValueError("Un sistema completo necesita módulos.")
    return dict(sistema)


def sistema_desde_estado(
    session_state: Mapping[str, Any],
    desglose: list[Mapping[str, Any]],
    poa_por_superficie: Mapping[str, pd.DataFrame],
) -> dict:
    """``resumen_sistema_multisuperficie`` con las superficies y paneles de la sesión."""
    from calculos.diseno_electrico_multisup import paneles_superficies_estado

    superficies = [s for s in (session_state.get("superficies_bipv") or []) if s.get("activa", True)]
    return resumen_sistema_multisuperficie(
        superficies, paneles_superficies_estado(session_state, superficies),
        desglose, poa_por_superficie,
    )


def estado_sistema_publicado(session_state: Mapping[str, Any]) -> dict:
    """``{"activo", "sistema", "problemas"}`` para Financiero, Baterías y CO₂.

    ``problemas`` explica en palabras sencillas por qué no se puede usar el
    sistema publicado; vacío si se puede.
    """
    if not session_state.get("multisup_activo"):
        return {"activo": False, "sistema": None, "problemas": []}
    sistema = session_state.get(CLAVE_SISTEMA)
    if not isinstance(sistema, Mapping):
        return {"activo": True, "sistema": None, "problemas": [
            "La energía multi-superficie se publicó con una versión anterior que no guardaba "
            "la potencia ni los módulos del sistema. Vuelve a publicarla en 🗺️ Vista 3D "
            "(«🔗 Usar sistema multi-superficie en Financiero»)."
        ]}
    if not sistema.get("completo"):
        faltan = ", ".join(f"«{n}»" for n in sistema.get("superficies_sin_grupos") or [])
        return {"activo": True, "sistema": dict(sistema), "problemas": [
            f"Sin grupos de strings en {faltan}: sin módulos no se conoce la potencia instalada "
            "ni el costo de esa superficie. Configura sus grupos en 🗺️ Vista 3D › ⚙️ Superficies "
            "BIPV › 🔌 Inversores por superficie y vuelve a publicar, o desactiva el modo "
            "multi-superficie."
        ]}
    return {"activo": True, "sistema": dict(sistema), "problemas": []}


def df_mensual_multisuperficie(sistema: Mapping[str, Any]) -> pd.DataFrame:
    """Producción mensual publicada con el formato de 📊 Producción."""
    from calculos.multi_superficie import MESES_ES

    return pd.DataFrame({"Mes": list(MESES_ES)[:12],
                         "E_ac (kWh)": [float(v) for v in sistema["mensual_kWh"]]})


def problemas_financieros(session_state: Mapping[str, Any]) -> list[str]:
    """Motivos para NO calcular TIR, VPN, payback ni LCOE con el sistema
    multi-superficie publicado (25-sep-2026).

    Además de los de ``estado_sistema_publicado``, un diseño eléctrico 🔴
    describe un sistema que no se puede construir (por ejemplo, un voltaje
    que daña el inversor): su TIR no es real. Sin estado registrado
    (publicación anterior a la fase A2) no se inventa un bloqueo.
    """
    problemas = list(estado_sistema_publicado(session_state)["problemas"])
    if not session_state.get("multisup_activo"):
        return problemas
    estado = session_state.get("multisup_estado_electrico")
    if isinstance(estado, Mapping) and estado.get("estado") == "rojo":
        problemas.append(
            f"El diseño eléctrico publicado tiene fallas 🔴 ({int(estado.get('n_bloqueos') or 0)}): "
            "describe un sistema que no se puede construir tal como está (por ejemplo, un "
            "voltaje que dañaría el inversor), así que su TIR, VPN y payback no serían "
            "reales. Revisa los mensajes 🔴 en 🗺️ Vista 3D › ⚙️ Superficies BIPV › "
            "⚡ Diseño eléctrico, corrígelos y vuelve a publicar la energía."
        )
    return problemas
