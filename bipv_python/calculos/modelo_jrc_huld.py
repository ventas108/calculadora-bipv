# -*- coding: utf-8 -*-
"""Segunda opinión independiente para tecnologías de capa fina (CdTe, CIS):
power-rating model de Huld et al. (JRC/ESTI, 2011), usado por PVGIS.

Coeficientes verificados contra el TEXTO COMPLETO (no el resumen) de 2 papers
del mismo grupo de autores (Kumar, Sudhakar, Samykano):

- CdTe: Kumar (2019) "Performance of single-sloped pitched roof cadmium
  telluride (CdTe) building-integrated photovoltaic system in tropical
  weather conditions", Beni-Suef Univ J Basic Appl Sci 8:2,
  DOI 10.1186/s43088-019-0003-2, Tabla 2.
- CIS: Kumar, Sudhakar, Samykano (2019) "Performance comparison of BAPV and
  BIPV systems with c-Si, CIS and CdTe photovoltaic technologies under
  tropical weather conditions", Case Studies in Thermal Engineering 13:100374,
  DOI 10.1016/j.csite.2018.100374, Tabla 4 -- esta misma tabla también trae
  CdTe, y sus valores coinciden EXACTOS con los ya verificados del primer
  paper (23,37/5,44/-0,046689/...) -- confirma que ambas fuentes son
  consistentes entre sí, no solo internamente.

Por qué existe este módulo (31-ago-2026): el proyecto real Teusaquillo
(fachada CdTe vertical, ver `FICHA_PVSYST_TEUSAQUILLO.md`) dio PR=100,6%/
101,2% con el motor principal de la app (SDM De Soto + Motor Óptico) --
inusual para un sistema real. La literatura de CdTe BIPV bajo clima tropical
nunca reporta PR por encima de 77%. Este módulo implementa un modelo
COMPLETAMENTE INDEPENDIENTE (ajuste empírico calibrado contra mediciones
reales de módulos en el ESTI europeo, no un circuito equivalente físico
como el SDM) para correr sobre los MISMOS datos horarios (POA, T_ambiente,
viento) que ya usa la app.

Generalizado a CIS el mismo día (pedido explícito del usuario: "los sistemas
BIPV necesitan también este tipo de tecnología") -- BIPV Colombia usa tanto
CdTe (SolTech/ASP, Solar First) como paneles con otras químicas de capa
fina en el catálogo; los coeficientes de CIS ahora también están verificados
y disponibles con el mismo rigor.

⚠️ NO reemplaza al motor principal (SDM De Soto, más riguroso físicamente) --
es una verificación cruzada puntual, mismo espíritu que el modo "curva IV
real" ya existente en 📊 Producción para comparar contra el modelo simplificado.
Solo cubre CdTe y CIS -- otras tecnologías (c-Si, perovskita, etc.) no tienen
coeficientes verificados aquí todavía.
"""
import numpy as np
import pandas as pd
import pvlib

# ── Coeficientes del power-rating model, por tecnología ─────────────────────
# Fuente primaria del método: Huld T., Friesen G., Skoczek A., Kenny R.P.,
# Sample T., Field M., Dunlop E.D. (2011) "A power-rating model for
# crystalline silicon PV modules", Sol Energy Mater Sol Cells 95(12):3359-3369.
# Coeficientes por tecnología (temperatura Faiman + potencia) verificados
# contra el texto completo de los 2 papers citados en el docstring del
# módulo -- ver ahí el detalle de cuál tabla trae cuál tecnología.
COEFICIENTES_JRC = {
    "CdTe": {
        "temperatura": {"u0": 23.37, "u1": 5.44},
        "potencia": {
            "t1": -0.046689, "t2": -0.072844, "t3": -0.002262,
            "t4": 0.000276, "t5": 0.000159, "t6": -0.000006,
        },
    },
    "CIS": {
        "temperatura": {"u0": 22.19, "u1": 4.09},
        "potencia": {
            "t1": -0.005554, "t2": -0.038724, "t3": -0.003723,
            "t4": -0.000905, "t5": -0.001256, "t6": 0.000001,
        },
    },
    # Agregada 31-ago-2026, mismo paper/Tabla 4 que CIS (pedido explícito del
    # usuario: "integra en el calculo interno technologies namely crystalline
    # (c-Si) y asi cumplimos con el ciclo" -- las 3 tecnologías que el paper
    # realmente compara).
    "Crystalline": {
        "temperatura": {"u0": 30.02, "u1": 6.28},
        "potencia": {
            "t1": -0.017237, "t2": -0.040465, "t3": -0.004702,
            "t4": 0.000149, "t5": 0.000170, "t6": 0.000005,
        },
    },
}

