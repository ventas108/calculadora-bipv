"""
Dimensionamiento de strings y sistema.
Equivalente de Mod_CalculoStringSizing + Mod_OptimizarStringSizing (VBA).

Resultado validado vs XLSM (hoja Optimizacion_String):
  N=8 paneles/string, Growatt MID15KTL3-X → 0 riesgos ✓
  N=7 → ALERTA (Vmp realista margen < 7.5%)
  N=9 → FALLA (Voc frío > 1100V)
"""
import math
from dataclasses import dataclass
from typing import Literal


EstadoVerif = Literal["OK", "ALERTA", "FALLA"]
UMBRAL_ALERTA_PCT = 7.5  # % — umbral de alerta (extraído de hoja Optimizacion_String L14)


def _numero_finito(valor, default: float = 0.0) -> float:
    """Convierte valores del Excel y trata NaN/inf como dato faltante."""
    try:
        numero = float(valor)
        return numero if math.isfinite(numero) else default
    except (TypeError, ValueError):
        return default


def _entero_catalogo(valor, default: int = 0) -> int:
    """Convierte contadores del catálogo sin ejecutar int(NaN)."""
    numero = _numero_finito(valor, float(default))
    return int(numero) if numero >= 0 else default


@dataclass
class ResultadoString:
    N_serie: int
    Voc_frio: float
    Vmp_real: float
    Vmp_extremo: float
    I_equiv_tracker: float
    v1_voc_max:   EstadoVerif = "OK"
    v2_vmp_real:  EstadoVerif = "OK"
    v3_vmp_extr:  EstadoVerif = "OK"
    v4_i_max:     EstadoVerif = "OK"
    v5_vmp_max:   EstadoVerif = "OK"   # Vmp_real ≤ Vmppt_max — límite superior MPPT
    riesgos: int = 0
    mppt_util_pct: float = 0.0         # Vmp_real / Vmppt_max × 100 — aprovechamiento del rango MPPT

    def semaforo_color(self) -> str:
        if self.riesgos == 0:
            return "🟢"
        elif any(v == "FALLA" for v in [self.v1_voc_max, self.v2_vmp_real,
                                         self.v3_vmp_extr, self.v4_i_max,
                                         self.v5_vmp_max]):
            return "🔴"
        return "🟡"


def semaforo(valor: float, limite: float, invertir=False) -> EstadoVerif:
    """
    Semáforo con margen de alerta de 7.5% (valor del VBA).
    invertir=False → valor debe ser ≤ limite  (ej: Voc ≤ Vdc_max)
    invertir=True  → valor debe ser ≥ limite  (ej: Vmp ≥ Vmppt_min)
    """
    if not invertir:
        if valor > limite:
            return "FALLA"
        margen = (limite - valor) / limite * 100
        return "ALERTA" if margen < UMBRAL_ALERTA_PCT else "OK"
    else:
        if valor < limite:
            return "FALLA"
        margen = (valor - limite) / limite * 100
        return "ALERTA" if margen < UMBRAL_ALERTA_PCT else "OK"


def calcular_voc_string(N, Voc_stc, Tk_beta, T_cel):
    return N * Voc_stc * (1 + Tk_beta / 100.0 * (T_cel - 25.0))


def calcular_vmp_string(N, Vmp_stc, Tk_beta, T_cel):
    """Vmp del string a temperatura T_cel.

    Usa Tk_beta (coeficiente de VOLTAJE, el de Voc) -- no Tk_gamma (el de
    POTENCIA, Pmax). Antes del 25-ago-2026 esta función recibía Tk_gamma
    por error: subestimaba cuánto sube el Voc en frío y cuánto baja el
    Vmp en calor, justo las dos condiciones extremas que evaluar_compatibilidad_string()
    usa para decidir si un string es eléctricamente seguro (ver
    tests/test_validacion_vba.py::test_vmp_n8_vs_xlsm).
    """
    return N * Vmp_stc * (1 + Tk_beta / 100.0 * (T_cel - 25.0))


