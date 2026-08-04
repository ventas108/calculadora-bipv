"""
Strings de distinta orientación compartiendo un mismo MPPT — curva IV combinada.

Física del problema (#157):
  Cuando dos o más strings con orientaciones distintas se conectan en PARALELO a la
  misma entrada MPPT, el inversor impone UN solo voltaje de operación para todos.
  La corriente total a ese voltaje es la suma de las corrientes de cada string
  (I_total(V) = Σ I_s(V)), y el MPPT encuentra el máximo de P(V) = V × I_total(V)
  de la curva AGREGADA — que en general es MENOR que la suma de los Pmp individuales
  (cada string querría operar a un Vmp distinto según su irradiancia y temperatura).

  La pérdida por mismatch de MPPT compartido es:
      L = 1 − Pmp_combinada / Σ Pmp_independientes

Modelo:
  • Cada string se modela con el SDM De Soto 2006 calibrado del panel (Motor IV),
    con Rsh exponencial CdTe (Mermoud 2005) — idéntico a calculos.produccion_iv.
  • Escalado módulo → string (N_serie módulos iguales en serie):
        V ×N_serie  ⇒  R_s×N, R_sh×N, nNsVth×N   (I_L, I_o iguales)
  • Escalado string → grupo (N_paralelo strings idénticos en paralelo):
        I ×N_paralelo ⇒ I_L×Np, I_o×Np, R_s/Np, R_sh/Np  (nNsVth igual)
  • Se asume diodo de bloqueo ideal por string: un string no absorbe corriente
    inversa cuando el voltaje del bus supera su Voc (I se recorta a ≥ 0).
  • Vectorizado: las 8760 h se resuelven con arrays (H × n_puntos) vía
    pvlib.pvsystem.i_from_v (Lambert-W), sin bucles hora a hora.

Para que la comparación sea justa, la Pmp "independiente" de cada grupo se evalúa
sobre la MISMA malla de voltaje (misma resolución y misma ventana MPPT si se da).
"""

import numpy as np
import pandas as pd
import pvlib

from calculos.modelo_iv import (
    obtener_constantes_tecnologia,
    tiene_sdm_completo,
    K_BOLTZMANN,
    Q_ELECTRON,
    T_REF_K,
    G_REF,
)

G_MIN_WM2 = 5.0          # por debajo no hay producción (igual que produccion_iv)
N_PUNTOS_DEFAULT = 120   # puntos de la malla de voltaje por hora


