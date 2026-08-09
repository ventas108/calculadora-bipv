# -*- coding: utf-8 -*-
"""Tests del lector de escenas de Site Designer (Andrew Marsh) — Fase 5."""
import json

import numpy as np
import pytest

from calculos.sitedesigner_marsh import (
    ESCALA_MM_A_M,
    ErrorSiteDesigner,
    cargar_escena_sitedesigner,
    verificar_ubicacion,
)


def _escena(north_offset=0, blocks=None, **loc_extra):
    loc = {"latitude": 4.702, "longitude": -74.147, "timezone": -5,
           "northOffset": north_offset, "elevation": 2548.4}
    loc.update(loc_extra)
    if blocks is None:
        blocks = [{"min": [900, 200, 0], "max": [5100, 3400, 10000]}]
    return json.dumps({"Location": loc, "Blocks": blocks})


def test_escala_mm_a_metros():
    """El bloque 4200×3200×10000 mm debe medir 4.2×3.2×10 m — nunca km."""
    malla, meta = cargar_escena_sitedesigner(_escena())
    dims = malla.bounds[1] - malla.bounds[0]
    assert np.allclose(dims, [4.2, 3.2, 10.0], atol=1e-6)
    assert meta["dim_m"] == {"x": 4.2, "y": 3.2, "z": 10.0}
    assert meta["n_bloques"] == 1
    assert meta["fuente"] == "externa_marsh"
    assert ESCALA_MM_A_M == 0.001


def test_metadata_ubicacion():
    _, meta = cargar_escena_sitedesigner(_escena())
    assert meta["lat"] == pytest.approx(4.702)
    assert meta["lon"] == pytest.approx(-74.147)
    assert meta["timezone"] == -5
    assert meta["elevacion_m"] == pytest.approx(2548.4)


def test_north_offset_rota_la_malla():
    """northOffset=90 (horario) debe llevar un bloque al este del origen hacia el sur."""
    bloque = [{"min": [1000, -500, 0], "max": [2000, 500, 3000]}]  # centrado en +X (este)
    sin_giro, _ = cargar_escena_sitedesigner(_escena(0, bloque))
    con_giro, meta = cargar_escena_sitedesigner(_escena(90, bloque))
    assert meta["north_offset_deg"] == 90
    c0 = sin_giro.bounds.mean(axis=0)
    c1 = con_giro.bounds.mean(axis=0)
    assert np.allclose(c0[:2], [1.5, 0.0], atol=1e-6)
    # giro horario -90° alrededor de Z (misma convención que cargar_malla):
    # (x, y) → (-y... ) verificamos numéricamente contra la matriz usada
    ang = -np.deg2rad(90.0)
    esperado = [c0[0] * np.cos(ang) - c0[1] * np.sin(ang),
                c0[0] * np.sin(ang) + c0[1] * np.cos(ang)]
    assert np.allclose(c1[:2], esperado, atol=1e-6)
    assert c1[2] == pytest.approx(c0[2])


def test_identidad_de_obstaculos_por_cara():
    blocks = [
        {"min": [0, 0, 0], "max": [1000, 1000, 1000]},
        {"min": [3000, 0, 0], "max": [4000, 1000, 2000]},
    ]
    malla, meta = cargar_escena_sitedesigner(_escena(0, blocks))
    ids = set(malla._bipv_obstacle_id_by_face.tolist())
    assert ids == {"bloque-1", "bloque-2"}
    assert len(malla._bipv_obstacle_id_by_face) == malla.faces.shape[0]
    assert meta["n_bloques"] == 2


def test_rechaza_sin_blocks():
    with pytest.raises(ErrorSiteDesigner, match="Blocks"):
        cargar_escena_sitedesigner(_escena(0, []))


def test_rechaza_bloque_degenerado():
    with pytest.raises(ErrorSiteDesigner, match="degenerado"):
        cargar_escena_sitedesigner(
            _escena(0, [{"min": [0, 0, 0], "max": [1000, 1000, 0]}]))


