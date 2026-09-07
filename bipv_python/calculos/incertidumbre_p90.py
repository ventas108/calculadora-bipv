# -*- coding: utf-8 -*-
"""
Variabilidad interanual REAL del recurso solar, para el modelo P90 de
📄 Financiero (7-sep-2026).

Contexto: pages/7_💰_Financiero.py ya calculaba un P90 bancable con la
metodología estándar de la industria (z₉₀ × σ_total, σ_total = combinación
cuadrática de σ_irr + σ_PR -- EPRI TR-107348 / IEC 61724-3, verificado
contra la metodología pública de Solargis antes de tocar nada). La fórmula
ya era correcta -- la brecha real era que σ_irr (variabilidad interanual)
venía de una tabla FIJA por ciudad (24 palabras clave colombianas), no de
un cálculo real para las coordenadas exactas del proyecto.

Este módulo calcula esa variabilidad DE VERDAD, con datos reales: descarga
la serie horaria multi-año de PVGIS (endpoint /seriescalc, vía
pvlib.iotools.get_pvgis_hourly() -- distinto del endpoint /tmy que ya usa
calculos/solar.py::obtener_tmy_pvgis(), que solo da UN año sintético
representativo, no la serie real año por año), sumas anuales de GHI
horizontal, y la desviación estándar relativa de esas sumas.

GHI horizontal, no POA transpuesta con la geometría del proyecto: la
variabilidad interanual es una propiedad del recurso solar del sitio
(dominada por variación de nubosidad año a año), prácticamente igual en
magnitud para GHI y para la POA de cualquier orientación -- mismo criterio
que usa la metodología pública de Solargis (calculan la variabilidad
"desde series temporales" del recurso, no re-transponen por cada
orientación de proyecto). Evita además duplicar el modelo de transposición
Hay-Davies del proyecto (calculos/solar.py::calcular_poa()) solo para este
cálculo auxiliar.

Nunca inventa: si PVGIS falla, da timeout, o no hay suficientes años
completos, devuelve sigma_irr_real_pct=None -- el llamador (Financiero)
cae al valor de tabla existente, comportamiento histórico sin cambios.
"""
from __future__ import annotations

import os
import re
import pickle
from datetime import datetime, timezone

import numpy as np

MIN_ANIOS_VALIDOS = 5  # menos de esto, la desviación estándar no es confiable

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "datos", "solar_cache")


def _cache_path(lat: float, lon: float, anios_atras: int) -> str:
    os.makedirs(_CACHE_DIR, exist_ok=True)
    return os.path.join(
        _CACHE_DIR, f"variabilidad_p90_{lat:.4f}_{lon:.4f}_{anios_atras}a.pkl"
    )


def _leer_cache_variabilidad(lat: float, lon: float, anios_atras: int) -> dict | None:
    try:
        p = _cache_path(lat, lon, anios_atras)
        if os.path.exists(p):
            with open(p, "rb") as f:
                return pickle.load(f)
    except Exception:
        pass
    return None


def _guardar_cache_variabilidad(lat: float, lon: float, anios_atras: int, resultado: dict) -> None:
    try:
        with open(_cache_path(lat, lon, anios_atras), "wb") as f:
            pickle.dump(resultado, f)
    except Exception:
        pass  # el caché es una optimización, no un requisito -- nunca revienta la página por esto


