# -*- coding: utf-8 -*-
"""🧭 Ruta del proyecto: las páginas en orden según el tipo de instalación.

Spec ``08-interfaz/ruta-proyecto`` (2-oct-2026). El orden de las páginas
(manual del Asistente, sección 119) se ve en 🏠 Proyecto como una línea de
estaciones con el estado de cada paso, leído de la sesión:

- ✅ listo: la página guardó su resultado;
- 🟠 desactualizado: cambió algo arriba (revisión de coherencia del Reporte
  o geometría del campo sin recalcular la POA);
- ▶️ siguiente: el primer paso obligatorio que falta;
- ⬜ por hacer · ⚪ opcional · 🔎 verificación (no guarda resultado).

Módulo puro: sin Streamlit.
"""
from __future__ import annotations

import html as _html
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Callable

GRANJA = "Granja fotovoltaica"


@dataclass(frozen=True)
class Paso:
    clave: str
    icono: str
    nombre: str
    pagina: str                       # ruta para st.page_link
    consejo: str
    listo: Callable[[Mapping[str, Any]], bool] | None = None   # None → verificación
    opcional: bool = False


def _tiene(valor: Any) -> bool:
    """¿La página guardó un resultado? Sin comparar con ``==``: las tablas de
    pandas no tienen un valor de verdad (ValueError en el servidor, 2-oct-2026)."""
    if valor is None or valor is False:
        return False
    if isinstance(valor, (dict, list, tuple, set, str)):
        return len(valor) > 0
    return True


def _hay(*claves: str) -> Callable[[Mapping[str, Any]], bool]:
    return lambda e: any(_tiene(e.get(k)) for k in claves)


def _poa_con_campo(e: Mapping[str, Any]) -> bool:
    from calculos.granja_fv import mismas_filas
    return e.get("poa_df") is not None and mismas_filas(e.get("poa_geometria_filas"), e.get("filas_energia"))


_P = "pages/"
PROYECTO = Paso("proyecto", "🏠", "Proyecto", _P + "1_🏠_Proyecto.py",
                "Tipo de instalación, ciudad o coordenadas, área y panel. 💾 Guardar configuración.",
                _hay("tipo_instalacion"))
SOL = Paso("sol", "☀️", "Recurso Solar", _P + "2_☀️_Recurso_Solar.py",
           "Año típico de PVGIS, inclinación y azimut; calcula la POA.", _hay("poa_df"))
SOL_1 = Paso("sol_1", "☀️", "Recurso Solar (1.ª)", _P + "2_☀️_Recurso_Solar.py",
             "Primera pasada: año típico de PVGIS y modelo bifacial. Granja FV la necesita.", _hay("tmy_df"))
SKETCHUP = Paso("sketchup", "🌳", "Sombras SketchUp", _P + "5a_🌳_Sombras_SketchUp.py",
                "Solo si hay obstáculos cercanos. Con Sky View Factor, vuelve a ☀️ Recurso Solar.",
                _hay("sk_df_fs", "factor_svf_isotropico"), opcional=True)
MOTOR_IV = Paso("motor_iv", "🔬", "Motor IV", _P + "3_🔬_Motor_IV.py",
                "Revisa «Origen del modelo» del panel, sin 🔴.", _hay("motor_iv_validacion_ok"), opcional=True)
DIM = Paso("dim", "📐", "Dimensionamiento", _P + "4_📐_Dimensionamiento.py",
           "Inversor, módulos en serie, strings por MPPT y cantidad de inversores.",
           lambda e: e.get("inversor_dict_dim") is not None and bool(e.get("N_serie")))
GRANJA_FV = Paso("granja", "🌾", "Granja FV", _P + "9b_🌾_Granja_FV.py",
                 "Filas, pitch, GCR y altura; luz al cultivo; eléctrico por bloques. "
                 "Pulsa «⚡ Usar la geometría del campo en la energía».", _hay("filas_energia"))
SOL_2 = Paso("sol_2", "☀️", "Recurso Solar (2.ª)", _P + "2_☀️_Recurso_Solar.py",
             "Segunda pasada: pulsa otra vez el cálculo; entran la sombra entre filas y la cara trasera.",
             _poa_con_campo)