TECNOLOGIAS_SOPORTADAS = tuple(COEFICIENTES_JRC.keys())

# ── Clasificador: texto libre real del catálogo -> tecnología JRC ───────────
# El catálogo real (`datos/catalogo_paneles_excel.py`) NO usa las etiquetas
# limpias "CdTe"/"CIS"/"Crystalline" -- trae texto libre de fabricante (ej.
# "CdTe pelicula delgada", "CIGS", "N-Type TopCon Bifacial Agri", "MonoSi",
# "Mono PERC Bifacial BIPV"). Comparar por igualdad exacta (como hacía
# `extraer_parametros_proyecto()` antes de esta generalización) rechazaba casi
# todo el catálogo real, no solo los paneles genuinamente sin coeficientes.
# Reglas conservadoras, por palabra clave -- nunca inventan una tecnología:
# si nada calza, se rechaza igual que antes, con el texto original en el
# mensaje de error para que quede claro qué no se pudo clasificar.
_PALABRAS_CDTE = ("cdte",)
_PALABRAS_CIS = ("cigs", "cis")
_PALABRAS_CRYSTALLINE = (
    "mono", "poly", "polycristalino", "policristalino", "monocristalino",
    "topcon", "perc", "n-type", "p-type", "c-si", "csi", "crystalline",
    "cristalino", "silicio", "silicon",
)


def clasificar_tecnologia_jrc(tecnologia_cruda: str | None) -> str | None:
    """
    Normaliza el texto libre de tecnología del catálogo real a una de las
    claves de COEFICIENTES_JRC, o None si no se reconoce ningún patrón (nunca
    adivina). CdTe se revisa primero porque "CdTe pelicula delgada" también
    podría matchear alguna palabra de otra categoría por coincidencia parcial
    -- el orden de las reglas importa.

    ⚠️ Aproximación declarada: "CIGS" (la variante real presente en el
    catálogo) se mapea a los coeficientes de "CIS" -- son familias de
    calcogenuro de cobre relacionadas pero no idénticas (CIGS añade galio);
    el paper fuente (Kumar et al. 2019) usa "CIS" de forma genérica para
    esta familia. Es la mejor aproximación disponible con literatura
    verificada, no una equivalencia exacta -- se documenta, no se oculta.
    """
    if not tecnologia_cruda:
        return None
    t = tecnologia_cruda.strip().lower()
    if any(p in t for p in _PALABRAS_CDTE):
        return "CdTe"
    if any(p in t for p in _PALABRAS_CIS):
        return "CIS"
    if any(p in t for p in _PALABRAS_CRYSTALLINE):
        return "Crystalline"
    return None


def _coeficientes_o_error(tecnologia: str) -> dict:
    coef = COEFICIENTES_JRC.get(tecnologia)
    if coef is None:
        raise ValueError(
            f"Tecnología '{tecnologia}' sin coeficientes verificados en este módulo -- "
            f"solo {', '.join(TECNOLOGIAS_SOPORTADAS)} tienen coeficientes citables "
            "confirmados contra el texto completo de la literatura (ver docstring)."
        )
    return coef


def temperatura_modulo_faiman_jrc(poa_wm2, t_ambiente_c, viento_ms, tecnologia: str = "CdTe"):
    """Temperatura de módulo (°C) vía Faiman, con los coeficientes específicos
    de la tecnología dada (no los genéricos u0=25/u1=6.84 de pvlib, calibrados
    para c-Si)."""
    coef = _coeficientes_o_error(tecnologia)["temperatura"]
    return pvlib.temperature.faiman(poa_wm2, t_ambiente_c, viento_ms, u0=coef["u0"], u1=coef["u1"])


def potencia_jrc(poa_wm2, t_modulo_c, p_stc_w: float, tecnologia: str = "CdTe"):
    """
    Potencia DC (W) hora a hora según el power-rating model de Huld et al.,
    con los coeficientes de la tecnología dada. Vectorizado (numpy/pandas),
    sin iteración.

    P(I',T') = I'·P_STC·[1 + t1·ln(I') + t2·ln(I')² + t3·T' + t4·T'·ln(I')
                          + t5·T'·ln(I')² + t6·T'²]
    con I' = I/1000 (irradiancia efectiva) y T' = T_módulo - 25 (temperatura
    efectiva). Para I'≤0 (de noche) la potencia es 0 -- ln(I') no está
    definido y físicamente no hay generación.
    """
    coef = _coeficientes_o_error(tecnologia)["potencia"]

    poa = np.asarray(poa_wm2, dtype=float)
    tmod = np.asarray(t_modulo_c, dtype=float)

    i_ef = poa / 1000.0
    t_ef = tmod - 25.0

    con_luz = i_ef > 0
    ln_i = np.zeros_like(i_ef)
    ln_i[con_luz] = np.log(i_ef[con_luz])

    factor = (
        1.0
        + coef["t1"] * ln_i
        + coef["t2"] * ln_i ** 2
        + coef["t3"] * t_ef
        + coef["t4"] * t_ef * ln_i
        + coef["t5"] * t_ef * ln_i ** 2
        + coef["t6"] * t_ef ** 2
    )

    p = np.where(con_luz, i_ef * p_stc_w * factor, 0.0)
    return np.clip(p, 0.0, None)


