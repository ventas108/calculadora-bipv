# -*- coding: utf-8 -*-
"""Escena de la Torre 5 reconstruida desde la tesis La Salle 2021 (3-oct-2026).

Medidas: ver references/lasalle-torre5-datos-escena-real.md y el informe
references/informe-lasalle-escena-tesis-2026-10-03.md. Marco local del edificio
(antes del northOffset): +X = normal de la fachada SO, +Y = normal de la
fachada SE, Z arriba; metros. Con northOffset = 160,5° la cara +Y queda a
160,5° y la +X a 250,5° (esquina real de 87° idealizada a 90°).
"""
from __future__ import annotations

import json, sys, time
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib
import trimesh

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "bipv_python"))
from calculos.sitedesigner_marsh import cargar_escena_sitedesigner  # noqa: E402
from calculos.sombras_3d import calcular_fs_horario, calcular_svf_difuso  # noqa: E402

LAT, LON, ELEV = 4.63833, -74.14833, 2555.0          # brújula Figs. 6 y 7
NORTE = 160.5
AZ_SE, AZ_SO = 162.0, 249.0
ALTO, ANCHO_SE = 36.4178, 17.2905                      # Fig. 4
FILAS, ALTO_FILA = 21, 36.4178 / 21
OFFSET_PUNTO = 0.30
SALIDA = RAIZ / "references" / "lasalle_torre5_escena_tesis"

# ── Geometría estimada (ver informe) ───────────────────────────────────────
NUCLEO = (3.80, 3.0)            # ancho a lo largo de la SO, sobresale en altura (m)
VUELO_BALCON = 1.68             # Fig. 4
ANCHO_BALCON = 3.50
PILAS_BALCON_SO = {             # rango Y de cada pila de balcones (Figs. 6, 8 y 20)
    "norte_medio": (-33.35, -29.85), "sur_medio": (-11.45, -7.95), "sur_esquina": (-3.60, 0.0),
}

def _bloque(x0, y0, z0, x1, y1, z1, nombre):
    return {"min": [x0 * 1000, y0 * 1000, z0 * 1000], "max": [x1 * 1000, y1 * 1000, z1 * 1000],
            "nombre_estimado": nombre}

def escena(p: dict) -> tuple[list, list]:
    """Bloques de edificio (sólidos) y de árboles (semitransparentes)."""
    largo_ala = ANCHO_SE
    y_sur0, y_nucleo0 = -largo_ala, -largo_ala - NUCLEO[0]
    y_norte0 = y_nucleo0 - largo_ala
    edif = [
        _bloque(0, y_sur0, 0, ANCHO_SE, 0, ALTO, "Torre5_ala_sur"),
        _bloque(ANCHO_SE - 6.0, y_nucleo0, 0, ANCHO_SE - 1.0, y_sur0, ALTO + NUCLEO[1], "Torre5_nucleo"),
        _bloque(p["retranqueo_norte"], y_norte0, 0, ANCHO_SE + p["retranqueo_norte"], y_nucleo0, ALTO,
                "Torre5_ala_norte"),
    ]
    for nombre, (ya, yb) in PILAS_BALCON_SO.items():
        x0 = ANCHO_SE + (p["retranqueo_norte"] if "norte" in nombre else 0.0)
        for k in range(1, 13):
            z = k * 2.80
            edif.append(_bloque(x0, ya, z - 0.10, x0 + VUELO_BALCON, yb, z + 0.10, f"balcon_{nombre}_{k}"))
            if p["baranda"]:
                edif.append(_bloque(x0 + VUELO_BALCON - 0.05, ya, z + 0.10, x0 + VUELO_BALCON, yb,
                                    z + 0.10 + p["baranda"], f"baranda_{nombre}_{k}"))
    # Balcones de la fachada NE en la esquina este de la SE (Fig. 31, iconos en el borde)
    for k in range(1, 13):
        z = k * 2.80
        edif.append(_bloque(-VUELO_BALCON, -ANCHO_BALCON, z - 0.10, 0, 0, z + 0.10, f"balcon_NE_{k}"))
    # Bloque vecino bajo frente a la SE (Fig. 17)
    v = p["vecino"]
    if v:
        edif.append(_bloque(v["x0"], v["dist"], 0, v["x1"], v["dist"] + v["prof"], v["alto"], "vecino_bajo_SE"))
    arb = []
    if p["arboles"]:
        a = p["arboles"]
        x0 = ANCHO_SE + a["dist"]
        arb.append(_bloque(x0, y_norte0 - 2, 0, x0 + a["prof"], 2.0, a["alto"], "arboles_SO"))
    return edif, arb

