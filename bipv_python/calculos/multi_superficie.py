"""
multi_superficie.py — Soporte BIPV para instalaciones con múltiples superficies.

Tipos soportados: Fachada | Techo | Pérgola | Marquesina
Cada superficie tiene su propia tilt, azimuth, área y POA calculada con pvlib.
"""

from __future__ import annotations
from collections.abc import Mapping
import numpy as np
import pandas as pd
from calculos.solar import calcular_poa

# ── Constantes de tipos ────────────────────────────────────────────────────────

TIPOS_SUPERFICIE: dict[str, dict] = {
    "Fachada": {
        "icon":        "🏢",
        "tilt_deg":    90,
        "azimuth_deg": 180,
        "color_hex":   "#2196F3",
        "descripcion": "Panel vertical integrado en cerramiento",
        "tilt_min":    70,
        "tilt_max":    90,
        "posicion_3d": "cara_vertical",
    },
    "Techo": {
        "icon":        "🏠",
        "tilt_deg":    10,
        "azimuth_deg": 180,
        "color_hex":   "#FF9800",
        "descripcion": "Panel sobre cubierta plana o inclinada",
        "tilt_min":    0,
        "tilt_max":    45,
        "posicion_3d": "cubierta",
    },
    "Pérgola": {
        "icon":        "🌿",
        "tilt_deg":    5,
        "azimuth_deg": 180,
        "color_hex":   "#4CAF50",
        "descripcion": "Estructura semi-horizontal con soporte propio",
        "tilt_min":    0,
        "tilt_max":    20,
        "posicion_3d": "exterior_horizontal",
    },
    "Marquesina": {
        "icon":        "🏪",
        "tilt_deg":    20,
        "azimuth_deg": 180,
        "color_hex":   "#9C27B0",
        "descripcion": "Voladizo inclinado adosado a fachada",
        "tilt_min":    5,
        "tilt_max":    45,
        "posicion_3d": "voladizo",
    },
}

MESES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

# ── Constructores ──────────────────────────────────────────────────────────────

def superficie_nueva(
    nombre: str,
    tipo: str,
    tilt_deg: float | None = None,
    azimuth_deg: float | None = None,
    area_m2: float = 20.0,
    activa: bool = True,
) -> dict:
    """Crea un dict de superficie con defaults del tipo dado."""
    meta = TIPOS_SUPERFICIE.get(tipo, TIPOS_SUPERFICIE["Fachada"])
    return {
        "nombre":      nombre,
        "tipo":        tipo,
        "tilt_deg":    tilt_deg    if tilt_deg    is not None else meta["tilt_deg"],
        "azimuth_deg": azimuth_deg if azimuth_deg is not None else meta["azimuth_deg"],
        "area_m2":     area_m2,
        "activa":      activa,
    }


def superficies_por_defecto(
    azimuth_principal: float = 180.0,
    area_fachada: float = 50.0,
) -> list[dict]:
    """Retorna una lista inicial con la fachada principal del proyecto."""
    return [
        superficie_nueva(
            "Fachada principal",
            "Fachada",
            tilt_deg=90,
            azimuth_deg=azimuth_principal,
            area_m2=area_fachada,
        )
    ]


# ── Cálculo POA por superficie ─────────────────────────────────────────────────

def calcular_poa_superficie(
    tmy_df: pd.DataFrame,
    lat: float,
    lon: float,
    alt_m: float,
    superficie: dict,
    albedo: float = 0.20,
    bifacial: dict | None = None,
) -> pd.DataFrame:
    """
    Calcula POA horaria para UNA superficie.
    Retorna DataFrame con columnas pvlib estándar (poa_global, ...).

    Si `bifacial` viene (o la superficie trae su propio dict en la clave
    "bifacial"), la POA incluye la ganancia de la cara trasera vía
    pvlib infinite_sheds. La clave de la superficie tiene prioridad.
    """
    return calcular_poa(
        tmy_df,
        lat,
        lon,
        alt_m,
        tilt=float(superficie["tilt_deg"]),
        azimuth=float(superficie["azimuth_deg"]),
        albedo=float(superficie.get("albedo", albedo)),
        bifacial=superficie.get("bifacial", bifacial),
    )


