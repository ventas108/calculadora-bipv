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

import re
from html import escape

from calculos.dimensionamiento import calcular_voc_string, calcular_vmp_string, corriente_diseno_ac


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
    factor_bifacial: float = 1.0,
    v_sistema_modulo_v: float | None = None,
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
            # Spec 07/unifilar-retie-bifacial-cruce: 1 + 0,135 φ (BNPI).
            "factor_bifacial": float(factor_bifacial or 1.0),
            # Spec 03/tension-maxima-modulo: VSYS de la ficha del módulo.
            "v_sistema_max_v": v_sistema_modulo_v,
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

    # Corrientes: se guarda primero el valor CRUDO (sin redondear) y de ahí
    # se derivan tanto la cifra a mostrar (redondeada a 1 decimal) como la
    # corriente de diseño y el breaker -- calcular la de diseño a partir de
    # la ya redondeada (doble redondeo) daba un resultado distinto al que
    # mostraba Página 20 (calculos/diagrama_unifilar.py) para el MISMO
    # proyecto (360,9 A aquí vs 360,8 A allá) -- encontrado en auditoría
    # (27-ago-2026) comparando ambos documentos del proyecto Urabá. Corregido
    # de raíz (7-sep-2026): ambos módulos ahora comparten
    # calculos.dimensionamiento.corriente_diseno_ac(), una sola fórmula.
    tension = inv["tension_salida_v"]
    i_inversor_crudo = corriente_diseno_ac(
        inv["potencia_ac_kw_unidad"], 1, tension, factor_continuo=1.0
    )
    i_total_crudo = corriente_diseno_ac(pac, 1, tension, factor_continuo=1.0)

    i_inversor = round(i_inversor_crudo, 1) if i_inversor_crudo is not None else None
    i_total = round(i_total_crudo, 1) if i_total_crudo is not None else None
    i_diseno = round(i_total_crudo * fc, 1) if i_total_crudo is not None else None

    breaker_inversor = (
        calibre_comercial_superior(i_inversor_crudo * fc) if i_inversor_crudo is not None else None
    )
    breaker_general = calibre_comercial_superior(i_diseno) if i_diseno is not None else None

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
    # Isc de diseño con la cara trasera del panel bifacial (BNPI, IEC TS
    # 60904-1-2): Isc × (1 + 0,135 φ) × 1,25. Monofacial: factor 1.
    fb = float(panel.get("factor_bifacial") or 1.0)
    isc_bnpi = round(panel["isc_a"] * fb, 2) if panel["isc_a"] else None
    isc_diseno = round(panel["isc_a"] * fb * fc, 1) if panel["isc_a"] else None

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
        "isc_bnpi_a": isc_bnpi, "factor_bifacial": fb,
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
    else:
        # Spec 03/tension-maxima-modulo: el menor entre inversor y módulo.
        from calculos.tension_modulo import limite_voc
        _lim = limite_voc({"V_sistema_max": cfg["panel"].get("v_sistema_max_v")},
                          {"Vdc_max": inv["vdc_max_v"]})
        _nombre = "tensión máx. del módulo" if _lim["origen"] == "modulo" else "Vdc máx."
        if calc["voc_string_frio_v"] < _lim["limite_v"]:
            out.append({"nivel": "OK", "titulo": "Voc del string en frío",
                        "detalle": f"{calc['voc_string_frio_v']:.1f} V < {_nombre} {_lim['limite_v']:.1f} V."})
        else:
            out.append({"nivel": "ERROR", "titulo": "Voc del string en frío",
                        "detalle": f"{calc['voc_string_frio_v']:.1f} V >= {_nombre} {_lim['limite_v']:.1f} V."})

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
# 2b. Sistema multi-superficie de 🗺️ Vista 3D (Spec 07/unifilar-retie-
#     multisuperficie, 28-sep-2026). Antes la ficha validaba el panel y el
#     inversor de 📐 Dimensionamiento aunque el proyecto tuviera dos paneles
#     y grupos de strings por MPPT. Las comprobaciones de string, MPPT e
#     inversor NO se recalculan aquí: salen del diagnóstico de
#     diseno_electrico_multisup (el mismo de ⚡ Diseño eléctrico).
# ══════════════════════════════════════════════════════════════════════════════
NIVEL_POR_ESTADO = {"verde": "OK", "amarillo": "PENDIENTE", "rojo": "ERROR"}
# Fusible gPV por string: corriente continua de diseño 1,25 × Isc y fusible
# ≥ 1,25 × esa corriente (NEC 690.8/690.9, referencia). El máximo lo fija el
# «fusible máximo en serie» de la ficha del módulo.
FACTOR_FUSIBLE_STRING = 1.25 * 1.25


