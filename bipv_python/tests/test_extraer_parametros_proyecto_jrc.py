# -*- coding: utf-8 -*-
"""`extraer_parametros_proyecto()` -- generalización del script JRC/Huld
para leer cualquier proyecto guardado (31-ago-2026, pedido explícito del
usuario). Casos anclados al proyecto real Teusaquillo (mismos valores que
`FICHA_PVSYST_TEUSAQUILLO.md`) para no perder la cobertura del caso ya
verificado al generalizar."""
import pytest

from calculos.modelo_jrc_cdte import extraer_parametros_proyecto


def _estado_teusaquillo() -> dict:
    # Mismos valores reales que datos/tecnologias_bipv.py::ASP_ST1_T40 y el
    # proyecto Teusaquillo (128 módulos, fachada vertical sur, Bogotá).
    return {
        "nombre_proyecto": "Teusaquillo",
        "ciudad": "Bogotá",
        "panel_dict": {"tecnologia": "CdTe", "Pmax_stc": 63.0},
        "panel_nombre_dim": "ASP-ST1-T40",
        "N_paneles_dim": 128,
        "tilt_fachada": 90.0,
        "azimuth_fachada": 180.0,
        "albedo_suelo": 0.20,
    }


def test_extrae_parametros_reales_de_teusaquillo():
    params = extraer_parametros_proyecto(_estado_teusaquillo())
    assert params["tecnologia"] == "CdTe"
    assert params["ciudad"] == "Bogotá"
    assert params["lat"] == pytest.approx(4.711)
    assert params["lon"] == pytest.approx(-74.072)
    assert params["alt_m"] == pytest.approx(2600)
    assert params["tilt"] == pytest.approx(90.0)
    assert params["azimuth"] == pytest.approx(180.0)
    assert params["n_paneles"] == 128
    assert params["p_stc_total_w"] == pytest.approx(63.0 * 128)  # 8064 W = 8,064 kWp real


def test_prefiere_n_paneles_granja_sobre_n_paneles_dim():
    # Proyecto multi-inversor ("Proyecto completo") -- mismo criterio de
    # prioridad ya usado en otras páginas (ej. Ficha RETIE, Diagrama Unifilar).
    estado = _estado_teusaquillo()
    estado["N_paneles_granja"] = 256
    estado["N_paneles_dim"] = 128
    params = extraer_parametros_proyecto(estado)
    assert params["n_paneles"] == 256


def test_rechaza_panel_no_cdte_con_mensaje_claro():
    estado = _estado_teusaquillo()
    estado["panel_dict"] = {"tecnologia": "c-Si", "Pmax_stc": 450.0}
    with pytest.raises(ValueError, match="c-Si"):
        extraer_parametros_proyecto(estado)


def test_rechaza_sin_panel_configurado():
    estado = _estado_teusaquillo()
    estado["panel_dict"] = {}
    with pytest.raises(ValueError):
        extraer_parametros_proyecto(estado)


def test_rechaza_ciudad_desconocida():
    estado = _estado_teusaquillo()
    estado["ciudad"] = "Ciudad Inventada Que No Existe"
    with pytest.raises(ValueError, match="Ciudad Inventada"):
        extraer_parametros_proyecto(estado)


def test_rechaza_sin_dimensionamiento_corrido():
    # Ni N_paneles_granja, ni N_paneles_dim, ni N_paneles -- Dimensionamiento
    # nunca se ejecutó en este proyecto guardado.
    estado = _estado_teusaquillo()
    for k in ("N_paneles_dim", "N_paneles_granja", "N_paneles"):
        estado.pop(k, None)
    with pytest.raises(ValueError, match="Dimensionamiento"):
        extraer_parametros_proyecto(estado)


def test_usa_defaults_razonables_si_faltan_tilt_azimuth_albedo():
    # Proyecto guardado antes de correr 2_Recurso_Solar, o con datos parciales
    # -- no debe reventar, cae a los defaults ya establecidos de la app.
    estado = _estado_teusaquillo()
    for k in ("tilt_fachada", "tilt_default", "azimuth_fachada", "albedo_suelo"):
        estado.pop(k, None)
    params = extraer_parametros_proyecto(estado)
    assert params["tilt"] == pytest.approx(90.0)
    assert params["azimuth"] == pytest.approx(180.0)
    assert params["albedo"] == pytest.approx(0.20)
