# -*- coding: utf-8 -*-
"""
comparador_paneles.py
======================
Compara paneles reales del catálogo sobre el MISMO sitio/geometría/inversor
de un proyecto -- hermano de calculos/comparador_inversores.py, pero con una
diferencia de fondo: cambiar de inversor solo afecta el lado AC (clipping
sobre una serie DC ya simulada), mientras que cambiar de panel cambia la
física DC completa (Voc/Isc/Vmp propios, área, tecnología) -- no hay forma
de "reclipear" una serie existente para simular otro panel. Cada candidato
se re-simula de verdad con run_bipv_simulation(), reusando el motor de
Fase 2/4 en vez de reimplementar nada aquí.

Función pura: recibe una BIPVConfiguration base + TMY ya descargado y
devuelve un DataFrame -- no lee st.session_state, no importa streamlit.
"""
from __future__ import annotations

import dataclasses

import pandas as pd

from simulation.bipv_simulator import run_bipv_simulation
from simulation.financial_simulator import run_financial_simulation
from simulation.schemas import BIPVConfiguration, FinancialConfiguration
from optimization.variables import variable_panel
from optimization.objectives import estimar_capex_parametrico_usd
from optimization.constraints import evaluar_compatibilidad_electrica


def comparar_paneles(
    config_base: BIPVConfiguration,
    tmy: pd.DataFrame,
    tipo_instalacion: str,
    tarifa_cop_kWh: float,
    tipo_cambio: float,
    tasa_descuento: float = 0.10,
    escenario_capex: str = "Base",
    zona_capex: str = "Bogotá / Sabana",
    catalogo: dict | None = None,
) -> pd.DataFrame:
    """
    Corre run_bipv_simulation() + run_financial_simulation() para cada panel
    SIMULABLE del catálogo (variable_panel() ya excluye las fichas
    incompletas -- ver su docstring) sobre la misma ubicación, geometría,
    inversor y strings de `config_base`. Compara hardware, no diseño: tilt/
    azimuth/N_serie/inversor quedan fijos, solo cambia el panel.

    El CAPEX de cada fila es una estimación paramétrica (calculos.presupuesto,
    vía optimization.objectives.estimar_capex_parametrico_usd) -- no una
    cotización real. Sirve para comparar el ORDEN de magnitud entre paneles,
    no para presupuestar.

    Devuelve un DataFrame con una fila por panel, ordenado por LCOE
    ascendente (mejor primero) -- vacío si no hay ningún panel simulable.
    """
    var_panel = variable_panel(catalogo)
    if catalogo is None:
        from datos.tecnologias_bipv import MODULOS_BIPV as catalogo

    filas = []
    for nombre in var_panel.opciones:
        panel = catalogo[nombre]
        cfg = dataclasses.replace(config_base, panel=panel)

        sim = run_bipv_simulation(cfg, tmy=tmy)
        capex = estimar_capex_parametrico_usd(sim, tipo_instalacion, escenario_capex, zona_capex)
        fin_cfg = FinancialConfiguration(
            capex_usd=capex, tarifa_cop_kWh=tarifa_cop_kWh, tipo_cambio=tipo_cambio,
            tasa_descuento=tasa_descuento,
        )
        fin = run_financial_simulation(sim, fin_cfg)
        compat = evaluar_compatibilidad_electrica(cfg)

        filas.append({
            "Panel": nombre,
            "Tecnología": panel.get("tecnologia", "—"),
            "Compatible": "✅" if compat.cumple else ("—" if not compat.evaluable else "❌"),
            "N° módulos": sim.dim["N_paneles"],
            "P_dc (kWp)": round(sim.P_dc_stc_kW, 2),
            "E_ac (kWh/año)": round(sim.E_ac_anual_kWh, 0),
            "PR": round(sim.PR, 3),
            "CAPEX (USD)": round(capex, 0),
            "VPN (USD)": round(fin.npv_usd, 0),
            "TIR (%)": fin.irr_pct,
            "Payback (años)": fin.payback_simple_anos,
            "LCOE (USD/kWh)": fin.metricas["lcoe_usd_kWh"],
            "_motivo_electrico": compat.mensaje,
        })

    df = pd.DataFrame(filas)
    if not df.empty:
        df = df.sort_values("LCOE (USD/kWh)", na_position="last").reset_index(drop=True)
    return df


def paneles_excluidos_por_ficha_incompleta(catalogo: dict | None = None) -> list[str]:
    """Nombres de paneles del catálogo que variable_panel() excluye por no
    tener Pmax_stc -- para mostrarle al usuario POR QUÉ no aparecen en la
    comparación, en vez de que simplemente falten sin explicación.

    No reusa variable_panel(catalogo) aquí a propósito: su filtro por
    Pmax_stc solo se aplica cuando NO se le pasa un catálogo explícito (ver
    su código) -- pasarle este mismo `catalogo` lo desactivaría. Se repite
    el mismo criterio directamente, autocontenido.
    """
    if catalogo is None:
        from datos.tecnologias_bipv import MODULOS_BIPV as catalogo
    return [k for k, v in catalogo.items() if v.get("Pmax_stc") is None]
