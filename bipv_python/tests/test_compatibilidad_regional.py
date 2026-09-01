# -*- coding: utf-8 -*-
"""`evaluar_compatibilidad_regional()` -- combina la matriz real portada
(31-ago-2026) desde la app hermana https://bipv.innovacionquimica.com.co/
con la detección de región por polígonos. Casos anclados a los ejemplos
REALES documentados en `EXPLICACION HOJA EXCEL BIPV EINNOVA COLOMBIA.rtf`
(Bifacial en Andina = rojo, Flexible en Pacífica = verde), para no perder
la fidelidad del juicio experto al portarlo."""
import pytest

from calculos.compatibilidad_regional import (
    clasificar_familia_regional,
    evaluar_compatibilidad_regional,
    evaluar_compatibilidad_regional_desde_ciudad,
)
from datos.compatibilidad_regional_bipv import COMPATIBILIDAD_REGIONAL_BIPV


def test_matriz_portada_tiene_las_21_familias_reales():
    assert len(COMPATIBILIDAD_REGIONAL_BIPV) == 21
    marcas = {info["marca"] for info in COMPATIBILIDAD_REGIONAL_BIPV.values()}
    assert marcas == {"hiitio", "einnova", "soltech"}


# ---------------------------------------------------------------------------
# clasificar_familia_regional() -- CdTe y CIS siempre resuelven a una
# familia representativa; Crystalline solo con evidencia positiva.
# ---------------------------------------------------------------------------


def test_cdte_generico_usa_familia_representativa():
    assert clasificar_familia_regional("CdTe") == "cdte_semit"
    assert clasificar_familia_regional("CdTe pelicula delgada") == "cdte_semit"


def test_cdte_soltech_o_asp_st1_usa_familia_soltech():
    # El panel real ASP-ST1-T40 (Teusaquillo) es de esta familia.
    assert clasificar_familia_regional("SolTech CdTe semitransparente") == "soltech_transparente"
    assert clasificar_familia_regional("ASP-ST1 CdTe") == "soltech_transparente"


def test_cis_o_cigs_usa_la_unica_familia_disponible():
    assert clasificar_familia_regional("CIGS") == "cigs"
    assert clasificar_familia_regional("CIS") == "cigs"


def test_crystalline_generico_sin_palabra_clave_no_inventa_familia():
    # "MonoSi" es Crystalline pero no da ninguna pista de familia específica
    # -- las familias Crystalline reales tienen puntajes MUY distintos entre
    # sí (bifacial=1 en Andina vs. teja BC=3 en Andina), así que asignar una
    # al azar sería falsa precisión. Debe devolver None.
    assert clasificar_familia_regional("MonoSi") is None
    assert clasificar_familia_regional("N-Type TOPCon Bifacial") == "einnova_bifacial"  # sí tiene pista


def test_crystalline_con_palabras_clave_reales_del_catalogo():
    assert clasificar_familia_regional("Mono PERC Bifacial BIPV") == "einnova_bifacial"
    assert clasificar_familia_regional("N-Type TopCon Flex") == "topcon_flex"
    # "Teja" por sí sola no basta -- primero debe reconocerse como
    # Crystalline (mono/topcon/etc.); "Teja BC negra" a secas no lo es
    # (ver test_tecnologia_no_reconocida_no_inventa_nada, mismo principio).
    assert clasificar_familia_regional("MonoSi Teja BC negra") == "einnova_teja_bc"


def test_tecnologia_no_reconocida_no_inventa_nada():
    assert clasificar_familia_regional("Perovskita experimental") is None
    assert clasificar_familia_regional(None) is None
    assert clasificar_familia_regional("") is None


# ---------------------------------------------------------------------------
# evaluar_compatibilidad_regional() -- casos reales anclados al RTF/Excel.
# ---------------------------------------------------------------------------


def test_bifacial_en_bogota_da_no_recomendado_caso_real_del_rtf():
    # "Bifacial 580W en Andina = 1 (rojo, no recomendado)" -- ejemplo real
    # documentado explícitamente: Bogotá/Medellín, tejados a dos aguas sin
    # cámara de aire, la ganancia bifacial no se aprovecha.
    r = evaluar_compatibilidad_regional("Mono PERC Bifacial BIPV", 4.711, -74.072)
    assert r is not None
    assert r["region"] == "andina"
    assert r["score"] == 1
    assert r["nivel"] == "no_recomendado"


def test_flexible_en_choco_da_optimo_caso_real_del_rtf():
    # "Flexible 250W en Pacífica = 3 (verde, óptimo)" -- arquitectura
    # palafítica, baja capacidad portante, tropicalización a humedad extrema.
    r = evaluar_compatibilidad_regional("N-Type TopCon Flex", 5.69, -76.66)
    assert r is not None
    assert r["region"] == "pacifica"
    assert r["score"] == 3
    assert r["nivel"] == "optimo"


def test_familia_no_clasificable_devuelve_none_no_falso_positivo():
    r = evaluar_compatibilidad_regional("MonoSi", 4.711, -74.072)
    assert r is None


def test_evaluar_desde_ciudad_resuelve_lat_lon_real():
    r = evaluar_compatibilidad_regional_desde_ciudad("CdTe", "Bogotá")
    assert r is not None
    assert r["region"] == "andina"
    assert r["confianza"] == "alta"


def test_evaluar_desde_ciudad_desconocida_devuelve_none():
    assert evaluar_compatibilidad_regional_desde_ciudad("CdTe", "Ciudad Inexistente XYZ") is None
