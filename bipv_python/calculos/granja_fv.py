# -*- coding: utf-8 -*-
"""🌾 Granja FV — campo de filas (mesas) para granjas solares y agrivoltaicas.

Spec ``03-dimensionamiento/granja-fv-campo`` (fase 1, 30-sep-2026). Separa
el diseño de granjas de 🗺️ Vista 3D (BIPV) sin duplicar cálculos: este
módulo solo describe la geometría del campo y la compara con los datos que
ya usan Dimensionamiento, Producción y el modelo bifacial. La energía no
cambia en esta fase.

Geometría (ejes del campo: x a lo largo de la fila, y de adelante hacia
atrás; con azimut 180° la fila corre de Este a Oeste):

- Mesa: ``modulos_pendiente`` módulos en la pendiente × ``modulos_por_mesa``
  a lo largo de la fila, con 2 cm entre módulos.
- Ancho de mesa (en la pendiente) = módulos en la pendiente × lado del
  módulo en la pendiente + separaciones.
- Huella de adelante hacia atrás = ancho de mesa × cos(inclinación).
- GCR = ancho de mesa ÷ separación entre filas (pitch).
- Ángulo límite de sombra = atan(ancho × sen(incl.) ÷ (pitch − ancho ×
  cos(incl.))): con el sol más bajo que este ángulo (en el plano de perfil),
  una fila sombrea a la siguiente.

Módulo puro: sin Streamlit.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Any

SEP_MODULOS_M = 0.02
TOL_GCR = 0.02
TOL_ALTURA_M = 0.10
ASPECTO_ESTIMADO = 0.56   # ancho ÷ largo cuando la ficha no trae dimensiones

GEOMETRIA_DEFECTO: dict[str, Any] = {
    "tilt_deg": 20.0,
    "azimut_deg": 180.0,
    "ancho_terreno_m": 50.0,
    "largo_terreno_m": 50.0,
    "modulos_pendiente": 2,
    "orientacion": "horizontal",   # «horizontal»: el lado corto va en la pendiente
    "modulos_por_mesa": 20,
    "mesas_por_fila": 1,
    "pasillo_m": 3.0,
    "pitch_m": 6.0,
    "altura_libre_m": 1.0,
}
CAMPOS_EDITABLES = ("ancho_terreno_m", "largo_terreno_m", "modulos_pendiente", "orientacion",
                    "modulos_por_mesa", "mesas_por_fila", "pasillo_m", "pitch_m", "altura_libre_m")


def dimensiones_modulo(panel: Mapping[str, Any] | None) -> dict:
    """Largo y ancho del módulo (m): de la ficha, o estimados desde el área."""
    panel = panel or {}
    m = re.search(r"(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)", str(panel.get("dimensiones_mm") or ""))
    if m:
        a, b = float(m.group(1)) / 1000.0, float(m.group(2)) / 1000.0
        return {"largo_m": max(a, b), "ancho_m": min(a, b), "origen": "ficha"}
    if panel.get("largo_mm") and panel.get("ancho_mm"):
        a, b = float(panel["largo_mm"]) / 1000.0, float(panel["ancho_mm"]) / 1000.0
        return {"largo_m": max(a, b), "ancho_m": min(a, b), "origen": "ficha"}
    area = float(panel.get("area_m2") or 1.6)
    largo = math.sqrt(area / ASPECTO_ESTIMADO)
    return {"largo_m": largo, "ancho_m": area / largo, "origen": "estimado"}


def _lados(dims: Mapping[str, Any], orientacion: str) -> tuple[float, float]:
    """(lado en la pendiente, lado a lo largo de la fila)."""
    if orientacion == "vertical":
        return float(dims["largo_m"]), float(dims["ancho_m"])
    return float(dims["ancho_m"]), float(dims["largo_m"])


def _medidas_mesa(geo: Mapping[str, Any], dims: Mapping[str, Any]) -> dict:
    d_pend, d_fila = _lados(dims, geo["orientacion"])
    mp, mm = int(geo["modulos_pendiente"]), int(geo["modulos_por_mesa"])
    ancho = mp * d_pend + (mp - 1) * SEP_MODULOS_M
    t = math.radians(float(geo["tilt_deg"]))
    return {
        "d_pend": d_pend, "d_fila": d_fila,
        "ancho_mesa_m": ancho,
        "largo_mesa_m": mm * d_fila + (mm - 1) * SEP_MODULOS_M,
        "huella_ns_m": ancho * math.cos(t),
        "elevacion_m": ancho * math.sin(t),
    }


def calcular_campo(geo: Mapping[str, Any], dims: Mapping[str, Any], n_modulos: int,
                   pmax_w: float) -> dict:
    """Distribución de ``n_modulos`` en filas de mesas dentro del terreno."""
    med = _medidas_mesa(geo, dims)
    W, L = float(geo["ancho_terreno_m"]), float(geo["largo_terreno_m"])
    pitch = float(geo["pitch_m"])
    mp, mm, nmesas = int(geo["modulos_pendiente"]), int(geo["modulos_por_mesa"]), int(geo["mesas_por_fila"])
    h0 = float(geo["altura_libre_m"])
    ancho, huella, dz = med["ancho_mesa_m"], med["huella_ns_m"], med["elevacion_m"]
    largo_fila = nmesas * med["largo_mesa_m"] + (nmesas - 1) * float(geo["pasillo_m"])

    errores = []
    if pitch <= huella:
        errores.append(f"Las filas se tocan: la separación entre filas ({pitch:.2f} m) es menor o igual "
                       f"que la huella de la mesa ({huella:.2f} m). Aumenta la separación.")
    if largo_fila > W:
        errores.append(f"La fila mide {largo_fila:.1f} m y el terreno tiene {W:.1f} m a lo largo de la "
                       "fila. Baja los módulos por mesa o las mesas por fila.")
    if huella > L:
        errores.append(f"Una mesa ocupa {huella:.2f} m de adelante hacia atrás y el terreno tiene "
                       f"{L:.1f} m.")

    mod_mesa = mp * mm
    mod_fila = mod_mesa * nmesas
    filas_caben = int(math.floor((L - huella) / pitch + 1e-9)) + 1 if (huella <= L and pitch > 0) else 0
    capacidad = filas_caben * mod_fila if largo_fila <= W else 0
    n = max(int(n_modulos or 0), 0)
    colocados = min(n, capacidad)
    filas_usadas = math.ceil(colocados / mod_fila) if mod_fila and colocados else 0

    # Ubicación: filas centradas en el terreno, mesas de izquierda a derecha;
    # la última mesa puede quedar incompleta (columnas completas de módulos).
    mesas = []
    marg_y = max((L - ((filas_usadas - 1) * pitch + huella)) / 2.0, 0.0) if filas_usadas else 0.0
    marg_x = max((W - largo_fila) / 2.0, 0.0)
    restantes = colocados
    for f in range(filas_usadas):
        y0 = marg_y + f * pitch
        for k in range(nmesas):
            if restantes <= 0:
                break
            n_mesa = min(mod_mesa, restantes)
            cols = math.ceil(n_mesa / mp)
            x0 = marg_x + k * (med["largo_mesa_m"] + float(geo["pasillo_m"]))
            ancho_x = cols * med["d_fila"] + (cols - 1) * SEP_MODULOS_M
            mesas.append({"fila": f, "x0": x0, "x1": x0 + ancho_x, "y0": y0, "y1": y0 + huella,
                          "z0": h0, "z1": h0 + dz, "modulos": n_mesa})
            restantes -= n_mesa

    proy = sum((m["x1"] - m["x0"]) * (m["y1"] - m["y0"]) for m in mesas)
    angulo = (math.degrees(math.atan2(dz, pitch - huella)) if pitch > huella else 90.0)
    return {
        **med,
        "gcr": ancho / pitch if pitch > 0 else 0.0,
        "angulo_limite_deg": angulo,
        "corredor_m": pitch - huella,
        "altura_superior_m": h0 + dz,
        "altura_centro_m": h0 + dz / 2.0,
        "largo_fila_m": largo_fila,
        "modulos_por_fila": mod_fila,
        "filas_caben": filas_caben,
        "capacidad": capacidad,
        "modulos_proyecto": n,
        "modulos_colocados": colocados,
        "faltan": n - colocados,
        "filas_usadas": filas_usadas,
        "mesas_por_fila": nmesas,
        "cabe": bool(n > 0 and colocados == n and not errores),
        "errores": errores,
        "kwp": round(colocados * float(pmax_w) / 1000.0, 3),
        "area_modulos_m2": colocados * float(dims["largo_m"]) * float(dims["ancho_m"]),
        "area_terreno_m2": W * L,
        "suelo_libre_pct": 100.0 * (1.0 - proy / (W * L)) if W * L > 0 else 0.0,
        "mesas": mesas,
        "ancho_terreno_m": W, "largo_terreno_m": L,
        "tilt_deg": float(geo["tilt_deg"]), "azimut_deg": float(geo["azimut_deg"]),
        "dims_origen": dims.get("origen"),
    }


def sugerir_distribucion(n_modulos: int, dims: Mapping[str, Any], geo: Mapping[str, Any]) -> dict | None:
    """Menos filas (una mesa por fila) en las que caben todos los módulos."""
    med = _medidas_mesa(dict(geo, modulos_por_mesa=1), dims)
    W, L, pitch = float(geo["ancho_terreno_m"]), float(geo["largo_terreno_m"]), float(geo["pitch_m"])
    mp = int(geo["modulos_pendiente"])
    if n_modulos <= 0 or pitch <= med["huella_ns_m"] or med["huella_ns_m"] > L:
        return None
    max_filas = int(math.floor((L - med["huella_ns_m"]) / pitch + 1e-9)) + 1
    for filas in range(1, max_filas + 1):
        mm = math.ceil(n_modulos / (filas * mp))
        if mm * med["d_fila"] + (mm - 1) * SEP_MODULOS_M <= W:
            return {"modulos_por_mesa": mm, "mesas_por_fila": 1}
    return None


def modulos_del_proyecto(estado: Mapping[str, Any]) -> dict:
    """Módulos a ubicar: los que simuló 📊 Producción o, si no, los de 📐 Dimensionamiento."""
    final = int(estado.get("N_paneles_final") or 0)
    dim = int(estado.get("N_paneles_granja") or 0)
    if final > 0:
        return {"n": final, "fuente": "produccion", "dimensionamiento": dim}
    if dim > 0:
        return {"n": dim, "fuente": "dimensionamiento", "dimensionamiento": dim}
    return {"n": 0, "fuente": None, "dimensionamiento": 0}


def geometria_desde_estado(estado: Mapping[str, Any], dims: Mapping[str, Any] | None = None) -> dict:
    """Geometría guardada (``granja_fv``) con inclinación y azimut de 🏠 Proyecto.

    Sin datos guardados: terreno cuadrado con el área de 🏠 Proyecto, separación
    entre filas desde el GCR del modelo bifacial (o el factor de ocupación) y
    altura libre desde la altura del modelo bifacial.
    """
    g = dict(GEOMETRIA_DEFECTO)
    g["tilt_deg"] = float(estado.get("tilt_fachada", g["tilt_deg"]) or 0.0)
    g["azimut_deg"] = float(estado.get("azimuth_fachada", g["azimut_deg"]) or 0.0)
    area = float(estado.get("area_fachada_m2") or 0.0)
    if area > 0:
        g["ancho_terreno_m"] = g["largo_terreno_m"] = math.sqrt(area)
    guardado = dict(estado.get("granja_fv") or {})
    bif = dict(estado.get("bifacial_cfg") or {})
    if dims is not None:
        med = _medidas_mesa(g, dims)
        if "pitch_m" not in guardado:
            gcr = float(bif.get("gcr") or 0) or float(estado.get("factor_ocupacion_pct") or 0) / 100.0
            if 0.05 <= gcr <= 0.95:
                g["pitch_m"] = round(med["ancho_mesa_m"] / gcr, 2)
        if "altura_libre_m" not in guardado and bif.get("altura_m"):
            g["altura_libre_m"] = round(max(float(bif["altura_m"]) - med["elevacion_m"] / 2.0, 0.1), 2)
    for k in CAMPOS_EDITABLES:
        if k in guardado and guardado[k] is not None:
            g[k] = guardado[k]
    return g


def coherencia_campo(campo: Mapping[str, Any], estado: Mapping[str, Any]) -> list[dict]:
    """Comprobaciones del campo frente al resto del proyecto: ``{id, nivel, texto}``."""
    out: list[dict] = []
    mp = modulos_del_proyecto(estado)
    n = campo["modulos_proyecto"]
    if n <= 0:
        out.append({"id": "modulos", "nivel": "🟡",
                    "texto": "Todavía no hay módulos del proyecto: define el sistema en 📐 Dimensionamiento."})
    elif campo["cabe"]:
        out.append({"id": "modulos", "nivel": "🟢",
                    "texto": f"El campo aloja los {n} módulos del proyecto ({campo['kwp']:,.2f} kWp) en "
                             f"{campo['filas_usadas']} filas."})
    else:
        detalle = " ".join(campo["errores"]) or (
            f"Caben {campo['capacidad']} de {n}: faltan {campo['faltan']} módulos. Amplía el terreno, "
            "agrega filas o módulos por mesa, o presiona «Sugerir distribución».")
        out.append({"id": "modulos", "nivel": "🔴", "texto": detalle})
    if mp["fuente"] == "produccion" and mp["dimensionamiento"] and mp["dimensionamiento"] != mp["n"]:
        out.append({"id": "modulos_fuentes", "nivel": "🟠",
                    "texto": f"📊 Producción simuló {mp['n']} módulos y 📐 Dimensionamiento tiene "
                             f"{mp['dimensionamiento']}. Vuelve a simular Producción para que coincidan."})
    bif = dict(estado.get("bifacial_cfg") or {})
    if estado.get("bifacial_activo") and bif:
        gcr_b = bif.get("gcr")
        if gcr_b is not None:
            ok = abs(float(gcr_b) - campo["gcr"]) <= TOL_GCR
            out.append({"id": "gcr_bifacial", "nivel": "🟢" if ok else "🟠", "texto": (
                f"GCR del campo {campo['gcr']:.2f} = GCR del modelo bifacial {float(gcr_b):.2f}." if ok else
                f"El modelo bifacial de ☀️ Recurso Solar usa GCR {float(gcr_b):.2f} y tu campo tiene "
                f"{campo['gcr']:.2f}: la cara trasera se calcula con otro espaciado. Cámbialo en "
                f"☀️ Recurso Solar a {campo['gcr']:.2f} y recalcula.")})
        alt_b = bif.get("altura_m")
        if alt_b is not None:
            ok = abs(float(alt_b) - campo["altura_centro_m"]) <= TOL_ALTURA_M
            out.append({"id": "altura_bifacial", "nivel": "🟢" if ok else "🟠", "texto": (
                f"Altura del centro de la mesa {campo['altura_centro_m']:.2f} m = altura del modelo "
                f"bifacial {float(alt_b):.2f} m." if ok else
                f"El modelo bifacial de ☀️ Recurso Solar usa {float(alt_b):.2f} m de altura (centro del "
                f"panel) y en tu campo el centro de la mesa queda a {campo['altura_centro_m']:.2f} m. "
                f"Cámbialo en ☀️ Recurso Solar a {campo['altura_centro_m']:.2f} m y recalcula.")})
    f_ocup = float(estado.get("factor_ocupacion_pct") or 0.0)
    if 0 < f_ocup < 100:
        ok = abs(f_ocup / 100.0 - campo["gcr"]) <= 0.05
        out.append({"id": "ocupacion", "nivel": "🟢" if ok else "🟡", "texto":
                    f"Factor de ocupación de 🏠 Proyecto {f_ocup:.0f} % · GCR del campo "
                    f"{campo['gcr'] * 100:.1f} %" + ("." if ok else
                    ": representan lo mismo (fracción del suelo con paneles); conviene igualarlos.")})
    area = float(estado.get("area_fachada_m2") or 0.0)
    if area > 0 and abs(campo["area_terreno_m2"] - area) > 0.05 * area:
        out.append({"id": "terreno", "nivel": "🟡", "texto":
                    f"El terreno dibujado mide {campo['area_terreno_m2']:,.0f} m² y 🏠 Proyecto dice "
                    f"{area:,.0f} m²."})
    if estado.get("multisup_activo"):
        out.append({"id": "multisuperficie", "nivel": "🟠", "texto":
                    "🗺️ Vista 3D tiene energía multi-superficie publicada: 💰 Financiero, 🌿 CO₂ y 🔋 "
                    "Baterías usan esa energía y no la de 📊 Producción. Si el proyecto es solo esta "
                    "granja, desactívala en 🗺️ Vista 3D › Integrar al análisis financiero."})
    tipo = str(estado.get("tipo_instalacion") or "")
    if tipo and tipo != "Granja fotovoltaica":
        out.append({"id": "tipo", "nivel": "🟡", "texto":
                    f"El proyecto es tipo «{tipo}» en 🏠 Proyecto; este módulo está pensado para granjas."})
    return out


def trazas_campo(campo: Mapping[str, Any], color: str = "rgb(52,101,164)") -> list:
    """Suelo y mesas del campo como ``plotly`` Mesh3d (ejes del campo, metros)."""
    import plotly.graph_objects as go

    W, L = campo["ancho_terreno_m"], campo["largo_terreno_m"]
    suelo = go.Mesh3d(
        x=[0, W, W, 0], y=[0, 0, L, L], z=[0, 0, 0, 0], i=[0, 0], j=[1, 2], k=[2, 3],
        color="rgb(46,125,50)", opacity=0.95, name="Suelo / cultivo", showlegend=True,
        hovertext=f"🌱 Suelo libre bajo y entre filas: {campo['suelo_libre_pct']:.0f} %", hoverinfo="text",
    )
    xs, ys, zs, fi, fj, fk = [], [], [], [], [], []
    for m in campo["mesas"]:
        b = len(xs)
        xs += [m["x0"], m["x1"], m["x1"], m["x0"]]
        ys += [m["y0"], m["y0"], m["y1"], m["y1"]]
        zs += [m["z0"], m["z0"], m["z1"], m["z1"]]
        fi += [b, b]; fj += [b + 1, b + 2]; fk += [b + 2, b + 3]
    mesas = go.Mesh3d(
        x=xs, y=ys, z=zs, i=fi, j=fj, k=fk, color=color, opacity=1.0,
        name="Mesas de paneles", showlegend=True, hoverinfo="text",
        hovertext=(f"☀️ {campo['modulos_colocados']} módulos · {campo['filas_usadas']} filas · "
                   f"GCR {campo['gcr'] * 100:.1f} % · inclinación {campo['tilt_deg']:.0f}° · "
                   f"corredor {campo['corredor_m']:.1f} m"),
    )
    return [suelo, mesas]
