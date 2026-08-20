"""
Módulo de presupuesto — estimación paramétrica de CAPEX/OPEX y recolección
de ítems de cotización.

Extraído de pages/8_💼_Presupuesto.py (auditoría Fase 1, cuello de botella
#3): la página tenía lógica financiera real escrita directamente en el
archivo de UI, sin módulo propio en calculos/. Funciones puras — no tocan
Streamlit ni session_state; la página sigue siendo dueña de leer/escribir
el estado de sesión y de pasar los datos ya extraídos.
"""

# ══════════════════════════════════════════════════════════════════════════════
# BENCHMARKS PARAMÉTRICOS — Colombia 2025-2026
# Fuente: Guía de Costos BIPV / IRENA / datos de mercado colombiano
# ══════════════════════════════════════════════════════════════════════════════
BENCH = {
    # ── tipo_instalacion → escenario → { ítem: USD/Wp o USD fijo }
    # ── Formato: (opt, base, cons)
    "Granja FV campo": {
        "modulos_wp":       (0.180, 0.200, 0.220),
        "inversores_wp":    (0.060, 0.075, 0.090),
        "estructura_wp":    (0.080, 0.100, 0.120),
        "cableado_wp":      (0.040, 0.050, 0.060),
        "protecciones_wp":  (0.015, 0.020, 0.025),
        "trafo_fijo":       (15000, 22000, 35000),   # USD fijo (>100 kWp)
        "scada_fijo":       ( 8000, 11000, 15000),   # USD fijo
        "obra_civil_wp":    (0.050, 0.070, 0.090),
        "montaje_wp":       (0.040, 0.055, 0.070),
        "elect_wp":         (0.030, 0.040, 0.050),
        "puesta_marcha_wp": (0.010, 0.015, 0.020),
        "logistica_pct":    (0.030, 0.050, 0.070),  # % de equipos (módulos+inv)
        "ingenieria_pct":   (0.015, 0.022, 0.030),  # % CAPEX directo
        "pm_pct":           (0.030, 0.040, 0.050),  # % CAPEX directo
        "permisos_fijo":    ( 5000,  8000, 14000),  # USD fijo
        "conexion_fijo":    ( 8000, 16000, 32000),  # USD fijo
        "contingencia_pct": (0.080, 0.100, 0.120),  # % CAPEX total
        "opex_om_kw":       (  8.0,  10.0,  12.0),  # USD/kWp/año
        "opex_limpieza_kw": (  2.0,   3.0,   4.0),
        "opex_reposicion_kw":(  2.0,   2.5,   3.0),
        "opex_monitoreo_kw":(  3.0,   4.0,   5.0),
        "opex_seguro_pct":  (0.003, 0.004, 0.005),  # % CAPEX/año
    },
    "Techo industrial": {
        "modulos_wp":       (0.180, 0.205, 0.230),
        "inversores_wp":    (0.065, 0.080, 0.095),
        "estructura_wp":    (0.060, 0.080, 0.100),
        "cableado_wp":      (0.035, 0.045, 0.055),
        "protecciones_wp":  (0.012, 0.018, 0.022),
        "trafo_fijo":       (    0,     0,     0),   # no aplica típicamente
        "scada_fijo":       ( 5000,  8000, 12000),
        "obra_civil_wp":    (0.020, 0.030, 0.040),
        "montaje_wp":       (0.035, 0.050, 0.065),
        "elect_wp":         (0.025, 0.035, 0.045),
        "puesta_marcha_wp": (0.008, 0.012, 0.018),
        "logistica_pct":    (0.020, 0.035, 0.050),
        "ingenieria_pct":   (0.015, 0.022, 0.030),
        "pm_pct":           (0.025, 0.035, 0.045),
        "permisos_fijo":    ( 3000,  6000, 10000),
        "conexion_fijo":    ( 5000, 10000, 20000),
        "contingencia_pct": (0.070, 0.090, 0.110),
        "opex_om_kw":       (  6.0,   9.0,  12.0),
        "opex_limpieza_kw": (  1.5,   2.5,   3.5),
        "opex_reposicion_kw":(  2.0,   2.5,   3.0),
        "opex_monitoreo_kw":(  2.0,   3.0,   4.0),
        "opex_seguro_pct":  (0.003, 0.004, 0.005),
    },
    "BIPV fachada/pérgola": {
        "modulos_wp":       (0.250, 0.320, 0.400),
        "inversores_wp":    (0.070, 0.090, 0.110),
        "estructura_wp":    (0.200, 0.280, 0.380),
        "cableado_wp":      (0.050, 0.065, 0.080),
        "protecciones_wp":  (0.015, 0.022, 0.030),
        "trafo_fijo":       (    0,     0,     0),
        "scada_fijo":       ( 6000,  9000, 14000),
        "obra_civil_wp":    (0.040, 0.060, 0.090),
        "montaje_wp":       (0.080, 0.120, 0.180),
        "elect_wp":         (0.040, 0.055, 0.070),
        "puesta_marcha_wp": (0.015, 0.022, 0.030),
        "logistica_pct":    (0.025, 0.040, 0.060),
        "ingenieria_pct":   (0.020, 0.030, 0.040),
        "pm_pct":           (0.035, 0.045, 0.060),
        "permisos_fijo":    ( 4000,  8000, 15000),
        "conexion_fijo":    ( 5000, 10000, 20000),
        "contingencia_pct": (0.100, 0.130, 0.160),
        "opex_om_kw":       ( 10.0,  13.0,  16.0),
        "opex_limpieza_kw": (  2.0,   3.0,   4.5),
        "opex_reposicion_kw":(  2.5,   3.0,   4.0),
        "opex_monitoreo_kw":(  1.0,   2.0,   3.0),   # Growatt cloud + soporte; SCADA ya en CAPEX
        "opex_seguro_pct":  (0.002, 0.003, 0.004),   # 0.2–0.4 %/año; sector solar Colombia
    },
}

