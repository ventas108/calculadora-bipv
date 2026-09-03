# -*- coding: utf-8 -*-
"""
Validación de Fase 4: sensibilidad, generación de candidatos, evaluación y
frente de Pareto. Reusa los fixtures de Fase 2/3 (TMY sintético offline,
panel/inversor reales validados contra el XLSM).
"""
import dataclasses

import pytest

from datos.catalogo_inversores import INVERSORES
from datos.tecnologias_bipv import ASP_ST1_T40

from simulation.schemas import FinancialConfiguration

from optimization import variables as opt_vars
from optimization.sensitivity import analizar_sensibilidad, ordenar_por_impacto
from optimization.scenario_generator import generar_candidatos, _muestrear_variable
from optimization.numerical_optimizer import evaluar_candidatos, ResultadoCandidato
from optimization.pareto import domina, frente_pareto
from optimization.objectives import estimar_capex_parametrico_usd

from tests.test_simulation_pipeline import _tmy_sintetico_offline, _config_base, LAT, LON, ALT_M

GROWATT = INVERSORES["Growatt-MID15KTL3-X"]


@pytest.fixture(scope="module")
def tmy_bogota():
    return _tmy_sintetico_offline(LAT, LON, ALT_M)


def _cfg_electricamente_valida():
    return dataclasses.replace(
        _config_base(), panel=ASP_ST1_T40, inversor=GROWATT,
        N_serie=8, N_strings_tracker=8,
    )


def _fin_builder(sim):
    capex = estimar_capex_parametrico_usd(sim, "BIPV fachada/pérgola")
    return FinancialConfiguration(capex_usd=capex, tarifa_cop_kWh=750.0, tipo_cambio=4000.0)


# ── sensitivity.py ────────────────────────────────────────────────────────

def test_sensibilidad_solo_evalua_variables_numericas(tmy_bogota):
    variables = opt_vars.variables_geometria("Fachada") + [opt_vars.variable_panel()]
    resultados = analizar_sensibilidad(_config_base(), variables, tmy_bogota)
    assert {r.variable for r in resultados} == {"tilt", "azimuth"}   # panel (categórica) excluida


def test_sensibilidad_impacto_absoluto_correcto(tmy_bogota):
    variables = opt_vars.variables_geometria("Fachada")
    resultados = analizar_sensibilidad(_config_base(), variables, tmy_bogota)
    for r in resultados:
        assert r.impacto_absoluto["energia_anual"] == pytest.approx(
            abs(r.objetivos_alto["energia_anual"] - r.objetivos_bajo["energia_anual"])
        )
        assert "npv" not in r.impacto_absoluto   # sin fin_config_builder, no hay valor numérico


def test_sensibilidad_con_financiero_incluye_npv(tmy_bogota):
    variables = [opt_vars.variable_k_bipv()]
    resultados = analizar_sensibilidad(_config_base(), variables, tmy_bogota, fin_config_builder=_fin_builder)
    assert resultados[0].objetivos_bajo["npv"] is not None
    assert "npv" in resultados[0].impacto_absoluto


def test_ordenar_por_impacto_descendente(tmy_bogota):
    variables = opt_vars.variables_geometria("Fachada") + [opt_vars.variable_k_bipv()]
    resultados = analizar_sensibilidad(_config_base(), variables, tmy_bogota)
    ordenado = ordenar_por_impacto(resultados, "energia_anual")
    impactos = [r.impacto_absoluto["energia_anual"] for r in ordenado]
    assert impactos == sorted(impactos, reverse=True)


