"""Vigencia del resultado de 💰 Financiero (TIR, VPN, payback, LCOE).

El resultado se guarda al pulsar «Calcular» y se vuelve a mostrar al entrar
a la página. Antes solo se descartaba si cambiaba el CAPEX: con otra tarifa
de excedentes, otra energía u otras tasas se seguía mostrando el TIR viejo
sin aviso (26-sep-2026). Ahora se comparan todos los datos del cálculo.
"""
from __future__ import annotations

import json
import math
from collections.abc import Mapping
from typing import Any

ETIQUETAS = {
    "capex_total": "CAPEX",
    "e_financiero": "energía anual",
    "tarifa_cop": "tarifa",
    "tarifa_excedentes_cop": "tarifa de excedentes",
    "frac_exportada": "fracción exportada",
    "tipo_cambio": "TRM",
    "tasa_desc": "tasa de descuento",
    "esc_tarifa": "escalación de la tarifa",
    "tasa_deg": "degradación",
    "opex_pct": "O&M",
    "esc_opex": "escalación del O&M",
    "n_anos": "años de análisis",
    "factor_p90": "factor P90",
    "config_degradacion": "modelo de degradación",
    "ben": "beneficios Ley 1715",
}


def _normalizar(valor: Any) -> Any:
    if isinstance(valor, bool) or valor is None or isinstance(valor, str):
        return valor
    if isinstance(valor, (int, float)):
        numero = float(valor)
        return round(numero, 6) if math.isfinite(numero) else str(numero)
    if isinstance(valor, Mapping):
        return {str(k): _normalizar(v) for k, v in sorted(valor.items(), key=lambda kv: str(kv[0]))}
    if isinstance(valor, (list, tuple)):
        return [_normalizar(v) for v in valor]
    try:
        return _normalizar(float(valor))
    except (TypeError, ValueError):
        return str(valor)


def datos_cambiados(anteriores: Mapping[str, Any] | None,
                    actuales: Mapping[str, Any]) -> list[str]:
    """Nombres, en palabras, de los datos que cambiaron desde el último cálculo.

    Sin datos guardados (resultado de una versión anterior) el resultado no se
    puede verificar y se considera viejo.
    """
    if not isinstance(anteriores, Mapping):
        return ["datos del cálculo anterior no disponibles"]
    cambiados = []
    for clave in list(ETIQUETAS) + sorted(set(actuales) - set(ETIQUETAS)):
        if clave not in actuales and clave not in anteriores:
            continue
        a = json.dumps(_normalizar(anteriores.get(clave)), sort_keys=True, default=str)
        b = json.dumps(_normalizar(actuales.get(clave)), sort_keys=True, default=str)
        if a != b:
            cambiados.append(ETIQUETAS.get(clave, clave))
    return cambiados
