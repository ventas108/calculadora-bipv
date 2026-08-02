#!/usr/bin/env python3
"""
Parche: Task #68 — Seleccionar N óptimo por máxima tensión MPPT
Aplicar en el servidor:
    cd /var/www/bipv/calculadora-bipv
    python3 bipv_python/scripts/patch_n_optimo_mppt.py
    pm2 restart streamlit-bipv

Cambios:
  1. calculos/dimensionamiento.py  — campo v5_vmp_max + mppt_util_pct en ResultadoString;
                                     check "Vmp_real ≤ Vmppt_max" en optimizar_n_serie
  2. pages/4_Dimensionamiento.py  — nueva columna "5-Vmp≤Vmppt_max" y "MPPT util %" en tabla;
                                     criterio de selección usa mppt_util_pct
"""
import glob
from pathlib import Path

BASE  = Path(__file__).resolve().parent.parent
CALC  = BASE / "calculos"
PAGES = BASE / "pages"

errors = []

def patch(ruta: Path, buscar: str, reemplazar: str, desc: str) -> bool:
    txt = ruta.read_text(encoding="utf-8")
    if buscar not in txt:
        print(f"  ⚠  '{desc}' — fragmento NOT found (already applied?)")
        errors.append(desc)
        return False
    ruta.write_text(txt.replace(buscar, reemplazar, 1), encoding="utf-8")
    print(f"  ✅  '{desc}' → {ruta.name}")
    return True

# ══════════════════════════════════════════════════════════════════════════════
# 1. calculos/dimensionamiento.py — dataclass + v5 en optimizador
# ══════════════════════════════════════════════════════════════════════════════
print("\n[1] calculos/dimensionamiento.py")

_dim = CALC / "dimensionamiento.py"

patch(
    _dim,
    buscar=(
        '    v1_voc_max:   EstadoVerif = "OK"\n'
        '    v2_vmp_real:  EstadoVerif = "OK"\n'
        '    v3_vmp_extr:  EstadoVerif = "OK"\n'
        '    v4_i_max:     EstadoVerif = "OK"\n'
        '    riesgos: int = 0\n'
        '\n'
        '    def semaforo_color(self) -> str:\n'
        '        if self.riesgos == 0:\n'
        '            return "🟢"\n'
        '        elif any(v == "FALLA" for v in [self.v1_voc_max, self.v2_vmp_real,\n'
        '                                         self.v3_vmp_extr, self.v4_i_max]):\n'
        '            return "🔴"\n'
        '        return "🟡"'
    ),
    reemplazar=(
        '    v1_voc_max:   EstadoVerif = "OK"\n'
        '    v2_vmp_real:  EstadoVerif = "OK"\n'
        '    v3_vmp_extr:  EstadoVerif = "OK"\n'
        '    v4_i_max:     EstadoVerif = "OK"\n'
        '    v5_vmp_max:   EstadoVerif = "OK"   # Vmp_real ≤ Vmppt_max — límite superior MPPT\n'
        '    riesgos: int = 0\n'
        '    mppt_util_pct: float = 0.0         # Vmp_real / Vmppt_max × 100 — aprovechamiento del rango MPPT\n'
        '\n'
        '    def semaforo_color(self) -> str:\n'
        '        if self.riesgos == 0:\n'
        '            return "🟢"\n'
        '        elif any(v == "FALLA" for v in [self.v1_voc_max, self.v2_vmp_real,\n'
        '                                         self.v3_vmp_extr, self.v4_i_max,\n'
        '                                         self.v5_vmp_max]):\n'
        '            return "🔴"\n'
        '        return "🟡"'
    ),
    desc="ResultadoString v5_vmp_max + mppt_util_pct"
)