def calcular_poa_todas(
    superficies: list[dict],
    tmy_df: pd.DataFrame,
    lat: float,
    lon: float,
    alt_m: float,
    albedo: float = 0.20,
    bifacial: dict | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Calcula POA para todas las superficies activas.
    Retorna dict {nombre_superficie: poa_df}.
    `albedo` y `bifacial` aplican a todas las superficies, salvo que una
    superficie traiga sus propios valores ("albedo" / "bifacial").
    """
    resultado: dict[str, pd.DataFrame] = {}
    for sup in superficies:
        if not sup.get("activa", True):
            continue
        try:
            resultado[sup["nombre"]] = calcular_poa_superficie(
                tmy_df, lat, lon, alt_m, sup, albedo=albedo, bifacial=bifacial
            )
        except Exception:
            resultado[sup["nombre"]] = pd.DataFrame()
    return resultado


# ── Vigencia de la POA por superficie (Spec 05/vigencia-poa-superficie) ──────
# La página ya no usa calcular_poa_todas (que convierte cualquier fallo en un
# DataFrame vacío sin causa): usa calcular_poa_superficies_firmadas, que
# indexa por uid, firma cada POA y reporta los errores. Los consumidores leen
# solo POA vigentes a través de poas_vigentes().

MOTIVO_POA_SIN_CALCULAR = "sin_calcular"
MOTIVO_POA_GEOMETRIA = "geometria_cambiada"
MOTIVO_POA_TMY = "tmy_cambiado"
MOTIVO_POA_ERROR = "error_calculo"

TEXTO_MOTIVO_POA = {
    MOTIVO_POA_SIN_CALCULAR: "POA sin calcular",
    MOTIVO_POA_GEOMETRIA: "cambió la geometría, el montaje, el albedo o el bifacial",
    MOTIVO_POA_TMY: "cambió el TMY o la ubicación del proyecto",
    MOTIVO_POA_ERROR: "el cálculo de la POA falló",
}

_COLUMNAS_TMY_POA = ("T2m", "G_h", "Gb_n", "Gd_h")


def config_bifacial_superficie(
    superficie: dict,
    bifacial_cfg: dict | None,
    usar_bifacial: bool,
) -> dict | None:
    """Configuración bifacial efectiva de UNA superficie (antes en la página).

    tilt < 80° ⇒ factor de vista trasero 1.0; fachadas (tilt ≥ 80°) según su
    montaje: Adosada ⇒ factor 0 y albedo trasero 0.05; Ventilada ⇒ 1.0;
    Heredar ⇒ el factor de ``bifacial_cfg``. Sin bifacial activo ⇒ None.
    """
    if not usar_bifacial or not bifacial_cfg:
        return None
    cfg = dict(bifacial_cfg)
    if float(superficie.get("tilt_deg", 0)) < 80:
        cfg["factor_vista_trasera"] = 1.0
    else:
        montaje = str(superficie.get("montaje_fachada") or "Heredar de ☀️ Recurso Solar")
        if montaje.startswith("Adosada"):
            cfg["factor_vista_trasera"] = 0.0
            cfg["albedo_trasero"] = 0.05
        elif montaje.startswith("Ventilada"):
            cfg["factor_vista_trasera"] = 1.0
    return cfg


def _firma_sitio_poa(tmy_df: pd.DataFrame, lat: float, lon: float, alt_m: float) -> str:
    from calculos.produccion_vigencia import fingerprint_mapping, huella_horaria

    if not isinstance(tmy_df, pd.DataFrame) or tmy_df.empty:
        raise ValueError("El TMY no está disponible para firmar la POA.")
    idx = pd.DatetimeIndex(tmy_df.index)
    huellas = {
        col: huella_horaria(idx, tmy_df[col].to_numpy(dtype=float))
        for col in _COLUMNAS_TMY_POA if col in tmy_df.columns
    }
    if not huellas:
        raise ValueError("El TMY no trae columnas de irradiancia ni T2m para firmar la POA.")
    return fingerprint_mapping({
        "lat": round(float(lat), 6), "lon": round(float(lon), 6),
        "alt_m": round(float(alt_m), 1), "tmy": huellas,
    })


def _firma_geometria_poa(superficie: dict, albedo: float, bifacial_efectivo: dict | None) -> str:
    from calculos.produccion_vigencia import fingerprint_mapping

    return fingerprint_mapping({
        "tipo": str(superficie.get("tipo")),
        "tilt_deg": float(superficie["tilt_deg"]),
        "azimuth_deg": float(superficie["azimuth_deg"]),
        "area_m2": float(superficie["area_m2"]),
        "montaje_fachada": str(superficie.get("montaje_fachada") or ""),
        "albedo": float(superficie.get("albedo", albedo)),
        "bifacial": dict(bifacial_efectivo) if bifacial_efectivo else None,
    })


def firma_poa_superficie(
    superficie: dict,
    tmy_df: pd.DataFrame,
    lat: float,
    lon: float,
    alt_m: float,
    albedo: float,
    bifacial_cfg: dict | None,
    usar_bifacial: bool,
) -> dict:
    """Firma de la POA de una superficie: ``{"sitio", "geometria", "firma"}``.

    ``sitio`` cubre TMY (T2m, G_h, Gb_n, Gd_h) y ubicación; ``geometria`` cubre
    tipo, tilt, azimuth, área, montaje, albedo y bifacial efectivo. La firma
    combinada es la que se guarda en ``superficie["firma_poa"]``.
    """
    from calculos.produccion_vigencia import fingerprint_mapping

    sitio = _firma_sitio_poa(tmy_df, lat, lon, alt_m)
    geometria = _firma_geometria_poa(
        superficie, albedo, config_bifacial_superficie(superficie, bifacial_cfg, usar_bifacial),
    )
    return {"sitio": sitio, "geometria": geometria,
            "firma": fingerprint_mapping({"sitio": sitio, "geometria": geometria})}


def calcular_poa_superficies_firmadas(
    superficies: list[dict],
    tmy_df: pd.DataFrame,
    lat: float,
    lon: float,
    alt_m: float,
    albedo: float = 0.20,
    bifacial_cfg: dict | None = None,
    usar_bifacial: bool = False,
) -> tuple[dict, dict]:
    """POA de cada superficie activa, indexada por ``uid`` y firmada.

    Retorna ``(resultados, errores)``: ``resultados[uid] = {"nombre", "poa",
    "firma_sitio", "firma_geometria", "firma"}``; ``errores[uid]`` = causa
    legible del fallo. Un fallo nunca se convierte en una POA vacía.
    """
    resultados: dict = {}
    errores: dict = {}
    for sup in superficies:
        if not sup.get("activa", True):
            continue
        uid = sup["uid"]
        try:
            firma = firma_poa_superficie(
                sup, tmy_df, lat, lon, alt_m, albedo, bifacial_cfg, usar_bifacial,
            )
            bif = config_bifacial_superficie(sup, bifacial_cfg, usar_bifacial)
            poa = calcular_poa_superficie(
                tmy_df, lat, lon, alt_m, {**sup, "bifacial": bif} if bif else sup,
                albedo=albedo, bifacial=None,
            )
            if not isinstance(poa, pd.DataFrame) or poa.empty or "poa_global" not in poa.columns:
                raise ValueError("el cálculo no devolvió una serie 'poa_global'")
        except Exception as exc:  # se reporta, nunca se oculta
            errores[uid] = f"{type(exc).__name__}: {exc}"
            continue
        resultados[uid] = {
            "nombre": sup.get("nombre"), "poa": poa,
            "firma_sitio": firma["sitio"], "firma_geometria": firma["geometria"],
            "firma": firma["firma"],
        }
    return resultados, errores


def poas_vigentes(
    superficies: list[dict],
    poa_superficies: dict | None,
    errores: dict | None,
    tmy_df: pd.DataFrame | None,
    lat: float,
    lon: float,
    alt_m: float,
    albedo: float,
    bifacial_cfg: dict | None,
    usar_bifacial: bool,
) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    """POA vigentes de las superficies activas, por NOMBRE actual.

    Retorna ``(vigentes, motivos)``: ``vigentes[nombre]`` solo contiene POA
    cuya firma coincide con la geometría, el TMY y la ubicación actuales;
    ``motivos[nombre]`` explica por qué una superficie activa no tiene POA
    vigente (constantes ``MOTIVO_POA_*``). Entradas antiguas indexadas por
    nombre o sin firma cuentan como ``sin_calcular``.
    """
    poa_superficies = poa_superficies or {}
    errores = errores or {}
    vigentes: dict[str, pd.DataFrame] = {}
    motivos: dict[str, str] = {}
    try:
        sitio_actual = _firma_sitio_poa(tmy_df, lat, lon, alt_m) if tmy_df is not None else None
    except (TypeError, ValueError):
        sitio_actual = None
    for sup in superficies:
        if not sup.get("activa", True):
            continue
        nombre = sup.get("nombre")
        uid = sup.get("uid")
        entrada = poa_superficies.get(uid) if uid is not None else None
        if uid is not None and uid in errores:
            motivos[nombre] = MOTIVO_POA_ERROR
            continue
        if not isinstance(entrada, dict) or "firma" not in entrada:
            motivos[nombre] = MOTIVO_POA_SIN_CALCULAR
            continue
        if sitio_actual is None or entrada.get("firma_sitio") != sitio_actual:
            motivos[nombre] = MOTIVO_POA_TMY
            continue
        geometria_actual = _firma_geometria_poa(
            sup, albedo, config_bifacial_superficie(sup, bifacial_cfg, usar_bifacial),
        )
        if entrada.get("firma_geometria") != geometria_actual:
            motivos[nombre] = MOTIVO_POA_GEOMETRIA
            continue
        vigentes[nombre] = entrada["poa"]
    return vigentes, motivos


def parametros_poa_estado(session_state) -> tuple[float, dict | None, bool]:
    """``(albedo, bifacial_cfg, usar_bifacial)`` tal como los usa Vista 3D.

    Fuente única para el cálculo y para la vigencia: el bifacial se aplica si
    ☀️ Recurso Solar lo activó con configuración y el usuario no lo apagó en
    Vista 3D (casilla ``ms_bifacial_on``, activa por defecto).
    """
    cfg = session_state.get("bifacial_cfg") or None
    usar = (
        bool(session_state.get("bifacial_activo")) and bool(cfg)
        and bool(session_state.get("ms_bifacial_on", True))
    )
    return float(session_state.get("albedo_suelo", 0.20)), cfg, usar


def poas_vigentes_estado(session_state, lat: float, lon: float, alt_m: float):
    """``poas_vigentes`` con las superficies, POA, errores y TMY de la sesión."""
    albedo, cfg, usar = parametros_poa_estado(session_state)
    return poas_vigentes(
        session_state.get("superficies_bipv") or [],
        session_state.get("poa_superficies"),
        session_state.get("poa_superficies_errores"),
        session_state.get("tmy_df"),
        lat, lon, alt_m, albedo, cfg, usar,
    )


def poa_mensual_superficie(poa_df: pd.DataFrame) -> list[float]:
    """
    Convierte POA horaria en lista de 12 valores mensuales [kWh/m²/mes].
    """
    if poa_df is None or poa_df.empty:
        return [0.0] * 12
    m_kwh = poa_df.groupby(poa_df.index.month)["poa_global"].sum() / 1000.0
    return [float(m_kwh.get(m, 0.0)) for m in range(1, 13)]


def poa_anual_superficie(poa_df: pd.DataFrame) -> float:
    """POA anual total en kWh/m²/año."""
    if poa_df is None or poa_df.empty:
        return 0.0
    return float(poa_df["poa_global"].sum() / 1000.0)


# ── Cálculo producción ─────────────────────────────────────────────────────────

def produccion_superficie(
    poa_df: pd.DataFrame,
    area_m2: float,
    eta_panel: float = 0.16,
    pr: float = 0.78,
) -> dict:
    """
    Calcula producción AC para una superficie.

    Parámetros
    ----------
    poa_df    : DataFrame POA horario (poa_global en W/m²)
    area_m2   : área activa de paneles
    eta_panel : eficiencia de panel [0-1] (default 0.16 = 16%)
    pr        : Performance Ratio [0-1] (default 0.78)

    Retorna dict con:
        e_ac_anual_kWh, e_ac_mensual (lista 12), poa_anual_kWh_m2
    """
    if poa_df is None or poa_df.empty:
        return {"e_ac_anual_kWh": 0.0, "e_ac_mensual": [0.0]*12, "poa_anual_kWh_m2": 0.0}

    poa_anual = poa_anual_superficie(poa_df)
    e_ac_anual = poa_anual * area_m2 * eta_panel * pr

    poa_mes = poa_mensual_superficie(poa_df)
    e_ac_mensual = [p * area_m2 * eta_panel * pr for p in poa_mes]

    return {
        "e_ac_anual_kWh":   round(e_ac_anual, 1),
        "e_ac_mensual":     [round(v, 1) for v in e_ac_mensual],
        "poa_anual_kWh_m2": round(poa_anual, 1),
    }


# ── Integración con CSV de Sombreado ──────────────────────────────────────────

def mapear_fachadas_csv(
    df_fs_raw: pd.DataFrame,
    superficies: list[dict],
) -> dict[str, str | None]:
    """
    Intenta mapear la columna 'fachada' del CSV a las superficies definidas.

    Retorna dict {nombre_superficie: nombre_fachada_csv | None}
    """
    if df_fs_raw is None or "fachada" not in df_fs_raw.columns:
        return {s["nombre"]: None for s in superficies}

    fachadas_csv = sorted(df_fs_raw["fachada"].dropna().unique().tolist())
    nombres_sup  = [s["nombre"] for s in superficies]

    mapeo: dict[str, str | None] = {}
    for nombre in nombres_sup:
        # Coincidencia exacta
        if nombre in fachadas_csv:
            mapeo[nombre] = nombre
            continue
        # Coincidencia parcial (ignora mayúsculas/espacios)
        norm = nombre.lower().replace(" ", "")
        match = next(
            (f for f in fachadas_csv if f.lower().replace(" ", "") == norm),
            None,
        )
        mapeo[nombre] = match
    return mapeo


def fs_mensual_por_superficie(
    df_fs_raw: pd.DataFrame,
    nombre_fachada_csv: str | None,
) -> list[float]:
    """
    Calcula FS promedio mensual para una superficie/fachada del CSV.
    Retorna lista de 12 valores FS ∈ [0,1]. 0=sin sombra.
    """
    if df_fs_raw is None or df_fs_raw.empty:
        return [0.0] * 12

    df = df_fs_raw.copy()
    if nombre_fachada_csv and "fachada" in df.columns:
        df = df[df["fachada"] == nombre_fachada_csv]

    if df.empty:
        return [0.0] * 12

    if "FS_geometrico" not in df.columns:
        raise ValueError(
            "El DataFrame de sombreado no contiene FS_geometrico; "
            "FS climático o combinado no puede colorear ni alimentar superficies."
        )

    fs_mes = df.groupby("mes")["FS_geometrico"].mean()
    return [float(fs_mes.get(m, 0.0)) for m in range(1, 13)]


# ── Paleta de colores ──────────────────────────────────────────────────────────

PALETA_TIPOS: dict[str, str] = {
    "Fachada":    "#2196F3",
    "Techo":      "#FF9800",
    "Pérgola":    "#4CAF50",
    "Marquesina": "#9C27B0",
}

def color_tipo(tipo: str) -> str:
    return PALETA_TIPOS.get(tipo, "#607D8B")


def color_poa_normalizado(val: float, vmin: float, vmax: float) -> str:
    """Mapea POA [vmin, vmax] a color rgb azul → amarillo → rojo."""
    rng = max(1.0, vmax - vmin)
    t   = max(0.0, min(1.0, (val - vmin) / rng))
    if t < 0.5:
        s = t * 2
        r = int(40  + 215 * s)
        g = int(100 + 155 * s)
        b = int(220 - 170 * s)
    else:
        s = (t - 0.5) * 2
        r = 255
        g = int(255 - 230 * s)
        b = int(50  -  50 * s)
    return f"rgb({r},{g},{b})"


def color_fs(fs: float) -> str:
    """FS 0-1 → color: verde (libre) → naranja (parcial) → rojo (bypass)."""
    if fs < 0.10:
        return "rgb(56, 161, 105)"    # verde
    if fs < 0.35:
        return "rgb(237, 137, 54)"    # naranja
    return "rgb(229, 62, 62)"         # rojo


# ── Integración multi-superficie → sistema principal ──────────────────────────

def agregar_poa_ponderada(
    poa_superficies: dict,
    superficies: list[dict],
) -> "pd.DataFrame":
    """
    Combina los perfiles POA horarios de múltiples superficies en un único
    DataFrame ponderado por área activa.

    No sobreescribe 'poa_df' (superficie simple de Pág. 2).
    Se guarda en session_state['poa_df_multisup'].

    Retorna DataFrame con columna 'poa_global' (W/m²) representando
    la irradiancia media ponderada del sistema completo.
    """
    frames, pesos = [], []
    for sup in superficies:
        if not sup.get("activa", True):
            continue
        poa = poa_superficies.get(sup["nombre"])
        if poa is None or poa.empty or "poa_global" not in poa.columns:
            continue
        frames.append(poa["poa_global"])
        pesos.append(float(sup["area_m2"]))

    if not frames:
        return pd.DataFrame()

    area_total = sum(pesos)
    if area_total <= 0:
        return pd.DataFrame()

    combinado = sum(f * (w / area_total) for f, w in zip(frames, pesos))
    return pd.DataFrame({"poa_global": combinado})


def e_ac_total_multisup(
    poa_superficies: dict,
    superficies: list[dict],
    eta_panel: float | Mapping[str, float] = 0.16,
    pr: float = 0.78,
) -> dict:
    """
    Calcula E_ac anual total y por superficie para el sistema multi-superficie.

    ``eta_panel`` puede ser un mapa ``nombre → η`` (Spec
    ``05/panel-por-superficie``): cada superficie usa la eficiencia de su
    panel y una superficie activa sin η es un error, no un 16 % implícito.

    Retorna:
        e_ac_total_kWh  : float — suma de todas las superficies activas
        area_total_m2   : float — suma de áreas activas
        desglose        : list[dict] — {nombre, tipo, area_m2, e_ac_kWh,
                          poa_kWh_m2[, eta_panel]}
    """
    por_superficie = isinstance(eta_panel, Mapping)
    desglose, e_total, area_total = [], 0.0, 0.0
    for sup in superficies:
        if not sup.get("activa", True):
            continue
        if por_superficie:
            if sup["nombre"] not in eta_panel:
                raise ValueError(
                    f"La superficie '{sup['nombre']}' no tiene la eficiencia de su panel."
                )
            eta_sup = float(eta_panel[sup["nombre"]])
        else:
            eta_sup = float(eta_panel)
        poa = poa_superficies.get(sup["nombre"])
        prod = produccion_superficie(poa, sup["area_m2"], eta_sup, pr)
        e_total    += prod["e_ac_anual_kWh"]
        area_total += sup["area_m2"]
        fila = {
            "nombre":       sup["nombre"],
            "tipo":         sup["tipo"],
            "area_m2":      sup["area_m2"],
            "e_ac_kWh":     prod["e_ac_anual_kWh"],
            "poa_kWh_m2":   prod["poa_anual_kWh_m2"],
        }
        if por_superficie:
            fila["eta_panel"] = round(eta_sup, 5)
        desglose.append(fila)
    return {
        "e_ac_total_kWh": round(e_total, 1),
        "area_total_m2":  round(area_total, 1),
        "desglose":        desglose,
    }
