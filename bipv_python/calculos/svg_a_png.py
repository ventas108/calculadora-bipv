# -*- coding: utf-8 -*-
"""Gráficas SVG del 📄 Reporte PDF convertidas a imagen PNG.

Spec ``07-informes/reporte-word-pdf`` (1-oct-2026). Word no muestra los SVG
del reporte: al abrir el HTML en Word se perdían las 6 gráficas (curva
eléctrica, producción mensual, vista 3D, luz en el suelo, mapa de sombra y
plano eléctrico). Este módulo dibuja con Pillow el subconjunto de SVG que
genera el propio reporte (``rect``, ``line``, ``polyline``, ``polygon``,
``circle`` y ``text`` con ``viewBox``), sin librerías externas de sistema.
Módulo puro: sin Streamlit.
"""
from __future__ import annotations

import io
import os
import re
from functools import lru_cache

from lxml import etree
from PIL import Image, ImageColor, ImageDraw, ImageFont

_NOMBRES = {"none": None, "transparent": None}


def _color(valor: str | None, opacidad: float = 1.0):
    """Color SVG → (r, g, b, a) o None."""
    if valor is None:
        return None
    v = str(valor).strip()
    if v.lower() in _NOMBRES:
        return None
    m = re.fullmatch(r"rgba?\(([^)]*)\)", v)
    try:
        if m:
            partes = [p.strip() for p in m.group(1).split(",")]
            r, g, b = (int(float(x)) for x in partes[:3])
            a = float(partes[3]) if len(partes) > 3 else 1.0
        else:
            r, g, b = ImageColor.getrgb(v)[:3]
            a = 1.0
    except (ValueError, TypeError):
        return None
    return (r, g, b, max(0, min(255, round(255 * a * opacidad))))


def _num(valor, defecto: float = 0.0) -> float:
    try:
        return float(str(valor).replace("px", ""))
    except (TypeError, ValueError):
        return defecto


@lru_cache(maxsize=32)
def _fuente(tam: int, negrita: bool):
    import matplotlib
    carpeta = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    archivo = "DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(os.path.join(carpeta, archivo), max(int(tam), 6))
    except OSError:
        return ImageFont.load_default()


def _puntos(texto: str, esc: float, dx: float, dy: float) -> list[tuple[float, float]]:
    nums = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", texto or "")]
    return [((nums[i] - dx) * esc, (nums[i + 1] - dy) * esc) for i in range(0, len(nums) - 1, 2)]


def _linea_discontinua(draw, pts, color, ancho, patron):
    if not patron:
        draw.line(pts, fill=color, width=ancho, joint="curve")
        return
    on, off = patron
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        largo = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        if largo == 0:
            continue
        ux, uy, t, dibuja = (x1 - x0) / largo, (y1 - y0) / largo, 0.0, True
        while t < largo:
            paso = min(on if dibuja else off, largo - t)
            if dibuja:
                draw.line([(x0 + ux * t, y0 + uy * t), (x0 + ux * (t + paso), y0 + uy * (t + paso))],
                          fill=color, width=ancho)
            t += paso
            dibuja = not dibuja


def svg_a_png(svg: str, ancho_px: int = 1600) -> bytes:
    """PNG (bytes) de un SVG del reporte, con ``ancho_px`` de ancho y fondo blanco."""
    raiz = etree.fromstring(svg.encode("utf-8"), parser=etree.XMLParser(recover=True, huge_tree=True))
    # El parser de HTML pasa los atributos a minúsculas: viewBox → viewbox.
    vb = [float(x) for x in re.split(r"[ ,]+", (raiz.get("viewBox") or raiz.get("viewbox") or "").strip()) if x]
    if len(vb) != 4:
        vb = [0.0, 0.0, _num(raiz.get("width"), 680), _num(raiz.get("height"), 300)]
    dx, dy, vw, vh = vb
    esc = ancho_px / vw
    alto_px = max(int(round(vh * esc)), 1)
    lienzo = Image.new("RGBA", (int(ancho_px), alto_px), (255, 255, 255, 255))
    capa = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(capa)

    def _vaciar():
        nonlocal capa, draw
        lienzo.alpha_composite(capa)
        capa = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(capa)

    for el in raiz.iter():
        tag = etree.QName(el).localname if isinstance(el.tag, str) else ""
        fill_op = _num(el.get("fill-opacity"), 1.0) * _num(el.get("opacity"), 1.0)
        fill = _color(el.get("fill", "black" if tag in ("rect", "polygon", "circle", "text") else "none"), fill_op)
        stroke = _color(el.get("stroke"), _num(el.get("stroke-opacity"), 1.0))
        ancho = max(int(round(_num(el.get("stroke-width"), 1.0) * esc)), 1)
        patron = [float(x) * esc for x in re.findall(r"\d+(?:\.\d+)?", el.get("stroke-dasharray") or "")][:2]
        if len(patron) == 1:
            patron = patron * 2
        translucido = fill is not None and fill[3] < 255
        if translucido:
            _vaciar()
        if tag == "rect":
            x0, y0 = (_num(el.get("x")) - dx) * esc, (_num(el.get("y")) - dy) * esc
            x1, y1 = x0 + _num(el.get("width")) * esc, y0 + _num(el.get("height")) * esc
            if x1 > x0 and y1 > y0:
                rx = _num(el.get("rx")) * esc
                if rx > 0:
                    draw.rounded_rectangle([x0, y0, x1, y1], radius=rx, fill=fill, outline=stroke,
                                           width=ancho if stroke else 0)
                else:
                    draw.rectangle([x0, y0, x1, y1], fill=fill, outline=stroke, width=ancho if stroke else 0)
        elif tag == "line":
            pts = [((_num(el.get("x1")) - dx) * esc, (_num(el.get("y1")) - dy) * esc),
                   ((_num(el.get("x2")) - dx) * esc, (_num(el.get("y2")) - dy) * esc)]
            if stroke:
                _linea_discontinua(draw, pts, stroke, ancho, patron)
        elif tag in ("polyline", "polygon"):
            pts = _puntos(el.get("points"), esc, dx, dy)
            if len(pts) >= 2:
                if tag == "polygon" and fill and len(pts) >= 3:
                    draw.polygon(pts, fill=fill)
                if tag == "polyline" and fill and len(pts) >= 3:
                    draw.polygon(pts, fill=fill)
                if stroke:
                    _linea_discontinua(draw, pts + ([pts[0]] if tag == "polygon" else []), stroke, ancho, patron)
        elif tag == "circle":
            cx, cy = (_num(el.get("cx")) - dx) * esc, (_num(el.get("cy")) - dy) * esc
            r = _num(el.get("r")) * esc
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=stroke, width=ancho if stroke else 0)
        elif tag == "text":
            texto = "".join(el.itertext()).strip()
            if texto and fill:
                tam = _num(el.get("font-size"), 12.0) * esc
                negrita = str(el.get("font-weight") or "").lower() in ("bold", "700", "800", "900")
                fuente = _fuente(int(round(tam)), negrita)
                x, y = (_num(el.get("x")) - dx) * esc, (_num(el.get("y")) - dy) * esc
                ancla = {"middle": "ms", "end": "rs"}.get(el.get("text-anchor") or "", "ls")
                draw.text((x, y), texto, fill=fill, font=fuente, anchor=ancla)
        if translucido:
            _vaciar()
    _vaciar()
    salida = io.BytesIO()
    lienzo.convert("RGB").save(salida, format="PNG", optimize=True)
    return salida.getvalue()
