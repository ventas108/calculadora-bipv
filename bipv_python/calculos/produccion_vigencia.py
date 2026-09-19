# -*- coding: utf-8 -*-
"""
Vigencia de Producción — Fase 1 (.openspec/proposals/produccion-codespec).

Implementa el contrato exacto de `produccion_run_signature_v1` y
`bypass_run_signature_v1` descrito en design.md/spec.yaml de ese CodeSpec:
una huella determinista SHA-256 de la corrida base (respectivamente, del
bypass monofacial), construida sobre una representación canónica que no
depende del orden de inserción del dict, del tipo numérico exacto (int vs.
numpy.int64) ni del proceso donde se calcula.

Uso previsto:
  - pages/6_📊_Produccion.py llama calcular_produccion_run_signature_v1() al
    terminar una corrida y la guarda en res_produccion/session_state; antes
    de reutilizar un res_produccion existente (produccion_ok=True sin volver
    a pulsar "Simular"), la recalcula con la configuración VISIBLE actual y
    la compara -- si no coincide, invalida en vez de republicar.
  - pages/5_🔀_Mismatch.py llama calcular_bypass_run_signature_v1() justo
    tras simular_bypass_horario() y la guarda junto a bypass_result.
    pages/6_📊_Produccion.py la reconstruye desde SU configuración vigente
    para decidir si el bypass sigue siendo consumible.
  - calculos/persistencia_resultados.py exige coincidencia exacta de
    produccion_run_signature_v1 antes de restaurar agregados persistidos.

Ninguna función de este módulo escribe en session_state ni conoce Streamlit
-- es intencionalmente pura para poder probarla sin la app completa.
"""
from __future__ import annotations

import hashlib
import json
import math

import numpy as np
import pandas as pd

SOURCE_MODES_VALIDOS = ("jrc_huld", "sdm_pvsyst", "motor_iv", "lineal")
POA_SOURCES_VALIDAS = ("poa_df", "poa_sin_termico_df")


# ══════════════════════════════════════════════════════════════════════════
# 1. Normalización canónica y serialización
# ══════════════════════════════════════════════════════════════════════════

def _normalizar_valor(valor):
    """
    Normaliza recursivamente un valor para que su representación JSON sea
    determinista entre procesos y no dependa del tipo numérico exacto:

    - None / bool → sin cambios (bool se revisa ANTES que int: en Python
      `isinstance(True, int)` es True).
    - int / numpy.integer → int nativo.
    - float / numpy.floating → `float.hex()` de un valor FINITO -- evita que
      la representación decimal de json.dumps difiera entre plataformas
      (p.ej. 0.1 vs 0.10000000000000001) y hace explícito el rechazo de
      NaN/infinito exigido por el CodeSpec.
    - str → sin cambios.
    - dict → nuevo dict con claves forzadas a `str` y ordenadas como
      cadenas, valores normalizados recursivamente (además de sort_keys=True
      en la serialización -- doble seguro, no hay ambigüedad de orden).
    - list / tuple → lista con cada elemento normalizado, mismo orden.
    - cualquier otro tipo → TypeError (tipo no soportado en la firma).
    """
    if valor is None:
        return None
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, np.integer)):
        return int(valor)
    if isinstance(valor, (float, np.floating)):
        v = float(valor)
        if not math.isfinite(v):
            raise ValueError(f"Valor no finito no permitido en la firma: {v!r}")
        return float.hex(v)
    if isinstance(valor, str):
        return valor
    if isinstance(valor, dict):
        return {
            str(k): _normalizar_valor(v)
            for k, v in sorted(valor.items(), key=lambda kv: str(kv[0]))
        }
    if isinstance(valor, (list, tuple)):
        return [_normalizar_valor(v) for v in valor]
    raise TypeError(f"Tipo no soportado en la firma: {type(valor).__name__}")


