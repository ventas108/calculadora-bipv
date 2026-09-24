"""Spec 05-perdidas-y-temperatura/vigencia-poa-superficie.

La POA por superficie de Vista 3D quedaba guardada por NOMBRE y sin firma:
tras cambiar tilt, azimuth, área, montaje, el TMY o las coordenadas, la
página seguía mostrándola e integrándola como si fuera vigente, y un fallo
de pvlib se convertía en un DataFrame vacío sin causa.
"""
import ast
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from calculos.multi_superficie import (
    MOTIVO_POA_ERROR,
    MOTIVO_POA_GEOMETRIA,
    MOTIVO_POA_SIN_CALCULAR,
    MOTIVO_POA_TMY,
    TEXTO_MOTIVO_POA,
    calcular_poa_superficies_firmadas,
    config_bifacial_superficie,
    firma_poa_superficie,
    parametros_poa_estado,
    poas_vigentes,
    poas_vigentes_estado,
)
from calculos.vinculador_sombra_multisuperficie import preservar_o_invalidar_campos_fisicos
from tests.test_simulation_pipeline import ALT_M, LAT, LON, _tmy_sintetico_offline

_PAGINA = Path(__file__).resolve().parents[1] / "pages" / "9_🗺️_Vista_3D.py"
_BIF = {"bifacialidad": 0.7, "altura_m": 1.0, "albedo_trasero": 0.2, "factor_vista_trasera": 0.5}


@pytest.fixture(scope="module")
def tmy():
    return _tmy_sintetico_offline(LAT, LON, ALT_M)


def _sup(uid=1, nombre="Sur", **cambios):
    base = {
        "uid": uid, "nombre": nombre, "tipo": "Fachada", "tilt_deg": 90.0,
        "azimuth_deg": 180.0, "area_m2": 20.0, "activa": True,
        "montaje_fachada": "Heredar de ☀️ Recurso Solar",
    }
    base.update(cambios)
    return base


def _firma(sup, tmy, lat=LAT, lon=LON, alt=ALT_M, albedo=0.2, bif=None, usar=False):
    return firma_poa_superficie(sup, tmy, lat, lon, alt, albedo, bif, usar)["firma"]


# ── Firma ────────────────────────────────────────────────────────────────────
def test_firma_estable_ante_renombrado(tmy):
    assert _firma(_sup(), tmy) == _firma(_sup(nombre="Fachada principal"), tmy)


@pytest.mark.parametrize("cambio", [
    {"tilt_deg": 80.0}, {"azimuth_deg": 90.0}, {"area_m2": 25.0},
    {"tipo": "Techo"}, {"montaje_fachada": "Adosada al muro (sellada)"},
])
def test_firma_cambia_con_cada_entrada_geometrica(tmy, cambio):
    assert _firma(_sup(), tmy) != _firma(_sup(**cambio), tmy)


def test_firma_cambia_con_albedo_bifacial_coordenadas_y_tmy(tmy):
    base = _firma(_sup(), tmy)
    assert base != _firma(_sup(), tmy, albedo=0.3)
    assert base != _firma(_sup(), tmy, bif=_BIF, usar=True)
    assert base != _firma(_sup(), tmy, lat=LAT + 0.01)
    assert base != _firma(_sup(), tmy, alt=ALT_M + 50)
    otro = tmy.copy()
    otro["G_h"] = otro["G_h"] * 1.05
    assert base != _firma(_sup(), otro)


def test_bifacial_sin_activar_no_entra_en_la_firma(tmy):
    assert _firma(_sup(), tmy) == _firma(_sup(), tmy, bif=_BIF, usar=False)


def test_config_bifacial_por_montaje():
    assert config_bifacial_superficie(_sup(), _BIF, False) is None
    assert config_bifacial_superficie(_sup(tilt_deg=30.0), _BIF, True)["factor_vista_trasera"] == 1.0
    adosada = config_bifacial_superficie(_sup(montaje_fachada="Adosada al muro (sellada)"), _BIF, True)
    assert adosada["factor_vista_trasera"] == 0.0 and adosada["albedo_trasero"] == 0.05
    ventilada = config_bifacial_superficie(
        _sup(montaje_fachada="Ventilada con superficie reflejante"), _BIF, True)
    assert ventilada["factor_vista_trasera"] == 1.0
    assert config_bifacial_superficie(_sup(), _BIF, True)["factor_vista_trasera"] == 0.5
    assert _BIF["factor_vista_trasera"] == 0.5  # no muta la configuración global


