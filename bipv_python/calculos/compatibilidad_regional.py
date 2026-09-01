# -*- coding: utf-8 -*-
"""Auditoría de compatibilidad regional BIPV — combina la matriz real de
juicio experto (`datos/compatibilidad_regional_bipv.py`, portada 1:1 desde
la app hermana https://bipv.innovacionquimica.com.co/) con la detección de
región por polígonos geográficos (`calculos/regiones_colombia.py`, misma
fuente) para producir una alarma no bloqueante: "¿este panel/tecnología
encaja con esta región?" — respondida con criterios físicos y de diseño
reales (estructura, estética, salinidad, logística, transmitancia), no solo
con el juicio energético del modelo JRC/Huld (ese es un dato COMPLEMENTARIO,
ver `calculos/modelo_jrc_huld.py`).

Pedido explícito del usuario (31-ago-2026): "que la app reconozca -- con los
mismos criterios reales que ya documentaste (GHI, temperatura, humedad,
fenómenos críticos) -- si ese panel/tecnología simplemente no encaja con esa
región", aclarando que esto NO es un veredicto sino una auditoría.

Diseño anti-falso-positivo (mismo principio que `diseno_electrico_confirmado()`
y el resto de esta sesión): si no se puede identificar con evidencia positiva
una familia de producto específica dentro de la matriz portada (ej. un panel
"Crystalline" genérico sin palabra clave reconocible -- bifacial, flex, teja,
etc. -- son familias con puntajes MUY distintos entre sí), la función
devuelve `None` para el score estático en vez de inventar un representante
-- nunca falsa precisión.
"""
from datos.compatibilidad_regional_bipv import COMPATIBILIDAD_REGIONAL_BIPV
from calculos.regiones_colombia import detectar_region_colombia
from calculos.modelo_jrc_huld import clasificar_tecnologia_jrc

NIVEL_POR_SCORE = {1: "no_recomendado", 2: "aceptable", 3: "optimo"}
ICONO_POR_SCORE = {1: "🔴", 2: "🟡", 3: "🟢"}


def clasificar_familia_regional(tecnologia_cruda: str | None) -> str | None:
    """
    Clasifica el texto libre de tecnología del catálogo (ej. "CdTe pelicula
    delgada", "Mono PERC Bifacial BIPV") hacia una de las 21 familias reales
    de `COMPATIBILIDAD_REGIONAL_BIPV`. Primero resuelve la tecnología amplia
    (CdTe/CIS/Crystalline, reutilizando `clasificar_tecnologia_jrc()`), luego
    busca palabras clave de familia DENTRO de esa tecnología -- nunca cruza
    entre tecnologías distintas.

    Para CdTe y CIS, siempre hay una familia representativa razonable (pocas
    familias, puntajes similares entre sí). Para Crystalline -- que en la
    matriz real tiene familias con puntajes MUY distintos entre sí, ej.
    bifacial=1 en Andina vs. teja BC=3 en Andina -- solo se asigna una
    familia si hay una palabra clave positiva; si no, devuelve None (más
    vale no responder que responder con falsa precisión).
    """
    tecnologia = clasificar_tecnologia_jrc(tecnologia_cruda) if tecnologia_cruda else None
    if tecnologia is None:
        return None
    t = tecnologia_cruda.lower()

    if tecnologia == "CdTe":
        if "soltech" in t or "asp-st1" in t or "asp st1" in t:
            return "soltech_transparente"
        if "vidrio" in t or "glass" in t:
            return "einnova_vidrio"
        return "cdte_semit"  # representante consensuado (HIITIO/EINNOVA comparten este puntaje)

    if tecnologia == "CIS":
        return "cigs"  # única familia CIS/CIGS disponible en la matriz portada

    # Crystalline -- solo con evidencia positiva de familia específica.
    if "bifacial" in t:
        return "einnova_bifacial"
    if "flex" in t:
        return "topcon_flex"
    if "curtain" in t or "cortina" in t:
        return "hjt_curtain"
    if "teja" in t or "tile" in t:
        return "einnova_teja_bc"
    if "antirreflej" in t:
        return "einnova_antirreflejo"
    if "agri" in t or "invernadero" in t:
        return "einnova_agripv"
    if "pavimento" in t:
        return "einnova_pavimento"
    if "fachada" in t:
        return "einnova_fachada"
    return None


def evaluar_compatibilidad_regional(tecnologia_cruda: str, lat: float, lon: float) -> dict | None:
    """
    Evalúa la compatibilidad regional real de un panel para un sitio dado.

    Devuelve `None` (nunca inventa) si no se pudo clasificar ninguna familia
    (`clasificar_familia_regional()` devolvió None). En cualquier otro caso,
    devuelve un dict:
      familia          : clave de la familia identificada.
      region / region_etiqueta / confianza : de `detectar_region_colombia()`.
      score            : 1/2/3 (no recomendado/aceptable/óptimo) para ESA región.
      nivel            : "no_recomendado" | "aceptable" | "optimo".
      icono            : 🔴/🟡/🟢.
      notas            : nota técnica real de la matriz portada.
      marca            : de qué catálogo real viene la familia (hiitio/einnova/soltech).
    """
    familia = clasificar_familia_regional(tecnologia_cruda)
    if familia is None:
        return None

    info = COMPATIBILIDAD_REGIONAL_BIPV[familia]
    deteccion = detectar_region_colombia(lat, lon)
    score = info["regional"][deteccion.region]

    return {
        "familia": familia,
        "region": deteccion.region,
        "region_etiqueta": deteccion.etiqueta,
        "confianza": deteccion.confianza,
        "score": score,
        "nivel": NIVEL_POR_SCORE[score],
        "icono": ICONO_POR_SCORE[score],
        "notas": info["notas"],
        "marca": info["marca"],
    }


def evaluar_compatibilidad_regional_desde_ciudad(tecnologia_cruda: str, ciudad_nombre: str) -> dict | None:
    """Igual que `evaluar_compatibilidad_regional()`, pero resolviendo lat/lon
    desde el nombre de ciudad vía `datos/ciudades_colombia.py` -- el punto de
    entrada más cómodo desde una página de la app, que solo tiene el nombre
    de la ciudad en session_state, no coordenadas sueltas."""
    from datos.ciudades_colombia import CIUDADES

    ciudad = CIUDADES.get(ciudad_nombre)
    if not ciudad:
        return None
    return evaluar_compatibilidad_regional(tecnologia_cruda, ciudad["lat"], ciudad["lon"])
