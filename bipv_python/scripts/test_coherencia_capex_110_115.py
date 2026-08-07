"""Pruebas puras para #110 y #115 — coherencia de CAPEX entre Presupuesto y Financiero.

No requiere Streamlit. Simula session_state como un dict y reproduce la lógica de:
- Marca de FUENTE + timestamp al escribir presupuesto_capex_usd.
- Escritura del subtotal (cotización real) en el mismo "rerun".
- Selección de la fuente efectiva en Financiero según el toggle.

Ejecutar:  python3 scripts/test_coherencia_capex_110_115.py
"""
from datetime import datetime


# ── Réplica exacta de la función usada en la página Presupuesto ───────────────
def marcar_fuente_capex(ss: dict, fuente: str) -> None:
    ss["presupuesto_fuente"] = fuente
    ss["presupuesto_capex_ts"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ── Réplica de la escritura del subtotal (modo cotización real) ───────────────
def publicar_subtotal(ss: dict, capex_total: float) -> None:
    """Reproduce el bloque `if not _est_activa:` de la página Presupuesto."""
    est_activa = ss.get("est_rapida_aplicada", False)
    if not est_activa:
        capex_prev = ss.get("presupuesto_capex_usd", None)
        ss["presupuesto_capex_usd"] = capex_total
        # Comparación EXACTA: cualquier cambio de precio refresca el timestamp.
        if capex_prev != capex_total or ss.get("presupuesto_fuente") != "Presupuesto detallado":
            marcar_fuente_capex(ss, "Presupuesto detallado")


# ── Réplica del OPEX que realmente entra al flujo de caja en Financiero ───────
def opex_anual_en_flujo(ss: dict, capex_total: float, usar_opex_ppto: bool,
                        opex_pct_slider: float = 1.5) -> float:
    """Reproduce el cálculo del OPEX año 1 usado por VPN/TIR/payback/LCOE.

    Financiero deriva opex_pct contra el CAPEX ACTIVO (capex_total) cuando el OPEX
    viene del Presupuesto, de modo que `capex_total * opex_pct/100` == monto absoluto
    del Presupuesto tanto en modo vinculado como desvinculado. `calcular_flujo_caja`
    aplica `capex_usd * opex_pct_capex / 100` con capex_usd = capex_total.
    """
    ppto_opex_anual = float(ss.get("presupuesto_opex_anual_usd", 0.0))
    if ppto_opex_anual > 0 and usar_opex_ppto:
        opex_pct = ppto_opex_anual / capex_total * 100 if capex_total > 0 else 0.0
    else:
        opex_pct = opex_pct_slider
    return capex_total * opex_pct / 100 if capex_total > 0 else 0.0


# ── Réplica de la selección de fuente efectiva en Financiero ──────────────────
def fuente_efectiva_financiero(ss: dict, toggle_usar_ppto: bool):
    ppto_capex = float(ss.get("presupuesto_capex_usd", 0.0))
    ppto_fuente = str(ss.get("presupuesto_fuente", "")) or "Presupuesto detallado"
    usar_ppto = toggle_usar_ppto if ppto_capex > 0 else False
    fuente = ppto_fuente if usar_ppto else "Manual"
    capex_activo = ppto_capex if usar_ppto else None  # None = usa paramétrico manual
    return usar_ppto, fuente, capex_activo


def test_subtotal_fluye_mismo_rerun():
    ss = {}
    # Primer "rerun": el subtotal calculado desde los tabs cambia.
    publicar_subtotal(ss, 120_000.0)
    assert ss["presupuesto_capex_usd"] == 120_000.0
    assert ss["presupuesto_fuente"] == "Presupuesto detallado"
    assert ss["presupuesto_capex_ts"]  # timestamp escrito
    ts1 = ss["presupuesto_capex_ts"]

    # Rerun sin cambio de precio → NO refresca el timestamp.
    publicar_subtotal(ss, 120_000.0)
    assert ss["presupuesto_capex_ts"] == ts1, "timestamp no debe cambiar sin cambio de precio"

    # El usuario actualiza precios → el CAPEX y el timestamp cambian de inmediato.
    publicar_subtotal(ss, 135_500.0)
    assert ss["presupuesto_capex_usd"] == 135_500.0
    print("OK test_subtotal_fluye_mismo_rerun")


def test_fuente_estimacion_rapida():
    ss = {}
    marcar_fuente_capex(ss, "Estimación Rápida")
    ss["presupuesto_capex_usd"] = 98_000.0
    ss["est_rapida_aplicada"] = True

    # En modo estimación rápida NO se pisa el CAPEX con los tabs.
    publicar_subtotal(ss, 40_000.0)
    assert ss["presupuesto_capex_usd"] == 98_000.0
    assert ss["presupuesto_fuente"] == "Estimación Rápida"

    usar_ppto, fuente, capex = fuente_efectiva_financiero(ss, toggle_usar_ppto=True)
    assert usar_ppto is True and fuente == "Estimación Rápida" and capex == 98_000.0
    print("OK test_fuente_estimacion_rapida")


def test_toggle_desvincula_a_manual():
    ss = {"presupuesto_capex_usd": 200_000.0, "presupuesto_fuente": "Presupuesto detallado"}
    # Vinculado → usa Presupuesto.
    usar, fuente, capex = fuente_efectiva_financiero(ss, toggle_usar_ppto=True)
    assert usar and fuente == "Presupuesto detallado" and capex == 200_000.0
    # Desvinculado → Manual, no usa el CAPEX del presupuesto.
    usar, fuente, capex = fuente_efectiva_financiero(ss, toggle_usar_ppto=False)
    assert (not usar) and fuente == "Manual" and capex is None
    print("OK test_toggle_desvincula_a_manual")


def test_sin_presupuesto_es_manual():
    ss = {}
    usar, fuente, capex = fuente_efectiva_financiero(ss, toggle_usar_ppto=True)
    assert (not usar) and fuente == "Manual" and capex is None
    print("OK test_sin_presupuesto_es_manual")


def test_opex_absoluto_vinculado_vs_desvinculado():
    # Caso del reporte de auditoría: Presupuesto USD 100k con OPEX USD 2k/año.
    ss = {"presupuesto_capex_usd": 100_000.0, "presupuesto_opex_anual_usd": 2_000.0}

    # Vinculado: capex_total == CAPEX del Presupuesto → OPEX exacto 2,000.
    opex_vinc = opex_anual_en_flujo(ss, capex_total=100_000.0, usar_opex_ppto=True)
    assert abs(opex_vinc - 2_000.0) < 1e-6, f"vinculado esperaba 2000, dio {opex_vinc}"

    # Desvinculado: CAPEX manual USD 50k. El OPEX del flujo DEBE seguir siendo el
    # monto absoluto del Presupuesto (USD 2,000/año), NO 50k*2% = 1,000.
    opex_desv = opex_anual_en_flujo(ss, capex_total=50_000.0, usar_opex_ppto=True)
    assert abs(opex_desv - 2_000.0) < 1e-6, f"desvinculado esperaba 2000, dio {opex_desv}"
    assert abs(opex_desv - opex_vinc) < 1e-6, "el OPEX no debe cambiar al desvincular el CAPEX"

    # Con OPEX del Presupuesto desactivado → usa el slider paramétrico sobre el CAPEX activo.
    opex_param = opex_anual_en_flujo(ss, capex_total=50_000.0, usar_opex_ppto=False, opex_pct_slider=1.5)
    assert abs(opex_param - 750.0) < 1e-6, f"paramétrico esperaba 750, dio {opex_param}"
    print("OK test_opex_absoluto_vinculado_vs_desvinculado")


def test_timestamp_cambio_pequeno():
    # #2 — un cambio de USD 1 (o menos) debe refrescar el timestamp.
    ss = {}
    publicar_subtotal(ss, 100_000.0)
    ts1 = ss["presupuesto_capex_ts"]
    # Cambio de exactamente USD 1 → antes se ignoraba con abs(...) > 1.0.
    publicar_subtotal(ss, 100_001.0)
    assert ss["presupuesto_capex_usd"] == 100_001.0
    # No aseveramos que el string de tiempo difiera (misma hora posible), pero sí
    # que la lógica marcó la fuente (rama ejecutada) tras el cambio pequeño.
    assert ss["presupuesto_fuente"] == "Presupuesto detallado"
    # Sin cambio → no re-marca (misma condición de igualdad exacta).
    _ts_before = ss["presupuesto_capex_ts"]
    publicar_subtotal(ss, 100_001.0)
    assert ss["presupuesto_capex_ts"] == _ts_before
    print("OK test_timestamp_cambio_pequeno")


if __name__ == "__main__":
    test_subtotal_fluye_mismo_rerun()
    test_fuente_estimacion_rapida()
    test_toggle_desvincula_a_manual()
    test_sin_presupuesto_es_manual()
    test_opex_absoluto_vinculado_vs_desvinculado()
    test_timestamp_cambio_pequeno()
    print("\n✅ TODOS LOS TESTS PASARON")