# Factor de zona geográfica (afecta obra civil + logística)
ZONA_FACTOR = {
    "Bogotá / Sabana":          1.00,
    "Medellín / Antioquia":     1.05,
    "Cali / Valle":             1.07,
    "Barranquilla / Costa":     1.08,
    "Urabá / Chocó (tropical)": 1.17,
    "Llanos Orientales":        1.12,
    "Otra zona remota":         1.15,
}


def calcular_parametrico(kwp, tipo, escenario, zona):
    """Devuelve dict con desglose y totales en USD."""
    idx = {"Optimista": 0, "Base": 1, "Conservador": 2}[escenario]
    b = BENCH[tipo]
    zf = ZONA_FACTOR[zona]
    wp = kwp * 1000

    def g(key): return b[key][idx]

    # ── Equipos / duros ────────────────────────────────────────────────
    mod     = g("modulos_wp")    * wp
    inv     = g("inversores_wp") * wp
    est     = g("estructura_wp") * wp * zf
    cable   = g("cableado_wp")   * wp
    prot    = g("protecciones_wp") * wp
    trafo   = g("trafo_fijo")   if kwp >= 100 else 0
    scada   = g("scada_fijo")
    log_eq  = (mod + inv) * g("logistica_pct") * zf
    equip_total = mod + inv + est + cable + prot + trafo + scada + log_eq

    # ── Construcción / EPC ─────────────────────────────────────────────
    civil   = g("obra_civil_wp")    * wp * zf
    montaje = g("montaje_wp")       * wp
    elect   = g("elect_wp")         * wp
    pm_obra = g("puesta_marcha_wp") * wp
    epc_total = civil + montaje + elect + pm_obra

    # ── Costos directos ────────────────────────────────────────────────
    directo = equip_total + epc_total

    # ── Costos blandos ─────────────────────────────────────────────────
    ing     = directo * g("ingenieria_pct")
    pm      = directo * g("pm_pct")
    perm    = g("permisos_fijo")
    conex   = g("conexion_fijo")
    soft_total = ing + pm + perm + conex

    capex_base = directo + soft_total

    # ── Contingencias ──────────────────────────────────────────────────
    cont    = capex_base * g("contingencia_pct")
    capex_total = capex_base + cont

    # ── OPEX anual ─────────────────────────────────────────────────────
    # O&M y limpieza escalan con zona: requieren visitas presenciales → más
    # costosas en zonas remotas (Urabá zf=1.17, Llanos zf=1.12, etc.)
    opex_om     = g("opex_om_kw")         * kwp * zf
    opex_limp   = g("opex_limpieza_kw")   * kwp * zf
    opex_repos  = g("opex_reposicion_kw") * kwp        # repuestos: costo similar
    opex_mon    = g("opex_monitoreo_kw")  * kwp        # monitoreo remoto: no escala
    opex_seg    = capex_total * g("opex_seguro_pct")
    # ── Mínimo absoluto O&M para instalaciones ≥ 50 kWp ───────────────
    # Representa el costo mínimo de un contrato de mantenimiento preventivo
    # (visitas periódicas + mano de obra). Por debajo de este piso el modelo
    # subestima costos reales en proyectos medianos/grandes en Colombia.
    # Referencia: contrato básico BIPV/FV Colombia = USD 6,000–10,000/año.
    _opex_om_limp_calc = opex_om + opex_limp
    _opex_om_limp_min  = 8000.0 if kwp >= 300 else (5000.0 if kwp >= 50 else 0.0)
    if _opex_om_limp_calc < _opex_om_limp_min:
        _factor_min = _opex_om_limp_min / _opex_om_limp_calc if _opex_om_limp_calc > 0 else 1.0
        opex_om   *= _factor_min
        opex_limp *= _factor_min
    opex_total  = opex_om + opex_limp + opex_repos + opex_mon + opex_seg

    return {
        "kwp": kwp, "wp": wp,
        # Equipos
        "mod": mod, "inv": inv, "est": est, "cable": cable,
        "prot": prot, "trafo": trafo, "scada": scada, "log_eq": log_eq,
        "equip_total": equip_total,
        # EPC
        "civil": civil, "montaje": montaje, "elect": elect, "pm_obra": pm_obra,
        "epc_total": epc_total,
        # Soft
        "ing": ing, "pm": pm, "perm": perm, "conex": conex,
        "soft_total": soft_total,
        # Totales
        "directo": directo,
        "capex_base": capex_base,
        "cont": cont,
        "capex_total": capex_total,
        # OPEX
        "opex_om": opex_om, "opex_limp": opex_limp,
        "opex_repos": opex_repos, "opex_mon": opex_mon, "opex_seg": opex_seg,
        "opex_total": opex_total,
    }


