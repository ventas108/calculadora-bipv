# -*- coding: utf-8 -*-
"""Prueba del generador «🧮 Generar un punto por módulo» con la fachada SO de
la Torre 5 (escena recalibrada por columnas, 3-oct-2026).

1. Precisión: una columna generada frente a los puntos del script 5.
2. Cuentas: 13 columnas × 21 filas y varias configuraciones de strings.
3. Campo regular frente a columnas reales (separación irregular).
4. Sombra por string (un string por columna) frente al promedio.
"""
from __future__ import annotations

import json, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lasalle_torre5_5_escena_tesis as L  # noqa: E402
import lasalle_torre5_6_calibrar_columnas as C  # noqa: E402
from calculos.puntos_modulo import generar_puntos_modulos, vectores_superficie  # noqa: E402

LARGO, ANCHO = 1.690, 1.046
PASO = L.ALTO_FILA                      # 1,7342 m por fila (tesis: 21 filas en 36,42 m)
SV = PASO - LARGO                       # separación vertical entre módulos
P, PILAS = C.parametros_columnas(3)
YS = P["columnas_so_y"]
AZ_GEO = (90.0 + L.NORTE) % 360         # normal de la cara SO de la malla: 250,5°
SALIDA = C.SALIDA


def _esquina_columna(y_centro):
    """Esquina inferior izquierda (vista desde afuera) de una columna, en la escena."""
    n, u, v = vectores_superficie(90.0, AZ_GEO)
    centro_base = np.array(L._rot(L.ANCHO_SE, y_centro, SV / 2))
    return centro_base - u * ANCHO / 2


def precision():
    """Columna 12 generada (1 × 21) frente a los puntos del script 5."""
    c = 12
    gen = generar_puntos_modulos("SO", 90.0, AZ_GEO, _esquina_columna(YS[c - 1]), filas=21, columnas=1,
                                 largo_m=LARGO, ancho_m=ANCHO, separacion_v_m=SV, separacion_fachada_m=L.OFFSET_PUNTO)
    ref = [q for q in L.puntos(P) if q["fachada"] == "SO" and q["col"] == c]
    ref = sorted(ref, key=lambda q: -q["fila"])          # tesis: fila 1 arriba; generador: F01 abajo
    err = max(np.linalg.norm([g["x"] - r["x"], g["y"] - r["y"], g["z"] - r["z"]]) for g, r in zip(gen, ref))
    return {"columna": c, "puntos": len(gen), "error_max_mm": round(1000 * err, 3),
            "nota": "F01 del generador = fila 21 de la tesis (el generador cuenta desde abajo)"}


def cuentas():
    casos = {}
    for nombre, grupos in {
        "21S x 13P (un string por columna)": [{"gid": "G1", "n_serie": 21, "n_paralelo": 13}],
        "7S x 39P": [{"gid": "G1", "n_serie": 7, "n_paralelo": 39}],
        "10S x 7P (70 módulos)": [{"gid": "G1", "n_serie": 10, "n_paralelo": 7}],
        "2 grupos 21S x 7P + 21S x 6P": [{"gid": "G1", "n_serie": 21, "n_paralelo": 7},
                                          {"gid": "G2", "n_serie": 21, "n_paralelo": 6}],
    }.items():
        try:
            pts = generar_puntos_modulos("SO", 90.0, AZ_GEO, _esquina_columna(YS[0]), 21, 13, LARGO, ANCHO,
                                         separacion_v_m=SV, grupos=grupos, cableado="columnas")
            strings = {}
            for q in pts:
                strings.setdefault(q["string"], set()).add(q["columna"])
            casos[nombre] = {"ok": True, "puntos": len(pts), "strings": len(strings),
                             "columnas_por_string": sorted({len(v) for v in strings.values()})}
        except ValueError as e:
            casos[nombre] = {"ok": False, "mensaje": str(e)}
    return casos


def regular_vs_real():
    """Un campo regular de 13 columnas entre la primera y la última columna real."""
    paso = (YS[-1] - YS[0]) / 12
    reg = [YS[0] + k * paso for k in range(13)]
    dif = [round(r - y, 2) for r, y in zip(reg, YS)]
    return {"paso_regular_m": round(paso, 3), "separacion_entre_modulos_m": round(paso - ANCHO, 3),
            "desvio_por_columna_m": dif, "desvio_max_m": round(max(abs(d) for d in dif), 2),
            "huecos_reales_m": [round(b - a, 2) for a, b in zip(YS, YS[1:])]}