def calcular_pr_jrc(poa_wm2, t_ambiente_c, viento_ms, p_stc_w: float, tecnologia: str = "CdTe") -> dict:
    """
    Corre el power-rating model de Huld/JRC (para CdTe o CIS) sobre una serie
    horaria completa (típicamente 8760 horas de un TMY) y devuelve el PR
    anual, como segunda opinión independiente del motor SDM principal de la app.

    Retorna dict:
      E_anual_kWh        : energía DC anual según este modelo.
      POA_anual_kWh_m2    : irradiación POA anual (para verificar que ambos
                             modelos parten del mismo recurso solar).
      PR_pct              : Performance Ratio (%) = E / (P_STC_kW × POA_kWh_m2).
      P_dc_jrc_w           : serie horaria de potencia (para inspección/gráficas).
    """
    poa = pd.Series(poa_wm2).astype(float).reset_index(drop=True)
    t_amb = pd.Series(t_ambiente_c).astype(float).reset_index(drop=True)
    viento = pd.Series(viento_ms).astype(float).reset_index(drop=True)

    t_modulo = temperatura_modulo_faiman_jrc(poa, t_amb, viento, tecnologia=tecnologia)
    p_dc = potencia_jrc(poa.to_numpy(), t_modulo.to_numpy(), p_stc_w, tecnologia=tecnologia)

    e_anual_kwh = float(p_dc.sum()) / 1000.0
    poa_anual_kwh_m2 = float(poa.sum()) / 1000.0
    p_stc_kw = p_stc_w / 1000.0

    pr_pct = (
        e_anual_kwh / (p_stc_kw * poa_anual_kwh_m2) * 100.0
        if poa_anual_kwh_m2 > 0 else None
    )

    return {
        "E_anual_kWh": round(e_anual_kwh, 1),
        "POA_anual_kWh_m2": round(poa_anual_kwh_m2, 1),
        "PR_pct": round(pr_pct, 2) if pr_pct is not None else None,
        "P_dc_jrc_w": p_dc,
    }


def extraer_parametros_proyecto(estado: dict) -> dict:
    """
    Extrae de un proyecto guardado (el dict "estado" de un JSON de
    `datos/proyectos/*.json`, ver `calculos/proyectos_manager.py`) los
    parámetros mínimos para correr la verificación JRC/Huld: sitio,
    geometría del array, tecnología y potencia STC total.

    Generalizado (31-ago-2026) en 3 pasos: primero para leer cualquier
    proyecto guardado (antes estaba fijo a constantes de Teusaquillo), luego
    para aceptar CIS además de CdTe, luego para agregar Crystalline (c-Si) y
    CLASIFICAR el texto libre real del catálogo (ej. "CdTe pelicula delgada",
    "CIGS", "N-Type TopCon Bifacial Agri") en vez de exigir una coincidencia
    exacta con la etiqueta limpia -- todo pedido explícito del usuario en la
    misma conversación.

    Lanza ValueError con un mensaje claro (nunca un valor inventado) si:
    - el panel del proyecto usa una tecnología que `clasificar_tecnologia_jrc()`
      no reconoce (ver ese docstring para las reglas y su límite);
    - la ciudad no está en `datos/ciudades_colombia.py`;
    - falta la potencia del panel o el número de módulos (Dimensionamiento
      nunca se corrió en ese proyecto).
    """
    panel = estado.get("panel_dict") or {}
    tecnologia_cruda = panel.get("tecnologia")
    tecnologia = clasificar_tecnologia_jrc(tecnologia_cruda)
    if tecnologia is None:
        raise ValueError(
            f"Este proyecto usa panel de tecnología '{tecnologia_cruda or 'desconocida'}' "
            f"-- el modelo JRC/Huld implementado aquí solo reconoce patrones de "
            f"{', '.join(TECNOLOGIAS_SOPORTADAS)} (ver `clasificar_tecnologia_jrc()`). "
            "No aplica a este proyecto."
        )

    from datos.ciudades_colombia import CIUDADES

    ciudad_nombre = estado.get("ciudad") or estado.get("tmy_ciudad")
    ciudad = CIUDADES.get(ciudad_nombre)
    if not ciudad:
        raise ValueError(
            f"Ciudad '{ciudad_nombre}' no reconocida en datos/ciudades_colombia.py "
            "-- no se puede derivar lat/lon/altitud para descargar el TMY."
        )

    p_stc_modulo_w = float(panel.get("Pmax_stc") or 0)
    n_paneles = int(
        estado.get("N_paneles_granja") or estado.get("N_paneles_dim")
        or estado.get("N_paneles") or 0
    )
    if p_stc_modulo_w <= 0 or n_paneles <= 0:
        raise ValueError(
            "Faltan datos del array (potencia del panel o número de módulos) -- "
            "corre 📐 Dimensionamiento en ese proyecto antes de esta verificación."
        )

    return {
        "nombre_proyecto": estado.get("nombre_proyecto", "Proyecto sin nombre"),
        "panel_nombre": estado.get("panel_nombre_dim", "?"),
        "tecnologia": tecnologia,
        "tecnologia_cruda": tecnologia_cruda,
        "ciudad": ciudad_nombre,
        "lat": float(ciudad["lat"]), "lon": float(ciudad["lon"]), "alt_m": float(ciudad["alt_m"]),
        "tilt": float(estado.get("tilt_fachada", estado.get("tilt_default", 90.0))),
        "azimuth": float(estado.get("azimuth_fachada", 180.0)),
        "albedo": float(estado.get("albedo_suelo", 0.20)),
        "p_stc_total_w": p_stc_modulo_w * n_paneles,
        "n_paneles": n_paneles,
    }


