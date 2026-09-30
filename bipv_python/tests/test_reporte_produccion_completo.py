# -*- coding: utf-8 -*-
"""Spec ``07-informes/reporte-produccion-completo`` (30-sep-2026).

El 📄 Reporte PDF no traía el sistema eléctrico (la casilla «Dimensionamiento»
no generaba nada), el diagrama de pérdidas de Producción, los datos
bifaciales nuevos ni 🌾 Granja FV. Caso Urabá (Apartadó): 308 ×
JAM66D46-720/LB, 2 × 100 kW, 11 strings de 28 (6 + 5).
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from calculos.reporte_produccion import (
    filas_bifacial,
    filas_perdidas,
    filas_sistema_electrico,
    secciones_granja,
)

PAGINA = next((Path(__file__).resolve().parents[1] / "pages").glob("10_*Reporte_PDF.py"))
JAM = {"nombre": "JAM66D46-720/LB", "dimensiones_mm": "2384x1303x33 mm", "area_m2": 3.1064,
       "Pmax_stc": 720.0, "Imp_stc": 17.48, "Vmp_stc": 41.19, "Isc_stc": 18.59, "Voc_stc": 49.0}
GEO = {"ancho_terreno_m": 80.0, "largo_terreno_m": 30.0, "modulos_pendiente": 2, "orientacion": "horizontal",
       "modulos_por_mesa": 31, "mesas_por_fila": 1, "pasillo_m": 3.0, "pitch_m": 6.60, "altura_libre_m": 2.4}
RES = {"P_stc_kW": 221.76, "E_dc_anual_kWh": 349_109.0, "E_ac_anual_kWh": 340_381.0, "PR": 0.80,
       "Y_f": 1535.0, "Y_r": 1920.0, "CF_pct": 17.5, "perdida_inv_kWh": 8_728.0, "perdida_temp_kWh": 22_000.0,
       "perdida_clipping_kWh": 1_250.0, "horas_con_clipping": 140, "E_ac_sin_recorte_kWh": 341_631.0}


def _estado(**kw):
    e = {"tipo_instalacion": "Granja fotovoltaica", "panel_dict": JAM, "panel_nombre_final": JAM["nombre"],
         "N_paneles_final": 308, "N_serie": 28, "reparto_strings_inversores": [6, 5],
         "inversor_dict_dim": {"P_ac_nom_W": 100_000.0, "nombre": "Growatt MAX 100KTL3 LV"},
         "inversor_nombre_dim": "Growatt MAX 100KTL3 LV", "produccion_n_inversores": 2,
         "produccion_p_ac_total_w": 200_000.0, "P_stc_kW_sistema": 221.76,
         "tilt_fachada": 10, "azimuth_fachada": 180, "granja_fv": GEO,
         "granja_fv_resultado": {"modulos_colocados": 308, "modulos_proyecto": 308, "filas_usadas": 5,
                                 "gcr": 0.3979, "ancho_mesa_m": 2.626, "angulo_limite_deg": 6.5,
                                 "corredor_m": 4.01, "altura_centro_m": 2.628, "suelo_libre_pct": 60.1},
         "poa_geometria_filas": {"gcr": 0.3979, "altura_m": 2.628, "ancho_colector_m": 2.626},
         "granja_sombra_estimada": {"perdida_frontal_pct": 0.19},
         "granja_luz_suelo": {"media_pct": 60.2, "media_kwh_m2": 1158.0, "referencia_kwh_m2": 1922.6,
                              "bajo_mesa_pct": 44.6, "entre_filas_pct": 70.6, "homogeneidad": 0.44},
         "granja_seguidor": {"fijo": {"poa_kwh_m2": 2420.0}, "backtracking": {"poa_kwh_m2": 3017.0},
                             "sin_backtracking": {"poa_kwh_m2": 2930.0}, "ganancia_backtracking_pct": 24.7,
                             "ganancia_sin_backtracking_pct": 21.1, "perdida_sombra_electrica_pct": 2.7},
         "bifacial_activo": True,
         "bifacial_cfg": {"bifacialidad": 0.8, "altura_m": 2.628, "albedo_trasero": 0.2, "gcr": 0.3979,
                          "ancho_colector_m": 2.626, "sombra_trasera_pct": 5.0, "mismatch_trasero_pct": 10.0}}
    e.update(kw)
    return e


def _dic(filas):
    return {f[0]: f for f in filas}


# ── Sistema eléctrico ────────────────────────────────────────────────────────
def test_sistema_electrico_de_uraba():
    d = _dic(filas_sistema_electrico(_estado(), RES))
    assert d["Número de módulos"][1] == "308"
    assert d["Potencia pico DC"][1] == "221.76"
    assert d["Módulos en serie por string"][1] == "28" and "11 strings" in d["Módulos en serie por string"][3]
    assert d["Inversores"][1].startswith("2 × Growatt")
    assert d["Potencia AC total"][1] == "200.0"
    assert d["Reparto de strings por inversor"][1] == "6 + 5"
    assert d["Relación DC/AC"][1] == "1.11"
    assert d["Recorte del inversor (clipping)"][1] == "1,250"


# ── Pérdidas ─────────────────────────────────────────────────────────────────
def test_perdidas_son_la_tabla_de_produccion():
    filas = filas_perdidas(RES, 1861.0, {})
    etapas = [f["etapa"] for f in filas]
    assert etapas[0].startswith("① E ref") and etapas[-1].startswith("⑤ E_ac")
    assert any("Recorte inversor" in e for e in etapas)
    assert filas[-1]["kwh"] == 340_381.0
    assert filas[0]["pct"] == 0.0
    assert filas_perdidas(None, 1861.0, {}) == [] and filas_perdidas(RES, 0.0, {}) == []


# ── Bifacial ─────────────────────────────────────────────────────────────────
def test_bifacial_completo():
    d = _dic(filas_bifacial(_estado()))
    assert d["GCR (cobertura del suelo)"][1] == "39.8"
    assert d["Ancho de la mesa en la pendiente"][1] == "2.63"
    assert d["Sombra de la estructura en la cara trasera"][1] == "5.0"
    assert d["Mismatch por luz trasera no uniforme"][1] == "10.0"
    assert filas_bifacial(_estado(bifacial_activo=False)) == []


# ── Granja FV ────────────────────────────────────────────────────────────────
def test_granja_completa():
    g = secciones_granja(_estado())
    assert set(g) == {"campo", "energia", "agrivoltaica", "seguidor", "electrico", "bloques"}
    campo = _dic(g["campo"])
    assert campo["GCR"][1] == "39.8" and campo["Ángulo límite de sombra"][1] == "6.5"
    assert _dic(g["energia"])["Geometría del campo en la energía"][1] == "Sí"
    assert _dic(g["agrivoltaica"])["Categoría agrivoltaica"][1].startswith("I ")
    assert "+24.7 %" in _dic(g["seguidor"])["Seguidor de un eje con backtracking"][3]
    assert _dic(g["electrico"])["Strings"][1] == "11 × 28 módulos"
    assert [b["strings"] for b in g["bloques"]] == [6, 5]


def test_granja_vacia_si_no_es_granja():
    assert secciones_granja(_estado(tipo_instalacion="Fachada BIPV")) == {}
    assert secciones_granja(_estado(granja_fv=None)) == {}


# ── Página del reporte ───────────────────────────────────────────────────────
def test_el_reporte_incluye_las_secciones_nuevas():
    import calculos.auth as _auth
    import calculos.trm_utils as _trm
    _auth.requerir_login = lambda solo_admin=False: {"email": "t@t", "rol": "admin", "activo": True, "nombre": "T"}
    at = AppTest.from_file(str(PAGINA), default_timeout=120)
    for k, v in {**_estado(), "ciudad": "Apartadó (Urabá)", "recurso_solar_ok": True, "produccion_ok": True,
                 "res_produccion": RES, "poa_anual_kWh_m2": 1861.0, "nombre_proyecto": "Urabá",
                 _trm._KEY_VALOR: 3900.0, _trm._KEY_FUENTE: "manual"}.items():
        at.session_state[k] = v
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    etiquetas = [c.label for c in at.checkbox]
    assert any("diagrama de pérdidas" in e for e in etiquetas)
    assert any("Granja FV" in e for e in etiquetas)
    next(b for b in at.button if "Generar Reporte" in b.label).click().run()
    assert not at.exception, [e.value for e in at.exception]
    html = at.session_state["_reporte_html"]
    for t in ("Sistema Eléctrico e Inversores", "Relación DC/AC", "6 + 5",
              "Diagrama de Pérdidas", "Recorte inversor",
              "Granja FV — Campo", "Ángulo límite de sombra", "Luz media en el suelo", "INV-1",
              "Sombra de la estructura en la cara trasera"):
        assert t in html, t
    assert "PVsyst" not in html


def test_produccion_guarda_los_inversores_de_la_simulacion():
    src = next((Path(__file__).resolve().parents[1] / "pages").glob("6_*Produccion.py")).read_text(encoding="utf-8")
    assert 'st.session_state["produccion_n_inversores"]' in src
    assert 'st.session_state["produccion_p_ac_total_w"]' in src


def test_manual_del_asistente_lo_explica():
    kb = (Path(__file__).resolve().parents[1] / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    seccion = kb[kb.index("## 101."):]
    for texto in ("Sistema Eléctrico e Inversores", "Diagrama de pérdidas", "Granja FV", "desmarca",
                  "Guardar como PDF", "6 + 5"):
        assert texto in seccion, texto
    assert "PVsyst" not in seccion