def evaluar_compatibilidad_string(
    panel: dict,
    inversor: dict,
    N_serie: int,
    T_frio: float = -5.0,
    T_real: float = 36.35,
    T_extremo: float = 41.94,
    N_strings_tracker: int = 1,
    FS_isc: float = 1.25,
) -> dict:
    """Evalúa una configuración concreta de string contra un inversor.

    Esta función es deliberadamente pura para que Producción, Dimensionamiento
    y las pruebas usen exactamente los mismos límites eléctricos.
    """
    try:
        n = int(N_serie)
        voc_frio = calcular_voc_string(
            n, float(panel["Voc_stc"]), float(panel["Tk_beta"]), float(T_frio)
        )
        vmp_real = calcular_vmp_string(
            n, float(panel["Vmp_stc"]), float(panel["Tk_beta"]), float(T_real)
        )
        vmp_extremo = calcular_vmp_string(
            n, float(panel["Vmp_stc"]), float(panel["Tk_beta"]), float(T_extremo)
        )
        isc_equiv = (
            float(panel["Isc_stc"]) * int(N_strings_tracker) * float(FS_isc)
        )
        vdc_max = _numero_finito(inversor.get("Vdc_max"))
        # Vmppt_activo_min PRIMERO -- es el piso de operación recomendado/típico
        # del inversor (ej. Growatt MAX 100KTL3 LV: 850 V), no el mínimo absoluto
        # de arranque (Vmppt_min, 200 V). El orden invertido (Vmppt_min primero)
        # aprobaba configuraciones que optimizar_n_serie() (validado contra el
        # XLSM original, misma función de este archivo) y
        # comparador_inversores.filtrar_inversores_compatibles() ya rechazaban
        # como FALLA/incompatible para la misma config -- encontrado en
        # auditoría (27-ago-2026) ejecutando las 3 funciones con datos reales
        # del proyecto Urabá (18 en serie: Vmp=720 V < Vmppt_activo_min=850 V,
        # pero > Vmppt_min=200 V). Esta función es la que usa el gate
        # verde/rojo de Página 6 Producción -- daba verde donde debía dar rojo.
        vmppt_min = _numero_finito(
            inversor.get("Vmppt_activo_min")
            or inversor.get("Vmppt_min")
        )
        vmppt_max = _numero_finito(inversor.get("Vmppt_max"))
        isc_max = _numero_finito(
            inversor.get("Isc_max_tracker")
            or inversor.get("I_max_tracker")
        )
    except (KeyError, TypeError, ValueError):
        return {
            "compatible": False,
            "evaluable": False,
            "mensajes": ["Faltan parámetros eléctricos válidos del panel o del inversor."],
        }

    faltantes = []
    if not vdc_max:
        faltantes.append("Vdc máximo")
    if not vmppt_min:
        faltantes.append("MPPT mínimo")
    if not vmppt_max:
        faltantes.append("MPPT máximo")
    if not isc_max:
        faltantes.append("corriente máxima por tracker")
    if faltantes:
        return {
            "compatible": False,
            "evaluable": False,
            "mensajes": [
                f"Ficha incompleta: falta(n) {', '.join(faltantes)} del inversor."
            ],
            "faltantes": faltantes,
            "N_serie": n,
        }

    # `compatible` usa exactamente las mismas comparaciones de siempre (sin
    # margen) -- no cambia para nadie que ya dependa de este booleano (incluye
    # proyectos reales ya entregados, ej. Urabá). `alerta_margen` es un dato
    # NUEVO, puramente informativo, agregado el 29-ago-2026 al armonizar esta
    # función con optimizar_n_serie()/semaforo(): esa función SÍ aplica un
    # margen de seguridad del 7,5% (UMBRAL_ALERTA_PCT, heredado de la hoja
    # Excel original Optimizacion_String celda L14) antes de considerar un N
    # "seguro" -- esta función, hasta ahora, no lo aplicaba en absoluto. Eso
    # hacía que el mismo N pudiera salir "✅ Compatible" aquí (usada por
    # mapear_inversores_catalogo() / "🧭 Mapeo de inversores") y a la vez
    # "🟡 ALERTA" en optimizar_n_serie() (el botón "▶️ Optimizar N paneles/
    # string") -- encontrado con datos reales (TriP 6K-HV, N=8: Voc frío
    # 987,6V a solo 1,24% del Vdc_max de 1000V -- "compatible" aquí, pero
    # "ALERTA" allá, dando recomendaciones de N distintas para el mismo
    # inversor real). `alerta_margen=True` NO cambia `compatible`; solo marca
    # que al menos una condición pasó por muy poco margen -- ver su uso en
    # mapear_inversores_catalogo() para preferir configuraciones con margen
    # real sobre las que solo raspan el límite.
    mensajes = []
    alerta_margen = False

    if voc_frio > vdc_max:
        mensajes.append(f"Voc en frío {voc_frio:.0f} V > Vdc máximo {vdc_max:.0f} V")
    elif semaforo(voc_frio, vdc_max, invertir=False) == "ALERTA":
        alerta_margen = True

    if vmp_real < vmppt_min:
        mensajes.append(f"Vmp real {vmp_real:.0f} V < MPPT mínimo {vmppt_min:.0f} V")
    elif semaforo(vmp_real, vmppt_min, invertir=True) == "ALERTA":
        alerta_margen = True
    if vmp_extremo < vmppt_min:
        mensajes.append(
            f"Vmp extremo {vmp_extremo:.0f} V < MPPT mínimo {vmppt_min:.0f} V"
        )
    elif semaforo(vmp_extremo, vmppt_min, invertir=True) == "ALERTA":
        alerta_margen = True

    if vmp_real > vmppt_max:
        mensajes.append(f"Vmp real {vmp_real:.0f} V > MPPT máximo {vmppt_max:.0f} V")
    elif semaforo(vmp_real, vmppt_max, invertir=False) == "ALERTA":
        alerta_margen = True
    if vmp_extremo > vmppt_max:
        mensajes.append(
            f"Vmp extremo {vmp_extremo:.0f} V > MPPT máximo {vmppt_max:.0f} V"
        )
    elif semaforo(vmp_extremo, vmppt_max, invertir=False) == "ALERTA":
        alerta_margen = True

    if isc_equiv > isc_max:
        mensajes.append(
            f"Isc de strings {isc_equiv:.2f} A > límite por tracker {isc_max:.2f} A"
        )
    elif semaforo(isc_equiv, isc_max, invertir=False) == "ALERTA":
        alerta_margen = True

    return {
        "compatible": not mensajes,
        "alerta_margen": alerta_margen,
        "evaluable": True,
        "mensajes": mensajes,
        "N_serie": n,
        "Voc_frio": voc_frio,
        "Vmp_real": vmp_real,
        "Vmp_extremo": vmp_extremo,
        "Isc_equiv_tracker": isc_equiv,
    }


