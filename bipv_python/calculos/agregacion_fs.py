"""Contrato común para agregar factores de sombreado por tamaño del array.

Un registro de FS representa un punto de análisis. Por eso un promedio simple
solo es físicamente equivalente cuando todos los puntos representan la misma
cantidad de módulos, área activa o potencia. Este módulo centraliza la
selección y deja la decisión auditable para la UI y para los modelos solares.
"""
from __future__ import annotations

import unicodedata
from typing import Any

import numpy as np
import pandas as pd


MODOS_AGREGACION_FS = ("auto", "simple", "modulos", "area", "potencia")

_ALIAS_PESO = {
    "n_modulos": (
        "nmodulos",
        "numeromodulos",
        "cantidadmodulos",
        "numpaneles",
        "npaneles",
        "cantidadpaneles",
        "modulos",
    ),
    "area_activa_m2": (
        "areaactivam2",
        "areaactiva",
        "aream2",
        "areamodulosm2",
        "superficieactivam2",
    ),
    "potencia_instalada_kw": (
        "potenciainstaladakw",
        "potenciainstalada",
        "potenciakw",
        "potenciakwp",
        "potenciaw",
        "potenciainstaladaw",
        "pdcw",
        "pdckw",
    ),
}

_ETIQUETAS = {
    "simple": "promedio simple por punto",
    "modulos": "ponderado por número de módulos",
    "area": "ponderado por área activa",
    "potencia": "ponderado por potencia instalada",
}


def normalizar_nombre_columna(nombre: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(nombre))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return "".join(c for c in texto.lower() if c.isalnum())


def detectar_columnas_peso(df: pd.DataFrame) -> dict[str, str]:
    """Devuelve columnas de peso reconocidas sin alterar el DataFrame."""
    encontradas: dict[str, str] = {}
    normalizadas = {
        normalizar_nombre_columna(col): str(col) for col in df.columns
    }
    for canonica, aliases in _ALIAS_PESO.items():
        for alias in aliases:
            if alias in normalizadas:
                encontradas[canonica] = normalizadas[alias]
                break
    return encontradas


def _modo_canonico(modo: str | None) -> str:
    modo = str(modo or "auto").strip().lower()
    equivalencias = {
        "automatico": "auto",
        "automático": "auto",
        "promedio": "simple",
        "numero_modulos": "modulos",
        "n_modulos": "modulos",
        "área": "area",
        "area_activa": "area",
        "potencia_instalada": "potencia",
    }
    modo = equivalencias.get(modo, modo)
    return modo if modo in MODOS_AGREGACION_FS else "auto"


def resolver_peso(
    df: pd.DataFrame,
    modo: str = "auto",
) -> tuple[pd.Series, dict[str, Any]]:
    """Resuelve un peso completo y positivo, o declara fallback simple.

    En ``auto`` se priorizan módulos, área y potencia, en ese orden. Si una
    columna existe pero tiene datos incompletos o no positivos, no se usa una
    fracción de ella: se cae a promedio simple con una advertencia explícita.
    """
    solicitado = _modo_canonico(modo)
    columnas = detectar_columnas_peso(df)
    candidatos = (
        ("modulos", "n_modulos"),
        ("area", "area_activa_m2"),
        ("potencia", "potencia_instalada_kw"),
    )
    advertencias: list[str] = []
    elegido: tuple[str, str] | None = None

    if solicitado == "simple":
        elegido = None
    elif solicitado == "auto":
        for modo_candidato, canonica in candidatos:
            if canonica in columnas:
                elegido = (modo_candidato, canonica)
                break
        if elegido is None:
            advertencias.append(
                "No hay N módulos, área activa ni potencia instalada; "
                "se usa promedio simple por punto."
            )
    else:
        canonica = dict(candidatos).get(solicitado)
        if canonica and canonica in columnas:
            elegido = (solicitado, canonica)
        else:
            advertencias.append(
                f"No se encontró una columna válida para ponderar por {solicitado}; "
                "se usa promedio simple por punto."
            )

    if elegido is None:
        pesos = pd.Series(1.0, index=df.index, dtype=float)
        return pesos, {
            "modo_solicitado": solicitado,
            "modo_aplicado": "simple",
            "columna_peso": None,
            "etiqueta": _ETIQUETAS["simple"],
            "n_filas": int(len(df)),
            "n_pesos_validos": int(len(df)),
            "cobertura_peso_pct": 100.0 if len(df) else 0.0,
            "pesos_constantes": True,
            "advertencias": advertencias,
        }

    modo_aplicado, canonica = elegido
    columna = columnas[canonica]
    pesos = pd.to_numeric(df[columna], errors="coerce")
    validos = pesos.notna() & np.isfinite(pesos) & (pesos > 0)
    cobertura = float(validos.mean() * 100.0) if len(df) else 0.0
    if not bool(validos.all()):
        advertencias.append(
            f"La columna {columna!r} no tiene pesos positivos en todas las "
            "filas; se usa promedio simple para evitar sesgo silencioso."
        )
        pesos = pd.Series(1.0, index=df.index, dtype=float)
        return pesos, {
            "modo_solicitado": solicitado,
            "modo_aplicado": "simple",
            "columna_peso": columna,
            "etiqueta": _ETIQUETAS["simple"],
            "n_filas": int(len(df)),
            "n_pesos_validos": int(validos.sum()),
            "cobertura_peso_pct": round(cobertura, 1),
            "pesos_constantes": True,
            "advertencias": advertencias,
        }

    pesos = pesos.astype(float)
    constantes = bool(np.isclose(pesos.to_numpy(), pesos.iloc[0]).all())
    if constantes and solicitado == "auto":
        advertencias.append(
            f"{columna!r} es constante: el ponderado coincide con promedio simple."
        )
    return pesos, {
        "modo_solicitado": solicitado,
        "modo_aplicado": modo_aplicado,
        "columna_peso": columna,
        "etiqueta": _ETIQUETAS[modo_aplicado],
        "n_filas": int(len(df)),
        "n_pesos_validos": int(validos.sum()),
        "cobertura_peso_pct": round(cobertura, 1),
        "pesos_constantes": constantes,
        "advertencias": advertencias,
    }


def promedio_fs_por_claves(
    df: pd.DataFrame,
    claves: list[str],
    *,
    modo: str = "auto",
    columna_fs: str = "FS_geometrico",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Agrega FS por claves usando el contrato de pesos resuelto."""
    if not claves:
        raise ValueError("Se requiere al menos una clave de agregación.")
    pesos, auditoria = resolver_peso(df, modo)
    trabajo = df[claves + [columna_fs]].copy()
    trabajo["_peso_fs"] = pesos
    trabajo["_fs_peso"] = (
        pd.to_numeric(trabajo[columna_fs], errors="coerce")
        .fillna(0.0)
        .clip(0.0, 1.0)
        * trabajo["_peso_fs"]
    )
    agrupado = (
        trabajo.groupby(claves, dropna=False)
        .agg(_fs_peso=("_fs_peso", "sum"), _peso_fs=("_peso_fs", "sum"))
        .reset_index()
    )
    agrupado[columna_fs] = (
        agrupado["_fs_peso"] / agrupado["_peso_fs"].replace(0.0, np.nan)
    ).fillna(0.0).clip(0.0, 1.0)
    resultado = agrupado[claves + [columna_fs]].copy()
    auditoria = {
        **auditoria,
        "claves": list(claves),
        "n_grupos": int(len(resultado)),
        "peso_total": round(float(trabajo["_peso_fs"].sum()), 6),
    }
    return resultado, auditoria