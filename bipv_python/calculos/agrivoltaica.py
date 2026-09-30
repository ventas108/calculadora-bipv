# -*- coding: utf-8 -*-
"""🌱 Agrivoltaica: luz que llega al cultivo y paso de la maquinaria.

Spec ``03-dimensionamiento/granja-agrivoltaica`` (granja FV fase 3,
30-sep-2026). Corte de perfil entre dos filas infinitas (misma hipótesis que
``pvlib.bifacial.infinite_sheds``), suelo plano:

- Luz directa: un punto del suelo recibe la directa horizontal
  (``G_h − Gd_h``) si no cae en la sombra de ninguna fila. La sombra de una
  mesa en el suelo va de ``h0·tanφ`` a ``huella + (h0 + Δz)·tanφ`` (medido
  desde el borde inferior de la mesa), con ``tanφ = cos(az_sol − az_panel) ·
  tan(cenit)``, y se repite cada separación entre filas.
- Luz difusa: difusa horizontal × fracción de cielo que ve el punto
  (factor de vista 2D; se descuenta el ángulo que tapa cada fila).
- No se suma la luz que reflejan el suelo y la cara inferior de los paneles
  (resultado del lado seguro, unos pocos %).

Posición ``y`` (m): 0 = borde inferior (frente) de una mesa; la mesa ocupa
``0 … huella`` y la siguiente empieza en la separación entre filas.

Módulo puro: sin Streamlit.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

N_PUNTOS = 60
MAX_FILAS_VISTA = 30
CENIT_MAX_DEG = 88.0
ALTURA_CATEGORIA_I_M = 2.10     # DIN SPEC 91434: cultivo bajo los paneles
HOLGURA_VERTICAL_M = 0.30
HOLGURA_LATERAL_M = 0.25        # por cada lado de la máquina


def geometria_corte(campo: Mapping[str, Any]) -> dict:
    """Medidas del corte de perfil (m) desde el resultado de ``calcular_campo``."""
    dz = float(campo["elevacion_m"])
    return {"pitch": float(campo["ancho_mesa_m"]) / float(campo["gcr"]),
            "huella": float(campo["huella_ns_m"]), "dz": dz,
            "h0": float(campo["altura_superior_m"]) - dz,
            "tilt": float(campo["tilt_deg"]), "azimut": float(campo["azimut_deg"])}


def puntos_suelo(pitch: float, n: int = N_PUNTOS) -> np.ndarray:
    """Centros de ``n`` franjas iguales entre el frente de una mesa y el de la siguiente."""
    return (np.arange(n) + 0.5) * float(pitch) / n


def vista_cielo_suelo(y, pitch: float, huella: float, h0: float, dz: float,
                      max_filas: int = MAX_FILAS_VISTA) -> np.ndarray:
    """Fracción del cielo (difusa isotrópica) que ve cada punto del suelo.

    En 2D, un sector de cielo entre los ángulos α₁ y α₂ (medidos desde el
    suelo hacia atrás) vale (cos α₁ − cos α₂) ÷ 2 para una superficie
    horizontal; el cielo completo vale 1. Se restan los sectores que tapan
    las filas (unión de intervalos, sin contar dos veces).
    """
    y = np.atleast_1d(np.asarray(y, dtype=float))
    k = np.arange(-max_filas, max_filas + 1)
    salida = np.empty(len(y))
    for i, yi in enumerate(y):
        a1 = np.arctan2(h0, k * pitch - yi)
        a2 = np.arctan2(h0 + dz, k * pitch + huella - yi)
        tramos = sorted(zip(np.minimum(a1, a2), np.maximum(a1, a2)))
        tapado, fin = 0.0, -1.0
        for lo, hi in tramos:
            lo = max(lo, fin)
            if hi > lo:
                tapado += (math.cos(lo) - math.cos(hi)) / 2.0
                fin = hi
        salida[i] = 1.0 - tapado
    return salida


def sol_en_el_suelo(y, pitch: float, huella: float, h0: float, dz: float, tan_phi) -> np.ndarray:
    """1 si el punto recibe sol directo, 0 si está en la sombra de una fila. Forma (horas, puntos)."""
    y = np.atleast_1d(np.asarray(y, dtype=float))[np.newaxis, :]
    t = np.atleast_1d(np.asarray(tan_phi, dtype=float))[:, np.newaxis]
    a = h0 * t
    b = huella + (h0 + dz) * t
    lo, ancho = np.minimum(a, b), np.abs(b - a)
    sombra = (np.mod(y - lo, pitch) <= ancho) | (ancho >= pitch)
    return (~sombra).astype(float)


def luz_en_el_suelo(tmy: pd.DataFrame, lat: float, lon: float, alt_m: float,
                    campo: Mapping[str, Any], n: int = N_PUNTOS) -> dict:
    """Luz anual y mensual que llega al suelo entre dos filas, frente a campo abierto."""
    import pvlib

    g = geometria_corte(campo)
    y = puntos_suelo(g["pitch"], n)
    sp = pvlib.location.Location(lat, lon, altitude=alt_m).get_solarposition(tmy.index)
    cenit = sp["apparent_zenith"].to_numpy(dtype=float)
    dia = cenit < CENIT_MAX_DEG
    ghi = np.clip(tmy["G_h"].to_numpy(dtype=float), 0.0, None)
    dhi = np.clip(tmy["Gd_h"].to_numpy(dtype=float), 0.0, None)
    directa = np.where(dia, np.clip(ghi - dhi, 0.0, None), 0.0)
    tan_phi = np.where(dia, np.cos(np.radians(sp["azimuth"].to_numpy(dtype=float) - g["azimut"]))
                       * np.tan(np.radians(np.minimum(cenit, CENIT_MAX_DEG))), 0.0)

    vf = vista_cielo_suelo(y, g["pitch"], g["huella"], g["h0"], g["dz"])
    sol = sol_en_el_suelo(y, g["pitch"], g["huella"], g["h0"], g["dz"], tan_phi)
    horaria = directa[:, None] * sol + dhi[:, None] * vf[None, :]      # W/m² por punto

    ref = float(ghi.sum()) / 1000.0
    anual = horaria.sum(axis=0) / 1000.0
    pct = 100.0 * anual / ref if ref > 0 else np.zeros_like(anual)
    meses = tmy.index.month.to_numpy()
    mensual_pct, mensual_ref = [], []
    for m in range(1, 13):
        sel = meses == m
        r = float(ghi[sel].sum()) / 1000.0
        mensual_ref.append(r)
        mensual_pct.append([round(100.0 * v / r, 2) if r > 0 else 0.0
                            for v in horaria[sel].sum(axis=0) / 1000.0])
    bajo = y <= g["huella"]
    return {
        "y_m": [round(float(v), 4) for v in y],
        "anual_kwh_m2": [round(float(v), 2) for v in anual],
        "pct": [round(float(v), 2) for v in pct],
        "vista_cielo": [round(float(v), 4) for v in vf],
        "referencia_kwh_m2": round(ref, 2),
        "media_kwh_m2": round(float(anual.mean()), 2),
        "media_pct": round(float(pct.mean()), 2),
        "bajo_mesa_pct": round(float(pct[bajo].mean()), 2) if bajo.any() else None,
        "entre_filas_pct": round(float(pct[~bajo].mean()), 2) if (~bajo).any() else None,
        "min_pct": round(float(pct.min()), 2),
        "max_pct": round(float(pct.max()), 2),
        "homogeneidad": round(float(pct.min() / pct.max()), 3) if pct.max() > 0 else 0.0,
        "mensual_pct": mensual_pct,
        "mensual_referencia_kwh_m2": [round(v, 2) for v in mensual_ref],
        "geometria": {k: round(v, 4) for k, v in g.items()},
    }


def paso_maquinaria(campo: Mapping[str, Any], altura_maquina_m: float, ancho_maquina_m: float) -> list[dict]:
    """Altura libre y corredor frente a la maquinaria: ``[{id, nivel, texto}]``."""
    g = geometria_corte(campo)
    h0, corredor = g["h0"], float(campo["corredor_m"])
    out = []
    if h0 >= ALTURA_CATEGORIA_I_M:
        out.append({"id": "categoria", "nivel": "🟢", "texto":
                    f"Altura libre {h0:.2f} m ≥ {ALTURA_CATEGORIA_I_M:.2f} m: agrivoltaica **categoría I** "
                    "(se puede cultivar debajo de los paneles)."})
    else:
        out.append({"id": "categoria", "nivel": "🟡", "texto":
                    f"Altura libre {h0:.2f} m < {ALTURA_CATEGORIA_I_M:.2f} m: agrivoltaica **categoría II** "
                    "(el cultivo va entre las filas; debajo de las mesas solo pasto o nada)."})
    necesita_h = float(altura_maquina_m) + HOLGURA_VERTICAL_M
    pasa_bajo = h0 >= necesita_h
    out.append({"id": "maquinaria_bajo", "nivel": "🟢" if pasa_bajo else "🟠", "texto": (
        f"Una máquina de {altura_maquina_m:.2f} m de alto pasa bajo las mesas con "
        f"{h0 - altura_maquina_m:.2f} m de holgura." if pasa_bajo else
        f"Una máquina de {altura_maquina_m:.2f} m de alto **no pasa** bajo las mesas: la altura libre es "
        f"{h0:.2f} m y se necesitan al menos {necesita_h:.2f} m ({HOLGURA_VERTICAL_M:.2f} m de holgura). "
        "Sube la altura libre o trabaja solo por el corredor.")})
    necesita_a = float(ancho_maquina_m) + 2 * HOLGURA_LATERAL_M
    pasa_entre = corredor >= necesita_a
    out.append({"id": "maquinaria_entre", "nivel": "🟢" if (pasa_entre or pasa_bajo) else "🟠", "texto": (
        f"El corredor libre entre filas ({corredor:.2f} m) deja pasar una máquina de "
        f"{ancho_maquina_m:.2f} m de ancho ({HOLGURA_LATERAL_M:.2f} m de holgura por lado)." if pasa_entre else
        f"El corredor libre entre filas ({corredor:.2f} m) es angosto para una máquina de "
        f"{ancho_maquina_m:.2f} m: necesita {necesita_a:.2f} m. "
        + ("Como pasa por debajo de las mesas, no es un problema." if pasa_bajo else
           "Aumenta la separación entre filas o usa una máquina más angosta."))})
    return out
