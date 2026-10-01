# -*- coding: utf-8 -*-
"""Spec ``07-informes/reporte-multisuperficie`` (1-oct-2026).

Con energía multi-superficie publicada en 🗺️ Vista 3D, el 📄 Reporte PDF
mostraba en «Producción Anual» la energía de 📊 Producción (superficie única)
y en otra sección la multi-superficie: dos cifras distintas para el cliente.
Tampoco mostraba orientación, panel, módulos, kWp, PR y kWh/kWp por
superficie, los inversores, la cadena de pérdidas ni los strings que cruzan.
Caso: fachadas Este y Oeste con un string que cruza la esquina.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

import calculos.reporte_multisuperficie as rms
from calculos.cadena_perdidas_multisup import registro_publicacion, tabla_desglose

PAGINA = next((Path(__file__).resolve().parents[1] / "pages").glob("10_*Reporte_PDF.py"))
PANEL = {"nombre": "SPR-E20-327", "Pmax_stc": 327.0, "Voc_stc": 64.9, "Isc_stc": 6.46,
         "Vmp_stc": 54.7, "Imp_stc": 5.98, "area_m2": 1.63}
RES_CADENA = {
    "Fachada Este": {"f_iam": 0.96, "f_soiling": 0.98, "f_termico": 0.93, "k_bipv": 1.3, "modelo": "SDM",
                     "f_mismatch": 0.99, "f_cables": 0.985, "eta_inversor": 0.97, "f_sombra": 1.0,
                     "f_cruce": 0.938, "pr": 0.71},
    "Fachada Oeste": {"f_iam": 0.96, "f_soiling": 0.98, "f_termico": 0.93, "k_bipv": 1.3, "modelo": "SDM",
                      "f_mismatch": 0.99, "f_cables": 0.985, "eta_inversor": 0.97, "f_sombra": 1.0,
                      "f_cruce": 0.938, "pr": 0.70},
}
MENSUAL = [1300.0, 1250.0, 1350.0, 1280.0, 1300.0, 1250.0, 1350.0, 1350.0, 1250.0, 1150.0, 1050.0, 1040.0]


def _estado(**kw):
    sups = [
        {"uid": "e1", "nombre": "Fachada Este", "tipo": "Fachada", "activa": True, "tilt_deg": 90.0,
         "azimuth_deg": 90.0, "grupos": [{"gid": "G1", "inversor_id": "INV-1", "mppt": 1, "n_serie": 10,
                                          "n_paralelo": 2, "cruce": {"uid": "o1", "modulos": 5}}]},
        {"uid": "o1", "nombre": "Fachada Oeste", "tipo": "Fachada", "activa": True, "tilt_deg": 90.0,
         "azimuth_deg": 270.0, "grupos": [{"gid": "G1", "inversor_id": "INV-1", "mppt": 2, "n_serie": 10,
                                           "n_paralelo": 2}]},
    ]
    e = {"multisup_activo": True, "E_ac_anual_kWh_multisup": 14_920.0, "area_total_multisup": 65.2,
         "multisup_origen": "simplificado",
         "multisup_desglose": [
             {"nombre": "Fachada Este", "tipo": "Fachada", "area_m2": 32.6, "e_ac_kWh": 7_560.0, "poa_kWh_m2": 1_010.0},
             {"nombre": "Fachada Oeste", "tipo": "Fachada", "area_m2": 32.6, "e_ac_kWh": 7_360.0, "poa_kWh_m2": 990.0}],
         "multisup_sistema": {"P_dc_stc_kW": 13.08, "n_modulos": 40,
                              "por_panel": [{"panel": "SPR-E20-327", "modulos": 40, "P_dc_stc_kW": 13.08}],
                              "mensual_kWh": MENSUAL, "completo": True},
         "multisup_estado_electrico": {"estado": "verde", "texto": "🟢 diseño eléctrico verificado."},
         "multisup_cadena_perdidas": registro_publicacion({}, RES_CADENA, sups),
         "superficies_bipv": sups,
         "multisup_inversores": [{"inversor_id": "INV-1", "nombre": "Fronius Primo 15.0",
                                  "ficha": {"P_ac_nom_W": 15_000.0}}],
         "panel_dict": PANEL, "panel_nombre_dim": PANEL["nombre"]}
    e.update(kw)
    return e


# ── Publicación de la cadena ─────────────────────────────────────────────────
def test_la_publicacion_guarda_la_tabla_de_perdidas():
    reg = registro_publicacion({}, RES_CADENA, [])
    assert reg["desglose"] == tabla_desglose(RES_CADENA)
    assert reg["pr"] == {"Fachada Este": 0.71, "Fachada Oeste": 0.70}


# ── Funciones del reporte ────────────────────────────────────────────────────
def _dic(filas):
    return {f[0]: f for f in filas}


def test_activo_solo_con_energia_publicada():
    assert rms.activo(_estado())
    assert not rms.activo(_estado(multisup_activo=False))
    assert not rms.activo(_estado(E_ac_anual_kWh_multisup=0.0))


def test_resumen_del_proyecto():
    d = _dic(rms.resumen(_estado()))
    assert d["Energía AC anual del proyecto"][1] == "14,920"
    assert d["Potencia pico DC"][1] == "13.08" and "40 módulos" in d["Potencia pico DC"][3]
    assert d["Rendimiento específico"][1] == "1,141"
    assert d["Método de cálculo"][1].startswith("simplificado")
    assert d["Diseño eléctrico"][1].startswith("🟢")


def test_tabla_por_superficie_con_cruce():
    t = {f["nombre"]: f for f in rms.tabla_superficies(_estado())}
    este, oeste = t["Fachada Este"], t["Fachada Oeste"]
    # 5 módulos × 2 strings de la Este están físicamente en la Oeste
    assert este["modulos"] == 10 and oeste["modulos"] == 30
    assert este["kwp"] == 10 * 327 / 1000 and oeste["azimut"] == 270.0
    assert este["pr"] == 0.71 and este["panel"] == "SPR-E20-327"
    assert abs(este["yield_kwh_kwp"] - 7_560.0 / 3.27) < 1e-6


def test_inversores():
    inv = rms.tabla_inversores(_estado())[0]
    assert inv["inversor"] == "INV-1" and inv["p_ac_kw"] == 15.0
    assert inv["strings"] == 4 and inv["modulos"] == 40
    assert abs(inv["kwp"] - 13.08) < 1e-9 and abs(inv["dc_ac"] - 13.08 / 15.0) < 1e-9
    assert inv["superficies"] == "Fachada Este, Fachada Oeste"


def test_cadena_cruces_mensual_y_por_panel():
    assert len(rms.cadena_por_superficie(_estado())) == 2
    assert "String que cruza" in rms.cadena_por_superficie(_estado())[0]
    assert rms.cadena_por_superficie(_estado(multisup_cadena_perdidas={"pr": {}})) == []
    c = rms.cruces(_estado())[0]
    assert (c["origen"], c["destino"], c["k"]) == ("Fachada Este", "Fachada Oeste", 5)
    assert rms.mensual(_estado()) == MENSUAL
    assert rms.filas_por_panel(_estado())[0][1] == "40 módulos"


# ── Página del reporte ───────────────────────────────────────────────────────
def _generar(**estado):
    import calculos.auth as _auth
    import calculos.trm_utils as _trm
    _auth.requerir_login = lambda solo_admin=False: {"email": "t@t", "rol": "admin", "activo": True, "nombre": "T"}
    at = AppTest.from_file(str(PAGINA), default_timeout=120)
    base = {"ciudad": "Bogotá", "recurso_solar_ok": True, "produccion_ok": True, "nombre_proyecto": "Edificio",
            "res_produccion": {"P_stc_kW": 5.0, "E_dc_anual_kWh": 6_100.0, "E_ac_anual_kWh": 5_900.0, "PR": 0.8,
                               "Y_f": 1180.0, "Y_r": 1475.0, "CF_pct": 13.5, "perdida_inv_kWh": 200.0,
                               "perdida_temp_kWh": 300.0},
            "poa_anual_kWh_m2": 1475.0, "N_serie": 10, "tipo_instalacion": "Fachada BIPV",
            _trm._KEY_VALOR: 3900.0, _trm._KEY_FUENTE: "manual"}
    for k, v in {**base, **estado}.items():
        at.session_state[k] = v
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    next(b for b in at.button if "Generar Reporte" in b.label).click().run()
    assert not at.exception, [e.value for e in at.exception]
    return at.session_state["_reporte_html"]


def test_reporte_multisuperficie_sin_doble_energia():
    html = _generar(**_estado())
    assert "Producción Anual del Proyecto — Multi-Superficie" in html
    assert "14,920" in html
    assert "Producción Anual — Simulación IEC 61724" not in html      # la de superficie única no aparece
    assert "5,900" not in html
    for t in ("Incl. / azimut", "270°", "SPR-E20-327", "kWh/kWp", "INV-1", "Fronius Primo 15.0",
              "Pérdidas de cada superficie", "String que cruza", "Strings que cruzan", "Fachada Este → Fachada Oeste",
              "Módulos por modelo de panel", "🟢 diseño eléctrico verificado"):
        assert t in html, t
    assert "PVsyst" not in html


def test_sin_multisuperficie_el_reporte_sigue_igual():
    html = _generar()
    assert "Producción Anual — Simulación IEC 61724" in html and "5,900" in html
    assert "Multi-Superficie" not in html


def test_manual_del_asistente_lo_explica():
    kb = (Path(__file__).resolve().parents[1] / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    seccion = kb[kb.index("## 102."):]
    for texto in ("dos cifras", "Vista 3D", "kWh/kWp", "PR", "inversor", "cruzan", "Integrar"):
        assert texto in seccion, texto
    assert "PVsyst" not in seccion
