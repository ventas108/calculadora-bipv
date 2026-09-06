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


def clasificar_familia_regional(
    tecnologia_cruda: str | None,
    marca: str | None = None,
    texto_adicional: str | None = None,
) -> str | None:
    """
    Clasifica el texto libre de tecnología del catálogo (ej. "CdTe pelicula
    delgada", "Mono PERC Bifacial BIPV") hacia una de las 21 familias reales
    de `COMPATIBILIDAD_REGIONAL_BIPV`. Primero resuelve la tecnología amplia
    (CdTe/CIS/Crystalline, reutilizando `clasificar_tecnologia_jrc()`), luego
    busca palabras clave de familia DENTRO de esa tecnología -- nunca cruza
    entre tecnologías distintas.

    Parámetros
    ----------
    tecnologia_cruda : campo "Tecnologia" del catálogo (obligatorio).
    marca            : campo "Marca" del catálogo (opcional). Bug real
                       encontrado el 6-sep-2026 auditando este módulo: sin
                       marca, palabras como "flex" o "teja"/"tile" resolvían
                       SIEMPRE a la misma familia hardcodeada sin importar
                       qué producto real disparó el match -- 5 de las 21
                       familias de la matriz eran estructuralmente
                       inalcanzables (ver DIAGNOSTICO_COMPATIBILIDAD_
                       REGIONAL_BIPV_v2.md). Con marca, se distingue
                       primero por fabricante y solo después por keyword.
    texto_adicional  : texto extra para desambiguar variantes de la MISMA
                       marca (ej. "nombre"/"notas" del catálogo) -- la
                       palabra que distingue "teja plana" de "teja BC" suele
                       estar en Notas/TipoPanel, no en el campo Tecnologia
                       (caso real: datos/panel_einnova_esm_ft_120w.json,
                       Tecnologia="...BIPV Tile" pero Notas="Teja solar
                       PLANA..." -- sin `texto_adicional` es indistinguible
                       de "teja BC" con solo el campo Tecnologia).

    Retrocompatible: sin `marca`/`texto_adicional` (ninguno de los callers
    anteriores a este fix los pasaba), el resultado es IDÉNTICO al de antes
    -- mismos defaults hardcodeados que ya estaban documentados y probados.

    Para Crystalline -- que en la matriz real tiene familias con puntajes
    MUY distintos entre sí, ej. bifacial=1 en Andina vs. teja BC=3 en Andina
    -- solo se asigna una familia si hay una palabra clave positiva; si no,
    devuelve None (más vale no responder que responder con falsa precisión).
    """
    tecnologia = clasificar_tecnologia_jrc(tecnologia_cruda) if tecnologia_cruda else None
    if tecnologia is None:
        return None
    t = tecnologia_cruda.lower()
    extra = (texto_adicional or "").lower()
    m = (marca or "").lower()
    t_completo = f"{t} {extra}"

    es_hiitio  = "hiitio"  in m
    es_einnova = "einnova" in m
    es_soltech = "soltech" in m or "soltech" in t or "asp-st1" in t or "asp st1" in t

    if tecnologia == "CdTe":
        if es_soltech:
            # 4 variantes SOLTECH reales con el mismo score hoy (ver docstring
            # del módulo) -- desambiguadas por si la matriz cambia a futuro.
            if "laminado" in t_completo:
                return "soltech_laminado"
            if "dvh" in t_completo or "doble vidrio" in t_completo or "double glass" in t_completo:
                return "soltech_dvh"
            if "opaco" in t_completo or "opaque" in t_completo:
                return "soltech_opaco"
            return "soltech_transparente"   # default SOLTECH sin más pistas
        if "vidrio" in t or "glass" in t:
            return "einnova_vidrio"
        return "cdte_semit"  # representante consensuado (HIITIO/EINNOVA comparten este puntaje)

    if tecnologia == "CIS":
        if es_soltech:
            return "soltech_teja"
        return "cigs"   # default HIITIO/sin marca -- comportamiento previo preservado

    # Crystalline -- solo con evidencia positiva de familia específica.
    if "bifacial" in t:
        return "einnova_bifacial"
    if "flex" in t_completo:
        return "einnova_flexible" if es_einnova else "topcon_flex"
    if "curtain" in t or "cortina" in t:
        return "hjt_curtain"
    if "teja" in t_completo or "tile" in t_completo:
        if es_hiitio:
            return "hjt_tile"
        if es_einnova and ("plana" in t_completo or "flat" in t_completo):
            return "einnova_teja_plana"
        return "einnova_teja_bc"   # default EINNOVA/sin marca -- comportamiento previo preservado
    if "antirreflej" in t:
        return "einnova_antirreflejo"
    if "agri" in t or "invernadero" in t:
        return "einnova_agripv"
    if "pavimento" in t:
        return "einnova_pavimento"
    if "fachada" in t:
        return "einnova_fachada"
    return None


# NOTA: "einnova_color_panel" queda sin palabra clave propia a propósito --
# no se encontró evidencia de una palabra distintiva real en ningún producto
# del catálogo actual para justificarla sin arriesgar un falso positivo
# (mismo principio "nunca falsa precisión" del resto de este módulo).
# Documentado como límite conocido, no corregido por falta de evidencia
# real, no por descuido. Si aparece un producto real con esa evidencia,
# agregar la rama aquí siguiendo el mismo patrón marca+keyword.


def evaluar_compatibilidad_regional(
    tecnologia_cruda: str,
    lat: float,
    lon: float,
    marca: str | None = None,
    texto_adicional: str | None = None,
) -> dict | None:
    """
    Evalúa la compatibilidad regional real de un panel para un sitio dado.

    `marca` y `texto_adicional` -- ver `clasificar_familia_regional()` para
    el porqué (bug real de 5 familias inalcanzables sin ellos, corregido
    6-sep-2026). Opcionales y retrocompatibles: si no se pasan, el resultado
    es idéntico al de antes de este fix.

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
    familia = clasificar_familia_regional(tecnologia_cruda, marca, texto_adicional)
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


def evaluar_compatibilidad_regional_desde_ciudad(
    tecnologia_cruda: str,
    ciudad_nombre: str,
    marca: str | None = None,
    texto_adicional: str | None = None,
) -> dict | None:
    """Igual que `evaluar_compatibilidad_regional()`, pero resolviendo lat/lon
    desde el nombre de ciudad vía `datos/ciudades_colombia.py` -- el punto de
    entrada más cómodo desde una página de la app, que solo tiene el nombre
    de la ciudad en session_state, no coordenadas sueltas."""
    from datos.ciudades_colombia import CIUDADES

    ciudad = CIUDADES.get(ciudad_nombre)
    if not ciudad:
        return None
    return evaluar_compatibilidad_regional(
        tecnologia_cruda, ciudad["lat"], ciudad["lon"], marca, texto_adicional
    )
