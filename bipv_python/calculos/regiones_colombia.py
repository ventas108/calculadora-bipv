# -*- coding: utf-8 -*-
"""Detección de región climática colombiana por coordenadas geográficas.

Portado 1:1 (31-ago-2026, pedido explícito del usuario) desde
`client/src/lib/colombianRegions.ts` — la misma lógica ya viva en producción
en https://bipv.innovacionquimica.com.co/ (otra app del mismo repositorio).
Polígonos simplificados basados en límites geográficos reconocidos por el
IDEAM y el IGAC — no se reinventan, se traducen del TypeScript original.

Colombia se divide en 6 regiones naturales:
- Caribe: costa norte, tierras bajas < 200 m.
- Andina: cordilleras, altiplanos, valles interandinos, elevaciones > 500 m.
- Pacífica: costa occidental, selva húmeda tropical.
- Orinoquía: llanos orientales, sabanas.
- Amazonía: selva amazónica sur-oriental.
- Insular: San Andrés y Providencia.
"""
from dataclasses import dataclass

Punto = tuple[float, float]      # (lat, lon)
Poligono = list[Punto]


@dataclass(frozen=True)
class _DefinicionRegion:
    clave: str
    etiqueta: str
    ciudades: str
    poligono: Poligono


@dataclass(frozen=True)
class ResultadoDeteccionRegion:
    region: str
    etiqueta: str
    confianza: str          # "alta" | "media" | "baja"
    en_colombia: bool
    ciudades_cercanas: str


