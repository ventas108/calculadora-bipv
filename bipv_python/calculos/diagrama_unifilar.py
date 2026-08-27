# -*- coding: utf-8 -*-
"""
Diagrama Unifilar — generador universal para proyectos FV/BIPV (Fase 1 / MVP).

Separación deliberada en 2 capas (mismo patrón que comparador_inversores.py):
  1. construir_config_unifilar() — traduce datos del proyecto (panel, inversor,
     N_serie, N_paneles, etc.) a una estructura neutral. No dibuja nada, no
     depende de Streamlit ni de schemdraw -- testeable con valores a mano.
  2. generar_diagrama_unifilar() — dibuja a partir de ese config. No sabe de
     dónde salieron los datos (Urabá, una fachada BIPV, o un test) -- por eso
     es universal: el mismo código sirve para cualquier proyecto.

Alcance Fase 1 (MVP): 1 sola rama DC (una superficie), 1 o más inversores
(mostrados como un solo bloque con multiplicador "N ×" si son varios -- no
ramas paralelas dibujadas, ver limitación abajo), sin batería.
Fase 2 (batería) y Fase 3 (multi-superficie) quedan fuera de este módulo por
ahora -- ver DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md / plan de implementación.

Límite importante (declarar siempre al usuario, mismo criterio que el resto
de la app con "documento preliminar" / "cifra contractual definitiva"): este
diagrama es un borrador técnico auto-poblado, NO un documento certificado
para trámite RETIE -- ese trámite requiere firma de ingeniero electricista
matriculado.
"""
from __future__ import annotations

import math

import schemdraw
import schemdraw.elements as elm

schemdraw.use("matplotlib")  # necesario para exportar PNG/PDF (SVG no requiere esto)


