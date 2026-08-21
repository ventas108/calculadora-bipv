# -*- coding: utf-8 -*-
"""
comparador_baterias.py
========================
Compara TODAS las baterías del catálogo (datos/catalogo_baterias_excel.py)
para el consumo diario, autonomía deseada e inversor del proyecto -- hermano
de calculos/comparador_paneles.py y calculos/comparador_orientacion.py, pero
para el módulo B-6 (pages/11_🔋_Baterias_y_Balance.py) en vez del motor
BIPV de Fase 2/4.

Reusa las mismas funciones puras que ya usa esa página para UNA sola
batería: calculos.baterias_balance.dimensionar_bateria() (dimensionamiento)
y calculos.compatibilidad_bateria.check_compatibilidad() (compatibilidad de
voltaje con el inversor, ahora sobre el rango completo cuando el catálogo lo
trae -- ver la nota en ese módulo). No se reimplementa ninguna física aquí.

A diferencia de comparador_paneles: no hay simulación de 8760h que correr
(el dimensionamiento de batería es una fórmula cerrada, no una serie
temporal), así que comparar TODO el catálogo es barato -- no hace falta
avisar de costo de cómputo como en el barrido de orientación.

Función pura: recibe el catálogo + parámetros de diseño ya resueltos y
devuelve un DataFrame -- no lee st.session_state, no importa streamlit.
"""
from __future__ import annotations

import pandas as pd

from calculos.baterias_balance import dimensionar_bateria
from calculos.compatibilidad_bateria import check_compatibilidad

_ICONO_ESTADO = {"ok": "✅", "warning": "⚠️", "error": "❌"}


def comparar_baterias(
    catalogo: dict,
    inversor_dict: dict,
    inversor_nombre: str,
    E_consumo_diario_kWh: float,
    autonomia_h: float,
) -> pd.DataFrame:
    """
    Para cada batería del catálogo: evalúa compatibilidad de voltaje con el
    inversor del proyecto (check_compatibilidad()) y dimensiona la cantidad
    de unidades necesaria (dimensionar_bateria()) para el consumo/autonomía
    dados.

    El icono de compatibilidad tiene TRES estados, a diferencia del ✅/❌ de
    paneles: "✅" (ok), "⚠️" (warning -- el catálogo no tiene datos
    suficientes para confirmar, NO es un "sí" garantizado) y "❌" (error,
    incompatibilidad detectada). Ver calculos/compatibilidad_bateria.py.

    Devuelve un DataFrame con una fila por batería, ordenado por: primero
    compatibilidad (✅ antes que ⚠️ antes que ❌/no-dimensionable), y dentro
    de cada grupo por vida estimada descendente (criterio técnico de
    durabilidad -- más años de servicio es mejor, análogo a E_ac/PR en
    paneles). Nunca CAPEX/costo como criterio de orden: eso es contexto de
    apoyo, no la decisión técnica.
    """
    filas = []
    for nombre, bat in catalogo.items():
        estado, msg = check_compatibilidad(bat, inversor_dict, inversor_nombre)
        dim = dimensionar_bateria(bat, E_consumo_diario_kWh, autonomia_h)

        if "error" in dim:
            filas.append({
                "Batería": nombre,
                "Compatible": _ICONO_ESTADO.get(estado, "—"),
                "N° unidades": None,
                "Capacidad instalada (kWh)": None,
                "Capacidad útil (kWh)": None,
                "DoD real (%)": None,
                "Vida estimada (años)": None,
                "Costo total (USD)": None,
                "_motivo_compat": msg,
                "_error_dimension": dim["error"],
                "_advertencias": "",
            })
            continue

        filas.append({
            "Batería": nombre,
            "Compatible": _ICONO_ESTADO.get(estado, "—"),
            "N° unidades": dim["N_baterias"],
            "Capacidad instalada (kWh)": dim["C_instalada_kWh"],
            "Capacidad útil (kWh)": dim["C_util_kWh"],
            "DoD real (%)": dim["dod_real_pct"],
            "Vida estimada (años)": dim["vida_estimada_anos"],
            "Costo total (USD)": dim.get("costo_total_usd"),
            "_motivo_compat": msg,
            "_error_dimension": None,
            "_advertencias": "; ".join(dim.get("advertencias", [])),
        })

    df = pd.DataFrame(filas)
    if not df.empty:
        _orden_compat = {"✅": 0, "⚠️": 1, "—": 2, "❌": 3}
        df["_orden_compat"] = df["Compatible"].map(_orden_compat).fillna(4)
        df = (
            df.sort_values(
                ["_orden_compat", "Vida estimada (años)"],
                ascending=[True, False],
                na_position="last",
            )
            .drop(columns="_orden_compat")
            .reset_index(drop=True)
        )
    return df


def formatear_comparacion_baterias(df: pd.DataFrame, tipo_instalacion: str) -> str:
    """Texto plano para agentes/analista_produccion.py -- mismo principio que
    formatear_comparacion_paneles(): nunca se le pasa el DataFrame crudo a un
    LLM, y el tipo de instalación se declara explícito.

    Aclara explícitamente que esta comparación es de BATERÍAS (autonomía,
    DoD, vida útil, compatibilidad de voltaje con el inversor) -- no de
    paneles ni de orientación, para que el agente no intente aplicar E_ac/PR
    ni compatibilidad eléctrica de panel a estos candidatos.
    """
    if df.empty:
        return (
            f"Tipo de instalación: {tipo_instalacion}.\n\n"
            "No hay ninguna batería en el catálogo para comparar."
        )

    lineas = [
        f"Tipo de instalación: {tipo_instalacion}.",
        "",
        "Esta comparación es de BATERÍAS de almacenamiento para el consumo diario y la "
        "autonomía configurados en el proyecto, contra el inversor ya elegido. El criterio "
        "técnico aquí es autonomía real entregada, margen de DoD, vida útil estimada "
        "(ciclos) y compatibilidad de VOLTAJE con el inversor -- NO energía anual (E_ac) ni "
        "PR (eso es para paneles/orientación) y NO compatibilidad eléctrica de panel.",
        "",
        "Compatible tiene tres estados: ✅ = compatible confirmado, ⚠️ = el catálogo no "
        "tiene datos suficientes para confirmar (NO tratar como un sí garantizado, decirlo "
        "explícitamente), ❌ = incompatibilidad detectada (nunca recomendar).",
        "",
        "## Baterías comparadas (agrupadas por compatibilidad, luego por vida estimada descendente)",
        "",
    ]
    for _, r in df.iterrows():
        motivo = f" — {r['_motivo_compat']}" if r["Compatible"] in ("⚠️", "❌") else ""
        if r["_error_dimension"]:
            lineas.append(
                f"- **{r['Batería']}** — Compatible: {r['Compatible']}{motivo}\n"
                f"  no se pudo dimensionar: {r['_error_dimension']}"
            )
            continue
        costo = (
            f", costo total=USD {r['Costo total (USD)']:,.0f}"
            if r["Costo total (USD)"] else ", costo total=no disponible"
        )
        lineas.append(
            f"- **{r['Batería']}** — Compatible: {r['Compatible']}{motivo}\n"
            f"  unidades={r['N° unidades']:.0f}, capacidad instalada={r['Capacidad instalada (kWh)']:.1f} kWh, "
            f"capacidad útil={r['Capacidad útil (kWh)']:.1f} kWh, DoD real={r['DoD real (%)']:.1f}%, "
            f"vida estimada={r['Vida estimada (años)']:.1f} años{costo}"
        )
    return "\n".join(lineas)