def evaluar_relacion_dc_ac(P_dc_stc_kW: float, P_ac_nom_W: float | None) -> dict:
    """
    Evalúa si la relación DC/AC (potencia FV instalada / potencia CA nominal
    del inversor -- PVsyst la llama "Proporción Pnom") es un acople de diseño
    coherente, más allá de la compatibilidad eléctrica pura (Voc/Vmppt/Isc,
    ver evaluar_compatibilidad_string()). Complementa esa función: un string
    puede ser eléctricamente válido (tensión y corriente dentro de ventana)
    y aun así estar mal dimensionado en POTENCIA -- inversor de más (capital
    desperdiciado) o de menos (recorte/clipping real, ver
    calculos.produccion.simular_produccion_anual, parámetro P_ac_nom_W).

    Pedido explícito del usuario (29-ago-2026) tras verificar en PVsyst 8.1.5
    que el proyecto Teusaquillo (128 módulos, 8,1 kWp, Growatt MID15KTL3-X
    15 kW CA) muestra el aviso real "La potencia del inversor está muy
    sobredimensionada" con "Proporción Pnom: 0.538" -- confirmado idéntico
    al 0.538 que calcula esta misma fórmula. La app no tenía ningún aviso
    equivalente; solo `calculos.comparador_inversores` reportaba el ratio
    como dato informativo, sin evaluarlo.

    Umbrales usados (criterio propio de esta app, NO el algoritmo interno de
    PVsyst -- no hay forma de verificar ese algoritmo desde aquí): anclados
    al dato real de PVsyst (0.538 → "muy sobredimensionado") por el lado
    bajo, y a la convención general de la industria para el "Inverter
    Loading Ratio" (rango típico de diseño 1.10–1.35, NREL/SAM) por el lado
    alto. Son un umbral de ORIENTACIÓN para el usuario, no una certificación
    -- cada proyecto real puede tener razones válidas para salirse de este
    rango (ej. reutilizar un inversor ya comprado, como el propio Teusaquillo).

    Retorna
    -------
    dict con:
      evaluable  : False si P_ac_nom_W es None/0 -- no hay con qué comparar.
      ratio      : P_dc_stc_kW*1000 / P_ac_nom_W (None si no evaluable).
      estado     : "muy_sobredimensionado" | "sobredimensionado" | "optimo"
                   | "alto" | "muy_alto" | None (si no evaluable).
      nivel      : "🔴" | "🟠" | "🟢" | None.
      mensaje    : texto listo para mostrar al usuario.
    """
    if not P_ac_nom_W or P_ac_nom_W <= 0:
        return {
            "evaluable": False,
            "ratio": None,
            "estado": None,
            "nivel": None,
            "mensaje": "El inversor no tiene potencia CA nominal registrada -- no se puede evaluar la relación DC/AC.",
        }

    ratio = round(P_dc_stc_kW * 1000.0 / P_ac_nom_W, 3)

    if ratio < 0.75:
        estado, nivel = "muy_sobredimensionado", "🔴"
        mensaje = (
            f"Inversor MUY sobredimensionado (relación DC/AC = {ratio:.2f}). "
            f"El array FV ({P_dc_stc_kW:.2f} kWp) usa menos de tres cuartos de la "
            f"capacidad del inversor ({P_ac_nom_W/1000:.1f} kW CA) -- capital de inversor "
            "sin aprovechar. Mismo tipo de aviso que da PVsyst (\"La potencia del inversor "
            "está muy sobredimensionada\") para relaciones en este rango."
        )
    elif ratio < 1.0:
        estado, nivel = "sobredimensionado", "🟠"
        mensaje = (
            f"Inversor sobredimensionado (relación DC/AC = {ratio:.2f}) -- por debajo del "
            "rango típico de diseño (0.95–1.35). Verifica si es una decisión deliberada "
            "(ej. inversor ya disponible/reutilizado) o si conviene un equipo más pequeño."
        )
    elif ratio <= 1.35:
        estado, nivel = "optimo", "🟢"
        mensaje = f"Relación DC/AC = {ratio:.2f} -- dentro del rango típico de diseño (0.95–1.35)."
    elif ratio <= 1.6:
        estado, nivel = "alto", "🟠"
        mensaje = (
            f"Relación DC/AC alta ({ratio:.2f}). Revisa `perdida_clipping_kWh` tras simular "
            "producción -- es probable que haya recorte real en las horas de mayor irradiancia."
        )
    else:
        estado, nivel = "muy_alto", "🔴"
        mensaje = (
            f"Relación DC/AC MUY alta ({ratio:.2f}). Se espera recorte (clipping) "
            "significativo -- confirma el % de energía recortada tras simular producción "
            "antes de dar este diseño por bueno."
        )

    return {
        "evaluable": True,
        "ratio": ratio,
        "estado": estado,
        "nivel": nivel,
        "mensaje": mensaje,
    }