def _txt(valor) -> str:
    """Número para una tarjeta: sin miles, coma decimal; texto tal cual."""
    if valor is None:
        return "sin dato"
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        if float(valor).is_integer():
            return f"{valor:g}"
        return (f"{valor:.2f}" if abs(valor) < 10 else f"{valor:.1f}").replace(".", ",")
    return str(valor)


def _con_unidad(valor, unidad: str) -> str:
    """Valor con su unidad; un texto sin cifras («un solo valor») va sin unidad."""
    texto = _txt(valor)
    return f"{texto}{unidad}" if any(ch.isdigit() for ch in texto) else texto


def calcular_retie_multisuperficie(topologia: dict, *, tension_salida_v: float | None,
                                   factor_continuo: float = 1.25) -> dict:
    """Mismas claves que ``calcular_retie`` (para las tarjetas de la ficha) más
    ``por_inversor``: corriente y breaker AC de cada inversor con SU potencia.
    Sin potencia AC de un inversor, su corriente y el total quedan en None."""
    por_inv, crudas = [], []
    for inv in topologia["inversores"]:
        i_cruda = corriente_diseno_ac(inv["p_ac_kW"], 1, tension_salida_v, factor_continuo=1.0)
        crudas.append(i_cruda)
        por_inv.append({
            "inversor_id": inv["inversor_id"], "nombre": inv["nombre"],
            "p_ac_kw": inv["p_ac_kW"], "p_dc_kwp": round(inv["p_dc_kWp"], 2),
            "relacion_dc_ac": round(inv["p_dc_kWp"] / inv["p_ac_kW"], 3) if inv["p_ac_kW"] else None,
            "strings": sum(r["strings"] for r in inv["ramas"]),
            "corriente_a": round(i_cruda, 1) if i_cruda is not None else None,
            "breaker_a": calibre_comercial_superior(i_cruda * factor_continuo) if i_cruda is not None else None,
        })
    completo = bool(crudas) and all(c is not None for c in crudas)
    i_total = sum(crudas) if completo else None
    # La relación sale de los valores crudos: con los ya redondeados daba otra
    # cifra (1,045 frente a 1,046), el mismo doble redondeo de calcular_retie.
    pdc_crudo, pac_crudo = topologia["p_dc_kWp"], topologia["p_ac_kW"]
    return {
        "potencia_dc_kwp": round(pdc_crudo, 2) if pdc_crudo else None,
        "potencia_ac_kw": round(pac_crudo, 2) if pac_crudo else None,
        "relacion_dc_ac": round(pdc_crudo / pac_crudo, 3) if pdc_crudo and pac_crudo else None,
        "corriente_inversor_a": None,
        "corriente_total_a": round(i_total, 1) if i_total is not None else None,
        "corriente_diseno_total_a": round(i_total * factor_continuo, 1) if i_total is not None else None,
        "breaker_inversor_a": None,
        "breaker_general_a": calibre_comercial_superior(i_total * factor_continuo) if i_total is not None else None,
        "pdc_por_inversor_kwp": [p["p_dc_kwp"] for p in por_inv],
        "dcac_por_inversor": [p["relacion_dc_ac"] for p in por_inv],
        "voc_string_stc_v": None, "voc_string_frio_v": None,
        "vmp_string_stc_v": None, "isc_diseno_string_a": None,
        "por_inversor": por_inv,
    }


def _etiqueta_diag(nivel: str, item: dict) -> str:
    if nivel == "grupo":
        return f"{item['superficie']} · {item['gid']}"
    if nivel == "mppt":
        return f"{item['inversor_id']} · MPPT {item['mppt']}"
    if nivel == "inversor":
        return str(item["inversor_id"])
    return str(item["superficie"])


def _limpiar_mensaje(texto: str) -> str:
    """Mensaje de compatibilidad_bateria sin markdown ni emoji, en una línea."""
    limpio = re.sub(r"[*`]", "", texto)
    limpio = re.sub(r"^[^\wÁÉÍÓÚáéíóú¿(]+", "", limpio.strip())
    return " ".join(limpio.replace("- ", "").split())