# ── Cálculo firmado ──────────────────────────────────────────────────────────
def test_calculo_indexa_por_uid_y_firma(tmy):
    resultados, errores = calcular_poa_superficies_firmadas(
        [_sup(), _sup(uid=2, nombre="Este", azimuth_deg=90.0),
         _sup(uid=3, nombre="Apagada", activa=False)],
        tmy, LAT, LON, ALT_M,
    )
    assert errores == {}
    assert set(resultados) == {1, 2}
    assert resultados[1]["nombre"] == "Sur"
    assert len(resultados[1]["poa"]) == 8760
    assert resultados[1]["firma"] == _firma(_sup(), tmy)


def test_un_fallo_se_reporta_y_no_se_convierte_en_poa_vacia(tmy):
    resultados, errores = calcular_poa_superficies_firmadas(
        [_sup(), _sup(uid=2, nombre="Rota", tilt_deg="no-numérico")],
        tmy, LAT, LON, ALT_M,
    )
    assert set(resultados) == {1}
    assert 2 in errores and errores[2]


# ── Vigencia ─────────────────────────────────────────────────────────────────
def _estado(tmy, sups):
    resultados, errores = calcular_poa_superficies_firmadas(sups, tmy, LAT, LON, ALT_M)
    return resultados, errores


def _vigentes(sups, res, err, tmy, lat=LAT, lon=LON, alt=ALT_M, albedo=0.2, bif=None, usar=False):
    return poas_vigentes(sups, res, err, tmy, lat, lon, alt, albedo, bif, usar)


def test_poa_vigente_tras_calcular_y_tras_renombrar(tmy):
    sups = [_sup(), _sup(uid=2, nombre="Este", azimuth_deg=90.0)]
    res, err = _estado(tmy, sups)
    vig, mot = _vigentes(sups, res, err, tmy)
    assert set(vig) == {"Sur", "Este"} and mot == {}
    renombradas = [_sup(nombre="Sur nuevo"), sups[1]]
    vig, mot = _vigentes(renombradas, res, err, tmy)
    assert set(vig) == {"Sur nuevo", "Este"} and mot == {}


def test_cambio_de_geometria_invalida_solo_esa_superficie(tmy):
    sups = [_sup(), _sup(uid=2, nombre="Este", azimuth_deg=90.0)]
    res, err = _estado(tmy, sups)
    vig, mot = _vigentes([_sup(tilt_deg=70.0), sups[1]], res, err, tmy)
    assert mot == {"Sur": MOTIVO_POA_GEOMETRIA}
    assert set(vig) == {"Este"}


def test_cambio_de_albedo_o_bifacial_invalida_por_geometria(tmy):
    sups = [_sup()]
    res, err = _estado(tmy, sups)
    assert _vigentes(sups, res, err, tmy, albedo=0.35)[1] == {"Sur": MOTIVO_POA_GEOMETRIA}
    assert _vigentes(sups, res, err, tmy, bif=_BIF, usar=True)[1] == {"Sur": MOTIVO_POA_GEOMETRIA}


def test_cambio_de_tmy_o_coordenadas_invalida_todas(tmy):
    sups = [_sup(), _sup(uid=2, nombre="Este", azimuth_deg=90.0)]
    res, err = _estado(tmy, sups)
    esperado = {"Sur": MOTIVO_POA_TMY, "Este": MOTIVO_POA_TMY}
    assert _vigentes(sups, res, err, tmy, lon=LON + 0.5) == ({}, esperado)
    otro = tmy.copy()
    otro["T2m"] = otro["T2m"] + 1.0
    assert _vigentes(sups, res, err, otro) == ({}, esperado)
    assert _vigentes(sups, res, err, None) == ({}, esperado)


def test_sin_calcular_error_e_inactivas(tmy):
    sups = [_sup(), _sup(uid=2, nombre="Nueva"), _sup(uid=3, nombre="Off", activa=False)]
    res, _ = _estado(tmy, [sups[0]])
    vig, mot = _vigentes(sups, res, {1: "ValueError: pvlib"}, tmy)
    assert vig == {}
    assert mot == {"Sur": MOTIVO_POA_ERROR, "Nueva": MOTIVO_POA_SIN_CALCULAR}
    assert set(TEXTO_MOTIVO_POA) >= {MOTIVO_POA_ERROR, MOTIVO_POA_SIN_CALCULAR,
                                     MOTIVO_POA_GEOMETRIA, MOTIVO_POA_TMY}