patch(
    _dim,
    buscar=(
        '        v1 = semaforo(Voc_fr,  inversor["Vdc_max"],          invertir=False)\n'
        '        v2 = semaforo(Vmp_re,  inversor["Vmppt_activo_min"], invertir=True)\n'
        '        v3 = semaforo(Vmp_ex,  inversor["Vmppt_activo_min"], invertir=True)\n'
        '        # Check 4-Isimax: comparar contra Isc_max_tracker (cortocircuito),\n'
        '        # no contra I_max_tracker (operación/MPP). Fallback a I_max_tracker si falta.\n'
        '        _isc_lim = inversor.get("Isc_max_tracker") or inversor.get("I_max_tracker", 0)\n'
        '        v4 = semaforo(I_equiv, _isc_lim,                    invertir=False)\n'
        '\n'
        '        riesgos = sum(1 for v in [v1, v2, v3, v4] if v in ("ALERTA", "FALLA"))\n'
        '        resultados.append(ResultadoString(\n'
        '            N_serie=N, Voc_frio=round(Voc_fr, 1), Vmp_real=round(Vmp_re, 1),\n'
        '            Vmp_extremo=round(Vmp_ex, 1), I_equiv_tracker=round(I_equiv, 2),\n'
        '            v1_voc_max=v1, v2_vmp_real=v2, v3_vmp_extr=v3, v4_i_max=v4,\n'
        '            riesgos=riesgos,\n'
        '        ))'
    ),
    reemplazar=(
        '        v1 = semaforo(Voc_fr,  inversor["Vdc_max"],          invertir=False)\n'
        '        v2 = semaforo(Vmp_re,  inversor["Vmppt_activo_min"], invertir=True)\n'
        '        v3 = semaforo(Vmp_ex,  inversor["Vmppt_activo_min"], invertir=True)\n'
        '        # Check 4-Isimax: comparar contra Isc_max_tracker (cortocircuito),\n'
        '        # no contra I_max_tracker (operación/MPP). Fallback a I_max_tracker si falta.\n'
        '        _isc_lim = inversor.get("Isc_max_tracker") or inversor.get("I_max_tracker", 0)\n'
        '        v4 = semaforo(I_equiv, _isc_lim,                    invertir=False)\n'
        '        # Check 5: Vmp_real ≤ Vmppt_max — límite superior del rango MPPT.\n'
        '        # Si Vmp supera Vmppt_max el inversor opera fuera de su ventana de seguimiento.\n'
        '        _vmppt_max = inversor.get("Vmppt_max") or inversor.get("Vmppt_activo_max", 0)\n'
        '        v5 = semaforo(Vmp_re, _vmppt_max, invertir=False) if _vmppt_max else "OK"\n'
        '\n'
        '        # MPPT utilization: qué fracción del techo MPPT aprovecha este string\n'
        '        _util = round(Vmp_re / _vmppt_max * 100, 1) if _vmppt_max else 0.0\n'
        '\n'
        '        riesgos = sum(1 for v in [v1, v2, v3, v4, v5] if v in ("ALERTA", "FALLA"))\n'
        '        resultados.append(ResultadoString(\n'
        '            N_serie=N, Voc_frio=round(Voc_fr, 1), Vmp_real=round(Vmp_re, 1),\n'
        '            Vmp_extremo=round(Vmp_ex, 1), I_equiv_tracker=round(I_equiv, 2),\n'
        '            v1_voc_max=v1, v2_vmp_real=v2, v3_vmp_extr=v3, v4_i_max=v4,\n'
        '            v5_vmp_max=v5, riesgos=riesgos, mppt_util_pct=_util,\n'
        '        ))'
    ),
    desc="v5 + mppt_util_pct en optimizar_n_serie"
)

# ══════════════════════════════════════════════════════════════════════════════
# 2. pages/4_Dimensionamiento.py — tabla + criterio selección
# ══════════════════════════════════════════════════════════════════════════════
print("\n[2] pages/4_Dimensionamiento.py")

_page_files = glob.glob(str(PAGES / "*Dimensionamiento*.py"))
if not _page_files:
    print("  ❌  4_Dimensionamiento.py no encontrado")
    errors.append("Dimensionamiento no encontrado")
