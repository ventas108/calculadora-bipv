# -*- coding: utf-8 -*-
"""Segunda opinión independiente para CdTe: power-rating model de Huld et al.
(JRC/ESTI, 2011), usado por PVGIS y citado con coeficientes explícitos para
CdTe en Kumar (2019) "Performance of single-sloped pitched roof cadmium
telluride (CdTe) building-integrated photovoltaic system in tropical weather
conditions", Beni-Suef Univ J Basic Appl Sci 8:2, DOI 10.1186/s43088-019-0003-2
(Tabla 2, texto completo verificado -- no solo el resumen).

Por qué existe este módulo (31-ago-2026): el proyecto real Teusaquillo
(fachada CdTe vertical, ver `FICHA_PVSYST_TEUSAQUILLO.md`) dio PR=100,6%/
101,2% con el motor principal de la app (SDM De Soto + Motor Óptico) --
inusual para un sistema real. La literatura de CdTe BIPV bajo clima tropical
(3 papers del mismo grupo Kumar/Sudhakar/Samykano) nunca reporta PR por
encima de 77%, ni en techo ni en fachada. Este módulo implementa un modelo
COMPLETAMENTE INDEPENDIENTE (ajuste empírico calibrado contra mediciones
reales de módulos CdTe en el ESTI europeo, no un circuito equivalente físico
como el SDM) para correr sobre los MISMOS datos horarios (POA, T_ambiente,
viento) que ya usa la app, y así distinguir dos hipótesis:

  (a) el PR>100% es un comportamiento real de CdTe a baja irradiancia/clima
      frío de altura -- en ese caso, este segundo modelo, calibrado también
      para CdTe pero con ecuaciones distintas, debería acercarse a un PR
      igualmente alto para las mismas horas; o
  (b) es un artefacto de la curva FF-vs-irradiancia calibrada del panel
      ASP-ST1-T40 en el SDM de esta app -- en ese caso, este modelo daría un
      PR mucho más cercano al rango de la literatura (66-77%).

NO reemplaza al motor principal (SDM De Soto, más riguroso físicamente) --
es una verificación cruzada puntual, mismo espíritu que el modo "curva IV
real" ya existente en 📊 Producción para comparar contra el modelo simplificado.
"""
import numpy as np
import pandas as pd
import pvlib

# ── Coeficientes del power-rating model, específicos de CdTe ────────────────
# Fuente: Huld T., Friesen G., Skoczek A., Kenny R.P., Sample T., Field M.,
# Dunlop E.D. (2011) "A power-rating model for crystalline silicon PV
# modules", Sol Energy Mater Sol Cells 95(12):3359-3369 -- coeficientes
# reproducidos para CdTe en Kumar (2019), Tabla 2 (ver docstring del módulo).
COEF_POTENCIA_CDTE = {
    "t1": -0.046689,
    "t2": -0.072844,
    "t3": -0.002262,
    "t4": 0.000276,
    "t5": 0.000159,
    "t6": -0.000006,
}

# Coeficientes de temperatura de módulo (modelo Faiman 1998/2008, adoptado en
# IEC 61853) estandarizados para CdTe -- Kumar (2019), Tabla 2, vía Koehl
# et al. (2011) "Modeling of the nominal operating cell temperature based on
# outdoor weathering", Sol Energy Mater Sol Cells 95(7):1638-1646.
# n = u0 (factor de pérdida térmica combinado), n* = u1 (factor dependiente
# del viento) en la nomenclatura de pvlib.temperature.faiman().
N_TEMPERATURA_CDTE = 23.37
N_ESTRELLA_TEMPERATURA_CDTE = 5.44


def temperatura_modulo_faiman_cdte(
    poa_wm2, t_ambiente_c, viento_ms,
    n: float = N_TEMPERATURA_CDTE, n_estrella: float = N_ESTRELLA_TEMPERATURA_CDTE,
):
    """Temperatura de módulo (°C) vía Faiman, con los coeficientes CdTe del
    paper (no los genéricos u0=25/u1=6.84 de pvlib, calibrados para c-Si)."""
    return pvlib.temperature.faiman(poa_wm2, t_ambiente_c, viento_ms, u0=n, u1=n_estrella)


def potencia_jrc_cdte(poa_wm2, t_modulo_c, p_stc_w: float, coef: dict = COEF_POTENCIA_CDTE):
    """
    Potencia DC (W) hora a hora según el power-rating model de Huld et al.
    para CdTe. Vectorizado (numpy/pandas), sin iteración.

    P(I',T') = I'·P_STC·[1 + t1·ln(I') + t2·ln(I')² + t3·T' + t4·T'·ln(I')
                          + t5·T'·ln(I')² + t6·T'²]
    con I' = I/1000 (irradiancia efectiva) y T' = T_módulo - 25 (temperatura
    efectiva). Para I'≤0 (de noche) la potencia es 0 -- ln(I') no está
    definido y físicamente no hay generación.
    """
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


def calcular_pr_jrc_cdte(
    poa_wm2, t_ambiente_c, viento_ms, p_stc_w: float,
    n: float = N_TEMPERATURA_CDTE, n_estrella: float = N_ESTRELLA_TEMPERATURA_CDTE,
    coef: dict = COEF_POTENCIA_CDTE,
) -> dict:
    """
    Corre el power-rating model de Huld/JRC para CdTe sobre una serie horaria
    completa (típicamente 8760 horas de un TMY) y devuelve el PR anual, como
    segunda opinión independiente del motor SDM principal de la app.

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

    t_modulo = temperatura_modulo_faiman_cdte(poa, t_amb, viento, n=n, n_estrella=n_estrella)
    p_dc = potencia_jrc_cdte(poa.to_numpy(), t_modulo.to_numpy(), p_stc_w, coef=coef)

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
    geometría del array y potencia STC total.

    Generalización (31-ago-2026, pedida explícitamente por el usuario tras
    correr la verificación a mano para Teusaquillo): antes esto estaba fijo
    como constantes al inicio de un script; ahora cualquier proyecto CdTe
    guardado puede verificarse sin editar código.

    Lanza ValueError con un mensaje claro (nunca un valor inventado) si:
    - el panel del proyecto no es CdTe -- los coeficientes de este modelo
      son específicos de esa tecnología, no aplican a c-Si/CIS/otros;
    - la ciudad no está en `datos/ciudades_colombia.py`;
    - falta la potencia del panel o el número de módulos (Dimensionamiento
      nunca se corrió en ese proyecto).
    """
    panel = estado.get("panel_dict") or {}
    tecnologia = panel.get("tecnologia")
    if tecnologia != "CdTe":
        raise ValueError(
            f"Este proyecto usa panel de tecnología '{tecnologia or 'desconocida'}' "
            "-- el modelo JRC/Huld implementado aquí solo tiene coeficientes "
            "calibrados para CdTe (ver docstring del módulo). No aplica a este proyecto."
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
