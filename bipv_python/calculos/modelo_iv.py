"""
Motor SDM — De Soto 2006 + Rsh exponencial CdTe (Mermoud 2005).
Equivalente Python de: Mod_ModeloDiodo + SimuladorIV_CdTe_v2 (VBA).

Validación numérica disponible en tests/test_validacion_vba.py:
  FF @ G=200 W/m² debe ser 76.28% ± 0.5% (hoja FF_vs_Irradiancia del XLSM)
"""
import numpy as np
import pvlib
from datos.tecnologias_bipv import CONSTANTES_TECNOLOGIA


# ── Constantes físicas ─────────────────────────────────────────────────────
K_BOLTZMANN = 1.380649e-23   # J/K
Q_ELECTRON  = 1.602176634e-19  # C
T_REF_K     = 298.15           # 25°C en Kelvin
G_REF       = 1000.0           # W/m² referencia STC


def obtener_constantes_tecnologia(tecnologia: str) -> dict:
    """
    Equivalente de ObtenerConstantesTecnologia (VBA).
    Lanza ValueError explícito en lugar del MsgBox silencioso del VBA.
    """
    tech = tecnologia.strip()
    if tech not in CONSTANTES_TECNOLOGIA:
        raise ValueError(
            f"Tecnología '{tech}' no reconocida. "
            f"Válidas: {list(CONSTANTES_TECNOLOGIA.keys())}"
        )
    return CONSTANTES_TECNOLOGIA[tech]


def calcular_rsh_cdte(G, R_sh_ref, c_Rsh=5.5, R_sh_base=0.0, G_ref=1000.0):
    """
    Rsh exponencial CdTe — Mermoud 2005.
    Equivalente al bloque interno de TrasladarParametrosGT (VBA).

    Rsh(G) = R_sh_ref × exp(−c_Rsh × (G/G_ref − 1)) + R_sh_base
    """
    G_arr  = np.atleast_1d(np.asarray(G, dtype=float))
    G_safe = np.where(G_arr > 0, G_arr, 1.0)
    rsh    = R_sh_ref * np.exp(-c_Rsh * (G_safe / G_ref - 1.0)) + R_sh_base
    return rsh.item() if rsh.size == 1 else rsh   # .item() compatible numpy 1.x y 2.x