VISTA_3D = Paso("vista3d", "🗺️", "Vista 3D", _P + "9_🗺️_Vista_3D.py",
                "Solo con varias superficies: publica el sistema multi-superficie (sección 108).",
                _hay("multisup_activo"), opcional=True)
OPTICO = Paso("optico", "🔆", "Motor Óptico", _P + "5b_🔆_Motor_Optico.py",
              "Montaje (k_BIPV), NOCT de la ficha y suciedad.", _hay("motor_optico_ok"))
MISMATCH = Paso("mismatch", "🔀", "Mismatch", _P + "5_🔀_Mismatch.py",
                "Calidad del módulo, mismatch de fabricación y bypass.", _hay("pct_mismatch_fab"))
UNIFILAR = Paso("unifilar", "⚡", "Unifilar", _P + "20_⚡_Diagrama_Unifilar.py",
                "Calibres y longitudes: da la pérdida real en cables. Va antes de Producción.",
                _hay("perdida_ohmica_unifilar"))
PRODUCCION = Paso("produccion", "📊", "Producción", _P + "6_📊_Produccion.py",
                  "▶️ Simular producción. Guarda la firma del diseño.", _hay("res_produccion"))
BATERIAS = Paso("baterias", "🔋", "Baterías", _P + "11_🔋_Baterias_y_Balance.py",
                "Solo si el proyecto lleva almacenamiento.", _hay("balance_ok", "bateria_ok"), opcional=True)
RETIE = Paso("retie", "📋", "Ficha RETIE", _P + "21_📋_Ficha_Validacion_RETIE.py",
             "Verificación: todo en 🟢.")
PRESUPUESTO = Paso("presupuesto", "💼", "Presupuesto", _P + "8_💼_Presupuesto.py",
                   "CAPEX, costos blandos y OPEX. Va antes de Financiero.", _hay("presupuesto_capex_usd"))
FINANCIERO = Paso("financiero", "💰", "Financiero", _P + "7_💰_Financiero.py",
                  "Flujo de caja, TIR y LCOE con la energía de Producción.", _hay("financiero_ok"))
CO2 = Paso("co2", "🌿", "Impacto CO₂", _P + "12_🌿_Impacto_CO2.py",
           "CO₂ evitado con la energía de Producción.", _hay("co2_anual_t"))
REPORTE = Paso("reporte", "📄", "Reporte", _P + "10_📄_Reporte_PDF.py",
               "Etapa del documento y revisión de coherencia sin 🔴.", _hay("reporte_generado"))

RUTA_BIPV = (PROYECTO, SOL, SKETCHUP, MOTOR_IV, DIM, VISTA_3D, OPTICO, MISMATCH, UNIFILAR, PRODUCCION,
             BATERIAS, RETIE, PRESUPUESTO, FINANCIERO, CO2, REPORTE)
RUTA_GRANJA = (PROYECTO, SOL_1, MOTOR_IV, DIM, GRANJA_FV, SOL_2, OPTICO, MISMATCH, UNIFILAR, PRODUCCION,
               RETIE, PRESUPUESTO, FINANCIERO, CO2, REPORTE)

# Revisión de coherencia del Reporte → paso que quedó viejo.
_DESACTUALIZA = (("inversores", "produccion"), ("diseño cambió", "produccion"), ("cables", "produccion"),
                 ("Impacto CO₂", "co2"), ("Financiero", "financiero"))


def ruta_de(tipo: str | None) -> tuple[Paso, ...]:
    return RUTA_GRANJA if tipo == GRANJA else RUTA_BIPV


def _desactualizados(estado: Mapping[str, Any]) -> dict[str, str]:
    from calculos.coherencia_reporte import revisar_coherencia_reporte
    out: dict[str, str] = {}
    for p in revisar_coherencia_reporte(estado):
        if p["nivel"] != "error":
            continue
        for texto, clave in _DESACTUALIZA:
            if texto in p["titulo"] and clave not in out:
                out[clave] = p["titulo"]
    if estado.get("filas_energia") and not _poa_con_campo(estado) and estado.get("poa_df") is not None:
        out["sol_2"] = "Cambiaste la geometría del campo: vuelve a calcular la POA"
    return out