def test_sensibilidad_azimuth_circular_ya_no_es_degenerada(tmy_bogota):
    # Regresión: el Analista Técnico-Financiero (agente) señaló un impacto
    # de sensibilidad de exactamente 0 en un barrido de azimuth 0°→360°
    # como "bandera roja metodológica" -- tenía razón. minimo=0 y
    # maximo=360 son el MISMO azimuth físico (Norte), así que el barrido
    # comparaba Norte contra Norte. Con tilt=90° (fachada vertical), Norte
    # vs Sur SÍ debe producir una diferencia real de energía.
    from optimization.sensitivity import _valores_extremos

    variables = opt_vars.variables_geometria("Fachada")
    azimuth_var = next(v for v in variables if v.nombre == "azimuth")
    assert azimuth_var.circular is True

    bajo, alto = _valores_extremos(azimuth_var)
    assert (bajo, alto) == (0.0, 180.0)   # Norte vs Sur, no Norte vs Norte

    cfg = dataclasses.replace(_cfg_electricamente_valida(), tilt=90.0, azimuth=180.0)
    resultados = analizar_sensibilidad(cfg, variables, tmy_bogota)
    r_azimuth = next(r for r in resultados if r.variable == "azimuth")

    assert r_azimuth.valor_bajo == 0.0
    assert r_azimuth.valor_alto == 180.0
    assert r_azimuth.impacto_absoluto["energia_anual"] > 0.0


# ── scenario_generator.py ────────────────────────────────────────────────

def test_muestrear_variable_categorica_devuelve_opcion_real_del_catalogo():
    # Antes generar_candidatos() no muestreaba categóricas (panel/inversor
    # quedaban fuera del barrido); ahora sí -- ver docstring del módulo.
    var = opt_vars.variable_panel()
    valor = _muestrear_variable(var, rng=__import__("random").Random(0))
    assert valor in var.opciones


def test_generar_candidatos_sin_inversor_no_fabrica_candidatos():
    # requerir_evaluables=True (default): compatibilidad_electrica no
    # evaluable sin inversor -> nunca se aprueba por defecto.
    cfg = dataclasses.replace(_config_base(), inversor=None)
    candidatos = generar_candidatos(
        cfg, opt_vars.variables_geometria("Fachada"), n_candidatos=5, seed=1,
    )
    assert candidatos == []


def test_generar_candidatos_relajando_evaluabilidad_si_produce_candidatos():
    cfg = dataclasses.replace(_config_base(), inversor=None)
    candidatos = generar_candidatos(
        cfg, opt_vars.variables_geometria("Fachada"), n_candidatos=5, seed=1,
        requerir_evaluables=False,
    )
    assert len(candidatos) == 5


def test_generar_candidatos_electricamente_validos_respeta_bounds():
    cfg = _cfg_electricamente_valida()
    variables = opt_vars.variables_geometria("Fachada")
    candidatos = generar_candidatos(cfg, variables, n_candidatos=8, seed=7)
    assert len(candidatos) == 8
    tilt_var = next(v for v in variables if v.nombre == "tilt")
    az_var = next(v for v in variables if v.nombre == "azimuth")
    for c in candidatos:
        assert tilt_var.minimo <= c.tilt <= tilt_var.maximo
        assert az_var.minimo <= c.azimuth <= az_var.maximo
        # el resto de la config (panel/inversor/N_serie) no se tocó
        assert c.N_serie == cfg.N_serie


def test_generar_candidatos_es_reproducible_con_seed():
    cfg = _cfg_electricamente_valida()
    variables = opt_vars.variables_geometria("Fachada")
    c1 = generar_candidatos(cfg, variables, n_candidatos=5, seed=42)
    c2 = generar_candidatos(cfg, variables, n_candidatos=5, seed=42)
    assert [(c.tilt, c.azimuth) for c in c1] == [(c.tilt, c.azimuth) for c in c2]


# ── scenario_generator.py + panel/inversor (extensión) ─────────────────────
# generar_candidatos() ahora también sortea variables categóricas de
# catálogo (panel, inversor) -- antes solo geometría/strings. Estos tests
# usan el catálogo REAL (INVERSORES, MODULOS_BIPV vía opt_vars.variable_panel())
# a propósito: un catálogo sintético habría escondido el hallazgo real de
# que 6 de los 7 paneles de MODULOS_BIPV tienen Pmax_stc=None y no son
# simulables -- ver el docstring de variable_panel().

def _variables_panel_inversor_completas():
    return (
        opt_vars.variables_geometria("Fachada")
        + [opt_vars.variable_panel(), opt_vars.variable_inversor()]
        + opt_vars.variables_string()
    )


