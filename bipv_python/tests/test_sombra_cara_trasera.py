"""Spec 05/sombra-cara-trasera: el ray-casting no puede marcar sombra cuando
el sol está detrás del plano del módulo.

Con el sol detrás del plano (sol · normal <= 0) el haz directo sobre el
módulo ya es cero por el ángulo de incidencia; un rayo hacia el sol desde
la fachada solo puede chocar con el propio edificio o con algo situado
detrás. Antes de esta Spec esas horas salían con FS_geometrico = 1 y el
bypass recortaba con ellas la irradiancia difusa real.

Evidencia y criterios: CodeSpecs/05-perdidas-y-temperatura/sombra-cara-trasera/.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

trimesh = pytest.importorskip("trimesh")

import calculos.sombras_3d as sombras_3d
from calculos.contrato_sombreado import CONTRACT_VERSION, validar_solicitud
from calculos.produccion_vigencia import huella_horaria
from calculos.sitedesigner_marsh import cargar_escena_sitedesigner
from calculos.sombras_3d import (
    VERSION_ALGORITMO_FS_POR_SUPERFICIE,
    calcular_fs_horario,
    calcular_fs_horario_por_superficie,
    posiciones_solares,
    vector_al_sol,
)
from calculos.vinculador_sombra_multisuperficie import (
    invalidar_sombra_por_version_algoritmo,
)

_HORAS_ANIO = 8760
_LAT_TORRE5, _LON_TORRE5 = 4.634, -74.148
_ESCENA_CIERRE = (
    Path(__file__).resolve().parents[2]
    / "attached_assets"
    / "site-designer-2026-07-14-1606-10_1786198985402.json"
)


def _idx_anual():
    return pd.date_range("2023-01-01", periods=_HORAS_ANIO, freq="h", tz="UTC")


def _tmy():
    idx = _idx_anual()
    t2m = 20.0 + 5.0 * np.sin((idx.hour.to_numpy() - 6) / 24.0 * 2 * np.pi)
    return pd.DataFrame({"T2m": t2m}, index=idx)


def _torre5():
    """Volumen provisional de Torre 5 (informe La Salle, 2026-09-22)."""
    lado, alto = 17.2905, 36.4178
    torre = trimesh.creation.box(bounds=[[-lado / 2, -lado / 2, 0.0], [lado / 2, lado / 2, alto]])
    torre.apply_transform(trimesh.transformations.rotation_matrix(-np.deg2rad(160.5), [0, 0, 1]))
    return torre, alto


def _puntos_en_caras(malla, z, separacion_m=0.10):
    """Un punto frente al centro de cada cara lateral, con su orientación."""
    por_cara = {}
    for centro, normal in zip(malla.triangles_center, malla.face_normals):
        if abs(normal[2]) > 0.5:
            continue
        az = round(float(np.degrees(np.arctan2(normal[0], normal[1])) % 360.0), 1)
        por_cara.setdefault(az, (normal, []))[1].append(centro)
    puntos = []
    for az, (normal, centros) in sorted(por_cara.items()):
        c = np.mean(centros, axis=0)
        c[2] = z
        p = c + normal * separacion_m
        puntos.append({
            "nombre": f"az{az:.1f}", "fachada": f"az{az:.1f}",
            "x": float(p[0]), "y": float(p[1]), "z": float(p[2]),
            "tilt_deg": 90.0, "azimuth_deg": az,
        })
    return puntos


def _sol_en(timestamp: str, lat=6.25, lon=-75.56):
    ts = pd.DatetimeIndex([timestamp])
    sol = posiciones_solares(lat, lon, ts)
    elev, az = float(sol.iloc[0]["elevacion"]), float(sol.iloc[0]["acimut"])
    return ts, elev, az, vector_al_sol(elev, az)


def _sin_orientacion(puntos):
    return [{k: v for k, v in p.items() if k not in ("tilt_deg", "azimuth_deg")} for p in puntos]


# ── Invariante: un volumen convexo no se sombrea a sí mismo ───────────────
def test_torre_convexa_aislada_no_se_autosombrea():
    torre, alto = _torre5()
    puntos = _puntos_en_caras(torre, z=alto / 2)
    assert len(puntos) == 4

    df = calcular_fs_horario(torre, puntos, _LAT_TORRE5, _LON_TORRE5, indice_tmy=_idx_anual())

    assert (df["FS_geometrico"] > 0).sum() == 0
    assert (df["FS"] > 0).sum() == 0
    # Cada cara tiene muchas horas con el sol detrás, todas neutralizadas.
    detras_por_cara = df.groupby("Punto")["sol_detras_plano"].sum()
    assert (detras_por_cara > 1000).all()


def test_sin_orientacion_conserva_comportamiento_previo_con_advertencia():
    torre, alto = _torre5()
    puntos = _puntos_en_caras(torre, z=alto / 2)
    idx = _idx_anual()

    con = calcular_fs_horario(torre, puntos, _LAT_TORRE5, _LON_TORRE5, indice_tmy=idx)
    sin = calcular_fs_horario(torre, _sin_orientacion(puntos), _LAT_TORRE5, _LON_TORRE5, indice_tmy=idx)

    # Mismas filas: una por punto y hora con sol.
    assert len(con) == len(sin)
    assert list(con["timestamp_utc"]) == list(sin["timestamp_utc"])
    # Sin orientación sigue el comportamiento anterior (autosombra falsa) ...
    assert (sin["FS_geometrico"] > 0).sum() > 8000
    assert sin["sol_detras_plano"].isna().all()
    avisos = sin.attrs.get("advertencias", [])
    assert any("orientacion_desconocida" in a for a in avisos)
    # ... y con orientación esa sombra desaparece solo en horas con sol detrás.
    assert not any("orientacion_desconocida" in a for a in con.attrs.get("advertencias", []))
    delante = ~con["sol_detras_plano"].astype(bool).to_numpy()
    assert (sin.loc[delante, "FS_geometrico"].to_numpy() == con.loc[delante, "FS_geometrico"].to_numpy()).all()
    assert (sin.loc[~delante, "FS_geometrico"] > 0).sum() == (sin["FS_geometrico"] > 0).sum()


# ── Casos de una hora: obstáculo delante y detrás ─────────────────────────
def test_obstaculo_delante_del_modulo_sigue_sombreando():
    ts, elev, az, direccion = _sol_en("2024-03-20T17:00:00Z")
    obstaculo = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
    obstaculo.apply_translation(direccion * 3.0)
    punto = {"nombre": "P1", "fachada": "F", "x": 0.0, "y": 0.0, "z": 0.0,
             "tilt_deg": 90.0 - elev, "azimuth_deg": az}  # módulo mirando al sol

    fila = calcular_fs_horario(obstaculo, [punto], 6.25, -75.56, ts).iloc[0]

    assert fila["FS_geometrico"] == 1.0
    assert bool(fila["sol_detras_plano"]) is False
    assert fila["first_hit_distance_m"] > 0


def test_obstaculo_detras_del_modulo_no_sombrea():
    ts, elev, az, direccion = _sol_en("2024-03-20T17:00:00Z")
    obstaculo = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
    obstaculo.apply_translation(direccion * 3.0)
    punto = {"nombre": "P1", "fachada": "F", "x": 0.0, "y": 0.0, "z": 0.0,
             "tilt_deg": 90.0, "azimuth_deg": (az + 180.0) % 360.0}  # de espaldas al sol

    fila = calcular_fs_horario(obstaculo, [punto], 6.25, -75.56, ts).iloc[0]

    assert fila["FS_geometrico"] == 0.0
    assert fila["FS"] == 0.0
    assert bool(fila["sol_detras_plano"]) is True
    assert fila["obstacle_id"] is None
    assert np.isnan(fila["first_hit_distance_m"])


def test_orientacion_del_punto_tiene_prioridad_sobre_la_de_la_funcion():
    ts, elev, az, direccion = _sol_en("2024-03-20T17:00:00Z")
    obstaculo = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
    obstaculo.apply_translation(direccion * 3.0)
    punto = {"nombre": "P1", "fachada": "F", "x": 0.0, "y": 0.0, "z": 0.0,
             "tilt_deg": 90.0 - elev, "azimuth_deg": az}

    fila = calcular_fs_horario(
        obstaculo, [punto], 6.25, -75.56, ts,
        tilt_deg=90.0, azimuth_deg=(az + 180.0) % 360.0,
    ).iloc[0]

    assert fila["FS_geometrico"] == 1.0
    assert bool(fila["sol_detras_plano"]) is False


def test_orientacion_de_la_funcion_aplica_a_puntos_sin_orientacion():
    ts, elev, az, direccion = _sol_en("2024-03-20T17:00:00Z")
    obstaculo = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
    obstaculo.apply_translation(direccion * 3.0)
    punto = {"nombre": "P1", "fachada": "F", "x": 0.0, "y": 0.0, "z": 0.0}

    fila = calcular_fs_horario(
        obstaculo, [punto], 6.25, -75.56, ts,
        tilt_deg=90.0, azimuth_deg=(az + 180.0) % 360.0,
    ).iloc[0]

    assert fila["FS_geometrico"] == 0.0
    assert bool(fila["sol_detras_plano"]) is True


@pytest.mark.parametrize("tilt,azimuth", [
    ("noventa", 180.0),
    (90.0, float("nan")),
    (-5.0, 180.0),
    (181.0, 180.0),
    (90.0, -1.0),
    (90.0, 361.0),
    (90.0, None),
    (None, 180.0),
])
def test_orientacion_invalida_se_rechaza(tilt, azimuth):
    ts, *_ = _sol_en("2024-03-20T17:00:00Z")
    punto = {"nombre": "P1", "fachada": "F", "x": 0.0, "y": 0.0, "z": 0.0,
             "tilt_deg": tilt, "azimuth_deg": azimuth}
    with pytest.raises(ValueError, match="P1"):
        calcular_fs_horario(trimesh.creation.box(extents=[1.0, 1.0, 1.0]), [punto], 6.25, -75.56, ts)


def test_cubierta_inclinada_filtra_solo_horas_con_sol_detras():
    # Obstáculo alto al norte de una cubierta de 10° mirando al sur.
    muro = trimesh.creation.box(bounds=[[-20.0, 3.0, 0.0], [20.0, 4.0, 30.0]])
    idx = _idx_anual()
    base = {"nombre": "C1", "fachada": "Cubierta", "x": 0.0, "y": 0.0, "z": 1.0}

    con = calcular_fs_horario(muro, [dict(base, tilt_deg=10.0, azimuth_deg=180.0)],
                              _LAT_TORRE5, _LON_TORRE5, indice_tmy=idx)
    sin = calcular_fs_horario(muro, [base], _LAT_TORRE5, _LON_TORRE5, indice_tmy=idx)

    detras = con["sol_detras_plano"].astype(bool).to_numpy()
    assert detras.any() and not detras.all()
    assert (con.loc[detras, "FS_geometrico"] == 0).all()
    assert (con.loc[~detras, "FS_geometrico"].to_numpy() == sin.loc[~detras, "FS_geometrico"].to_numpy()).all()
    # Con el sol detrás del plano de 10° el sol está bajo, al norte, y el
    # muro sí lo tapa: antes se contaba como sombra.
    assert (sin.loc[detras, "FS_geometrico"] > 0).any()


# ── Escena sintética de la prueba de cierre multisuperficie ───────────────
def _fachada_sur_cierre():
    return [
        {"nombre": f"S{i}", "fachada": "Fachada Sur", "x": 8.0, "y": 0.0, "z": z,
         "tilt_deg": 90.0, "azimuth_deg": 180.0}
        for i, z in enumerate([2.0, 3.5, 5.0, 6.5, 8.0], start=1)
    ]


def test_escena_sintetica_de_cierre_solo_conserva_sombra_real():
    malla, meta = cargar_escena_sitedesigner(_ESCENA_CIERRE.read_text(encoding="utf-8"))
    edificio = trimesh.creation.box(bounds=[[6.0, 0.10, 0.0], [10.0, 6.0, 10.0]])
    con_edificio = trimesh.util.concatenate([malla, edificio])
    puntos = _fachada_sur_cierre()

    solo_arbol = calcular_fs_horario(malla, puntos, meta["lat"], meta["lon"])
    con_muro = calcular_fs_horario(con_edificio, puntos, meta["lat"], meta["lon"])
    antes = calcular_fs_horario(malla, _sin_orientacion(puntos), meta["lat"], meta["lon"])

    assert (antes["FS_geometrico"] > 0).sum() == 4080
    assert (solo_arbol["FS_geometrico"] > 0).sum() == 678
    assert (con_muro["FS_geometrico"] > 0).sum() == 678


# ── Flujo por superficie ──────────────────────────────────────────────────
def test_por_superficie_pasa_la_orientacion_al_ray_casting():
    torre, alto = _torre5()
    cara_se = [p for p in _puntos_en_caras(torre, z=alto / 2) if p["azimuth_deg"] == 160.5]
    puntos = {"SE": [{k: v for k, v in cara_se[0].items() if k not in ("tilt_deg", "azimuth_deg")}]}
    puntos_originales = [dict(p) for p in puntos["SE"]]
    geometria = {"SE": {"tilt_deg": 90.0, "azimuth_deg": 160.5}}

    resultado = calcular_fs_horario_por_superficie(
        torre, puntos, _LAT_TORRE5, _LON_TORRE5, _tmy(), geometria,
        malla_horizonte="torre5-provisional",
    )["SE"]

    assert resultado["estado_sombra"] == sombras_3d.ESTADO_SOMBRA_CERO_CALCULADA
    assert float(resultado["p_shade"].max()) == 0.0
    assert resultado["firma_sombra"]["version_algoritmo"].endswith(".v2")
    assert resultado["firma_sombra"]["puntos_analisis"] == puntos_originales
    assert puntos["SE"] == puntos_originales


@pytest.mark.parametrize("geometria", [{}, {"tilt_deg": 90.0}, {"azimuth_deg": 180.0}])
def test_por_superficie_sin_orientacion_es_error_geometrico(geometria):
    torre, alto = _torre5()
    punto = _sin_orientacion(_puntos_en_caras(torre, z=alto / 2))[:1]

    resultado = calcular_fs_horario_por_superficie(
        torre, {"A": punto}, _LAT_TORRE5, _LON_TORRE5, _tmy(), {"A": geometria},
        malla_horizonte="torre5-provisional",
    )["A"]

    assert resultado["estado_sombra"] == sombras_3d.ESTADO_ERROR_GEOMETRICO
    assert resultado["calidad_confianza"] == "baja"
    assert any("orientaci" in a.lower() for a in resultado["advertencias"])


# ── Sombras persistidas con el algoritmo anterior ─────────────────────────
def _sup(**extra):
    base = {"uid": 1, "nombre": "SE", "tipo": "Fachada", "tilt_deg": 90.0,
            "azimuth_deg": 160.5, "area_m2": 20.0, "activa": True,
            "p_shade": np.ones(_HORAS_ANIO), "estado_sombra": "calculado_completo"}
    base.update(extra)
    return base


def test_version_vigente_es_v2():
    assert VERSION_ALGORITMO_FS_POR_SUPERFICIE == "sombras_3d.ray_casting_por_superficie.v2"


def test_sombra_persistida_v1_de_sombras_3d_se_retira():
    viejo = _sup(firma_sombra={"fuente": "sombras_3d",
                               "version_algoritmo": "sombras_3d.ray_casting_por_superficie.v1"})
    resultado = invalidar_sombra_por_version_algoritmo([viejo])[0]
    assert "p_shade" not in resultado and "firma_sombra" not in resultado
    assert "estado_sombra" not in resultado
    assert "algoritmo" in resultado["sombra_bloqueo_motivo"].lower()


def test_sombra_v2_y_otras_fuentes_se_conservan():
    vigente = _sup(firma_sombra={"fuente": "sombras_3d",
                                 "version_algoritmo": VERSION_ALGORITMO_FS_POR_SUPERFICIE})
    externa = _sup(firma_sombra={"fuente": "csv_externo"})
    sin_firma = {k: v for k, v in _sup().items() if k != "p_shade"}
    resultado = invalidar_sombra_por_version_algoritmo([vigente, externa, sin_firma])
    assert np.all(resultado[0]["p_shade"] == 1.0)
    assert np.all(resultado[1]["p_shade"] == 1.0)
    assert "sombra_bloqueo_motivo" not in resultado[2]


def test_recalculo_fisico_aplica_la_invalidacion_por_version(monkeypatch):
    import calculos.vinculador_sombra_multisuperficie as vinc

    tmy = _tmy()
    fp = huella_horaria(tmy.index, tmy["T2m"].to_numpy(dtype=float))
    viejo = _sup(firma_sombra={"fuente": "sombras_3d", "tmy_fingerprint": fp,
                               "version_algoritmo": "sombras_3d.ray_casting_por_superficie.v1"})
    capturado = {}

    def _capturar(session_state):
        capturado["superficies"] = session_state["superficies_bipv"]
        raise RuntimeError("detener tras invalidar")

    monkeypatch.setattr(vinc, "construir_proyecto_desde_session_state", _capturar)
    with pytest.raises(RuntimeError, match="detener"):
        vinc.construir_y_recalcular_proyecto_fisico(
            {"superficies_bipv": [viejo]}, tmy, _LAT_TORRE5, _LON_TORRE5, 2550.0,
        )
    assert "p_shade" not in capturado["superficies"][0]


# ── Contrato de la app web ────────────────────────────────────────────────
_UBICACION_CONTRATO = {"latitude": 6.25, "longitude": -75.56, "timezone": -5, "elevation_m": 1495.0}


def _solicitud(**punto_extra):
    punto = {"id": "P1", "facade": "Sur", "x_m": 0.0, "y_m": 0.0, "z_m": 0.0}
    punto.update(punto_extra)
    return {
        "contract_version": CONTRACT_VERSION,
        "location": _UBICACION_CONTRATO,
        "timestamps_utc": ["2024-03-20T17:00:00Z"],
        "points": [punto],
        "triangles": [{"a": [0.0, 5.0, 0.0], "b": [1.0, 5.0, 0.0], "c": [0.0, 5.0, 1.0]}],
    }


def test_contrato_acepta_orientacion_completa_o_ausente():
    validar_solicitud(_solicitud())
    validar_solicitud(_solicitud(tilt_deg=90.0, azimuth_deg=180.0))


@pytest.mark.parametrize("extra", [
    {"tilt_deg": 90.0},
    {"azimuth_deg": 180.0},
    {"tilt_deg": "90", "azimuth_deg": 180.0},
    {"tilt_deg": 90.0, "azimuth_deg": 400.0},
])
def test_contrato_rechaza_orientacion_invalida(extra):
    with pytest.raises(ValueError, match="P1"):
        validar_solicitud(_solicitud(**extra))


def test_contrato_web_filtra_sol_detras_del_plano():
    import scripts.run_shading_contract as contrato

    ts, elev, az, direccion = _sol_en("2024-03-20T17:00:00Z")
    caja = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
    caja.apply_translation(direccion * 3.0)
    triangulos = [{"a": caja.vertices[f[0]].tolist(), "b": caja.vertices[f[1]].tolist(),
                   "c": caja.vertices[f[2]].tolist()} for f in caja.faces]
    base = {"contract_version": CONTRACT_VERSION, "location": _UBICACION_CONTRATO,
            "timestamps_utc": ["2024-03-20T17:00:00Z"], "triangles": triangulos}
    punto = {"id": "P1", "facade": "Sur", "x_m": 0.0, "y_m": 0.0, "z_m": 0.0}

    sin = contrato._run(dict(base, points=[punto]))
    de_espaldas = contrato._run(dict(base, points=[dict(punto, tilt_deg=90.0,
                                                        azimuth_deg=(az + 180.0) % 360.0)]))

    assert sin["results"][0]["fs_geometrico"] == 1.0
    assert de_espaldas["results"][0]["fs_geometrico"] == 0.0
