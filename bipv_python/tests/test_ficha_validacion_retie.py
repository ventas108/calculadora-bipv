# -*- coding: utf-8 -*-
"""
Tests de calculos/ficha_validacion_retie.py.

Foco explícito: el usuario advirtió (27-ago-2026) que NO debía quedar
hardcodeado al proyecto Urabá -- varios de estos tests usan A PROPÓSITO
datos de proyectos completamente distintos (1 inversor, 3 inversores,
BIPV residencial pequeño) para demostrar que el motor es universal, no
solo "funciona con los números de Urabá".
"""
import pytest

from calculos.ficha_validacion_retie import (
    construir_config_retie,
    calcular_retie,
    validar_retie,
    generar_ficha_svg,
    calibre_comercial_superior,
)


def test_calibre_comercial_superior_redondea_hacia_arriba():
    assert calibre_comercial_superior(140.0) == 160
    assert calibre_comercial_superior(160.0) == 160
    assert calibre_comercial_superior(0.0) == 16


def test_calibre_comercial_superior_none_si_falta_dato():
    assert calibre_comercial_superior(None) is None


def test_calibre_comercial_superior_none_si_excede_tabla():
    assert calibre_comercial_superior(5000.0) is None


# ══════════════════════════════════════════════════════════════════════════
# Caso Urabá (2 inversores) -- referencia conocida, para verificar que los
# números coinciden con los ya validados manualmente.
# ══════════════════════════════════════════════════════════════════════════
def _config_uraba(**overrides):
    base = dict(
        nombre_proyecto="Agrivoltaico Uraba", panel_nombre="JA Solar JAM66D46-720/LB",
        potencia_w=720.0, inversor_nombre="Growatt MAX 100KTL3 LV",
        potencia_ac_kw_unidad=100.0, n_inversores=2, tension_salida_v=400.0,
        n_paneles=306, n_serie=18, strings_por_inversor=[9, 8],
    )
    base.update(overrides)
    return construir_config_retie(**base)


def test_uraba_calculos_conocidos():
    cfg = _config_uraba()
    calc = calcular_retie(cfg)
    assert calc["potencia_dc_kwp"] == 220.32
    assert calc["potencia_ac_kw"] == 200.0
    assert calc["relacion_dc_ac"] == pytest.approx(1.1016, abs=1e-3)
    assert calc["corriente_total_a"] == pytest.approx(288.7, abs=0.1)
    assert calc["corriente_diseno_total_a"] == 360.8  # exacto, ver test de doble redondeo abajo
    assert calc["breaker_general_a"] == 400
    assert calc["breaker_inversor_a"] == 200
    assert calc["pdc_por_inversor_kwp"] == [116.64, 103.68]


def test_corriente_diseno_no_tiene_doble_redondeo():
    # Bug real encontrado en auditoria (27-ago-2026): calcular i_diseno
    # multiplicando el factor por corriente_total_a YA REDONDEADA daba
    # 360.9 A en vez de 360.8 A -- un numero DISTINTO al que muestra
    # Pagina 20 (diagrama_unifilar.py) para el mismo proyecto Uraba.
    # Verificado comparando contra el calculo directo sin redondeo
    # intermedio (round(1.25 * p_ac_total_kW * 1000 / (sqrt(3) * V), 1),
    # mismo patron que proteccion_ac_A en diagrama_unifilar.py).
    from math import sqrt
    cfg = _config_uraba()
    calc = calcular_retie(cfg)
    esperado = round(1.25 * 200.0 * 1000 / (sqrt(3) * 400.0), 1)
    assert calc["corriente_diseno_total_a"] == esperado
    assert esperado == 360.8  # confirma que el bug SI cambiaba el resultado


def test_uraba_validaciones_balance_pendiente():
    cfg = _config_uraba()
    calc = calcular_retie(cfg)
    checks = validar_retie(cfg, calc)
    balance = next(c for c in checks if c["titulo"] == "Balance entre inversores")
    assert balance["nivel"] == "PENDIENTE"  # diferencia 1.17 vs 1.04 > 0.10