else:
    _page = Path(_page_files[0])

    patch(
        _page,
        buscar=(
            '            "1-Voc≤Vdc": r.v1_voc_max,\n'
            '            "2-Vmp≥Vmppt": r.v2_vmp_real,\n'
            '            "3-Vmp_ext≥Vmppt": r.v3_vmp_extr,\n'
            '            "4-I≤Imax": r.v4_i_max,\n'
            '            "Riesgos": r.riesgos,\n'
            '            "": r.semaforo_color(),\n'
            '        })'
        ),
        reemplazar=(
            '            "1-Voc≤Vdc": r.v1_voc_max,\n'
            '            "2-Vmp≥Vmppt_min": r.v2_vmp_real,\n'
            '            "3-Vmp_ext≥Vmppt_min": r.v3_vmp_extr,\n'
            '            "4-I≤Imax": r.v4_i_max,\n'
            '            "5-Vmp≤Vmppt_max": r.v5_vmp_max,\n'
            '            "MPPT util %": r.mppt_util_pct,\n'
            '            "Riesgos": r.riesgos,\n'
            '            "": r.semaforo_color(),\n'
            '        })'
        ),
        desc="columnas v5 + MPPT util %"
    )

    patch(
        _page,
        buscar=(
            '    styled = df.style.applymap(colorear,\n'
            '                                subset=["1-Voc≤Vdc", "2-Vmp≥Vmppt",\n'
            '                                        "3-Vmp_ext≥Vmppt", "4-I≤Imax"])'
        ),
        reemplazar=(
            '    styled = df.style.applymap(colorear,\n'
            '                                subset=["1-Voc≤Vdc", "2-Vmp≥Vmppt_min",\n'
            '                                        "3-Vmp_ext≥Vmppt_min", "4-I≤Imax",\n'
            '                                        "5-Vmp≤Vmppt_max"])'
        ),
        desc="styled subset v5"
    )

    patch(
        _page,
        buscar=(
            '    # Mejor opción: N con 0 riesgos y MÁXIMA Vmp (mejor aprovechamiento MPPT)\n'
            '    sin_riesgos = [r for r in resultados if r.riesgos == 0]\n'
            '    if sin_riesgos:\n'
            '        mejor = max(sin_riesgos, key=lambda r: r.Vmp_real)\n'
            '        st.success(f"✅ N óptimo = **{mejor.N_serie} paneles/string** — 0 riesgos · Vmp = {mejor.Vmp_real:.1f} V (máximo MPPT)")'
        ),
        reemplazar=(
            '    # Mejor opción: N con 0 riesgos y MÁXIMA utilización del rango MPPT\n'
            '    # (Vmp_real / Vmppt_max). Con el check v5 activo, candidatos con Vmp > Vmppt_max\n'
            '    # ya quedan excluidos por riesgos > 0, así que max(mppt_util_pct) es seguro.\n'
            '    sin_riesgos = [r for r in resultados if r.riesgos == 0]\n'
            '    if sin_riesgos:\n'
            '        mejor = max(sin_riesgos, key=lambda r: r.mppt_util_pct if r.mppt_util_pct > 0 else r.Vmp_real)\n'
            '        _util_msg = f" · {mejor.mppt_util_pct:.1f}% MPPT" if mejor.mppt_util_pct > 0 else ""\n'
            '        st.success(\n'
            '            f"✅ N óptimo = **{mejor.N_serie} paneles/string** — "\n'
            '            f"0 riesgos · Vmp = {mejor.Vmp_real:.1f} V{_util_msg}"\n'
            '        )'
        ),
        desc="criterio selección mppt_util_pct"
    )

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
if errors:
    print(f"⚠  {len(errors)} parche(s) omitidos:")
    for e in errors: print(f"   · {e}")
else:
    print("✅ Todos los parches aplicados correctamente.")
print("Próximo paso: pm2 restart streamlit-bipv")
