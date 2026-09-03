# -*- coding: utf-8 -*-
"""Validación de calculos/comparador_paneles.py (Página 4c) con datos reales
-- catálogo real de paneles/inversores, TMY sintético offline (mismo patrón
que test_simulation_pipeline.py). No usa datos inventados: si el catálogo
cambia, estos tests deben reflejarlo, no al revés.
"""
from datos.catalogo_inversores import INVERSORES
from datos.tecnologias_bipv import ASP_ST1_T40
from simulation.schemas import BIPVConfiguration
from calculos.comparador_paneles import (
    comparar_paneles,
    formatear_comparacion_paneles,
    paneles_excluidos_por_ficha_incompleta,
)
from tests.test_simulation_pipeline import _tmy_sintetico_offline, LAT, LON, ALT_M

GROWATT = INVERSORES["Growatt-MID15KTL3-X"]


def _cfg_base():
    return BIPVConfiguration(
        lat=LAT, lon=LON, alt_m=ALT_M, tilt=90.0, azimuth=180.0, area_m2=100.0,
        panel=ASP_ST1_T40, inversor=GROWATT, N_serie=8, N_strings_tracker=8,
    )


def test_paneles_excluidos_por_ficha_incompleta_refleja_el_catalogo_real():
    # Hasta 2026-08-21 T10-T70 estaban excluidos (Pmax_stc=None) -- se
    # completaron con los valores reales de datos/paneles_catalogo.xlsx (ver
    # datos/tecnologias_bipv.py). Hoy los 7 tienen ficha completa.
    #
    # ACTUALIZADO (3-sep-2026): tras importar 278 paneles reales de JA Solar
    # (datos/agregar_paneles_ja_solar_nrel.py, fuente NREL/SAM + Sandia JPV
    # 2025), 115 de ellos no traen dimensiones físicas en la fuente (solo
    # área total, DimensionesMM="N/D") -- area_m2=None. El filtro real de
    # variable_panel()/paneles_excluidos_por_ficha_incompleta() se extendió
    # el mismo día para exigir también area_m2 (antes solo Pmax_stc, ver
    # optimization/variables.py) -- este NO es un catálogo con menos fichas
    # completas, es el mismo filtro real detectando un hueco de datos real
    # que antes no existía en ningún panel del catálogo Excel.
    #
    # ACTUALIZADO otra vez (3-sep-2026, mismo día): tras importar 1.255
    # paneles reales de Trina Solar (datos/agregar_paneles_trina_nrel.py,
    # mismas 2 fuentes), 437 más sin dimensiones -- 115 (JA Solar) + 437
    # (Trina) = 552 excluidos reales.
    #
    # ACTUALIZADO otra vez (3-sep-2026, mismo día): tras importar 408
    # paneles reales de Jinko Solar (datos/agregar_paneles_jinko_nrel.py,
    # mismas 2 fuentes), 95 más sin dimensiones -- 552 + 95 = 647 excluidos.
    #
    # ACTUALIZADO otra vez (3-sep-2026, mismo día): tras importar 380
    # paneles reales de Canadian Solar (datos/agregar_paneles_canadian_nrel.py,
    # mismas 2 fuentes -- fabricante real "CSI Solar Co Ltd"), 310 más sin
    # dimensiones (81% de este lote, el más alto hasta ahora, verificado
    # real en la fuente) -- 647 + 310 = 957 excluidos reales hoy.
    excluidos = paneles_excluidos_por_ficha_incompleta()
    assert len(excluidos) == 957
    # Los 7 ASP-ST1 (con SDM calibrado, dimensiones reales) nunca deben
    # aparecer excluidos -- si alguno lo hiciera, sería una regresión real
    # de datos, no del import de JA Solar.
    assert not any(n.startswith("ASP-ST1") for n in excluidos)
    # Todos los excluidos deben serlo específicamente por area_m2 -- ninguno
    # por Pmax_stc (el import de JA Solar siempre trae Pmax_stc real de CEC).
    from optimization.variables import _catalogo_paneles_real
    catalogo = _catalogo_paneles_real()
    assert all(catalogo[n].get("area_m2") is None for n in excluidos)
    assert all(catalogo[n].get("Pmax_stc") is not None for n in excluidos)


def test_comparar_paneles_no_crashea_y_devuelve_todos_los_simulables():
    # Desde que variable_panel() se conectó al catálogo Excel (27-ago-2026,
    # ver optimization/variables.py::_catalogo_paneles_real()) comparar_paneles()
    # ya no compara solo los 7 ASP-ST1 -- compara el catálogo real unido
    # completo (72: 7 + 65 del Excel). Este test verifica eso, no un
    # conjunto fijo de 7 nombres que ya no refleja el catálogo real.
    from optimization.variables import variable_panel
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    df = comparar_paneles(
        _cfg_base(), tmy, "BIPV fachada/pérgola",
        tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    )
    assert not df.empty
    assert set(df["Panel"]) == set(variable_panel().opciones)
    # La familia ASP-ST1 completa (SDM calibrado) sigue simulable dentro del
    # catálogo unido -- no la perdió la unión con el Excel.
    assert {f"ASP-ST1-T{n}" for n in (10, 20, 30, 40, 50, 60, 70)} <= set(df["Panel"])


