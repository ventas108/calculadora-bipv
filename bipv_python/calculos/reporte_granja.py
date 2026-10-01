# -*- coding: utf-8 -*-
"""Gráficas y revisiones de 🌾 Granja FV para el 📄 Reporte PDF.

Spec ``07-informes/reporte-granja-completo`` (1-oct-2026). La página de la
granja dibuja con plotly (interactivo); el reporte necesita imágenes fijas que
se impriman igual en el navegador, en Word y en PDF. Aquí se redibujan en SVG
puro, con los MISMOS datos que la página:

* la vista 3D del campo (sección 9 de la página): terreno, postes y cada
  módulo con el color del inversor al que va conectado;
* el plano eléctrico (sección 8): cada módulo con el color de su inversor y
  dos tonos alternos para distinguir un string del siguiente, los inversores
  y la ruta AC al punto de conexión;
* la luz en el suelo entre dos filas y el mapa de sombra mensual (sección 6);
* el paso de la maquinaria y las revisiones de coherencia del campo.

Nunca recalcula energía ni guarda nada en el estado. Módulo puro: sin Streamlit.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from html import escape
from typing import Any

COLORES_INVERSOR = ["#3465A4", "#E69138", "#2E7D32", "#8E44AD", "#C0392B", "#16A085"]
_COLOR_SIN_INVERSOR = "#7F8C8D"
_MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def color_inversor(inversor: int | None) -> str:
    if not inversor:
        return _COLOR_SIN_INVERSOR
    return COLORES_INVERSOR[(int(inversor) - 1) % len(COLORES_INVERSOR)]


def _aclarar(color: str, t: float) -> str:
    """Mezcla ``color`` (#RRGGBB) con blanco en proporción ``t``."""
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(c + (255 - c) * t):02X}" for c in (r, g, b))


# ── Datos del campo ──────────────────────────────────────────────────────────
def campo_desde_estado(estado: Mapping[str, Any]) -> dict | None:
    """Campo de la granja con sus mesas, calculado como en 🌾 Granja FV (None si no hay campo válido)."""
    if str(estado.get("tipo_instalacion") or "") != "Granja fotovoltaica" or not estado.get("granja_fv"):
        return None
    from calculos.granja_fv import calcular_campo, dimensiones_modulo, geometria_desde_estado, modulos_del_proyecto

    panel = dict(estado.get("panel_dict") or {})
    dims = dimensiones_modulo(panel)
    campo = calcular_campo(geometria_desde_estado(estado, dims), dims, modulos_del_proyecto(estado)["n"],
                           float(panel.get("Pmax_stc") or 0.0))
    return campo if campo["mesas"] and not campo["errores"] else None