def test_variable_panel_incluye_toda_la_familia_asp_st1_completa():
    # Hasta 2026-08-21, 6 de los 7 paneles de MODULOS_BIPV tenían Pmax_stc=None
    # (fichas incompletas, nunca ejercitadas porque el proyecto real usaba
    # T40) -- dimensionar_sistema() revienta con TypeError si se les intenta
    # dimensionar. Se completaron con los valores reales de
    # datos/paneles_catalogo.xlsx (ver datos/tecnologias_bipv.py) -- ahora
    # los 7 tienen ficha completa y variable_panel() ya no excluye ninguno.
    # Si el catálogo vuelve a crecer con una ficha incompleta, este test debe
    # fallar para que se note, no pasar en silencio.
    # Desde que variable_panel() se conectó al catálogo Excel (27-ago-2026),
    # var.opciones ya NO es igual a MODULOS_BIPV.keys() -- es un superconjunto
    # (las 7 + hasta 65 del Excel). La comprobación de regresión que importa
    # sigue siendo "los 7 ASP-ST1 completos están todos adentro", ahora como
    # subconjunto, no como igualdad exacta.
    from datos.tecnologias_bipv import MODULOS_BIPV
    var = opt_vars.variable_panel()
    assert "ASP-ST1-T40" in var.opciones
    incompletos = {k for k, v in MODULOS_BIPV.items() if v.get("Pmax_stc") is None}
    assert not incompletos, f"hay fichas incompletas de nuevo en el catálogo: {sorted(incompletos)}"
    assert set(MODULOS_BIPV.keys()) <= set(var.opciones)


def test_catalogo_paneles_real_prioriza_sdm_calibrado_sobre_excel_para_asp_st1():
    # _catalogo_paneles_real() hace una UNIÓN (no una preferencia lisa como
    # con inversores) -- para las 7 claves que existen en AMBAS fuentes
    # (ASP-ST1-T10..T70), debe ganar MODULOS_BIPV (SDM calibrado por curve-fit
    # contra el XLSM), no la versión del Excel (sin a_ref/I_L_ref/etc, solo
    # un NsA/n_idealidad estimado). Si esto se rompiera, el proyecto
    # Teusaquillo (el único auditado contra el XLSM) perdería su modelo de
    # diodo único sin que ningún test lo notara.
    from datos.tecnologias_bipv import MODULOS_BIPV
    from optimization.variables import _catalogo_paneles_real
    from calculos.produccion import panel_tiene_sdm_completo

    union = _catalogo_paneles_real()
    for clave in MODULOS_BIPV:
        assert union[clave] is MODULOS_BIPV[clave] or union[clave] == MODULOS_BIPV[clave]
        assert panel_tiene_sdm_completo(union[clave])
        assert union[clave].get("a_ref") == MODULOS_BIPV[clave].get("a_ref")


def test_catalogo_paneles_real_incluye_paneles_exclusivos_del_excel():
    # Verifica la parte nueva de la unión: un panel que NO está en
    # MODULOS_BIPV (solo en el catálogo Excel de 65) debe aparecer en
    # variable_panel().opciones y resolverse sin KeyError vía
    # generar_candidatos() -- exactamente el bug de tercera aparición
    # encontrado y corregido el 27-ago-2026 en
    # optimization.scenario_generator._resolver_categoricas_de_catalogo() y
    # calculos.comparador_paneles.comparar_paneles().
    from datos.tecnologias_bipv import MODULOS_BIPV
    from optimization.variables import _catalogo_paneles_real, OptimizationVariable
    from optimization.scenario_generator import _resolver_categoricas_de_catalogo

    union = _catalogo_paneles_real()
    solo_excel = [k for k in union if k not in MODULOS_BIPV]
    assert solo_excel, "el catálogo Excel debería aportar paneles que MODULOS_BIPV no tiene"
    clave_excel = solo_excel[0]
    assert clave_excel in opt_vars.variable_panel().opciones

    # No se compara el dict completo con == -- varias columnas del Excel
    # (Voc/Isc/Imp/Isc_stc) traen NaN, y NaN != NaN en Python (IEEE754), así
    # que dos dicts idénticos en contenido fallarían la igualdad por eso, no
    # por ningún bug real. "nombre" y Pmax_stc alcanzan para confirmar que
    # se resolvió al panel correcto del catálogo Excel.
    resuelto = _resolver_categoricas_de_catalogo({"panel": clave_excel})
    assert resuelto["panel"]["nombre"] == union[clave_excel]["nombre"]
    assert resuelto["panel"]["Pmax_stc"] == union[clave_excel]["Pmax_stc"]

    cfg = _cfg_electricamente_valida()
    var_panel_fijo = OptimizationVariable("panel", "categorica", opciones=(clave_excel,))
    candidatos = generar_candidatos(
        cfg, [var_panel_fijo], n_candidatos=1, seed=1, requerir_evaluables=False,
    )
    if candidatos:
        assert candidatos[0].panel["nombre"] == union[clave_excel]["nombre"]


