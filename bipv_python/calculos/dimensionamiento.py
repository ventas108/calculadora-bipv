"""
Dimensionamiento de strings y sistema.
Equivalente de Mod_CalculoStringSizing + Mod_OptimizarStringSizing (VBA).

Resultado validado vs XLSM (hoja Optimizacion_String):
  N=8 paneles/string, Growatt MID15KTL3-X → 0 riesgos ✓
  N=7 → ALERTA (Vmp realista margen < 7.5%)
  N=9 → FALLA (Voc frío > 1100V)
"""
from dataclasses import dataclass
from typing import Literal


EstadoVerif = Literal["OK", "ALERTA", "FALLA"]
UMBRAL_ALERTA_PCT = 7.5  # % — umbral de alerta (extraído de hoja Optimizacion_String L14)


@dataclass
class ResultadoString:
    N_serie: int
    Voc_frio: float
    Vmp_real: float
    Vmp_extremo: float
    I_equiv_tracker: float
    v1_voc_max:   EstadoVerif = "OK"
    v2_vmp_real:  EstadoVerif = "OK"
    v3_vmp_extr:  EstadoVerif = "OK"
    v4_i_max:     EstadoVerif = "OK"
    riesgos: int = 0

    def semaforo_color(self) -> str:
        if self.riesgos == 0:
            return "🟢"
        elif any(v == "FALLA" for v in [self.v1_voc_max, self.v2_vmp_real,
                                         self.v3_vmp_extr, self.v4_i_max]):
            return "🔴"
        return "🟡"


def semaforo(valor: float, limite: float, invertir=False) -> EstadoVerif:
    """
    Semáforo con margen de alerta de 7.5% (valor del VBA).
    invertir=False → valor debe ser ≤ limite  (ej: Voc ≤ Vdc_max)
    invertir=True  → valor debe ser ≥ limite  (ej: Vmp ≥ Vmppt_min)
    """
    if not invertir:
        if valor > limite:
            return "FALLA"
        margen = (limite - valor) / limite * 100
        return "ALERTA" if margen < UMBRAL_ALERTA_PCT else "OK"
    else:
        if valor < limite:
            return "FALLA"
        margen = (valor - limite) / limite * 100
        return "ALERTA" if margen < UMBRAL_ALERTA_PCT else "OK"


def calcular_voc_string(N, Voc_stc, Tk_beta, T_cel):
    return N * Voc_stc * (1 + Tk_beta / 100.0 * (T_cel - 25.0))


def calcular_vmp_string(N, Vmp_stc, Tk_gamma, T_cel):
    return N * Vmp_stc * (1 + Tk_gamma / 100.0 * (T_cel - 25.0))


def optimizar_n_serie(panel: dict, inversor: dict,
                      T_frio: float = -5.0,
                      T_real: float = 36.35,
                      T_extremo: float = 41.94,
                      N_strings_tracker: int = 8,
                      FS_isc: float = 1.25,
                      N_min: int = 6,
                      N_max: int = 12) -> list:
    """
    Equivalente de Mod_OptimizarStringSizing (VBA).
    Barrido de N paneles/string con semáforo OK/ALERTA/FALLA.

    Resultado validado vs XLSM (hoja Optimizacion_String):
      N=6 → Voc=763V OK, Vmp=499.5V → FALLA  ✓
      N=7 → Voc=890V OK, Vmp=582.8V → ALERTA ✓
      N=8 → Voc=1017V OK, Vmp=666V  → OK ✓  SELECCIONADO
      N=9 → Voc=1145V FALLA (>1100V) ✓
    """
    resultados = []
    for N in range(N_min, N_max + 1):
        Voc_fr  = calcular_voc_string(N, panel["Voc_stc"], panel["Tk_beta"], T_frio)
        Vmp_re  = calcular_vmp_string(N, panel["Vmp_stc"], panel["Tk_gamma"], T_real)
        Vmp_ex  = calcular_vmp_string(N, panel["Vmp_stc"], panel["Tk_gamma"], T_extremo)
        I_equiv = panel["Isc_stc"] * N_strings_tracker * FS_isc

        v1 = semaforo(Voc_fr,  inversor["Vdc_max"],          invertir=False)
        v2 = semaforo(Vmp_re,  inversor["Vmppt_activo_min"], invertir=True)
        v3 = semaforo(Vmp_ex,  inversor["Vmppt_activo_min"], invertir=True)
        # Check 4-Isimax: comparar contra Isc_max_tracker (cortocircuito),
        # no contra I_max_tracker (operación/MPP). Fallback a I_max_tracker si falta.
        _isc_lim = inversor.get("Isc_max_tracker") or inversor.get("I_max_tracker", 0)
        v4 = semaforo(I_equiv, _isc_lim,                    invertir=False)

        riesgos = sum(1 for v in [v1, v2, v3, v4] if v in ("ALERTA", "FALLA"))
        resultados.append(ResultadoString(
            N_serie=N, Voc_frio=round(Voc_fr, 1), Vmp_real=round(Vmp_re, 1),
            Vmp_extremo=round(Vmp_ex, 1), I_equiv_tracker=round(I_equiv, 2),
            v1_voc_max=v1, v2_vmp_real=v2, v3_vmp_extr=v3, v4_i_max=v4,
            riesgos=riesgos,
        ))
    return resultados


def dimensionar_sistema(panel: dict, area_m2: float, N_serie: int,
                        N_strings_tracker: int, N_mppt: int) -> dict:
    """
    Dimensionamiento del sistema completo a partir del N óptimo.
    """
    N_strings_total = N_strings_tracker * N_mppt
    N_paneles       = N_serie * N_strings_total
    area_ocupada    = N_paneles * panel["area_m2"]
    P_dc_stc_W      = N_paneles * panel.get("Pmax_stc", 0)

    return {
        "N_paneles":         N_paneles,
        "N_strings_total":   N_strings_total,
        "P_dc_stc_kW":       round(P_dc_stc_W / 1000, 3),
        "area_ocupada_m2":   round(area_ocupada, 2),
        "cobertura_pct":     round(area_ocupada / area_m2 * 100, 1) if area_m2 > 0 else 0,
        "N_serie":           N_serie,
        "N_strings_tracker": N_strings_tracker,
        "N_mppt":            N_mppt,
    }