def _serializar_canonico(payload: dict) -> bytes:
    """JSON UTF-8 canónico: claves ordenadas, separadores compactos, ASCII."""
    normalizado = _normalizar_valor(payload)
    return json.dumps(
        normalizado, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fingerprint_mapping(mapping: dict | None) -> str | None:
    """
    SHA-256 hex de la representación canónica de `mapping` (p.ej. el dict
    completo de un panel o un inversor). `None` retorna `None` -- un mapping
    ausente no es lo mismo que un mapping vacío `{}` (que sí fingerprintea).
    """
    if mapping is None:
        return None
    if not isinstance(mapping, dict):
        raise TypeError("fingerprint_mapping() espera un dict o None.")
    return _sha256_hex(_serializar_canonico(mapping))


# ══════════════════════════════════════════════════════════════════════════
# 2. Huellas horarias
# ══════════════════════════════════════════════════════════════════════════

def huella_horaria(index: pd.DatetimeIndex, values) -> str:
    """
    SHA-256 de una serie horaria: zona horaria (UTF-8, cadena vacía si el
    índice es naive) + índice convertido a UTC cuando tiene zona, como
    enteros int64 nanosegundos little-endian + valores contiguos float64
    little-endian. Valores no finitos y longitudes desiguales se rechazan
    antes de firmar; un índice con timestamps duplicados es ambiguo (no
    identifica una hora única) y también se rechaza.
    """
    if not isinstance(index, pd.DatetimeIndex):
        raise TypeError("huella_horaria() espera un pandas.DatetimeIndex.")
    if index.has_duplicates:
        raise ValueError(
            "Índice ambiguo (timestamps duplicados); no se puede firmar de "
            "forma determinista."
        )
    valores = np.asarray(values, dtype=np.float64)
    if valores.ndim != 1 or len(valores) != len(index):
        raise ValueError(
            "El índice y los valores deben tener la misma longitud (1D) "
            "para firmar una serie horaria."
        )
    if not np.all(np.isfinite(valores)):
        raise ValueError(
            "Serie horaria con valores no finitos (NaN/inf); no se puede "
            "firmar."
        )

    tz = index.tz
    tz_bytes = (str(tz) if tz is not None else "").encode("utf-8")
    idx_utc = index.tz_convert("UTC") if tz is not None else index
    idx_ns_le = idx_utc.astype("int64").to_numpy().astype("<i8")
    valores_le = valores.astype("<f8")

    hasher = hashlib.sha256()
    hasher.update(tz_bytes)
    hasher.update(idx_ns_le.tobytes())
    hasher.update(valores_le.tobytes())
    return hasher.hexdigest()


def huella_horaria_opcional(index: pd.DatetimeIndex, values) -> str | None:
    """Como huella_horaria(), pero retorna None si `values` es None."""
    if values is None:
        return None
    return huella_horaria(index, values)


def _validar_enum(valor: str, permitidos: tuple[str, ...], nombre_campo: str) -> str:
    if valor not in permitidos:
        raise ValueError(
            f"{nombre_campo}={valor!r} no es válido; debe ser uno de {permitidos}."
        )
    return valor


def _int_o_none(v) -> int | None:
    return int(v) if v is not None else None


def _float_o_none(v) -> float | None:
    return float(v) if v is not None else None


# ══════════════════════════════════════════════════════════════════════════
# 3. produccion_run_signature_v1
# ══════════════════════════════════════════════════════════════════════════

def calcular_produccion_run_signature_v1(
    *,
    panel: dict,
    panel_nombre: str,
    inversor: dict,
    inversor_nombre: str,
    N_paneles: int | None,
    N_serie: int | None,
    N_strings_tracker: int | None,
    n_inversores: int | None,
    P_dc_stc_kW: float | None,
    eta_inversor: float | None,
    P_ac_nom_W_total: float | None,
    NOCT: float | None,
    k_bipv: float | None,
    produccion_usar_iv: bool,
    source_mode: str,
    tmy_index: pd.DatetimeIndex,
    tmy_T2m,
    poa_source: str,
    poa_index: pd.DatetimeIndex,
    poa_global,
    factor_mismatch_aplicado: float,
    factor_espectral=None,
    pct_mismatch_fab: float | None = None,
    pct_cableado_dc: float | None = None,
    pct_cableado_ac: float | None = None,
    perdida_ohmica_unifilar: dict | None = None,
) -> str:
    """
    Huella determinista de la corrida BASE de Producción (sin bypass ni
    multi-superficie, que tienen ciclos de vida downstream separados). Ver
    .openspec/proposals/produccion-codespec/design.md § "Contrato propuesto
    de entrada" para la justificación de cada campo.

    panel/inversor: el mapping completo tal como se usó en la simulación
      (p.ej. el panel YA con el NOCT de Motor Óptico inyectado, si aplica --
      la firma debe capturar los parámetros EFECTIVOS, no los nominales).
    source_mode: uno de SOURCE_MODES_VALIDOS.
    poa_source: uno de POA_SOURCES_VALIDAS.
    tmy_T2m / poa_global: arrays 1D alineados a tmy_index / poa_index
      respectivamente.
    factor_espectral: array 1D alineado a tmy_index, o None si no se aplicó.

    Retorna el digest SHA-256 hex (64 caracteres) — este es literalmente el
    valor de `produccion_run_signature_v1`.
    """
    payload = {
        "signature_version": 1,
        "panel_fingerprint": fingerprint_mapping(panel),
        "panel_nombre": str(panel_nombre),
        "inverter_fingerprint": fingerprint_mapping(inversor),
        "inversor_nombre": str(inversor_nombre),
        "N_paneles": _int_o_none(N_paneles),
        "N_serie": _int_o_none(N_serie),
        "N_strings_tracker": _int_o_none(N_strings_tracker),
        "n_inversores": _int_o_none(n_inversores),
        "P_dc_stc_kW": _float_o_none(P_dc_stc_kW),
        "eta_inversor": _float_o_none(eta_inversor),
        "P_ac_nom_W_total": _float_o_none(P_ac_nom_W_total),
        "produccion_usar_iv": bool(produccion_usar_iv),
        "source_mode": _validar_enum(source_mode, SOURCE_MODES_VALIDOS, "source_mode"),
        "tmy_T2m_fingerprint": huella_horaria(tmy_index, tmy_T2m),
        "poa_source": _validar_enum(poa_source, POA_SOURCES_VALIDAS, "poa_source"),
        "poa_global_fingerprint": huella_horaria(poa_index, poa_global),
        "factor_mismatch_aplicado": float(factor_mismatch_aplicado),
        "NOCT": _float_o_none(NOCT),
        "k_bipv": _float_o_none(k_bipv),
        "factor_espectral_fingerprint": huella_horaria_opcional(tmy_index, factor_espectral),
        "pct_mismatch_fab": _float_o_none(pct_mismatch_fab),
        "pct_cableado_dc": _float_o_none(pct_cableado_dc),
        "pct_cableado_ac": _float_o_none(pct_cableado_ac),
        "perdida_ohmica_fingerprint": fingerprint_mapping(perdida_ohmica_unifilar),
    }
    return _sha256_hex(_serializar_canonico(payload))


# ══════════════════════════════════════════════════════════════════════════
# 4. bypass_run_signature_v1
# ══════════════════════════════════════════════════════════════════════════

def calcular_bypass_run_signature_v1(
    *,
    panel: dict,
    N_series: int | None,
    N_parallel: int | None,
    total_modules: int | None,
    tmy_index: pd.DatetimeIndex,
    G_eff,
    T_amb,
    p_shade_final,
    NOCT: float | None,
    k_bipv: float | None,
    umbral_shade: float | None,
) -> str:
    """
    Huella determinista de los argumentos EFECTIVOS de
    calculos.mismatch_bypass.simular_bypass_horario(): panel completo,
    topología del string, y las tres series horarias que determinan el
    resultado físico (G_eff, T_amb, p_shade final -- este último ya
    incorpora fachada, inversión de FS, modo/agregación de alineación y
    horizonte combinado, sin necesidad de firmar cada metadato causal por
    separado).

    Excluye explícitamente produccion_run_signature_v1 y cualquier estado
    multi-superficie (ver spec.yaml bypass_signature.excludes) -- bypass
    monofacial y multi-superficie tienen ciclos de vida independientes.

    G_eff es la POA óptica sin térmico que usa Página 5 (poa_sin_termico_df
    cuando Motor Óptico está activo); NUNCA debe mezclarse con
    factor_mismatch_sin_soiling -- ese factor pertenece a la corrida BASE de
    Producción, no a esta firma (por eso esta función no acepta ningún
    parámetro de mismatch).
    """
    payload = {
        "panel_fingerprint": fingerprint_mapping(panel),
        "N_series": _int_o_none(N_series),
        "N_parallel": _int_o_none(N_parallel),
        "total_modules": _int_o_none(total_modules),
        "g_eff_hourly_fingerprint": huella_horaria(tmy_index, G_eff),
        "t_amb_hourly_fingerprint": huella_horaria(tmy_index, T_amb),
        "p_shade_final_hourly_fingerprint": huella_horaria(tmy_index, p_shade_final),
        "NOCT": _float_o_none(NOCT),
        "k_bipv": _float_o_none(k_bipv),
        "umbral_shade": _float_o_none(umbral_shade),
    }
    return _sha256_hex(_serializar_canonico(payload))
