# -*- coding: utf-8 -*-
"""Puntos de análisis automáticos, uno por módulo (Spec
05-perdidas-y-temperatura/puntos-automaticos-por-modulo, 3-oct-2026).

Geometría (marco de la escena: X = Este, Y = Norte, Z = arriba, metros):

* ``n``: normal exterior del módulo, la misma de ``sombras_3d`` (elevación
  90° − tilt, azimut de la superficie).
* ``u``: dirección horizontal del plano, hacia la derecha de quien mira la
  superficie desde afuera: (sen(az − 90°), cos(az − 90°), 0).
* ``v = n × u``: dirección cuesta arriba en el plano (vertical en una
  fachada).

``esquina`` es la esquina inferior izquierda del campo de módulos, vista
desde afuera, sobre el plano de los módulos. El centro del módulo de la fila
``r`` y la columna ``c`` (desde 0) es::

    esquina + u·(c·(w + sh) + w/2) + v·(r·(h + sv) + h/2) + n·d

con ``w``, ``h`` el ancho y el alto del módulo en el plano, ``sh``, ``sv``
las separaciones entre módulos y ``d`` la separación del punto al plano.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np

SEPARACION_FACHADA_M = 0.30
# validar_puntos avisa por debajo de 2 × OFFSET_RAYO_M (0,10 m): un punto más
# cerca nace casi dentro del obstáculo.
SEPARACION_MIN_M = 0.10
_LADO_MIN_M, _LADO_MAX_M = 0.2, 3.5


def vectores_superficie(tilt_deg: float, azimuth_deg: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(n, u, v) unitarios y ortogonales de la superficie."""
    tilt, az = math.radians(float(tilt_deg)), math.radians(float(azimuth_deg))
    elev = math.pi / 2 - tilt
    n = np.array([math.sin(az) * math.cos(elev), math.cos(az) * math.cos(elev), math.sin(elev)])
    u = np.array([math.sin(az - math.pi / 2), math.cos(az - math.pi / 2), 0.0])
    v = np.cross(n, u)
    return n / np.linalg.norm(n), u / np.linalg.norm(u), v / np.linalg.norm(v)


def _orden_cableado(filas: int, columnas: int, cableado: str) -> list[tuple[int, int]]:
    if cableado == "columnas":
        return [(r, c) for c in range(columnas) for r in range(filas)]
    if cableado == "filas":
        return [(r, c) for r in range(filas) for c in range(columnas)]
    raise ValueError(f"cableado debe ser «columnas» o «filas», no «{cableado}».")


def _strings(grupos: Sequence[Mapping[str, Any]] | None, total: int) -> list[str | None]:
    if not grupos:
        return [None] * total
    etiquetas: list[str] = []
    for g in grupos:
        n_serie, n_par = int(g.get("n_serie") or 0), int(g.get("n_paralelo") or 0)
        if n_serie < 1 or n_par < 1:
            raise ValueError(f"El grupo {g.get('gid')} necesita módulos en serie y strings en paralelo.")
        for s in range(1, n_par + 1):
            etiquetas += [f"{g.get('gid', 'G1')}-S{s}"] * n_serie
    if len(etiquetas) != total:
        raise ValueError(
            f"El campo tiene {total} módulos y los grupos de strings suman {len(etiquetas)}: "
            "ajusta filas × columnas o los módulos en serie × strings en paralelo.")
    return etiquetas


def _offsets_columnas(columnas: int, w: float, sh: float,
                      posiciones: Sequence[float] | None) -> list[float]:
    """Distancia de la esquina al borde izquierdo de cada columna."""
    if posiciones is None:
        return [c * (w + sh) for c in range(columnas)]
    pos = [float(x) for x in posiciones]
    if len(pos) != columnas:
        raise ValueError(f"Hay {len(pos)} posiciones de columna y el campo tiene {columnas} columnas: "
                         "escribe una posición por columna.")
    if not all(math.isfinite(x) for x in pos):
        raise ValueError("Las posiciones de columna deben ser números en metros.")
    if pos[0] < 0:
        raise ValueError("La primera posición de columna no puede ser negativa: se mide desde la esquina.")
    for a, b in zip(pos, pos[1:]):
        if b < a:
            raise ValueError("Escribe las posiciones de columna en orden, de izquierda a derecha.")
        if b - a < w - 1e-9:
            raise ValueError(f"Las columnas en {a:g} m y {b:g} m se solapan: deben estar separadas al menos "
                             f"el ancho del módulo ({w:.3f} m).")
    return pos


