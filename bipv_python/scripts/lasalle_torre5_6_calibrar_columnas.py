# -*- coding: utf-8 -*-
"""Recalibración por columnas de la escena de la Torre 5 (3-oct-2026).

La calibración anterior (script 5) ajustaba la sombra media y los perfiles
ordenados; la sombra quedaba en otras columnas. Aquí se ubican las pilas de
balcones y las columnas de módulos de la fachada SO para reproducir la sombra
de cada columna de la tabla de referencia de la tesis.

Paso 1 (--biblioteca): sombra de una columna de módulos en función de su
distancia lateral a una pila de balcones (una sola pila, ala sur, fila 10).
"""
from __future__ import annotations

import json, sys, time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lasalle_torre5_5_escena_tesis as L  # noqa: E402

CAL = json.loads((L.SALIDA / "calibracion.json").read_text(encoding="utf-8"))["parametros"]
SALIDA = L.SALIDA / "calibracion_columnas"


def _puntos_y(ys, filas, x0=L.ANCHO_SE):
    pts = []
    for f in filas:
        z = L.ALTO - (f - 0.5) * L.ALTO_FILA
        for c, y in enumerate(ys, 1):
            x, yy, zz = L._rot(x0 + L.OFFSET_PUNTO, y, z)
            pts.append({"nombre": f"SO-f{f:02d}-c{c:02d}", "fachada": "SO", "fila": f, "col": c,
                        "x": x, "y": yy, "z": zz, "tilt_deg": 90.0, "azimuth_deg": L.AZ_SO})
    return pts


def biblioteca():
    """Sombra (directa + difusa) de puntos a lo largo del ala sur con UNA pila
    de balcones en y ∈ [-10.25, -6.75]."""
    d, comp = L.clima()
    p = dict(CAL); p["arboles"] = None; p["vecino"] = None
    L.PILAS_BALCON_SO = {"sur_prueba": (-10.25, -6.75)}
    ys = list(np.round(np.arange(-16.0, -0.49, 0.25), 2))
    t = time.time()
    sim = L.sombra_por_modulo(p, _puntos_y(ys, [10]), d, comp)
    sim["y"] = ys
    sim = sim[sim.fachada == "SO"]
    print(f"{len(ys)} puntos en {time.time() - t:.0f} s")
    SALIDA.mkdir(parents=True, exist_ok=True)
    sim.to_csv(SALIDA / "biblioteca_pila.csv", index=False)
    print(sim[["y", "sombra_pct"]].to_string(index=False))


if __name__ == "__main__" and "--biblioteca" in sys.argv:
    biblioteca()


def biblioteca_alas():
    """Sombra sin pilas de balcones a lo largo de las dos alas (efecto del
    escalón entre alas y de los bordes), fila 10."""
    d, comp = L.clima()
    p = dict(CAL); p["arboles"] = None; p["vecino"] = None
    L.PILAS_BALCON_SO = {}
    ys = list(np.round(np.arange(-38.25, -21.0, 0.25), 2)) + list(np.round(np.arange(-17.25, -0.2, 0.25), 2))
    p2 = dict(p); p2["columnas_so_y"] = ys; p2["columnas_se_x"] = []
    t = time.time()
    sim = L.sombra_por_modulo(p2, [q for q in L.puntos(p2, filas=[10]) if q["fachada"] == "SO"], d, comp)
    sim["y"] = ys
    print(f"{len(ys)} puntos en {time.time() - t:.0f} s")
    sim.to_csv(SALIDA / "biblioteca_alas.csv", index=False)
    print(sim[["y", "sombra_pct"]].iloc[::2].to_string(index=False))


if __name__ == "__main__" and "--alas" in sys.argv:
    biblioteca_alas()


# ── Paso 2: ubicar pilas y columnas (modelo rápido con la biblioteca) ──────
ALA_NORTE = (-38.2, -21.3)
ALA_SUR = (-17.1, -0.4)
SEPARACION_MIN = 1.10          # módulo de 1,046 m de ancho


def objetivo_columnas():
    ref = L.referencia()
    so = ref[(ref.fachada == "SO") & ref.fila.between(2, 16)]
    return so.groupby("columna").ref.mean().to_numpy()


def _lib():
    b = pd.read_csv(SALIDA / "biblioteca_pila.csv")
    dy = b["y"].to_numpy() - (-8.5)                  # distancia al centro de la pila
    s = b["sombra_pct"].to_numpy() / 100.0
    base = float(s[[0, -1]].min())
    return dy, np.clip((s - base) / (1 - base), 0, 1), base


def modelo(ys, centros, lib):
    dy, s, base = lib
    tot = np.full(len(ys), 1 - base)
    for c in centros:
        tot *= 1 - np.interp(np.asarray(ys) - c, dy, s, left=0.0, right=0.0)
    return 100 * (1 - tot)


