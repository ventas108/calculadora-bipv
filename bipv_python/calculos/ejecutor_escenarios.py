"""Ejecutor reproducible de los escenarios de comparación (Fase 4).

Toma una base congelada (``bipv.comparison-base.v1``) y una definición de
escenarios (``bipv.scenarios.v1``) y calcula ``E_AC_anual_kWh`` para
referencia, situación actual y alternativa optimizada con exactamente el
mismo método eléctrico, cambiando únicamente la serie ``p_shade``.

Reglas:
- La base congelada es autoridad: si el estado actual difiere de la base,
  la ejecución falla en vez de simular con supuestos mezclados.
- Solo ``FS_geometrico`` alimenta el modelo de bypass (0 = sin sombra,
  1 = sombra total). Nunca se mezcla con FS climático.
- No se inventan defaults: entradas faltantes producen errores explícitos
  o estados "pendiente", jamás valores silenciosos.
- Mismo ``base_id`` + mismas entradas ⇒ mismos resultados (determinismo).
"""
from __future__ import annotations

import hashlib
from typing import Any
from collections.abc import Mapping

import numpy as np
import pandas as pd

from calculos.escenarios_fase4 import (
    _huella,
    comparar_bases,
    validar_base_comparacion,
    validar_definicion_escenarios,
)
from calculos.mismatch_bypass import (
    alinear_fs_con_tmy,
    combinar_fs_con_horizonte,
    simular_bypass_horario,
)

RESULTADOS_SCHEMA_VERSION = "bipv.scenario-results.v1"
_HORAS_ANIO = 8760


def _huella_serie(valores: np.ndarray) -> str:
    """Huella SHA-256 de una serie numérica (float64, byte a byte)."""
    return hashlib.sha256(
        np.ascontiguousarray(valores, dtype=np.float64).tobytes()
    ).hexdigest()


def _validar_horaria(nombre: str, valores: np.ndarray) -> np.ndarray:
    arr = np.asarray(valores, dtype=float)
    if arr.ndim != 1 or arr.shape[0] != _HORAS_ANIO:
        raise ValueError(
            f"{nombre} debe ser una serie horaria de {_HORAS_ANIO} valores; "
            f"se recibieron {arr.shape}."
        )
    if not np.isfinite(arr).all():
        raise ValueError(
            f"{nombre} contiene NaN o infinitos; corrige la fuente antes de simular."
        )
    return arr


def _validar_p_shade(nombre: str, valores: np.ndarray) -> np.ndarray:
    arr = _validar_horaria(nombre, valores)
    if (arr < 0.0).any() or (arr > 1.0).any():
        raise ValueError(
            f"{nombre} tiene valores fuera de [0, 1]; FS_geometrico debe ser "
            "0 = sin sombra … 1 = sombra total."
        )
    return arr


def _verificar_contra_base(
    base: Mapping[str, Any],
    *,
    panel: Mapping[str, Any],
    n_serie: int,
    n_paralelo: int,
    eta_inversor: float,
) -> None:
    """Rechaza entradas eléctricas que difieran de la base congelada."""
    componentes = base["componentes"]
    valor_panel = componentes["panel"]["valor"]
    ficha_congelada = valor_panel.get("ficha")
    # La ficha congelada (panel_dict de Dimensionamiento) y el panel del
    # bloque bypass (catálogo MODULOS_BIPV) son representaciones distintas
    # del MISMO módulo: comparar huellas de diccionario completo daba falso
    # negativo. La identidad real es el nombre del modelo; además se exige
    # coherencia en los campos numéricos que ambas fichas compartan.
    nombre_congelado = str(
        valor_panel.get("nombre")
        or (ficha_congelada or {}).get("nombre")
        or ""
    ).strip().lower()
    nombre_entregado = str(
        dict(panel).get("nombre") or dict(panel).get("modelo") or ""
    ).strip().lower()
    if not nombre_congelado:
        raise ValueError(
            "La base congelada no registra el nombre del panel; recongela la base."
        )
    if nombre_entregado and nombre_entregado != nombre_congelado:
        raise ValueError(
            f"El panel entregado ({nombre_entregado!r}) no coincide con el "
            f"congelado en la base ({nombre_congelado!r})."
        )
    # Nota: NO se comparan los campos numéricos entre fichas — la ficha de
    # Dimensionamiento trae valores de datasheet (Excel) y la del bypass usa
    # parámetros calibrados (tecnologias_bipv); difieren a propósito para el
    # mismo módulo. La huella de la ficha congelada ya viaja en base_id.
    cfg = componentes["configuracion_electrica"]["valor"]["configuracion"]
    # n_paralelo se valida contra N_paneles/N_serie (strings totales de la
    # planta); N_strings_tracker es otra magnitud (strings por combinadora).
    n_paralelo_esperado = None
    if cfg.get("N_paneles") and cfg.get("N_serie"):
        n_paralelo_esperado = int(round(int(cfg["N_paneles"]) / int(cfg["N_serie"])))
    checks = (
        ("N_serie", int(n_serie), cfg.get("N_serie")),
        ("N_paralelo (N_paneles/N_serie)", int(n_paralelo), n_paralelo_esperado),
        ("eta_inversor", float(eta_inversor), cfg.get("eta_inversor")),
    )
    for nombre, entregado, congelado in checks:
        if congelado is None or _huella(entregado) != _huella(
            type(entregado)(congelado)
        ):
            raise ValueError(
                f"{nombre} entregado ({entregado!r}) no coincide con la base "
                f"congelada ({congelado!r}); no se simulan supuestos mezclados."
            )