def resolver_n_strings_tracker(
    inversor: dict,
    inversor_nombre: str,
    session_state,
    N_total_cadenas: int = 0,
) -> dict:
    """
    Resuelve N_strings/tracker con DOS mecanismos posibles -- comparación
    honesta pedida explícitamente por el usuario (29-ago-2026) contra cómo
    lo hace PVsyst, tras validar el proyecto real Teusaquillo:

    1) MECANISMO PVsyst (si `N_total_cadenas` > 0): el usuario declara el
       TOTAL de cadenas que quiere para todo el generador -- lo mismo que
       PVsyst pide en su campo "Núm. cadenas" -- y esta función reparte ese
       total entre los trackers/MPPT del inversor:
           N_str_tr = ceil(N_total_cadenas / n_trackers)
       Es el mecanismo que PVsyst usa siempre: parte de lo que el usuario
       QUIERE instalar, no de la capacidad del equipo.

    2) MECANISMO CATÁLOGO (si `N_total_cadenas` es 0/None, default): el
       comportamiento anterior de esta función -- autocalcula desde la
       capacidad MÁXIMA que soporta el inversor en el catálogo
       (`inversor["n_strings_tracker"]`). Sigue siendo el default porque
       esta página es de EXPLORACIÓN ("¿cuánto cabe?"), no de verificación
       de un diseño que el usuario ya decidió -- PVsyst asume lo segundo,
       por eso siempre pide el total primero. Antes (29-ago-2026) el widget
       quedaba fijo en 1 sin importar el inversor elegido, lo que llevó a
       calcular "16 paneles/inversor, 8 inversores necesarios" en vez de
       "128 paneles/inversor, 1 inversor" para el proyecto real Teusaquillo.

    En ambos casos se respeta un ajuste manual posterior del usuario
    mientras la fuente activa no cambie (mismo inversor y mismo total
    declarado -- para el mecanismo 1 --, o mismo inversor sin total -- para
    el 2). Cambiar de un mecanismo a otro, de inversor, o de total declarado
    SIEMPRE resetea al valor recién calculado esa vez.

    `session_state` es cualquier objeto dict-like con `.get()` y asignación
    por índice (`st.session_state` en producción; un `dict` plano en tests).
    Guarda `N_str_tr` (el valor efectivo, mismo nombre que ya usan pages/4 y
    pages/6) y `N_str_tr_fuente_ref` (firma de qué combinación de
    mecanismo/inversor/total produjo ese valor -- permite detectar el
    cambio entre reruns).

    Retorna dict:
      valor       : N_strings/tracker efectivo (int)
      fuente      : "total" | "catalogo"
      recalculado : True solo en el render donde se detectó un cambio de
                    fuente/inversor/total y se reseteó al valor calculado
                    esa vez; en cualquier otro render retorna False y
                    respeta lo que ya haya en `session_state["N_str_tr"]`
      n_trackers  : trackers/MPPT del inversor usados para el reparto
                    (solo relevante -- y no None -- cuando fuente=="total")
    """
    n_trackers = int(inversor.get("n_trackers") or inversor.get("N_mppt") or 1)

    if N_total_cadenas:
        N_total_cadenas = int(N_total_cadenas)
        derivado = math.ceil(N_total_cadenas / n_trackers) if n_trackers > 0 else N_total_cadenas
        firma = ("total", inversor_nombre, N_total_cadenas, n_trackers)
        fuente, default_valor = "total", derivado
    else:
        firma = ("catalogo", inversor_nombre)
        fuente, default_valor = "catalogo", int(inversor.get("n_strings_tracker") or 1)

    if session_state.get("N_str_tr_fuente_ref") != firma:
        session_state["N_str_tr"] = default_valor
        session_state["N_str_tr_fuente_ref"] = firma
        return {
            "valor": default_valor, "sugerido": default_valor,
            "fuente": fuente, "recalculado": True, "n_trackers": n_trackers,
        }

    return {
        "valor": int(session_state.get("N_str_tr", default_valor) or default_valor),
        "sugerido": default_valor,
        "fuente": fuente,
        "recalculado": False,
        "n_trackers": n_trackers,
    }


