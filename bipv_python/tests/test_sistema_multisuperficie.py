"""Spec 06-analisis-financiero/sistema-multisuperficie (H-D5)."""
import numpy as np
import pandas as pd
import pytest

from calculos.publicacion_multisuperficie import (
    CLAVES_PUBLICACION, publicar_energia_multisuperficie, resultados_multisuperficie_a_guardar,
)
from calculos.sistema_multisuperficie import (
    df_mensual_multisuperficie, estado_sistema_publicado, resumen_sistema_multisuperficie,
    sistema_desde_estado,
)
from datos.tecnologias_bipv import MODULOS_BIPV

_ASP = dict(MODULOS_BIPV["ASP-ST1-T40"])
_SPR = dict(MODULOS_BIPV["SPR-E20-327 (E20-327NE-WHT-D)"])
_IDX = pd.date_range("2026-01-01", periods=8760, freq="h")


def _poa(escala=1.0):
    horas = np.arange(8760)
    g = np.clip(np.sin((horas % 24 - 6) / 12 * np.pi), 0, None) * 800 * escala
    g = g * (1 + 0.3 * np.cos(2 * np.pi * horas / 8760))       # forma estacional
    return pd.DataFrame({"poa_global": g}, index=_IDX)


def _g(gid, mppt, ns, np_):
    return {"gid": gid, "topologia": "string", "inversor_id": "INV-1", "mppt": mppt,
            "n_serie": ns, "n_paralelo": np_}


def _escenario_d5():
    sups = [
        {"uid": 1, "nombre": "Fachada principal", "area_m2": 97.3, "activa": True,
         "grupos": [_g("G1", 1, 6, 3)]},
        {"uid": 2, "nombre": "Techo 1", "area_m2": 97.3, "activa": True,
         "grupos": [_g("G1", 2, 8, 1), _g("G2", 2, 8, 1)]},
    ]
    paneles = {"Fachada principal": {"panel": _ASP, "nombre": "ASP-ST1-T40"},
               "Techo 1": {"panel": _SPR, "nombre": "SPR-E20-327"}}
    desglose = [
        {"nombre": "Fachada principal", "tipo": "Fachada", "area_m2": 12.96, "e_ac_kWh": 714.0, "poa_kWh_m2": 808.0},
        {"nombre": "Techo 1", "tipo": "Techo", "area_m2": 26.091, "e_ac_kWh": 6838.0, "poa_kWh_m2": 1675.0},
    ]
    poas = {"Fachada principal": _poa(0.5), "Techo 1": _poa(1.0)}
    return sups, paneles, desglose, poas


def test_criterio_1_potencia_y_modulos_del_diseno_de_vista_3d():
    s = resumen_sistema_multisuperficie(*_escenario_d5())
    assert s["n_modulos"] == 34
    assert s["P_dc_stc_kW"] == pytest.approx((18 * 63.0 + 16 * 327.1) / 1000, abs=1e-3)   # 6,37 kWp
    assert {p["panel"]: p["modulos"] for p in s["por_panel"]} == {"ASP-ST1-T40": 18, "SPR-E20-327": 16}
    assert s["completo"] and s["superficies_sin_grupos"] == []


def test_reparto_mensual_suma_la_energia_y_sigue_la_poa():
    s = resumen_sistema_multisuperficie(*_escenario_d5())
    assert len(s["mensual_kWh"]) == 12
    assert sum(s["mensual_kWh"]) == pytest.approx(714.0 + 6838.0, abs=0.5)
    # Forma estacional: enero (cos máximo) produce más que julio.
    assert s["mensual_kWh"][0] > s["mensual_kWh"][6]


def test_superficie_sin_grupos_deja_el_sistema_incompleto():
    sups, paneles, desglose, poas = _escenario_d5()
    sups[1]["grupos"] = []
    s = resumen_sistema_multisuperficie(sups, paneles, desglose, poas)
    assert not s["completo"] and s["superficies_sin_grupos"] == ["Techo 1"]
    assert s["n_modulos"] == 18


def test_falta_poa_de_una_superficie_es_error():
    sups, paneles, desglose, poas = _escenario_d5()
    poas.pop("Techo 1")
    with pytest.raises(ValueError, match="Falta la POA de 'Techo 1'"):
        resumen_sistema_multisuperficie(sups, paneles, desglose, poas)


def test_panel_sin_potencia_es_error():
    sups, paneles, desglose, poas = _escenario_d5()
    paneles["Techo 1"] = {"panel": {**_SPR, "Pmax_stc": None}, "nombre": "SPR"}
    with pytest.raises(ValueError, match="no trae su potencia"):
        resumen_sistema_multisuperficie(sups, paneles, desglose, poas)