def _simular_escenario(
    *,
    poa_global: np.ndarray,
    t_amb: np.ndarray,
    p_shade: np.ndarray,
    n_serie: int,
    n_paralelo: int,
    panel: Mapping[str, Any],
    eta_inversor: float,
    base_id: str,
    fuente_p_shade: str,
) -> dict[str, Any]:
    if "NOCT" not in panel:
        raise ValueError(
            "El panel no declara NOCT; no se usan defaults silenciosos."
        )
    res = simular_bypass_horario(
        G_eff=poa_global,
        T_amb=t_amb,
        p_shade=p_shade,
        N_series=int(n_serie),
        N_parallel=int(n_paralelo),
        panel=dict(panel),
        NOCT=float(panel["NOCT"]),
        umbral_shade=0.05,
    )
    e_dc_kwh = float(np.sum(np.asarray(res["P_dc_kW"], dtype=float)))
    e_ac_kwh = e_dc_kwh * float(eta_inversor)
    return {
        "estado": "calculado",
        "E_AC_anual_kWh": round(e_ac_kwh, 1),
        "E_DC_anual_kWh": round(e_dc_kwh, 1),
        "kwh_bypass_anual": res["kwh_bypass_anual"],
        "horas_bypass": res["horas_bypass"],
        "horas_sombra": res["horas_sombra"],
        "metodo": "bypass_horario_sdm + eta_inversor",
        "base_id": base_id,
        "fuente_p_shade": fuente_p_shade,
        "p_shade_huella": _huella_serie(p_shade),
    }