def test_comparar_paneles_columnas_esperadas_y_valores_positivos():
    # Con el catálogo unido (72 paneles) la mejor LCOE (df.iloc[0]) ya no es
    # necesariamente ASP-ST1-T40 -- N_serie/N_strings_tracker quedan FIJOS en
    # _cfg_base() para los 72, así que un panel con Voc/Vmp muy distinto
    # puede terminar eléctricamente incompatible (❌) con esa config aunque
    # tenga buena LCOE simulada. Se busca la fila T40 explícitamente -- es
    # el único candidato de este archivo ya auditado contra el XLSM como
    # compatible con N_serie=8/Growatt (ver FICHA_PVSYST_TEUSAQUILLO.md) --
    # en vez de asumir que la primera fila lo es.
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    df = comparar_paneles(
        _cfg_base(), tmy, "BIPV fachada/pérgola",
        tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    )
    assert not df.empty
    for _, fila in df.iterrows():
        assert fila["N° módulos"] > 0
        assert fila["P_dc (kWp)"] > 0
        assert fila["E_ac (kWh/año)"] > 0
        assert 0.0 < fila["PR"] < 1.5
        assert fila["CAPEX (USD)"] > 0

    fila_t40 = df[df["Panel"] == "ASP-ST1-T40"].iloc[0]
    assert fila_t40["Compatible"] == "✅"   # N_serie=8 con Growatt ya validado contra el XLSM


def test_comparar_paneles_ordena_por_lcoe_ascendente():
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    df = comparar_paneles(
        _cfg_base(), tmy, "BIPV fachada/pérgola",
        tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    )
    lcoe = df["LCOE (USD/kWh)"].tolist()
    assert lcoe == sorted(lcoe)


def test_comparar_paneles_marca_incompatibilidad_electrica_real():
    # N_serie=40 (fuera de la ventana MPPT del Growatt para este panel) debe
    # marcar el candidato como incompatible -- sin inventar el criterio,
    # reusa optimization.constraints.evaluar_compatibilidad_electrica().
    import dataclasses
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    cfg = dataclasses.replace(_cfg_base(), N_serie=40)
    df = comparar_paneles(
        cfg, tmy, "BIPV fachada/pérgola",
        tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    )
    assert df.iloc[0]["Compatible"] == "❌"


# ── formatear_comparacion_paneles() -- contexto para agentes/analista_produccion.py

def test_formatear_comparacion_declara_el_tipo_de_instalacion():
    # Mismo principio que corrigió el sesgo de fachada en los otros agentes:
    # el tipo de instalación va como dato explícito, no algo que el LLM deba
    # adivinar del nombre genérico "BIPV" de la plataforma.
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    df = comparar_paneles(
        _cfg_base(), tmy, "Granja FV campo",
        tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    )
    texto = formatear_comparacion_paneles(df, "Granja FV campo")
    assert "Tipo de instalación: Granja FV campo" in texto


def test_formatear_comparacion_cita_los_numeros_reales_del_dataframe():
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    df = comparar_paneles(
        _cfg_base(), tmy, "BIPV fachada/pérgola",
        tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    )
    fila = df.iloc[0]
    texto = formatear_comparacion_paneles(df, "BIPV fachada/pérgola")
    assert fila["Panel"] in texto
    assert f"{fila['E_ac (kWh/año)']:,.0f}" in texto
    assert f"{fila['PR']:.3f}" in texto


def test_formatear_comparacion_incluye_motivo_de_incompatibilidad():
    # El agente necesita saber POR QUÉ un candidato se descartó, no solo
    # que salga marcado ❌, para no recomendarlo sin explicación.
    import dataclasses
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    cfg = dataclasses.replace(_cfg_base(), N_serie=40)
    df = comparar_paneles(
        cfg, tmy, "BIPV fachada/pérgola",
        tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    )
    texto = formatear_comparacion_paneles(df, "BIPV fachada/pérgola")
    assert "❌" in texto
    assert df.iloc[0]["_motivo_electrico"] in texto


def test_formatear_comparacion_dataframe_vacio_no_crashea():
    import pandas as pd
    texto = formatear_comparacion_paneles(pd.DataFrame(), "Granja FV campo")
    assert "Granja FV campo" in texto
    assert "No hay ningún panel simulable" in texto
