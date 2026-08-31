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
}

TECNOLOGIAS_SOPORTADAS = tuple(COEFICIENTES_JRC.keys())


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

    Generalizado (31-ago-2026) en 2 pasos: primero para leer cualquier
    proyecto guardado (antes estaba fijo a constantes de Teusaquillo), luego
    para aceptar CIS además de CdTe (pedido explícito del usuario).

    Lanza ValueError con un mensaje claro (nunca un valor inventado) si:
    - el panel del proyecto usa una tecnología sin coeficientes verificados
      aquí (solo CdTe y CIS por ahora, ver TECNOLOGIAS_SOPORTADAS);
    - la ciudad no está en `datos/ciudades_colombia.py`;
    - falta la potencia del panel o el número de módulos (Dimensionamiento
      nunca se corrió en ese proyecto).
    """
    panel = estado.get("panel_dict") or {}
    tecnologia = panel.get("tecnologia")
    if tecnologia not in TECNOLOGIAS_SOPORTADAS:
        raise ValueError(
            f"Este proyecto usa panel de tecnología '{tecnologia or 'desconocida'}' "
            f"-- el modelo JRC/Huld implementado aquí solo tiene coeficientes "
            f"verificados para {', '.join(TECNOLOGIAS_SOPORTADAS)} (ver docstring "
            "del módulo). No aplica a este proyecto."
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
        "ciudad": ciudad_nombre,
        "lat": float(ciudad["lat"]), "lon": float(ciudad["lon"]), "alt_m": float(ciudad["alt_m"]),
        "tilt": float(estado.get("tilt_fachada", estado.get("tilt_default", 90.0))),
        "azimuth": float(estado.get("azimuth_fachada", 180.0)),
        "albedo": float(estado.get("albedo_suelo", 0.20)),
        "p_stc_total_w": p_stc_modulo_w * n_paneles,
        "n_paneles": n_paneles,
    }
