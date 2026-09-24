"""Spec 08-interfaz/estado-sombra-superficie.

El motor clasificaba la sombra de cada superficie, pero Vista 3D no mostraba
ningún estado: el usuario solo lo descubría en el modo físico como
«falta 'p_shade'», sin motivo.
"""
import copy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from calculos.adaptador_multisuperficie import construir_proyecto_desde_session_state
from calculos.produccion_vigencia import huella_horaria
from calculos.sombras_3d import VERSION_ALGORITMO_FS_POR_SUPERFICIE
from calculos.vinculador_sombra_multisuperficie import (
    ESTADOS_DIAGNOSTICO_SOMBRA,
    aplicar_sombra_a_superficies,
    diagnostico_sombra_superficies,
    invalidar_sombra_por_cambio_tmy,
    invalidar_sombra_por_version_algoritmo,
    preservar_o_invalidar_campos_fisicos,
)

_PAGINA = Path(__file__).resolve().parents[1] / "pages" / "9_🗺️_Vista_3D.py"
_IDX = pd.date_range("2025-01-01", periods=8760, freq="h", tz="UTC")
_TMY = pd.DataFrame({"T2m": np.linspace(10, 30, 8760)}, index=_IDX)
_TMY_FP = huella_horaria(_IDX, _TMY["T2m"].to_numpy(dtype=float))


def _firma(**cambios):
    firma = {"tmy_fingerprint": _TMY_FP, "fuente": "sombras_3d", "proveedor": "sombras_3d",
             "version_algoritmo": VERSION_ALGORITMO_FS_POR_SUPERFICIE,
             "puntos_analisis": [{"x": 1}, {"x": 2}]}
    firma.update(cambios)
    return firma


def _sup(nombre="Sur", uid=1, **cambios):
    base = {
        "uid": uid, "nombre": nombre, "tipo": "Fachada", "tilt_deg": 90.0,
        "azimuth_deg": 180.0, "area_m2": 20.0, "activa": True,
        "n_serie": 8, "n_paralelo": 1, "inversor_id": "INV-1",
        "p_shade": np.full(8760, 0.1), "firma_sombra": _firma(),
        "estado_sombra": "calculado_completo",
        "cobertura_sombra": {"horas_con_sol_calculadas": 4300, "estado": "calculado_completo"},
        "calidad_confianza_sombra": "alta", "advertencias_sombra": [],
    }
    base.update(cambios)
    return base


def _sin_sombra(sup, **extra):
    for campo in ("p_shade", "firma_sombra", "cobertura_sombra", "estado_sombra",
                  "calidad_confianza_sombra", "advertencias_sombra"):
        sup.pop(campo, None)
    sup.update(extra)
    return sup


def _casos():
    return {
        "calculado_completo": _sup(),
        "sombra_cero_calculada": _sup(
            p_shade=np.zeros(8760), estado_sombra="sombra_cero_calculada"),
        "calculo_incompleto": _sin_sombra(_sup(), estado_sombra="calculo_incompleto",
                                          advertencias_sombra=["120 horas con sol no fueron calculadas."]),
        "error_geometrico": _sin_sombra(_sup(), estado_sombra="error_geometrico", advertencias_sombra=[
            "error_geometrico: El punto «Sur-P1» está DENTRO del modelo — daría sombra total falsa."]),
        "sin_calcular": _sin_sombra(_sup()),
        "invalidada_tmy": _sup(firma_sombra=_firma(tmy_fingerprint="otro-tmy")),
        "invalidada_version": _sup(firma_sombra=_firma(
            version_algoritmo="sombras_3d.ray_casting_por_superficie.v1")),
        "invalidada_geometria": _sin_sombra(_sup(), sombra_invalidada_motivo="tilt"),
    }


def _diag(sups, tmy=_TMY):
    return {d["nombre"]: d for d in diagnostico_sombra_superficies(sups, tmy)}


@pytest.mark.parametrize("estado", list(_casos()))
def test_diagnostico_de_cada_estado(estado):
    d = _diag([_casos()[estado]])["Sur"]
    assert d["estado"] == estado
    assert d["utilizable"] is (estado in ("calculado_completo", "sombra_cero_calculada"))
    assert d["motivo"] and d["accion"]
    assert "p_shade" not in d["motivo"] + d["accion"]
    assert set(d) >= {"nombre", "estado", "utilizable", "motivo",
                      "horas_con_sol_calculadas", "calidad", "n_puntos", "accion"}


def test_los_ocho_estados_estan_definidos():
    assert set(_casos()) == set(ESTADOS_DIAGNOSTICO_SOMBRA)


def test_detalles_del_diagnostico():
    diag = _diag([_casos()["calculado_completo"]])["Sur"]
    assert diag["horas_con_sol_calculadas"] == 4300 and diag["n_puntos"] == 2
    assert diag["calidad"] == "alta"
    geom = _diag([_casos()["error_geometrico"]])["Sur"]
    assert "Sur-P1" in geom["motivo"] and "DENTRO" in geom["motivo"]
    assert "tilt" in _diag([_casos()["invalidada_geometria"]])["Sur"]["motivo"]


def test_sin_tmy_las_sombras_calculadas_quedan_invalidadas():
    d = _diag([_sup()], tmy=None)["Sur"]
    assert d["estado"] == "invalidada_tmy" and not d["utilizable"]
    assert "Recurso Solar" in d["accion"]