def modulos_del_campo(campo: Mapping[str, Any], diseno: Mapping[str, Any] | None = None) -> list[dict]:
    """Cada módulo con su fila, posición, string e inversor.

    Recorre los módulos en el mismo orden que ``granja_electrico.armar_strings``
    (filas en orden, mesas de izquierda a derecha, columna por columna), así el
    módulo k pertenece al string ``k // n_serie + 1``.
    """
    d_fila, d_pend = float(campo["d_fila"]), float(campo["d_pend"])
    mp = max(int(round(campo["ancho_mesa_m"] / max(d_pend, 1e-9) + 0.01)), 1)
    paso = d_fila + 0.02
    n_serie = int((diseno or {}).get("n_serie") or 0)
    inv_de = {int(s["id"]): s.get("inversor") for s in (diseno or {}).get("strings") or []}
    out, k_global = [], 0
    for m in sorted(campo["mesas"], key=lambda m: (m["fila"], m["x0"])):
        for k in range(int(m["modulos"])):
            j = k % mp
            x = m["x0"] + (k // mp) * paso + d_fila / 2.0
            sid = k_global // n_serie + 1 if n_serie else None
            if sid is not None and sid not in inv_de:
                sid = None                       # módulo sobrante, sin string completo
            out.append({"fila": int(m["fila"]), "x": x, "j": j, "mp": mp, "mesa": m,
                        "string": sid, "inversor": inv_de.get(sid) if sid else None})
            k_global += 1
    return out


# ── Vista 3D (oblicua, escala real) ──────────────────────────────────────────
def svg_campo_3d(campo: Mapping[str, Any], diseno: Mapping[str, Any] | None = None,
                 W: int = 680) -> str:
    """Perspectiva del campo vista desde el frente: terreno, postes y módulos por inversor."""
    if not campo or not campo.get("mesas"):
        return ""
    Wt, Lt = float(campo["ancho_terreno_m"]), float(campo["largo_terreno_m"])
    k_x, k_y = 0.35, 0.5                         # desplazamiento y escala de la profundidad
    z_top = max(m["z1"] for m in campo["mesas"])

    def p(x, y, z):
        return x + k_x * y, -(k_y * y + z)

    ext_x, ext_y = Wt + k_x * Lt, k_y * Lt + z_top
    ml, mr, mt, mb = 12, 12, 30, 40
    esc = (W - ml - mr) / ext_x
    H = int(mt + mb + ext_y * esc)

    def sx(pt):
        return f"{ml + pt[0] * esc:.1f},{mt + (ext_y + pt[1]) * esc:.1f}"

    def poli(puntos, fill, stroke="none", sw=0.4, extra=""):
        return (f'<polygon points="{" ".join(sx(q) for q in puntos)}" fill="{fill}" stroke="{stroke}" '
                f'stroke-width="{sw}"{extra}/>')

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'style="max-width:100%;height:auto;font-family:Arial,sans-serif;">',
         f'<text x="{ml}" y="16" font-size="12" font-weight="bold" fill="#333">Vista 3D del campo — '
         f'{int(campo["modulos_colocados"]):,} módulos · {float(campo["kwp"]):,.2f} kWp · '
         f'GCR {float(campo["gcr"]) * 100:.1f} %</text>',
         poli([p(0, 0, 0), p(Wt, 0, 0), p(Wt, Lt, 0), p(0, Lt, 0)], "#E8F5E9", "#2E7D32", 1.0)]
    mods = modulos_del_campo(campo, diseno)
    d = float(campo["d_fila"]) / 2.0
    for fila in sorted({m["fila"] for m in mods}, reverse=True):          # de atrás hacia adelante
        mesas = [m for m in campo["mesas"] if m["fila"] == fila]
        for me in mesas:                                                  # postes en los extremos y al centro
            for x in (me["x0"], (me["x0"] + me["x1"]) / 2.0, me["x1"]):
                for y, z in ((me["y0"], me["z0"]), (me["y1"], me["z1"])):
                    a, b = p(x, y, 0), p(x, y, z)
                    s.append(f'<polyline points="{sx(a)} {sx(b)}" stroke="#8D8D8D" stroke-width="0.8"/>')
        for m in (m for m in mods if m["fila"] == fila):
            me, mp = m["mesa"], m["mp"]
            fy0, fy1 = m["j"] / mp, (m["j"] + 1) / mp
            y0, y1 = me["y0"] + (me["y1"] - me["y0"]) * fy0, me["y0"] + (me["y1"] - me["y0"]) * fy1
            z0, z1 = me["z0"] + (me["z1"] - me["z0"]) * fy0, me["z0"] + (me["z1"] - me["z0"]) * fy1
            c = color_inversor(m["inversor"])
            if m["string"] and m["string"] % 2 == 0:
                c = _aclarar(c, 0.35)
            s.append(poli([p(m["x"] - d, y0, z0), p(m["x"] + d, y0, z0), p(m["x"] + d, y1, z1),
                           p(m["x"] - d, y1, z1)], c, "#FFFFFF", 0.3))
    s.append(f'<text x="{ml}" y="{H - 22}" font-size="10" fill="#555">{Wt:,.0f} m a lo largo de la fila · {Lt:,.0f} m de adelante hacia atrás · '
             f'altura libre {float(campo["mesas"][0]["z0"]):.2f} m</text>')
    s.append(f'<text x="{ml}" y="{H - 6}" font-size="10" fill="#555">▲ Frente de los paneles: azimut '
             f'{float(campo["azimut_deg"]):.0f}° · inclinación {float(campo["tilt_deg"]):.0f}° · escala real</text>')
    s += _leyenda_inversores(diseno, W - mr, mt - 8)
    s.append("</svg>")
    return "".join(s)


def _leyenda_inversores(diseno: Mapping[str, Any] | None, x_der: float, y: float) -> list[str]:
    bloques = (diseno or {}).get("bloques") or []
    out = []
    for i, b in enumerate(reversed(bloques)):
        x = x_der - 70 * (i + 1)
        out.append(f'<rect x="{x:.0f}" y="{y - 8:.0f}" width="10" height="10" fill="{color_inversor(b["inversor"])}"/>')
        out.append(f'<text x="{x + 14:.0f}" y="{y + 1:.0f}" font-size="10" fill="#333">INV-{b["inversor"]}</text>')
    return out


