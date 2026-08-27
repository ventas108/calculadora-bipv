# -*- coding: utf-8 -*-
"""
Ficha de Validación RETIE — dashboard ejecutivo + validaciones eléctricas
básicas para proyectos FV/BIPV, universal (no atado a un proyecto en
particular).

Origen: el usuario aportó un script aparte (dataclasses `frozen` fijas al
proyecto Urabá con exactamente 2 inversores, motor SVG propio sin
dependencias) con un tipo de documento que nuestro sistema no tenía: no un
diagrama de línea única (eso ya lo cubre `diagrama_unifilar.py`), sino una
ficha de una página con tarjetas KPI, un flujo simplificado de 5 bloques,
una tabla de cargas/protecciones y, lo más valioso, un MOTOR DE
VALIDACIÓN que hoy no existe en la app: Voc del string en frío vs Vdc
máxima del inversor, ventana MPPT, balance DC/AC entre inversores,
selección de breaker por calibre comercial, y banderas OK/PENDIENTE/ERROR
cuando falta un dato de ficha técnica (en vez de inventar el valor).

Se decidió (a pedido explícito del usuario, tras presentarle las 3
opciones) construir una página NUEVA con este módulo reutilizable, en vez
de fusionarlo con `diagrama_unifilar.py` -- son dos tipos de documento
distintos con propósitos distintos, igual que 📄 Reporte PDF y 🔍
Diagnóstico son páginas separadas aunque ambas describen el mismo
proyecto.

Separación deliberada en 3 capas (mismo patrón que diagrama_unifilar.py):
  1. construir_config_retie() -- normaliza datos del proyecto a una
     estructura neutral. No dibuja nada, no depende de Streamlit.
  2. calcular_retie() / validar_retie() -- cálculos y validaciones puras
     sobre ese config. Generaliza el motor original a N inversores (no 2
     fijos) vía `strings_por_inversor: list[int]`.
  3. generar_ficha_svg() -- dibuja el SVG a partir de config+cálculos+
     validaciones. Reutiliza (generalizado) el motor SVG del script
     original -- es liviano y sin dependencias, no hace falta schemdraw
     para este tipo de documento (no es un esquema eléctrico con símbolos
     normalizados, es una ficha/dashboard).

Con datos faltantes (Voc, Vmp, Isc, límites MPPT, Icc del PCC, esquema de
tierra), las validaciones correspondientes quedan en "PENDIENTE" en vez de
fallar o inventar un valor -- mismo criterio que
`construir_config_unifilar` ("dato faltante no es lo mismo que dato
inválido").

Limitación declarada: esta ficha, igual que el diagrama unifilar, es un
documento de apoyo para revisión -- NO sustituye memorias de cálculo,
estudio de cortocircuito, coordinación de protecciones, declaración de
cumplimiento, inspección ni firma de un ingeniero electricista
matriculado exigida por RETIE.
"""
from __future__ import annotations

from html import escape
from math import sqrt

from calculos.dimensionamiento import calcular_voc_string, calcular_vmp_string


CALIBRES_COMERCIALES_A = (
    16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 225, 250,
    300, 315, 350, 400, 500, 630, 800, 1000, 1250,
)


def calibre_comercial_superior(corriente_a: float) -> int | None:
    """Primer calibre comercial >= corriente_a. None si corriente_a es None
    o excede el mayor calibre de la tabla (caso raro, MT/grandes plantas --
    se declara None en vez de reventar, el llamador decide cómo avisarlo)."""
    if corriente_a is None:
        return None
    for calibre in CALIBRES_COMERCIALES_A:
        if calibre >= corriente_a:
            return calibre
    return None


