"""
Cálculo de temperatura de celda.
Equivalente de Mod_TemperaturasDiseno (VBA).
"""
import pvlib


def temperatura_celda_noct(G_poa, T_amb, NOCT=45.0):
    """
    T_c = T_amb + (NOCT - 20) / 800 × G
    Equivalente exacto de la fórmula del VBA.
    pvlib.temperature.faiman() implementa esto directamente.

    Validado vs XLSM (hoja Datos_Tecnicos, fila 31):
      G=850, T_amb=20°C, NOCT=45°C → T_c ≈ 46.6°C
    """
    return pvlib.temperature.faiman(G_poa, T_amb, noct=NOCT, module_efficiency=0.0)