def trasladar_parametros_gt(G, T_cel_C, panel: dict):
    """
    Equivalente Python de TrasladarParametrosGT (VBA, Mod_ModeloDiodo).
    Traduce los parámetros SDM de STC a condiciones reales (G, T_celda).

    Usa pvlib.calcparams_desoto() para I_L, I_o, nNsVth, R_s
    y reemplaza R_sh por el modelo exponencial CdTe de Mermoud 2005.
    """
    constantes = obtener_constantes_tecnologia(panel["tecnologia"])

    # nNsVth_ref en Voltios (pvlib espera Voltios, no adimensional)
    Vt_ref      = K_BOLTZMANN * T_REF_K / Q_ELECTRON   # 0.025693 V @ 25°C
    nNsVth_ref  = panel["a_ref"] * Vt_ref               # 154 × 0.025693 = 3.957 V

    # R_sh exponencial CdTe (Mermoud 2005) — reemplaza el lineal de pvlib
    R_sh_exp = calcular_rsh_cdte(
        G,
        panel["R_sh_ref"],
        c_Rsh     = constantes["c_Rsh"],
        R_sh_base = panel.get("R_sh_base", 0.0),
    )

    # pvlib.calcparams_desoto para I_L, I_o, R_s, nNsVth
    # alpha_sc: pvlib espera A/°C (no %/°C).
    # Conversión: Tk_alfa [%/°C] / 100 × Isc_stc [A] = A/°C
    _Isc_stc = float(panel.get("Isc_stc") or panel.get("Isc") or 1.0)
    _alpha_sc = panel["Tk_alfa"] / 100.0 * _Isc_stc

    I_L, I_o, R_s, _R_sh_pvlib, nNsVth = pvlib.pvsystem.calcparams_desoto(
        effective_irradiance = G,
        temp_cell            = T_cel_C,
        alpha_sc             = _alpha_sc,
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

    # Devuelve con Rsh exponencial CdTe en lugar del lineal de pvlib
    return I_L, I_o, R_s, R_sh_exp, nNsVth


def resolver_curva_iv(G, T_cel_C, panel: dict, n_puntos=100):
    """
    Equivalente Python de CurvaIV_CdTe (VBA, SimuladorIV_CdTe_v2).
    Retorna curva I-V completa + puntos clave (Voc, Isc, Vmp, Imp, Pmax, FF).
    """
    if G <= 0:
        return {"Voc": 0, "Isc": 0, "Vmp": 0, "Imp": 0, "Pmax": 0, "FF": 0,
                "V": None, "I": None}

    I_L, I_o, R_s, R_sh, nNsVth = trasladar_parametros_gt(G, T_cel_C, panel)

    resultado = pvlib.pvsystem.singlediode(
        photocurrent       = I_L,
        saturation_current = I_o,
        resistance_series  = R_s,
        resistance_shunt   = R_sh,
        nNsVth             = nNsVth,
        method             = 'lambertw',
    )

    Voc  = float(resultado['v_oc'])
    Isc  = float(resultado['i_sc'])
    Pmax = float(resultado['p_mp'])
    FF   = Pmax / (Voc * Isc) if (Voc * Isc) > 0 else 0.0

    # Generar curva I-V manualmente (pvlib >=0.9 elimino ivcurve_pnts)
    if n_puntos > 0 and Voc > 0:
        V_arr = np.linspace(0, Voc, n_puntos)
        I_arr = pvlib.pvsystem.i_from_v(
            resistance_shunt   = R_sh,
            resistance_series  = R_s,
            nNsVth             = nNsVth,
            voltage            = V_arr,
            saturation_current = I_o,
            photocurrent       = I_L,
            method             = 'lambertw',
        )
    else:
        V_arr = None
        I_arr = None

    return {
        "Voc":  Voc,
        "Isc":  Isc,
        "Vmp":  float(resultado['v_mp']),
        "Imp":  float(resultado['i_mp']),
        "Pmax": Pmax,
        "FF":   FF,
        "V":    V_arr,
        "I":    I_arr,
    }


def simular_iv_hora_a_hora(G_array, T_cel_array, panel: dict):
    """
    Equivalente de simular_iv_hora_a_hora() (plan maestro).
    Procesa arrays de G y T_celda hora a hora.
    Retorna DataFrame con Voc, Isc, Vmp, Imp, Pmax, FF por hora.
    """
    import pandas as pd
    registros = []
    for G, T in zip(G_array, T_cel_array):
        registros.append(resolver_curva_iv(float(G), float(T), panel, n_puntos=0))
    return pd.DataFrame(registros)


# ── Parámetros mínimos requeridos para el Motor SDM ───────────────────────────
_SDM_KEYS = ("I_L_ref", "I_o_ref", "R_s", "R_sh_ref", "a_ref", "Tk_alfa", "tecnologia")


def tiene_sdm_completo(panel: dict) -> bool:
    """True si el panel tiene todos los parámetros SDM calibrados y válidos."""
    return all(panel.get(k) not in (None, 0, "", "nan") for k in _SDM_KEYS)


def estimar_sdm_desde_ficha(panel: dict) -> "dict | None":
    """
    Estima parámetros SDM (De Soto 2006) a partir de datos básicos de ficha técnica.

    Requiere: Voc_stc, Isc_stc, Vmp_stc, Imp_stc, N_s o NsA, tecnologia.
    Opcional: Tk_beta (coef. Voc %/°C), Tk_gamma (coef. Pmax %/°C).

    Retorna dict compatible con resolver_curva_iv() o None si faltan datos.
    El dict incluye '_estimado': True para advertir al usuario.
    """
    from datos.tecnologias_bipv import CONSTANTES_TECNOLOGIA

    Voc = float(panel.get("Voc_stc") or panel.get("Voc") or 0)
    Isc = float(panel.get("Isc_stc") or panel.get("Isc") or 0)
    Vmp = float(panel.get("Vmp_stc") or panel.get("Vmp") or 0)
    Imp = float(panel.get("Imp_stc") or panel.get("Imp") or 0)
    N_s = panel.get("N_s")
    NsA = panel.get("NsA")

    if not all([Voc > 0, Isc > 0, Vmp > 0, Imp > 0]):
        return None

    # ── Normalizar tecnología ──────────────────────────────────────────────────
    tec_raw = str(panel.get("tecnologia", "")).strip().lower()
    _MAP = {
        "mono-si": "Mono-Si", "mono si": "Mono-Si", "monocrystalline": "Mono-Si",
        "monocristalino": "Mono-Si", "mono": "Mono-Si",
        "poli-si": "Poli-Si", "poly-si": "Poli-Si", "poly": "Poli-Si",
        "policristalino": "Poli-Si", "polycrystalline": "Poli-Si",
        "multicrystalline": "Poli-Si",
        "cdte": "CdTe", "cd te": "CdTe", "cadmium telluride": "CdTe",
    }
    tec_norm = _MAP.get(tec_raw, "Mono-Si")
    if tec_norm not in CONSTANTES_TECNOLOGIA:
        tec_norm = "Mono-Si"

    const  = CONSTANTES_TECNOLOGIA[tec_norm]
    EgRef  = const["Eg_ref"]
    dEgdT  = const["dEgdT"]
    Vt_ref = K_BOLTZMANN * T_REF_K / Q_ELECTRON    # 0.025693 V @ 25°C

    # ── a_ref = n × Ns × Vt ───────────────────────────────────────────────────
    if NsA:
        a_ref = float(NsA) * Vt_ref
        N_s_est = N_s or int(round(float(NsA) / const.get("n_mediana", 1.05)))
    elif N_s:
        n_typ = {"CdTe": 1.09, "Mono-Si": 1.05, "Poli-Si": 1.10}.get(tec_norm, 1.05)
        a_ref = n_typ * float(N_s) * Vt_ref
        N_s_est = int(N_s)
    else:
        N_s_est = max(int(round(Voc / 0.65)), 36)  # ≈ 0.65 V/cell c-Si
        n_typ = 1.05
        a_ref = n_typ * N_s_est * Vt_ref

    # ── Coeficientes de temperatura ────────────────────────────────────────────
    Tk_beta  = panel.get("Tk_beta")  or panel.get("CoefVoc_C") or panel.get("beta_oc")
    Tk_gamma = panel.get("Tk_gamma") or panel.get("gamma_mp")   or panel.get("beta_mp")
    Tk_alfa  = panel.get("Tk_alfa")  or panel.get("alpha_sc")

    # beta_voc en V/°C (pvlib necesita V/°C, no %/°C)
    if Tk_beta:
        beta_voc_V = float(Tk_beta) / 100.0 * Voc
    else:
        beta_pct = {"CdTe": -0.30, "Mono-Si": -0.37, "Poli-Si": -0.40}.get(tec_norm, -0.37)
        beta_voc_V = beta_pct / 100.0 * Voc

    # alpha_sc en A/°C
    if Tk_alfa:
        alpha_sc_A = float(Tk_alfa) / 100.0 * Isc
    else:
        alpha_pct = {"CdTe": 0.02, "Mono-Si": 0.05, "Poli-Si": 0.05}.get(tec_norm, 0.05)
        alpha_sc_A = alpha_pct / 100.0 * Isc

    # ── Estimación SDM con pvlib fit_desoto ────────────────────────────────────
    try:
        fit = pvlib.ivtools.sdm.fit_desoto(
            v_mp            = Vmp,
            i_mp            = Imp,
            v_oc            = Voc,
            i_sc            = Isc,
            alpha_sc        = alpha_sc_A,
            beta_voc        = beta_voc_V,
            cells_in_series = N_s_est,
            EgRef           = EgRef,
            dEgdT           = dEgdT,
            irrad_ref       = 1000.0,
            temp_ref        = 25.0,
        )
        I_L  = float(fit["I_L_ref"])
        I_o  = float(fit["I_o_ref"])
        R_s  = float(fit["R_s"])
        R_sh = float(fit["R_sh_ref"])
        _metodo = "fit_desoto"
    except Exception:
        # Fallback heurístico si la optimización falla
        I_L  = Isc * 1.001
        I_o  = Isc * np.exp(-Voc / a_ref) * 1e-3
        R_s  = (Voc - Vmp) / Imp * 0.20
        R_sh = Vmp / max(Isc - Imp, 1e-6) * 5.0
        _metodo = "heurístico"

    return {
        "nombre":     panel.get("nombre", "Panel"),
        "tecnologia": tec_norm,
        "I_L_ref":    I_L,
        "I_o_ref":    I_o,
        "R_s":        R_s,
        "R_sh_ref":   R_sh,
        "a_ref":      a_ref,
        "Tk_alfa":    float(Tk_alfa) if Tk_alfa else alpha_pct if "alpha_pct" in dir() else 0.05,
        "Tk_gamma":   float(Tk_gamma) if Tk_gamma else -0.40,
        "Voc_stc":    Voc,
        "Isc_stc":    Isc,
        "Pmax_stc":   Vmp * Imp,
        "R_sh_base":  0.0,
        "_estimado":  True,
        "_metodo":    _metodo,
        "_tec_norm":  tec_norm,
    }


def validar_sdm_vs_ficha(panel: dict, tolerancia_pct=5.0) -> dict:
    """
    Compara el SDM calibrado contra los valores STC de la ficha.
    Valores de referencia del XLSM (hoja FF_vs_Irradiancia, G=1000, T=25°C):
      Voc calculado  = 116.44 V  (ficha: 116.0 V  → error 0.38% ✓)
      Isc calculado  =   0.800 A  (ficha:   0.8 A  → error 0.00% ✓)
      Pmax calculado =  60.48 W  (ficha:  63.0 W  → error 3.97% ✓ <5%)
      FF calculado   =  64.92%   (VBA: 64.92% ✓)
    """
    res = resolver_curva_iv(1000.0, 25.0, panel, n_puntos=0)

    campos = {
        "Voc":  (res["Voc"],  panel["Voc_stc"]),
        "Isc":  (res["Isc"],  panel["Isc_stc"]),
        "Pmax": (res["Pmax"], panel["Pmax_stc"]),
    }
    resultado = {}
    todo_ok   = True
    for param, (calc, ref) in campos.items():
        err = abs(calc - ref) / ref * 100
        ok  = err <= tolerancia_pct
        if not ok:
            todo_ok = False
        resultado[param] = {
            "calculado": round(calc, 4),
            "referencia": ref,
            "error_pct": round(err, 2),
            "ok": ok,
        }
    resultado["validacion_ok"] = todo_ok
    return resultado