# Rangos de PR reportados en la literatura real (Kumar, Sudhakar, Samykano
# 2019, Case Studies in Thermal Engineering 13:100374 -- mismo paper y misma
# Tabla que los coeficientes de arriba, así que Crystalline/CIS/CdTe son
# directamente comparables entre sí, sin mezclar configuraciones de estudios
# distintos), clima tropical de Malasia, sistema 32.7 kWp.
REFERENCIA_LITERATURA_PR = {
    "Crystalline": {"BIPV": (71.11, 73.92), "BAPV": (74.18, 76.34)},
    "CIS": {"BIPV": (72.21, 73.92), "BAPV": (73.68, 75.46)},
    "CdTe": {"BIPV": (75.55, 76.94), "BAPV": (76.32, 78.12)},
}


def resultado_jrc_desde_sesion(session_state) -> dict | None:
    """
    Versión "en vivo" de la verificación cruzada, pensada para correr DENTRO
    de una página de la app (31-ago-2026, pedido explícito del usuario: que
    la comparación aparezca físicamente dentro del módulo respectivo, no
    solo en un script de terminal).

    A diferencia de `scripts/verificar_jrc_huld.py` (que SIEMPRE descarga un
    TMY fresco de PVGIS porque un proyecto guardado no conserva los
    DataFrames), esta función reutiliza `session_state["poa_df"]` y
    `session_state["tmy_df"]` -- el mismo recurso solar que ☀️ Recurso Solar
    ya calculó para esta sesión -- así que NO hace ninguna llamada de red
    nueva ni recalcula nada que la app ya tenga.

    Devuelve None (nunca lanza) si no aplica: tecnología sin coeficientes
    reconocidos, o Recurso Solar todavía no se corrió en esta sesión. El
    llamador simplemente no muestra nada en ese caso -- mismo principio que
    el resto de alertas de esta app: nunca inventar una comparación que no
    se puede respaldar con datos reales.
    """
    try:
        params = extraer_parametros_proyecto(dict(session_state))
    except ValueError:
        return None

    poa_df = session_state.get("poa_df")
    tmy_df = session_state.get("tmy_df")
    if poa_df is None or tmy_df is None or len(poa_df) == 0 or len(tmy_df) == 0:
        return None
    if "poa_global" not in poa_df.columns or "T2m" not in tmy_df.columns or "WS10m" not in tmy_df.columns:
        return None

    r = calcular_pr_jrc(
        poa_wm2=poa_df["poa_global"].to_numpy(),
        t_ambiente_c=tmy_df["T2m"].to_numpy(),
        viento_ms=tmy_df["WS10m"].to_numpy(),
        p_stc_w=params["p_stc_total_w"],
        tecnologia=params["tecnologia"],
    )
    if r["PR_pct"] is None:
        return None

    return {
        "tecnologia": params["tecnologia"],
        "tecnologia_cruda": params["tecnologia_cruda"],
        "panel_nombre": params["panel_nombre"],
        "PR_pct": r["PR_pct"],
        "E_anual_kWh": r["E_anual_kWh"],
        "POA_anual_kWh_m2": r["POA_anual_kWh_m2"],
        "referencia_literatura": REFERENCIA_LITERATURA_PR.get(params["tecnologia"]),
    }