# ── Plano eléctrico (vista de planta) ────────────────────────────────────────
def svg_plano_electrico(campo: Mapping[str, Any], diseno: Mapping[str, Any] | None, W: int = 680) -> str:
    """Planta del campo: módulos por inversor y string, inversores y ruta AC al punto de conexión."""
    if not campo or not campo.get("mesas") or not diseno:
        return ""
    Wt, Lt = float(campo["ancho_terreno_m"]), float(campo["largo_terreno_m"])
    xs_inv = [float(b["x_inversor"]) for b in diseno["bloques"]] + [float(diseno["punto_conexion_xy"][0])]
    x_lo, x_hi = min([0.0] + xs_inv) - 2.0, max([Wt] + xs_inv) + 2.0
    ml, mr, mt, mb = 70, 50, 30, 44
    esc = min((W - ml - mr) / (x_hi - x_lo), 560.0 / Lt)
    H = int(mt + mb + Lt * esc)

    def X(x):
        return ml + (x - x_lo) * esc

    def Y(y):                                   # el frente (y = 0) abajo
        return mt + (Lt - y) * esc

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'style="max-width:100%;height:auto;font-family:Arial,sans-serif;">',
         f'<text x="{ml}" y="16" font-size="12" font-weight="bold" fill="#333">Plano eléctrico — '
         f'{diseno["n_strings"]} strings de {diseno["n_serie"]} módulos · reparto '
         f'{" + ".join(str(r) for r in diseno["reparto"])}</text>',
         f'<rect x="{X(0):.1f}" y="{Y(Lt):.1f}" width="{Wt * esc:.1f}" height="{Lt * esc:.1f}" '
         f'fill="#F1F8E9" stroke="#2E7D32" stroke-width="1"/>']
    d = float(campo["d_fila"]) / 2.0
    primero: dict[int, dict] = {}
    for m in modulos_del_campo(campo, diseno):
        me, mp = m["mesa"], m["mp"]
        y0 = me["y0"] + (me["y1"] - me["y0"]) * m["j"] / mp
        y1 = me["y0"] + (me["y1"] - me["y0"]) * (m["j"] + 1) / mp
        c = color_inversor(m["inversor"])
        if m["string"] and m["string"] % 2 == 0:
            c = _aclarar(c, 0.4)
        s.append(f'<rect x="{X(m["x"] - d):.1f}" y="{Y(y1):.1f}" width="{2 * d * esc:.1f}" '
                 f'height="{(y1 - y0) * esc:.1f}" fill="{c}" stroke="#FFFFFF" stroke-width="0.3"/>')
        if m["string"] and m["string"] not in primero:
            primero[m["string"]] = m
    for sid, m in primero.items():               # número del string en su primer módulo
        me = m["mesa"]
        s.append(f'<text x="{X(m["x"]):.1f}" y="{Y(me["y1"]) - 1.5:.1f}" font-size="7" fill="#222" '
                 f'text-anchor="middle">{sid}</text>')
    for fila in sorted({me["fila"] for me in campo["mesas"]}):
        me = next(me for me in campo["mesas"] if me["fila"] == fila)
        s.append(f'<text x="{X(x_hi) + 4:.1f}" y="{Y((me["y0"] + me["y1"]) / 2) + 3:.1f}" font-size="8" '
                 f'fill="#666">Fila {fila + 1}</text>')
    x_poi, y_poi = (float(v) for v in diseno["punto_conexion_xy"])
    for b in diseno["bloques"]:
        c = color_inversor(b["inversor"])
        xi, yi = float(b["x_inversor"]), float(b["y_inversor"])
        s.append(f'<polyline points="{X(xi):.1f},{Y(yi):.1f} {X(x_poi):.1f},{Y(yi):.1f} {X(x_poi):.1f},'
                 f'{Y(y_poi):.1f}" fill="none" stroke="{c}" stroke-width="1.4" stroke-dasharray="4,3"/>')
        s.append(f'<rect x="{X(xi) - 6:.1f}" y="{Y(yi) - 6:.1f}" width="12" height="12" fill="{c}" '
                 f'stroke="#222" stroke-width="0.8"/>')
        s.append(f'<text x="{X(xi) - 9:.1f}" y="{Y(yi) + 4:.1f}" font-size="9" font-weight="bold" '
                 f'fill="#222" text-anchor="end">INV-{b["inversor"]}</text>')
    s.append(f'<text x="{X(x_poi):.1f}" y="{Y(y_poi) + 5:.1f}" font-size="15" text-anchor="middle" '
             f'fill="#000">★</text>')
    s.append(f'<text x="12" y="{H - 20}" font-size="10" fill="#555">▼ Frente del campo · ★ punto de conexión · '
             f'cuadros: inversores · línea punteada: cable AC</text>')
    s.append(f'<text x="12" y="{H - 6}" font-size="10" fill="#555">El número marca el primer módulo de cada '
             f'string; dos tonos alternos separan un string del siguiente.</text>')
    s += _leyenda_inversores(diseno, W - mr, mt - 8)
    s.append("</svg>")
    return "".join(s)