def ejecutar_escenarios(
    *,
    definicion: dict[str, Any],
    base_estado_actual: dict[str, Any],
    tmy: pd.DataFrame,
    poa_global: np.ndarray | pd.Series,
    panel: Mapping[str, Any],
    n_serie: int,
    n_paralelo: int,
    eta_inversor: float,
    df_fs_actual: pd.DataFrame,
    df_fs_optimizada: pd.DataFrame | None = None,
    modo_alineacion: str = "mensual",
    modo_agregacion: str = "auto",
    mascara_horizonte: pd.Series | None = None,
) -> dict[str, Any]:
    """Ejecuta los tres escenarios sobre la base congelada de ``definicion``.

    Parámetros
    ----------
    definicion          : contrato ``bipv.scenarios.v1`` con ``base_comparacion``.
    base_estado_actual  : base recapturada del estado vivo; debe coincidir con
                          la base congelada (mismo ``base_id``) o se aborta.
    tmy                 : DataFrame TMY 8760 con columna ``T2m``.
    poa_global          : irradiancia POA efectiva W/m² (8760).
    panel               : ficha del panel (parámetros SDM + NOCT).
    n_serie, n_paralelo : configuración eléctrica del array.
    eta_inversor        : eficiencia del inversor (0 < η ≤ 1).
    df_fs_actual        : DataFrame FS geométrico de la situación actual
                          (columnas mes/dia/hora/FS_geometrico).
    df_fs_optimizada    : FS de la alternativa optimizada; si es None el
                          escenario queda explícitamente pendiente.

    Retorna un dict ``resultados`` (no muta ``definicion``):
    ``{"schema_version", "base_id", "parametros", "referencia", "actual",
    "optimizada"}``.
    """
    validar_definicion_escenarios(definicion)
    base = definicion.get("base_comparacion")
    if not isinstance(base, dict):
        raise ValueError("La definición no contiene una base de comparación congelada.")
    validar_base_comparacion(base)
    comparar_bases(base, base_estado_actual)
    _verificar_contra_base(
        base,
        panel=panel,
        n_serie=n_serie,
        n_paralelo=n_paralelo,
        eta_inversor=eta_inversor,
    )
    base_id = base["base_id"]

    if not isinstance(tmy, pd.DataFrame) or "T2m" not in tmy.columns:
        raise ValueError("El TMY debe ser un DataFrame con columna T2m.")
    if not isinstance(df_fs_actual, pd.DataFrame) or df_fs_actual.empty:
        raise ValueError(
            "La situación actual requiere un DataFrame FS_geometrico no vacío."
        )
    for etiqueta, df_fs in (
        ("actual", df_fs_actual),
        ("optimizada", df_fs_optimizada),
    ):
        if isinstance(df_fs, pd.DataFrame) and "FS_geometrico" in df_fs.columns:
            fs_vals = pd.to_numeric(df_fs["FS_geometrico"], errors="coerce")
            if fs_vals.isna().any() or (fs_vals < 0.0).any() or (fs_vals > 1.0).any():
                raise ValueError(
                    f"FS_geometrico ({etiqueta}) tiene valores fuera de [0, 1] "
                    "o no numéricos; la agregación los recortaría en silencio."
                )
    eta = float(eta_inversor)
    if not 0.0 < eta <= 1.0:
        raise ValueError(f"eta_inversor fuera de rango (0, 1]: {eta_inversor!r}")
    if int(n_serie) < 1 or int(n_paralelo) < 1:
        raise ValueError("N_serie y N_paralelo deben ser enteros >= 1.")
    if modo_alineacion not in {"mensual", "exacto"}:
        raise ValueError(f"Modo de alineación no soportado: {modo_alineacion!r}")

    poa = _validar_horaria("POA global", poa_global)
    t_amb = _validar_horaria("T2m", tmy["T2m"].to_numpy(dtype=float))
    if len(tmy.index) != _HORAS_ANIO:
        raise ValueError("El TMY debe tener exactamente 8760 registros horarios.")

    comunes = dict(
        poa_global=poa,
        t_amb=t_amb,
        n_serie=int(n_serie),
        n_paralelo=int(n_paralelo),
        panel=panel,
        eta_inversor=eta,
        base_id=base_id,
    )

    # Referencia: se elimina únicamente la sombra geométrica (FS = 0).
    p_shade_ref = np.zeros(_HORAS_ANIO, dtype=float)
    referencia = _simular_escenario(
        p_shade=p_shade_ref, fuente_p_shade="fs_geometrico_cero", **comunes
    )

    # Situación actual: FS geométrico reconciliado de la fuente declarada.
    # Si la definición declara 'horizonte' como fuente, la máscara es
    # OBLIGATORIA: nunca se simula "actual" fingiendo que el horizonte no
    # existe (#232). Si llega máscara sin declararla, también se aborta —
    # supuestos mezclados.
    fuentes_actual = (definicion.get("politica_fuentes_actual") or {}).get(
        "fuentes_declaradas", []
    )
    horizonte_declarado = "horizonte" in fuentes_actual
    if horizonte_declarado and mascara_horizonte is None:
        raise ValueError(
            "La definición declara 'horizonte' como fuente de la situación "
            "actual, pero no se entregó la máscara de sombreado de horizonte. "
            "Calcula el sombreado de horizonte en esta sesión (sección 🏔️ de "
            "Mismatch) antes de ejecutar los escenarios."
        )
    if mascara_horizonte is not None and not horizonte_declarado:
        raise ValueError(
            "Se entregó una máscara de horizonte pero la definición congelada "
            "no declara 'horizonte' como fuente; redefine los escenarios con "
            "el horizonte activado para no mezclar supuestos."
        )

    p_shade_actual = alinear_fs_con_tmy(
        df_fs_actual, tmy.index, modo=modo_alineacion, modo_agregacion=modo_agregacion
    )
    fuente_actual = "fs_geometrico_actual"
    if mascara_horizonte is not None:
        p_shade_actual, _ = combinar_fs_con_horizonte(
            p_shade_actual, mascara_horizonte
        )
        fuente_actual = "fs_geometrico_actual+horizonte"
    actual = _simular_escenario(
        p_shade=_validar_p_shade("p_shade actual", p_shade_actual.to_numpy()),
        fuente_p_shade=fuente_actual,
        **comunes,
    )

    # Alternativa optimizada: solo si existe una nueva distribución declarada.
    if isinstance(df_fs_optimizada, pd.DataFrame) and not df_fs_optimizada.empty:
        p_shade_opt = alinear_fs_con_tmy(
            df_fs_optimizada,
            tmy.index,
            modo=modo_alineacion,
            modo_agregacion=modo_agregacion,
        )
        # El horizonte es del sitio, no de la distribución de paneles: si la
        # situación actual lo incluye, la alternativa también (misma física).
        fuente_opt = "fs_geometrico_optimizado"
        if mascara_horizonte is not None:
            p_shade_opt, _ = combinar_fs_con_horizonte(
                p_shade_opt, mascara_horizonte
            )
            fuente_opt = "fs_geometrico_optimizado+horizonte"
        optimizada = _simular_escenario(
            p_shade=_validar_p_shade("p_shade optimizada", p_shade_opt.to_numpy()),
            fuente_p_shade=fuente_opt,
            **comunes,
        )
    else:
        optimizada = {
            "estado": "pendiente_parametros",
            "motivo": (
                "La alternativa optimizada aún no declara su nueva distribución "
                "de paneles (FS geométrico optimizado)."
            ),
            "base_id": base_id,
        }

    return {
        "schema_version": RESULTADOS_SCHEMA_VERSION,
        "base_id": base_id,
        "parametros": {
            "poa_huella": _huella_serie(poa),
            "modo_alineacion": modo_alineacion,
            "modo_agregacion": modo_agregacion,
            "N_serie": int(n_serie),
            "N_paralelo": int(n_paralelo),
            "eta_inversor": eta,
            "umbral_shade": 0.05,
        },
        "referencia": referencia,
        "actual": actual,
        "optimizada": optimizada,
    }
