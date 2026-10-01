"""Spec 03-dimensionamiento/tension-maxima-modulo.

El Voc en frío del string se compara con el MENOR entre la tensión DC máxima
del inversor y la tensión máxima de sistema del módulo (VSYS de la ficha).
Caso real: Teusaquillo, ASP-ST1-T40 (VSYS 1.000 V) con un Sungrow SG8.0RT
(1.100 V). Con 8 en serie el Voc a 0 °C es 1.002,5 V: pasa el módulo.
"""
from pathlib import Path

import pytest

from calculos.comparador_inversores import filtrar_inversores_compatibles, mejor_n_por_inversor
from calculos.diseno_electrico_multisup import rango_n_serie, validar_diseno_electrico
from calculos.dimensionamiento import (
    curva_electrica_temperatura,
    evaluar_compatibilidad_string,
    interpretar_curva_electrica,
    optimizar_n_serie,
)
from calculos.ficha_inversor import margen_voc
from calculos.ficha_validacion_retie import calcular_retie, construir_config_retie, validar_retie
from calculos.tension_modulo import limite_voc, v_sistema_modulo
from datos.tecnologias_bipv import MODULOS_BIPV

_RAIZ = Path(__file__).resolve().parents[1]
_ASP = dict(MODULOS_BIPV["ASP-ST1-T40"])
_ASP_SIN_DATO = {k: v for k, v in _ASP.items() if k != "V_sistema_max"}
_SPR = dict(MODULOS_BIPV["SPR-E20-327 (E20-327NE-WHT-D)"])
# Sungrow SG8.0RT tal como está en el catálogo.
_SG8 = {"nombre": "SG8.0RT", "Vdc_max": 1100.0, "Vmppt_min": 160.0, "Vmppt_activo_min": 160.0,
        "Vmppt_max": 1000.0, "I_max_tracker": 12.5, "Isc_max_tracker": 18.0,
        "n_trackers": 2, "N_mppt": 2, "n_strings_tracker": 1, "P_ac_nom_W": 8000.0}
_T5 = {"T_frio": 5.0, "T_real": 36.35, "T_extremo": 41.94}
_T0 = {"T_frio": 0.0, "T_real": 36.35, "T_extremo": 41.94}


# ── El límite ────────────────────────────────────────────────────────────────
def test_familia_asp_tiene_1000_v_de_la_ficha():
    for t in (10, 20, 30, 40, 50, 60, 70):
        assert MODULOS_BIPV[f"ASP-ST1-T{t}"]["V_sistema_max"] == 1000.0


def test_limite_es_el_menor_y_dice_quien_manda():
    assert limite_voc(_ASP, _SG8) == {"limite_v": 1000.0, "origen": "modulo",
                                      "vdc_inversor_v": 1100.0, "v_sistema_modulo_v": 1000.0}
    assert limite_voc(_ASP_SIN_DATO, _SG8)["origen"] == "inversor"
    assert limite_voc(_ASP_SIN_DATO, _SG8)["limite_v"] == 1100.0
    assert limite_voc(_ASP, {"Vdc_max": 1000.0})["origen"] == "inversor"     # empate
    assert limite_voc(_ASP, {"Vdc_max": 600.0})["limite_v"] == 600.0
    assert limite_voc(_ASP_SIN_DATO, {})["origen"] is None
    assert v_sistema_modulo({"V_sistema_max": "1500"}) == 1500.0
    assert v_sistema_modulo({"V_sistema_max": 0}) is None and v_sistema_modulo(None) is None


# ── 📐 Dimensionamiento / 📊 Producción ─────────────────────────────────────
def test_ocho_en_serie_a_0_grados_no_cabe_por_el_modulo():
    r = evaluar_compatibilidad_string(_ASP, _SG8, 8, N_strings_tracker=1, **_T0)
    assert r["compatible"] is False
    assert r["limite_voc_V"] == 1000.0 and r["limite_voc_origen"] == "modulo"
    assert any("módulo" in m and "1000" in m for m in r["mensajes"])


def test_sin_el_dato_todo_queda_como_antes():
    r = evaluar_compatibilidad_string(_ASP_SIN_DATO, _SG8, 8, N_strings_tracker=1, **_T0)
    assert r["compatible"] is True and r["limite_voc_origen"] == "inversor"


def test_siete_en_serie_queda_con_margen():
    r = evaluar_compatibilidad_string(_ASP, _SG8, 7, N_strings_tracker=1, **_T5)
    assert r["compatible"] is True and not r["alerta_margen"]
    assert r["Voc_frio"] == pytest.approx(864.1, abs=0.1)