def recolectar_items_cotizacion(secciones, trm_cop, etiquetas):
    """Extrae ítems activos de DataFrames de sección → filas de cotización.

    secciones : {clave_seccion: DataFrame} — ya extraídos de session_state
                por el llamador (columnas: Activo, Descripcion, Ref,
                Cantidad, Unidad, USD_un). El orden de iteración del dict
                determina el orden de las filas de salida.
    etiquetas : {clave_seccion: nombre_categoria_visible}

    NO incluye la columna 'Costos Blandos' aquí: se muestra como línea de
    total aparte para mantener el subtotal = CAPEX directo (materiales +
    equipos + mano de obra).
    """
    filas = []
    for _key, _df in secciones.items():
        if _df is None or not hasattr(_df, "iterrows"):
            continue
        for _, _r in _df.iterrows():
            if not bool(_r.get("Activo", True)):
                continue
            try:
                _cant = float(_r.get("Cantidad", 0) or 0)
                _uni_usd = float(_r.get("USD_un", 0) or 0)
            except (TypeError, ValueError):
                continue
            _desc = str(_r.get("Descripcion", "") or "").strip()
            _tot_usd = _cant * _uni_usd
            if not _desc or _tot_usd <= 0:
                continue
            filas.append({
                "categoria":    etiquetas.get(_key, _key),
                "descripcion":  _desc,
                "ref":          str(_r.get("Ref", "") or ""),
                "cantidad":     _cant,
                "unidad":       str(_r.get("Unidad", "") or ""),
                "unitario_usd": _uni_usd,
                "total_usd":    _tot_usd,
                "unitario_cop": _uni_usd * trm_cop,
                "total_cop":    _tot_usd * trm_cop,
            })
    return filas