def sombra_por_string():
    """Puntos reales (columnas irregulares), un string por columna (21S × 13P)."""
    import pandas as pd
    from calculos.sombras_3d import calcular_fs_horario_por_superficie
    from calculos.mismatch_bypass import simular_bypass_horario, simular_bypass_por_strings
    L.PILAS_BALCON_SO = PILAS
    d, comp = L.clima()
    pts = []
    for c, y in enumerate(YS, 1):
        pts += generar_puntos_modulos(f"SO-c{c:02d}", 90.0, AZ_GEO, _esquina_columna(y), 21, 1, LARGO, ANCHO,
                                      separacion_v_m=SV, grupos=[{"gid": "G1", "n_serie": 21, "n_paralelo": 1}])
    for c, q in zip(np.repeat(range(1, 14), 21), pts):
        q["string"] = f"G1-S{c}"; q["fachada"] = "SO"
    edif, _ = L.escena(P)
    malla, meta = L.cargar_escena_sitedesigner(L._json(edif))
    tmy = pd.DataFrame({"G_h": d["ghi"].to_numpy(float), "Gb_n": d["dni"].to_numpy(float),
                        "Gd_h": d["dhi"].to_numpy(float), "T2m": d["temp_air"].to_numpy(float)}, index=d.index)
    r = calcular_fs_horario_por_superficie(malla, {"SO": pts}, L.LAT, L.LON, tmy,
                                           {"SO": {"tilt_deg": 90.0, "azimuth_deg": AZ_GEO}}, malla_horizonte="m")["SO"]
    poa = comp["SO"]; g = (poa["poa_direct"] + poa["poa_sky_diffuse"] + poa["poa_ground_diffuse"]).to_numpy()
    fdir = np.divide(poa["poa_direct"].to_numpy(), g, out=np.zeros_like(g), where=g > 0)
    panel = json.loads(json.dumps(L.__dict__.get("PANEL_SPR", {}))) or None
    from calculos.modelo_iv import estimar_sdm_desde_ficha
    ficha = {"nombre": "SPR-MAX3-400", "tecnologia": "Mono-Si", "Voc_stc": 75.6, "Vmp_stc": 65.8, "Isc_stc": 6.58,
             "Imp_stc": 6.08, "Pmax_stc": 65.8 * 6.08, "Tk_beta": -0.236, "Tk_alfa": 0.058, "Tk_gamma": -0.27,
             "N_s": 104, "NOCT": 45.0, "largo_mm": 1690, "ancho_mm": 1046, "area_m2": LARGO * ANCHO,
             "transparencia_pct": 0, "sdm_estimado": True}
    panel = {**ficha, **estimar_sdm_desde_ficha(ficha)}
    t = d["temp_air"].to_numpy(float)
    sps = r["sombra_por_string"]
    strings = [(sps[f"G1-S{c}"]["fraccion"], sps[f"G1-S{c}"]["profundidad"]) for c in range(1, 14)]
    por_string = simular_bypass_por_strings(G_eff=g, T_amb=t, strings=strings, N_series=21, panel=panel,
                                            fraccion_directa=fdir)
    promedio = simular_bypass_horario(G_eff=g, T_amb=t, p_shade=r["fraccion_modulos_sombra"],
                                      profundidad_sombra=r["profundidad_sombra"], N_series=21, N_parallel=13,
                                      panel=panel, fraccion_directa=fdir)
    return {"modulos": len(pts), "strings": len(sps), "cielo_visible": round(r["factor_cielo_visible"], 3),
            "perdida_bypass_por_string_pct": por_string["pct_bypass_anual"],
            "perdida_bypass_promedio_superficie_pct": promedio["pct_bypass_anual"],
            "perdida_por_columna_pct": {f"c{c}": s["pct_bypass_anual"] for c, s in enumerate(por_string["por_string"], 1)}}


if __name__ == "__main__":
    res = {"precision": precision(), "cuentas": cuentas(), "regular_vs_real": regular_vs_real()}
    print(json.dumps(res, indent=1, ensure_ascii=False), flush=True)
    if "--sombra" in sys.argv:
        res["sombra_por_string"] = sombra_por_string()
        print(json.dumps(res["sombra_por_string"], indent=1, ensure_ascii=False))
    (SALIDA / "prueba_puntos_automaticos.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