def test_generar_candidatos_con_panel_e_inversor_varia_ambos():
    # max_intentos_por_candidato=120 (default 20 -> 300 intentos totales no
    # alcanza; 60 tampoco, ver abajo): tras corregir evaluar_compatibilidad_string()
    # (27-ago-2026, auditoría) para usar Vmppt_activo_min en vez de Vmppt_min
    # como piso -- el umbral correcto, ya usado por optimizar_n_serie() y
    # comparador_inversores.py -- el espacio eléctrico válido del catálogo
    # real es más angosto de lo que el presupuesto por defecto asumía. El
    # propio docstring de generar_candidatos() indica subir el presupuesto
    # explícitamente en vez de relajar la aserción.
    #
    # Subido de 60 a 120 (3-sep-2026): tras importar 278 paneles reales de JA
    # Solar (datos/agregar_paneles_ja_solar_nrel.py), variable_panel() sortea
    # sobre un catálogo mucho más grande y heterogéneo (354 paneles reales,
    # antes ~72) -- muchos son módulos crystalinos antiguos de baja potencia
    # que no calzan eléctricamente con el inversor fijo de esta prueba, así
    # que la tasa de aciertos por intento baja. Verificado empíricamente
    # (mismo seed=3): 60 intentos da 10/15, 100 da 15/15 -- se deja margen a
    # 120 en vez del mínimo exacto encontrado.
    cfg = _cfg_electricamente_valida()
    candidatos = generar_candidatos(
        cfg, _variables_panel_inversor_completas(), n_candidatos=15, seed=3,
        max_intentos_por_candidato=120,
    )
    assert len(candidatos) == 15
    inversores = {c.inversor["modelo"] for c in candidatos}
    assert len(inversores) > 1, "el barrido debería explorar más de un inversor real"
    inversor_var = opt_vars.variable_inversor()
    # Resolver contra _catalogo_inversores_real() (el catálogo real de 105 del
    # Excel, ya conectado localmente desde el fix de ruta de
    # datos/catalogo_inversores_excel.py, 28-ago-2026) -- no contra
    # INVERSORES (7) a secas: sus claves ("Growatt-MID15KTL3-X") no coinciden
    # con las del Excel ("MID 15KTL3-X"), mismo patrón de bug ya evitado en
    # otros lugares esta sesión.
    catalogo_real = opt_vars._catalogo_inversores_real()
    for c in candidatos:
        assert c.panel["nombre"] in opt_vars.variable_panel().opciones
        assert any(c.inversor["modelo"] == catalogo_real[k]["modelo"] for k in inversor_var.opciones)


def test_generar_candidatos_sincroniza_eta_inversor_con_el_inversor_sorteado():
    # Regresión: un candidato con inversor Growatt pero eta_inversor de otra
    # marca sería una config internamente inconsistente. Verificado contra
    # el catálogo real, no un valor inventado.
    #
    # El catálogo Excel real (105 modelos, conectado localmente desde el fix
    # de ruta de datos/catalogo_inversores_excel.py, 28-ago-2026) no trae
    # "eficiencia_max" para NINGÚN modelo (el datasheet fuente no lo reporta
    # -- ver docstring de tests/test_catalogo_inversores_real.py). Por eso
    # aquí, a nivel de generar_candidatos() end-to-end, lo que se puede
    # verificar con datos reales es la mitad "no inventar": eta_inversor
    # conserva el de config_base cuando el inversor sorteado no trae el dato.
    # El caso positivo (sí sincroniza cuando SÍ hay eficiencia_max real) ya
    # está cubierto a nivel unitario, con un catálogo controlado, en
    # test_catalogo_inversores_real.py::test_resolver_sincroniza_eta_inversor_cuando_si_hay_dato_real.
    cfg = _cfg_electricamente_valida()
    candidatos = generar_candidatos(
        cfg, _variables_panel_inversor_completas(), n_candidatos=15, seed=5,
        max_intentos_por_candidato=60,  # ver comentario en el test anterior
    )
    assert len(candidatos) == 15
    for c in candidatos:
        _efic = c.inversor.get("eficiencia_max")
        if _efic is not None:
            assert c.eta_inversor == pytest.approx(_efic)
        else:
            assert c.eta_inversor == cfg.eta_inversor


