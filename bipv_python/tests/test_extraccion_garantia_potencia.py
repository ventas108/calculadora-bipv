# -*- coding: utf-8 -*-
"""Tests de calculos/pdf_panel_extractor.py::_extraer_garantia_potencia()
(degradación no lineal -- 7-sep-2026). Casos con texto sintético representativo
de fichas reales (formato de garantía lineal Tier 1), sin depender de PDFs
reales ni de red -- mismo patrón que el resto de la suite offline."""
from calculos.pdf_panel_extractor import _extraer_garantia_potencia


def test_ficha_estilo_ingles_tier1():
    texto = (
        "Linear Power Warranty\n"
        "97.5% in the first year, then a maximum annual degradation of 0.55%\n"
        "per year, ensuring 87.4% of nominal power at year 25.\n"
    )
    r = _extraer_garantia_potencia(texto)
    # 97.5% en año 1 -> caída = 100 - 97.5 = 2.5%, pero el extractor no resta;
    # busca directamente el texto de la caída/degradación, no el nivel
    # garantizado -- este texto de ejemplo no menciona "2.5%" explícito, así
    # que sólo se confirma la tasa lineal (0.55%), que sí matchea.
    assert r["degradacion_lineal_pct_anio"] == 0.55


def test_ficha_con_caida_explicita_anio1_en_espanol():
    texto = (
        "Garantía de potencia lineal\n"
        "Año 1: 2.5% de degradación\n"
        "Degradación anual: 0.55% por año hasta el año 25\n"
    )
    r = _extraer_garantia_potencia(texto)
    assert r["degradacion_anio1_pct"] == 2.5
    assert r["degradacion_lineal_pct_anio"] == 0.55


def test_ficha_sin_texto_de_garantia_no_inventa():
    texto = "Pmax: 550W  Voc: 49.5V  Isc: 14.2A  Vmp: 41.8V  Imp: 13.2A\n"
    r = _extraer_garantia_potencia(texto)
    assert r["degradacion_anio1_pct"] is None
    assert r["degradacion_lineal_pct_anio"] is None


def test_valor_implausible_se_descarta_no_se_fuerza():
    # "50% per year" no es una tasa de degradación real -- fuera del rango
    # plausible (0.1-1.2%/año), debe descartarse en vez de aceptarse ciego.
    texto = "Efficiency drops 50% per year under extreme conditions (edge case).\n"
    r = _extraer_garantia_potencia(texto)
    assert r["degradacion_lineal_pct_anio"] is None
