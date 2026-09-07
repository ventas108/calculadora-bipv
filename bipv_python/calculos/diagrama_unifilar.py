# -*- coding: utf-8 -*-
"""
Diagrama Unifilar — generador universal para proyectos FV/BIPV.

Separación deliberada en 2 capas (mismo patrón que comparador_inversores.py):
  1. construir_config_unifilar() — traduce datos del proyecto (panel, inversor,
     N_serie, N_paneles, batería, etc.) a una estructura neutral. No dibuja
     nada, no depende de Streamlit ni de schemdraw -- testeable con valores
     a mano.
  2. generar_diagrama_unifilar() — dibuja a partir de ese config. No sabe de
     dónde salieron los datos (Urabá, una fachada BIPV, o un test) -- por eso
     es universal: el mismo código sirve para cualquier proyecto.

Alcance:
  Fase 1 (26-ago-2026): 1 sola rama DC (una superficie), 1 o más inversores
    (mostrados como un solo bloque con multiplicador "N ×" si son varios --
    no ramas paralelas dibujadas para múltiples inversores, ver limitación
    abajo), sin batería.
  Fase 2 (27-ago-2026): batería, cuando el proyecto tiene una configurada
    (Página 11 — Baterías y Balance). Ver calculos/compatibilidad_bateria.py:
    en esta app la batería se conecta al MISMO inversor híbrido (verificación
    por rango de voltaje), no a un inversor separado -- por eso la rama de
    batería cuelga del punto DC justo antes del inversor, como una segunda
    entrada DC del mismo equipo, no como un circuito aparte.
  Fase 3 (27-ago-2026): multi-superficie -- cuando el proyecto tiene 2+
    superficies activas (Página 9 — Vista 3D y Multi-Superficie), cada una
    se dibuja como su propio bloque generador con su propia protección DC,
    todas convergiendo en un bus horizontal común antes del inversor. Con 0
    o 1 superficie (el caso normal) el diagrama sale idéntico a Fase 1/2 --
    sin regresión.
  Detalle RETIE (27-ago-2026): campos opcionales para enriquecer el
    contenido del diagrama con anotaciones típicas de una revisión RETIE
    (fusibles gPV, seccionador DC, DPS, cable solar, equipotencialidad,
    notas/pendientes) -- inspirado en un generador aparte que el usuario
    aportó (SVG crudo, sin schemdraw, codificado a mano para un único
    proyecto de 2 inversores). Se decidió NO adoptar ese motor de dibujo
    (habría duplicado arquitectura y descartado la geometría ya probada de
    batería/multi-superficie) -- en cambio se extrajo su CONTENIDO como
    texto opcional sobre la arquitectura universal existente. Todos los
    parámetros nuevos son opcionales y sin valor por defecto activo -- un
    proyecto que no los usa produce el mismo diagrama que antes (sin
    regresión).

Limitaciones conocidas (declaradas a propósito, no ocultas):
  - Con más de 1 inversor, se muestra como un solo bloque "N × modelo" en
    vez de N ramas paralelas dibujadas -- evita geometría de ramas múltiples
    frágil para un beneficio principalmente cosmético.
  - La rama de batería es una "rama que cuelga" (convención propia de
    diagramas unifilares: no se dibuja el camino de retorno) -- no repite
    todos los símbolos de protección de un diagrama de detalle completo.
  - Multi-superficie asume que TODAS las superficies convergen en el/los
    MISMO(S) inversor(es) del proyecto -- no modela strings de distinta
    orientación compartiendo un mismo MPPT (eso ya lo resuelve Página 9,
    sección 6, como cálculo aparte e informativo, no como topología física).
  - Este diagrama es un borrador técnico auto-poblado, NO un documento
    certificado para trámite RETIE -- ese trámite requiere firma de
    ingeniero electricista matriculado. Declarar esto siempre al usuario
    (mismo criterio que el resto de la app con "documento preliminar" /
    "cifra contractual definitiva").
  - notas_retie / pendientes_retie NO se dibujan dentro de la imagen del
    esquema -- quedan en config["retie"] como listas de texto para que la
    página Streamlit las muestre debajo del diagrama (como el resto del
    contenido de documento, igual que el título/cliente). Se decidió así
    a propósito: agregar cajas de texto largo dentro del dibujo schemdraw
    es geometría nueva no probada (mismo tipo de riesgo que costó varias
    iteraciones en la rama de batería de Fase 2) -- el texto plano fuera
    del dibujo es la vía de menor riesgo para el mismo contenido.
"""
from __future__ import annotations

