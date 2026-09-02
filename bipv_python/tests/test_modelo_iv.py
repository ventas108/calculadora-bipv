"""
Tests de calculos.modelo_iv -- sin cobertura directa hasta el 30-ago-2026.

Auditoría en 2 rondas pedida por el usuario:
1. "confírmalo en Motor IV también" -- verificar que el modelo lineal usado
   por curva_electrica_temperatura()/evaluar_compatibilidad_string()
   (Voc_stc/Vmp_stc escalados por Tk_beta) es coherente con el modelo físico
   completo del propio Motor IV (SDM De Soto 2006). Encontró un bug real
   (Imp_stc, ver los 2 primeros tests) que bloqueaba la comprobación.
2. "investiga por qué falla fit_desoto para paneles reales" -- encontró la
   causa real de la no-convergencia (sistema de 5 ecuaciones mal escalado,
   ver comentarios en calculos/modelo_iv.py::estimar_sdm_desde_ficha), un
   respaldo cerrado (fit_desoto_batzelis) que sí funciona para la enorme
   mayoría del catálogo real, y un SEGUNDO bug real más grave detrás de
   ambos: un desajuste de unidades en `a_ref` que colapsaba Voc ~39× para
   CUALQUIER panel estimado on-demand (no solo los que fallaban por
   Imp_stc) -- ver los tests de "unidades_a_ref" más abajo.
"""
import copy

import pytest

from calculos.modelo_iv import (
    estimar_sdm_desde_ficha,
    preparar_panel_iv,
    resolver_curva_iv,
    tiene_sdm_completo,
    validar_sdm_vs_ficha,
)
from calculos.dimensionamiento import calcular_voc_string, calcular_vmp_string
from datos.catalogo_paneles_excel import cargar_catalogo_paneles
from datos.tecnologias_bipv import ASP_ST1_T40


# ---------------------------------------------------------------------------
# Bug real (30-ago-2026): datos/catalogo_paneles_excel.py fijaba los alias
# "Voc_stc"/"Vmp_stc"/"Isc_stc" pero NO "Imp_stc", aunque el valor (`Imp`)
# sí estaba disponible en la ficha. calculos.modelo_iv.validar_sdm_vs_ficha()
# accede a panel["Imp_stc"] con subíndice directo (no .get()), así que
# preparar_panel_iv() lanzaba KeyError dentro de su propio try/except y lo
# convertía en "datos insuficientes" (None) para CUALQUIER panel real del
# catálogo Excel sin SDM precalibrado -- incluso cuando el ajuste habría
# sido válido. Encontrado auditando la coherencia Motor IV vs.
# curva_electrica_temperatura() con el panel real de Urabá (JA Solar
# JAM66D46-720/LB), que expuso el bug de inmediato.
# ---------------------------------------------------------------------------
def test_catalogo_excel_incluye_imp_stc_para_todo_panel_con_imp():
    catalogo = cargar_catalogo_paneles()
    assert catalogo, "el catálogo real no debería estar vacío"
    sin_alias = [
        nombre for nombre, p in catalogo.items()
        if p.get("Imp") and not p.get("Imp_stc")
    ]
    assert sin_alias == [], (
        f"{len(sin_alias)} panel(es) del catálogo real tienen 'Imp' pero no "
        f"el alias 'Imp_stc' -- volvió el bug que bloqueaba preparar_panel_iv() "
        f"con un KeyError silencioso: {sin_alias[:5]}"
    )


def test_validar_sdm_vs_ficha_no_lanza_keyerror_sin_alias_imp_stc():
    # Reproduce el síntoma exacto sin depender de que pvlib.fit_desoto()
    # converja (ver nota de no-determinismo más abajo): un panel con SDM ya
    # calibrado (ASP-ST1-T40) al que le falta el alias "Imp_stc" no debe
    # romper la validación con KeyError -- debe evaluarse igual, con "Imp"
    # como respaldo.
    panel = copy.deepcopy(ASP_ST1_T40)
    panel["Imp"] = panel.pop("Imp_stc")
    resultado = validar_sdm_vs_ficha(panel, tolerancia_pct=5.0)
    assert "Imp" in resultado
    assert resultado["validacion_ok"] is True


