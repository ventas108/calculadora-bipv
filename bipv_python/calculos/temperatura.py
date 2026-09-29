"""
Cálculo de temperatura de celda.
Equivalente de Mod_TemperaturasDiseno (VBA).
"""
import numpy as np


def temperatura_celda_noct(G_poa, T_amb, NOCT: float = 45.0, k_bipv: float = 1.0):
    """
    T_c = T_amb + G_poa × (NOCT − 20) / 800 × k_bipv

    Parámetros
    ----------
    G_poa  : irradiancia en el plano del array (W/m²) — escalar o array numpy
    T_amb  : temperatura ambiente (°C) — escalar o array numpy
    NOCT   : temperatura nominal de operación (°C); defecto 45°C (estándar IEC 61215)
    k_bipv : factor de confinamiento térmico BIPV (IEA-PVPS T15):
               1.0 → fachada ventilada libre (espacio > 10 cm)
               1.3 → fachada confinada típica (cámara 2–5 cm) ← defecto BIPV
               1.5 → sellado total, sin cámara de aire

    Validado vs XLSM (hoja Datos_Tecnicos, fila 31) con k_bipv=1.0:
      G=850, T_amb=20°C, NOCT=45°C → T_c ≈ 46.6°C

    Ejemplo BIPV confinado con k_bipv=1.3:
      G=800, T_amb=25°C, NOCT=50°C → T_c ≈ 25 + 800×(30/800)×1.3 = 64°C
    """
    G   = np.asarray(G_poa, dtype=float)
    T   = np.asarray(T_amb, dtype=float)
    k   = float(np.clip(k_bipv, 0.5, 2.0))   # límites físicos razonables
    noct = float(NOCT)
    return T + G * ((noct - 20.0) / 800.0) * k


# ── #229 — validación del trío de temperaturas de diseño ─────────────────────
KEYS_TEMPS_DISENO = ("T_min_diseno", "T_cel_realista", "T_cel_extremo")


def temps_diseno_en_cero(estado: dict) -> bool:
    """
    True solo si las TRES temperaturas de diseño están presentes y en 0.0.

    Físicamente T_mín, T_celda realista y T_celda extremo nunca son 0 °C a la
    vez (un solo 0 °C es legítimo, p. ej. T_mín en páramo; un subconjunto en
    cero con las demás ausentes tampoco se toca — solo el trío completo en
    cero es el estado corrupto heredado que no debe guardarse ni restaurarse).
    """
    valores = [estado.get(k) for k in KEYS_TEMPS_DISENO]
    if any(v is None for v in valores):
        return False
    try:
        return all(abs(float(v)) < 1e-9 for v in valores)
    except (TypeError, ValueError):
        return False


# ── Temperaturas de diseño desde el TMY (Spec 03/temperaturas-diseno) ────────
# 29-sep-2026: el recálculo dependía solo del NOMBRE de la ciudad, así que
# otra versión de PVGIS, otras coordenadas u otro panel no lo disparaban, y
# 🏠 Proyecto las pisaba con los valores fijos de la ciudad. La firma del
# TMY (y del NOCT) decide cuándo recalcular; se guarda con el proyecto.
CLAVE_FIRMA_TEMPS_TMY = "dim_temps_tmy_firma"


def temperaturas_diseno_desde_tmy(t2m, noct: float) -> dict:
    """Mismas fórmulas que Mod_TemperaturasDiseno (VBA):
    T_mín = mínima del TMY; T_celda realista = P95 + (NOCT − 20)/800 × 800;
    T_celda extremo = máxima + (NOCT − 20)/800 × 1000."""
    serie = np.asarray(t2m, dtype=float)
    t_min = round(float(np.nanmin(serie)), 1)
    t_p95 = round(float(np.nanquantile(serie, 0.95)), 1)
    t_max = round(float(np.nanmax(serie)), 1)
    k = (float(noct) - 20.0) / 800.0
    return {
        "T_min_diseno": t_min,
        "T_cel_realista": round(t_p95 + k * 800.0, 1),
        "T_cel_extremo": round(t_max + k * 1000.0, 1),
    }


def firma_temperaturas_tmy(t2m, noct: float) -> str:
    serie = np.asarray(t2m, dtype=float)
    return (f"{np.nanmin(serie):.2f}|{np.nanquantile(serie, 0.95):.2f}|"
            f"{np.nanmax(serie):.2f}|{serie.size}|{float(noct):.1f}")


def temperaturas_a_aplicar(estado, t2m, noct: float) -> dict | None:
    """Temperaturas (y firma) a escribir en la sesión, o ``None`` si hay que
    respetar las actuales: se recalcula si cambió el TMY o el NOCT, si falta
    alguna o si las tres están en 0."""
    if t2m is None:
        return None
    firma = firma_temperaturas_tmy(t2m, noct)
    faltan = any(estado.get(k) is None for k in KEYS_TEMPS_DISENO)
    if estado.get(CLAVE_FIRMA_TEMPS_TMY) == firma and not faltan and not temps_diseno_en_cero(estado):
        return None
    return {**temperaturas_diseno_desde_tmy(t2m, noct), CLAVE_FIRMA_TEMPS_TMY: firma}