def test_costo_por_referencia_de_panel():
    sups, paneles, desglose, poas = _escenario_d5()
    paneles["Techo 1"]["panel"] = {**_SPR, "costo_usd": 180.0}
    s = resumen_sistema_multisuperficie(sups, paneles, desglose, poas)
    costos = {p["panel"]: p["costo_usd"] for p in s["por_panel"]}
    assert costos["SPR-E20-327"] == 180.0


# ── Publicación ──────────────────────────────────────────────────────────────
def _publicar(ss, sistema, total=7552.0):
    _, _, desglose, poas = _escenario_d5()
    return publicar_energia_multisuperficie(
        ss, origen="simplificado", e_ac_total=total, desglose=desglose,
        poa_ponderada=_poa(0.8), area_total=12.96 + 26.091, sistema=sistema,
    )


def test_publicacion_guarda_el_sistema_y_se_retira_con_la_energia():
    ss = {}
    sistema = resumen_sistema_multisuperficie(*_escenario_d5())
    assert _publicar(ss, sistema)["publicado"]
    assert ss["multisup_sistema"]["n_modulos"] == 34
    assert "multisup_sistema" in CLAVES_PUBLICACION
    assert resultados_multisuperficie_a_guardar(ss)["multisup_sistema"]["n_modulos"] == 34
    _publicar(ss, None)
    assert "multisup_sistema" not in ss        # nunca queda un sistema de otra publicación


def test_publicacion_rechaza_reparto_que_no_suma():
    sistema = resumen_sistema_multisuperficie(*_escenario_d5())
    sistema["mensual_kWh"] = [1.0] * 12
    with pytest.raises(ValueError, match="reparto mensual"):
        _publicar({}, sistema)


# ── Estado para los consumidores ─────────────────────────────────────────────
def test_estado_sin_modo_multisuperficie():
    assert estado_sistema_publicado({}) == {"activo": False, "sistema": None, "problemas": []}


def test_criterio_4_publicacion_anterior_pide_volver_a_publicar():
    e = estado_sistema_publicado({"multisup_activo": True})
    assert e["activo"] and e["sistema"] is None and "Vuelve a publicarla" in e["problemas"][0]


def test_criterio_3_sistema_incompleto_nombra_la_superficie():
    sups, paneles, desglose, poas = _escenario_d5()
    sups[1]["grupos"] = []
    ss = {"multisup_activo": True,
          "multisup_sistema": resumen_sistema_multisuperficie(sups, paneles, desglose, poas)}
    e = estado_sistema_publicado(ss)
    assert "«Techo 1»" in e["problemas"][0] and "grupos de strings" in e["problemas"][0]


def test_df_mensual_para_baterias():
    from calculos.baterias_balance import balance_mensual

    sistema = resumen_sistema_multisuperficie(*_escenario_d5())
    df = df_mensual_multisuperficie(sistema)
    bal = balance_mensual(df, [478.0] * 12)
    assert bal["E_solar_kWh"].sum() == pytest.approx(7552.0, abs=0.5)


def test_sistema_desde_el_estado_de_la_sesion():
    sups, _, desglose, poas = _escenario_d5()
    ss = {"superficies_bipv": sups, "panel_dict": _ASP, "panel_nombre_dim": "ASP-ST1-T40"}
    sups[1]["panel_origen"] = "catalogo"
    sups[1]["panel_nombre"] = "SPR-E20-327 (E20-327NE-WHT-D)"
    sups[1]["panel_ficha"] = _SPR
    s = sistema_desde_estado(ss, desglose, poas)
    assert s["n_modulos"] == 34


# ── Páginas (fuente) ─────────────────────────────────────────────────────────
from pathlib import Path

_PAGINAS = Path(__file__).resolve().parents[1] / "pages"


def _src(nombre):
    return (_PAGINAS / nombre).read_text(encoding="utf-8")


def test_financiero_usa_el_sistema_publicado_sin_exigir_produccion():
    src = _src("7_💰_Financiero.py")
    assert "estado_sistema_publicado(st.session_state)" in src
    assert "if (prod_ok or _ms_activo) and e_ac > 0:" in src
    assert 'p_stc = float(_sistema_ms["P_dc_stc_kW"])' in src
    assert 'n_pan = int(_sistema_ms["n_modulos"])' in src
    # 🔴 y se detiene si el sistema está incompleto o la publicación es anterior.
    assert "st.stop()" in src[src.index("_est_ms[\"problemas\"]"):src.index("_ms_activo:\n    p_stc")]
    # Costo por referencia de panel y Presupuesto desvinculado por defecto.
    assert 'key=f"fin_costo_panel_ms_{_i_pp}"' in src and "value=not _ms_activo" in src


