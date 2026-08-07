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
