"""Cadena de pérdidas del sistema multi-superficie (Spec 05/cadena-perdidas-multisuperficie).

Antes (27-sep-2026) la energía de 🗺️ Vista 3D era POA × área × η × 0,78 fijo y
🔆 Motor Óptico / 🔀 Mismatch no llegaban a Financiero; el físico usaba la POA
bruta y k_bipv = 1.
"""
from pathlib import Path

import numpy as np
import pytest

from calculos.cadena_perdidas_multisup import (
    CLAVE_PUBLICACION,
    K_BIPV_POR_TIPO,
    MONTAJE_AUTOMATICO,
    aviso_cadena_vencida,
    cadena_superficie,
    cadena_superficies_estado,
    k_bipv_superficie,
    parametros_cadena,
    registro_publicacion,
)
from calculos.multi_superficie import calcular_poa_superficie, e_ac_total_multisup, poa_anual_superficie
from calculos.produccion import simular_produccion_anual
from datos.ciudades_colombia import CIUDADES
from datos.tecnologias_bipv import MODULOS_BIPV
from tests.test_simulation_pipeline import _tmy_sintetico_offline

VISTA_3D = Path(__file__).resolve().parents[1] / "pages" / "9_🗺️_Vista_3D.py"
ASP = "ASP-ST1-T40"
SPR = "SPR-E20-327 (E20-327NE-WHT-D)"


@pytest.fixture(scope="module")
def sitio():
    c = CIUDADES["Bogotá"]
    return c, _tmy_sintetico_offline(c["lat"], c["lon"], c["alt_m"])


def _poa(sitio, tilt, az=180):
    c, tmy = sitio
    return calcular_poa_superficie(tmy, c["lat"], c["lon"], c["alt_m"], {"tilt_deg": tilt, "azimuth_deg": az})


def _cadena(sitio, panel, tilt, k, parametros=None, n=20):
    return cadena_superficie(_poa(sitio, tilt), sitio[1], dict(MODULOS_BIPV[panel]), nombre_panel=panel,
                             tilt_deg=tilt, k_bipv=k, eta_inversor=0.97,
                             parametros=parametros or parametros_cadena({}), n_modulos=n)


@pytest.mark.parametrize("panel, tilt, k", [(ASP, 90, 1.3), (SPR, 10, 1.0)])
def test_criterio_2_coincide_con_produccion(sitio, panel, tilt, k):
    # Misma geometría, panel, óptica y pérdidas: la energía de la cadena es la
    # de 📊 Producción (su mismo motor SDM), no un PR genérico.
    r = _cadena(sitio, panel, tilt, k)
    poa = _poa(sitio, tilt)
    poa_st = poa.copy()
    poa_st["poa_global"] = r["poa_sin_termico"].to_numpy()
    tmy = sitio[1].set_axis(poa.index)
    prod = simular_produccion_anual(
        tmy, poa_st, dict(MODULOS_BIPV[panel]), 20, 0.97, 1.0, k_bipv=k,
        poa_bruta_kWh_m2=poa_anual_superficie(poa), pct_mismatch_fab=1.0,
        pct_cableado_dc=1.5, pct_cableado_ac=0.0)
    assert r["pr"] == pytest.approx(prod["PR"], abs=0.002)
    assert r["modelo"] == "SDM"


def test_fachada_cdte_no_se_sobreestima_con_una_formula_lineal(sitio):
    # Con γ lineal la fachada vertical de CdTe salía ~11 % por encima de Producción.
    r = _cadena(sitio, ASP, 90, 1.3)
    assert r["pr"] < 0.72


def test_criterio_4_vertical_y_techo(sitio):
    fachada = _cadena(sitio, SPR, 90, 1.3)
    techo = _cadena(sitio, SPR, 10, 1.0)
    assert fachada["f_iam"] < techo["f_iam"]            # más pérdida por ángulo en vertical
    assert fachada["vertical"] and not techo["vertical"]
    assert fachada["f_soiling"] > techo["f_soiling"]    # se ensucia menos (auto-limpieza)
    assert k_bipv_superficie({"tipo": "Fachada"}) == K_BIPV_POR_TIPO["Fachada"] == 1.3
    assert k_bipv_superficie({"tipo": "Techo", "k_bipv_montaje": MONTAJE_AUTOMATICO}) == 1.0
    assert k_bipv_superficie({"tipo": "Techo", "k_bipv_montaje": "Sin ventilación (k=1.5) — sellado total"}) == 1.5


def test_mas_calor_menos_energia(sitio):
    assert _cadena(sitio, SPR, 10, 1.5)["pr"] < _cadena(sitio, SPR, 10, 1.0)["pr"]


def test_criterio_3_motor_optico_cambia_la_energia_y_vence_la_publicacion(sitio):
    base = _cadena(sitio, SPR, 10, 1.0)
    estado_mo = {"motor_optico_ok": True, "mo_panel_ref": SPR, "motor_optico_b0": 0.12,
                 "motor_optico_f_iam_dif": 0.90}
    con_mo = _cadena(sitio, SPR, 10, 1.0, parametros_cadena(estado_mo))
    assert con_mo["f_iam"] < base["f_iam"] and con_mo["pr"] < base["pr"]

    sup = [{"nombre": "Techo 1", "tipo": "Techo", "activa": True}]
    estado = {"multisup_activo": True, "superficies_bipv": sup}
    assert "versión anterior" in aviso_cadena_vencida(estado)          # publicado con 0,78
    estado[CLAVE_PUBLICACION] = registro_publicacion(estado, {}, sup)
    assert aviso_cadena_vencida(estado) is None
    estado.update(estado_mo)                                          # corre Motor Óptico después
    assert "Cambiaron los parámetros" in aviso_cadena_vencida(estado)
    estado[CLAVE_PUBLICACION] = registro_publicacion(estado, {}, sup)
    sup[0]["k_bipv_montaje"] = "Sin ventilación (k=1.5) — sellado total"   # cambia el montaje
    assert "Cambiaron los parámetros" in aviso_cadena_vencida(estado)