import schemdraw
import schemdraw.elements as elm

from calculos.dimensionamiento import corriente_diseno_dc, corriente_diseno_ac

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
    bateria_nombre: str = "",
    bateria: dict | None = None,
    n_baterias: int = 0,
    capacidad_kWh_unidad: float | None = None,
    proteccion_bat_A: float | None = None,
    superficies: list[dict] | None = None,
    equipotencialidad: bool = False,
    detalle_proteccion_dc: list[str] | None = None,
    detalle_proteccion_ac: list[str] | None = None,
    notas_retie: list[str] | None = None,
    pendientes_retie: list[str] | None = None,
) -> dict:
    """
    Normaliza los datos de un proyecto a la estructura mínima que necesita
    generar_diagrama_unifilar(). Calcula derivados (kWp, N_strings, P_ac
    total, corriente AC estimada, capacidad total de batería) -- no dibuja
    nada.

    panel / inversor / bateria: dicts del catálogo (mismo formato que usan
    comparador_inversores.py, catalogo_inversores.py y baterias_balance.py).
    Si faltan campos, los derivados quedan en None en vez de reventar -- el
    llamador decide si avisa al usuario (igual criterio que
    filtrar_inversores_compatibles: dato faltante no es lo mismo que dato
    inválido).

    n_baterias=0 (default) significa "sin batería en este proyecto" --
    generar_diagrama_unifilar() no dibuja la rama de batería en ese caso,
    el diagrama sale idéntico al de la Fase 1 (sin regresión).

    superficies: lista opcional para multi-superficie (Fase 3). Cada item:
    {"nombre": str, "n_paneles": int, "p_dc_kWp": float|None, "tipo": str}.
    Con menos de 2 items activos, se ignora y se usa el generador único
    (panel/n_paneles/n_serie de arriba) -- sin regresión frente a Fase 1/2.
    Este parámetro NO reemplaza panel/n_paneles/n_serie: cuando SÍ hay 2+
    superficies, esos parámetros del generador único se ignoran para el
    dibujo (cada superficie ya trae su propio kWp), pero conviene seguir
    pasando n_serie si se quiere seguir viendo el aviso de string incompleto
    a nivel de proyecto.

    equipotencialidad / detalle_proteccion_dc / detalle_proteccion_ac /
    notas_retie / pendientes_retie: anotaciones opcionales de contenido
    RETIE (ver docstring del módulo, "Detalle RETIE"). Todas por defecto
    inactivas -- no cambian el diagrama de un proyecto que no las use.
    detalle_proteccion_dc/ac son listas de ítems de texto libre (ej.
    ["Fusibles gPV por string", "Seccionador DC bajo carga", "DPS DC Tipo
    2"]) que se agregan como líneas extra a la etiqueta de protección
    correspondiente -- el llamador decide el contenido, este módulo no
    inventa valores normativos.
    """
    panel = panel or {}
    inversor = inversor or {}
    bateria = bateria or {}
    superficies = [s for s in (superficies or []) if s.get("n_paneles")]

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
    # reemplaza el cálculo del ingeniero responsable del proyecto. Delegada
    # (7-sep-2026) a calculos.dimensionamiento.corriente_diseno_ac(), la misma
    # fórmula que ya usaba calculos.ficha_validacion_retie.py con una
    # divergencia de redondeo distinta -- ver el comentario de esa función.
    if proteccion_ac_A is None and p_ac_unidad_kW and n_inversores and tension_red_V:
        _i_ac = corriente_diseno_ac(p_ac_unidad_kW, n_inversores, tension_red_V, factor_continuo=1.25)
        proteccion_ac_A = round(_i_ac, 1) if _i_ac is not None else None

    cap_unidad = capacidad_kWh_unidad or bateria.get("capacidad_kWh") or None
    cap_total_kWh = (
        round(cap_unidad * n_baterias, 1) if cap_unidad and n_baterias else None
    )

    superficies_out = None
    if len(superficies) >= 2:
        superficies_out = []
        for s in superficies:
            n_pan_s = int(s.get("n_paneles") or 0)
            p_kwp_s = s.get("p_dc_kWp")
            if p_kwp_s is None and pmax_stc and n_pan_s:
                p_kwp_s = round(pmax_stc * n_pan_s / 1000, 2)
            superficies_out.append({
                "nombre": s.get("nombre") or "Superficie",
                "tipo": s.get("tipo") or "",
                "n_paneles": n_pan_s,
                "p_dc_kWp": p_kwp_s,
            })

    return {
        "nombre_proyecto": nombre_proyecto,
        "cliente": cliente,
        "tipo_instalacion": tipo_instalacion,
        "superficies": superficies_out,
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
        "bateria": {
            "activa": bool(n_baterias and n_baterias > 0),
            "nombre": bateria_nombre,
            "cantidad": int(n_baterias),
            "capacidad_kWh_unidad": cap_unidad,
            "capacidad_total_kWh": cap_total_kWh,
            "proteccion_bat_A": proteccion_bat_A,
        },
        "retie": {
            "equipotencialidad": bool(equipotencialidad),
            "detalle_dc": list(detalle_proteccion_dc) if detalle_proteccion_dc else [],
            "detalle_ac": list(detalle_proteccion_ac) if detalle_proteccion_ac else [],
            "notas": list(notas_retie) if notas_retie else [],
            "pendientes": list(pendientes_retie) if pendientes_retie else [],
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# 1b. Pérdida óhmica — capa de cálculo eléctrico real, sin dibujo (7-sep-2026)
# ══════════════════════════════════════════════════════════════════════════════
RESISTIVIDAD_COBRE_OHM_MM2_M_20C = 0.0172  # Ω·mm²/m a 20°C, cobre recocido (IEC 60228)
COEF_TEMP_COBRE_POR_C = 0.00393            # 1/°C, coeficiente de temperatura del cobre

CALIBRES_COMERCIALES_MM2 = (1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240)


def _resistividad_cobre(T_C: float) -> float:
    return RESISTIVIDAD_COBRE_OHM_MM2_M_20C * (1 + COEF_TEMP_COBRE_POR_C * (T_C - 20.0))


def calcular_perdida_ohmica(
    *,
    panel: dict,
    inversor: dict,
    N_strings_tracker: int = 1,
    n_inversores: int = 1,
    tension_red_V: float | None = None,
    tramos_dc: list[dict] | None = None,
    n_paneles_total: int | None = None,
    longitud_ac_m: float | None = None,
    calibre_ac_mm2: float | None = None,
    T_diseno_C: float = 45.0,
) -> dict:
    """
    Calcula la resistencia (Ω) de cada tramo DC declarado (uno por superficie
    activa) y del tramo AC, a partir de longitud + calibre real del proyecto.
    Capa de cálculo eléctrico puro (sin Streamlit, sin dibujo) -- pensada
    para alimentar el motor de producción (calculos/produccion.py,
    calculos/produccion_iv.py), que aplica esta resistencia a la corriente
    REAL hora a hora (P_pérdida(t) = I(t)² · R) en vez de un % fijo anual a
    condiciones STC como hace PVsyst -- ver docstring de esos módulos.

    tramos_dc: uno por superficie activa, ej. [{"nombre": "Fachada Sur",
      "longitud_m": 25.0, "calibre_mm2": 6.0, "n_paneles": 40}, ...]. Con un
      único tramo (o ningún dato multi-superficie) se comporta como un
      proyecto de un solo tramo DC -- mismo criterio de degradación que
      construir_config_unifilar() ya usa para 0/1 superficie.

    n_paneles_total: total REAL de paneles del proyecto (no solo los de los
      tramos declarados) -- usado como denominador de `fraccion_paneles` de
      cada tramo. Si se omite, cae a la suma de los tramos declarados (única
      opción retrocompatible antes de este parámetro, y sigue siendo
      EXACTA cuando los tramos ya cubren el 100% de los paneles del
      proyecto). Auditoría (7-sep-2026): si el usuario declara cable para
      SOLO ALGUNAS superficies de un proyecto multi-superficie, normalizar
      contra la suma de tramos declarados (en vez del total real) le
      atribuye a esos tramos MÁS corriente de la que en verdad llevan --
      el motor de producción escala I_total(t) contra el N_paneles REAL del
      proyecto, no contra los paneles con tramo declarado, así que ambos
      denominadores deben coincidir para que la física sea correcta. Pasar
      n_paneles_total explícito corrige esto: los paneles sin tramo
      declarado simplemente no aportan pérdida (subestima en vez de
      sobreestimar -- el lado seguro, mismo principio de nunca inventar).

    Los tramos NO se combinan en una sola resistencia equivalente: cada uno
    lleva solo la corriente de SU PROPIA superficie, no la del proyecto
    completo -- por eso cada tramo devuelve su propia `resistencia_ohm` y
    su `fraccion_paneles` (n_paneles del tramo / n_paneles_total). El motor
    reparte la corriente total hora a hora entre tramos según esa fracción:
    I_tramo(t) = I_total(t) × fraccion_paneles -- una aproximación declarada
    (asume que todas las superficies reciben una irradiancia
    proporcionalmente similar a la del conjunto), no una simulación óptica
    independiente por superficie.

    Nunca inventa un número: un tramo sin longitud+calibre queda con
    resistencia_ohm=None (el llamador decide si avisa al usuario).

    Fuente de la resistividad: IEC 60228, cobre recocido, 0,0172 Ω·mm²/m a
    20°C, corregida por temperatura con el coeficiente estándar del cobre
    (0,393%/°C). T_diseno_C es una temperatura de diseño FIJA (no la
    T_celda horaria) -- mismo criterio que usa la práctica real de
    ingeniería (RETIE/NEC evalúan caída de tensión a una condición de
    diseño fija, no con clima horario); el motor de producción puede
    sustituir esta T fija por T_celda(t) si quiere mayor precisión hora a
    hora -- esta función solo entrega la resistencia a esa temperatura, no
    decide cuál usar.
    """
    resistividad = _resistividad_cobre(T_diseno_C)

    tramos_in = [t for t in (tramos_dc or []) if t.get("n_paneles")]
    _suma_tramos = sum(int(t["n_paneles"]) for t in tramos_in) or None
    # n_paneles_total explícito tiene prioridad -- ver docstring arriba de
    # por qué normalizar contra la suma de tramos declarados sobreestima la
    # pérdida cuando faltan superficies por declarar.
    n_paneles_total_efectivo = int(n_paneles_total) if n_paneles_total else _suma_tramos

    tramos_out = []
    for tramo in tramos_in:
        L = tramo.get("longitud_m")
        S = tramo.get("calibre_mm2")
        r_ohm = (2.0 * float(L) * resistividad / float(S)) if L and S else None
        fraccion = (
            int(tramo["n_paneles"]) / n_paneles_total_efectivo
            if n_paneles_total_efectivo else None
        )
        tramos_out.append({
            "nombre": tramo.get("nombre") or "Tramo DC",
            "n_paneles": int(tramo["n_paneles"]),
            "longitud_m": L,
            "calibre_mm2": S,
            "resistencia_ohm": r_ohm,
            "fraccion_paneles": fraccion,
        })

    # Resistencia DC EFECTIVA para pérdida total, Σ(fracción_i² · R_i): la
    # potencia perdida en cada tramo es (I_total·fracción_i)²·R_i, así que
    # la pérdida TOTAL de todos los tramos es exactamente
    # I_total² · Σ(fracción_i²·R_i) -- una sola resistencia escalar que el
    # motor de producción puede multiplicar por I_total(t)² hora a hora sin
    # tener que iterar tramo por tramo dentro del cálculo vectorizado.
    # (OJO: NO es la combinación en paralelo 1/Σ(1/R_i) -- esa fórmula solo
    # es correcta si todos los tramos llevan la MISMA corriente total, y
    # aquí cada tramo lleva solo su propia fracción.)
    resistencia_dc_efectiva_ohm = None
    if tramos_out and all(t["resistencia_ohm"] is not None for t in tramos_out):
        resistencia_dc_efectiva_ohm = sum(
            (t["fraccion_paneles"] ** 2) * t["resistencia_ohm"] for t in tramos_out
        )

    # Factor 3 (no 2): el tramo AC es trifásico -- la corriente que el motor
    # de producción multiplica contra esta resistencia (I_ac = P/(√3·V), la
    # corriente DE LÍNEA, misma convención que corriente_diseno_ac() usa en
    # todo el resto de la app) fluye por 3 conductores de fase, cada uno con
    # resistencia ρ·L/S -- la pérdida TOTAL es 3·I_línea²·(ρ·L/S), no
    # 2·I²·(ρ·L/S) (esa duplicación es la convención de un circuito DC de 2
    # hilos -- ida y vuelta -- que NO aplica aquí). Encontrado en auditoría
    # (7-sep-2026): con el factor 2 original, la pérdida óhmica AC calculada
    # quedaba subestimada ~33% frente al valor físico real.
    resistencia_ac_ohm = (
        3.0 * float(longitud_ac_m) * resistividad / float(calibre_ac_mm2)
        if longitud_ac_m and calibre_ac_mm2 else None
    )

    corriente_dc_diseno_A = corriente_diseno_dc(panel.get("Isc_stc"), N_strings_tracker)
    p_ac_unidad_kW = (
        float(inversor["P_ac_nom_W"]) / 1000.0 if inversor.get("P_ac_nom_W")
        else float(inversor["P_ac_nom_kW"]) if inversor.get("P_ac_nom_kW") else None
    )
    corriente_ac_diseno_A = corriente_diseno_ac(p_ac_unidad_kW, n_inversores, tension_red_V)

    return {
        "tramos": tramos_out,
        "resistencia_dc_efectiva_ohm": resistencia_dc_efectiva_ohm,
        "resistencia_ac_ohm": resistencia_ac_ohm,
        "corriente_dc_diseno_A": corriente_dc_diseno_A,
        "corriente_ac_diseno_A": corriente_ac_diseno_A,
        "resistividad_ohm_mm2_m": round(resistividad, 6),
        "T_diseno_C": T_diseno_C,
        "fuente": "IEC 60228 (cobre recocido, 0.0172 Ω·mm²/m a 20°C) + coef. temp. 0.393%/°C",
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
    if cfg.get("retie", {}).get("equipotencialidad"):
        # Sin símbolo unicode: "⏚" (earth ground, U+23DA) no está en la
        # fuente por defecto de matplotlib (DejaVu Sans) -- se renderiza
        # como glyph faltante. Encontrado renderizando de verdad (no solo
        # `isinstance(d, Drawing)`, que no detecta esto).
        lineas.append("Equipotencialidad: estructura y marcos → PE")
    return "\n".join(lineas)


def _dibujar_detalle_proteccion(d: schemdraw.Drawing, detalle: list[str], x: float, y_top: float) -> None:
    """
    Dibuja los ítems de detalle RETIE de una protección (DC o AC) como un
    bloque de texto APARTE, a la derecha del símbolo -- NO fusionado con
    la etiqueta propia del Fuse/Breaker.

    Primer intento (descartado): concatenar todo en una sola etiqueta
    `.label(texto, loc="right")`. Con una etiqueta de varias líneas,
    schemdraw la centra sobre el propio símbolo (no la desplaza a la
    derecha como con una etiqueta corta de 1 línea) -- el bloque quedaba
    literalmente encima del fusible/breaker. Intentar corregirlo con
    `halign="left"` + `ofst` no dio un desplazamiento horizontal
    predecible (probado con varios valores en /scratchpad) y además
    rompía el caso base (sin detalle) que ya estaba auditado.

    En vez de pelear con el alineado automático, se usa un elemento
    `elm.Label()` aparte posicionado con coordenadas EXPLÍCITAS -- mismo
    criterio que `_caja`/`_gap` desde Fase 2. `y_top` es la Y del extremo
    superior del Fuse/Breaker (y0 en el llamador); el bloque se ancla un
    poco más abajo y a la derecha, con `valign="top"` para que crezca
    hacia abajo (el llamador debe reservar espacio de sobra con
    `_holgura_por_detalle` en el gap que sigue).
    """
    if not detalle:
        return
    texto = "\n".join(f"• {item}" for item in detalle)
    d.add(elm.Label().label(texto, halign="left", valign="top").at((x + 0.35, y_top - 0.55)))


def _holgura_por_detalle(n_items: int) -> float:
    """Espacio extra (schemdraw units) a sumar al gap que sigue a un
    Fuse/Breaker con detalle RETIE, para que el bloque de
    `_dibujar_detalle_proteccion` (que crece hacia abajo) no invada la
    siguiente caja. El gap ANTES del Fuse/Breaker no necesita holgura
    extra -- el detalle empieza a la altura de y_top hacia abajo, no
    hacia arriba, así que no le quita espacio a la caja anterior
    (verificado renderizando de verdad en /scratchpad). Constante
    calibrada empíricamente, mismo método que _calcular_paso_superficies."""
    return n_items * 0.32


def _label_inversor(cfg: dict) -> str:
    inv = cfg["inversores"]
    n = inv["cantidad"]
    nombre = inv.get("nombre") or "Inversor"
    prefijo = f"{n} × " if n > 1 else ""
    sufijo_hibrido = " Híbrido" if cfg["bateria"]["activa"] and "híbrido" not in nombre.lower() and "hibrido" not in nombre.lower() else ""
    lineas = [f"{prefijo}{nombre}{sufijo_hibrido}"]
    if inv.get("p_ac_total_kW"):
        sufijo = " total" if n > 1 else ""
        lineas.append(f"{inv['p_ac_total_kW']:.1f} kW AC{sufijo}")
    return "\n".join(lineas)


def _label_superficie(s: dict) -> str:
    lineas = [s.get("nombre") or "Superficie"]
    partes = []
    if s.get("n_paneles"):
        partes.append(f"{s['n_paneles']} paneles")
    if s.get("p_dc_kWp"):
        partes.append(f"{s['p_dc_kWp']:.2f} kWp")
    if partes:
        lineas.append(" · ".join(partes))
    return "\n".join(lineas)


def _label_bateria(cfg: dict) -> str:
    b = cfg["bateria"]
    lineas = [b.get("nombre") or "Batería"]
    partes = []
    if b.get("cantidad"):
        partes.append(f"{b['cantidad']} unidades")
    if b.get("capacidad_total_kWh"):
        partes.append(f"{b['capacidad_total_kWh']:.1f} kWh")
    if partes:
        lineas.append(" · ".join(partes))
    return "\n".join(lineas)


def _caja(d: schemdraw.Drawing, w: float, h: float, x_centro: float, y_top: float,
          label: str, loc: str = "top") -> float:
    """
    Coloca un Rect (bloque genérico: generador, inversor, batería, medidor)
    centrado en x_centro con su borde SUPERIOR en y_top. Devuelve y_bottom.

    Nota técnica (por qué existe este helper en vez de encadenar elementos):
    Rect().at((x, y)) ancla su esquina INFERIOR-IZQUIERDA en (x, y), no el
    centro ni el borde superior -- verificado empíricamente (ver
    DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md, sección Diagrama Unifilar Fase 2).
    Encadenar elementos con .down()/.right() implícito (sin .at()) funciona
    para una sola columna vertical (Fase 1), pero se vuelve impredecible en
    cuanto hay una rama lateral (batería) -- por eso desde Fase 2 el módulo
    usa coordenadas explícitas en toda la función, no solo en la rama nueva.
    """
    y_bottom = y_top - h
    d.add(elm.Rect(w=w, h=h).right().at((x_centro - w / 2, y_bottom)).label(label, loc=loc))
    return y_bottom


def _gap(d: schemdraw.Drawing, x: float, y_top: float, largo: float) -> float:
    """Línea de separación vertical -- también reserva el espacio que necesita
    la etiqueta (2-3 líneas) del bloque que viene después. Sin este espacio
    las etiquetas de bloques consecutivos se superponen (mismo hallazgo que
    el de _caja: verificado empíricamente, no es una suposición)."""
    y_bottom = y_top - largo
    d.add(elm.Line().at((x, y_top)).to((x, y_bottom)))
    return y_bottom


def _calcular_paso_superficies(superficies: list[dict], ancho_caja: float) -> float:
    """
    Separación centro-a-centro entre bloques de superficies vecinas.

    Un paso fijo (ancho_caja + 1.3) se ve bien con nombres cortos ("Sup0"),
    pero con nombres reales largos ("Marquesina Estacionamiento", 26
    caracteres) las etiquetas de dos superficies vecinas se solapan --
    encontrado en auditoría (27-ago-2026) probando con nombres realistas,
    no solo nombres de prueba cortos. Se calibró empíricamente el ancho de
    texto en schemdraw (~0.15-0.18 unidades por carácter a fontsize=11)
    para escalar el paso según el nombre más largo, en vez de un número
    fijo que solo funciona para nombres cortos.
    """
    max_chars = max(
        (len(linea) for sup in superficies for linea in _label_superficie(sup).split("\n")),
        default=0,
    )
    return max(ancho_caja + 1.3, max_chars * 0.17 + 1.0)


def _dibujar_generadores(d: schemdraw.Drawing, config: dict, x_main: float) -> float:
    """
    Dibuja el/los bloque(s) generador(es) y devuelve la Y desde donde debe
    continuar el resto de la cadena (Protección DC en adelante).

    Caso normal (0 o 1 superficie): un solo bloque "Generador FV" centrado
    en x_main -- idéntico a Fase 1/2, sin regresión.

    Caso multi-superficie (2+ superficies activas): N bloques generadores
    en fila, cada uno con su propia protección DC, todos convergiendo en
    un bus horizontal común. Geometría validada en /scratchpad antes de
    integrarla aquí (mismo criterio que la rama de batería en Fase 2) --
    a diferencia de la batería, las superficies SÍ deben converger (son
    fuentes que alimentan el mismo inversor, no una rama informativa que
    cuelga), por eso usan un bus horizontal en vez de líneas colgantes.
    """
    superficies = config.get("superficies")
    if not superficies or len(superficies) < 2:
        return _caja(d, 2.8, 1.4, x_main, 0.0, _label_generador(config))

    n = len(superficies)
    ancho_caja = 2.6
    paso = _calcular_paso_superficies(superficies, ancho_caja)
    x0 = -paso * (n - 1) / 2.0
    bus_y = None
    for i, sup in enumerate(superficies):
        x = x0 + i * paso
        y = _caja(d, ancho_caja, 1.2, x, 0.0, _label_superficie(sup))
        y = _gap(d, x, y, 0.5)
        y0, y1 = y, y - 0.8
        d += elm.Fuse().at((x, y0)).to((x, y1)).label("Prot.", loc="bottom")
        d += elm.Dot().at((x, y1))
        bus_y = y1  # todas las superficies usan la misma altura de caja -> mismo y1

    x_izq, x_der = x0, x0 + paso * (n - 1)
    d += elm.Line().at((x_izq, bus_y)).to((x_der, bus_y))
    return bus_y


def generar_diagrama_unifilar(config: dict) -> schemdraw.Drawing:
    """
    Dibuja el diagrama unifilar a partir de un config de
    construir_config_unifilar(). Ver docstring del módulo para el alcance
    exacto por fase y las limitaciones conocidas.
    """
    # Nota: el título del proyecto/cliente NO se dibuja dentro del esquema --
    # lo pinta quien use el diagrama (página Streamlit, PDF), igual que el
    # resto de la app separa encabezados de documento del contenido gráfico.
    d = schemdraw.Drawing(fontsize=11)
    X_MAIN, X_BAT = 0.0, -2.8

    detalle_dc = config.get("retie", {}).get("detalle_dc", [])
    holgura_dc = _holgura_por_detalle(len(detalle_dc))

    Y = _dibujar_generadores(d, config, X_MAIN)
    Y = _gap(d, X_MAIN, Y, 0.9)
    d += elm.Dot().at((X_MAIN, Y))

    dc_A = config.get("proteccion_dc_A")
    etiqueta_dc = f"Protección DC ({dc_A:.0f} A)" if dc_A else "Protección DC"
    y0, Y = Y, Y - 1.1
    d += elm.Fuse().at((X_MAIN, y0)).to((X_MAIN, Y)).label(etiqueta_dc, loc="right")
    _dibujar_detalle_proteccion(d, detalle_dc, X_MAIN, y0)
    d += elm.Dot().at((X_MAIN, Y))
    dc_bus_y = Y  # punto donde la batería (si existe) entra al mismo bus DC

    bat = config["bateria"]
    if bat["activa"]:
        d += elm.Line().at((X_MAIN, dc_bus_y)).to((X_BAT, dc_bus_y))
        y = _gap(d, X_BAT, dc_bus_y, 0.7)

        bat_A = bat.get("proteccion_bat_A")
        etiqueta_bat = f"Protección Bat. ({bat_A:.0f} A)" if bat_A else "Protección Bat."
        y0, y1 = y, y - 1.1
        d += elm.Fuse().at((X_BAT, y0)).to((X_BAT, y1)).label(etiqueta_bat, loc="left")
        y1 = _gap(d, X_BAT, y1, 0.5)
        _caja(d, 2.2, 1.1, X_BAT, y1, _label_bateria(config), loc="left")

    detalle_ac = config.get("retie", {}).get("detalle_ac", [])
    holgura_ac = _holgura_por_detalle(len(detalle_ac))

    Y = _gap(d, X_MAIN, dc_bus_y, 0.8 + holgura_dc)
    Y = _caja(d, 2.8, 1.3, X_MAIN, Y, _label_inversor(config))
    Y = _gap(d, X_MAIN, Y, 0.9)

    ac_A = config.get("proteccion_ac_A")
    etiqueta_ac = f"Protección AC ({ac_A:.0f} A)" if ac_A else "Protección AC"
    y0, Y = Y, Y - 1.1
    d += elm.Breaker().at((X_MAIN, y0)).to((X_MAIN, Y)).label(etiqueta_ac, loc="right")
    _dibujar_detalle_proteccion(d, detalle_ac, X_MAIN, y0)

    Y = _gap(d, X_MAIN, Y, 0.7 + holgura_ac)
    medidor_txt = f"Medidor {config.get('medidor') or 'Bidireccional'}"
    Y = _caja(d, 2.8, 1.1, X_MAIN, Y, medidor_txt)
    Y = _gap(d, X_MAIN, Y, 0.9)
    d += elm.Dot().at((X_MAIN, Y))

    tension = config.get("tension_red_V")
    etiqueta_red = (
        f"Red / Punto de Conexión Común — PCC ({tension:.0f} V)"
        if tension else "Red / Punto de Conexión Común — PCC"
    )
    y0, Y = Y, Y - 0.6
    d += elm.Line().at((X_MAIN, y0)).to((X_MAIN, Y)).label(etiqueta_red, loc="right")
    d += elm.Ground().at((X_MAIN, Y))

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