def test_uraba_genera_svg_valido():
    cfg = _config_uraba()
    calc = calcular_retie(cfg)
    checks = validar_retie(cfg, calc)
    svg = generar_ficha_svg(cfg, calc, checks)
    assert svg.startswith("<?xml")
    assert "<svg" in svg
    assert "220,32" in svg or "220.32" in svg  # potencia DC visible en el SVG


def test_svg_no_se_titula_diagrama_unifilar():
    # Bug real encontrado en auditoria (27-ago-2026): el titulo dentro del
    # SVG decia literalmente "DIAGRAMA UNIFILAR FOTOVOLTAICO" (heredado
    # sin cambiar del script original), pero este documento NO es el
    # esquema de linea unica -- eso es Pagina 20. Confundia cual era cual
    # si se archivaban los dos documentos del mismo proyecto.
    cfg = _config_uraba()
    calc = calcular_retie(cfg)
    checks = validar_retie(cfg, calc)
    svg = generar_ficha_svg(cfg, calc, checks)
    assert "DIAGRAMA UNIFILAR" not in svg
    assert "FICHA DE VALIDACIÓN RETIE" in svg


# ══════════════════════════════════════════════════════════════════════════
# Universalidad -- proyectos DISTINTOS a Urabá, un solo inversor.
# ══════════════════════════════════════════════════════════════════════════
def test_proyecto_bipv_un_inversor_no_revienta():
    cfg = construir_config_retie(
        nombre_proyecto="Fachada BIPV Residencial", panel_nombre="ASP-ST1-T40",
        potencia_w=200.0, inversor_nombre="Growatt MIN 5000TL-X",
        potencia_ac_kw_unidad=5.0, n_inversores=1, tension_salida_v=220.0,
        n_paneles=40, n_serie=10, strings_por_inversor=[4],
    )
    calc = calcular_retie(cfg)
    assert calc["potencia_dc_kwp"] == 8.0
    assert calc["potencia_ac_kw"] == 5.0
    assert calc["pdc_por_inversor_kwp"] == [8.0]
    # Con 1 solo inversor no hay "balance entre inversores" que calcular.
    assert calc["dcac_por_inversor"] == [pytest.approx(1.6)]
    checks = validar_retie(cfg, calc)
    assert not any(c["titulo"] == "Balance entre inversores" for c in checks)
    svg = generar_ficha_svg(cfg, calc, checks)
    assert "<svg" in svg
    assert "INV-01" in svg
    assert "INV-02" not in svg  # no debe inventar un segundo inversor


def test_proyecto_tres_inversores_genera_tres_filas():
    cfg = construir_config_retie(
        nombre_proyecto="Planta FV Comercial", panel_nombre="Trina Vertex 550",
        potencia_w=550.0, inversor_nombre="Huawei SUN2000-100KTL",
        potencia_ac_kw_unidad=100.0, n_inversores=3, tension_salida_v=400.0,
        n_paneles=900, n_serie=20, strings_por_inversor=[15, 15, 15],
    )
    calc = calcular_retie(cfg)
    assert calc["potencia_dc_kwp"] == 495.0
    assert calc["potencia_ac_kw"] == 300.0
    assert len(calc["pdc_por_inversor_kwp"]) == 3
    checks = validar_retie(cfg, calc)
    balance = next(c for c in checks if c["titulo"] == "Balance entre inversores")
    assert balance["nivel"] == "OK"  # las 3 ramas están perfectamente balanceadas
    assert "INV-01=" in balance["detalle"] and "INV-03=" in balance["detalle"]
    svg = generar_ficha_svg(cfg, calc, checks)
    assert "INV-01" in svg and "INV-02" in svg and "INV-03" in svg


