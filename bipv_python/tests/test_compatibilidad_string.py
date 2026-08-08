import pytest

from calculos.dimensionamiento import evaluar_compatibilidad_string
from datos.tecnologias_bipv import ASP_ST1_T40


def _eco_sna_12k() -> dict:
    return {
        "Vdc_max": 480,
        "Vmppt_min": 120,
        "Vmppt_max": 440,
        "Isc_max_tracker": 44,
    }


def test_economico_sna_12k_detecta_tension_y_mppt_fuera_de_rango() -> None:
    resultado = evaluar_compatibilidad_string(
        ASP_ST1_T40,
        _eco_sna_12k(),
        N_serie=8,
        T_frio=-5.0,
        T_real=36.35,
        T_extremo=41.94,
        N_strings_tracker=1,
    )

    assert resultado["evaluable"] is True
    assert resultado["compatible"] is False
    assert resultado["Voc_frio"] == pytest.approx(1017.4, abs=1.0)
    assert resultado["Vmp_real"] == pytest.approx(674.0, abs=1.0)
    assert any("Voc en frío" in m for m in resultado["mensajes"])
    assert any("MPPT máximo" in m for m in resultado["mensajes"])


def test_configuracion_de_dos_modulos_es_electronicamente_valida_para_eco() -> None:
    resultado = evaluar_compatibilidad_string(
        ASP_ST1_T40,
        _eco_sna_12k(),
        N_serie=2,
        T_frio=-5.0,
        T_real=36.35,
        T_extremo=41.94,
        N_strings_tracker=1,
    )

    assert resultado["compatible"] is True
    assert resultado["mensajes"] == []