def ajustar(n_pilas=3, semillas=40, lam=0.02):
    from scipy.optimize import minimize
    lib = _lib(); obj = objetivo_columnas(); y0 = np.array(CAL["columnas_so_y"], float)
    rng = np.random.default_rng(0)

    def costo(v):
        ys, cs = v[:13], v[13:]
        e = modelo(ys, cs, lib) - obj
        pen = 0.0
        d = np.diff(ys)
        pen += 1e3 * np.sum(np.clip(SEPARACION_MIN - d, 0, None) ** 2)
        for i, y in enumerate(ys):
            a, b = ALA_NORTE if i < 6 else ALA_SUR
            pen += 1e3 * (max(0, a - y) ** 2 + max(0, y - b) ** 2)
        for c in cs:
            pen += 1e3 * min(max(0, -38.2 + 1.75 - c) ** 2 + max(0, c + 21.3 + 1.75) ** 2,
                             max(0, -17.1 + 1.75 - c) ** 2 + max(0, c + 0.4 + 1.75) ** 2)
        cs_ord = np.sort(cs)
        pen += 1e3 * np.sum(np.clip(3.6 - np.diff(cs_ord), 0, None) ** 2)
        return float(np.sum(e ** 2) + lam * np.sum((ys - y0) ** 2) + pen)

    mejor = None
    for _ in range(semillas):
        cs0 = rng.uniform(-37, -1, n_pilas)
        v0 = np.concatenate([y0 + rng.normal(0, 1.0, 13), cs0])
        r = minimize(costo, v0, method="Powell", options={"maxiter": 20000, "xtol": 1e-3, "ftol": 1e-6})
        if mejor is None or r.fun < mejor.fun:
            mejor = r
    ys, cs = mejor.x[:13], np.sort(mejor.x[13:])
    return {"n_pilas": n_pilas, "costo": float(mejor.fun), "columnas_so_y": [round(float(y), 2) for y in ys],
            "pilas_centro_y": [round(float(c), 2) for c in cs],
            "modelo": [round(float(m), 1) for m in modelo(ys, cs, lib)],
            "objetivo": [round(float(o), 1) for o in obj]}


if __name__ == "__main__" and "--ajustar" in sys.argv:
    for n in (3, 4, 5):
        r = ajustar(n)
        print(json.dumps(r, ensure_ascii=False), flush=True)
        (SALIDA / f"ajuste_{n}_pilas.json").write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Paso 3: verificación con ray tracing completo (21 filas, SO y SE) ──────
def parametros_columnas(n_pilas=3):
    a = json.loads((SALIDA / f"ajuste_{n_pilas}_pilas.json").read_text(encoding="utf-8"))
    p = json.loads(json.dumps(CAL))
    p["retranqueo_norte"] = 0.0          # la tabla de referencia no muestra el escalón entre alas
    p["columnas_so_y"] = a["columnas_so_y"]
    pilas = {f"pila_{i + 1}": (round(c - L.ANCHO_BALCON / 2, 2), round(c + L.ANCHO_BALCON / 2, 2))
             for i, c in enumerate(a["pilas_centro_y"])}
    return p, pilas


def verificar(n_pilas=3):
    p, pilas = parametros_columnas(n_pilas)
    L.PILAS_BALCON_SO = pilas
    d, comp = L.clima(); ref = L.referencia()
    t = time.time()
    sim = L.sombra_por_modulo(p, L.puntos(p), d, comp)
    print(f"{len(sim)} módulos en {time.time() - t:.0f} s")
    sim.to_csv(SALIDA / "sombra_por_modulo_app_columnas.csv", index=False)
    m = sim.rename(columns={"col": "columna"}).merge(ref, on=["fachada", "fila", "columna"])
    res = {"parametros": p, "pilas_balcon_so": pilas}
    for f in ("SO", "SE"):
        x = m[m.fachada == f]; el = x[x.ref < 2]
        res[f] = {"media_ref": round(float(x.ref.mean()), 2), "media_app": round(float(x.sombra_pct.mean()), 2),
                  "correlacion_por_modulo": round(float(np.corrcoef(x.ref, x.sombra_pct)[0, 1]), 3),
                  "error_medio_abs_por_modulo": round(float((x.ref - x.sombra_pct).abs().mean()), 2),
                  "elegidos_tesis": int(len(el)), "elegidos_ref_media": round(float(el.ref.mean()), 2),
                  "elegidos_app_media": round(float(el.sombra_pct.mean()), 2),
                  "elegidos_app_mayor_2": int((el.sombra_pct >= 2).sum())}
    (SALIDA / "verificacion.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k in ("SO", "SE")}, indent=1, ensure_ascii=False))
    pd.set_option("display.width", 250)
    print(m[m.fachada == "SO"].pivot(index="fila", columns="columna", values="sombra_pct").round(0).astype(int).to_string())


if __name__ == "__main__" and "--verificar" in sys.argv:
    verificar()


# ── Paso 4: energía con la escena recalibrada (mismo cálculo del script 5) ──
def energia(n_pilas=3):
    import shutil
    p, pilas = parametros_columnas(n_pilas)
    L.PILAS_BALCON_SO = pilas
    (SALIDA / "calibracion.json").write_text(json.dumps({"parametros": p}, indent=2, ensure_ascii=False),
                                             encoding="utf-8")
    shutil.copy(SALIDA / "sombra_por_modulo_app_columnas.csv", SALIDA / "sombra_por_modulo_app.csv")
    L.SALIDA = SALIDA                    # energia() lee y escribe aquí
    L.energia()


if __name__ == "__main__" and "--energia-columnas" in sys.argv:
    energia()
