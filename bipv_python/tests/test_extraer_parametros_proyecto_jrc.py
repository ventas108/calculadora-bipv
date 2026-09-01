# -*- coding: utf-8 -*-
"""`extraer_parametros_proyecto()` -- generalización del script JRC/Huld
para leer cualquier proyecto guardado (31-ago-2026, pedido explícito del
usuario). Casos anclados al proyecto real Teusaquillo (mismos valores que
`FICHA_PVSYST_TEUSAQUILLO.md`) para no perder la cobertura del caso ya
verificado al generalizar."""
import pytest

from calculos.modelo_jrc_huld import extraer_parametros_proyecto


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


def test_acepta_panel_cis_con_los_mismos_criterios_que_cdte():
    # Generalizado el mismo día a CIS (pedido explícito del usuario) --
    # coeficientes verificados contra Kumar, Sudhakar, Samykano (2019),
    # Tabla 4. Ya no debe rechazarse.
    estado = _estado_teusaquillo()
    estado["panel_dict"] = {"tecnologia": "CIS", "Pmax_stc": 100.0}
    params = extraer_parametros_proyecto(estado)
    assert params["tecnologia"] == "CIS"


def test_acepta_panel_crystalline_agregado_el_mismo_dia():
    # Pedido explícito del usuario: "integra en el calculo interno
    # technologies namely crystalline (c-Si) y asi cumplimos con el ciclo".
    estado = _estado_teusaquillo()
    estado["panel_dict"] = {"tecnologia": "c-Si", "Pmax_stc": 450.0}
    params = extraer_parametros_proyecto(estado)
    assert params["tecnologia"] == "Crystalline"


@pytest.mark.parametrize("texto_real_catalogo,esperado", [
    ("CdTe pelicula delgada", "CdTe"),
    ("CIGS", "CIS"),
    ("MonoSi", "Crystalline"),
    ("N-Type TopCon Bifacial Agri", "Crystalline"),
])
def test_acepta_texto_libre_real_del_catalogo_no_solo_etiquetas_limpias(texto_real_catalogo, esperado):
    # datos/catalogo_paneles_excel.py trae texto libre de fabricante, no las
    # etiquetas limpias "CdTe"/"CIS"/"Crystalline" -- verificado con 4 valores
    # reales distintos encontrados en el catálogo al auditar esta generalización.
    estado = _estado_teusaquillo()
    estado["panel_dict"] = {"tecnologia": texto_real_catalogo, "Pmax_stc": 300.0}
    params = extraer_parametros_proyecto(estado)
    assert params["tecnologia"] == esperado
    assert params["tecnologia_cruda"] == texto_real_catalogo


def test_rechaza_panel_tecnologia_sin_coeficientes_verificados():
    # Ninguna palabra clave reconocida (ni CdTe, ni CIGS/CIS, ni las
    # variantes de silicio cristalino) -- debe rechazarse con mensaje claro,
    # nunca dar un número inventado.
    estado = _estado_teusaquillo()
    estado["panel_dict"] = {"tecnologia": "Perovskita experimental", "Pmax_stc": 450.0}
    with pytest.raises(ValueError, match="Perovskita"):
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
