"""
Módulo de producción anual BIPV — IEC 61724.

Simula la energía hora a hora aplicando:
  1. SDM De Soto 2006 vectorizado  (pvlib + Rsh CdTe Mermoud 2005)
  2. Factor de pérdidas ópticas/eléctricas de la cascada Mismatch
  3. Temperatura de celda NOCT hora a hora
  4. Curva de eficiencia del inversor

Métricas de salida (IEC 61724):
  Y_f  — Final yield    (kWh/kWp)
  Y_r  — Reference yield (kWh/m² / kW/m² = h)
  Y_a  — Array yield    (kWh/kWp)
  PR   — Performance Ratio = Y_f / Y_r
  CF   — Capacity Factor (%)
"""

import numpy as np
import pandas as pd
import pvlib

from calculos.modelo_iv import calcular_rsh_cdte, obtener_constantes_tecnologia
from calculos.temperatura import temperatura_celda_noct
from calculos.agregador_anual import (
    agregar_anual_8760_poa,
    validar_entradas_horarias_8760,
)

# ── Constantes físicas (mismas que modelo_iv.py) ──────────────────────────────
K_BOLTZMANN = 1.380649e-23
Q_ELECTRON  = 1.602176634e-19
T_REF_K     = 298.15
G_REF       = 1000.0


# ── Parámetros SDM mínimos requeridos para el modelo De Soto completo ─────────
_SDM_PARAMS_REQUERIDOS = ("I_L_ref", "I_o_ref", "R_s", "R_sh_ref", "a_ref")


def panel_tiene_sdm_completo(panel: dict) -> bool:
    """Retorna True si el panel tiene todos los parámetros SDM para De Soto 2006."""
    return all(
        panel.get(p) is not None and float(panel.get(p)) != 0.0
        for p in _SDM_PARAMS_REQUERIDOS
    )


def _calcular_pmax_vectorizado(
    G: np.ndarray,
    T_cel: np.ndarray,
    panel: dict,
) -> np.ndarray:
    """
    Calcula Pmax (W) por módulo hora a hora usando SDM De Soto 2006 vectorizado.
    Utiliza el modelo Rsh exponencial CdTe (Mermoud 2005) en lugar del lineal de pvlib.

    G     : irradiancia efectiva en el plano (W/m²) — array 1D
    T_cel : temperatura de celda (°C) — array 1D
    panel : dict con parámetros SDM del catálogo

    Retorna: array 1D de Pmax (W) por módulo
    """
    # ── Fallback para paneles sin parámetros SDM completos ───────────────────
    # (paneles del catálogo Excel que no tienen a_ref, I_L_ref, etc.)
    if not panel_tiene_sdm_completo(panel):
        # panel.get("Tk_gamma", -0.45) NO cubre el caso real: en el catálogo
        # Excel la clave existe pero vale None (no está ausente) -- .get()
        # con default solo aplica si la clave falta, así que quedaba
        # float(None) y TypeError. Bug preexistente, alcanzable recién ahora
        # que variable_panel() expone el catálogo Excel completo (27-ago-2026)
        # -- encontrado corriendo comparar_paneles() sobre los 65 paneles
        # reales. Mismo idiom `or` que ya usan NOCT (línea ~171) y Tk_alfa
        # (línea ~86) en este archivo para el mismo problema.
        gamma = float(panel.get("Tk_gamma") or -0.45) / 100.0   # %/°C → 1/°C
        pmax_stc = float(panel.get("Pmax_stc") or 0)
        pmax = pmax_stc * np.where(G > 5.0, G / 1000.0, 0.0) * (1.0 + gamma * (T_cel - 25.0))
        pmax = np.maximum(pmax, 0.0)
        return pmax

    constantes = obtener_constantes_tecnologia(panel["tecnologia"])

    # nNsVth_ref en Voltios (pvlib convention)
    Vt_ref     = K_BOLTZMANN * T_REF_K / Q_ELECTRON   # 0.025693 V
    nNsVth_ref = panel["a_ref"] * Vt_ref               # 154 × Vt_ref

    # R_sh exponencial saturado (Mermoud 2005 / PVsyst) — ver calcular_rsh_cdte()
    R_sh = calcular_rsh_cdte(
        G, panel["R_sh_ref"], c_Rsh=constantes["c_Rsh"], R_sh_0=panel.get("R_sh_0"),
    )

    I_L, I_o, R_s, _rsh_pvlib, nNsVth = pvlib.pvsystem.calcparams_desoto(
        effective_irradiance = G,
        temp_cell            = T_cel,
        alpha_sc             = panel["Tk_alfa"] / 100.0 * float(panel.get("Isc_stc") or panel.get("Isc") or 1.0),
        a_ref                = nNsVth_ref,
        I_L_ref              = panel["I_L_ref"],
        I_o_ref              = panel["I_o_ref"],
        R_sh_ref             = panel["R_sh_ref"],
        R_s                  = panel["R_s"],
        EgRef                = constantes["Eg_ref"],
        dEgdT                = constantes["dEgdT"],
        irrad_ref            = G_REF,
        temp_ref             = 25.0,
    )

    resultado = pvlib.pvsystem.singlediode(
        photocurrent       = I_L,
        saturation_current = I_o,
        resistance_series  = R_s,
        resistance_shunt   = R_sh,   # modelo CdTe Mermoud 2005
        nNsVth             = nNsVth,
        method             = 'lambertw',
    )

    pmax = np.array(resultado["p_mp"], dtype=float)
    pmax[G < 5.0] = 0.0     # sin producción nocturna / irradiancia mínima
    pmax[pmax < 0] = 0.0    # seguridad numérica
    return pmax