# ---------------------------------------------------------------------------
# Segundo bug real, más grave, encontrado investigando por qué fit_desoto()
# fallaba (30-ago-2026): `estimar_sdm_desde_ficha()` devolvía `a_ref` en
# VOLTIOS (la convención nativa de pvlib -- así lo dan fit_desoto()/
# fit_desoto_batzelis(), y así lo necesita la fórmula heurística interna
# exp(-Voc/a_ref)), pero `trasladar_parametros_gt()` y
# `calculos/produccion_iv.py::_pmp_iv_vectorizado()` esperan la convención
# UNITLESS (n × Ns) que usa el único panel precalibrado a mano de esta app
# (ASP-ST1-T40, a_ref=154.0) y multiplican por Vt_ref ellos mismos para
# convertir a voltios -- devolver ya-en-voltios lo convertía DOS veces,
# encogiendo nNsVth ~39× y colapsando Voc a ~1.3-1.6 V. Afectaba a
# CUALQUIER panel estimado on-demand desde que la función existe, sin que
# ningún test lo detectara porque los tests existentes solo comparaban la
# fórmula interna de a_ref, nunca la física reproducida.
# ---------------------------------------------------------------------------
def test_estimar_sdm_desde_ficha_devuelve_a_ref_en_convencion_unitless():
    # Regresión directa del bug de unidades: a_ref debe venir en la misma
    # convención (n × Ns, NO en voltios) que usa ASP-ST1-T40 -- del orden de
    # decenas/cientos para un panel normal de 60-72 celdas, nunca ~1-4 (eso
    # sería el valor en voltios, el síntoma exacto del bug).
    panel = {
        "Voc_stc": 37.5, "Vmp_stc": 30.5, "Isc_stc": 8.5, "Imp_stc": 8.0,
        "N_s": 60, "tecnologia": "Mono-Si", "Tk_beta": -0.35, "Tk_alfa": 0.05,
    }
    res = estimar_sdm_desde_ficha(panel)
    assert res is not None
    assert 30 < res["a_ref"] < 200, (
        f"a_ref={res['a_ref']} fuera del rango unitless esperado (n×Ns) -- "
        f"¿volvió el bug de unidades (a_ref en voltios, ~1-4)?"
    )


def test_panel_real_uraba_activa_motor_iv_y_reproduce_ficha_stc():
    # El caso concreto que expuso ambos bugs (Imp_stc y unidades de a_ref):
    # antes de corregirlos, preparar_panel_iv() devolvía None para este
    # panel real (JA Solar JAM66D46-720/LB, sin SDM precalibrado).
    catalogo = cargar_catalogo_paneles()
    panel = catalogo["JA Solar JAM66D46-720/LB"]
    assert not tiene_sdm_completo(panel)  # este panel depende del ajuste on-demand

    resultado = preparar_panel_iv(panel)
    assert resultado is not None, (
        "preparar_panel_iv() no debe rechazar este panel real -- si esto "
        "falla, volvió el bug de Imp_stc o el de unidades de a_ref."
    )
    prueba = {**panel, **resultado}
    val = validar_sdm_vs_ficha(prueba, tolerancia_pct=5.0)
    assert val["validacion_ok"] is True, val


def test_mayoria_del_catalogo_real_activa_motor_iv():
    # Auditoría completa (30/31-ago-2026): antes de corregir Imp_stc +
    # unidades de a_ref, 0 de 76 paneles reales del catálogo activaban el
    # ajuste on-demand. Tras esos 2 fixes: 62/76. Tras agregar N_s estimado
    # (por analogía real con ASP-ST1-T40) a los 10 paneles Solar First que
    # solo les faltaba ese dato: 72/76. Umbral conservador (65) para no
    # romper el test con cambios normales al catálogo real, mientras sigue
    # detectando una regresión grande si algo de esto se rompe.
    catalogo = cargar_catalogo_paneles()
    activa_ok = sum(
        1 for p in catalogo.values()
        if tiene_sdm_completo(p) or preparar_panel_iv(p) is not None
    )
    assert activa_ok >= 65, (
        f"solo {activa_ok}/{len(catalogo)} paneles reales activan Motor IV -- "
        f"muy por debajo de los 72/76 medidos tras los fixes de Imp_stc, "
        f"unidades de a_ref, y N_s estimado para Solar First; investigar "
        f"antes de continuar."
    )