def mapear_inversores_catalogo(
    panel: dict,
    inversores: dict,
    N_min: int = 1,
    N_max: int = 40,
    T_frio: float = -5.0,
    T_real: float = 36.35,
    T_extremo: float = 41.94,
    N_strings_tracker: int = 1,
    FS_isc: float = 1.25,
) -> list[dict]:
    """Mapea inversores opcionales para un panel en todo el rango de N/string.

    Regla de opción: un inversor es opcional si existe al menos un N dentro del
    rango indicado que pasa simultáneamente Voc frío, MPPT mínimo, MPPT máximo
    y corriente por tracker. No cambia la selección activa del proyecto.
    """
    try:
        n_min = max(1, int(N_min))
        n_max = max(n_min, int(N_max))
    except (TypeError, ValueError):
        n_min, n_max = 1, 40

    def _resumir_rango(valores: list[int]) -> str:
        if not valores:
            return "—"
        grupos = []
        inicio = anterior = valores[0]
        for valor in valores[1:]:
            if valor == anterior + 1:
                anterior = valor
                continue
            grupos.append(str(inicio) if inicio == anterior else f"{inicio}–{anterior}")
            inicio = anterior = valor
        grupos.append(str(inicio) if inicio == anterior else f"{inicio}–{anterior}")
        return ", ".join(grupos)

    filas = []
    for nombre, inversor in sorted((inversores or {}).items()):
        evaluaciones = [
            evaluar_compatibilidad_string(
                panel=panel,
                inversor=inversor,
                N_serie=n,
                T_frio=T_frio,
                T_real=T_real,
                T_extremo=T_extremo,
                N_strings_tracker=N_strings_tracker,
                FS_isc=FS_isc,
            )
            for n in range(n_min, n_max + 1)
        ]
        evaluables = [r for r in evaluaciones if r.get("evaluable")]
        n_trackers = _entero_catalogo(
            inversor.get("n_trackers") or inversor.get("N_mppt")
        )
        strings_tracker = _entero_catalogo(
            inversor.get("n_strings_tracker")
            or inversor.get("N_strings_nativo")
        )
        faltantes_conexion = []
        if n_trackers <= 0:
            faltantes_conexion.append("número de trackers")
        if strings_tracker <= 0:
            faltantes_conexion.append("strings por tracker")
        compatibles = (
            [r for r in evaluables if r.get("compatible")]
            if not faltantes_conexion
            else []
        )

        vmppt_max = _numero_finito(inversor.get("Vmppt_max"))
        if faltantes_conexion:
            elegido = next(iter(evaluables), evaluaciones[0] if evaluaciones else {})
            estado = "🟡 No evaluable"
            motivo = (
                "Ficha incompleta: faltan "
                + ", ".join(faltantes_conexion)
                + "."
            )
        elif compatibles:
            # Igual criterio que el optimizador: aprovechar al máximo el techo
            # MPPT, sin introducir una preferencia comercial arbitraria. Desde
            # el 29-ago-2026, también prioriza `not alerta_margen` PRIMERO
            # (evita recomendar un N que solo "compatible" técnicamente pero
            # raspando el límite físico por <7,5%) -- antes este `max()`
            # podía recomendar un N distinto al que elige optimizar_n_serie()
            # para el MISMO inversor real (ver docstring de
            # evaluar_compatibilidad_string() para el caso real que expuso
            # esto: TriP 6K-HV, N=8 vs N=7).
            elegido = max(
                compatibles,
                key=lambda r: (
                    not r.get("alerta_margen", False),
                    r["Vmp_real"] / vmppt_max if vmppt_max else 0.0,
                    r["N_serie"],
                ),
            )
            estado = "✅ Compatible"
            motivo = "Al menos un N/string pasa todos los límites eléctricos."
        elif evaluables:
            elegido = min(evaluables, key=lambda r: (len(r.get("mensajes", [])), r["N_serie"]))
            estado = "🔴 No compatible"
            motivo = (
                f"Mejor intento N={elegido['N_serie']}: "
                + "; ".join(elegido.get("mensajes", []))
            )
        else:
            elegido = evaluaciones[0] if evaluaciones else {}
            estado = "🟡 No evaluable"
            motivo = "; ".join(elegido.get("mensajes", [])) or "Rango sin evaluaciones."

        filas.append({
            "modelo": nombre,
            "estado": estado,
            "compatible": bool(compatibles),
            "N_string_recomendado": elegido.get("N_serie"),
            "recomendado_con_margen_ajustado": bool(elegido.get("alerta_margen", False)),
            "N_viables": _resumir_rango(sorted(r["N_serie"] for r in compatibles)),
            "Voc_frio_V": round(elegido["Voc_frio"], 1) if elegido.get("Voc_frio") is not None else None,
            "Vmp_real_V": round(elegido["Vmp_real"], 1) if elegido.get("Vmp_real") is not None else None,
            "Isc_tracker_A": round(elegido["Isc_equiv_tracker"], 2) if elegido.get("Isc_equiv_tracker") is not None else None,
            "Vdc_max_V": inversor.get("Vdc_max"),
            "MPPT_V": (
                # Vmppt_activo_min primero: es el piso que realmente se evalúa
                # más abajo (semáforo v2/v3) -- mostrar Vmppt_min aquí sería
                # inconsistente con el umbral que de verdad se aplica.
                f"{inversor.get('Vmppt_activo_min') or inversor.get('Vmppt_min') or '—'}–"
                f"{inversor.get('Vmppt_max') or '—'}"
            ),
            "trackers": n_trackers,
            "strings_tracker": strings_tracker,
            "P_ac_nom_kW": (
                round(float(inversor.get("P_ac_nom_W")) / 1000.0, 2)
                if inversor.get("P_ac_nom_W")
                else inversor.get("P_ac_nom_kW")
            ),
            "costo_usd": inversor.get("costo_usd"),
            "motivo": motivo,
        })

    return sorted(
        filas,
        key=lambda fila: (
            not fila["compatible"],
            fila["N_string_recomendado"] is None,
            fila["modelo"],
        ),
    )