def _params_grupo(G, T_cel, panel: dict, n_serie: int, n_paralelo: int):
    """
    Parámetros SDM equivalentes del GRUPO (N_serie en serie × N_paralelo en paralelo)
    hora a hora. Retorna (I_L, I_o, R_s, R_sh, nNsVth) como arrays (H,).
    """
    G     = np.asarray(G, dtype=float)
    T_cel = np.asarray(T_cel, dtype=float)
    if n_serie < 1 or n_paralelo < 1:
        raise ValueError("N_serie y N_paralelo deben ser >= 1.")

    constantes = obtener_constantes_tecnologia(panel["tecnologia"])
    Vt_ref     = K_BOLTZMANN * T_REF_K / Q_ELECTRON
    nNsVth_ref = panel["a_ref"] * Vt_ref

    # Rsh exponencial CdTe (Mermoud 2005) a nivel de módulo
    G_safe = np.where(G > 0, G, 1.0)
    R_sh_mod = (panel["R_sh_ref"] * np.exp(-constantes["c_Rsh"] * (G_safe / G_REF - 1.0))
                + panel.get("R_sh_base", 0.0))

    _Isc_stc = float(panel.get("Isc_stc") or panel.get("Isc") or 1.0)
    alpha_sc = panel["Tk_alfa"] / 100.0 * _Isc_stc

    I_L, I_o, R_s_mod, _rsh_pvlib, nNsVth = pvlib.pvsystem.calcparams_desoto(
        effective_irradiance = G,
        temp_cell            = T_cel,
        alpha_sc             = alpha_sc,
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

    ns, npar = float(n_serie), float(n_paralelo)
    I_L_g    = np.asarray(I_L, dtype=float) * npar
    I_o_g    = np.asarray(I_o, dtype=float) * npar
    R_s_g    = np.asarray(R_s_mod, dtype=float) * ns / npar
    R_sh_g   = np.asarray(R_sh_mod, dtype=float) * ns / npar
    nNsVth_g = np.asarray(nNsVth, dtype=float) * ns
    return I_L_g, I_o_g, R_s_g, R_sh_g, nNsVth_g


def _voc_grupo(I_L, I_o, R_sh, nNsVth):
    """Voc (V) del grupo hora a hora (0 donde no hay fotocorriente)."""
    con_luz = I_L > 1e-9
    voc = np.zeros_like(I_L)
    if np.any(con_luz):
        voc_l = pvlib.pvsystem.v_from_i(
            current            = 0.0,
            photocurrent       = I_L[con_luz],
            saturation_current = I_o[con_luz],
            resistance_series  = 0.0,          # sin corriente, Rs no afecta Voc
            resistance_shunt   = R_sh[con_luz],
            nNsVth             = nNsVth[con_luz],
            method             = 'lambertw',
        )
        voc[con_luz] = np.maximum(np.asarray(voc_l, dtype=float), 0.0)
    return voc


def simular_mppt_compartido(
    grupos: list,
    n_puntos: int = N_PUNTOS_DEFAULT,
    v_mppt_min: float | None = None,
    v_mppt_max: float | None = None,
) -> dict:
    """
    Simula 8760 h de varios grupos de strings (uno por orientación) compartiendo
    un mismo MPPT, resolviendo la curva IV combinada hora a hora.

    grupos : lista de dicts con keys:
        nombre      : etiqueta (p.ej. nombre de la superficie)
        G           : array (H,) irradiancia efectiva en el plano del grupo (W/m²)
        T_cel       : array (H,) temperatura de celda (°C)
        panel       : dict del catálogo con ficha SDM completa
        n_serie     : módulos en serie por string
        n_paralelo  : strings idénticos en paralelo de ese grupo

    v_mppt_min / v_mppt_max : ventana de voltaje del MPPT (V). Si se dan, tanto la
        Pmp combinada como las independientes se evalúan SOLO dentro de la ventana
        (comparación simétrica).

    Retorna dict:
        p_dc_comb_W    : array (H,) potencia DC del MPPT con curva combinada
        p_dc_indep_W   : array (H,) suma de Pmp independientes (MPPT ideal por grupo)
        e_dc_comb_kWh, e_dc_indep_kWh, perdida_kWh, perdida_pct
        desglose       : lista por grupo {nombre, e_dc_indep_kWh, n_serie, n_paralelo}
        peor_hora      : dict {idx, V, I_grupos, I_total, p_comb_W, p_indep_W,
                               nombres} — curva de la hora con mayor pérdida absoluta
        horas_con_perdida : nº de horas con pérdida relativa > 0.5%
    """
    if len(grupos) < 1:
        raise ValueError("Se requiere al menos un grupo de strings.")
    for g in grupos:
        if not tiene_sdm_completo(g["panel"]):
            raise ValueError(
                f"El panel del grupo '{g.get('nombre','?')}' no tiene ficha SDM completa."
            )
    H = len(np.asarray(grupos[0]["G"]))
    for g in grupos:
        if len(np.asarray(g["G"])) != H or len(np.asarray(g["T_cel"])) != H:
            raise ValueError("Todos los grupos deben tener arrays G/T_cel del mismo largo.")
    if v_mppt_min is not None and v_mppt_max is not None and v_mppt_max <= v_mppt_min:
        raise ValueError("v_mppt_max debe ser mayor que v_mppt_min.")

    # ── Parámetros y Voc por grupo ────────────────────────────────────────────
    params, vocs = [], []
    for g in grupos:
        p = _params_grupo(g["G"], g["T_cel"], g["panel"],
                          int(g["n_serie"]), int(g["n_paralelo"]))
        params.append(p)
        vocs.append(_voc_grupo(p[0], p[1], p[3], p[4]))

    voc_max = np.max(np.stack(vocs, axis=0), axis=0)          # (H,)
    hay_luz = voc_max > 1e-6

    # ── Malla de voltaje por hora: (H, P) ─────────────────────────────────────
    v_lo = 0.0 if v_mppt_min is None else float(v_mppt_min)
    frac = np.linspace(0.0, 1.0, n_puntos)                    # (P,)
    v_hi = voc_max.copy()
    if v_mppt_max is not None:
        v_hi = np.minimum(v_hi, float(v_mppt_max))
    v_hi = np.maximum(v_hi, v_lo)                             # ventana degenerada → punto
    V = v_lo + (v_hi - v_lo)[:, None] * frac[None, :]         # (H, P)

    # ── Corriente de cada grupo sobre la malla común ──────────────────────────
    I_total  = np.zeros_like(V)
    p_indep  = np.zeros(H)
    e_indep_por_grupo = []
    I_por_grupo = []
    for (I_L, I_o, R_s, R_sh, nNsVth), voc_g, g in zip(params, vocs, grupos):
        I_g = np.zeros_like(V)
        if np.any(hay_luz):
            idx = np.where(hay_luz)[0]
            I_calc = pvlib.pvsystem.i_from_v(
                voltage            = V[idx, :],
                photocurrent       = I_L[idx, None],
                saturation_current = I_o[idx, None],
                resistance_series  = R_s[idx, None],
                resistance_shunt   = R_sh[idx, None],
                nNsVth             = nNsVth[idx, None],
                method             = 'lambertw',
            )
            # Diodo de bloqueo ideal: el string no absorbe corriente inversa
            I_g[idx, :] = np.clip(np.asarray(I_calc, dtype=float), 0.0, None)
        I_por_grupo.append(I_g)
        I_total += I_g
        # Pmp independiente del grupo sobre la MISMA malla (comparación simétrica)
        p_g = np.max(V * I_g, axis=1)
        p_g = np.where(np.asarray(g["G"], dtype=float) < G_MIN_WM2, 0.0, p_g)
        p_indep += p_g
        e_indep_por_grupo.append(float(p_g.sum()) / 1000.0)

    # ── Pmp de la curva combinada ─────────────────────────────────────────────
    P_comb = V * I_total                                      # (H, P)
    p_comb = np.max(P_comb, axis=1)                           # (H,)
    G_all_min = np.max(np.stack([np.asarray(g["G"], dtype=float) for g in grupos]), axis=0)
    p_comb = np.where(G_all_min < G_MIN_WM2, 0.0, p_comb)
    p_comb = np.minimum(p_comb, p_indep)                      # seguridad numérica

    e_comb  = float(p_comb.sum()) / 1000.0
    e_ind   = float(p_indep.sum()) / 1000.0
    perdida = e_ind - e_comb
    perdida_pct = perdida / e_ind * 100.0 if e_ind > 0 else 0.0

    # Horas con pérdida relativa apreciable (>0.5%)
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = np.where(p_indep > 0, (p_indep - p_comb) / p_indep, 0.0)
    horas_perdida = int(np.sum(rel > 0.005))

    # ── Snapshot de la peor hora (para graficar la curva combinada) ──────────
    h_peor = int(np.argmax(p_indep - p_comb))
    peor_hora = {
        "idx":        h_peor,
        "V":          V[h_peor, :].copy(),
        "I_grupos":   [I_g[h_peor, :].copy() for I_g in I_por_grupo],
        "I_total":    I_total[h_peor, :].copy(),
        "p_comb_W":   float(p_comb[h_peor]),
        "p_indep_W":  float(p_indep[h_peor]),
        "nombres":    [g.get("nombre", f"Grupo {i+1}") for i, g in enumerate(grupos)],
    }

    return {
        "p_dc_comb_W":       p_comb,
        "p_dc_indep_W":      p_indep,
        "e_dc_comb_kWh":     round(e_comb, 1),
        "e_dc_indep_kWh":    round(e_ind, 1),
        "perdida_kWh":       round(perdida, 1),
        "perdida_pct":       round(perdida_pct, 2),
        "horas_con_perdida": horas_perdida,
        "desglose": [
            {"nombre": g.get("nombre", f"Grupo {i+1}"),
             "e_dc_indep_kWh": round(e_indep_por_grupo[i], 1),
             "n_serie": int(g["n_serie"]), "n_paralelo": int(g["n_paralelo"])}
            for i, g in enumerate(grupos)
        ],
        "peor_hora": peor_hora,
        "metodo": "curva_iv_combinada_mppt",
    }


def simular_mppts_proyecto(asignaciones: dict, grupos_por_nombre: dict,
                           n_puntos: int = N_PUNTOS_DEFAULT) -> dict:
    """
    Ejecuta simular_mppt_compartido por cada MPPT del proyecto.

    asignaciones      : {mppt_id(int): [nombre_grupo, ...]}
    grupos_por_nombre : {nombre_grupo: dict grupo (ver simular_mppt_compartido)}

    Retorna dict:
        por_mppt      : {mppt_id: resultado de simular_mppt_compartido}
        e_dc_comb_kWh, e_dc_indep_kWh, perdida_kWh, perdida_pct (totales del sistema)
    """
    por_mppt, e_comb, e_ind = {}, 0.0, 0.0
    for mppt_id, nombres in asignaciones.items():
        gs = [grupos_por_nombre[n] for n in nombres if n in grupos_por_nombre]
        if not gs:
            continue
        r = simular_mppt_compartido(gs, n_puntos=n_puntos)
        por_mppt[mppt_id] = r
        e_comb += r["e_dc_comb_kWh"]
        e_ind  += r["e_dc_indep_kWh"]
    perdida = e_ind - e_comb
    return {
        "por_mppt":        por_mppt,
        "e_dc_comb_kWh":   round(e_comb, 1),
        "e_dc_indep_kWh":  round(e_ind, 1),
        "perdida_kWh":     round(perdida, 1),
        "perdida_pct":     round(perdida / e_ind * 100.0, 2) if e_ind > 0 else 0.0,
    }