def test_proyecto_sin_strings_por_inversor_no_calcula_balance():
    # El llamador no dio la distribución por inversor -- el motor NO debe
    # asumir una distribución pareja, debe dejarlo pendiente/vacío.
    cfg = construir_config_retie(
        nombre_proyecto="Proyecto sin desglose", potencia_w=450.0,
        potencia_ac_kw_unidad=50.0, n_inversores=2, tension_salida_v=380.0,
        n_paneles=100, n_serie=20,
    )
    calc = calcular_retie(cfg)
    assert calc["pdc_por_inversor_kwp"] == []
    assert calc["dcac_por_inversor"] == []
    checks = validar_retie(cfg, calc)
    assert not any(c["titulo"] == "Distribución de strings" for c in checks)
    svg = generar_ficha_svg(cfg, calc, checks)
    assert "<svg" in svg  # no revienta con datos incompletos


def test_config_sin_datos_no_revienta():
    cfg = construir_config_retie()
    calc = calcular_retie(cfg)
    assert calc["potencia_dc_kwp"] is None
    assert calc["breaker_general_a"] is None
    checks = validar_retie(cfg, calc)
    assert len(checks) > 0  # sigue devolviendo el checklist de pendientes
    svg = generar_ficha_svg(cfg, calc, checks)
    assert "<svg" in svg


# ══════════════════════════════════════════════════════════════════════════
# Validaciones individuales -- Voc frío, ventana MPPT, string incompleto.
# ══════════════════════════════════════════════════════════════════════════
def test_voc_frio_error_si_supera_vdc_max():
    cfg = construir_config_retie(
        potencia_w=450.0, voc_v=49.5, coef_voc_pct_c=-0.25,
        n_paneles=20, n_serie=20, temperatura_minima_diseno_c=-10.0,
        potencia_ac_kw_unidad=10.0, n_inversores=1, vdc_max_v=900.0,
    )
    calc = calcular_retie(cfg)
    # Voc frio = 49.5 * (1 + (-0.25/100)*(-10-25)) * 20 = 49.5*1.0875*20 ≈ 1076.6 V > 900
    assert calc["voc_string_frio_v"] > 900
    checks = validar_retie(cfg, calc)
    voc_check = next(c for c in checks if c["titulo"] == "Voc del string en frío")
    assert voc_check["nivel"] == "ERROR"


def test_voc_frio_ok_si_no_supera_vdc_max():
    cfg = construir_config_retie(
        potencia_w=450.0, voc_v=49.5, coef_voc_pct_c=-0.25,
        n_paneles=20, n_serie=10, temperatura_minima_diseno_c=-10.0,
        potencia_ac_kw_unidad=10.0, n_inversores=1, vdc_max_v=900.0,
    )
    calc = calcular_retie(cfg)
    checks = validar_retie(cfg, calc)
    voc_check = next(c for c in checks if c["titulo"] == "Voc del string en frío")
    assert voc_check["nivel"] == "OK"


def test_ventana_mppt_error_si_fuera_de_rango():
    cfg = construir_config_retie(
        potencia_w=450.0, vmp_v=41.5, n_paneles=8, n_serie=8,
        potencia_ac_kw_unidad=5.0, n_inversores=1,
        vmppt_min_v=500.0, vmppt_max_v=800.0,
    )
    calc = calcular_retie(cfg)
    assert calc["vmp_string_stc_v"] == 332.0  # fuera del rango 500-800
    checks = validar_retie(cfg, calc)
    mppt_check = next(c for c in checks if c["titulo"] == "Ventana MPPT")
    assert mppt_check["nivel"] == "ERROR"


def test_string_incompleto_marca_error():
    cfg = construir_config_retie(potencia_w=450.0, n_paneles=25, n_serie=10)
    calc = calcular_retie(cfg)
    checks = validar_retie(cfg, calc)
    mod_check = next(c for c in checks if c["titulo"] == "Cantidad de módulos")
    assert mod_check["nivel"] == "ERROR"