def test_sesion_antigua_indexada_por_nombre_no_es_vigente(tmy):
    legado = {"Sur": pd.DataFrame({"poa_global": np.ones(8760)}, index=tmy.index)}
    vig, mot = _vigentes([_sup()], legado, None, tmy)
    assert vig == {} and mot == {"Sur": MOTIVO_POA_SIN_CALCULAR}


def test_poas_vigentes_estado_lee_los_mismos_parametros_que_el_calculo(tmy):
    sups = [_sup()]
    estado = {"superficies_bipv": sups, "tmy_df": tmy, "albedo_suelo": 0.25,
              "bifacial_cfg": _BIF, "bifacial_activo": True}
    albedo, cfg, usar = parametros_poa_estado(estado)
    assert (albedo, usar) == (0.25, True) and cfg == _BIF
    res, err = calcular_poa_superficies_firmadas(
        sups, tmy, LAT, LON, ALT_M, albedo=albedo, bifacial_cfg=cfg, usar_bifacial=usar)
    estado.update({"poa_superficies": res, "poa_superficies_errores": err})
    vig, mot = poas_vigentes_estado(estado, LAT, LON, ALT_M)
    assert set(vig) == {"Sur"} and mot == {}
    estado["ms_bifacial_on"] = False  # el usuario apaga el bifacial en Vista 3D
    assert poas_vigentes_estado(estado, LAT, LON, ALT_M)[1] == {"Sur": MOTIVO_POA_GEOMETRIA}


# ── firma_poa en la superficie ───────────────────────────────────────────────
def _editada(**cambios):
    datos = {k: v for k, v in _sup().items()}
    datos.update(cambios)
    return datos


def test_preservar_conserva_firma_poa_si_no_cambia_la_geometria():
    anterior = {**_sup(), "firma_poa": "abc"}
    assert preservar_o_invalidar_campos_fisicos(anterior, _editada(nombre="Otro"))["firma_poa"] == "abc"
    assert preservar_o_invalidar_campos_fisicos(anterior, _editada(activa=False))["firma_poa"] == "abc"


@pytest.mark.parametrize("cambio", [
    {"tilt_deg": 80.0}, {"azimuth_deg": 90.0}, {"area_m2": 21.0},
    {"tipo": "Techo"}, {"montaje_fachada": "Adosada al muro (sellada)"},
])
def test_preservar_retira_firma_poa_si_cambia_la_geometria(cambio):
    anterior = {**_sup(), "firma_poa": "abc"}
    assert "firma_poa" not in preservar_o_invalidar_campos_fisicos(anterior, _editada(**cambio))


# ── Página: ningún consumidor lee la POA sin pasar por la vigencia ───────────
def _arbol():
    return ast.parse(_PAGINA.read_text(encoding="utf-8"))


def test_pagina_no_lee_poa_superficies_directamente():
    lecturas = []
    for nodo in ast.walk(_arbol()):
        if isinstance(nodo, ast.Call) and ast.unparse(nodo.func).endswith("session_state.get"):
            if nodo.args and isinstance(nodo.args[0], ast.Constant) and nodo.args[0].value == "poa_superficies":
                lecturas.append(nodo.lineno)
        if (isinstance(nodo, ast.Subscript) and isinstance(nodo.ctx, ast.Load)
                and ast.unparse(nodo.value).endswith("session_state")
                and isinstance(nodo.slice, ast.Constant) and nodo.slice.value == "poa_superficies"):
            lecturas.append(nodo.lineno)
    assert not lecturas, f"Lecturas directas de poa_superficies en líneas {lecturas}"


def test_pagina_calcula_con_firma_y_consulta_vigencia():
    src = _PAGINA.read_text(encoding="utf-8")
    assert "calcular_poa_superficies_firmadas(" in src
    assert "calcular_poa_todas(" not in src
    assert src.count("poas_vigentes_estado(") >= 4  # resumen/integrar, vista, producción, mapa
    assert 'st.session_state["poa_superficies_errores"]' in src
    assert '"firma_poa"' in src
