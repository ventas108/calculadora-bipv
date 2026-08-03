"""
panel_iv_check.py — Validación de datos IV para Motor IV (SDM De Soto).
Módulo compartido usado por Dimensionamiento y Motor IV.
"""
from calculos.modelo_iv import verificar_ns_halfcut


def analizar_panel_motiv(p: dict) -> tuple:
    """
    Analiza si un panel tiene los datos necesarios para el Motor IV.

    Retorna (errores, advertencias) donde:
      errores      = [(campo, descripción)] — bloquean la simulación
      advertencias = [(campo, descripción)] — se usan defaults, menor precisión

    Criterio de campos requeridos (bloquean si faltan):
      Voc, Isc, Vmp, Imp

    Campos opcionales con default (generan advertencia):
      N_s, Tecnología, CoefVoc (β), CoefIsc (α)
    """
    _val = lambda *keys: any(
        p.get(k) not in (None, 0, 0.0, "", "nan", "0") for k in keys
    )

    errores = []
    if not _val("Voc_stc", "Voc"):
        errores.append(("Voc", "Tensión de circuito abierto en STC (V)"))
    if not _val("Isc_stc", "Isc"):
        errores.append(("Isc", "Corriente de cortocircuito en STC (A)"))
    if not _val("Vmp_stc", "Vmp"):
        errores.append(("Vmp", "Tensión en el punto de máxima potencia en STC (V)"))
    if not _val("Imp_stc", "Imp"):
        errores.append(("Imp", "Corriente en el punto de máxima potencia en STC (A)"))

    advertencias = []
    if not errores:
        if not _val("N_s", "NsA"):
            advertencias.append(("N_s", "Número de celdas en serie — se estimará desde Voc/0.65 V"))
        else:
            _hc = verificar_ns_halfcut(p)
            if _hc and _hc["tipo"] == "ns_duplicado":
                _r = _hc["rango_esperado"]
                advertencias.append((
                    "⚠️ N_s incorrecto (half-cut)",
                    f"N_s={_hc['N_s_ingresado']} da Voc/celda = {_hc['Voc_por_celda']:.3f} V "
                    f"(rango esperado {_r[0]:.2f}–{_r[1]:.2f} V). "
                    f"Valor correcto para SDM: N_s = {_hc['N_s_sugerido']}. "
                    f"Corrige `Ns (Celdas Serie)` en el Excel."
                ))
            elif _hc and _hc["tipo"] == "ns_mitad":
                _r = _hc["rango_esperado"]
                advertencias.append((
                    "⚠️ N_s incorrecto (muy bajo)",
                    f"N_s={_hc['N_s_ingresado']} da Voc/celda = {_hc['Voc_por_celda']:.3f} V "
                    f"(rango esperado {_r[0]:.2f}–{_r[1]:.2f} V). "
                    f"Valor sugerido: N_s = {_hc['N_s_sugerido']}."
                ))
        if not p.get("tecnologia"):
            advertencias.append(("Tecnología", "Tecnología del panel — se asumirá Mono-Si"))
        if not _val("Tk_beta", "CoefVoc_C", "beta_oc"):
            advertencias.append(("Coef. Temp. Voc (β)", "Se usará default por tecnología"))
        if not _val("Tk_alfa", "alpha_sc"):
            advertencias.append(("Coef. Temp. Isc (α)", "Se usará default por tecnología"))

    return errores, advertencias