def test_optimizador_marca_8_y_aprueba_7():
    por_n = {r.N_serie: r for r in optimizar_n_serie(_ASP, _SG8, N_strings_tracker=1, N_min=6, N_max=9, **_T5)}
    assert por_n[8].v1_voc_max == "ALERTA"          # 987,6 V: 1,2 % del límite de 1.000 V
    assert por_n[7].v1_voc_max == "OK"
    assert por_n[9].v1_voc_max == "FALLA"
    sin = {r.N_serie: r for r in optimizar_n_serie(_ASP_SIN_DATO, _SG8, N_strings_tracker=1, N_min=8, N_max=8, **_T5)}
    assert sin[8].v1_voc_max == "OK"                # 10,2 % frente a 1.100 V


def test_curva_e_interpretacion_nombran_al_modulo():
    curva = curva_electrica_temperatura(_ASP, _SG8, 8, N_strings_tracker=1, **_T0)
    assert curva["vdc_max"] == 1000.0 and curva["limite_voc_origen"] == "modulo"
    voc = interpretar_curva_electrica(curva)[0]
    assert voc["nivel"] == "critico" and "módulo" in voc["texto"]


# ── ⚖️ Comparador ───────────────────────────────────────────────────────────
def test_comparador_usa_el_limite_del_modulo():
    fila = filtrar_inversores_compatibles(_ASP, {"SG8.0RT": _SG8}, 8, T_frio=0.0, T_real=36.35,
                                          T_extremo=41.94).iloc[0]
    assert not fila["compatible"] and "módulo" in fila["motivo"]
    fila7 = filtrar_inversores_compatibles(_ASP, {"SG8.0RT": _SG8}, 7, T_frio=5.0, T_real=36.35,
                                           T_extremo=41.94).iloc[0]
    assert fila7["compatible"] and fila7["margen_voc_pct"] == pytest.approx(13.6, abs=0.1)


def test_mejor_n_del_comparador_es_7_para_teusaquillo():
    df = mejor_n_por_inversor(_ASP, {"SG8.0RT": _SG8}, 112, T_frio=5.0, T_real=36.35, T_extremo=41.94)
    fila = df.iloc[0]
    assert fila["N_serie"] == 7 and fila["strings"] == 16 and fila["nivel_voc"] == "🟢"
    assert fila["margen_voc_V"] == pytest.approx(1000.0 - 864.0, abs=1.0)


# ── 🗺️ Vista 3D ─────────────────────────────────────────────────────────────
def _inv_vista():
    return {"inversor_id": "INV-1", "clase": "string", "origen_ficha": "catalogo", "nombre": "SG8.0RT",
            "ficha": dict(_SG8), "eta_inversor": 0.97, "P_ac_nom_W": 8000.0}


def _sups(n_serie, n_par):
    return [
        {"uid": 1, "nombre": "Fachada", "tipo": "Fachada", "tilt_deg": 90, "azimuth_deg": 180, "area_m2": 81,
         "activa": True, "grupos": [{"gid": "G1", "topologia": "string", "inversor_id": "INV-1", "mppt": 1,
                                     "n_serie": n_serie, "n_paralelo": n_par}]},
        {"uid": 2, "nombre": "Techo", "tipo": "Techo", "tilt_deg": 10, "azimuth_deg": 180, "area_m2": 7,
         "activa": True, "grupos": [{"gid": "G1", "topologia": "string", "inversor_id": "INV-1", "mppt": 2,
                                     "n_serie": 4, "n_paralelo": 1}]},
    ]


_PANELES = {"Fachada": {"panel": _ASP, "nombre": "ASP-ST1-T40"},
            "Techo": {"panel": _SPR, "nombre": "SPR-E20-327"}}


def test_vista3d_ocho_en_serie_a_0_grados_bloquea_por_el_modulo():
    d = validar_diseno_electrico(_sups(8, 14), [_inv_vista()], _PANELES, {**_T0, "origen": "proyecto"})
    g = next(g for g in d["grupos"] if g["superficie"] == "Fachada")
    chk = {c["nombre"]: c for c in g["checks"]}["Voc en frío ≤ tensión máx. del módulo"]
    assert chk["estado"] == "rojo" and chk["limite"] == 1000.0
    assert any("módulo" in b for b in d["bloqueos"])


def test_vista3d_teusaquillo_siete_por_dieciseis_en_verde():
    d = validar_diseno_electrico(_sups(7, 16), [_inv_vista()], _PANELES, {**_T5, "origen": "proyecto"})
    assert d["bloqueos"] == []
    g = next(g for g in d["grupos"] if g["superficie"] == "Fachada")
    assert {c["nombre"]: c for c in g["checks"]}["Voc en frío ≤ tensión máx. del módulo"]["estado"] == "verde"
    # El techo (sin dato de módulo) sigue con el nombre de siempre.
    t = next(g for g in d["grupos"] if g["superficie"] == "Techo")
    assert "Voc en frío ≤ Vdc máximo" in {c["nombre"] for c in t["checks"]}


def test_rango_n_serie_respeta_el_modulo():
    ficha = {k: _SG8[k] for k in ("Vdc_max", "Vmppt_min", "Vmppt_activo_min", "Vmppt_max")}
    assert rango_n_serie(_ASP, ficha, _T0)[1] == 7
    assert rango_n_serie(_ASP_SIN_DATO, ficha, _T0)[1] == 8