def simular_produccion_anual(
    tmy: pd.DataFrame,
    poa_base: pd.DataFrame,
    panel: dict,
    N_paneles: int,
    eta_inversor: float,
    factor_pr_mismatch: float,
    P_dc_stc_kW: float | None = None,
    k_bipv: float = 1.0,
    P_ac_nom_W: float | None = None,
) -> dict:
    """
    Simulación de producción anual hora a hora — IEC 61724.

    Parámetros
    ----------
    tmy                 : DataFrame TMY con columna 'T2m' (°C)
    poa_base            : DataFrame POA bruta con columna 'poa_global' (W/m²)
    panel               : dict del catálogo MODULOS_BIPV
    N_paneles           : número de módulos del sistema
    eta_inversor        : eficiencia del inversor (0.90–0.99)
    factor_pr_mismatch  : factor de pérdidas cascada (0–1)
                          = poa_efectiva / poa_bruta  (de página Mismatch)
    P_dc_stc_kW         : potencia pico instalada kWp; si None → N_paneles × Pmax_stc
    k_bipv              : factor de confinamiento térmico BIPV (IEA-PVPS T15).
                          1.0 = ventilado libre, 1.3 = fachada confinada (defecto BIPV),
                          1.5 = sellado total. Aumenta T_celda y reduce eficiencia.
    P_ac_nom_W          : potencia AC nominal del inversor (W) -- tope físico real de
                          salida (PVsyst la llama "Pnom" y SIEMPRE recorta con ella).
                          Si None (default, retrocompatible), NO se aplica ningún tope
                          -- comportamiento histórico de esta función. Bug real
                          encontrado el 29-ago-2026: sin este parámetro, P_ac = P_dc ×
                          eta_inversor sin límite, así que un array DC más grande que
                          el inversor (relación DC/AC > 1 -- el diseño ESTÁNDAR de la
                          industria, típicamente 1.1-1.3, no un caso raro) hacía que la
                          app sobreestimara producción -- verificado con un caso
                          sintético DC/AC=1.3: +10.8% en un día despejado, 5 de 24 h
                          recortadas. Nunca se detectó en los proyectos ya validados
                          contra PVsyst esta sesión (Urabá 0.88, Teusaquillo 0.54)
                          porque AMBOS tienen relación DC/AC < 1 -- el recorte nunca se
                          disparaba en esos casos, no porque no hiciera falta.

    Retorna dict
    ────────────
    E_dc_anual_kWh       : energía DC anual (kWh)
    E_ac_anual_kWh       : energía AC anual (kWh) -- YA recortada si P_ac_nom_W se pasó
    P_stc_kW             : potencia instalada (kWp)
    Y_f                  : Final yield (kWh/kWp)
    Y_r                  : Reference yield (h = kWh/m²)
    Y_a                  : Array yield (kWh/kWp)
    PR                   : Performance Ratio IEC 61724
    CF_pct               : Capacity Factor (%)
    perdida_temp_kWh     : energía perdida por temperatura
    perdida_inv_kWh      : energía perdida en inversor por eficiencia (SIN recorte)
    perdida_clipping_kWh : energía perdida por recorte al Pnom del inversor (0 si no
                          se pasó P_ac_nom_W, o si el array nunca superó el inversor)
    horas_con_clipping   : nº de horas del año con recorte activo (0-8760)
    df_horario           : DataFrame horario (G_eff, T_cel, Pmax, P_dc, P_ac, clipping_kW)
    df_mensual           : DataFrame mensual con E_dc, E_ac, kWh/kWp
    """
    if P_dc_stc_kW is None:
        P_dc_stc_kW = round(panel.get("Pmax_stc", 60) * N_paneles / 1000, 3)

    # ── Validar año TMY completo antes de simular ─────────────────────────────
    # Nunca usar intersection(): descartaría horas silenciosamente y después
    # las métricas anuales aparentarían cubrir 8760 h aunque no lo hagan.
    validar_entradas_horarias_8760(tmy, poa_base)
    idx   = tmy.index
    G_raw = poa_base.loc[idx, "poa_global"].values.astype(float)
    T_amb = tmy.loc[idx, "T2m"].values.astype(float)

    # ── Irradiancia efectiva (cascada mismatch aplicada) ──────────────────────
    G_eff = np.clip(G_raw * factor_pr_mismatch, 0, None)

    # ── Temperatura de celda hora a hora (modelo NOCT + k_BIPV confinamiento) ──
    try:
        NOCT = float(panel.get("NOCT") or 45.0)
        if not (20.0 < NOCT < 100.0):
            NOCT = 45.0
    except (TypeError, ValueError):
        NOCT = 45.0
    # k_bipv eleva la temperatura de celda en fachadas con ventilación restringida.
    # IEA-PVPS T15: 1.0=ventilado libre, 1.3=confinado típico, 1.5=sellado total.
    T_cel = temperatura_celda_noct(G_eff, T_amb, NOCT=NOCT, k_bipv=k_bipv)

    # ── SDM vectorizado — Pmax por módulo ─────────────────────────────────────
    pmax_mod = _calcular_pmax_vectorizado(G_eff, T_cel, panel)

    # ── Pérdida por temperatura (referencia: Pmax a T=25°C con mismo G_eff) ───
    T_ref_arr = np.full_like(T_cel, 25.0)
    pmax_stc_g = _calcular_pmax_vectorizado(G_eff, T_ref_arr, panel)
    perdida_temp_por_modulo = np.maximum(pmax_stc_g - pmax_mod, 0.0)

    # ── Escalar al sistema ─────────────────────────────────────────────────────
    P_dc_W       = pmax_mod * N_paneles
    P_ac_sin_recorte_W = P_dc_W * eta_inversor
    # Recorte al Pnom del inversor (PVsyst: siempre activo) -- ver docstring
    # "P_ac_nom_W" de esta función para el hallazgo real que motivó esto.
    if P_ac_nom_W is not None and P_ac_nom_W > 0:
        P_ac_W = np.minimum(P_ac_sin_recorte_W, P_ac_nom_W)
    else:
        P_ac_W = P_ac_sin_recorte_W
    clipping_W = P_ac_sin_recorte_W - P_ac_W   # siempre >= 0

    # ── Energías anuales (Wh → kWh) ───────────────────────────────────────────
    E_dc_anual  = float(P_dc_W.sum()) / 1000.0
    E_ac_anual  = float(P_ac_W.sum()) / 1000.0
    E_ac_sin_recorte_anual = float(P_ac_sin_recorte_W.sum()) / 1000.0
    perdida_temp_kWh = float(perdida_temp_por_modulo.sum()) * N_paneles / 1000.0
    # Pérdida de eficiencia PURA (sin recorte) -- separada del recorte para que
    # cada pérdida se pueda reportar por su causa real, como hace PVsyst.
    perdida_inv_kWh      = E_dc_anual - E_ac_sin_recorte_anual
    perdida_clipping_kWh = E_ac_sin_recorte_anual - E_ac_anual
    horas_con_clipping   = int(np.sum(clipping_W > 1e-6))

    # ── Métricas IEC 61724 ────────────────────────────────────────────────────
    H_i  = float(G_raw.sum()) / 1000.0          # POA bruta kWh/m²
    H_ef = float(G_eff.sum()) / 1000.0          # POA efectiva kWh/m² (post-mismatch)
    Y_r  = H_i                                   # Reference yield [h] = H_t / G_STC (IEC 61724)
    # NOTA: Y_r usa POA bruta (H_i), no H_ef, para que el PR incluya las pérdidas
    # de mismatch como una pérdida real (PR más conservador y correcto según IEC 61724).
    Y_a  = E_dc_anual  / P_dc_stc_kW if P_dc_stc_kW > 0 else 0.0   # Array yield
    Y_f  = E_ac_anual  / P_dc_stc_kW if P_dc_stc_kW > 0 else 0.0   # Final yield
    PR   = Y_f / Y_r   if Y_r > 0    else 0.0   # Performance Ratio
    CF   = E_ac_anual  / (P_dc_stc_kW * 8760) if P_dc_stc_kW > 0 else 0.0

    # ── DataFrame horario ─────────────────────────────────────────────────────
    df_h = pd.DataFrame({
        "G_eff_Wm2":    G_eff,
        "T_cel_C":      T_cel,
        "Pmax_mod_W":   pmax_mod,
        "P_dc_kW":      P_dc_W  / 1000.0,
        "P_ac_kW":      P_ac_W  / 1000.0,
        "perdida_T_kW": perdida_temp_por_modulo * N_paneles / 1000.0,
        "clipping_kW":  clipping_W / 1000.0,
    }, index=idx)

    # ── Contrato anual oficial: suma directa de las 8760 horas ───────────────
    # Se conservan las claves E_* históricas para Baterías, Financiero y Reporte.
    anual_8760 = agregar_anual_8760_poa(
        resultado_horario=df_h,
        poa_horaria=poa_base,
        columnas_energia=("P_dc_kW", "P_ac_kW", "perdida_T_kW", "clipping_kW"),
    )["annual_8760"]

    # ── DataFrame mensual ─────────────────────────────────────────────────────
    meses_es = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
    df_m = (df_h[["P_dc_kW","P_ac_kW","perdida_T_kW","clipping_kW"]]
            .resample("ME").sum()
            .rename(columns={
                "P_dc_kW":      "E_dc (kWh)",
                "P_ac_kW":      "E_ac (kWh)",
                "perdida_T_kW": "Pérdida T° (kWh)",
                "clipping_kW":  "Recorte inversor (kWh)",
            }))
    df_m["Producción (kWh/kWp)"] = df_m["E_ac (kWh)"] / P_dc_stc_kW if P_dc_stc_kW > 0 else 0
    df_m.index = [meses_es[m] for m in df_m.index.month]

    return {
        "E_dc_anual_kWh":         round(E_dc_anual, 0),
        "E_ac_anual_kWh":         round(E_ac_anual, 0),
        "P_stc_kW":               round(P_dc_stc_kW, 3),
        "Y_f":                    round(Y_f, 0),
        "Y_r":                    round(Y_r, 0),
        "Y_a":                    round(Y_a, 0),
        "PR":                     round(PR, 3),
        "CF_pct":                 round(CF * 100, 1),
        "perdida_temp_kWh":       round(perdida_temp_kWh, 0),
        "perdida_inv_kWh":        round(perdida_inv_kWh, 0),
        "perdida_clipping_kWh":   round(perdida_clipping_kWh, 0),
        "horas_con_clipping":     horas_con_clipping,
        "E_ac_sin_recorte_kWh":   round(E_ac_sin_recorte_anual, 0),
        "H_i_kWh_m2":             round(H_i, 1),
        "H_ef_kWh_m2":            round(H_ef, 1),
        "df_horario":             df_h,
        "df_mensual":             df_m,
        "annual_8760":            anual_8760,
        "critical_dates":         None,
        "uso_modelo_simplificado": not panel_tiene_sdm_completo(panel),
    }


