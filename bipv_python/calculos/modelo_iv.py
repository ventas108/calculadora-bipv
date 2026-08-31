"""
Motor SDM — De Soto 2006 + Rsh exponencial CdTe (Mermoud 2005).
Equivalente Python de: Mod_ModeloDiodo + SimuladorIV_CdTe_v2 (VBA).

Validación numérica disponible en tests/test_validacion_vba.py:
  FF @ G=200 W/m² debe ser 76.28% ± 0.5% (hoja FF_vs_Irradiancia del XLSM)
"""
import numpy as np
import pvlib
from scipy.special import lambertw
from datos.tecnologias_bipv import CONSTANTES_TECNOLOGIA


# ── Constantes físicas ─────────────────────────────────────────────────────
K_BOLTZMANN = 1.380649e-23   # J/K
Q_ELECTRON  = 1.602176634e-19  # C
T_REF_K     = 298.15           # 25°C en Kelvin
G_REF       = 1000.0           # W/m² referencia STC


def _fit_desoto_batzelis_local(v_mp, i_mp, v_oc, i_sc, alpha_sc, beta_voc):
    """
    Reimplementación local, cerrada (Lambert W, sin iteración), del método
    Batzelis para estimar los 5 parámetros del SDM De Soto desde datos de
    ficha técnica -- mismas ecuaciones y mismo resultado (verificado
    bit-a-bit, dif=0.0 en 3 paneles reales) que
    `pvlib.ivtools.sdm.fit_desoto_batzelis()`.

    Reimplementada aquí (31-ago-2026) en vez de llamar directo a pvlib
    porque esa función SOLO existe en versiones de pvlib más nuevas que la
    fijada en requirements.txt (pvlib==0.11.1) -- usarla directamente pasaba
    los tests locales (con un pvlib más nuevo ya instalado en el entorno de
    desarrollo) pero fallaba en CI y en cualquier entorno que respetara el
    pin real (`AttributeError`, capturado en silencio por el except
    genérico de `estimar_sdm_desde_ficha()`, cayendo siempre al heurístico
    tosco sin que ningún test lo notara). Usa `scipy.special.lambertw`
    (ya fijado en requirements.txt) en vez del helper privado
    `pvlib.ivtools.utils._lambertw_pvlib` -- verificado que da el mismo
    valor (dif=0.0) para los rangos reales de esta app.

    Referencia: E. I. Batzelis, "Simple PV Performance Equations
    Theoretically Well Founded on the Single-Diode Model", IEEE J.
    Photovoltaics, vol. 7, no. 5, 2017.
    """
    alpha_sc_n = alpha_sc / i_sc
    beta_voc_n = beta_voc / v_oc
    t0 = 298.15  # K
    del0 = (1 - beta_voc_n * t0) / (50.1 - alpha_sc_n * t0)
    w0 = float(lambertw(np.exp(1.0 / del0 + 1.0)).real)
    a0 = del0 * v_oc
    Rs0 = (a0 * (w0 - 1) - v_mp) / i_mp
    Rsh0 = a0 * (w0 - 1) / (i_sc * (1 - 1 / w0) - i_mp)
    Iph0 = (1 + Rs0 / Rsh0) * i_sc
    Isat0 = Iph0 * np.exp(-1 / del0)
    return {
        "alpha_sc": alpha_sc_n * i_sc,
        "a_ref": a0,
        "I_L_ref": Iph0,
        "I_o_ref": Isat0,
        "R_sh_ref": Rsh0,
        "R_s": Rs0,
    }


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


