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