def perdidas_desglosadas(
    res: dict,
    poa_bruta_kWh_m2: float,
    motor_optico_summary: dict | None = None,
) -> pd.DataFrame:
    """
    Tabla de balance energético IEC 61724 — nombres alineados con el "Loss
    Diagram" oficial de PVsyst (POA → IAM → Soiling → efectiva → STC →
    SDM → inversor → red), para que una corrida manual de PVsyst se pueda
    auditar contra esta tabla fila por fila, no solo comparando el PR final.
    Ver DIAGNOSTICO_LOSS_DIAGRAM_PVSYST.md (1-sep-2026).

    Para climas fríos de alta altitud (Bogotá, Medellín) el SDM puede producir
    MÁS que la referencia STC porque los módulos operan por debajo de 25°C.
    En ese caso el 'delta SDM' es positivo (ganancia, no pérdida).

    motor_optico_summary: el dict que devuelve calculos.motor_optico.cascada_optica()
    (o su copia en session_state["motor_optico_summary"]). Si trae las claves
    IAM/soiling reales, se insertan como filas propias (①a/①b) ANTES de "②
    Efecto SDM" -- cuya referencia entonces pasa a ser la POA post-IAM+soiling
    (no la bruta), para no contar la misma pérdida dos veces. Si no se pasa
    (o el Motor Óptico no corrió), la tabla queda exactamente como antes --
    nunca inventa un desglose que no se calculó de verdad para esta sesión.

    Categorías del Loss Diagram de PVsyst que esta tabla NO modela hoy
    (a propósito, sin inventar un número): "Module quality loss" y "Ohmic
    wiring loss" -- ver el diagnóstico arriba para el detalle.
    """
    P_stc  = res["P_stc_kW"]
    ref_dc = P_stc * poa_bruta_kWh_m2   # kWh teóricos a STC (Pmax_nom × POA bruta)
    if ref_dc == 0:
        return pd.DataFrame()

    filas = [
        {
            "Etapa":     "① E ref  (P_STC × POA bruta)",
            "kWh":       round(ref_dc, 0),
            "Δ kWh":     0,
            "Nota":      "Baseline a condiciones STC · equivalente a \"Global incident in coll. plane\" de PVsyst",
        },
    ]

    # ── ①a/①b — IAM y Soiling (solo si el Motor Óptico corrió de verdad) ──────
    _mo = motor_optico_summary or {}
    _tiene_cascada_optica = all(
        k in _mo for k in ("poa_optica_anual_kWh_m2", "poa_post_soil_anual_kWh_m2",
                            "perdida_iam_kWh_m2", "perdida_soil_kWh_m2")
    )
    if _tiene_cascada_optica:
        ref_post_iam  = P_stc * _mo["poa_optica_anual_kWh_m2"]
        ref_post_soil = P_stc * _mo["poa_post_soil_anual_kWh_m2"]
        filas.append({
            "Etapa":     "①a Pérdida IAM  (ángulo de incidencia)",
            "kWh":       round(ref_post_iam, 0),
            "Δ kWh":     round(-P_stc * _mo["perdida_iam_kWh_m2"], 0),
            "Nota":      f"ASHRAE b₀ · equivalente a \"IAM factor on global\" de PVsyst · factor medio {_mo.get('f_iam_prom', '—')}",
        })
        filas.append({
            "Etapa":     "①b Pérdida soiling  (suciedad)",
            "kWh":       round(ref_post_soil, 0),
            "Δ kWh":     round(-P_stc * _mo["perdida_soil_kWh_m2"], 0),
            "Nota":      f"Calendario Colombia · equivalente a \"Soiling loss factor\" de PVsyst · factor medio {_mo.get('f_soil_prom', '—')}",
        })
        # A partir de aquí, la referencia de "② Efecto SDM" es la POA YA
        # corregida por IAM+soiling -- si se siguiera comparando contra la
        # bruta, esas dos pérdidas se contarían dos veces (una aquí arriba,
        # otra de nuevo escondidas dentro del delta de SDM).
        ref_sdm = ref_post_soil
    else:
        ref_sdm = ref_dc

    delta_sdm = res["E_dc_anual_kWh"] - ref_sdm         # positivo = ganancia temperatura
    delta_t   = -res["perdida_temp_kWh"]                 # horas T > 25 °C (siempre ≤ 0)
    delta_inv = -res["perdida_inv_kWh"]                  # pérdida inversor (siempre ≤ 0)

    def _signo(v):
        return f"+{v:,.0f}" if v >= 0 else f"{v:,.0f}"

    filas += [
        {
            "Etapa":     "② Efecto SDM  (T° + baja irradiancia)",
            "kWh":       round(res["E_dc_anual_kWh"], 0),
            "Δ kWh":     round(delta_sdm, 0),
            "Nota":      ("🟢 Ganancia por T_cel < 25°C (clima frío / alta altitud)"
                          if delta_sdm >= 0
                          else "🔴 Pérdida óptica + temperatura") +
                         (" · combina \"irradiance level\" + \"temperature\" de PVsyst (no separables sin una segunda corrida SDM)"
                          if _tiene_cascada_optica else ""),
        },
        {
            # Fila informativa: desglosa la componente térmica pura del efecto SDM de fila ②
            # NO es un paso acumulado — la kWh muestra E_dc (mismo que fila ②)
            "Etapa":     "   ↳ Componente T° horas calientes  (T_cel > 25°C)",
            "kWh":       round(res["E_dc_anual_kWh"], 0),
            "Δ kWh":     round(delta_t, 0),
            "Nota":      f"Sub-componente de ②  ·  Tk_gamma={res.get('Tk_gamma_pct','—')}%/°C",
        },
        {
            "Etapa":     "③ E_dc  (salida del array)",
            "kWh":       round(res["E_dc_anual_kWh"], 0),
            "Δ kWh":     0,
            "Nota":      "",
        },
        {
            "Etapa":     "④ Pérdida inversor (eficiencia)",
            "kWh":       round(res.get("E_ac_sin_recorte_kWh", res["E_ac_anual_kWh"]), 0),
            "Δ kWh":     round(delta_inv, 0),
            "Nota":      f"η_inv = {round(res.get('E_ac_sin_recorte_kWh', res['E_ac_anual_kWh']) / res['E_dc_anual_kWh'] * 100, 1) if res['E_dc_anual_kWh'] > 0 else '—'}%",
        },
        {
            "Etapa":     "④b Recorte inversor (Pnom, clipping)",
            "kWh":       round(res["E_ac_anual_kWh"], 0),
            "Δ kWh":     round(-res.get("perdida_clipping_kWh", 0.0), 0),
            "Nota":      (
                f"{res.get('horas_con_clipping', 0):,} h/año recortadas"
                if res.get("perdida_clipping_kWh", 0.0) > 0
                else "Sin recorte -- DC/AC dentro del rango del inversor"
            ),
        },
        {
            "Etapa":     "⑤ E_ac  (energía a la red / edificio)",
            "kWh":       round(res["E_ac_anual_kWh"], 0),
            "Δ kWh":     0,
            "Nota":      "",
        },
    ]
    df = pd.DataFrame(filas)
    df["% de E_ref"] = (df["Δ kWh"].abs() / ref_dc * 100).round(2)
    return df