def calcular_variabilidad_interanual_real(
    lat: float,
    lon: float,
    anios_atras: int = 11,
    usar_cache: bool = True,
) -> dict:
    """
    Descarga la serie horaria multi-año real de PVGIS para (lat, lon) y
    calcula la variabilidad interanual del recurso solar -- σ_irr_real (%),
    la desviación estándar relativa de las sumas anuales de GHI horizontal.

    anios_atras: cuántos años hacia atrás pedir desde el más reciente
    disponible en PVGIS (default 11 -- suficiente para una desviación
    estándar razonablemente estable sin pedir una serie excesivamente
    larga; PVGIS/ERA5 típicamente cubre desde ~2005).

    Retorna dict:
      sigma_irr_real_pct : float | None -- None si falló o hay <5 años
                            completos (nunca inventa con pocos datos)
      n_anios             : int -- años calendario COMPLETOS usados
      anio_inicio/anio_fin: rango real de años usados
      media_kwh_m2_anio   : float -- GHI anual promedio del período
      raddatabase         : str -- base de datos que PVGIS eligió (ej.
                            "PVGIS-ERA5", "PVGIS-SARAH2" -- varía según
                            cobertura geográfica, se declara siempre)
      anios_detalle        : dict {año: GHI_kWh_m2} -- para auditoría
      error                : str | None -- motivo si sigma_irr_real_pct es None

    Nunca lanza excepción -- cualquier falla de red/parseo se captura y
    se refleja en el campo "error", con sigma_irr_real_pct=None.
    """
    resultado_vacio = {
        "sigma_irr_real_pct": None, "n_anios": 0, "anio_inicio": None,
        "anio_fin": None, "media_kwh_m2_anio": None, "raddatabase": None,
        "anios_detalle": {}, "error": None,
    }

    if usar_cache:
        cacheado = _leer_cache_variabilidad(lat, lon, anios_atras)
        if cacheado is not None:
            return cacheado

    try:
        from pvlib.iotools import get_pvgis_hourly
    except ImportError:
        r = dict(resultado_vacio, error="pvlib no disponible")
        return r

    anio_actual = datetime.now(timezone.utc).year
    anio_fin_pedido = anio_actual - 1  # el año en curso nunca está completo
    anio_inicio_pedido = anio_fin_pedido - anios_atras + 1

    # PVGIS tiene un año final REAL de cobertura que no necesariamente
    # coincide con "año actual - 1" (su base de datos se actualiza con
    # rezago propio) -- en vez de asumirlo, se intenta con el pedido
    # ingenuo primero y, si PVGIS lo rechaza, se reintenta UNA vez con el
    # rango real que el propio servidor reporta en el mensaje de error
    # ("...enter an integer between 2005 and 2023.") -- nunca se inventa
    # el año límite, se lee de la respuesta real del servidor. Encontrado
    # en vivo (7-sep-2026): pedir hasta "el año actual - 1" fallaba porque
    # PVGIS solo cubre hasta 2023 en este momento.
    def _pedir(start, end):
        return get_pvgis_hourly(
            float(lat), float(lon),
            start=start, end=end,
            surface_tilt=0, surface_azimuth=180,
            components=True, timeout=90,
        )

    try:
        df, inputs, meta = _pedir(anio_inicio_pedido, anio_fin_pedido)
    except Exception as exc:
        _match = re.search(r"between (\d{4}) and (\d{4})", str(exc))
        if _match:
            anio_max_real = int(_match.group(2))
            anio_fin_pedido = anio_max_real
            anio_inicio_pedido = anio_fin_pedido - anios_atras + 1
            try:
                df, inputs, meta = _pedir(anio_inicio_pedido, anio_fin_pedido)
            except Exception as exc2:
                r = dict(resultado_vacio, error=f"PVGIS no respondió (reintento): {exc2}")
                if usar_cache:
                    _guardar_cache_variabilidad(lat, lon, anios_atras, r)
                return r
        else:
            r = dict(resultado_vacio, error=f"PVGIS no respondió: {exc}")
            if usar_cache:
                _guardar_cache_variabilidad(lat, lon, anios_atras, r)
            return r

    if df is None or df.empty:
        r = dict(resultado_vacio, error="PVGIS devolvió una serie vacía para esta ubicación")
        return r

    ghi = df["poa_direct"] + df["poa_sky_diffuse"] + df["poa_ground_diffuse"]
    ghi_anual_wh = ghi.groupby(ghi.index.year).sum()

    # Solo años CALENDARIO completos (8760 u 8784 en bisiesto) -- un año
    # parcial al inicio/fin de la serie descargada distorsionaría la
    # desviación estándar sin avisar. Tolerancia de 24h por husos horarios
    # de la serie (viene en UTC).
    horas_por_anio = ghi.groupby(ghi.index.year).size()
    anios_completos = [
        a for a in ghi_anual_wh.index
        if horas_por_anio.get(a, 0) >= 8759  # 8760 (u 8784 bisiesto) - 1h de margen
    ]

    if len(anios_completos) < MIN_ANIOS_VALIDOS:
        r = dict(
            resultado_vacio,
            error=(
                f"Solo {len(anios_completos)} año(s) completo(s) disponibles "
                f"(se requieren ≥{MIN_ANIOS_VALIDOS}) -- desviación estándar no confiable"
            ),
        )
        if usar_cache:
            _guardar_cache_variabilidad(lat, lon, anios_atras, r)
        return r

    ghi_anual_kwh = {a: round(float(ghi_anual_wh[a]) / 1000.0, 1) for a in anios_completos}
    valores = np.array(list(ghi_anual_kwh.values()))
    media = float(valores.mean())
    sigma_pct = float(valores.std(ddof=1) / media * 100.0) if media > 0 else None

    raddb = None
    if isinstance(inputs, dict):
        raddb = inputs.get("meteo_data", {}).get("radiation_db")

    resultado = {
        "sigma_irr_real_pct": round(sigma_pct, 2) if sigma_pct is not None else None,
        "n_anios": len(anios_completos),
        "anio_inicio": min(anios_completos),
        "anio_fin": max(anios_completos),
        "media_kwh_m2_anio": round(media, 1),
        "raddatabase": raddb,
        "anios_detalle": ghi_anual_kwh,
        "error": None,
    }
    if usar_cache:
        _guardar_cache_variabilidad(lat, lon, anios_atras, resultado)
    return resultado


def elegir_sigma_irr(sigma_tabla_pct: float, resultado_real: dict) -> dict:
    """
    Regla de combinación entre el σ_irr de tabla (existente, por ciudad) y
    el σ_irr real calculado con datos (esta función) -- NUNCA se usa
    silenciosamente el valor MÁS BAJO de los dos.

    Si el real es mayor que la tabla (el sitio es más variable de lo
    asumido): se usa el real -- más protector, más honesto para el banco.
    Si el real es menor que la tabla (como Urabá: 2,85% real vs. 6,5% de
    tabla, verificado 7-sep-2026): la tabla sigue mandando -- un banco
    exigente sería escéptico de un σ "sorprendentemente bajo" controlado
    por el desarrollador del proyecto sin más escrutinio independiente.
    Sin dato real disponible: cae a la tabla sola, comportamiento histórico.

    Retorna {"sigma_irr_usado_pct", "fuente_usada" ("tabla"|"real"),
    "sigma_tabla_pct", "sigma_real_pct"} -- ambos valores siempre expuestos
    para que la página los muestre lado a lado, nunca se oculta ninguno.
    """
    sigma_real = resultado_real.get("sigma_irr_real_pct")
    if sigma_real is None:
        return {
            "sigma_irr_usado_pct": sigma_tabla_pct,
            "fuente_usada": "tabla",
            "sigma_tabla_pct": sigma_tabla_pct,
            "sigma_real_pct": None,
        }
    usado = max(sigma_tabla_pct, sigma_real)
    return {
        "sigma_irr_usado_pct": usado,
        "fuente_usada": "real" if sigma_real >= sigma_tabla_pct else "tabla",
        "sigma_tabla_pct": sigma_tabla_pct,
        "sigma_real_pct": sigma_real,
    }
