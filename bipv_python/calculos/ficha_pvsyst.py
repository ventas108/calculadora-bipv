"""
Ficha de conversión app → PVsyst (módulo custom + ajuste térmico Uc/Uv).

Contexto: el catálogo de PVsyst 8.1.5 no trae paneles BIPV vidrio-vidrio
(solo silicio cristalino o amorfo "de catálogo"), así que la comparación
manzanas-con-manzanas exige crear un módulo custom en PVsyst
("PV module" → "New") con los mismos parámetros de datasheet que ya tiene
esta app, y ajustar el modelo térmico ("Détails du système" → pérdidas
térmicas, Uc/Uv) al mismo supuesto de montaje que usa `k_BIPV` aquí.

Esta ficha genera ambos bloques en texto plano, en el orden y unidades que
pide el diálogo de PVsyst, para evitar error de transcripción manual y dejar
la comparación documentada/auditable.

Ver DIAGNOSTICO_MODELO_TERMICO_UC_UV.md para la tabla de equivalencia
k_BIPV ↔ Uc/Uv y sus límites (nuestro modelo es un multiplicador NOCT de un
solo parámetro; el de PVsyst es un balance térmico de dos parámetros con
dependencia real del viento — la equivalencia es aproximada, no exacta).
"""
from __future__ import annotations

# k_BIPV (factor de confinamiento, ver calculos/temperatura.py y
# calculos/motor_optico.py) → preset más cercano de PVsyst y su Uc/Uv típico.
# Uv=0 en los tres casos: PVsyst permite ajustarlo si se tiene velocidad de
# viento de sitio, pero el preset base que se compara aquí es Uc solamente.
EQUIVALENCIA_K_BIPV_UC_UV = {
    1.0: {
        "preset_pvsyst": "Free standing (montaje libre)",
        "Uc_W_m2K": 29.0,
        "Uv_W_m2K_por_ms": 0.0,
    },
    1.3: {
        "preset_pvsyst": "Semi-integrated (semi-integrado)",
        "Uc_W_m2K": 20.0,
        "Uv_W_m2K_por_ms": 0.0,
    },
    1.5: {
        "preset_pvsyst": "Integrated (integración total, sin ventilación)",
        "Uc_W_m2K": 15.0,
        "Uv_W_m2K_por_ms": 0.0,
    },
}


def _equivalencia_mas_cercana(k_bipv: float) -> tuple[float, dict]:
    k = min(EQUIVALENCIA_K_BIPV_UC_UV, key=lambda kk: abs(kk - k_bipv))
    return k, EQUIVALENCIA_K_BIPV_UC_UV[k]


def generar_ficha_conversion_pvsyst(
    panel: dict,
    tipo_instalacion: str,
    k_bipv: float,
) -> str:
    """
    Genera la ficha de conversión (texto plano) para un panel del catálogo.

    Parameters
    ----------
    panel : dict con la estructura de datos/catalogo_paneles_excel.py
            (Voc_stc, Vmp_stc, Isc_stc, Imp, Pmax_stc, NOCT, Tk_beta,
             Tk_gamma, tecnologia, marca, nombre, area_m2).
    tipo_instalacion : uno de los 6 tipos de pages/1_🏠_Proyecto.py
                        (solo informativo en la ficha).
    k_bipv : factor de confinamiento térmico elegido en 🔆 Motor Óptico.
    """
    nombre = panel.get("nombre", "—")
    marca = panel.get("marca", "—")
    tecnologia = panel.get("tecnologia", "—") or "—"

    Pmax = panel.get("Pmax_stc")
    Voc = panel.get("Voc_stc")
    Vmp = panel.get("Vmp_stc")
    Isc = panel.get("Isc_stc")
    Imp = panel.get("Imp")
    NOCT = panel.get("NOCT")
    Tk_beta = panel.get("Tk_beta")    # coef. temp. Voc (%/°C)
    Tk_gamma = panel.get("Tk_gamma")  # coef. temp. Pmax (%/°C)
    area = panel.get("area_m2")

    k_cercano, eq = _equivalencia_mas_cercana(k_bipv)
    nota_k = "" if abs(k_cercano - k_bipv) < 1e-9 else (
        f" (k_BIPV={k_bipv:.2f} no es uno de los 3 presets estándar — "
        f"se usó el más cercano, k={k_cercano:.1f}, para la equivalencia)"
    )

    lineas = [
        f"FICHA DE CONVERSIÓN A PVsyst — {nombre}",
        "=" * (26 + len(nombre)),
        "",
        "── 1. Módulo custom en PVsyst (\"PV module\" → \"New\") ──",
        f"  Fabricante / modelo   : {marca} / {nombre}",
        f"  Tecnología            : {tecnologia}  "
        f"(clasificar en PVsyst como 'Si-mono' si es célula c-Si, "
        f"aunque el laminado sea vidrio-vidrio BIPV)",
        f"  Pnom (STC)            : {_fmt(Pmax, 'W')}",
        f"  Vmp (STC)             : {_fmt(Vmp, 'V')}",
        f"  Imp (STC)             : {_fmt(Imp, 'A')}",
        f"  Voc (STC)             : {_fmt(Voc, 'V')}",
        f"  Isc (STC)             : {_fmt(Isc, 'A')}",
        f"  Área del módulo       : {_fmt(area, 'm²')}",
        "",
        "── 2. Coeficientes de temperatura ──",
        f"  μVoc                  : {_fmt(Tk_beta, '%/°C')}",
        f"  μPmax (γ)             : {_fmt(Tk_gamma, '%/°C')}",
        "  μIsc                  : NO disponible en el catálogo de esta app "
        "— pedir al fabricante o usar default típico c-Si (~+0.04 %/°C). "
        "No lo completes con un valor inventado sin marcarlo como supuesto.",
        f"  NOCT/NMOT             : {_fmt(NOCT, '°C')}",
        "",
        "── 3. Ajuste térmico de montaje (Uc/Uv) ──",
        f"  Tipo de instalación   : {tipo_instalacion}",
        f"  k_BIPV usado en la app: {k_bipv:.2f}{nota_k}",
        f"  Preset PVsyst sugerido: {eq['preset_pvsyst']}",
        f"  Uc (constante)        : {eq['Uc_W_m2K']:.1f} W/m²K",
        f"  Uv (dependiente viento): {eq['Uv_W_m2K_por_ms']:.1f} W/m²K por m/s",
        "  Ruta en PVsyst: \"Détails du système\" → pestaña de pérdidas "
        "térmicas → introducir Uc/Uv manualmente (no dejar el default de "
        "montaje libre si el proyecto es una fachada/techo confinado).",
        "",
        "⚠️ Esta equivalencia es aproximada: el modelo de esta app (NOCT × "
        "k_BIPV) es un multiplicador de un solo parámetro; el de PVsyst "
        "(Faiman, Uc+Uv·viento) es un balance térmico de dos parámetros con "
        "dependencia real de la velocidad del viento del sitio. Útil para "
        "partir de un supuesto físico coherente entre ambas herramientas, "
        "no como igualdad numérica exacta. Ver DIAGNOSTICO_MODELO_TERMICO_UC_UV.md.",
    ]
    return "\n".join(lineas)


def _fmt(valor, unidad: str) -> str:
    if valor is None:
        return "— (no disponible en el catálogo)"
    return f"{valor:g} {unidad}"