def texto_strings_cruzan(diseno: Mapping[str, Any] | None, campo: Mapping[str, Any] | None) -> str:
    """Explicación para el cliente cuando los strings pasan de una fila a la siguiente."""
    if not diseno or not campo or not diseno.get("strings_cruzan_filas"):
        return ""
    return (f"Cada string tiene {diseno['n_serie']} módulos y cada fila {int(campo['modulos_por_fila'])}: "
            f"{diseno['strings_cruzan_filas']} de los {diseno['n_strings']} strings continúan en la fila "
            "siguiente con un cable de unión entre filas. Es una conexión normal; en el plano se ve dónde "
            "empieza cada string.")


# ── Agrivoltaica ─────────────────────────────────────────────────────────────
def svg_luz_suelo(luz: Mapping[str, Any] | None, W: int = 680, H: int = 230) -> str:
    """Luz anual en el suelo entre dos filas (% del campo abierto)."""
    if not luz or not luz.get("y_m") or not luz.get("pct"):
        return ""
    ys, pct = [float(v) for v in luz["y_m"]], [float(v) for v in luz["pct"]]
    huella = float((luz.get("geometria") or {}).get("huella") or 0.0)
    ml, mr, mt, mb = 44, 10, 26, 34
    cw, ch = W - ml - mr, H - mt - mb
    y_lo, y_hi = min(ys), max(ys)

    def X(v):
        return ml + cw * (v - y_lo) / (y_hi - y_lo) if y_hi > y_lo else ml

    def Y(v):
        return mt + ch * (1 - v / 100.0)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'style="max-width:100%;height:auto;font-family:Arial,sans-serif;">',
         f'<text x="{ml}" y="15" font-size="12" font-weight="bold" fill="#333">Luz anual en el suelo entre '
         f'dos filas (% del terreno sin paneles)</text>']
    if huella > 0:
        s.append(f'<rect x="{X(y_lo):.1f}" y="{mt}" width="{X(min(huella, y_hi)) - X(y_lo):.1f}" height="{ch}" '
                 f'fill="#3465A4" fill-opacity="0.13"/>')
        s.append(f'<text x="{X(y_lo) + 4:.1f}" y="{mt + 12}" font-size="9" fill="#3465A4">bajo la mesa</text>')
    for g in (25, 50, 75, 100):
        s.append(f'<line x1="{ml}" y1="{Y(g):.1f}" x2="{W - mr}" y2="{Y(g):.1f}" stroke="#eee"/>')
        s.append(f'<text x="{ml - 4}" y="{Y(g) + 3:.1f}" font-size="9" fill="#999" text-anchor="end">{g} %</text>')
    s.append('<polyline fill="none" stroke="#2E7D32" stroke-width="2.5" points="'
             + " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in zip(ys, pct)) + '"/>')
    s.append(f'<text x="{ml + cw / 2:.1f}" y="{H - 6}" font-size="10" fill="#555" text-anchor="middle">'
             f'Posición desde el borde de una mesa hasta la siguiente (0 a {y_hi:.1f} m)</text>')
    s.append("</svg>")
    return "".join(s)


def _color_ylgn(v: float) -> str:
    paradas = [(0, (255, 255, 229)), (25, (217, 240, 163)), (50, (120, 198, 121)),
               (75, (35, 132, 67)), (100, (0, 69, 41))]
    v = min(max(float(v), 0.0), 100.0)
    for (a, ca), (b, cb) in zip(paradas, paradas[1:]):
        if v <= b:
            t = (v - a) / (b - a)
            return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))
    return "#004529"


