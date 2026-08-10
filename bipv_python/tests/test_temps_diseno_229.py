# -*- coding: utf-8 -*-
"""#229: el trío de temperaturas de diseño en cero no se guarda ni restaura."""
from calculos.temperatura import temps_diseno_en_cero as _temps_diseno_en_cero


def test_trio_en_cero_detectado():
    assert _temps_diseno_en_cero(
        {"T_min_diseno": 0.0, "T_cel_realista": 0, "T_cel_extremo": 0.0}
    )


def test_valores_reales_no_detecta():
    assert not _temps_diseno_en_cero(
        {"T_min_diseno": 5.0, "T_cel_realista": 36.35, "T_cel_extremo": 41.94}
    )


def test_un_cero_legitimo_no_detecta():
    # T_min 0°C es físicamente posible (páramo); solo el trío completo es inválido
    assert not _temps_diseno_en_cero(
        {"T_min_diseno": 0.0, "T_cel_realista": 38.0, "T_cel_extremo": 45.0}
    )


def test_sin_temperaturas_no_detecta():
    assert not _temps_diseno_en_cero({"otra_clave": 1})


def test_parcial_en_cero_no_detecta():
    # Subconjunto en cero (faltan claves) NO se sanea: solo el trío completo
    # en cero es inequívocamente corrupto — no borrar datos parciales válidos
    assert not _temps_diseno_en_cero({"T_min_diseno": 0.0, "T_cel_extremo": 0.0})
    assert not _temps_diseno_en_cero({"T_min_diseno": 0.0})


def test_no_numerico_no_revienta():
    assert not _temps_diseno_en_cero(
        {"T_min_diseno": "abc", "T_cel_realista": 0.0, "T_cel_extremo": 0.0}
    )