def parsear_posiciones(texto: str | None) -> list[float] | None:
    """«0; 1,1; 3,43» o «0 1.1 3.43» → [0.0, 1.1, 3.43]. Vacío → None.

    Separadores: punto y coma o espacios; la coma es decimal."""
    if texto is None or not str(texto).strip():
        return None
    partes = [t for t in str(texto).replace(";", " ").split() if t]
    valores = []
    for t in partes:
        try:
            valores.append(float(t.replace(",", ".")))
        except ValueError:
            raise ValueError(f"«{t}» no es un número: separa las posiciones con «;» "
                             "(por ejemplo 0; 1,1; 3,43).") from None
    return valores


def generar_puntos_modulos(
    nombre_superficie: str,
    tilt_deg: float,
    azimuth_deg: float,
    esquina: Sequence[float],
    filas: int,
    columnas: int,
    largo_m: float,
    ancho_m: float,
    orientacion: str = "vertical",
    separacion_h_m: float = 0.02,
    separacion_v_m: float = 0.02,
    separacion_fachada_m: float = SEPARACION_FACHADA_M,
    grupos: Sequence[Mapping[str, Any]] | None = None,
    cableado: str = "columnas",
    posiciones_columnas_m: Sequence[float] | None = None,
) -> list[dict]:
    """Un punto por módulo, con fila, columna, string y posición en el string.

    ``posiciones_columnas_m`` (Spec 05/columnas-a-medida): distancia, sobre
    ``u``, desde la esquina hasta el borde izquierdo de cada columna, vista
    desde afuera. Si se da, reemplaza la separación horizontal regular.
    """
    filas, columnas = int(filas), int(columnas)
    if filas < 1 or columnas < 1:
        raise ValueError("El campo necesita al menos 1 en filas y 1 en columnas de módulos.")
    for lado in (largo_m, ancho_m):
        if not (_LADO_MIN_M <= float(lado) <= _LADO_MAX_M):
            raise ValueError("Las medidas del módulo van en metros (por ejemplo 1.69 × 1.046).")
    if float(separacion_fachada_m) < SEPARACION_MIN_M:
        raise ValueError("La separación del punto a la superficie debe ser de al menos 0,10 m.")
    if min(float(separacion_h_m), float(separacion_v_m)) < 0:
        raise ValueError("Las separaciones entre módulos no pueden ser negativas.")
    if orientacion == "vertical":
        w, h = float(ancho_m), float(largo_m)
    elif orientacion == "horizontal":
        w, h = float(largo_m), float(ancho_m)
    else:
        raise ValueError("La orientación del módulo debe ser «vertical» u «horizontal».")
    offsets = _offsets_columnas(columnas, w, float(separacion_h_m), posiciones_columnas_m)
    orden = _orden_cableado(filas, columnas, cableado)
    etiquetas = _strings(grupos, filas * columnas)
    n, u, v = vectores_superficie(tilt_deg, azimuth_deg)
    e = np.asarray(esquina, dtype=float)
    if e.shape != (3,) or not np.isfinite(e).all():
        raise ValueError("La esquina del campo necesita 3 coordenadas x, y, z en metros.")
    posiciones: dict[str, int] = {}
    puntos = []
    for (r, c), etiqueta in zip(orden, etiquetas):
        p = (e + u * (offsets[c] + w / 2)
             + v * (r * (h + float(separacion_v_m)) + h / 2) + n * float(separacion_fachada_m))
        punto = {"nombre": f"{nombre_superficie}-F{r + 1:02d}-C{c + 1:02d}", "fachada": nombre_superficie,
                 "x": float(p[0]), "y": float(p[1]), "z": float(p[2]), "fila": r + 1, "columna": c + 1,
                 "tilt_deg": float(tilt_deg), "azimuth_deg": float(azimuth_deg)}
        if etiqueta is not None:
            posiciones[etiqueta] = posiciones.get(etiqueta, 0) + 1
            punto.update(string=etiqueta, posicion=posiciones[etiqueta])
        puntos.append(punto)
    return puntos


def _mm(valor: float) -> str:
    return f"{round(float(valor), 3) + 0.0:.3f}"


def texto_puntos(puntos: Sequence[Mapping[str, Any]]) -> str:
    """Texto x,y,z (metros, al milímetro) para el cuadro de puntos 3D."""
    return "\n".join(f"{_mm(p['x'])},{_mm(p['y'])},{_mm(p['z'])}" for p in puntos)


def etiquetar_strings(puntos: Sequence[Mapping[str, Any]], texto_actual: str,
                      meta: Mapping[str, Any] | None) -> list[dict]:
    """Añade ``string`` a cada punto si el texto es exactamente el generado.

    Si el usuario editó el texto, la correspondencia punto ↔ string ya no es
    segura y no se añade nada (la sombra se calcula por superficie)."""
    salida = [dict(p) for p in puntos]
    if not meta or meta.get("texto") != texto_actual:
        return salida
    strings = list(meta.get("strings") or [])
    if len(strings) != len(salida) or any(s is None for s in strings):
        return salida
    for p, s in zip(salida, strings):
        p["string"] = s
    return salida