# ══════════════════════════════════════════════════════════════════════════════
# 1. Config — capa de datos, sin dibujo
# ══════════════════════════════════════════════════════════════════════════════
def construir_config_retie(
    *,
    nombre_proyecto: str = "Proyecto BIPV",
    propietario: str = "",
    direccion: str = "",
    municipio: str = "",
    operador_red: str = "",
    disenador: str = "",
    matricula: str = "",
    plano: str = "DU-FV-001",
    revision: str = "0",
    fecha: str = "",
    panel_nombre: str = "",
    potencia_w: float = 0.0,
    voc_v: float | None = None,
    vmp_v: float | None = None,
    isc_a: float | None = None,
    coef_voc_pct_c: float | None = None,
    inversor_nombre: str = "",
    potencia_ac_kw_unidad: float = 0.0,
    n_inversores: int = 1,
    tension_salida_v: float | None = None,
    frecuencia_hz: float = 60.0,
    vdc_max_v: float | None = None,
    vmppt_min_v: float | None = None,
    vmppt_max_v: float | None = None,
    n_paneles: int = 0,
    n_serie: int = 0,
    strings_por_inversor: list[int] | None = None,
    temperatura_minima_diseno_c: float | None = None,
    factor_continuo: float = 1.25,
    corriente_cortocircuito_pcc_ka: float | None = None,
    esquema_tierra: str = "",
) -> dict:
    """
    Normaliza los datos de un proyecto FV/BIPV a la estructura que
    necesitan calcular_retie()/validar_retie()/generar_ficha_svg().

    strings_por_inversor: lista opcional, un entero por inversor (ej.
    [9, 8] para 2 inversores). Generaliza el motor original (que traía
    "strings_inversor_1"/"strings_inversor_2" fijos) a cualquier cantidad
    de inversores. Si no se da, el balance por inversor queda sin
    calcular (derivados en None) -- no se asume una distribución pareja
    que el llamador no confirmó.
    """
    n_strings = int(n_paneles // n_serie) if n_serie else None
    strings_por_inversor = list(strings_por_inversor) if strings_por_inversor else None

    return {
        "proyecto": {
            "nombre_proyecto": nombre_proyecto, "propietario": propietario,
            "direccion": direccion, "municipio": municipio,
            "operador_red": operador_red, "disenador": disenador,
            "matricula": matricula, "plano": plano, "revision": revision,
            "fecha": fecha,
        },
        "panel": {
            "nombre": panel_nombre, "potencia_w": potencia_w,
            "voc_v": voc_v, "vmp_v": vmp_v, "isc_a": isc_a,
            "coef_voc_pct_c": coef_voc_pct_c,
        },
        "inversor": {
            "nombre": inversor_nombre, "potencia_ac_kw_unidad": potencia_ac_kw_unidad,
            "cantidad": max(int(n_inversores), 1), "tension_salida_v": tension_salida_v,
            "frecuencia_hz": frecuencia_hz, "vdc_max_v": vdc_max_v,
            "vmppt_min_v": vmppt_min_v, "vmppt_max_v": vmppt_max_v,
        },
        "generador": {
            "n_paneles": n_paneles, "n_serie": n_serie, "n_strings": n_strings,
            "strings_por_inversor": strings_por_inversor,
        },
        "diseno": {
            "temperatura_minima_c": temperatura_minima_diseno_c,
            "factor_continuo": factor_continuo,
            "corriente_cortocircuito_pcc_ka": corriente_cortocircuito_pcc_ka,
            "esquema_tierra": esquema_tierra,
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# 2. Cálculos y validaciones — puros, sin dibujo
# ══════════════════════════════════════════════════════════════════════════════
def calcular_retie(cfg: dict) -> dict:
    """Deriva potencias, corrientes y breakers preliminares. Cualquier
    derivado cuyos insumos falten queda en None (o, para listas por
    inversor, en []) -- no se inventa un valor."""
    panel, inv, gen, diseno = cfg["panel"], cfg["inversor"], cfg["generador"], cfg["diseno"]
    fc = diseno["factor_continuo"]

    pdc = (
        round(gen["n_paneles"] * panel["potencia_w"] / 1000.0, 2)
        if gen["n_paneles"] and panel["potencia_w"] else None
    )
    pac = (
        round(inv["cantidad"] * inv["potencia_ac_kw_unidad"], 2)
        if inv["potencia_ac_kw_unidad"] else None
    )
    relacion_dc_ac = round(pdc / pac, 3) if pdc and pac else None

    tension = inv["tension_salida_v"]
    i_inversor = (
        round(inv["potencia_ac_kw_unidad"] * 1000.0 / (sqrt(3) * tension), 1)
        if inv["potencia_ac_kw_unidad"] and tension else None
    )
    i_total = (
        round(pac * 1000.0 / (sqrt(3) * tension), 1)
        if pac and tension else None
    )
    i_diseno = round(i_total * fc, 1) if i_total else None

    breaker_inversor = calibre_comercial_superior(i_inversor * fc) if i_inversor else None
    breaker_general = calibre_comercial_superior(i_diseno) if i_diseno else None

    pdc_por_inversor: list[float] = []
    dcac_por_inversor: list[float] = []
    if gen["strings_por_inversor"] and gen["n_serie"] and panel["potencia_w"]:
        for n_strings_inv in gen["strings_por_inversor"]:
            p = round(n_strings_inv * gen["n_serie"] * panel["potencia_w"] / 1000.0, 2)
            pdc_por_inversor.append(p)
            dcac_por_inversor.append(
                round(p / inv["potencia_ac_kw_unidad"], 3) if inv["potencia_ac_kw_unidad"] else None
            )

    # Voc/Vmp del string a 25°C (STC) -- caso particular de
    # calcular_voc_string/calcular_vmp_string con T_cel=25 (delta cero).
    # Se reutilizan esas funciones (calculos/dimensionamiento.py) en vez de
    # repetir la fórmula, para no arriesgarse a que diverjan con el tiempo
    # -- ese módulo ya documenta un bug real de confundir Tk_beta (Voc) con
    # Tk_gamma (potencia) en este mismo cálculo.
    voc_string_stc = (
        round(calcular_voc_string(gen["n_serie"], panel["voc_v"], 0.0, 25.0), 1)
        if panel["voc_v"] and gen["n_serie"] else None
    )
    vmp_string_stc = (
        round(calcular_vmp_string(gen["n_serie"], panel["vmp_v"], 0.0, 25.0), 1)
        if panel["vmp_v"] and gen["n_serie"] else None
    )
    isc_diseno = round(panel["isc_a"] * fc, 1) if panel["isc_a"] else None

    voc_string_frio = None
    if (
        panel["voc_v"] is not None and panel["coef_voc_pct_c"] is not None
        and diseno["temperatura_minima_c"] is not None and gen["n_serie"]
    ):
        voc_string_frio = round(
            calcular_voc_string(
                gen["n_serie"], panel["voc_v"], panel["coef_voc_pct_c"],
                diseno["temperatura_minima_c"],
            ),
            1,
        )

    return {
        "potencia_dc_kwp": pdc, "potencia_ac_kw": pac, "relacion_dc_ac": relacion_dc_ac,
        "corriente_inversor_a": i_inversor, "corriente_total_a": i_total,
        "corriente_diseno_total_a": i_diseno,
        "breaker_inversor_a": breaker_inversor, "breaker_general_a": breaker_general,
        "pdc_por_inversor_kwp": pdc_por_inversor, "dcac_por_inversor": dcac_por_inversor,
        "voc_string_stc_v": voc_string_stc, "voc_string_frio_v": voc_string_frio,
        "vmp_string_stc_v": vmp_string_stc, "isc_diseno_string_a": isc_diseno,
    }


def validar_retie(cfg: dict, calc: dict) -> list[dict]:
    """Lista de validaciones {"nivel": "OK"|"PENDIENTE"|"ERROR", "titulo",
    "detalle"}. Generalizado a N inversores (no 2 fijos)."""
    panel, inv, gen, diseno = cfg["panel"], cfg["inversor"], cfg["generador"], cfg["diseno"]
    out: list[dict] = []

    if gen["n_strings"] is not None:
        modulos_calc = gen["n_strings"] * gen["n_serie"]
        if modulos_calc == gen["n_paneles"]:
            out.append({"nivel": "OK", "titulo": "Cantidad de módulos",
                        "detalle": f"{gen['n_strings']} × {gen['n_serie']} = {gen['n_paneles']} módulos."})
        else:
            out.append({"nivel": "ERROR", "titulo": "Cantidad de módulos",
                        "detalle": f"{gen['n_strings']} strings × {gen['n_serie']} = {modulos_calc}, "
                                   f"pero se declararon {gen['n_paneles']} módulos (string incompleto)."})

    if gen["strings_por_inversor"]:
        asignados = sum(gen["strings_por_inversor"])
        if gen["n_strings"] is not None:
            if asignados == gen["n_strings"]:
                out.append({"nivel": "OK", "titulo": "Distribución de strings",
                            "detalle": " + ".join(str(n) for n in gen["strings_por_inversor"])
                                       + f" = {gen['n_strings']} strings."})
            else:
                out.append({"nivel": "ERROR", "titulo": "Distribución de strings",
                            "detalle": f"Se asignaron {asignados} de {gen['n_strings']} strings entre inversores."})

    if calc["relacion_dc_ac"] is None:
        out.append({"nivel": "PENDIENTE", "titulo": "Relación DC/AC total",
                    "detalle": "Faltan potencia DC o AC para calcularla."})
    elif 1.00 <= calc["relacion_dc_ac"] <= 1.35:
        out.append({"nivel": "OK", "titulo": "Relación DC/AC total",
                    "detalle": f"{calc['relacion_dc_ac']:.2f}; dentro del rango preliminar 1,00-1,35."})
    else:
        out.append({"nivel": "PENDIENTE", "titulo": "Relación DC/AC total",
                    "detalle": f"{calc['relacion_dc_ac']:.2f}; requiere justificación técnica."})

    dcac_list = [d for d in calc["dcac_por_inversor"] if d is not None]
    if len(dcac_list) >= 2:
        diferencia = max(dcac_list) - min(dcac_list)
        resumen = "; ".join(f"INV-{n+1:02d}={d:.2f}" for n, d in enumerate(dcac_list))
        if diferencia <= 0.10:
            out.append({"nivel": "OK", "titulo": "Balance entre inversores", "detalle": resumen + "."})
        else:
            out.append({"nivel": "PENDIENTE", "titulo": "Balance entre inversores",
                        "detalle": resumen + "; validar distribución por MPPT."})

    if calc["voc_string_frio_v"] is None:
        out.append({"nivel": "PENDIENTE", "titulo": "Voc del string en frío",
                    "detalle": "Faltan Voc, coeficiente de Voc o temperatura mínima de diseño."})
    elif inv["vdc_max_v"] is None:
        out.append({"nivel": "PENDIENTE", "titulo": "Voc del string en frío",
                    "detalle": f"Voc frío calculado={calc['voc_string_frio_v']:.1f} V; falta Vdc máxima "
                               "oficial del inversor."})
    elif calc["voc_string_frio_v"] < inv["vdc_max_v"]:
        out.append({"nivel": "OK", "titulo": "Voc del string en frío",
                    "detalle": f"{calc['voc_string_frio_v']:.1f} V < Vdc máx. {inv['vdc_max_v']:.1f} V."})
    else:
        out.append({"nivel": "ERROR", "titulo": "Voc del string en frío",
                    "detalle": f"{calc['voc_string_frio_v']:.1f} V >= Vdc máx. {inv['vdc_max_v']:.1f} V."})

    if calc["vmp_string_stc_v"] is None or inv["vmppt_min_v"] is None or inv["vmppt_max_v"] is None:
        out.append({"nivel": "PENDIENTE", "titulo": "Ventana MPPT",
                    "detalle": "Faltan Vmp del módulo o límites MPPT oficiales del inversor."})
    elif inv["vmppt_min_v"] <= calc["vmp_string_stc_v"] <= inv["vmppt_max_v"]:
        out.append({"nivel": "OK", "titulo": "Ventana MPPT",
                    "detalle": f"Vmp string={calc['vmp_string_stc_v']:.1f} V dentro de "
                               f"{inv['vmppt_min_v']:.0f}-{inv['vmppt_max_v']:.0f} V."})
    else:
        out.append({"nivel": "ERROR", "titulo": "Ventana MPPT",
                    "detalle": f"Vmp string={calc['vmp_string_stc_v']:.1f} V fuera de "
                               f"{inv['vmppt_min_v']:.0f}-{inv['vmppt_max_v']:.0f} V."})

    if diseno["corriente_cortocircuito_pcc_ka"] is None:
        out.append({"nivel": "PENDIENTE", "titulo": "Capacidad interruptiva",
                    "detalle": "Falta la corriente de cortocircuito disponible en el PCC."})
    else:
        out.append({"nivel": "PENDIENTE", "titulo": "Capacidad interruptiva",
                    "detalle": f"Icc PCC={diseno['corriente_cortocircuito_pcc_ka']:.2f} kA; seleccionar "
                               "Icu/Ics de interruptores y verificar coordinación."})

    if diseno["esquema_tierra"]:
        out.append({"nivel": "PENDIENTE", "titulo": "Sistema de puesta a tierra",
                    "detalle": f"Esquema declarado: {diseno['esquema_tierra']}; verificar resistividad, "
                               "electrodos, calibre PE y continuidad."})
    else:
        out.append({"nivel": "PENDIENTE", "titulo": "Sistema de puesta a tierra",
                    "detalle": "Falta definir esquema de tierra, electrodos, barra PE y calibres."})

    return out


# ══════════════════════════════════════════════════════════════════════════════
# 3. Dibujo (SVG) — a partir de config+cálculos+validaciones, sin saber de
#    dónde salieron. Motor SVG liviano sin dependencias (mismo criterio que
#    el script original que aportó el usuario) -- no hace falta schemdraw
#    para una ficha de tarjetas/tabla, a diferencia del esquema eléctrico
#    de diagrama_unifilar.py.
# ══════════════════════════════════════════════════════════════════════════════
COLORES = {
    "texto": "#172033", "azul": "#176B9D", "azul_claro": "#EAF4FB",
    "verde": "#16835D", "verde_claro": "#EAF7F0", "naranja": "#D26B14",
    "naranja_claro": "#FFF3E3", "rojo": "#C53030", "rojo_claro": "#FFF0F0",
    "gris": "#64748B", "gris_claro": "#F3F5F7", "fondo": "#F7F9FB",
}

_NIVEL_COLORES = {
    "OK": (COLORES["verde"], COLORES["verde_claro"], "OK"),
    "PENDIENTE": (COLORES["naranja"], COLORES["naranja_claro"], "!"),
    "ERROR": (COLORES["rojo"], COLORES["rojo_claro"], "X"),
}


class _SVG:
    def __init__(self, width: int = 1800, height: int = 1420):
        self.width = width
        self.height = height
        self.elementos: list[str] = []

    def rect(self, x, y, w, h, fill="#fff", stroke="#172033", sw=2, rx=8):
        self.elementos.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def text(self, x, y, texto, size=15, weight=400, fill=None, anchor="start"):
        self.elementos.append(
            f'<text x="{x}" y="{y}" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="{size}" font-weight="{weight}" '
            f'fill="{fill or COLORES["texto"]}" text-anchor="{anchor}">'
            f'{escape(str(texto))}</text>'
        )

    def line(self, x1, y1, x2, y2, color=None, width=4, arrow=False):
        marker = ' marker-end="url(#arrow)"' if arrow else ""
        self.elementos.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color or COLORES["texto"]}" stroke-width="{width}"{marker}/>'
        )

    def path(self, data, color=None, width=4):
        self.elementos.append(
            f'<path d="{data}" fill="none" stroke="{color or COLORES["texto"]}" stroke-width="{width}"/>'
        )

    def circle(self, cx, cy, r, fill="#fff", stroke="#172033", sw=2):
        self.elementos.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def multiline(self, x, y, lineas, size=14, step=21, fill=None, weight=400):
        for n, linea in enumerate(lineas):
            self.text(x, y + n * step, linea, size, weight, fill)

    def render(self) -> str:
        defs = (
            '<defs><marker id="arrow" markerWidth="10" markerHeight="10" '
            'refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" '
            f'fill="{COLORES["texto"]}"/></marker></defs>'
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" '
            f'height="{self.height}" viewBox="0 0 {self.width} {self.height}">\n'
            f'{defs}\n{"".join(self.elementos)}\n</svg>\n'
        )


def _fmt(valor: float | None, decimales: int = 1, unidad: str = "") -> str:
    """Formato numérico es-CO (coma decimal, punto de miles). None ->
    'PENDIENTE' en vez de un número inventado."""
    if valor is None:
        return "PENDIENTE"
    numero = f"{valor:,.{decimales}f}"
    numero = numero.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{numero}{unidad}"


def _tarjeta(d: _SVG, x, y, w, titulo, valor, subtitulo, color=COLORES["azul"]):
    d.rect(x, y, w, 105, "#FFFFFF", "#D9E2EC", 1, 10)
    d.rect(x, y, 8, 105, color, color, 0, 4)
    d.text(x + 24, y + 28, titulo.upper(), 12, 700, COLORES["gris"])
    d.text(x + 24, y + 64, valor, 27, 700, color)
    d.text(x + 24, y + 88, subtitulo, 12, 400, COLORES["gris"])


def _bloque(d: _SVG, x, y, w, h, titulo, lineas, fill=COLORES["azul_claro"], stroke=COLORES["azul"]):
    d.rect(x, y, w, h, fill, stroke, 2, 10)
    d.text(x + 22, y + 31, titulo, 17, 700, stroke)
    d.line(x + 20, y + 43, x + w - 20, y + 43, stroke, 1)
    d.multiline(x + 22, y + 70, lineas, 13, 20)


def _dibujar_validaciones(d: _SVG, validaciones: list[dict], x: float, y: float) -> None:
    d.text(x, y, "ESTADO DE VALIDACIÓN", 20, 700)
    d.text(x + 245, y, "Verde: correcto · Naranja: pendiente · Rojo: corregir", 12, 400, COLORES["gris"])
    columnas, ancho, alto, sep_x, sep_y = 4, 410, 92, 20, 16
    for n, v in enumerate(validaciones):
        fila, col = divmod(n, columnas)
        bx = x + col * (ancho + sep_x)
        by = y + 22 + fila * (alto + sep_y)
        color, fondo, simbolo = _NIVEL_COLORES[v["nivel"]]
        d.rect(bx, by, ancho, alto, fondo, color, 1, 8)
        d.circle(bx + 28, by + 28, 15, color, color, 1)
        d.text(bx + 28, by + 34, simbolo, 13, 700, "#fff", "middle")
        d.text(bx + 52, by + 27, v["titulo"], 14, 700, color)
        detalle, corte = v["detalle"], 54
        if len(detalle) > corte:
            punto = detalle.rfind(" ", 0, corte)
            punto = punto if punto > 25 else corte
            lineas = [detalle[:punto], detalle[punto:].strip()]
        else:
            lineas = [detalle]
        d.multiline(bx + 52, by + 52, lineas, 11, 17, COLORES["texto"])


def generar_ficha_svg(cfg: dict, calc: dict, checks: list[dict]) -> str:
    """Dibuja la ficha completa (SVG). Universal: el número de bloques del
    inversor y de filas de la tabla se ajustan a `inv['cantidad']`, no a 2
    fijos como en el script original."""
    proy, panel, inv, gen = cfg["proyecto"], cfg["panel"], cfg["inversor"], cfg["generador"]
    n_filas_validacion = -(-len(checks) // 4)  # techo de división, sin importar
    height = max(1420, 700 + n_filas_validacion * 108 + 400)
    d = _SVG(height=height)

    d.rect(0, 0, d.width, d.height, COLORES["fondo"], COLORES["fondo"], 0, 0)
    d.rect(25, 20, d.width - 50, d.height - 45, "#fff", COLORES["texto"], 2, 8)

    d.text(55, 60, "DIAGRAMA UNIFILAR FOTOVOLTAICO", 29, 700)
    d.text(55, 88, "Lectura ejecutiva para cliente + revisión técnica orientada a RETIE", 15, 400, COLORES["gris"])
    d.rect(d.width - 430, 40, 365, 65, COLORES["gris_claro"], "#CBD5E1", 1, 5)
    d.text(d.width - 410, 65, f"PLANO: {proy['plano']}", 12, 700)
    d.text(d.width - 410, 88, f"REV. {proy['revision']} · {proy['fecha']} · PARA REVISIÓN", 11, 400, COLORES["gris"])

    ancho_tarjeta = (d.width - 110 - 4 * 20) / 5
    tarjetas = [
        ("Potencia instalada", _fmt(calc["potencia_dc_kwp"], 2, " kWp"), "Generador fotovoltaico", COLORES["azul"]),
        ("Potencia nominal", _fmt(calc["potencia_ac_kw"], 0, " kW"), f"Salida total de {inv['cantidad']} inversor(es)", COLORES["azul"]),
        ("Relación DC/AC", _fmt(calc["relacion_dc_ac"], 2), "Relación global del sistema", COLORES["azul"]),
        ("Corriente nominal", _fmt(calc["corriente_total_a"], 1, " A"), "Salida trifásica", COLORES["azul"]),
        ("Protección preliminar", _fmt(calc["breaker_general_a"], 0, " A"), "Confirmar Icu/Ics y conductor", COLORES["naranja"]),
    ]
    for n, (titulo, valor, sub, color) in enumerate(tarjetas):
        _tarjeta(d, 55 + n * (ancho_tarjeta + 20), 125, ancho_tarjeta, titulo, valor, sub, color)

    d.text(55, 265, "FLUJO DE ENERGÍA Y PROTECCIONES", 20, 700)
    y = 300
    x, alto_flujo = 55, 235

    lineas_campo = [
        f"{gen['n_paneles']} × {panel['nombre'] or 'módulo FV'}",
        (f"{gen['n_strings']} strings × {gen['n_serie']} módulos" if gen["n_strings"] else "Strings: PENDIENTE"),
        f"Pdc = {_fmt(calc['potencia_dc_kwp'], 2, ' kWp')}",
        f"Voc string STC: {_fmt(calc['voc_string_stc_v'], 1, ' V')}",
        f"Voc string frío: {_fmt(calc['voc_string_frio_v'], 1, ' V')}",
        f"Isc diseño: {_fmt(calc['isc_diseno_string_a'], 1, ' A')}",
    ]
    _bloque(d, x, y, 270, alto_flujo, "1. CAMPO FV", lineas_campo)
    x += 270
    d.line(x, y + alto_flujo / 2, x + 55, y + alto_flujo / 2, COLORES["azul"], 5, True)
    x += 55

    _bloque(d, x, y, 240, alto_flujo, "2. PROTECCIÓN DC", [
        "Fusibles gPV (+/-)*", "Seccionador DC bajo carga*", "DPS DC Tipo 2*",
        "Cable solar H1Z2Z2-K*", "Ucpv >= Voc máxima", "*Dimensionar con ficha",
    ], COLORES["naranja_claro"], COLORES["naranja"])
    x += 240
    d.line(x, y + alto_flujo / 2, x + 55, y + alto_flujo / 2, COLORES["azul"], 5, True)
    x += 55

    lineas_inv = [f"{inv['cantidad']} × {inv['nombre'] or 'inversor'}"]
    if calc["pdc_por_inversor_kwp"]:
        for n, pdc_n in enumerate(calc["pdc_por_inversor_kwp"]):
            lineas_inv.append(f"INV-{n+1:02d}: {_fmt(pdc_n, 2, ' kWp')} → {_fmt(inv['potencia_ac_kw_unidad'], 0, ' kW')}")
    lineas_inv.append(f"I por inversor = {_fmt(calc['corriente_inversor_a'], 1, ' A')}")
    lineas_inv.append(f"QF preliminar = {_fmt(calc['breaker_inversor_a'], 0, ' A')}*")
    ancho_inv = 390
    _bloque(d, x, y, ancho_inv, alto_flujo, "3. INVERSORES", lineas_inv)
    x += ancho_inv
    d.line(x, y + alto_flujo / 2, x + 55, y + alto_flujo / 2, COLORES["rojo"], 5, True)
    x += 55

    _bloque(d, x, y, 295, alto_flujo, "4. TABLERO TGFV", [
        f"{_fmt(calc['potencia_ac_kw'], 0, ' kW')} · {_fmt(inv['tension_salida_v'], 0, ' V')} · 3F · 4H",
        f"I nominal = {_fmt(calc['corriente_total_a'], 1, ' A')}",
        f"I diseño 125% = {_fmt(calc['corriente_diseno_total_a'], 1, ' A')}",
        f"QF-G preliminar = {_fmt(calc['breaker_general_a'], 0, ' A')}*",
        "Icu/Ics: PENDIENTE", "Barras y conductor: PENDIENTE",
    ], COLORES["naranja_claro"], COLORES["naranja"])
    x += 295
    d.line(x, y + alto_flujo / 2, x + 55, y + alto_flujo / 2, COLORES["rojo"], 5, True)
    x += 55

    _bloque(d, x, y, d.width - 55 - x, alto_flujo, "5. PCC / RED", [
        "Medidor bidireccional", f"PCC: {_fmt(inv['tension_salida_v'], 0, ' V')}",
        f"{_fmt(inv['frecuencia_hz'], 0, ' Hz')} · trifásico", "Protección interfaz / anti-isla*",
        f"Operador: {cfg['proyecto']['operador_red'] or 'POR DEFINIR'}", "Icc PCC: PENDIENTE",
    ], COLORES["gris_claro"], COLORES["gris"])

    d.path(f"M190 {y+alto_flujo+50} V{y+alto_flujo+100} H{d.width-200} V{y+alto_flujo+50}", COLORES["verde"], 4)
    d.text(d.width / 2, y + alto_flujo + 93, "PE / EQUIPOTENCIALIDAD: módulos, estructuras, inversores, tableros, DPS y barra principal de tierra",
           12, 700, COLORES["verde"], "middle")

    y_tabla = y + alto_flujo + 160
    d.text(55, y_tabla - 25, "CUADRO DE CARGAS Y PROTECCIONES", 20, 700)
    anchos = [250, 185, 145, 165, 190, 245, d.width - 110 - (250+185+145+165+190+245)]
    encabezados = ["Circuito", "Potencia", "Tensión", "Corriente", "Protección", "Conductor", "Estado / observación"]

    filas = []
    for n in range(inv["cantidad"]):
        dcac_n = calc["dcac_por_inversor"][n] if n < len(calc["dcac_por_inversor"]) else None
        strings_n = gen["strings_por_inversor"][n] if gen["strings_por_inversor"] and n < len(gen["strings_por_inversor"]) else None
        obs = f"{strings_n} strings · DC/AC {dcac_n:.2f}" if strings_n and dcac_n else "Ver bloque 3"
        filas.append([
            f"INV-{n+1:02d} AC", _fmt(inv["potencia_ac_kw_unidad"], 0, " kW"),
            _fmt(inv["tension_salida_v"], 0, " V, 3F"), _fmt(calc["corriente_inversor_a"], 1, " A"),
            f"{_fmt(calc['breaker_inversor_a'], 0, ' A')}*", "Por calcular", obs,
        ])
    filas.append([
        "Alimentador general", _fmt(calc["potencia_ac_kw"], 0, " kW"),
        _fmt(inv["tension_salida_v"], 0, " V, 3F"), _fmt(calc["corriente_total_a"], 1, " A"),
        f"{_fmt(calc['breaker_general_a'], 0, ' A')}*", "Por calcular",
        f"I diseño={_fmt(calc['corriente_diseno_total_a'], 1, ' A')} · Icu/Ics pendiente",
    ])
    filas.append(["Puesta a tierra", "-", "-", "-", "-", "Por calcular", "Electrodos, barra PE y continuidad pendientes"])

    alto_fila = 45
    total_w = sum(anchos)
    d.rect(55, y_tabla, total_w, alto_fila, COLORES["texto"], COLORES["texto"], 1, 0)
    cursor = 55
    for ancho, titulo in zip(anchos, encabezados):
        d.text(cursor + 10, y_tabla + 28, titulo, 12, 700, "#fff")
        cursor += ancho
        d.line(cursor, y_tabla, cursor, y_tabla + alto_fila * (len(filas) + 1), "#CBD5E1", 1)
    for nf, fila in enumerate(filas):
        fy = y_tabla + alto_fila * (nf + 1)
        fondo = "#FFFFFF" if nf % 2 == 0 else COLORES["gris_claro"]
        d.rect(55, fy, total_w, alto_fila, fondo, "#CBD5E1", 1, 0)
        cursor = 55
        for ancho, valor in zip(anchos, fila):
            color = COLORES["naranja"] if "Por calcular" in valor or "pendiente" in valor.lower() else COLORES["texto"]
            d.text(cursor + 10, fy + 28, valor, 11, 400, color)
            cursor += ancho

    y_valid = y_tabla + alto_fila * (len(filas) + 1) + 60
    _dibujar_validaciones(d, checks, 55, y_valid)

    y_footer = d.height - 135
    d.rect(55, y_footer, d.width - 110 - 510 - 20, 80, COLORES["gris_claro"], "#CBD5E1", 1, 3)
    d.text(75, y_footer + 24, f"PROYECTO: {proy['nombre_proyecto']}", 12, 700)
    d.text(75, y_footer + 48, f"PROPIETARIO: {proy['propietario'] or 'POR DEFINIR'}", 11)
    d.text(75, y_footer + 68, f"UBICACIÓN: {proy['direccion'] or 'POR DEFINIR'} · {proy['municipio'] or 'POR DEFINIR'}", 11)
    d.text(650, y_footer + 48, f"DISEÑÓ: {proy['disenador'] or 'POR DEFINIR'}", 11)
    d.text(650, y_footer + 68, f"MATRÍCULA: {proy['matricula'] or 'POR DEFINIR'}", 11)

    d.rect(d.width - 510 - 55, y_footer, 510, 80, COLORES["rojo_claro"], COLORES["rojo"], 1, 3)
    d.text(d.width - 490 - 55, y_footer + 24, "DOCUMENTO PARA REVISIÓN — NO CONSTRUCTIVO", 12, 700, COLORES["rojo"])
    d.text(d.width - 490 - 55, y_footer + 48, "Requiere memorias, coordinación, estudio de Icc,", 11)
    d.text(d.width - 490 - 55, y_footer + 67, "selección definitiva y firma profesional competente.", 11)

    return d.render()


# ══════════════════════════════════════════════════════════════════════════════
# 4. Exportación
# ══════════════════════════════════════════════════════════════════════════════
def exportar_ficha_svg_bytes(svg: str) -> bytes:
    return svg.encode("utf-8")


def exportar_ficha_png_bytes(svg: str, width: int = 2400) -> bytes | None:
    """PNG vía CairoSVG (dependencia OPCIONAL, no agregada a requirements.txt
    -- igual que el script original: si no está instalada, se degrada
    devolviendo None en vez de reventar. El llamador (la página) decide si
    muestra el botón de descarga PNG."""
    try:
        import cairosvg
    except ImportError:
        return None
    return cairosvg.svg2png(bytestring=svg.encode("utf-8"), output_width=width)
