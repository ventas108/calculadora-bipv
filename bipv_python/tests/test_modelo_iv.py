"""
Tests de calculos.modelo_iv -- sin cobertura directa hasta el 30-ago-2026.

Auditoría pedida por el usuario ("confírmalo en Motor IV también"): verificar
que el modelo lineal usado por curva_electrica_temperatura()/
evaluar_compatibilidad_string() (Voc_stc/Vmp_stc escalados por Tk_beta) es
coherente con el modelo físico completo del propio Motor IV (SDM De Soto
2006). Durante la auditoría se encontró y corrigió un bug real (ver los dos
primeros tests) que impedía completar la comprobación para paneles reales
del catálogo Excel.
"""
import copy

import pytest

from calculos.modelo_iv import resolver_curva_iv, validar_sdm_vs_ficha
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
# Coherencia modelo lineal (curva_electrica_temperatura) vs. SDM completo
# (Motor IV) -- pedido explícito del usuario, 30-ago-2026. Usa ASP-ST1-T40,
# el único panel de esta app con SDM auditado contra VBA (ver docstring de
# validar_sdm_vs_ficha: Voc/Isc/Pmax/FF ya verificados ahí) -- sin invocar
# pvlib.fit_desoto() (ya calibrado), así que es 100% determinista.
#
# NOTA: los paneles reales del catálogo Excel (JA Solar Urabá, etc.) NO
# sirven para esta comprobación todavía: pvlib.fit_desoto() (0.15.2) da
# resultados NO DETERMINISTAS para sus datos entre una corrida y otra en
# este entorno -- a veces converge, a veces falla con RuntimeError de
# Jacobiano, a veces con un TypeError interno de pvlib ("tuple indices must
# be integers, not str") para EXACTAMENTE los mismos parámetros de entrada.
# Es un hallazgo real y separado (documentado en el diagnóstico), fuera del
# código de esta app -- el auto-chequeo de preparar_panel_iv() (rechazar
# cualquier SDM que no reproduzca la ficha STC dentro de 5%) ya protege al
# usuario de que se muestre una curva incorrecta cuando esto pasa.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "T_cel, tol_voc_pct, tol_vmp_pct",
    [
        (-5.0, 3.0, 8.0),      # frío: Voc dif real ~2.2%, Vmp dif real ~6.4%
        (36.35, 2.0, 4.0),     # real: Voc dif real ~1.0%, Vmp dif real ~2.7%
        (41.94, 2.0, 5.0),     # extremo: Voc dif real ~1.5%, Vmp dif real ~4.0%
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
