# -*- coding: utf-8 -*-
"""
comparador_orientacion.py
==========================
Compara distintas combinaciones de tilt/azimuth sobre el MISMO sitio, panel,
inversor y strings de un proyecto -- hermano de calculos/comparador_paneles.py
y calculos/comparador_inversores.py, pero variando GEOMETRÍA en vez de
hardware. Reusa optimization/variables.py::variables_geometria() como fuente
de los límites físicos (tilt 0-90°, azimuth 0-360° circular) y
simulation/bipv_simulator.py::run_bipv_simulation() para cada candidato --
mismo motor de Fase 2/4, sin reimplementar nada aquí.

A diferencia de comparador_paneles: el hardware no cambia, así que no hay
CAPEX distinto entre candidatos ni compatibilidad eléctrica que evaluar --
el criterio es puramente energético (E_ac, PR). Por eso este módulo no
corre run_financial_simulation().

Función pura: recibe una BIPVConfiguration base + TMY ya descargado y
devuelve un DataFrame -- no lee st.session_state, no importa streamlit.
"""
from __future__ import annotations

import dataclasses

import pandas as pd

from simulation.bipv_simulator import run_bipv_simulation
from simulation.schemas import BIPVConfiguration


def _rango(minimo: float, maximo: float, paso: float) -> list[float]:
    if paso <= 0:
        raise ValueError("paso debe ser > 0")
    if maximo < minimo:
        raise ValueError("maximo debe ser >= minimo")
    n_pasos = int(round((maximo - minimo) / paso))
    return [round(minimo + i * paso, 4) for i in range(n_pasos + 1)]


def malla_tilt_azimuth(
    tilt_min: float = 0.0,
    tilt_max: float = 90.0,
    tilt_paso: float = 15.0,
    azimuth_min: float = 0.0,
    azimuth_max: float = 360.0,
    azimuth_paso: float = 30.0,
    tilt_actual: float | None = None,
    azimuth_actual: float | None = None,
) -> tuple[list[float], list[float]]:
    """
    Genera los valores de tilt y azimuth a barrer. Los límites por defecto
    son los físicos reales que ya usa el resto de la app (ver el slider de
    tilt en pages/2_☀️_Recurso_Solar.py: 0-90°, y ORIENTACIONES en
    calculos/solar.py: azimuth 0-360°) -- no un rango inventado para este
    módulo.

    0°=360°=Norte (ver OptimizationVariable.circular en
    optimization/variables.py) -- si el barrido cubre el círculo completo,
    el último punto duplicaría el primero: mismo azimuth físico, misma
    simulación, fila redundante. Se descarta automáticamente.

    Si se pasan tilt_actual/azimuth_actual y no caen exactamente en la malla
    (paso que no divide al valor actual del proyecto), se insertan -- sin
    esto, el barrido podría no incluir nunca el punto de partida real contra
    el que el usuario quiere comparar.
    """
    tilt_valores = _rango(tilt_min, tilt_max, tilt_paso)
    azimuth_valores = _rango(azimuth_min, azimuth_max, azimuth_paso)
    if len(azimuth_valores) > 1 and azimuth_valores[-1] % 360 == azimuth_valores[0] % 360:
        azimuth_valores = azimuth_valores[:-1]

    if tilt_actual is not None and not any(abs(t - tilt_actual) < 1e-6 for t in tilt_valores):
        tilt_valores = sorted(tilt_valores + [round(float(tilt_actual), 4)])
    if azimuth_actual is not None and not any(abs(a - azimuth_actual) < 1e-6 for a in azimuth_valores):
        azimuth_valores = sorted(azimuth_valores + [round(float(azimuth_actual), 4)])

    return tilt_valores, azimuth_valores


def comparar_orientacion(
    config_base: BIPVConfiguration,
    tmy: pd.DataFrame,
    tilt_valores: list[float],
    azimuth_valores: list[float],
) -> pd.DataFrame:
    """
    Corre run_bipv_simulation() para cada combinación (tilt, azimuth) de la
    malla, manteniendo panel/inversor/N_serie/N_strings_tracker/N_inversores/
    área fijos en los valores de `config_base` -- compara ORIENTACIÓN, no
    hardware.

    Marca con Actual=True la fila (si existe) cuyo tilt/azimuth coincide con
    la orientación actual de `config_base` -- útil para que el agente y el
    usuario ubiquen el punto de partida dentro del barrido.

    Devuelve un DataFrame con una fila por combinación, ordenado por energía
    anual (E_ac) descendente (mejor primero) -- vacío si no se pasó ningún
    valor de tilt o azimuth.
    """
    filas = []
    for tilt in tilt_valores:
        for azimuth in azimuth_valores:
            cfg = dataclasses.replace(config_base, tilt=tilt, azimuth=azimuth)
            sim = run_bipv_simulation(cfg, tmy=tmy)
            filas.append({
                "Tilt (°)": tilt,
                "Azimuth (°)": azimuth,
                "Actual": (
                    abs(tilt - config_base.tilt) < 1e-6
                    and abs(azimuth - config_base.azimuth) < 1e-6
                ),
                "N° módulos": sim.dim["N_paneles"],
                "P_dc (kWp)": round(sim.P_dc_stc_kW, 2),
                "E_ac (kWh/año)": round(sim.E_ac_anual_kWh, 0),
                "PR": round(sim.PR, 3),
            })

    df = pd.DataFrame(filas)
    if not df.empty:
        df = df.sort_values("E_ac (kWh/año)", ascending=False).reset_index(drop=True)
    return df


def formatear_comparacion_orientacion(df: pd.DataFrame, tipo_instalacion: str) -> str:
    """Texto plano para agentes/analista_produccion.py -- mismo principio que
    formatear_comparacion_paneles(): nunca se le pasa el DataFrame crudo a un
    LLM, y el tipo de instalación se declara explícito para que el agente no
    tenga que adivinarlo.

    A diferencia de la comparación de paneles, aquí se aclara explícitamente
    que el hardware NO cambia y que no hay compatibilidad eléctrica que
    evaluar -- para que el agente no invente ese criterio ni intente
    replicar lo que ya hace 🧩 Comparador de Paneles / ⚖️ Comparador de
    Inversores.
    """
    if df.empty:
        return (
            f"Tipo de instalación: {tipo_instalacion}.\n\n"
            "No hay ninguna combinación tilt/azimuth simulada."
        )

    lineas = [
        f"Tipo de instalación: {tipo_instalacion}.",
        "",
        "Esta comparación es de ORIENTACIÓN (inclinación/tilt y azimuth) sobre el MISMO "
        "panel, inversor y hardware ya elegidos para el proyecto -- el hardware NO cambia "
        "entre candidatos, así que no hay CAPEX distinto ni compatibilidad eléctrica que "
        "evaluar aquí (eso ya se evalúa en 🧩 Comparador de Paneles / ⚖️ Comparador de "
        "Inversores). El criterio es puramente energético: E_ac y PR.",
        "",
        "## Combinaciones tilt/azimuth comparadas (ordenadas por energía anual, mejor primero)",
        "",
    ]
    for _, r in df.iterrows():
        marca = " ← orientación actual del proyecto" if r["Actual"] else ""
        lineas.append(
            f"- **tilt={r['Tilt (°)']:.0f}°, azimuth={r['Azimuth (°)']:.0f}°**{marca} — "
            f"E_ac={r['E_ac (kWh/año)']:,.0f} kWh/año, PR={r['PR']:.3f}, "
            f"P_dc={r['P_dc (kWp)']:.2f} kWp, módulos={r['N° módulos']}"
        )
    return "\n".join(lineas)