def test_rechaza_json_invalido_y_sin_location():
    with pytest.raises(ErrorSiteDesigner, match="JSON"):
        cargar_escena_sitedesigner(b"esto no es json")
    with pytest.raises(ErrorSiteDesigner, match="Location"):
        cargar_escena_sitedesigner(json.dumps({"Blocks": [{"min": [0, 0, 0], "max": [1, 1, 1]}]}))


def test_rechaza_escena_gigante():
    """Un archivo que tras mm→m siga midiendo >5 km no es un export normal."""
    with pytest.raises(ErrorSiteDesigner, match="milímetros"):
        cargar_escena_sitedesigner(
            _escena(0, [{"min": [0, 0, 0], "max": [6_000_000_000, 1000, 1000]}]))


def test_rechaza_north_offset_faltante_o_invalido():
    """northOffset es física, no cosmética: nunca asumir 0 en silencio."""
    esc = json.loads(_escena())
    del esc["Location"]["northOffset"]
    with pytest.raises(ErrorSiteDesigner, match="northOffset"):
        cargar_escena_sitedesigner(json.dumps(esc))
    with pytest.raises(ErrorSiteDesigner, match="northOffset"):
        cargar_escena_sitedesigner(_escena(north_offset=None))
    with pytest.raises(ErrorSiteDesigner, match="northOffset"):
        cargar_escena_sitedesigner(_escena(north_offset=float("nan")))
    with pytest.raises(ErrorSiteDesigner, match="northOffset"):
        cargar_escena_sitedesigner(_escena(north_offset=720))


def test_rechaza_demasiados_bloques():
    from calculos.sitedesigner_marsh import MAX_BLOQUES
    blocks = [{"min": [i * 2000, 0, 0], "max": [i * 2000 + 1000, 1000, 1000]}
              for i in range(MAX_BLOQUES + 1)]
    with pytest.raises(ErrorSiteDesigner, match="bloques"):
        cargar_escena_sitedesigner(_escena(0, blocks))


def test_integracion_lector_a_fs_y_csv():
    """End-to-end: escena Site Designer → calcular_fs_horario → CSV."""
    from calculos.sombras_3d import calcular_fs_horario, exportar_csv_fs
    # muro alto justo al ESTE del punto → sombra en horas de la mañana
    muro = [{"min": [2000, -10000, 0], "max": [3000, 10000, 30000]}]
    malla, meta = cargar_escena_sitedesigner(_escena(0, muro))
    puntos = [{"nombre": "P1", "fachada": "Norte", "fila": "Fila 1",
               "n_modulos": 1, "area_activa_m2": 0.0, "potencia_instalada_kw": 0.0,
               "x": 0.0, "y": 0.0, "z": 1.0}]
    df = calcular_fs_horario(malla, puntos, meta["lat"], meta["lon"])
    assert not df.empty
    assert df["FS_geometrico"].between(0, 1).all()
    assert df["FS_geometrico"].max() == 1.0  # el muro sí sombrea
    csv = exportar_csv_fs(df)
    cab = csv.decode("utf-8-sig").splitlines()[0]
    assert "FS_geometrico" in cab and "Punto" in cab


def test_verificar_ubicacion():
    _, meta = cargar_escena_sitedesigner(_escena())
    assert verificar_ubicacion(meta, 4.702, -74.147) == []
    avisos = verificar_ubicacion(meta, 6.25, -75.57)  # Medellín ≠ Bogotá
    assert len(avisos) == 1 and "NO coincide" in avisos[0]


def test_acepta_bytes_utf8_sig():
    contenido = _escena().encode("utf-8-sig")
    malla, _ = cargar_escena_sitedesigner(contenido)
    assert malla.faces.shape[0] > 0


def test_archivo_real_de_ejemplo():
    """Los JSON reales subidos por el usuario deben cargar sin errores."""
    import glob
    import os
    ejemplos = sorted(glob.glob(os.path.join(
        os.path.dirname(__file__), "..", "..", "attached_assets", "site-designer-*.json")))
    if not ejemplos:
        pytest.skip("sin archivos de ejemplo en este entorno")
    for ruta in ejemplos:
        with open(ruta, "rb") as f:
            malla, meta = cargar_escena_sitedesigner(f.read())
        assert malla.faces.shape[0] > 0
        assert -90 <= meta["lat"] <= 90
