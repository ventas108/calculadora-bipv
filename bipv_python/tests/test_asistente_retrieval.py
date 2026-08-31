# -*- coding: utf-8 -*-
"""Calidad de búsqueda del 🧭 Asistente (`BaseConocimiento.buscar()`).

Bug real encontrado probando la app en vivo (31-ago-2026): el usuario preguntó
"que alertas nuevas se instalaron para no cometer errores aguas abajo en los
modulos" y el asistente citó 2 alertas VIEJAS (densidad/PR, alarma SDM) en vez
de la alerta de vigencia real de esa semana. `buscar()` nunca tuvo tests --
esta clase de regresión podía (y de hecho volvió a) pasar desapercibida.

Causas reales encontradas, ambas corregidas en `calculos/asistente.py`:
1. Conteo de palabras sin ponderar: "nuevo"/"nueva" marca decenas de
   secciones no relacionadas en todo el manual (cada función agregada se
   documenta con esa etiqueta) -- una pregunta genérica les daba el mismo
   peso que a una palabra realmente específica de la sección correcta.
   Corregido con IDF (frecuencia inversa de documento): palabras raras
   pesan más que las genéricas.
2. Sin normalización de plural/singular: la pregunta decía "alertas" pero el
   título de la sección real decía "alerta" (singular) -- nunca calzaban,
   así que la sección específica perdía el bono de título. Corregido con
   `_singularizar()`, una heurística simple aplicada en `_normalizar()`.

Ver `DIAGNOSTICO_RETRIEVAL_IDF_PLURALES.md` para el detalle completo.
"""
from calculos.asistente import BaseConocimiento, _normalizar, _singularizar


# ---------------------------------------------------------------------------
# _singularizar() / _normalizar() -- la normalización de plurales en sí.
# ---------------------------------------------------------------------------


def test_singularizar_calza_plural_es_con_singular():
    # El caso real exacto del bug: la pregunta del usuario decía "alertas",
    # el título de la sección real decía "alerta".
    assert _singularizar("alertas") == _singularizar("alerta") == "alerta"
    assert _singularizar("errores") == _singularizar("error") == "error"
    assert _singularizar("paneles") == _singularizar("panel") == "panel"
    assert _singularizar("modulos") == _singularizar("modulo") == "modulo"


def test_singularizar_no_toca_palabras_cortas():
    # Evita falsos positivos agresivos en palabras de 4 letras o menos --
    # "mes"/"gas" no deben perder su última letra.
    assert _singularizar("mes") == "mes"
    assert _singularizar("gas") == "gas"


def test_normalizar_aplica_singularizacion_end_to_end():
    assert "alerta" in _normalizar("cuáles son las alertas nuevas")
    assert _normalizar("Módulos y Paneles") == ["modulo", "panel"]


# ---------------------------------------------------------------------------
# IDF -- palabras raras deben pesar más que las genéricas al puntuar.
# ---------------------------------------------------------------------------


def _base_sintetica() -> BaseConocimiento:
    # 5 secciones "decoy" con la palabra genérica "nuevo" (como el patrón
    # real "NUEVO" que marca funciones agregadas en todo el manual real) +
    # 1 sección específica con la palabra rara "vigencia", simulando el caso
    # real 25f contra las docenas de secciones "NUEVO" que le ganaban antes.
    secciones = []
    for i in range(5):
        texto = f"## Función genérica {i} NUEVO\n\nEsta función nueva hace algo distinto cada vez."
        secciones.append({"titulo": f"Función genérica {i} NUEVO", "texto": texto,
                           "tokens": set(_normalizar(texto))})
    texto_especifico = (
        "## Alerta de vigencia del diseño\n\n"
        "Esta alerta nueva avisa si el diseño perdió vigencia tras un cambio."
    )
    secciones.append({"titulo": "Alerta de vigencia del diseño", "texto": texto_especifico,
                       "tokens": set(_normalizar(texto_especifico))})
    return BaseConocimiento(secciones, idf=_idf_real(secciones))


def _idf_real(secciones):
    from calculos.asistente import _calcular_idf
    return _calcular_idf(secciones)


def test_idf_prioriza_seccion_especifica_sobre_decoys_genericos():
    base = _base_sintetica()
    # Pregunta genérica, igual en espíritu al bug real: usa "nuevas" (calza
    # con "nuevo" en las 6 secciones) pero también "vigencia" (calza SOLO
    # con la sección específica).
    resultado = base.buscar("que alertas nuevas hay sobre vigencia", k=1)
    assert resultado[0]["titulo"] == "Alerta de vigencia del diseño"


def test_sin_idf_precalculado_cae_a_peso_uniforme_no_revienta():
    # Instancia armada a mano (como en un test unitario simple), sin pasar
    # por cargar() -- buscar() no debe fallar por KeyError ni requerir idf.
    secciones = [
        {"titulo": "Sección A", "texto": "## Sección A\n\ncontenido sobre paneles",
         "tokens": set(_normalizar("Sección A contenido sobre paneles"))},
    ]
    base = BaseConocimiento(secciones)  # sin idf explícito
    resultado = base.buscar("paneles", k=1)
    assert resultado[0]["titulo"] == "Sección A"


# ---------------------------------------------------------------------------
# Regresión anclada al corpus REAL (el manual que de verdad usa la app) --
# la pregunta textual que el usuario hizo en el chat en vivo.
# ---------------------------------------------------------------------------


def test_buscar_real_encuentra_la_alerta_de_vigencia_no_solo_alertas_viejas():
    base = BaseConocimiento.cargar()
    pregunta = "que alertas nuevas se instalaron para no cometer errores aguas abajo en los modulos"

    resultado_k4 = base.buscar(pregunta, k=4)
    titulos_k4 = [s["titulo"] for s in resultado_k4]
    # La sección dedicada a la alerta real de esta semana debe aparecer en el
    # top-4 -- antes del fix de IDF/plurales, NO aparecía ni en el top-8.
    assert any("alerta de vigencia" in t.lower() for t in titulos_k4), titulos_k4

    # El detalle operativo específico de Dimensionamiento (dónde se dispara)
    # compite por los mismos primeros lugares con otras secciones igual de
    # válidas sobre el mismo tema (25f, 25g, 25h) -- se verifica con una
    # ventana un poco más ancha (k=6) en vez de exigirle el top-4 exacto,
    # que es sensible a qué tan seguido se agreguen nuevas secciones sobre
    # este mismo tema.
    titulos_k6 = [s["titulo"] for s in base.buscar(pregunta, k=6)]
    assert any("dimensionamiento" in t.lower() and "alerta" in t.lower() for t in titulos_k6), titulos_k6


def test_buscar_real_variante_de_la_pregunta_tambien_encuentra_25f():
    base = BaseConocimiento.cargar()
    resultado = base.buscar("cuales alertas son nuevas de esta semana", k=4)
    titulos = [s["titulo"] for s in resultado]
    assert any("manual consolidado" in t.lower() or "vigencia" in t.lower() or
               ("dimensionamiento" in t.lower() and "alerta" in t.lower())
               for t in titulos), titulos