def estado_ruta(tipo: str | None, estado: Mapping[str, Any]) -> list[dict]:
    """Pasos de la ruta con ``estado`` ∈ listo / desactualizado / siguiente /
    por_hacer / opcional / verificacion y el motivo si quedó viejo."""
    viejos = _desactualizados(estado)
    pasos = []
    for p in ruta_de(tipo):
        if p.listo is None:
            st_p = "verificacion"
        elif p.clave in viejos:
            st_p = "desactualizado"
        elif p.listo(estado):
            st_p = "listo"
        else:
            st_p = "opcional" if p.opcional else "por_hacer"
        pasos.append({"clave": p.clave, "icono": p.icono, "nombre": p.nombre, "pagina": p.pagina,
                      "consejo": p.consejo, "opcional": p.opcional, "estado": st_p,
                      "motivo": viejos.get(p.clave, "")})
    # Aguas abajo: lo que ya estaba listo después de un paso viejo también lo está.
    viejo = next((x for x in pasos if x["estado"] == "desactualizado"), None)
    if viejo:
        for x in pasos[pasos.index(viejo) + 1:]:
            if x["estado"] == "listo":
                x["estado"] = "desactualizado"
                x["motivo"] = x["motivo"] or f"Depende de {viejo['icono']} {viejo['nombre']}, que quedó desactualizado"
    # Siguiente: el primer paso, en orden, desactualizado u obligatorio por hacer
    # (si faltan los cables va ⚡ Unifilar antes de volver a 📊 Producción).
    sig = next((x for x in pasos if x["estado"] in ("desactualizado", "por_hacer")), None)
    if sig and sig["estado"] == "por_hacer":
        sig["estado"] = "siguiente"
    return pasos


def siguiente(pasos: list[dict]) -> dict | None:
    return next((x for x in pasos if x["estado"] in ("desactualizado", "siguiente")), None)


SIMBOLO = {"listo": "✅", "desactualizado": "🟠", "siguiente": "▶️", "por_hacer": "⬜",
           "opcional": "⚪", "verificacion": "🔎"}
_COLOR = {"listo": "#16835d", "desactualizado": "#d35400", "siguiente": "#1a569a", "por_hacer": "#888",
          "opcional": "#aaa", "verificacion": "#888"}


def html_ruta(pasos: list[dict]) -> str:
    """Línea de estaciones (se acomoda en varias filas en pantallas angostas)."""
    celdas = []
    for i, x in enumerate(pasos):
        color = _COLOR[x["estado"]]
        borde = "3px solid" if x["estado"] in ("siguiente", "desactualizado") else "1px solid"
        titulo = _html.escape(x["consejo"] + (f" — {x['motivo']}" if x["motivo"] else ""), quote=True)
        celdas.append(
            f'<div class="ruta-paso" title="{titulo}" style="display:flex;flex-direction:column;'
            f'align-items:center;min-width:64px;max-width:80px;text-align:center;">'
            f'<div style="font-size:1.05em;">{SIMBOLO[x["estado"]]}</div>'
            f'<div style="border:{borde} {color};border-radius:50%;width:34px;height:34px;display:flex;'
            f'align-items:center;justify-content:center;font-size:1.1em;">{x["icono"]}</div>'
            f'<div style="font-size:0.72em;color:{color};line-height:1.1;margin-top:2px;">'
            f'{i + 1}. {_html.escape(x["nombre"])}</div></div>')
    flecha = '<div style="color:#bbb;align-self:center;margin-top:10px;">──</div>'
    return ('<div class="ruta-proyecto" style="display:flex;flex-wrap:wrap;gap:4px 2px;'
            'align-items:flex-start;">' + flecha.join(celdas) + '</div>')


def resumen(pasos: list[dict]) -> str:
    obligatorios = [x for x in pasos if not x["opcional"] and x["estado"] != "verificacion"]
    listos = sum(1 for x in obligatorios if x["estado"] == "listo")
    return f"{listos} de {len(obligatorios)} pasos listos"