def calcular_rsh_cdte(G, R_sh_ref, c_Rsh=5.5, R_sh_0=None, G_ref=1000.0):
    """
    Rsh exponencial SATURADO — Mermoud 2005 / PVsyst (mismo modelo que
    pvlib.pvsystem.calcparams_pvsyst / _pvsyst_Rsh).

    Rsh(G) = Rsh_base + (R_sh_0 − Rsh_base) × exp(−c_Rsh × G/G_ref)
    Rsh_base = (R_sh_ref − R_sh_0 × exp(−c_Rsh)) / (1 − exp(−c_Rsh))

    `R_sh_0` es la resistencia shunt a la que la curva SATURA a muy baja
    irradiancia (G→0) -- un valor FINITO, a diferencia de la fórmula
    anterior de un solo término (R_sh_ref × exp(−c_Rsh×(G/Gref−1))), que
    diverge sin límite cuando G→0 (a G=100 W/m² con c_Rsh=5.5 llegaba a
    ~245× R_sh_ref, un valor sin sentido físico que hacía que el Fill
    Factor subiera de forma anómala a baja irradiancia en vez de seguir
    la curva real "en joroba" documentada para capa delgada (Batzner et
    al. 2001): sube desde ~100 W/m², hace pico ~150-200 W/m², y BAJA de
    nuevo hacia irradiancias más altas.

    La corrección Rsh_base ancla la curva para que Rsh(G_ref) = R_sh_ref
    EXACTO sin importar R_sh_0/c_Rsh (necesario: R_sh_ref ya está
    calibrado contra la ficha técnica en STC, ver validar_sdm_vs_ficha()).

    Si `R_sh_0` no se especifica (panel sin calibración propia contra una
    referencia real), cae al comportamiento de la fórmula anterior
    (R_sh_0 = R_sh_ref × exp(c_Rsh)) -- mismo resultado que antes de esta
    corrección, sin regresión, hasta que ese panel tenga su propia
    referencia para calibrar un R_sh_0 real.
    """
    G_era_escalar = np.ndim(G) == 0   # bool/int/float puros, no arrays de 1 elemento
    G_arr  = np.atleast_1d(np.asarray(G, dtype=float))
    G_safe = np.where(G_arr > 0, G_arr, 1.0)
    if R_sh_0 is None:
        R_sh_0 = R_sh_ref * np.exp(c_Rsh)
    exp_c   = np.exp(-c_Rsh)
    rsh_base = (R_sh_ref - R_sh_0 * exp_c) / (1.0 - exp_c)
    rsh_base = max(rsh_base, 0.0)   # nunca negativo (ver pvlib._pvsyst_Rsh)
    rsh = rsh_base + (R_sh_0 - rsh_base) * np.exp(-c_Rsh * G_safe / G_ref)
    # Solo colapsa a escalar si el LLAMADOR pasó un escalar -- un array de un
    # solo elemento (G=np.array([100.0]), típico de código vectorizado con
    # H=1 hora) debe seguir devolviendo un array de 1 elemento, no un float
    # suelto, para no romper el contrato de forma de quien lo llama
    # (ver test_consistencia_sdm_entre_modulos.py, que atrapó exactamente
    # esta inconsistencia en mppt_combinado._params_grupo()).
    return rsh.item() if G_era_escalar else rsh


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

    # R_sh exponencial saturado (Mermoud 2005 / PVsyst) — reemplaza el lineal de pvlib
    R_sh_exp = calcular_rsh_cdte(
        G,
        panel["R_sh_ref"],
        c_Rsh  = constantes["c_Rsh"],
        R_sh_0 = panel.get("R_sh_0"),   # None → sin regresión si el panel no está calibrado
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


def resolver_panel_calibrado(panel: dict) -> dict:
    """
    Devuelve la versión calibrada canónica cuando el nombre del panel existe
    también en el catálogo interno auditado.

    El catálogo Excel puede contener la ficha comercial del mismo modelo sin
    los parámetros SDM calibrados, o con Ns/NsA curados de otra fuente. En ese
    caso no se deben mezclar silenciosamente ambas parametrizaciones: el SDM
    calibrado es la fuente eléctrica común para Motor IV y Producción.
    """
    nombre = str(panel.get("nombre", "")).strip()
    if not nombre:
        return panel

    # Import local para evitar acoplar la carga del catálogo interno al módulo.
    from datos.tecnologias_bipv import MODULOS_BIPV

    calibrado = MODULOS_BIPV.get(nombre)
    if not calibrado or not tiene_sdm_completo(calibrado):
        return panel

    # Preservar metadatos comerciales del catálogo seleccionado, pero nunca
    # sobrescribir parámetros eléctricos ni térmicos del modelo auditado.
    # En particular, NOCT puede ser un valor estimado en el Excel.
    metadatos = (
        "marca", "fabricante", "costo_usd", "area_m2", "dimensiones_mm",
        "transparencia_pct", "bifacialidad_pct", "notas",
        "confianza", "fuente_NsA",
    )
    resultado = dict(calibrado)
    for clave in metadatos:
        valor = panel.get(clave)
        if valor not in (None, "", "nan"):
            resultado[clave] = valor
    resultado["_sdm_calibrado_canonico"] = True
    return resultado


# ── Rangos Voc/celda @ STC esperados por tecnología (V/celda) ─────────────────
_VOC_POR_CELDA_RANGO = {
    "Mono-Si":  (0.55, 0.76),
    "Poli-Si":  (0.52, 0.70),
    "CdTe":     (0.76, 1.20),
    "CIGS":     (0.52, 0.80),
    "a-Si":     (0.58, 0.90),
}
_VOC_POR_CELDA_DEFAULT = (0.48, 1.25)

# Palabras clave que indican panel half-cut en el nombre del modelo
_HALFCUT_KEYWORDS = ("half-cut", "half cut", "halfcut", "half_cut", " hc ", "-hc-", "-hc ")


def verificar_ns_halfcut(panel: dict) -> "dict | None":
    """
    Detecta si N_s en el catálogo es incorrecto para paneles half-cut.

    Los paneles half-cut tienen las celdas cortadas a la mitad. Algunos fabricantes
    listan N_s como el número TOTAL de semiceldas (p.ej. 144), cuando el modelo SDM
    De Soto necesita el número de celdas EQUIVALENTES en serie desde el punto de vista
    eléctrico (p.ej. 72 para una string de 72 semiceldas).

    Heurística: calcula Voc / N_s y lo compara con el rango típico por tecnología.
    - Si Voc/N_s < rango_min × 0.65  → N_s está duplicado  → N_s_sugerido = N_s // 2
    - Si Voc/N_s > rango_max × 1.40  → N_s está a la mitad → N_s_sugerido = N_s × 2

    Retorna None si no hay problema evidente, o dict con:
        tipo              str   "ns_duplicado" | "ns_mitad"
        Voc_por_celda     float Voc / N_s calculado
        rango_esperado    tuple (min, max) para la tecnología
        N_s_ingresado     int   valor en catálogo
        N_s_sugerido      int   valor corregido recomendado
        es_halfcut_nombre bool  True si el nombre del modelo contiene indicadores
        tecnologia        str   tecnología normalizada usada
        mensaje           str   texto para mostrar al usuario
    """
    Voc = float(panel.get("Voc_stc") or panel.get("Voc") or 0)
    N_s = panel.get("N_s")
    if not (Voc > 10 and N_s and float(N_s) > 0):
        return None   # sin datos suficientes para verificar

    N_s_f = float(N_s)
    voc_per_cell = Voc / N_s_f

    # Normalizar tecnología
    tec_raw = str(panel.get("tecnologia", "")).strip().lower()
    _MAP = {
        "mono-si": "Mono-Si", "mono si": "Mono-Si", "monocrystalline": "Mono-Si",
        "monocristalino": "Mono-Si", "mono": "Mono-Si",
        "poli-si": "Poli-Si", "poly-si": "Poli-Si", "policristalino": "Poli-Si",
        "multicrystalline": "Poli-Si", "poly": "Poli-Si",
        "cdte": "CdTe", "cd te": "CdTe",
        "cigs": "CIGS", "cis": "CIGS",
        "a-si": "a-Si", "asi": "a-Si", "amorphous": "a-Si",
    }
    tec_norm = _MAP.get(tec_raw, "")
    rango = _VOC_POR_CELDA_RANGO.get(tec_norm, _VOC_POR_CELDA_DEFAULT)
    r_min, r_max = rango

    # Detectar indicadores half-cut en el nombre del modelo
    nombre_lower = str(panel.get("nombre", "")).lower()
    es_halfcut_nombre = any(kw in nombre_lower for kw in _HALFCUT_KEYWORDS)

    tipo = None
    N_s_sug = int(N_s_f)

    if voc_per_cell < r_min * 0.65:
        tipo     = "ns_duplicado"
        N_s_sug  = max(1, int(round(N_s_f / 2)))
    elif voc_per_cell > r_max * 1.40:
        tipo     = "ns_mitad"
        N_s_sug  = int(round(N_s_f * 2))

    if tipo is None and not es_halfcut_nombre:
        return None   # todo dentro del rango y sin indicadores en el nombre

    if tipo is None:
        # Nombre indica half-cut pero el voltaje parece correcto — solo informar
        return {
            "tipo":              "nombre_halfcut_ok",
            "Voc_por_celda":     round(voc_per_cell, 4),
            "rango_esperado":    rango,
            "N_s_ingresado":     int(N_s_f),
            "N_s_sugerido":      int(N_s_f),
            "es_halfcut_nombre": True,
            "tecnologia":        tec_norm or tec_raw,
            "mensaje": (
                f"El nombre del panel sugiere diseño **half-cut** y N_s={int(N_s_f)} "
                f"da Voc/celda = {voc_per_cell:.3f} V — dentro del rango esperado "
                f"({r_min:.2f}–{r_max:.2f} V). N_s parece correcto."
            ),
        }

    _desc = {
        "ns_duplicado": (
            f"N_s={int(N_s_f)} parece el conteo de **semiceldas** (half-cut). "
            f"El SDM De Soto necesita el conteo de **celdas equivalentes en serie** "
            f"= N_s // 2 = **{N_s_sug}**."
        ),
        "ns_mitad": (
            f"N_s={int(N_s_f)} parece demasiado bajo para Voc={Voc:.1f} V. "
            f"El valor sugerido es **{N_s_sug}**."
        ),
    }

    return {
        "tipo":              tipo,
        "Voc_por_celda":     round(voc_per_cell, 4),
        "rango_esperado":    rango,
        "N_s_ingresado":     int(N_s_f),
        "N_s_sugerido":      N_s_sug,
        "es_halfcut_nombre": es_halfcut_nombre,
        "tecnologia":        tec_norm or tec_raw,
        "mensaje":           _desc[tipo],
    }


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
    _ns_corregido     = False
    _ns_original      = None
    _ns_halfcut_info  = None

    n_typ = {"CdTe": 1.09, "Mono-Si": 1.05, "Poli-Si": 1.10}.get(tec_norm, 1.05)
    if NsA:
        # ── #67: el camino NsA TAMBIÉN se verifica contra half-cut ──────────
        # NsA = n × Ns viene del mismo catálogo/ficha: si el Ns registrado es
        # el total de semiceldas (p.ej. 144 en vez de 72), NsA arrastra el
        # mismo doble conteo y duplicaría a_ref (Voc del modelo se dispara).
        # Derivar celdas con la n MEDIANA de la tecnología (igual que antes de
        # #67): para CIGS n_mediana=1.35 ≠ n_typ 1.05 y usar la equivocada
        # clasificaría mal paneles legítimos.
        _n_med = const.get("n_mediana", n_typ)
        _N_s_deriv = N_s or int(round(float(NsA) / _n_med))
        _panel_chk = dict(panel)
        _panel_chk["N_s"] = _N_s_deriv
        _hc = verificar_ns_halfcut(_panel_chk)
        if _hc and _hc["tipo"] == "ns_duplicado":
            _ns_original     = int(_N_s_deriv)
            N_s_est          = _hc["N_s_sugerido"]
            _ns_corregido    = True
            _ns_halfcut_info = _hc
            # NsA heredó el doble conteo → recomputar desde el Ns corregido
            # con la misma n que se usó para derivar (coherencia a_ref/celdas)
            a_ref = _n_med * N_s_est * Vt_ref
        else:
            a_ref = float(NsA) * Vt_ref
            N_s_est = _N_s_deriv
    elif N_s:
        n_typ = {"CdTe": 1.09, "Mono-Si": 1.05, "Poli-Si": 1.10}.get(tec_norm, 1.05)
        # ── Verificar si N_s es incorrecto por half-cut (tarea #67) ──────────
        _hc = verificar_ns_halfcut(panel)
        if _hc and _hc["tipo"] == "ns_duplicado":
            _ns_original     = int(float(N_s))
            N_s_est          = _hc["N_s_sugerido"]
            _ns_corregido    = True
            _ns_halfcut_info = _hc
        else:
            N_s_est = int(N_s)
        a_ref = n_typ * N_s_est * Vt_ref
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
    # Cascada de 3 métodos, del más riguroso al más tosco (30-ago-2026,
    # investigación pedida por el usuario: "investiga por qué falla
    # fit_desoto para paneles reales"):
    #
    # 1. fit_desoto() -- el método iterativo (Newton/MINPACK 'hybr', sin
    #    escalar) que ya se usaba. Auditado: falla de forma REPRODUCIBLE
    #    (no es ruido aleatorio -- mismos parámetros de entrada, mismo
    #    resultado en corridas repetidas) para el panel real de Urabá y,
    #    según la auditoría del catálogo completo, para la enorme mayoría
    #    de los 76 paneles reales. Causa: los 5 parámetros del SDM abarcan
    #    magnitudes muy distintas (I_o ~1e-14, I_L ~10-20, Rsh ~100-1000),
    #    y el jacobiano por diferencias finitas de un solver sin escalar
    #    es numéricamente frágil para esa combinación -- una debilidad ya
    #    documentada del método clásico con módulos modernos de alta
    #    corriente/muchas celdas, no un bug de esta app.
    # 2. fit_desoto_batzelis() -- método CERRADO (Lambert W, sin iteración,
    #    no puede fallar por no-convergencia) del mismo pvlib. Probado
    #    contra los 76 paneles reales del catálogo: reproduce Voc/Vmp/Pmax
    #    de la ficha STC dentro del margen de validación del 5% en 71 de
    #    74 casos evaluables (vs. 0 de 76 con fit_desoto solo) -- respaldo
    #    mucho mejor que el heurístico anterior, que llegó a dar Voc con
    #    96% de error para el panel real de Urabá.
    # 3. Heurístico (el que ya existía) -- último recurso si ambos fallan.
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
        try:
            # Método cerrado -- sus 5 parámetros son mutuamente consistentes
            # entre sí (resueltos juntos por las mismas ecuaciones), así que
            # se usa también su propio a_ref en vez del heurístico n×Ns×Vt de
            # arriba (que no fue derivado junto con I_L/I_o/Rs/Rsh de Batzelis
            # y rompería esa consistencia interna).
            fit_b = _fit_desoto_batzelis_local(
                v_mp=Vmp, i_mp=Imp, v_oc=Voc, i_sc=Isc,
                alpha_sc=alpha_sc_A, beta_voc=beta_voc_V,
            )
            I_L   = float(fit_b["I_L_ref"])
            I_o   = float(fit_b["I_o_ref"])
            R_s   = float(fit_b["R_s"])
            R_sh  = float(fit_b["R_sh_ref"])
            a_ref = float(fit_b["a_ref"])
            _metodo = "fit_desoto_batzelis"
        except Exception:
            # Fallback heurístico si ambos ajustes fallan
            I_L  = Isc * 1.001
            I_o  = Isc * np.exp(-Voc / a_ref) * 1e-3
            R_s  = (Voc - Vmp) / Imp * 0.20
            R_sh = Vmp / max(Isc - Imp, 1e-6) * 5.0
            _metodo = "heurístico"

    # Bug real, más grave que los métodos de ajuste en sí (30-ago-2026):
    # `a_ref` arriba está en VOLTIOS (convención nativa de pvlib -- así lo
    # devuelven fit_desoto()/fit_desoto_batzelis(), y así lo necesita la
    # fórmula heurística de I_o unas líneas arriba, exp(-Voc/a_ref)). Pero
    # `trasladar_parametros_gt()` (más abajo en este mismo archivo) y
    # `calculos/produccion_iv.py::_pmp_iv_vectorizado()` esperan que
    # panel["a_ref"] venga en la convención UNITLESS (n × Ns) usada por el
    # único panel precalibrado a mano de esta app (ASP-ST1-T40 en
    # datos/tecnologias_bipv.py, a_ref=154.0) y multiplican por Vt_ref para
    # convertir a voltios ellos mismos -- devolver aquí el valor ya en
    # voltios lo convertía DOS VECES, encogiendo nNsVth ~39× (1/Vt_ref) y
    # colapsando Voc a ~1.3-1.6 V en vez de los ~40-50 V reales. Esto
    # afectaba a CUALQUIER panel estimado on-demand (fit_desoto, Batzelis o
    # heurístico) desde que esta función existe -- enmascarado hasta hoy
    # porque ningún panel real llegaba tan lejos (ver bug de Imp_stc y la
    # no-convergencia de fit_desoto, ambos corregidos/documentados arriba).
    a_ref_unitless = a_ref / Vt_ref

    return {
        "nombre":            panel.get("nombre", "Panel"),
        "tecnologia":        tec_norm,
        "I_L_ref":           I_L,
        "I_o_ref":           I_o,
        "R_s":               R_s,
        "R_sh_ref":          R_sh,
        "a_ref":             a_ref_unitless,
        "Tk_alfa":           float(Tk_alfa) if Tk_alfa else alpha_pct if "alpha_pct" in dir() else 0.05,
        "Tk_gamma":          float(Tk_gamma) if Tk_gamma else -0.40,
        "Voc_stc":           Voc,
        "Isc_stc":           Isc,
        "Pmax_stc":          Vmp * Imp,
        "R_sh_base":         0.0,
        "_estimado":         True,
        "_metodo":           _metodo,
        "_tec_norm":         tec_norm,
        # ── Corrección half-cut N_s (tarea #67) ──────────────────────────────
        "_ns_corregido":     _ns_corregido,
        "_ns_original":      _ns_original,
        "_N_s_usado":        N_s_est,
        "_ns_halfcut_info":  _ns_halfcut_info,
    }

def preparar_panel_iv(panel: dict) -> "dict | None":
    """
    Auto-activa el Motor IV para paneles del catálogo Excel.

    Lógica de cascada:
    1. Si el panel ya tiene SDM calibrado (I_L_ref, I_o_ref, R_s, R_sh_ref válidos)
       → devuelve el panel tal cual para usar directamente.
    2. Si el panel tiene NsA (o N_s) y datos básicos de ficha (Voc, Isc, Vmp, Imp)
       → llama estimar_sdm_desde_ficha() con fit_desoto() on-demand.
    3. Si faltan datos mínimos → devuelve None (solo cálculo energético).

    Retorna un dict compatible con resolver_curva_iv() o None.
    Los paneles del catálogo Excel con NsA disponible activan automáticamente
    el Motor IV sin necesidad de parámetros SDM precalibrados.
    """
    # Caso 0: el mismo modelo tiene una parametrización SDM calibrada auditada.
    # Debe resolverse antes de mirar la ficha básica del Excel para que todas
    # las páginas usen exactamente la misma curva IV.
    panel_canonico = resolver_panel_calibrado(panel)
    if panel_canonico is not panel:
        return panel_canonico

    # Caso 1: SDM ya calibrado en catálogo (ruta rápida)
    if tiene_sdm_completo(panel):
        return panel

    # Caso 2: tiene ficha básica + NsA/N_s → fit_desoto on-demand
    tiene_ficha = all([
        panel.get("Voc_stc") or panel.get("Voc"),
        panel.get("Isc_stc") or panel.get("Isc"),
        panel.get("Vmp_stc") or panel.get("Vmp"),
        (panel.get("Imp_stc") or panel.get("Imp")),
    ])
    tiene_ns = bool(panel.get("NsA") or panel.get("N_s"))

    if not (tiene_ficha and tiene_ns):
        return None  # Datos insuficientes → solo cálculo energético

    estimado = estimar_sdm_desde_ficha(panel)
    if estimado is None:
        return None

    # Nunca activar un SDM estimado que no reproduzca los puntos STC de ficha.
    # Esto evita que un Ns/NsA incompatible produzca una curva con escala de
    # tensión incorrecta y una energía anual aparentemente válida.
    prueba = {**panel, **estimado}
    try:
        validacion = validar_sdm_vs_ficha(prueba, tolerancia_pct=5.0)
    except (KeyError, TypeError, ValueError, FloatingPointError):
        return None
    if not validacion.get("validacion_ok", False):
        return None
    return estimado
def validar_sdm_vs_ficha(panel: dict, tolerancia_pct=5.0) -> dict:
    """
    Compara el SDM calibrado contra los valores STC de la ficha.
    Valores de referencia del XLSM (hoja FF_vs_Irradiancia, G=1000, T=25°C):
      Voc calculado  = 116.44 V  (ficha: 116.0 V  → error 0.38% ✓)
      Isc calculado  =   0.800 A  (ficha:   0.8 A  → error 0.00% ✓)
      Pmax calculado =  60.48 W  (ficha:  63.0 W  → error 3.97% ✓ <5%)
      FF calculado   =  64.92%   (VBA: 64.92% ✓)

    Incluye también Vmp e Imp (2026-08-21): resolver_curva_iv() ya los
    calcula, pero antes no se comparaban contra la ficha -- un punto ciego
    real, porque Voc/Isc/Pmax podían validar los tres mientras Vmp estaba
    mal calibrado, y Vmp es justo el valor que usan los chequeos de
    compatibilidad eléctrica (ventana MPPT) en
    calculos.dimensionamiento.calcular_vmp_string() y en los comparadores
    de paneles/inversores.
    """
    res = resolver_curva_iv(1000.0, 25.0, panel, n_puntos=0)

    # .get() con respaldo a la clave sin "_stc" -- bug real (30-ago-2026):
    # el subíndice directo panel["Imp_stc"] lanzaba KeyError para cualquier
    # panel cuya fuente no hubiera fijado ese alias exacto (encontrado con
    # datos/catalogo_paneles_excel.py, que omitía "Imp_stc" mientras sí
    # fijaba "Voc_stc"/"Vmp_stc"/"Isc_stc"). preparar_panel_iv() capturaba
    # ese KeyError y lo convertía en "datos insuficientes" (None) en
    # silencio -- bloqueaba el Motor IV on-demand para cualquier panel real
    # afectado, incluso cuando el ajuste SDM habría sido válido.
    campos = {
        "Voc":  (res["Voc"],  panel.get("Voc_stc")  or panel.get("Voc")),
        "Isc":  (res["Isc"],  panel.get("Isc_stc")  or panel.get("Isc")),
        "Vmp":  (res["Vmp"],  panel.get("Vmp_stc")  or panel.get("Vmp")),
        "Imp":  (res["Imp"],  panel.get("Imp_stc")  or panel.get("Imp")),
        "Pmax": (res["Pmax"], panel.get("Pmax_stc") or panel.get("Pmax")),
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


# ── Causa técnica típica por métrica cuando validar_sdm_vs_ficha() falla ──────
# No son certezas, son la explicación más probable dado cómo entra cada
# parámetro en el modelo de diodo -- ver el docstring de cada campo en
# datos/tecnologias_bipv.py::ASP_ST1_T40 para el rol exacto de cada uno.
_CAUSA_TECNICA_FALLO = {
    "Voc": (
        "el número de celdas en serie (N_s) o el parámetro a_ref (n×N_s) usado para "
        "calibrar el SDM no corresponde a la construcción real de este panel -- revisa "
        "'Ns (Celdas Serie)' y 'n (Factor Idealidad)' en la hoja Catalogo_Paneles_FV del "
        "Excel."
    ),
    "Isc": (
        "la fotocorriente calibrada (I_L_ref) no corresponde al área activa real del "
        "panel -- típico cuando se copiaron los parámetros SDM de OTRA variante de "
        "transparencia/potencia de la misma familia sin reescalar I_L_ref proporcional "
        "al Isc real de esta ficha específica."
    ),
    "Pmax": (
        "la potencia máxima calculada no reproduce la de placa. Si Voc e Isc SÍ "
        "validan pero Pmax no, el problema está en el Factor de Forma de la curva: "
        "revisa R_s (resistencia serie) y R_sh_ref (resistencia shunt), que determinan "
        "la forma de la curva I-V entre Voc e Isc sin afectar sus extremos."
    ),
    "Vmp": (
        "el punto de máxima potencia calculado no coincide con el de la ficha -- esto es "
        "crítico porque Vmp (no Voc) es el valor que usan los chequeos de compatibilidad "
        "eléctrica (ventana MPPT) para dimensionar el string. Si Voc SÍ valida pero Vmp "
        "no, revisa R_s y R_sh_ref: definen dónde cae la 'rodilla' de la curva entre Voc "
        "e Isc, y por lo tanto dónde queda el punto de máxima potencia."
    ),
    "Imp": (
        "la corriente en el punto de máxima potencia no coincide con la de la ficha -- "
        "si Isc SÍ valida pero Imp no, el Factor de Forma real del panel difiere del "
        "calibrado: revisa R_s y R_sh_ref junto con Vmp (ambos suelen fallar juntos, ya "
        "que Imp y Vmp describen el mismo punto de la curva)."
    ),
}


def explicar_fallo_validacion_sdm(panel_nombre: str, val: dict) -> str:
    """
    Texto técnico determinista (NO es una llamada a un agente de IA -- mismo
    principio que el resto de los avisos de la calculadora: directo, cita
    números exactos, sin costo ni latencia de API) que explica EN QUÉ
    métricas falla validar_sdm_vs_ficha() y qué revisar en el catálogo.

    Se muestra automáticamente en 📐 Dimensionamiento y 📊 Producción cuando
    la validación no pasa -- antes de esto, la única forma de enterarse era
    entrar manualmente a 🔬 Motor IV y presionar el botón de validación, sin
    ninguna alarma en el resto de la app.
    """
    fallos = [(p, d) for p, d in val.items() if p != "validacion_ok" and not d["ok"]]
    if not fallos:
        return (
            f"✅ {panel_nombre}: SDM validado -- Voc/Isc/Vmp/Imp/Pmax dentro de la tolerancia "
            "de error (5%) contra la ficha técnica."
        )

    n_total = len(val) - 1  # descuenta la clave "validacion_ok"
    lineas = [
        f"🔴 **{panel_nombre} — validación SDM vs ficha técnica: {len(fallos)} de "
        f"{n_total} métricas fuera de tolerancia (>5% de error).**",
        "",
        "Esto significa que los parámetros del modelo de diodo (I_L_ref, I_o_ref, R_s, "
        "R_sh_ref, a_ref) usados para simular este panel NO reproducen su comportamiento "
        "real a condiciones estándar (1000 W/m², 25°C). Todo cálculo de energía que use "
        "este panel (📊 Producción, 💰 Financiero, 🧩 Comparador de Paneles, 🔋 Baterías) "
        "hereda ese mismo desajuste.",
        "",
    ]
    for param, datos in fallos:
        lineas.append(
            f"- **{param}**: calculado={datos['calculado']} vs ficha={datos['referencia']} "
            f"→ error {datos['error_pct']}% (límite 5%). "
            + _CAUSA_TECNICA_FALLO.get(param, "revisa la calibración de este parámetro.")
        )
    lineas.append("")
    lineas.append(
        "Corrige la calibración en el catálogo y vuelve a correr la validación en "
        "🔬 Motor IV antes de confiar en los resultados de energía de este panel."
    )
    return "\n".join(lineas)