def svg_mapa_luz_mensual(luz: Mapping[str, Any] | None, W: int = 680) -> str:
    """Mapa de sombra en el suelo: luz de cada mes en cada punto entre dos filas."""
    if not luz or not luz.get("mensual_pct") or not luz.get("y_m"):
        return ""
    z = [[float(v) for v in fila] for fila in luz["mensual_pct"]][:12]
    ys = [float(v) for v in luz["y_m"]]
    n = min(len(ys), min(len(f) for f in z))
    if n < 2 or len(z) < 12:
        return ""
    huella = float((luz.get("geometria") or {}).get("huella") or 0.0)
    ml, mr, mt, mb, alto = 36, 56, 26, 30, 15
    cw = W - ml - mr
    H = mt + mb + 12 * alto
    paso = cw / n
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'style="max-width:100%;height:auto;font-family:Arial,sans-serif;">',
         f'<text x="{ml}" y="15" font-size="12" font-weight="bold" fill="#333">Mapa de sombra en el suelo: '
         f'luz de cada mes (% del terreno sin paneles)</text>']
    for i in range(12):
        s.append(f'<text x="{ml - 4}" y="{mt + i * alto + 11}" font-size="9" fill="#555" '
                 f'text-anchor="end">{_MESES[i]}</text>')
        for k in range(n):
            s.append(f'<rect x="{ml + k * paso:.1f}" y="{mt + i * alto}" width="{paso + 0.3:.1f}" '
                     f'height="{alto}" fill="{_color_ylgn(z[i][k])}"/>')
    if huella > 0 and ys[-1] > ys[0]:
        xh = ml + cw * (huella - ys[0]) / (ys[-1] - ys[0])
        s.append(f'<line x1="{xh:.1f}" y1="{mt}" x2="{xh:.1f}" y2="{mt + 12 * alto}" stroke="#3465A4" '
                 f'stroke-width="1.5" stroke-dasharray="4,3"/>')
    for j, v in enumerate((0, 25, 50, 75, 100)):  # escala
        yy = mt + 12 * alto - j * (12 * alto) / 4
        s.append(f'<rect x="{W - mr + 8}" y="{yy - 10:.1f}" width="12" height="10" fill="{_color_ylgn(v)}"/>')
        s.append(f'<text x="{W - mr + 24}" y="{yy - 2:.1f}" font-size="9" fill="#555">{v} %</text>')
    s.append(f'<text x="{ml + cw / 2:.1f}" y="{H - 8}" font-size="10" fill="#555" text-anchor="middle">'
             f'Posición entre dos filas (m) · la línea punteada marca el fin de la mesa</text>')
    s.append("</svg>")
    return "".join(s)


def maquinaria(estado: Mapping[str, Any], campo: Mapping[str, Any] | None) -> list[dict]:
    """¿Cabe la maquinaria? Con la altura y el ancho guardados en 🌾 Granja FV (o los de la página)."""
    if not campo or float(campo.get("gcr") or 0) <= 0:
        return []
    from calculos.agrivoltaica import paso_maquinaria

    return paso_maquinaria(campo, float(estado.get("granja_altura_maquinaria_m") or 2.5),
                           float(estado.get("granja_ancho_maquinaria_m") or 2.2))


def coherencia(estado: Mapping[str, Any], campo: Mapping[str, Any] | None) -> list[dict]:
    """Las mismas revisiones de la sección 4 de 🌾 Granja FV."""
    if not campo:
        return []
    from calculos.granja_fv import coherencia_campo

    return list(coherencia_campo(campo, estado))


def html_revisiones(revisiones: list[dict]) -> str:
    """Lista 🟢/🟡/🟠/🔴 para el reporte."""
    if not revisiones:
        return ""
    import re

    colores = {"🔴": "#c62828", "🟠": "#e67e22", "🟡": "#b7950b", "🟢": "#2e7d32"}

    def _texto(t):                                # **negrita** de Streamlit → <strong>
        return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escape(str(t or "")))

    filas = "".join(
        f'<li style="margin:3px 0;color:{colores.get(r.get("nivel"), "#333")};">{escape(str(r.get("nivel") or ""))} '
        f'<span style="color:#333;">{_texto(r.get("texto"))}</span></li>' for r in revisiones)
    return f'<ul style="list-style:none;padding-left:4px;margin:6px 0 10px;font-size:0.9em;">{filas}</ul>'
