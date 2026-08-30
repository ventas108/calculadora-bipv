"""
Regresión: ficha de conversión app → PVsyst (módulo custom + Uc/Uv).

Ver DIAGNOSTICO_MODELO_TERMICO_UC_UV.md.
"""
from calculos.ficha_pvsyst import (
    EQUIVALENCIA_K_BIPV_UC_UV,
    generar_ficha_conversion_pvsyst,
)

PANEL_JASOLAR = {
    "nombre": "JAM66D46-720/LB",
    "marca": "JA Solar",
    "tecnologia": "Mono PERC bifacial",
    "Pmax_stc": 720.0,
    "Voc_stc": 49.00,
    "Vmp_stc": 41.19,
    "Isc_stc": 18.59,
    "Imp": 17.48,
    "NOCT": 45.0,
    "Tk_beta": -0.25,
    "Tk_gamma": -0.35,
    "area_m2": 3.1064,
}

# Panel REAL del proyecto Teusaquillo (fachada BIPV vertical, Bogotá) — mismos
# valores que datos/tecnologias_bipv.py::ASP_ST1_T40. A propósito usa el
# esquema de MODULOS_BIPV (fabricante/Imp_stc/Tk_alfa), NO el del catálogo
# Excel (marca/Imp) — la Fase 3 del plan pedía anclar la regresión a este
# caso real precisamente porque expone el segundo esquema.
PANEL_TEUSAQUILLO = {
    "nombre": "ASP-ST1-T40",
    "fabricante": "SolTech Energy LaTam",
    "tecnologia": "CdTe",
    "Pmax_stc": 63.0,
    "Voc_stc": 116.0,
    "Vmp_stc": 86.4,
    "Isc_stc": 0.80,
    "Imp_stc": 0.70,
    "NOCT": 45.0,
    "Tk_beta": -0.321,
    "Tk_alfa": 0.060,
    "Tk_gamma": -0.214,
    "area_m2": 0.72,
}


def test_ficha_incluye_todos_los_parametros_electricos_del_panel():
    ficha = generar_ficha_conversion_pvsyst(PANEL_JASOLAR, "Fachada BIPV", 1.3)
    assert "JAM66D46-720/LB" in ficha
    assert "720" in ficha       # Pnom
    assert "41.19" in ficha     # Vmp
    assert "49" in ficha        # Voc
    assert "18.59" in ficha     # Isc
    assert "17.48" in ficha     # Imp
    assert "45" in ficha        # NOCT
    assert "-0.25" in ficha     # Tk_beta
    assert "-0.35" in ficha     # Tk_gamma


def test_ficha_marca_ausencia_de_coeficiente_isc_en_vez_de_inventarlo():
    ficha = generar_ficha_conversion_pvsyst(PANEL_JASOLAR, "Fachada BIPV", 1.3)
    assert "μIsc" in ficha
    assert "NO disponible" in ficha


def test_ficha_usa_equivalencia_uc_uv_correcta_para_cada_k_bipv():
    for k_bipv, eq in EQUIVALENCIA_K_BIPV_UC_UV.items():
        ficha = generar_ficha_conversion_pvsyst(PANEL_JASOLAR, "Fachada BIPV", k_bipv)
        assert f"{eq['Uc_W_m2K']:.1f} W/m²K" in ficha
        assert eq["preset_pvsyst"] in ficha


def test_ficha_fachada_confinada_no_usa_preset_de_montaje_libre():
    # Regresión directa del riesgo que motivó esta ficha: una fachada BIPV
    # confinada (k=1.3) NO debe sugerir el preset "Free standing" (Uc=29),
    # que subestimaría la temperatura de operación real.
    ficha = generar_ficha_conversion_pvsyst(PANEL_JASOLAR, "Fachada BIPV", 1.3)
    assert "Free standing" not in ficha
    assert "Semi-integrated" in ficha


def test_ficha_advierte_cuando_k_bipv_no_es_uno_de_los_presets():
    ficha = generar_ficha_conversion_pvsyst(PANEL_JASOLAR, "Fachada BIPV", 1.22)
    assert "no es uno de los 4 presets estándar" in ficha


def test_ficha_semiventilado_usa_uc_interpolado_sin_preset_oficial():
    # k=1.15 (Pérgola/Marquesina) no tiene preset oficial de PVsyst -- Uc
    # interpolado entre Free standing (29.0) y Semi-integrated (20.0).
    ficha = generar_ficha_conversion_pvsyst(PANEL_JASOLAR, "Pérgola / sombreadero", 1.15)
    assert "24.5 W/m²K" in ficha
    assert "Sin preset oficial" in ficha


def test_ficha_maneja_campos_faltantes_sin_reventar():
    panel_incompleto = {"nombre": "Panel sin datos"}
    ficha = generar_ficha_conversion_pvsyst(panel_incompleto, "Granja fotovoltaica", 1.0)
    assert "no disponible en el catálogo" in ficha


# ── Regresión anclada al caso real Teusaquillo (Fase 3 del plan) ──────────────
# Panel real de MODULOS_BIPV (fabricante/Imp_stc/Tk_alfa), no del catálogo
# Excel (marca/Imp) — expone el bug real de esquema encontrado en la auditoría
# del 30-ago-2026: la primera versión de generar_ficha_conversion_pvsyst()
# solo leía las claves del esquema Excel.

def test_ficha_teusaquillo_lee_fabricante_no_solo_marca():
    ficha = generar_ficha_conversion_pvsyst(PANEL_TEUSAQUILLO, "Fachada BIPV", 1.3)
    assert "SolTech Energy LaTam" in ficha
    assert "Fabricante / modelo   : SolTech Energy LaTam / ASP-ST1-T40" in ficha


def test_ficha_teusaquillo_lee_imp_stc_no_solo_imp():
    ficha = generar_ficha_conversion_pvsyst(PANEL_TEUSAQUILLO, "Fachada BIPV", 1.3)
    assert "Imp (STC)             : 0.7 A" in ficha


def test_ficha_teusaquillo_reporta_coeficiente_isc_real_no_disponible():
    # Bug real: antes del fix, este panel SÍ tiene Tk_alfa (+0.06 %/°C) pero
    # la ficha decía "NO disponible" porque nunca leía esa clave.
    ficha = generar_ficha_conversion_pvsyst(PANEL_TEUSAQUILLO, "Fachada BIPV", 1.3)
    assert "μIsc                  : 0.06 %/°C" in ficha
    assert "NO disponible" not in ficha


def test_ficha_teusaquillo_usa_preset_fachada_confinada():
    # Teusaquillo es una fachada BIPV vertical real -- k=1.3, no montaje libre.
    ficha = generar_ficha_conversion_pvsyst(PANEL_TEUSAQUILLO, "Fachada BIPV", 1.3)
    assert "Semi-integrated" in ficha
    assert "20.0 W/m²K" in ficha