def test_generar_candidatos_panel_inversor_es_reproducible_con_seed():
    cfg = _cfg_electricamente_valida()
    variables = _variables_panel_inversor_completas()
    c1 = generar_candidatos(cfg, variables, n_candidatos=10, seed=99)
    c2 = generar_candidatos(cfg, variables, n_candidatos=10, seed=99)
    assert [(c.panel["nombre"], c.inversor["modelo"], c.N_serie) for c in c1] == \
           [(c.panel["nombre"], c.inversor["modelo"], c.N_serie) for c in c2]


# ── numerical_optimizer.py ───────────────────────────────────────────────

def test_evaluar_candidatos_end_to_end(tmy_bogota):
    cfg = _cfg_electricamente_valida()
    candidatos = generar_candidatos(cfg, opt_vars.variables_geometria("Fachada"), n_candidatos=4, seed=3)
    resultados = evaluar_candidatos(candidatos, tmy_bogota, fin_config_builder=_fin_builder)

    assert len(resultados) == 4
    for r in resultados:
        assert r.objetivos["energia_anual"] > 0
        assert r.objetivos["npv"] is not None


def test_evaluar_candidatos_sin_fin_builder_dejan_financieros_en_none(tmy_bogota):
    cfg = _cfg_electricamente_valida()
    candidatos = generar_candidatos(cfg, opt_vars.variables_geometria("Fachada"), n_candidatos=2, seed=3)
    resultados = evaluar_candidatos(candidatos, tmy_bogota)
    assert all(r.objetivos["npv"] is None for r in resultados)


# ── pareto.py ─────────────────────────────────────────────────────────────

def test_domina_ignora_objetivos_none():
    a = {"npv": 100.0, "payback_simple": None}
    b = {"npv": 50.0, "payback_simple": None}
    assert domina(a, b, ["npv", "payback_simple"]) is True   # solo npv es comparable


def test_domina_requiere_mejor_o_igual_en_todos():
    a = {"npv": 100.0, "payback_simple": 6.0}
    b = {"npv": 50.0, "payback_simple": 4.0}   # b tiene mejor payback
    assert domina(a, b, ["npv", "payback_simple"]) is False
    assert domina(b, a, ["npv", "payback_simple"]) is False


def test_domina_empate_total_no_domina():
    a = {"npv": 100.0}
    b = {"npv": 100.0}
    assert domina(a, b, ["npv"]) is False


def test_frente_pareto_caso_sintetico_conocido():
    r = [
        ResultadoCandidato(config=None, objetivos={"npv": 100.0, "payback_simple": 8.0}),  # A
        ResultadoCandidato(config=None, objetivos={"npv": 80.0,  "payback_simple": 4.0}),  # B
        ResultadoCandidato(config=None, objetivos={"npv": 50.0,  "payback_simple": 9.0}),  # C: dominado por A y B
    ]
    frente = frente_pareto(r, ["npv", "payback_simple"])
    assert len(frente) == 2
    assert r[2] not in frente


def test_frente_pareto_end_to_end_ningun_miembro_dominado(tmy_bogota):
    cfg = _cfg_electricamente_valida()
    candidatos = generar_candidatos(cfg, opt_vars.variables_geometria("Fachada"), n_candidatos=10, seed=11)
    resultados = evaluar_candidatos(candidatos, tmy_bogota, fin_config_builder=_fin_builder)
    frente = frente_pareto(resultados, ["npv", "payback_simple"])

    assert 0 < len(frente) <= len(resultados)
    for candidato in frente:
        assert not any(
            domina(otro.objetivos, candidato.objetivos, ["npv", "payback_simple"])
            for otro in resultados if otro is not candidato
        )
