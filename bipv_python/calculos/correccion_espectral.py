# -*- coding: utf-8 -*-
"""
Corrección espectral para módulos CdTe — modelo First Solar.

Pedido explícito del usuario (6-sep-2026), tras la auditoría del motor de
producción: "la corrección espectral es importante justo para CdTe, que es
buena parte del catálogo real (Soltech, First Solar)".

Qué es y por qué importa
------------------------
El espectro solar real varía hora a hora según cuánta atmósfera atraviesa
la luz (masa de aire) y cuánto vapor de agua hay en el camino (agua
precipitable) -- más masa de aire/agua = espectro corrido hacia el rojo. La
corriente de cortocircuito (Isc) de un módulo depende de qué tan bien su
respuesta espectral cubre el espectro que realmente le está llegando en ese
momento, no el espectro estándar AM1.5G de la ficha STC. Para silicio
cristalino este efecto es pequeño (~±1-2%) y casi ninguna herramienta lo
aplica por defecto. Para **CdTe es mucho más relevante** (~±5-10% real)
porque su respuesta espectral es más angosta que la del silicio -- por eso
PVsyst y la literatura técnica SÍ lo aplican para esta tecnología
específicamente.

Modelo usado: First Solar (Pelaez et al. 2019; coeficientes originales de
Jäger et al., First Solar Series 4-2 CdTe) vía
`pvlib.spectrum.spectral_factor_firstsolar(module_type="cdte")` -- el MISMO
modelo/enfoque que usa PVsyst para esta tecnología, no una aproximación
propia. Verificado que la función y sus coeficientes 'cdte' son IDÉNTICOS
entre pvlib==0.11.1 (pin de producción) y 0.15.2 (sandbox local) -- a
diferencia del bug de nombres de columna encontrado el mismo día con
`haydavies(return_components=True)` (ver sección 59 del manual), esta
función no tuvo ese riesgo.

Aplica a TODOS los paneles CdTe del catálogo (Soltech, First Solar, HIITIO,
EINNOVA/vidrio) porque el factor depende del SITIO y la ATMÓSFERA (lat/lon/
TMY), no del panel específico -- un mismo factor horario sirve para
cualquier ficha CdTe que se simule en ese proyecto.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pvlib

# Límites físicos de defensa (no del modelo -- el modelo pvlib ya clipea
# internamente contra su rango validado de masa de aire/agua precipitable).
# Este clip adicional es solo para que un factor jamás pueda amplificar o
# recortar la potencia de forma absurda si algo aguas arriba viene mal.
_FACTOR_MIN = 0.5
_FACTOR_MAX = 1.5


def calcular_factor_espectral_cdte(
    tmy: pd.DataFrame,
    lat: float,
    lon: float,
    alt_m: float,
) -> pd.Series:
    """
    Factor multiplicativo horario M(t) de corrección espectral CdTe (modelo
    First Solar). Multiplica la irradiancia efectiva ANTES del cálculo de
    potencia -- ver `calculos.produccion.simular_produccion_anual()`,
    parámetro `factor_espectral`.

    Requiere la columna "RH" (humedad relativa %) en el TMY -- PVGIS la
    entrega, pero `obtener_tmy_pvgis()` la descartaba antes del 6-sep-2026
    (ver su docstring). Si el TMY viene de un caché de disco DESCARGADO
    ANTES de ese fix, no tendrá "RH" -- en ese caso esta función retorna
    una serie de 1.0 (sin corrección, retrocompatible) en vez de fallar o
    inventar el dato; `serie.attrs["aplicado"]` queda en False para que el
    caller pueda avisar ("vuelve a descargar el TMY para activar esto").

    Retorna
    -------
    pd.Series indexada como `tmy`, valores en [0.5, 1.5] (ver `_FACTOR_MIN`/
    `_FACTOR_MAX`), 1.0 exacto de noche (sin sol, el factor no tiene sentido
    físico y G_efectiva ya es 0 ahí de todas formas).
    `.attrs["aplicado"]` (bool) y `.attrs["motivo"]` (str, solo si no se
    aplicó) para trazabilidad -- nunca falla en silencio.
    """
    if "RH" not in tmy.columns:
        serie = pd.Series(1.0, index=tmy.index, name="factor_espectral_cdte")
        serie.attrs["aplicado"] = False
        serie.attrs["motivo"] = (
            "El TMY no tiene columna RH (humedad relativa) -- probablemente "
            "viene de un caché de disco descargado antes del 6-sep-2026. "
            "Usa '🔄 Limpiar caché' en ☀️ Recurso Solar y descarga de nuevo "
            "para activar la corrección espectral CdTe."
        )
        return serie

    loc = pvlib.location.Location(latitude=lat, longitude=lon, altitude=alt_m, tz="UTC")
    solar_pos = loc.get_solarposition(tmy.index)

    precipitable_water = pvlib.atmosphere.gueymard94_pw(
        tmy["T2m"].to_numpy(dtype=float), tmy["RH"].to_numpy(dtype=float)
    )
    airmass_rel = pvlib.atmosphere.get_relative_airmass(solar_pos["apparent_zenith"])
    airmass_abs = pvlib.atmosphere.get_absolute_airmass(
        airmass_rel, tmy["SP"].to_numpy(dtype=float)
    )

    factor = pvlib.spectrum.spectral_factor_firstsolar(
        precipitable_water=precipitable_water,
        airmass_absolute=airmass_abs.to_numpy(dtype=float),
        module_type="cdte",
    )
    factor = np.asarray(factor, dtype=float)

    # De noche (sol bajo el horizonte) la masa de aire relativa diverge y el
    # factor no tiene sentido físico -- fijar a 1.0 (neutro). G_efectiva ya
    # es 0 en esas horas de todas formas (ver simular_produccion_anual), así
    # que esto es solo higiene numérica, no cambia ningún resultado.
    elevacion = solar_pos["apparent_elevation"].to_numpy(dtype=float)
    factor = np.where(elevacion > 0.0, factor, 1.0)
    factor = np.nan_to_num(factor, nan=1.0, posinf=1.0, neginf=1.0)
    factor = np.clip(factor, _FACTOR_MIN, _FACTOR_MAX)

    serie = pd.Series(factor, index=tmy.index, name="factor_espectral_cdte")
    serie.attrs["aplicado"] = True
    return serie
