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


# ---------------------------------------------------------------------------
# Fix real (6-sep-2026, auditoría pedida por el usuario): sin marca/texto
# adicional, 5 de las 21 familias eran estructuralmente inalcanzables --
# "flex"/"teja"/"tile"/CIS/CdTe-soltech siempre resolvían a la misma familia
# hardcodeada sin importar la marca real del producto. Ver
# calculos.compatibilidad_regional::clasificar_familia_regional() docstring.
# ---------------------------------------------------------------------------


def test_panel_einnova_real_con_tile_resuelve_a_teja_plana_no_teja_bc():
    # Caso real encontrado auditando: datos/panel_einnova_esm_ft_120w.json
    # -- Tecnologia="...BIPV Tile" (no distingue plana/BC por sí sola),
    # pero Notas dice explícitamente "Teja solar PLANA doble vidrio BIPV".
    # Antes del fix, esto SIEMPRE resolvía a "einnova_teja_bc" (puntajes
    # reales distintos en Caribe 3 vs 2 e Insular 3 vs 2 -- falso positivo).
    familia = clasificar_familia_regional(
        "N-Type TOPCon Double Glass BIPV Tile",
        marca="EINNOVA Solarline",
        texto_adicional=(
            "EINNOVA ESM-FT 120W Flat Tile Color "
            "EINNOVA ESM-FT 120W — Teja solar plana doble vidrio BIPV."
        ),
    )
    assert familia == "einnova_teja_plana"


def test_panel_einnova_tile_sin_pista_de_plana_sigue_dando_teja_bc():
    # Con marca EINNOVA pero SIN la palabra "plana"/"flat" en ningún lado,
    # el default correcto sigue siendo teja_bc (no se inventa "plana" sin
    # evidencia -- mismo principio "nunca falsa precisión" del resto).
    assert clasificar_familia_regional(
        "N-Type TOPCon Double Glass BIPV Tile", marca="EINNOVA Solarline",
    ) == "einnova_teja_bc"


def test_hiitio_tile_ya_no_se_confunde_con_einnova():
    # Antes del fix, CUALQUIER "tile"/"teja" resolvía a "einnova_teja_bc"
    # sin importar la marca -- un HIITIO real (familia "hjt_tile", puntajes
    # propios) se habría reportado con los puntajes/notas de EINNOVA.
    assert clasificar_familia_regional(
        "N-Type TopCon Tile", marca="HIITIO",
    ) == "hjt_tile"


def test_einnova_flex_ya_no_se_confunde_con_topcon_flex_hiitio():
    # Antes del fix, "flex" SIEMPRE resolvía a "topcon_flex" (HIITIO) --
    # puntajes reales distintos en Orinoquía (3 vs 1) e Insular (3 vs 2).
    assert clasificar_familia_regional(
        "N-Type TopCon Flex", marca="EINNOVA",
    ) == "einnova_flexible"
    # Sin marca EINNOVA, el default previo (topcon_flex) se preserva --
    # ver test_crystalline_con_palabras_clave_reales_del_catalogo arriba.


def test_soltech_cis_ya_no_se_confunde_con_cigs_hiitio():
    # Antes del fix, cualquier CIS/CIGS SIEMPRE resolvía a "cigs" (HIITIO).
    assert clasificar_familia_regional("CIS", marca="SOLTECH") == "soltech_teja"
    assert clasificar_familia_regional("CIGS") == "cigs"   # sin marca: default previo intacto


@pytest.mark.parametrize("texto_adicional,familia_esperada", [
    ("Laminado", "soltech_laminado"),
    ("Doble Vidrio Hermetico DVH", "soltech_dvh"),
    ("Modulo opaco premium", "soltech_opaco"),
    ("", "soltech_transparente"),   # sin pista extra -- default SOLTECH previo
])
def test_soltech_cdte_desambigua_las_4_variantes_reales(texto_adicional, familia_esperada):
    assert clasificar_familia_regional(
        "CdTe", marca="SOLTECH", texto_adicional=texto_adicional,
    ) == familia_esperada


def test_evaluar_compatibilidad_regional_propaga_marca_y_texto_adicional():
    # Verifica el pipeline completo (no solo el clasificador aislado): con
    # la marca/notas reales del panel EINNOVA Tile, el score de Caribe debe
    # ser el de "einnova_teja_plana" (2), no el de "einnova_teja_bc" (3).
    r = evaluar_compatibilidad_regional(
        "N-Type TOPCon Double Glass BIPV Tile", 10.4, -75.5,   # Cartagena, Caribe
        marca="EINNOVA Solarline",
        texto_adicional="Teja solar plana doble vidrio BIPV.",
    )
    assert r is not None
    assert r["familia"] == "einnova_teja_plana"
    assert r["region"] == "caribe"
    assert r["score"] == 2