def test_solar_first_activa_motor_iv_con_ns_estimado():
    # Los 10 paneles reales de la familia Solar First (ST1/ST2) no publican
    # N_s en su ficha -- estimado el 31-ago-2026 (pedido explícito del
    # usuario) por analogía con ASP-ST1-T40 (mismas dimensiones físicas
    # 1200x600mm, mismo Voc ~116V para ST1; ST2 con la mitad de celdas,
    # consistente con su Voc ~59V siendo casi exactamente la mitad).
    # Marcado como "Estimado -- no confirmado por fabricante" en el Excel
    # real, sin tocar la política de no inventar coeficientes de
    # temperatura para esta misma familia.
    catalogo = cargar_catalogo_paneles()
    modelos_st1 = [f"Solar First ST1-{n}" for n in (72, 64, 56, 48, 40, 32, 24, 16)]
    modelos_st2 = ["Solar First ST2-80", "Solar First ST2-85"]
    for nombre in modelos_st1 + modelos_st2:
        panel = catalogo[nombre]
        assert panel.get("N_s"), f"{nombre} debería tener N_s estimado"
        assert panel.get("confianza", "").lower().startswith("estimado"), (
            f"{nombre}: la confianza debe declarar que el N_s es estimado, "
            f"no del fabricante"
        )
        resultado = preparar_panel_iv(panel)
        assert resultado is not None, f"{nombre} debería activar Motor IV"
        prueba = {**panel, **resultado}
        val = validar_sdm_vs_ficha(prueba)  # tolerancia por defecto (6.0%, ver docstring)
        assert val["validacion_ok"] is True, (nombre, val)


# ---------------------------------------------------------------------------
# Coherencia modelo lineal (curva_electrica_temperatura) vs. SDM completo
# (Motor IV) -- pedido explícito del usuario, 30-ago-2026. Usa ASP-ST1-T40,
# el único panel de esta app con SDM auditado contra VBA (ver docstring de
# validar_sdm_vs_ficha: Voc/Isc/Pmax/FF ya verificados ahí) -- sin invocar
# pvlib.fit_desoto() (ya calibrado), así que es 100% determinista.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "T_cel, tol_voc_pct, tol_vmp_pct",
    [
        # Tolerancias recalibradas 2-sep-2026 tras migrar el motor SDM de
        # De Soto 2006 a PVsyst v6 (calcparams_pvsyst, ver
        # DIAGNOSTICO_MOTOR_PVSYST.md) -- el nuevo modelo de Gamma(T) via
        # mu_gamma cambia ligeramente la respuesta térmica de Voc/Vmp frente
        # al modelo lineal simplificado.
        (-5.0, 4.5, 1.5),      # frío: Voc dif real ~3.8%, Vmp dif real ~1.0%
        (36.35, 2.5, 1.5),     # real: Voc dif real ~1.8%, Vmp dif real ~0.7%
        (41.94, 3.5, 1.5),     # extremo: Voc dif real ~2.8%, Vmp dif real ~1.1%
    ],
)
def test_coherencia_modelo_lineal_vs_sdm_asp_st1_t40(T_cel, tol_voc_pct, tol_vmp_pct):
    panel = ASP_ST1_T40
    N = 8
    voc_lin = calcular_voc_string(N, panel["Voc_stc"], panel["Tk_beta"], T_cel)
    vmp_lin = calcular_vmp_string(N, panel["Vmp_stc"], panel["Tk_beta"], T_cel)
    r = resolver_curva_iv(1000.0, T_cel, panel, n_puntos=0)
    voc_sdm = r["Voc"] * N
    vmp_sdm = r["Vmp"] * N

    dif_voc_pct = abs(voc_sdm - voc_lin) / voc_lin * 100
    dif_vmp_pct = abs(vmp_sdm - vmp_lin) / vmp_lin * 100
    assert dif_voc_pct < tol_voc_pct, (
        f"Voc lineal ({voc_lin:.1f}V) diverge {dif_voc_pct:.1f}% del SDM "
        f"({voc_sdm:.1f}V) a T={T_cel}°C -- más de lo ya documentado."
    )
    assert dif_vmp_pct < tol_vmp_pct, (
        f"Vmp lineal ({vmp_lin:.1f}V) diverge {dif_vmp_pct:.1f}% del SDM "
        f"({vmp_sdm:.1f}V) a T={T_cel}°C -- más de lo ya documentado."
    )
