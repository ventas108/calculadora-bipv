# -*- coding: utf-8 -*-
"""`contexto_sesion()` incluyendo la verificación cruzada JRC/Huld
(31-ago-2026, pedido explícito del usuario: "el asistente si se le pregunta
ayude a explicar de forma asertiva dicha comparacion de acuerdo a los
valores calculados"). Sin tests previos para `contexto_sesion()` en este
repo -- primera cobertura."""
from calculos.asistente import contexto_sesion


def test_contexto_sesion_sin_verificacion_jrc_no_la_menciona():
    # 📊 Producción nunca corrió en esta sesión (o el panel no es
    # CdTe/CIS/Crystalline) -- no debe inventar una comparación.
    contexto = contexto_sesion({})
    assert "JRC" not in contexto


def test_contexto_sesion_incluye_verificacion_jrc_cuando_esta_disponible():
    estado = {
        "PR_sistema": 1.006,  # 100.6%, mismo caso real Teusaquillo
        "verificacion_jrc": {
            "tecnologia": "CdTe",
            "panel_nombre": "ASP-ST1-T40",
            "PR_pct": 89.41,
            "E_anual_kWh": 5825.0,
            "POA_anual_kWh_m2": 807.8,
            "referencia_literatura": {"techo": (74.92, 77.36)},
        },
    }
    contexto = contexto_sesion(estado)
    assert "JRC" in contexto
    assert "89.4" in contexto or "89,4" in contexto
    assert "100.6" in contexto or "100,6" in contexto


def test_contexto_sesion_con_verificacion_jrc_none_no_revienta():
    # session_state["verificacion_jrc"] queda explícitamente en None cuando
    # 📊 Producción corre pero la tecnología no aplica -- no debe romper.
    contexto = contexto_sesion({"verificacion_jrc": None})
    assert "JRC" not in contexto


def test_contexto_sesion_sin_compatibilidad_regional_no_la_menciona():
    contexto = contexto_sesion({})
    assert "Compatibilidad regional" not in contexto


def test_contexto_sesion_incluye_compatibilidad_regional_cuando_esta_disponible():
    estado = {
        "compatibilidad_regional_bipv": {
            "familia": "einnova_bifacial", "region": "andina", "region_etiqueta": "Andina",
            "confianza": "alta", "score": 1, "nivel": "no_recomendado", "icono": "🔴",
            "notas": "Cubiertas planas, agrovoltaico", "marca": "einnova",
        },
    }
    contexto = contexto_sesion(estado)
    assert "Compatibilidad regional" in contexto
    assert "Andina" in contexto
    assert "no recomendado" in contexto


def test_contexto_sesion_con_compatibilidad_regional_none_no_revienta():
    contexto = contexto_sesion({"compatibilidad_regional_bipv": None})
    assert "Compatibilidad regional" not in contexto