def test_mismatch_aplica_sombra_de_horizonte_solo_al_simplificado(sitio):
    estado = {"mismatch_ok": True, "factor_sombra_anual": 0.10, "pct_mismatch_fab": 2.0}
    par = parametros_cadena(estado)
    assert par["f_sombra_horizonte"] == pytest.approx(0.90)
    poa = _poa(sitio, 10)
    kw = dict(nombre_panel=SPR, tilt_deg=10, k_bipv=1.0, eta_inversor=0.97, parametros=par, n_modulos=20)
    simpl = cadena_superficie(poa, sitio[1], dict(MODULOS_BIPV[SPR]), **kw)
    bypass = cadena_superficie(poa, sitio[1], dict(MODULOS_BIPV[SPR]), aplicar_horizonte=False, **kw)
    assert simpl["f_sombra"] == pytest.approx(0.90) and bypass["f_sombra"] == 1.0
    # Producción aplica la sombra de horizonte a la irradiancia antes del SDM:
    # el efecto en energía es cercano, no idéntico, al 10 %.
    assert 0.88 < simpl["pr"] / bypass["pr"] < 0.93


def test_criterio_6_sin_doble_transparencia():
    src = (Path(__file__).resolve().parents[1] / "calculos" / "cadena_perdidas_multisup.py").read_text(encoding="utf-8")
    assert "transparencia=0.0" in src


def test_criterio_1_vista3d_sin_pr_fijo():
    src = VISTA_3D.read_text(encoding="utf-8")
    assert 'get("pr_sistema", 0.78)' not in src
    assert "cadena_superficies_estado(" in src and "tabla_desglose(" in src


def test_energia_total_con_pr_por_superficie():
    import pandas as pd
    idx = pd.date_range("2023-01-01", periods=8760, freq="h")
    poa = {"A": pd.DataFrame({"poa_global": np.full(8760, 100.0)}, index=idx)}
    sups = [{"nombre": "A", "tipo": "Fachada", "area_m2": 10.0, "activa": True}]
    res = e_ac_total_multisup(poa, sups, {"A": 0.1}, {"A": 0.7})
    assert res["e_ac_total_kWh"] == pytest.approx(876.0 * 10 * 0.1 * 0.7, rel=1e-3)
    assert res["desglose"][0]["pr"] == 0.7
    with pytest.raises(ValueError):
        e_ac_total_multisup(poa, sups, {"A": 0.1}, {})


def test_cache_no_recalcula(sitio, monkeypatch):
    import calculos.cadena_perdidas_multisup as cad
    c, tmy = sitio
    llamadas = []
    real = cad.cadena_superficie
    monkeypatch.setattr(cad, "cadena_superficie", lambda *a, **k: llamadas.append(1) or real(*a, **k))
    estado = {"tmy_df": tmy}
    sups = [{"nombre": "T", "tipo": "Techo", "tilt_deg": 10, "modulos": 4, "grupos": []}]
    paneles = {"T": {"panel": dict(MODULOS_BIPV[SPR]), "nombre": SPR}}
    poas = {"T": _poa(sitio, 10)}
    r1, e1 = cadena_superficies_estado(estado, sups, poas, paneles)
    r2, _ = cadena_superficies_estado(estado, sups, poas, paneles)
    assert not e1 and len(llamadas) == 1 and r1["T"]["pr"] == r2["T"]["pr"]


def test_criterio_5_fisico_usa_poa_optica_y_k_bipv_del_tipo():
    from calculos.cadena_perdidas_multisup import cadena_optica_fisico
    from calculos.transicion_multisuperficie import recalcular_fisica_superficie, superficie_nueva
    from tests.test_transicion_multisuperficie import _PANEL, _p_shade, _tmy
    tmy = _tmy()
    base = superficie_nueva("F", "Fachada", tilt_deg=90, azimuth_deg=180, area_m2=40.0, panel=_PANEL,
                            n_serie=10, n_paralelo=4, inversor_id="INV-1", p_shade=_p_shade(0.0), k_bipv=1.3)
    sin = recalcular_fisica_superficie(base, tmy, 4.6, -74.1, 2600.0)
    con_sup = dict(base)
    con_sup["cadena_optica"] = cadena_optica_fisico({"tilt_deg": 90}, _PANEL, parametros_cadena({}))
    con = recalcular_fisica_superficie(con_sup, tmy, 4.6, -74.1, 2600.0)
    f = con["resultados_dc"]["f_optico"]
    assert 0.6 < f < 1.0 and sin["resultados_dc"]["f_optico"] == 1.0
    assert con["resultados_dc"]["E_dc_anual_kWh"] < sin["resultados_dc"]["E_dc_anual_kWh"]
    # la POA anual informada sigue siendo la bruta (misma base que las demás tablas)
    assert con["resultados_dc"]["poa_anual_kWh_m2"] == sin["resultados_dc"]["poa_anual_kWh_m2"]
