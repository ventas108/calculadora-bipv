"""Campos de los editores de Vista 3D: lo escrito nunca se revierte."""
from calculos.campos_editor import sincronizar_campo


def _ejecucion(estado, datos, escrito=None):
    """Una ejecución de la página: el usuario escribió ``escrito`` (o nada),
    el campo se sincroniza con los datos y la página guarda su valor."""
    if escrito is not None:
        estado["campo"] = escrito
    valor = sincronizar_campo(estado, "campo", datos["valor"])
    datos["valor"] = valor
    return valor


def test_cambios_seguidos_del_mismo_campo_no_se_revierten():
    # Hallado 25-sep-2026: el segundo cambio seguido se revertía (azimuth y N serie).
    estado, datos = {}, {"valor": 180.0}
    assert _ejecucion(estado, datos) == 180.0
    for escrito in (170.0, 160.0, 150.0, 150.0, 140.0):
        assert _ejecucion(estado, datos, escrito) == escrito
        assert datos["valor"] == escrito
    assert _ejecucion(estado, datos) == 140.0   # rerun sin cambios


def test_texto_de_n_serie_cambiado_dos_veces():
    estado, datos = {}, {"valor": "8"}
    _ejecucion(estado, datos)
    assert _ejecucion(estado, datos, "12") == "12"
    assert _ejecucion(estado, datos, "8") == "8"


def test_dato_cambiado_fuera_del_campo_se_muestra():
    # Cargar un proyecto cambia el dato sin tocar el campo.
    estado, datos = {}, {"valor": 90.0}
    _ejecucion(estado, datos)
    _ejecucion(estado, datos, 85.0)
    datos["valor"] = 30.0
    assert _ejecucion(estado, datos) == 30.0
    assert _ejecucion(estado, datos, 35.0) == 35.0