# ── 📄 Reporte y 📋 RETIE ───────────────────────────────────────────────────
def test_margen_voc_con_panel():
    m = margen_voc(1002.5, _SG8, _ASP)
    assert m["nivel"] == "🔴" and m["origen"] == "modulo" and m["vdc_max_v"] == 1000.0
    assert margen_voc(1002.5, _SG8)["nivel"] == "🟢"          # sin panel: como antes
    assert margen_voc(864.1, _SG8, _ASP)["nivel"] == "🟢"


def test_retie_compara_con_el_modulo():
    base = dict(panel_nombre="ASP-ST1-T40", potencia_w=63.0, voc_v=116.0, vmp_v=86.4, isc_a=0.8,
                coef_voc_pct_c=-0.321, inversor_nombre="SG8.0RT", potencia_ac_kw_unidad=8.0,
                vdc_max_v=1100.0, vmppt_min_v=160.0, vmppt_max_v=1000.0, n_paneles=112,
                temperatura_minima_diseno_c=0.0)
    cfg = construir_config_retie(**base, n_serie=8, v_sistema_modulo_v=1000.0)
    voc = next(c for c in validar_retie(cfg, calcular_retie(cfg)) if c["titulo"] == "Voc del string en frío")
    assert voc["nivel"] == "ERROR" and "módulo" in voc["detalle"]
    cfg7 = construir_config_retie(**{**base, "n_paneles": 112}, n_serie=7, v_sistema_modulo_v=1000.0)
    voc7 = next(c for c in validar_retie(cfg7, calcular_retie(cfg7)) if c["titulo"] == "Voc del string en frío")
    assert voc7["nivel"] == "OK" and "módulo" in voc7["detalle"]
    sin = construir_config_retie(**base, n_serie=8)
    assert next(c for c in validar_retie(sin, calcular_retie(sin))
                if c["titulo"] == "Voc del string en frío")["nivel"] == "OK"


# ── 📋 Catálogo de paneles ──────────────────────────────────────────────────
def test_catalogo_lee_la_columna_y_usa_el_respaldo_de_la_familia():
    from datos.catalogo_paneles_excel import v_sistema_desde_fila
    assert v_sistema_desde_fila({"VsistemaMaxV": 1500}, "Otro-panel") == 1500.0
    assert v_sistema_desde_fila({}, "ASP-ST1-T40") == 1000.0          # respaldo de la ficha
    assert v_sistema_desde_fila({"VsistemaMaxV": 600}, "ASP-ST1-T40") == 600.0   # el Excel manda
    assert v_sistema_desde_fila({}, "Panel-sin-dato") is None


def test_catalogo_real_trae_el_dato_del_asp():
    from datos.catalogo_paneles_excel import cargar_catalogo_paneles
    cat = cargar_catalogo_paneles()
    assert cat["ASP-ST1-T40"]["V_sistema_max"] == 1000.0


def test_extractor_lee_la_tension_maxima_del_sistema():
    from calculos.pdf_panel_extractor import _apply_patterns
    assert _apply_patterns("Voltaje máximo del sistema VSYS(V) 1000\n")["V_sistema"] == 1000.0
    assert _apply_patterns("Maximum System Voltage 1500V DC (IEC)\n")["V_sistema"] == 1500.0
    assert _apply_patterns("Max. System Voltage [V] 1000\n")["V_sistema"] == 1000.0


def test_paginas_guardan_y_pasan_el_dato():
    cat = (_RAIZ / "pages" / "14_📋_Catálogo_Paneles.py").read_text(encoding="utf-8")
    assert cat.count('"VsistemaMaxV"') >= 2                         # formulario y edición
    retie = (_RAIZ / "pages" / "21_📋_Ficha_Validacion_RETIE.py").read_text(encoding="utf-8")
    assert "v_sistema_modulo_v=" in retie
    rep = (_RAIZ / "pages" / "10_📄_Reporte_PDF.py").read_text(encoding="utf-8")
    assert "margen_voc(_ev_pdf.get(\"Voc_frio\"), _inv_dim_pdf, " in rep


def test_el_diseno_del_xlsm_pasa_el_modulo_a_menos_5_grados():
    """La hoja Excel original aprobaba 8 en serie con el Growatt a −5 °C
    (1.017 V frente a 1.100 V); con la ficha del módulo no cabe."""
    from datos.catalogo_inversores import INVERSORES
    r = evaluar_compatibilidad_string(_ASP, INVERSORES["Growatt-MID15KTL3-X"], 8, T_frio=-5.0,
                                      T_real=36.35, T_extremo=41.94, N_strings_tracker=8)
    assert r["compatible"] is False and r["Voc_frio"] == pytest.approx(1017.2, abs=0.5)
    assert r["limite_voc_origen"] == "modulo"