def optimizar_n_serie(panel: dict, inversor: dict,
                      T_frio: float = -5.0,
                      T_real: float = 36.35,
                      T_extremo: float = 41.94,
                      N_strings_tracker: int = 8,
                      FS_isc: float = 1.25,
                      N_min: int = 6,
                      N_max: int = 12) -> list:
    """
    Equivalente de Mod_OptimizarStringSizing (VBA).
    Barrido de N paneles/string con semáforo OK/ALERTA/FALLA.

    Resultado validado vs XLSM (hoja Optimizacion_String):
      N=6 → Voc=763V OK, Vmp=499.5V → FALLA  ✓
      N=7 → Voc=890V OK, Vmp=582.8V → ALERTA ✓
      N=8 → Voc=1017V OK, Vmp=666V  → OK ✓  SELECCIONADO
      N=9 → Voc=1145V FALLA (>1100V) ✓
    """
    resultados = []
    for N in range(N_min, N_max + 1):
        Voc_fr  = calcular_voc_string(N, panel["Voc_stc"], panel["Tk_beta"], T_frio)
        Vmp_re  = calcular_vmp_string(N, panel["Vmp_stc"], panel["Tk_beta"], T_real)
        Vmp_ex  = calcular_vmp_string(N, panel["Vmp_stc"], panel["Tk_beta"], T_extremo)
        I_equiv = panel["Isc_stc"] * N_strings_tracker * FS_isc

        v1 = semaforo(Voc_fr,  inversor["Vdc_max"],          invertir=False)
        v2 = semaforo(Vmp_re,  inversor["Vmppt_activo_min"], invertir=True)
        v3 = semaforo(Vmp_ex,  inversor["Vmppt_activo_min"], invertir=True)
        # Check 4-Isimax: comparar contra Isc_max_tracker (cortocircuito),
        # no contra I_max_tracker (operación/MPP). Fallback a I_max_tracker si falta.
        _isc_lim = inversor.get("Isc_max_tracker") or inversor.get("I_max_tracker", 0)
        v4 = semaforo(I_equiv, _isc_lim,                    invertir=False)
        # Check 5: Vmp_real ≤ Vmppt_max — límite superior del rango MPPT.
        # Si Vmp supera Vmppt_max el inversor opera fuera de su ventana de seguimiento.
        _vmppt_max = inversor.get("Vmppt_max") or inversor.get("Vmppt_activo_max", 0)
        v5 = semaforo(Vmp_re, _vmppt_max, invertir=False) if _vmppt_max else "OK"

        # MPPT utilization: qué fracción del techo MPPT aprovecha este string
        _util = round(Vmp_re / _vmppt_max * 100, 1) if _vmppt_max else 0.0

        riesgos = sum(1 for v in [v1, v2, v3, v4, v5] if v in ("ALERTA", "FALLA"))
        resultados.append(ResultadoString(
            N_serie=N, Voc_frio=round(Voc_fr, 1), Vmp_real=round(Vmp_re, 1),
            Vmp_extremo=round(Vmp_ex, 1), I_equiv_tracker=round(I_equiv, 2),
            v1_voc_max=v1, v2_vmp_real=v2, v3_vmp_extr=v3, v4_i_max=v4,
            v5_vmp_max=v5, riesgos=riesgos, mppt_util_pct=_util,
        ))
    return resultados


def dimensionar_sistema(panel: dict, area_m2: float, N_serie: int,
                        N_strings_tracker: int, N_mppt: int) -> dict:
    """
    Dimensionamiento del sistema completo a partir del N óptimo.
    """
    N_strings_total = N_strings_tracker * N_mppt
    N_paneles       = N_serie * N_strings_total
    area_ocupada    = N_paneles * panel["area_m2"]
    P_dc_stc_W      = N_paneles * panel.get("Pmax_stc", 0)

    return {
        "N_paneles":         N_paneles,
        "N_strings_total":   N_strings_total,
        "P_dc_stc_kW":       round(P_dc_stc_W / 1000, 3),
        "area_ocupada_m2":   round(area_ocupada, 2),
        "cobertura_pct":     round(area_ocupada / area_m2 * 100, 1) if area_m2 > 0 else 0,
        "N_serie":           N_serie,
        "N_strings_tracker": N_strings_tracker,
        "N_mppt":            N_mppt,
    }
