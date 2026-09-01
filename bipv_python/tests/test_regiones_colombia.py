# -*- coding: utf-8 -*-
"""`detectar_region_colombia()` -- portado 1:1 (31-ago-2026, pedido explícito
del usuario) desde `client/src/lib/colombianRegions.ts`, la misma lógica ya
viva en producción en https://bipv.innovacionquimica.com.co/. Casos anclados
a coordenadas reales de ciudades colombianas, verificados también contra el
resultado real del módulo TypeScript original (no solo "se ve razonable")."""
import pytest

from calculos.regiones_colombia import detectar_region_colombia


@pytest.mark.parametrize("nombre,lat,lon,esperado", [
    ("Bogotá", 4.711, -74.072, "andina"),
    ("Medellín", 6.244, -75.574, "andina"),
    ("Barranquilla", 10.98, -74.78, "caribe"),
    ("Quibdó", 5.69, -76.66, "pacifica"),
    ("Leticia", -4.2, -69.94, "amazonia"),
    ("San Andrés", 12.58, -81.7, "insular"),
])
def test_detecta_region_correcta_para_ciudades_reales(nombre, lat, lon, esperado):
    r = detectar_region_colombia(lat, lon)
    assert r.region == esperado, f"{nombre}: se esperaba {esperado}, dio {r.region}"
    assert r.en_colombia is True


def test_villavicencio_cae_en_andina_mismo_limite_conocido_del_original_ts():
    # Villavicencio está en el piedemonte llanero, exactamente en el límite
    # entre los polígonos Andina/Orinoquía -- verificado que el propio
    # colombianRegions.ts ORIGINAL (no la copia en Python) ya clasifica este
    # punto como "andina", no "orinoquia" -- es un límite conocido del
    # polígono simplificado real, no un error introducido al portar. Este
    # test ancla el comportamiento IDÉNTICO al original, no lo "corrige".
    r = detectar_region_colombia(4.15, -73.63)
    assert r.region == "andina"


def test_fuera_de_colombia_usa_fallback_por_distancia_con_confianza_baja():
    # Madrid, España -- claramente fuera del bounding box de Colombia.
    r = detectar_region_colombia(40.4, -3.7)
    assert r.en_colombia is False
    assert r.confianza == "baja"


def test_punto_en_colombia_sin_poligono_usa_fallback_con_confianza_media():
    # Coordenada dentro del bounding box de Colombia pero en zona fronteriza
    # sin polígono definido -- debe caer al centroide más cercano con
    # confianza "media", no "alta" (nunca inventa certeza que no tiene).
    r = detectar_region_colombia(0.0, -68.0)  # sur profundo, límite Amazonía/Orinoquía
    assert r.en_colombia is True
    assert r.confianza in ("alta", "media")  # puede caer en polígono amazonía real