def _json(bloques):
    return json.dumps({"Location": {"latitude": LAT, "longitude": LON, "timezone": -5,
                                    "northOffset": NORTE, "elevation": ELEV},
                       "Blocks": bloques})

def _rot(x, y, z):
    R = trimesh.transformations.rotation_matrix(-np.deg2rad(NORTE), [0, 0, 1])[:3, :3]
    v = R @ np.array([x, y, z]); return float(v[0]), float(v[1]), float(v[2])

def puntos(p: dict, filas=range(1, FILAS + 1)):
    ys_so = p["columnas_so_y"]
    xs_se = p["columnas_se_x"]
    pts = []
    for f in filas:
        z = ALTO - (f - 0.5) * ALTO_FILA
        for c, y in enumerate(ys_so, 1):
            x0 = ANCHO_SE + (p["retranqueo_norte"] if y < -ANCHO_SE - NUCLEO[0] else 0.0)
            x, yy, zz = _rot(x0 + OFFSET_PUNTO, y, z)
            pts.append({"nombre": f"SO-f{f:02d}-c{c:02d}", "fachada": "SO", "fila": f, "col": c,
                        "x": x, "y": yy, "z": zz, "tilt_deg": 90.0, "azimuth_deg": AZ_SO})
        for c, xx in enumerate(xs_se, 1):
            x, yy, zz = _rot(xx, OFFSET_PUNTO, z)
            pts.append({"nombre": f"SE-f{f:02d}-c{c:02d}", "fachada": "SE", "fila": f, "col": c,
                        "x": x, "y": yy, "z": zz, "tilt_deg": 90.0, "azimuth_deg": AZ_SE})
    return pts

def clima():
    import glob, zipfile, io
    z = zipfile.ZipFile(glob.glob(str(RAIZ / "attached_assets" / "COL_CUN_Bogota-Eldorado*.zip"))[0])
    nombre = [n for n in z.namelist() if n.endswith(".epw")][0]
    tmp = SALIDA / "_tmyx.epw"; tmp.write_bytes(z.read(nombre))
    d, _ = pvlib.iotools.read_epw(str(tmp), coerce_year=2023); tmp.unlink()
    idx = d.index - pd.Timedelta("30min")
    sp = pvlib.solarposition.get_solarposition(idx, LAT, LON, ELEV); sp.index = d.index
    dx = pvlib.irradiance.get_extra_radiation(d.index)
    am = pvlib.atmosphere.get_relative_airmass(sp.apparent_zenith)
    comp = {}
    for fach, az in (("SO", AZ_SO), ("SE", AZ_SE)):
        poa = pvlib.irradiance.get_total_irradiance(90, az, sp.apparent_zenith, sp.azimuth, d.dni, d.ghi, d.dhi,
                                                    dni_extra=dx, model="perez", albedo=0.2, airmass=am)
        comp[fach] = poa[["poa_direct", "poa_sky_diffuse", "poa_ground_diffuse"]].clip(lower=0)
    return d, comp