def validar_retie_multisuperficie(topologia: dict, diagnostico: dict, calc: dict, *,
                                  corriente_cortocircuito_pcc_ka: float | None = None,
                                  esquema_tierra: str = "",
                                  bateria_dict: dict | None = None) -> list[dict]:
    """Validaciones ``{nivel, titulo, detalle}`` del sistema multi-superficie.

    Verde → OK, amarillo → PENDIENTE, rojo → ERROR, igual que ⚡ Diseño
    eléctrico. Agrega cajas combinadoras (fusibles gPV), batería,
    optimizadores, temperaturas de diseño, capacidad interruptiva y tierra.
    """
    from calculos.compatibilidad_bateria import check_compatibilidad

    icc = corriente_cortocircuito_pcc_ka
    out: list[dict] = []
    if topologia.get("sin_asignar"):
        out.append({"nivel": "ERROR", "titulo": "Grupos sin inversor o MPPT válido",
                    "detalle": ", ".join(topologia["sin_asignar"]) + ": asígnalos en 🗺️ Vista 3D."})
    if (diagnostico.get("temperaturas") or {}).get("origen") != "proyecto":
        out.append({"nivel": "PENDIENTE", "titulo": "Temperaturas de diseño",
                    "detalle": "Se usan las de por defecto; define las del sitio en 📐 Dimensionamiento."})

    for nivel, clave in (("grupo", "grupos"), ("mppt", "mppt"), ("inversor", "inversores"),
                         ("superficie", "superficies")):
        for item in diagnostico.get(clave, []):
            etiqueta = _etiqueta_diag(nivel, item)
            for c in item.get("checks", []):
                unidad = f" {c['unidad']}" if c.get("unidad") else ""
                if c.get("valor") is None:
                    detalle = str(c.get("formula") or "")
                elif c.get("limite") is None:
                    detalle = f"{_con_unidad(c['valor'], unidad)}; límite sin dato en la ficha."
                else:
                    detalle = (f"{_con_unidad(c['valor'], unidad)} · límite "
                               f"{_con_unidad(c['limite'], unidad)}.")
                out.append({"nivel": NIVEL_POR_ESTADO.get(c.get("estado"), "PENDIENTE"),
                            "titulo": f"{c['nombre']} — {etiqueta}", "detalle": detalle})

    for inv in topologia["inversores"]:
        for rama in inv["ramas"]:
            if not rama["caja_combinadora"]:
                continue
            # isc_stc_A de la topología ya viene en BNPI si el panel es bifacial.
            isc = max((g["isc_stc_A"] or 0.0) for g in rama["grupos"]) or None
            bif = any(float(g.get("factor_bifacial") or 1.0) > 1.0 for g in rama["grupos"])
            minimo = (f"fusible gPV por string ≥ {_fmt(isc * FACTOR_FUSIBLE_STRING, 2, ' A')} "
                      f"(1,25 × 1,25 × Isc{' BNPI (bifacial)' if bif else ''} {_fmt(isc, 2, ' A')})"
                      if isc else "fusible gPV por string")
            out.append({"nivel": "PENDIENTE",
                        "titulo": f"Caja combinadora — {inv['inversor_id']} · MPPT {rama['mppt']}",
                        "detalle": f"{rama['strings']} strings en paralelo: {minimo} y ≤ fusible máximo "
                                   "de la ficha del módulo; seccionador y DPS DC."})

    bat = topologia.get("bateria")
    if bat:
        inv = next(i for i in topologia["inversores"] if i["inversor_id"] == bat["inversor_id"])
        estado, mensaje = check_compatibilidad(dict(bateria_dict or {}), inv["ficha"], inv["nombre"])
        nivel = {"ok": "OK", "warning": "PENDIENTE"}.get(estado, "ERROR")
        out.append({"nivel": nivel, "titulo": f"Batería — {bat['inversor_id']}",
                    "detalle": _limpiar_mensaje(mensaje)})

    if topologia.get("optimizadores"):
        out.append({"nivel": "PENDIENTE", "titulo": "Optimizadores (MLPE)",
                    "detalle": "La app no valida strings con optimizador: longitud del string, "
                               "voltaje fijo y compatibilidad con el inversor según el fabricante."})

    if icc is None:
        out.append({"nivel": "PENDIENTE", "titulo": "Capacidad interruptiva",
                    "detalle": "Falta la corriente de cortocircuito disponible en el PCC."})
    else:
        out.append({"nivel": "PENDIENTE", "titulo": "Capacidad interruptiva",
                    "detalle": f"Icc PCC={icc:.2f} kA; seleccionar Icu/Ics de interruptores y "
                               "verificar coordinación."})
    if esquema_tierra:
        out.append({"nivel": "PENDIENTE", "titulo": "Sistema de puesta a tierra",
                    "detalle": f"Esquema declarado: {esquema_tierra}; verificar resistividad, "
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
        # «Nombre — dónde» (multi-superficie): el «dónde» va en su propia línea;
        # en una sola línea no cabía en la tarjeta (se salía por la derecha).
        titulo, _, donde = v["titulo"].partition(" — ")
        d.text(bx + 52, by + 27, titulo, 14, 700, color)
        if donde:
            d.text(bx + 52, by + 45, donde, 12, 700, COLORES["gris"])
            d.multiline(bx + 52, by + 64, _partir_detalle(v["detalle"], max_lineas=2), 11, 17, COLORES["texto"])
        else:
            d.multiline(bx + 52, by + 52, _partir_detalle(v["detalle"]), 11, 17, COLORES["texto"])


def _partir_detalle(detalle: str, corte: int = 54, max_lineas: int = 3) -> list[str]:
    """Detalle en líneas de ~``corte`` caracteres; lo que no cabe en la tarjeta
    termina en «…» (antes la segunda línea llevaba todo el resto y se salía)."""
    palabras, lineas, actual = detalle.split(), [], ""
    for palabra in palabras:
        if actual and len(actual) + 1 + len(palabra) > corte:
            lineas.append(actual)
            actual = palabra
        else:
            actual = f"{actual} {palabra}".strip()
    if actual:
        lineas.append(actual)
    if len(lineas) > max_lineas:
        lineas = lineas[:max_lineas]
        lineas[-1] = lineas[-1][: corte - 1].rstrip() + "…"
    return lineas or [""]


def _lineas_multisuperficie(topologia: dict, calc: dict, tension_v) -> dict:
    """Líneas de los bloques y filas de la tabla con cada superficie y cada
    inversor del sistema multi-superficie (en vez de un solo panel)."""
    campo = []
    for sup in topologia["superficies"]:
        _mf = sup.get("modulos_fisicos", sup["modulos"])
        campo.append(f"{sup['nombre']}: {_mf} mód."
                     + (f" ({sup['modulos']} en sus strings)" if _mf != sup["modulos"] else "")
                     + f" · {_fmt(sup['p_dc_kWp'], 2, ' kWp')}")
        campo.append("  " + " + ".join(str(p) for p in sup["paneles"]))
    campo.append(f"Pdc = {_fmt(calc['potencia_dc_kwp'], 2, ' kWp')}")
    if topologia.get("optimizadores"):
        campo.append("Optimizadores MLPE por módulo")
    n_cajas = sum(r["caja_combinadora"] for i in topologia["inversores"] for r in i["ramas"])
    dc = ["Fusibles gPV (+/-)*", "Seccionador DC bajo carga*", "DPS DC Tipo 2*", "Cable solar H1Z2Z2-K*"]
    dc.append(f"Caja combinadora × {n_cajas}" if n_cajas else "Ucpv >= Voc máxima")
    dc.append("*Dimensionar con ficha")
    inversores, filas = [], []
    for inv, c in zip(topologia["inversores"], calc["por_inversor"]):
        mppts = ", ".join(str(r["mppt"]) for r in inv["ramas"])
        inversores.append(f"{inv['inversor_id']} {inv['nombre'] or 'inversor'} (MPPT {mppts})")
        inversores.append(f"  {_fmt(c['p_dc_kwp'], 2, ' kWp')} → {_fmt(c['p_ac_kw'], 1, ' kW')} · "
                          f"QF {_fmt(c['breaker_a'], 0, ' A')}*")
        obs = f"{c['strings']} strings" + (f" · DC/AC {_fmt(c['relacion_dc_ac'], 2)}" if c["relacion_dc_ac"] else "")
        filas.append([f"{inv['inversor_id']} AC", _fmt(c["p_ac_kw"], 1, " kW"), _fmt(tension_v, 0, " V, 3F"),
                      _fmt(c["corriente_a"], 1, " A"), f"{_fmt(c['breaker_a'], 0, ' A')}*", "Por calcular", obs])
    bat = topologia.get("bateria")
    if bat:
        inversores.append(f"Batería {bat['nombre'] or ''} → {bat['inversor_id']}")
        filas.append([f"Batería ({bat['inversor_id']})", "-", "DC", "-", "Por calcular", "Por calcular",
                      f"{bat['cantidad']} × {_fmt(bat['capacidad_kWh_unidad'], 1, ' kWh')} · "
                      f"total {_fmt(bat['capacidad_total_kWh'], 1, ' kWh')}"])
    return {"campo": campo[:8], "dc": dc, "inversores": inversores[:8], "filas": filas,
            "n_inversores": len(topologia["inversores"])}


def generar_ficha_svg(cfg: dict, calc: dict, checks: list[dict], topologia: dict | None = None) -> str:
    """Dibuja la ficha completa (SVG). Universal: el número de bloques del
    inversor y de filas de la tabla se ajustan a `inv['cantidad']`, no a 2
    fijos como en el script original. Con ``topologia`` (sistema
    multi-superficie) el campo FV, los inversores y la tabla de cargas
    muestran cada superficie y cada inversor con su propia potencia."""
    proy, panel, inv, gen = cfg["proyecto"], cfg["panel"], cfg["inversor"], cfg["generador"]
    multi = _lineas_multisuperficie(topologia, calc, inv["tension_salida_v"]) if topologia else None
    n_filas_validacion = -(-len(checks) // 4)  # techo de división, sin importar
    # Alto según lo que se dibuja: tabla (filas por inversor + general + tierra)
    # y tarjetas. Antes no contaba la tabla y la última fila de tarjetas quedaba
    # debajo del pie de página (28-sep-2026).
    n_filas_tabla = (len(multi["filas"]) if multi else inv["cantidad"]) + 2
    height = max(1420, 695 + 45 * (n_filas_tabla + 1) + 60 + 22 + n_filas_validacion * 108 + 170)
    d = _SVG(height=height)

    d.rect(0, 0, d.width, d.height, COLORES["fondo"], COLORES["fondo"], 0, 0)
    d.rect(25, 20, d.width - 50, d.height - 45, "#fff", COLORES["texto"], 2, 8)

    d.text(55, 60, "FICHA DE VALIDACIÓN RETIE", 29, 700)
    d.text(55, 88, "Lectura ejecutiva para cliente + checklist de validación técnica orientado a RETIE", 15, 400, COLORES["gris"])
    d.rect(d.width - 430, 40, 365, 65, COLORES["gris_claro"], "#CBD5E1", 1, 5)
    d.text(d.width - 410, 65, f"PLANO: {proy['plano']}", 12, 700)
    d.text(d.width - 410, 88, f"REV. {proy['revision']} · {proy['fecha']} · PARA REVISIÓN", 11, 400, COLORES["gris"])

    ancho_tarjeta = (d.width - 110 - 4 * 20) / 5
    tarjetas = [
        ("Potencia instalada", _fmt(calc["potencia_dc_kwp"], 2, " kWp"), "Generador fotovoltaico", COLORES["azul"]),
        ("Potencia nominal", _fmt(calc["potencia_ac_kw"], 1 if multi else 0, " kW"),
         f"Salida total de {multi['n_inversores'] if multi else inv['cantidad']} inversor(es)", COLORES["azul"]),
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
        f"Isc diseño: {_fmt(calc['isc_diseno_string_a'], 1, ' A')}"
        + (f" (Isc BNPI {_fmt(calc.get('isc_bnpi_a'), 2, ' A')})"
           if float(calc.get("factor_bifacial") or 1.0) > 1.0 else ""),
    ]
    if multi:
        lineas_campo = multi["campo"]
    _bloque(d, x, y, 270, alto_flujo, "1. CAMPO FV", lineas_campo)
    x += 270
    d.line(x, y + alto_flujo / 2, x + 55, y + alto_flujo / 2, COLORES["azul"], 5, True)
    x += 55

    _bloque(d, x, y, 240, alto_flujo, "2. PROTECCIÓN DC", multi["dc"] if multi else [
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
    if multi:
        lineas_inv = multi["inversores"]
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
    if multi:
        filas = multi["filas"]
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
