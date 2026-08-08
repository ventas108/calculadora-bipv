import pytest

from calculos.escenarios_fase4 import (
    SCENARIO_SCHEMA_VERSION,
    construir_definicion_escenarios,
    validar_definicion_escenarios,
)


def test_bogota_define_tres_escenarios_y_reconciliacion():
    definicion = construir_definicion_escenarios(
        nombre_proyecto="Proyecto BIPV Bogotá Teusaquillo",
        fuente_horizonte=True,
        fuente_sketchup=True,
        tipo_optimizacion="paneles",
        panel_nombre="ASP-ST1-T40",
        inversor_nombre="ECO HIBRID SNA US 6K",
    )

    validar_definicion_escenarios(definicion)
    assert definicion["schema_version"] == SCENARIO_SCHEMA_VERSION
    assert definicion["escenarios"]["referencia"]["estado"] == "definido"
    assert (
        definicion["escenarios"]["actual"]["estado"]
        == "definido_reconciliacion_pendiente"
    )
    assert definicion["escenarios"]["optimizada"]["estado"] == "pendiente_parametros"
    assert definicion["politica_fuentes_actual"]["no_sumar_dos_veces"] is True


def test_no_permite_situacion_actual_sin_fuente():
    with pytest.raises(ValueError, match="al menos una fuente"):
        construir_definicion_escenarios(
            nombre_proyecto="Bogotá",
            fuente_horizonte=False,
            fuente_sketchup=False,
        )


def test_rechaza_doble_fuente_sin_politica_de_reconciliacion():
    definicion = construir_definicion_escenarios(
        nombre_proyecto="Bogotá",
        fuente_horizonte=True,
        fuente_sketchup=True,
    )
    definicion["politica_fuentes_actual"]["no_sumar_dos_veces"] = False
    with pytest.raises(ValueError, match="doble conteo"):
        validar_definicion_escenarios(definicion)