def test_estado_del_motor_no_listado_se_muestra_tal_cual():
    sup = _sin_sombra(_sup(), estado_sombra="resolucion_insuficiente",
                      advertencias_sombra=["Hay menos puntos de analisis que modulos en serie."])
    d = _diag([sup])["Sur"]
    assert d["estado"] == "resolucion_insuficiente" and not d["utilizable"]


def test_p_shade_invalido_no_es_utilizable():
    d = _diag([_sup(p_shade=np.full(100, 0.1))])["Sur"]
    assert not d["utilizable"]


def test_inactivas_no_aparecen_y_no_muta_la_entrada():
    sups = [_sup(), _sup(nombre="Off", uid=2, activa=False)]
    antes = copy.deepcopy(sups)
    diag = diagnostico_sombra_superficies(sups, _TMY)
    assert [d["nombre"] for d in diag] == ["Sur"]
    for a, b in zip(antes, sups):
        assert a.keys() == b.keys()
        np.testing.assert_array_equal(a["p_shade"], b["p_shade"])
        assert a["firma_sombra"] == b["firma_sombra"]


# ── Coherencia con lo que acepta el modo físico ──────────────────────────────
def _modo_fisico_acepta(sup) -> bool:
    frescas = invalidar_sombra_por_version_algoritmo(
        invalidar_sombra_por_cambio_tmy([copy.deepcopy(sup)], _TMY))
    estado = {
        "superficies_bipv": frescas,
        "panel_dict": {"modelo": "P"},
        "multisup_inversores": [{"inversor_id": "INV-1", "tipo": "dedicado", "eta_inversor": 0.97}],
    }
    try:
        construir_proyecto_desde_session_state(estado)
    except ValueError:
        return False
    return True


@pytest.mark.parametrize("estado", list(_casos()) + ["p_shade_corto", "p_shade_fuera_de_rango"])
def test_utilizable_coincide_con_el_modo_fisico(estado):
    casos = _casos()
    casos["p_shade_corto"] = _sup(p_shade=np.full(100, 0.1))
    casos["p_shade_fuera_de_rango"] = _sup(p_shade=np.full(8760, 1.5))
    sup = casos[estado]
    assert _diag([sup])["Sur"]["utilizable"] is _modo_fisico_acepta(sup)


# ── Conservación de motivos ──────────────────────────────────────────────────
def test_aplicar_sombra_conserva_advertencias_en_estados_no_aceptables():
    resultado = {"Sur": {
        "estado_sombra": "error_geometrico",
        "advertencias": ["error_geometrico: El punto «Sur-P2» está a 4 cm de la malla"],
        "calidad_confianza": "baja", "p_shade": np.zeros(8760), "firma_sombra": _firma(),
        "cobertura": {"horas_con_sol_calculadas": 1},
    }}
    nueva = aplicar_sombra_a_superficies([_sup()], resultado)[0]
    assert nueva["estado_sombra"] == "error_geometrico"
    assert nueva["advertencias_sombra"] == resultado["Sur"]["advertencias"]
    assert nueva["calidad_confianza_sombra"] == "baja"
    for campo in ("p_shade", "firma_sombra", "cobertura_sombra"):
        assert campo not in nueva


def test_aplicar_sombra_valida_limpia_motivo_de_invalidacion():
    resultado = {"Sur": {"estado_sombra": "calculado_completo", "advertencias": [],
                         "p_shade": np.zeros(8760), "firma_sombra": _firma(), "cobertura": {}}}
    sup = _sin_sombra(_sup(), sombra_invalidada_motivo="tilt")
    assert "sombra_invalidada_motivo" not in aplicar_sombra_a_superficies([sup], resultado)[0]


def _editada(sup, **cambios):
    datos = {k: sup[k] for k in ("uid", "nombre", "tipo", "tilt_deg", "azimuth_deg",
                                 "area_m2", "activa")}
    datos.update(cambios)
    return datos


@pytest.mark.parametrize("campo, valor, texto", [
    ("tilt_deg", 80.0, "tilt"), ("azimuth_deg", 90.0, "azimuth"), ("area_m2", 25.0, "área"),
])
def test_cambio_de_geometria_deja_motivo_con_el_campo(campo, valor, texto):
    anterior = _sup()
    nueva = preservar_o_invalidar_campos_fisicos(anterior, _editada(anterior, **{campo: valor}))
    assert "p_shade" not in nueva
    assert texto in nueva["sombra_invalidada_motivo"]
    d = _diag([nueva])["Sur"]
    assert d["estado"] == "invalidada_geometria" and texto in d["motivo"]
    # El motivo sobrevive a los reruns sin cambios.
    siguiente = preservar_o_invalidar_campos_fisicos(nueva, _editada(nueva))
    assert siguiente["sombra_invalidada_motivo"] == nueva["sombra_invalidada_motivo"]


def test_sin_sombra_previa_no_hay_motivo_de_invalidacion():
    anterior = _sin_sombra(_sup())
    nueva = preservar_o_invalidar_campos_fisicos(anterior, _editada(anterior, tilt_deg=80.0))
    assert "sombra_invalidada_motivo" not in nueva


# ── Página ───────────────────────────────────────────────────────────────────
def test_pagina_muestra_la_tabla_desde_el_diagnostico():
    src = _PAGINA.read_text(encoding="utf-8")
    assert "diagnostico_sombra_superficies(" in src
    assert "revisa el estado antes de adoptar resultados" not in src
    inicio = src.index('key="btn_calcular_sombra_multisup"')
    assert inicio < src.index("diagnostico_sombra_superficies(", inicio)