def test_baterias_usa_el_reparto_mensual_publicado():
    src = _src("11_🔋_Baterias_y_Balance.py")
    assert 'df_m_prod = df_mensual_multisuperficie(_est_ms_bat["sistema"])' in src
    assert "balance horario no está disponible" in src


def test_co2_y_presupuesto_no_mezclan_sistemas():
    co2 = _src("12_🌿_Impacto_CO2.py")
    assert 'p_stc = float(_est_ms_co2["sistema"]["P_dc_stc_kW"])' in co2
    assert "multisup_sistema" in _src("8_💼_Presupuesto.py")


def test_vista_3d_publica_el_sistema_en_simplificado_y_bypass():
    src = _src("9_🗺️_Vista_3D.py")
    assert src.count("sistema=sistema_desde_estado(") == 2


# ── Aviso fijo de energía retirada (hasta volver a publicar) ────────────────
from calculos.publicacion_multisuperficie import aviso_energia_retirada


def _estado_con_diseno():
    sups, _, desglose, poas = _escenario_d5()
    ss = {"superficies_bipv": sups, "panel_dict": _ASP, "panel_nombre_dim": "ASP-ST1-T40",
          "multisup_inversores": [{"inversor_id": "INV-1", "eta_inversor": 0.97, "P_ac_nom_W": 5000.0}]}
    sups[1].update(panel_origen="catalogo", panel_nombre="SPR-E20-327 (E20-327NE-WHT-D)", panel_ficha=_SPR)
    return ss, desglose, poas


def _publicar_estado(ss, desglose, poas):
    publicar_energia_multisuperficie(
        ss, origen="simplificado", e_ac_total=7552.0, desglose=desglose,
        poa_ponderada=_poa(0.8), area_total=12.96 + 26.091,
        sistema=sistema_desde_estado(ss, desglose, poas))


def test_cambio_electrico_deja_aviso_fijo_con_la_superficie_hasta_publicar():
    from calculos.diseno_electrico_multisup import invalidar_por_cambio_electrico

    ss, desglose, poas = _estado_con_diseno()
    invalidar_por_cambio_electrico(ss)                 # registra la huella
    _publicar_estado(ss, desglose, poas)
    assert aviso_energia_retirada(ss) is None
    ss["superficies_bipv"][0]["grupos"][0]["n_paralelo"] = 2
    assert invalidar_por_cambio_electrico(ss)
    aviso = aviso_energia_retirada(ss)
    assert "cambió el diseño eléctrico" in aviso and "«Fachada principal»" in aviso
    assert "Vuelve a publicarla" in aviso
    # Sigue visible en los reruns siguientes (no es un mensaje de un instante)…
    invalidar_por_cambio_electrico(ss)
    assert aviso_energia_retirada(ss) == aviso
    # …y desaparece al volver a publicar.
    _publicar_estado(ss, desglose, poas)
    assert aviso_energia_retirada(ss) is None


def test_cambio_de_panel_deja_aviso_fijo():
    from calculos.panel_superficie import invalidar_por_cambio_panel

    ss, desglose, poas = _estado_con_diseno()
    invalidar_por_cambio_panel(ss)
    _publicar_estado(ss, desglose, poas)
    ss["superficies_bipv"][1]["panel_nombre"] = "otro"
    invalidar_por_cambio_panel(ss)
    aviso = aviso_energia_retirada(ss)
    assert "cambió el panel" in aviso and "«Techo 1»" in aviso


def test_sin_energia_publicada_no_hay_aviso_de_retiro():
    from calculos.diseno_electrico_multisup import invalidar_por_cambio_electrico

    ss, _, _ = _estado_con_diseno()
    invalidar_por_cambio_electrico(ss)
    ss["superficies_bipv"][0]["grupos"][0]["n_paralelo"] = 2
    invalidar_por_cambio_electrico(ss)
    assert aviso_energia_retirada(ss) is None


def test_desactivar_a_mano_no_deja_aviso_de_retiro():
    from calculos.publicacion_multisuperficie import retirar_energia_multisuperficie

    ss, desglose, poas = _estado_con_diseno()
    _publicar_estado(ss, desglose, poas)
    ss["_multisup_retiro_motivo"] = {"texto": "x"}
    retirar_energia_multisuperficie(ss)
    assert aviso_energia_retirada(ss) is None


def test_vista_3d_muestra_el_aviso_fijo_en_integrar():
    src = _src("9_🗺️_Vista_3D.py")
    i = src.index("# ── Integrar al análisis financiero")
    seccion = src[i:i + 3000]
    assert "_aviso_retiro = aviso_energia_retirada(st.session_state)" in seccion
    assert "_ci2.info(_aviso_retiro)" in seccion