def _punto_en_poligono(punto: Punto, poligono: Poligono) -> bool:
    """Algoritmo ray-casting -- idéntico al de colombianRegions.ts."""
    y, x = punto
    dentro = False
    n = len(poligono)
    j = n - 1
    for i in range(n):
        yi, xi = poligono[i]
        yj, xj = poligono[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            dentro = not dentro
        j = i
    return dentro


# Polígonos simplificados de las regiones colombianas (lat, lon) -- IGAC.
_POLIGONOS_REGION: list[_DefinicionRegion] = [
    _DefinicionRegion(
        "insular", "Insular", "San Andrés, Providencia",
        [(14.0, -82.0), (14.0, -81.0), (12.0, -81.0), (12.0, -82.0)],
    ),
    _DefinicionRegion(
        "caribe", "Caribe",
        "Barranquilla, Cartagena, Santa Marta, Valledupar, Montería, Sincelejo, Riohacha",
        [
            (12.6, -77.0), (12.6, -71.0), (11.0, -71.8), (10.0, -72.8),
            (9.5, -73.5), (8.5, -73.5), (8.0, -74.0), (7.5, -74.8),
            (7.8, -75.5), (8.0, -76.0), (8.5, -76.5), (8.8, -76.8),
            (9.5, -76.5), (9.3, -76.0), (9.5, -75.5), (10.5, -75.5),
            (11.0, -75.0), (12.0, -75.5), (12.5, -77.0),
        ],
    ),
    _DefinicionRegion(
        "pacifica", "Pacífica", "Quibdó, Buenaventura, Tumaco",
        [
            (8.8, -76.8), (8.5, -76.5), (8.0, -76.0), (7.8, -76.5),
            (7.5, -77.0), (7.0, -77.5), (6.5, -77.5), (6.0, -77.5),
            (5.5, -77.5), (5.0, -77.5), (4.5, -77.5), (4.0, -77.8),
            (3.5, -78.0), (3.0, -78.2), (2.5, -78.5), (2.0, -78.8),
            (1.5, -79.0), (1.4, -78.5), (1.5, -78.0), (2.0, -77.5),
            (2.5, -77.0), (3.0, -76.8), (3.5, -76.5), (4.0, -76.5),
            (4.5, -76.5), (5.0, -76.5), (5.5, -76.5), (6.0, -76.3),
            (6.5, -76.5), (7.0, -76.5), (7.5, -76.5), (8.0, -76.5),
            (8.5, -76.8),
        ],
    ),
    _DefinicionRegion(
        "amazonia", "Amazonía", "Leticia, Florencia, Mocoa, Puerto Asís",
        [
            (2.5, -76.0), (2.0, -76.0), (1.5, -76.5), (1.0, -76.5),
            (0.5, -76.0), (0.0, -75.5), (-0.5, -75.0), (-1.0, -74.5),
            (-1.5, -73.5), (-2.0, -72.5), (-2.5, -71.5), (-3.0, -70.5),
            (-4.2, -70.0), (-4.2, -69.5), (-2.0, -69.5), (-1.0, -70.0),
            (0.0, -70.0), (1.0, -70.0), (2.0, -70.0), (2.5, -70.5),
            (3.0, -71.0), (3.5, -71.5), (3.5, -72.0), (3.0, -73.0),
            (2.5, -74.0), (2.0, -74.5), (2.0, -75.0), (2.5, -75.5),
        ],
    ),
    _DefinicionRegion(
        "orinoquia", "Orinoquía", "Villavicencio, Yopal, Arauca",
        [
            (7.5, -72.5), (7.0, -71.0), (6.5, -67.5), (6.0, -67.5),
            (5.0, -68.0), (4.0, -68.0), (3.5, -69.0), (3.0, -70.0),
            (2.5, -70.5), (2.0, -70.0), (2.5, -71.5), (3.0, -72.0),
            (3.5, -72.5), (4.0, -73.0), (4.5, -73.5), (5.0, -73.5),
            (5.5, -73.0), (6.0, -72.5), (6.5, -72.5), (7.0, -72.5),
        ],
    ),
    _DefinicionRegion(
        "andina", "Andina",
        "Bogotá, Medellín, Cali, Bucaramanga, Pereira, Manizales, Tunja, Ibagué",
        [
            (8.0, -76.0), (7.8, -75.5), (7.5, -74.8), (7.5, -73.5),
            (7.5, -72.5), (7.0, -72.5), (6.5, -72.5), (6.0, -72.5),
            (5.5, -73.0), (5.0, -73.5), (4.5, -73.5), (4.0, -73.0),
            (3.5, -72.5), (3.0, -73.0), (2.5, -74.0), (2.0, -75.0),
            (2.0, -76.0), (2.5, -76.0), (3.0, -76.5), (3.5, -76.5),
            (4.0, -76.5), (4.5, -76.5), (5.0, -76.5), (5.5, -76.5),
            (6.0, -76.3), (6.5, -76.5), (7.0, -76.5), (7.5, -76.5),
        ],
    ),
]

# Centroides aproximados por región, para el fallback por distancia.
_CENTROIDES_REGION: list[dict] = [
    {"clave": "caribe", "etiqueta": "Caribe", "ciudades": "Barranquilla, Cartagena, Santa Marta", "lat": 10.4, "lon": -75.5},
    {"clave": "andina", "etiqueta": "Andina", "ciudades": "Bogotá, Medellín, Cali, Bucaramanga", "lat": 5.5, "lon": -74.5},
    {"clave": "pacifica", "etiqueta": "Pacífica", "ciudades": "Quibdó, Buenaventura, Tumaco", "lat": 4.5, "lon": -77.0},
    {"clave": "orinoquia", "etiqueta": "Orinoquía", "ciudades": "Villavicencio, Yopal, Arauca", "lat": 5.0, "lon": -71.0},
    {"clave": "amazonia", "etiqueta": "Amazonía", "ciudades": "Leticia, Florencia, Mocoa", "lat": 0.5, "lon": -73.0},
    {"clave": "insular", "etiqueta": "Insular", "ciudades": "San Andrés, Providencia", "lat": 12.5, "lon": -81.7},
]


def _region_mas_cercana(lat: float, lon: float, en_colombia: bool) -> ResultadoDeteccionRegion:
    mejor = _CENTROIDES_REGION[1]  # default: Andina
    mejor_dist = float("inf")
    for c in _CENTROIDES_REGION:
        dist = ((lat - c["lat"]) ** 2 + (lon - c["lon"]) ** 2) ** 0.5
        if dist < mejor_dist:
            mejor_dist = dist
            mejor = c
    return ResultadoDeteccionRegion(
        region=mejor["clave"], etiqueta=mejor["etiqueta"],
        confianza="media" if en_colombia else "baja",
        en_colombia=en_colombia, ciudades_cercanas=mejor["ciudades"],
    )


def detectar_region_colombia(lat: float, lon: float) -> ResultadoDeteccionRegion:
    """
    Detecta la región climática colombiana para unas coordenadas dadas.
    Primero verifica el bounding box de Colombia, luego usa los polígonos
    reales (ray-casting) para clasificar; si cae en zona fronteriza sin
    polígono, usa la región del centroide más cercano.
    """
    en_bbox = -4.3 <= lat <= 13.5 and -82.0 <= lon <= -66.8
    if not en_bbox:
        return _region_mas_cercana(lat, lon, en_colombia=False)

    for definicion in _POLIGONOS_REGION:
        if _punto_en_poligono((lat, lon), definicion.poligono):
            return ResultadoDeteccionRegion(
                region=definicion.clave, etiqueta=definicion.etiqueta,
                confianza="alta", en_colombia=True,
                ciudades_cercanas=definicion.ciudades,
            )

    return _region_mas_cercana(lat, lon, en_colombia=True)