def sombra_por_modulo(p, pts, d, comp):
    edif, arb = escena(p)
    malla_e, _ = cargar_escena_sitedesigner(_json(edif))
    fs = calcular_fs_horario(malla_e, pts, LAT, LON, indice_tmy=d.index)
    fs_t = None
    if arb:
        malla_a, _ = cargar_escena_sitedesigner(_json(arb))
        fs_t = calcular_fs_horario(malla_a, pts, LAT, LON, indice_tmy=d.index, transparencia=0.3)
        malla_svf = trimesh.util.concatenate([malla_e, malla_a])
    else:
        malla_svf = malla_e
    out = []
    for fach in ("SO", "SE"):
        sub = [q for q in pts if q["fachada"] == fach]
        if not sub:
            continue
        svf = calcular_svf_difuso(malla_svf, sub, 90.0, AZ_SO if fach == "SO" else AZ_SE, resolucion_deg=10.0)
        svf = dict(zip(svf["Punto"], svf["f_svf"]))
        c = comp[fach]
        b = c["poa_direct"].to_numpy(); dif = c["poa_sky_diffuse"].to_numpy(); r = c["poa_ground_diffuse"].to_numpy()
        tot = (b + dif + r).sum()
        for q in sub:
            serie = np.zeros(len(d))
            for df_fs, peso in ((fs, 1.0), (fs_t, 1.0)):
                if df_fs is None:
                    continue
                g = df_fs[df_fs["Punto"] == q["nombre"]]
                h = ((pd.to_datetime(dict(year=2023, month=g["Mes"], day=g["Dia"])) - pd.Timestamp("2023-01-01")).dt.days * 24
                     + g["Hora"].astype(int)).to_numpy()
                ok = (h >= 0) & (h < len(d))
                s = np.zeros(len(d)); s[h[ok]] = g["FS"].to_numpy(dtype=float)[ok]
                serie = 1 - (1 - serie) * (1 - s)
            recibido = (b * (1 - serie) + dif * svf[q["nombre"]] + r).sum()
            out.append({"fachada": fach, "fila": q["fila"], "col": q["col"],
                        "sombra_pct": round(100 * (1 - recibido / tot), 2),
                        "p_shade_haz_medio": float(serie[b > 0].mean())})
    return pd.DataFrame(out)

PARAM_BASE = {
    "retranqueo_norte": 0.0, "baranda": 1.0,
    "arboles": {"dist": 2.5, "prof": 4.0, "alto": 6.0},
    "vecino": {"x0": -25.0, "x1": 10.0, "dist": 18.0, "prof": 15.0, "alto": 18.0},
    # Columnas de módulos: entre ventanas y junto a las pilas de balcones (Figs. 6, 20).
    "columnas_so_y": [-37.0, -35.4, -34.0, -28.5, -25.5, -22.5, -16.5, -15.0, -13.5, -12.1, -7.2, -5.4, -4.1],
    "columnas_se_x": [15.5, 12.0, 8.6, 5.2, 1.5],
}

if __name__ == "__main__" and "--calibrar" not in sys.argv and "--energia" not in sys.argv and "--submodulo" not in sys.argv:
    SALIDA.mkdir(parents=True, exist_ok=True)
    d, comp = clima()
    t = time.time()
    pts = puntos(PARAM_BASE, filas=[1, 11, 21])
    r = sombra_por_modulo(PARAM_BASE, pts, d, comp)
    print(f"{len(pts)} puntos en {time.time()-t:.1f} s"); print(r.head(20))


# ── Calibración contra las Tablas 19 y 20 (perfiles, no posiciones) ─────────
def referencia():
    t = pd.read_csv(RAIZ / "references" / "lasalle-sombra-por-modulo-referencia-tablas-19-20.csv")
    return t.rename(columns={"sombra_pct_ref": "ref"})

def error_perfiles(sim: pd.DataFrame, ref: pd.DataFrame, fach: str) -> dict:
    s, r = sim[sim.fachada == fach], ref[ref.fachada == fach]
    filas_s, filas_r = s.groupby("fila").sombra_pct.mean(), r.groupby("fila").ref.mean()
    cols_s = np.sort(s.groupby("col").sombra_pct.mean().to_numpy())
    cols_r = np.sort(r.groupby("columna").ref.mean().to_numpy())
    return {"rmse_filas": float(np.sqrt(((filas_s - filas_r) ** 2).mean())),
            "rmse_columnas": float(np.sqrt(((cols_s - cols_r) ** 2).mean())),
            "media_sim": float(s.sombra_pct.mean()), "media_ref": float(r.ref.mean()),
            "n_menor_2_sim": int((s.sombra_pct < 2).sum()), "n_menor_2_ref": int((r.ref < 2).sum())}

