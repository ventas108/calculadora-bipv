# -*- coding: utf-8 -*-
"""Spec ``07-informes/reporte-granja-completo`` (1-oct-2026).

Reporte real de la Granja Solar Apartadó (Urabá): no traía la vista 3D del
campo ni el plano eléctrico de 🌾 Granja FV (secciones 9 y 8), ni las gráficas
de luz en el suelo, la maquinaria o las revisiones del campo. Además decía
«Factor Mismatch aplicado 100 %» con calidad y mismatch aplicados, la altitud
salía «—», usaba textos de fachada («Área de fachada», «al edificio»,
«Bogotá», «CdTe») en una granja y no avisaba de la suciedad en 0 %. El
catálogo traía el Growatt MAX 100KTL3 LV con 1.500 V DC (ficha oficial:
1.100 V, MPPT 180–1.000 V) y la app daba 🟢 a 28 en serie (Voc 1.386 V).
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

import calculos.reporte_granja as rg
from calculos.ficha_inversor import alertas_ficha_inversor, margen_voc
from calculos.granja_electrico import diseno_desde_estado
from calculos.reporte_produccion import (
    altitud_proyecto, aviso_soiling, etiquetas_tipo, filas_mismatch, nota_poa, nota_pr,
)

RAIZ = Path(__file__).resolve().parents[1]
PAGINA = next((RAIZ / "pages").glob("10_*Reporte_PDF.py"))
JAM = {"nombre": "JAM66D46-720/LB", "dimensiones_mm": "2384x1303x33 mm", "area_m2": 3.1064,
       "Pmax_stc": 720.0, "Imp_stc": 17.48, "Vmp_stc": 41.19, "Isc_stc": 18.59, "Voc_stc": 49.0, "Tk_beta": -0.25}
# Terreno real del reporte: 30 × 100 m, 13 filas de 2 × 12 módulos, pitch 6,60 m
GEO = {"ancho_terreno_m": 30.0, "largo_terreno_m": 100.0, "modulos_pendiente": 2, "orientacion": "horizontal",
       "modulos_por_mesa": 12, "mesas_por_fila": 1, "pasillo_m": 3.0, "pitch_m": 6.60, "altura_libre_m": 2.4}
INV_CATALOGO = {"nombre": "Growatt MAX 100KTL3 LV", "Vdc_max": 1500.0, "Vmppt_min": 200.0, "Vmppt_max": 1300.0,
                "Vmppt_activo_min": 850.0, "I_max_tracker": 26.0, "Isc_max_tracker": 32.5, "P_ac_nom_W": 100_000.0}
INV_FICHA = {**INV_CATALOGO, "Vdc_max": 1100.0, "Vmppt_min": 180.0, "Vmppt_max": 1000.0, "Vmppt_activo_min": 600.0,
             "I_max_tracker": 32.0, "Isc_max_tracker": 40.0}
RES = {"P_stc_kW": 221.76, "E_dc_anual_kWh": 347_818.0, "E_ac_anual_kWh": 335_307.0, "PR": 0.823,
       "Y_f": 1512.0, "Y_r": 1838.0, "CF_pct": 17.3, "perdida_inv_kWh": 8_695.0, "perdida_temp_kWh": 24_500.0,
       "pct_calidad_modulo_aplicado": 3.0, "pct_mismatch_fab_aplicado": 2.0,
       "perdida_calidad_modulo_kWh": 10_997.0, "perdida_mismatch_fab_kWh": 7_111.0}
LUZ = {"y_m": [i * 0.33 for i in range(21)], "pct": [40 + i * 2 for i in range(21)],
       "mensual_pct": [[40 + i * 2 + m for i in range(21)] for m in range(12)],
       "geometria": {"huella": 2.59, "pitch": 6.6}, "media_pct": 60.0, "media_kwh_m2": 1008.0,
       "referencia_kwh_m2": 1683.0, "bajo_mesa_pct": 42.0, "entre_filas_pct": 72.0, "homogeneidad": 0.35,
       "min_pct": 40.0, "max_pct": 80.0}


def _estado(**kw):
    e = {"tipo_instalacion": "Granja fotovoltaica", "panel_dict": JAM, "panel_nombre_final": JAM["nombre"],
         "N_paneles_final": 308, "N_serie": 22, "reparto_strings_inversores": [7, 7],
         "inversor_dict_dim": INV_FICHA, "inversor_nombre_dim": INV_FICHA["nombre"],
         "produccion_n_inversores": 2, "produccion_p_ac_total_w": 200_000.0, "P_stc_kW_sistema": 221.76,
         "tilt_fachada": 10, "azimuth_fachada": 180, "granja_fv": GEO, "area_fachada_m2": 3000.0,
         "ciudad": "Apartadó (Urabá)", "granja_luz_suelo": LUZ,
         "granja_altura_maquinaria_m": 2.5, "granja_ancho_maquinaria_m": 2.2}
    e.update(kw)
    return e


# ── Ficha del inversor ───────────────────────────────────────────────────────
def test_ficha_lv_con_1500_v_se_marca():
    ids = {a["id"] for a in alertas_ficha_inversor(INV_CATALOGO)}
    assert ids == {"lv_1500"}
    assert alertas_ficha_inversor(INV_FICHA) == []
    assert alertas_ficha_inversor({"nombre": "MAX 100KTL3-X LV", "Vdc_max": 1500.0}) != []
    assert alertas_ficha_inversor({"nombre": "SG250HX", "Vdc_max": 1500.0, "Vmppt_max": 1300.0}) == []
    rojo = {a["id"]: a["nivel"] for a in alertas_ficha_inversor({"nombre": "X", "Vdc_max": 1000.0,
                                                                 "Vmppt_min": 200.0, "Vmppt_max": 1100.0})}
    assert rojo == {"mppt_sobre_vdc": "🔴"}
    assert {a["id"] for a in alertas_ficha_inversor({"nombre": "X", "I_max_tracker": 32.0,
                                                    "Isc_max_tracker": 26.0})} == {"isc_menor"}


def test_margen_de_voc_frente_a_la_ficha_real():
    assert margen_voc(1386.1, INV_FICHA)["nivel"] == "🔴"          # 28 en serie
    m22 = margen_voc(1089.0, INV_FICHA)                             # 22 en serie: 11 V de margen
    assert m22["nivel"] == "🟠" and round(m22["margen_v"]) == 11
    assert margen_voc(990.0, INV_FICHA)["nivel"] == "🟢"
    assert margen_voc(None, INV_FICHA) is None and margen_voc(1000.0, {}) is None


# ── Campo, vista 3D y plano eléctrico ────────────────────────────────────────
def test_campo_y_modulos_por_inversor():
    campo = rg.campo_desde_estado(_estado())
    assert campo["modulos_colocados"] == 308 and campo["filas_usadas"] == 13
    d = diseno_desde_estado(_estado())
    mods = rg.modulos_del_campo(campo, d)
    assert len(mods) == 308
    assert {m["string"] for m in mods} == set(range(1, 15))
    assert sum(m["inversor"] == 1 for m in mods) == 154 and sum(m["inversor"] == 2 for m in mods) == 154
    d28 = diseno_desde_estado(_estado(N_serie=28, reparto_strings_inversores=[6, 5]))
    m28 = rg.modulos_del_campo(campo, d28)
    assert sum(m["inversor"] == 1 for m in m28) == 168 and sum(m["inversor"] == 2 for m in m28) == 140
    assert rg.campo_desde_estado(_estado(tipo_instalacion="Fachada BIPV")) is None


def test_svg_vista_3d_y_plano_electrico():
    campo, d = rg.campo_desde_estado(_estado()), diseno_desde_estado(_estado())
    v3d = rg.svg_campo_3d(campo, d)
    assert v3d.startswith("<svg") and "Vista 3D del campo" in v3d
    assert v3d.count("<polygon") >= 309                               # terreno + 308 módulos
    assert rg.color_inversor(1) in v3d and rg.color_inversor(2) in v3d and "INV-2" in v3d
    plano = rg.svg_plano_electrico(campo, d)
    for t in ("Plano eléctrico", "14 strings de 22", "7 + 7", "INV-1", "INV-2", "★", "Fila 1<", "Fila 13<"):
        assert t in plano, t
    assert plano.count("<rect") >= 308
    assert rg.svg_plano_electrico(campo, None) == "" and rg.svg_campo_3d(None) == ""


def test_texto_strings_que_cruzan_filas():
    campo = rg.campo_desde_estado(_estado())
    d28 = diseno_desde_estado(_estado(N_serie=28, reparto_strings_inversores=[6, 5]))
    txt = rg.texto_strings_cruzan(d28, campo)
    assert "28 módulos" in txt and "cada fila 24" in txt and "continúan en la fila siguiente" in txt


def test_agrivoltaica_graficas_maquinaria_y_coherencia():
    luz = rg.svg_luz_suelo(LUZ)
    assert "<polyline" in luz and "bajo la mesa" in luz
    mapa = rg.svg_mapa_luz_mensual(LUZ)
    assert "Ene" in mapa and "Dic" in mapa and mapa.count("<rect") >= 12 * 21
    assert rg.svg_luz_suelo(None) == "" and rg.svg_mapa_luz_mensual({}) == ""
    campo = rg.campo_desde_estado(_estado())
    assert {c["id"] for c in rg.maquinaria(_estado(), campo)} >= {"maquinaria_bajo", "maquinaria_entre"}
    coh = rg.coherencia(_estado(), campo)
    assert coh and coh[0]["nivel"] == "🟢"
    html = rg.html_revisiones(coh)
    assert "<li" in html and "🟢" in html
    assert "**" not in rg.html_revisiones(rg.maquinaria(_estado(), campo))


# ── Textos y datos del reporte ───────────────────────────────────────────────
def test_textos_segun_tipo_de_instalacion():
    g, f = etiquetas_tipo("Granja fotovoltaica"), etiquetas_tipo("Fachada BIPV")
    assert g["area"][0] == "Área del terreno" and "red" in g["destino"] and g["panel"] == "Módulo fotovoltaico"
    assert f["area"][0] == "Área de fachada" and "edificio" in f["destino"] and f["panel"] == "Módulo BIPV"
    assert "fachada" not in g["poa"][0] and "90° = fachada" not in g["inclinacion"]
    assert "mayor que la irradiación horizontal" in nota_poa(1838, 1683, False)
    assert "fachada vertical" in nota_poa(900, 1600, True)
    assert nota_pr(82.3) is None and "PR > 100" in nota_pr(103.0)


def test_mismatch_real_altitud_y_suciedad():
    filas = {f[0]: f for f in filas_mismatch({"factor_mismatch_aplicado": 1.0}, RES)}
    assert filas["Calidad del módulo (aplicada)"][1] == "3.0"
    assert filas["Mismatch módulos y strings (aplicado)"][1] == "2.0"
    assert "Otras pérdidas de 🔀 Mismatch" not in filas
    viejo = {f[0]: f for f in filas_mismatch({"factor_mismatch_aplicado": 0.97}, {})}
    assert viejo["Otras pérdidas de 🔀 Mismatch"][1] == "3.0"
    assert altitud_proyecto({"alt_proyecto": 25}) == 25.0
    assert altitud_proyecto({"ciudad": "Apartadó (Urabá)"}) is not None
    assert "2–3 %" in aviso_soiling({"f_soil_prom": 1.0}, True)
    assert aviso_soiling({"f_soil_prom": 0.98}, True) is None


# ── Página del reporte ───────────────────────────────────────────────────────
def _generar(**estado):
    import calculos.auth as _auth
    import calculos.trm_utils as _trm
    _auth.requerir_login = lambda solo_admin=False: {"email": "t@t", "rol": "admin", "activo": True, "nombre": "T"}
    at = AppTest.from_file(str(PAGINA), default_timeout=120)
    base = {"recurso_solar_ok": True, "produccion_ok": True, "res_produccion": RES, "poa_anual_kWh_m2": 1838.0,
            "ghi_anual_kWh_m2": 1683.0, "nombre_proyecto": "Granja Apartadó", "factor_mismatch_aplicado": 1.0,
            "motor_optico_ok": True, "poa_efectiva_anual_kWh_m2": 1669.0,
            "motor_optico_summary": {"b0": 0.05, "k_bipv": 1.0, "noct": 45, "coef_temp": -0.0029,
                                     "factor_global": 0.9079, "perdida_iam_kWh_m2": 62.0, "perdida_soil_kWh_m2": 0.0,
                                     "perdida_term_kWh_m2": 107.3, "f_iam_prom": 0.9662, "f_soil_prom": 1.0,
                                     "f_term_prom": 0.9396},
            "T_min_diseno": 20.9, "T_cel_realista": 54.2, "T_cel_extremo": 63.6,
            _trm._KEY_VALOR: 3900.0, _trm._KEY_FUENTE: "manual"}
    for k, v in {**base, **estado}.items():
        at.session_state[k] = v
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    next(b for b in at.button if "Generar Reporte" in b.label).click().run()
    assert not at.exception, [e.value for e in at.exception]
    return at.session_state["_reporte_html"]


def test_reporte_de_granja_completo_y_coherente():
    html = _generar(**_estado())
    for t in ("Vista 3D del campo", "Plano eléctrico", "Luz anual en el suelo", "Mapa de sombra en el suelo",
              "maquinaria", "Coherencia del campo", "Área del terreno", "Energía AC neta entregada a la red",
              "Módulo fotovoltaico", "Calidad del módulo (aplicada)", "Mismatch módulos y strings (aplicado)",
              "La pérdida por suciedad quedó en 0 %", "Margen frente a la tensión DC máxima",
              "POA bruta (plano de los paneles)"):
        assert t in html, t
    for t in ("Factor Mismatch aplicado", "CdTe", "Bogotá es favorecida", "Para un proyecto de 100 m²",
              "90° = fachada vertical", "entregada al edificio", "Área de fachada", "PVsyst"):
        assert t not in html, t
    assert ">—</td>" not in html.split("Altitud", 1)[1][:400]


def test_reporte_de_fachada_conserva_sus_textos():
    html = _generar(**_estado(tipo_instalacion="Fachada BIPV", granja_fv=None))
    assert "Área de fachada" in html and "Módulo BIPV" in html
    assert "Vista 3D del campo" not in html


def test_dimensionamiento_muestra_las_alertas_de_la_ficha():
    src = next((RAIZ / "pages").glob("4_*Dimensionamiento.py")).read_text(encoding="utf-8")
    assert "alertas_ficha_inversor(" in src


def test_manual_del_asistente_lo_explica():
    kb = (RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    seccion = kb[kb.index("## 103."):]
    for texto in ("Vista 3D del campo", "Plano eléctrico", "1.100 V", "22", "Mismatch", "Altitud",
                  "suciedad", "LV"):
        assert texto in seccion, texto
    assert "PVsyst" not in seccion