# ══════════════════════════════════════════════════════════════════════════════
# 1. Config — capa de datos, sin dibujo
# ══════════════════════════════════════════════════════════════════════════════
def construir_config_unifilar(
    *,
    nombre_proyecto: str = "Proyecto BIPV",
    cliente: str = "",
    tipo_instalacion: str = "",
    panel_nombre: str = "",
    panel: dict | None = None,
    n_paneles: int = 0,
    n_serie: int = 0,
    inversor_nombre: str = "",
    inversor: dict | None = None,
    n_inversores: int = 1,
    proteccion_dc_A: float | None = None,
    proteccion_ac_A: float | None = None,
    tension_red_V: float | None = None,
    medidor: str = "Bidireccional",
) -> dict:
    """
    Normaliza los datos de un proyecto a la estructura mínima que necesita
    generar_diagrama_unifilar(). Calcula derivados (kWp, N_strings, P_ac
    total, corriente AC estimada) -- no dibuja nada.

    panel / inversor: dicts del catálogo (mismo formato que usan
    comparador_inversores.py y catalogo_inversores.py). Si faltan campos,
    los derivados quedan en None en vez de reventar -- el llamador decide
    si avisa al usuario (igual criterio que filtrar_inversores_compatibles:
    dato faltante no es lo mismo que dato inválido).
    """
    panel = panel or {}
    inversor = inversor or {}

    pmax_stc = float(panel.get("Pmax_stc") or panel.get("PmaxWp") or 0) or None
    p_dc_kWp = round(pmax_stc * n_paneles / 1000, 2) if pmax_stc and n_paneles else None
    n_strings = int(n_paneles // n_serie) if n_serie else None
    string_incompleto = bool(n_serie and n_paneles and n_paneles % n_serie != 0)

    p_ac_unidad_kW = None
    if inversor.get("P_ac_nom_W"):
        p_ac_unidad_kW = float(inversor["P_ac_nom_W"]) / 1000.0
    elif inversor.get("P_ac_nom_kW"):
        p_ac_unidad_kW = float(inversor["P_ac_nom_kW"])
    p_ac_total_kW = (
        round(p_ac_unidad_kW * n_inversores, 1) if p_ac_unidad_kW else None
    )

    # Corriente AC estimada (trifásica, FS=1.25 NEC) SOLO si no la dio el usuario.
    # Es una referencia de dimensionamiento preliminar del breaker -- no
    # reemplaza el cálculo del ingeniero responsable del proyecto.
    if proteccion_ac_A is None and p_ac_total_kW and tension_red_V:
        proteccion_ac_A = round(
            1.25 * p_ac_total_kW * 1000 / (math.sqrt(3) * tension_red_V), 1
        )

    return {
        "nombre_proyecto": nombre_proyecto,
        "cliente": cliente,
        "tipo_instalacion": tipo_instalacion,
        "generador": {
            "panel_nombre": panel_nombre,
            "n_paneles": n_paneles,
            "n_serie": n_serie,
            "n_strings": n_strings,
            "string_incompleto": string_incompleto,
            "p_dc_kWp": p_dc_kWp,
        },
        "proteccion_dc_A": proteccion_dc_A,
        "inversores": {
            "nombre": inversor_nombre,
            "cantidad": max(int(n_inversores), 1),
            "p_ac_unidad_kW": p_ac_unidad_kW,
            "p_ac_total_kW": p_ac_total_kW,
        },
        "proteccion_ac_A": proteccion_ac_A,
        "tension_red_V": tension_red_V,
        "medidor": medidor,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 2. Dibujo — a partir del config, sin saber de dónde salió
# ══════════════════════════════════════════════════════════════════════════════
def _label_generador(cfg: dict) -> str:
    g = cfg["generador"]
    lineas = [g.get("panel_nombre") or "Generador FV"]
    partes = []
    if g.get("n_paneles"):
        partes.append(f"{g['n_paneles']} paneles")
    if g.get("p_dc_kWp"):
        partes.append(f"{g['p_dc_kWp']:.2f} kWp DC")
    if partes:
        lineas.append(" · ".join(partes))
    if g.get("n_strings") and g.get("n_serie"):
        sufijo = "  ⚠ string incompleto" if g.get("string_incompleto") else ""
        lineas.append(f"{g['n_strings']} strings × {g['n_serie']} en serie{sufijo}")
    return "\n".join(lineas)


def _label_inversor(cfg: dict) -> str:
    inv = cfg["inversores"]
    n = inv["cantidad"]
    nombre = inv.get("nombre") or "Inversor"
    prefijo = f"{n} × " if n > 1 else ""
    lineas = [f"{prefijo}{nombre}"]
    if inv.get("p_ac_total_kW"):
        sufijo = " total" if n > 1 else ""
        lineas.append(f"{inv['p_ac_total_kW']:.1f} kW AC{sufijo}")
    return "\n".join(lineas)


def generar_diagrama_unifilar(config: dict) -> schemdraw.Drawing:
    """
    Dibuja el diagrama unifilar a partir de un config de
    construir_config_unifilar(). Fase 1: 1 rama DC, inversor(es) como un solo
    bloque (con multiplicador si son varios -- ver limitación en el
    docstring del módulo), sin batería.
    """
    # Nota: el título del proyecto/cliente NO se dibuja dentro del esquema --
    # lo pinta quien use el diagrama (página Streamlit, PDF), igual que el
    # resto de la app separa encabezados de documento del contenido gráfico.
    # Ver config["nombre_proyecto"] / config["cliente"] para ese texto.
    d = schemdraw.Drawing(fontsize=11)

    d += elm.Rect(w=2.8, h=1.4).right().label(_label_generador(config), loc="top")
    d += elm.Line().down().length(1.1)
    d += elm.Dot()

    dc_A = config.get("proteccion_dc_A")
    etiqueta_dc = f"Protección DC ({dc_A:.0f} A)" if dc_A else "Protección DC"
    d += elm.Fuse().down().label(etiqueta_dc, loc="right")
    d += elm.Line().down().length(1.1)

    d += elm.Rect(w=2.8, h=1.3).right().label(_label_inversor(config), loc="top")
    d += elm.Line().down().length(1.1)

    ac_A = config.get("proteccion_ac_A")
    etiqueta_ac = f"Protección AC ({ac_A:.0f} A)" if ac_A else "Protección AC"
    d += elm.Breaker().down().label(etiqueta_ac, loc="right")
    d += elm.Line().down().length(1.1)

    medidor_txt = f"Medidor {config.get('medidor') or 'Bidireccional'}"
    d += elm.Rect(w=2.8, h=1.1).right().label(medidor_txt, loc="top")
    d += elm.Line().down().length(1.0)
    d += elm.Dot()

    tension = config.get("tension_red_V")
    etiqueta_red = f"Red / Punto de conexión ({tension:.0f} V)" if tension else "Red / Punto de conexión"
    d += elm.Line().down().length(0.6).label(etiqueta_red, loc="right")
    d += elm.Ground()

    return d


def exportar_unifilar_bytes(drawing: schemdraw.Drawing, fmt: str = "png") -> bytes:
    """
    Devuelve el diagrama como bytes en memoria (sin tocar disco) -- para
    st.download_button/st.image en la página de Streamlit. fmt: 'png',
    'svg', 'pdf' o 'jpg'.
    """
    return drawing.get_imagedata(fmt)


def exportar_unifilar(drawing: schemdraw.Drawing, ruta: str, dpi: int = 160) -> str:
    """
    Guarda el diagrama en disco. El formato lo determina la extensión de
    `ruta` (.svg, .png, .pdf) -- SVG no requiere el backend de matplotlib,
    PNG/PDF sí (ya activado por schemdraw.use('matplotlib') al importar
    este módulo).
    """
    drawing.save(ruta, dpi=dpi)
    return ruta