def calibrar():
    import copy, itertools
    d, comp = clima(); ref = referencia(); filas_todas = list(range(1, FILAS + 1))
    res = []
    for ret, ad, ah, vd, va in itertools.product((-7.7, 0.0, 7.7), (1.5, 3.0), (6.0, 7.0), (14.0, 22.0), (15.0, 21.0)):
        p = copy.deepcopy(PARAM_BASE)
        p["retranqueo_norte"] = ret; p["arboles"].update(dist=ad, alto=ah); p["vecino"].update(dist=vd, alto=va)
        res.append((p, None))
    # SO no depende del vecino ni SE de los árboles: se calibran por separado.
    filas = []
    vistos = {}
    for p, _ in res:
        clave_so = (p["retranqueo_norte"], p["arboles"]["dist"], p["arboles"]["alto"])
        clave_se = (p["vecino"]["dist"], p["vecino"]["alto"])
        if clave_so in vistos.get("so", {}) and clave_se in vistos.get("se", {}):
            continue
        t = time.time()
        sim = sombra_por_modulo(p, puntos(p, filas_todas), d, comp)
        vistos.setdefault("so", {})[clave_so] = (p, sim, error_perfiles(sim, ref, "SO"))
        vistos.setdefault("se", {})[clave_se] = (p, sim, error_perfiles(sim, ref, "SE"))
        print(clave_so, clave_se, f"{time.time()-t:.0f}s",
              {k: round(v, 2) if isinstance(v, float) else v for k, v in vistos["so"][clave_so][2].items()},
              {k: round(v, 2) if isinstance(v, float) else v for k, v in vistos["se"][clave_se][2].items()}, flush=True)
    mejor_so = min(vistos["so"].items(), key=lambda kv: kv[1][2]["rmse_filas"] + kv[1][2]["rmse_columnas"])
    mejor_se = min(vistos["se"].items(), key=lambda kv: kv[1][2]["rmse_filas"] + kv[1][2]["rmse_columnas"])
    p = copy.deepcopy(PARAM_BASE)
    p["retranqueo_norte"], ad, ah = mejor_so[0]; p["arboles"].update(dist=ad, alto=ah)
    p["vecino"].update(dist=mejor_se[0][0], alto=mejor_se[0][1])
    sim = sombra_por_modulo(p, puntos(p, filas_todas), d, comp)
    sim.to_csv(SALIDA / "sombra_por_modulo_app.csv", index=False)
    edif, arb = escena(p)
    (SALIDA / "escena_torre5_edificios.json").write_text(_json(edif), encoding="utf-8")
    (SALIDA / "escena_torre5_arboles.json").write_text(_json(arb), encoding="utf-8")
    resumen = {"parametros": p, "SO": error_perfiles(sim, ref, "SO"), "SE": error_perfiles(sim, ref, "SE"),
               "candidatos_SO": {str(k): v[2] for k, v in vistos["so"].items()},
               "candidatos_SE": {str(k): v[2] for k, v in vistos["se"].items()}}
    (SALIDA / "calibracion.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print("MEJOR", json.dumps({"SO": resumen["SO"], "SE": resumen["SE"], "ret_arb": mejor_so[0], "vecino": mejor_se[0]}))

if __name__ == "__main__" and "--calibrar" in sys.argv:
    SALIDA.mkdir(parents=True, exist_ok=True)
    calibrar()


# ── Energía: módulos con sombra < 2 % y física de la app (bypass + inversor) ─
def _serie_fs(p, pts, d):
    edif, arb = escena(p)
    malla_e, _ = cargar_escena_sitedesigner(_json(edif))
    capas = [calcular_fs_horario(malla_e, pts, LAT, LON, indice_tmy=d.index)]
    if arb:
        malla_a, _ = cargar_escena_sitedesigner(_json(arb))
        capas.append(calcular_fs_horario(malla_a, pts, LAT, LON, indice_tmy=d.index, transparencia=0.3))
    series = {}
    for q in pts:
        serie = np.zeros(len(d))
        for df_fs in capas:
            g = df_fs[df_fs["Punto"] == q["nombre"]]
            h = ((pd.to_datetime(dict(year=2023, month=g["Mes"], day=g["Dia"])) - pd.Timestamp("2023-01-01")).dt.days * 24
                 + g["Hora"].astype(int)).to_numpy()
            ok = (h >= 0) & (h < len(d))
            s = np.zeros(len(d)); s[h[ok]] = g["FS"].to_numpy(dtype=float)[ok]
            serie = 1 - (1 - serie) * (1 - s)
        series[q["nombre"]] = serie
    return series

def energia():
    from calculos.modelo_iv import estimar_sdm_desde_ficha
    from calculos.transicion_multisuperficie import superficie_nueva
    from calculos.vinculador_sombra_multisuperficie import (
        aplicar_sombra_a_superficies, construir_y_recalcular_proyecto_fisico)
    from calculos.sombras_3d import calcular_fs_horario_por_superficie
    cal = json.loads((SALIDA / "calibracion.json").read_text(encoding="utf-8"))
    p = cal["parametros"]
    sim = pd.read_csv(SALIDA / "sombra_por_modulo_app.csv")
    d, _ = clima()
    tmy = pd.DataFrame({"G_h": d["ghi"].to_numpy(float), "Gb_n": d["dni"].to_numpy(float),
                        "Gd_h": d["dhi"].to_numpy(float), "T2m": d["temp_air"].to_numpy(float)}, index=d.index)
    ficha = {"nombre": "SPR-MAX3-400", "tecnologia": "Mono-Si", "transparencia_pct": 0, "sdm_estimado": True,
             "Voc_stc": 75.6, "Vmp_stc": 65.8, "Isc_stc": 6.58, "Imp_stc": 6.08, "Pmax_stc": 65.8 * 6.08,
             "Tk_beta": -0.236, "Tk_alfa": 0.058, "Tk_gamma": -0.27, "N_s": 104, "NOCT": 45.0,
             "largo_mm": 1690, "ancho_mm": 1046, "area_m2": 1.690 * 1.046}
    panel = {**ficha, **estimar_sdm_desde_ficha(ficha)}
    todos = puntos(p)
    if "--seleccion-referencia" in sys.argv:
        # Los mismos módulos que eligió la tesis (< 2 % según su tabla).
        ref = referencia()
        elegidos = {r.fachada + f"-f{int(r.fila):02d}-c{int(r.columna):02d}" for r in ref.itertuples() if r.ref < 2.0}
    else:
        elegidos = {r.fachada + f"-f{int(r.fila):02d}-c{int(r.col):02d}" for r in sim.itertuples() if r.sombra_pct < 2.0}
    pts_sel = [q for q in todos if q["nombre"] in elegidos]
    series = _serie_fs(p, pts_sel, d)
    resultado = {}
    edif, _ = escena(p)
    malla_e, meta = cargar_escena_sitedesigner(_json(edif))
    import hashlib
    meta.setdefault("malla_fingerprint", "externa_marsh-" + hashlib.sha256(_json(edif).encode()).hexdigest()[:16])
    for fach, az in (("SO", AZ_SO), ("SE", AZ_SE)):
        sel = [q for q in pts_sel if q["fachada"] == fach]
        n = len(sel)
        n_serie = min(18, n); n_par = max(1, n // n_serie)
        nombre_sup = f"Fachada-{fach}"
        # Firma real del motor de la app (puntos, TMY, versión); la p_shade se
        # reemplaza por la combinada edificios + árboles semitransparentes.
        base = calcular_fs_horario_por_superficie(
            malla_e, {nombre_sup: [{k: v for k, v in q.items() if k not in ("fila", "col")} for q in sel]},
            LAT, LON, tmy, {nombre_sup: {"tilt_deg": 90.0, "azimuth_deg": az}},
            malla_horizonte=meta["malla_fingerprint"])[nombre_sup]
        m = np.array([series[q["nombre"]] for q in sel])
        p_shade = m.mean(axis=0)
        # Spec 05/sombra-por-string: cuántos módulos tienen sombra (> 5 %) y
        # cuánta luz pierden esos módulos, con edificios + árboles.
        sombreado = m > 0.05
        fraccion = sombreado.mean(axis=0)
        profundidad = np.where(sombreado, m, 0.0).sum(axis=0) / np.maximum(sombreado.sum(axis=0), 1)
        cero = np.zeros(len(d))
        # Spec 05/difusa-sombra-por-string: cielo visible de los módulos
        # elegidos, como lo calcula la app (edificios sólidos, árboles con
        # transparencia 0,3).
        from calculos.sombras_3d import calcular_svf_difuso
        _pts = [{k: v for k, v in q.items() if k not in ("fila", "col")} for q in sel]
        _edif, _arb = escena(p)
        _me, _ = cargar_escena_sitedesigner(_json(_edif))
        svf_e = calcular_svf_difuso(_me, _pts, 90.0, az, resolucion_deg=10.0)["f_svf"].to_numpy()
        if _arb:
            import trimesh
            _ma, _ = cargar_escena_sitedesigner(_json(_arb))
            svf_ea = calcular_svf_difuso(trimesh.util.concatenate([_me, _ma]), _pts, 90.0, az,
                                         resolucion_deg=10.0)["f_svf"].to_numpy()
        else:
            svf_ea = svf_e
        tapado = (1 - svf_e) + (svf_e - svf_ea) * (1 - 0.3)
        factor_cielo = float(1 - tapado.mean())
        energias = {}
        for etiqueta, ps, extra in (
            ("sin_sombra", cero, {"fraccion_modulos_sombra": None, "profundidad_sombra": None, "factor_cielo_visible": None}),
            ("con_sombra", p_shade, {"fraccion_modulos_sombra": None, "profundidad_sombra": None, "factor_cielo_visible": None}),
            ("con_sombra_por_string", p_shade, {"fraccion_modulos_sombra": fraccion, "profundidad_sombra": profundidad,
                                                "factor_cielo_visible": None}),
            ("con_difusa", p_shade, {"fraccion_modulos_sombra": fraccion, "profundidad_sombra": profundidad,
                                     "factor_cielo_visible": factor_cielo}),
        ):
            sup = superficie_nueva(nombre=nombre_sup, tipo="Fachada", tilt_deg=90.0, azimuth_deg=az,
                                   area_m2=panel["area_m2"] * n_serie * n_par, panel=panel, n_serie=n_serie,
                                   n_paralelo=n_par, inversor_id="Fronius-Primo-15", p_shade=np.zeros(len(d)), albedo=0.20)
            res = {nombre_sup: {**{k: v for k, v in base.items() if k != "df"}, "p_shade": ps,
                                "estado_sombra": "calculado_completo", **extra}}
            [sup] = aplicar_sombra_a_superficies([sup], res)
            ss = {"panel_dict": panel, "superficies_bipv": [sup], "multisup_malla_meta": meta,
                  "multisup_inversores": [{"inversor_id": "Fronius-Primo-15", "tipo": "compartido",
                                           "eta_inversor": 0.986, "P_ac_nom_W": None, "ficha": {}}]}
            pr = construir_y_recalcular_proyecto_fisico(ss, tmy, lat=LAT, lon=LON, alt_m=ELEV)
            s_ = pr["superficies"][nombre_sup]
            energias[etiqueta] = {"E_ac": s_["resultados_ac"]["E_ac_anual_kWh"],
                                  "kWp": s_["resultados_ac"]["P_dc_stc_kW"],
                                  "poa": s_["resultados_dc"]["poa_anual_kWh_m2"]}
        resultado[fach] = {"modulos_elegidos": n, "n_serie": n_serie, "n_paralelo": n_par,
                           "sombra_irradiacion_media_pct": float(sim[(sim.fachada == fach) & (sim.fachada + "-f" + sim.fila.map("{:02d}".format) + "-c" + sim.col.map("{:02d}".format)).isin(elegidos)].sombra_pct.mean()),
                           "p_shade_haz_medio_diurno": float(p_shade[tmy["Gb_n"].to_numpy() > 0].mean()),
                           **energias,
                           "perdida_energia_sombra_pct": 100 * (1 - energias["con_sombra"]["E_ac"] / energias["sin_sombra"]["E_ac"]),
                           "perdida_energia_sombra_por_string_pct": 100 * (1 - energias["con_sombra_por_string"]["E_ac"] / energias["sin_sombra"]["E_ac"]),
                           "fraccion_modulos_sombra_media_diurna": float(fraccion[tmy["Gb_n"].to_numpy() > 0].mean()),
                           "factor_cielo_visible": factor_cielo,
                           "perdida_energia_con_difusa_pct": 100 * (1 - energias["con_difusa"]["E_ac"] / energias["sin_sombra"]["E_ac"])}
    e_sin = sum(r["sin_sombra"]["E_ac"] for r in resultado.values())
    e_con = sum(r["con_sombra"]["E_ac"] for r in resultado.values())
    e_str = sum(r["con_sombra_por_string"]["E_ac"] for r in resultado.values())
    e_dif = sum(r["con_difusa"]["E_ac"] for r in resultado.values())
    kwp = sum(r["con_sombra"]["kWp"] for r in resultado.values())
    resultado["total"] = {"perdida_energia_sombra_pct": 100 * (1 - e_con / e_sin),
                          "perdida_energia_sombra_por_string_pct": 100 * (1 - e_str / e_sin),
                          "perdida_energia_con_difusa_pct": 100 * (1 - e_dif / e_sin),
                          "rendimiento_por_string_kWh_kWp": e_str / kwp,
                          "rendimiento_kWh_kWp": e_con / kwp, "modulos": sum(r["modulos_elegidos"] for k, r in resultado.items())}
    (SALIDA / ("energia_seleccion_referencia.json" if "--seleccion-referencia" in sys.argv else "energia.json")).write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

if __name__ == "__main__" and "--energia" in sys.argv:
    energia()


# ── Resolución dentro del módulo: centro frente a bordes (celdas/diodos) ────
def sub_modulo():
    """5 puntos por módulo elegido (centro, arriba, abajo, izquierda, derecha)
    para acotar la pérdida cuando el borde de una sombra cruza celdas."""
    cal = json.loads((SALIDA / "calibracion.json").read_text(encoding="utf-8"))
    p = cal["parametros"]
    sim = pd.read_csv(SALIDA / "sombra_por_modulo_app.csv")
    d, comp = clima()
    elegidos = {r.fachada + f"-f{int(r.fila):02d}-c{int(r.col):02d}" for r in sim.itertuples() if r.sombra_pct < 2.0}
    base = [q for q in puntos(p) if q["nombre"] in elegidos]
    R = trimesh.transformations.rotation_matrix(-np.deg2rad(NORTE), [0, 0, 1])[:3, :3]
    desp = {"centro": (0, 0), "arriba": (0, 0.75), "abajo": (0, -0.75), "izq": (-0.45, 0), "der": (0.45, 0)}
    pts = []
    for q in base:
        # dirección horizontal a lo largo de la fachada (local): SO → eje Y, SE → eje X
        eje = R @ (np.array([0, 1, 0]) if q["fachada"] == "SO" else np.array([1, 0, 0]))
        for k, (h, v) in desp.items():
            pts.append({**q, "nombre": q["nombre"] + "-" + k, "x": q["x"] + h * eje[0], "y": q["y"] + h * eje[1],
                        "z": q["z"] + v, "base": q["nombre"]})
    series = _serie_fs(p, pts, d)
    out = {}
    for fach in ("SO", "SE"):
        c = comp[fach]; g = (c["poa_direct"] + c["poa_sky_diffuse"] + c["poa_ground_diffuse"]).to_numpy()
        b = c["poa_direct"].to_numpy()
        mods = sorted({q["base"] for q in pts if q["fachada"] == fach})
        centro = np.mean([series[m + "-centro"] for m in mods], axis=0)
        peor = np.mean([np.max([series[f"{m}-{k}"] for k in desp], axis=0) for m in mods], axis=0)
        media5 = np.mean([np.mean([series[f"{m}-{k}"] for k in desp], axis=0) for m in mods], axis=0)
        out[fach] = {"modulos": len(mods),
                     "perdida_haz_centro_pct": 100 * float((centro * b).sum() / g.sum()),
                     "perdida_haz_media5_pct": 100 * float((media5 * b).sum() / g.sum()),
                     # cota alta: si cualquier borde del módulo está a la sombra, el módulo
                     # pierde esa fracción de TODA su irradiancia (bypass de las subcadenas)
                     "perdida_peor_borde_total_pct": 100 * float((peor * g).sum() / g.sum())}
        # Cota de string: cada columna es un string (Fig. 20); sin bypass, el
        # módulo más sombreado limita la corriente de todo el string.
        cols = sorted({m.split("-c")[1] for m in mods})
        perd_str = []
        for cc in cols:
            ms = [m for m in mods if m.endswith("-c" + cc)]
            peor_mod = np.max([np.max([series[f"{m}-{k}"] for k in desp], axis=0) for m in ms], axis=0)
            perd_str.append((peor_mod * g).sum() * len(ms))
        out[fach]["perdida_string_sin_bypass_pct"] = 100 * float(sum(perd_str) / (g.sum() * len(mods)))
    (SALIDA / "sub_modulo.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))

if __name__ == "__main__" and "--submodulo" in sys.argv:
    sub_modulo()
