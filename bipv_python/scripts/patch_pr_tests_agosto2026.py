#!/usr/bin/env python3
"""
Parche: Task #99 + #100 — PR IEC 61724 y tests temperatura campo
Aplicar en el servidor:
    cd /var/www/bipv/calculadora-bipv
    python3 bipv_python/scripts/patch_pr_tests_agosto2026.py
    pm2 restart streamlit-bipv

Cambios:
  1. 6_Produccion.py  — tooltip PR ampliado + alertas rango + tabla Colombia BIPV
  2. tests/test_validacion_vba.py — 4 tests nuevos: Isc(T) y pendiente alpha_sc
  3. calculos/modelo_iv.py       — fix numpy 2.x: rsh.item() en lugar de float(rsh)
"""
from pathlib import Path

BASE  = Path(__file__).resolve().parent.parent
PAGES = BASE / "pages"
TESTS = BASE / "tests"
CALC  = BASE / "calculos"

errors = []

def patch(ruta, buscar, reemplazar, desc):
    txt = ruta.read_text(encoding="utf-8")
    if buscar not in txt:
        print(f"  ⚠  '{desc}' — fragmento NOT found (already applied?)")
        errors.append(desc)
        return
    ruta.write_text(txt.replace(buscar, reemplazar, 1), encoding="utf-8")
    print(f"  ✅  '{desc}' → {ruta.name}")


# ══════════════════════════════════════════════════════════════════════════════
# 1. 6_Produccion.py — tooltip PR + alertas de rango
# ══════════════════════════════════════════════════════════════════════════════
print("\n[1] 6_Produccion.py — tooltip PR y alertas de rango")

_prod = None
for _p in PAGES.iterdir():
    if "Produccion" in _p.name or "Producción" in _p.name:
        _prod = _p; break

if not _prod:
    print("  ❌  Produccion.py no encontrado"); errors.append("Produccion no encontrado")
else:
    patch(
        _prod,
        buscar='    m5.metric("PR (Perf. Ratio)",  f"{res[\'PR\']*100:.1f}%",\n'
               '              help="Performance Ratio IEC 61724 = Y_f / Y_r. Bueno: >75%")\n'
               '    m6.metric("Factor de Planta",  f"{res[\'CF_pct\']:.1f}%",\n'
               '              help="Capacity Factor = E_ac / (P_STC × 8760 h)")\n'
               '\n'
               '    # ── Gráfica mensual ───────────────────────────────────────────────────────\n'
               '    st.subheader("📅 Producción mensual")',
        reemplazar=(
            '    m5.metric("PR (Perf. Ratio)",  f"{res[\'PR\']*100:.1f}%",\n'
            '              help=(\n'
            '                  "**Performance Ratio IEC 61724**  \\n"\n'
            '                  "PR = Y_f / Y_r = E_ac / (P_stc × H_POA_bruta)  \\n\\n"\n'
            '                  "Mide la eficiencia global del sistema frente a su potencial teórico "\n'
            '                  "(irradiancia × potencia nominal).  \\n\\n"\n'
            '                  "**Rangos típicos Colombia BIPV:**  \\n"\n'
            '                  "· Fachada vertical: 55–70 %  \\n"\n'
            '                  "· Techo inclinado optimizado: 70–80 %  \\n"\n'
            '                  "· PR > 100 %: normal en climas fríos (Bogotá, Manizales) — "\n'
            '                  "los módulos CdTe ganan eficiencia por debajo de 25 °C"\n'
            '              ))\n'
            '    m6.metric("Factor de Planta",  f"{res[\'CF_pct\']:.1f}%",\n'
            '              help="Capacity Factor = E_ac / (P_STC × 8760 h)")\n'
            '\n'
            '    # ── Alertas de rango PR IEC 61724 ─────────────────────────────────────────\n'
            '    _pr_pct = res["PR"] * 100\n'
            '    if _pr_pct < 50:\n'
            '        st.error(\n'
            '            f"🔴 **PR = {_pr_pct:.1f}% — MUY BAJO (< 50%).**  \\n"\n'
            '            "Posibles causas: inversor sobredimensionado, pérdidas de cableado altas, "\n'
            '            "paneles degradados o datos de entrada inconsistentes.  \\n"\n'
            '            "Revisa la simulación antes de utilizarla en un análisis financiero."\n'
            '        )\n'
            '    elif _pr_pct < 60:\n'
            '        st.warning(\n'
            '            f"⚠️ **PR = {_pr_pct:.1f}% — por debajo del rango típico Colombia BIPV (60–75%).**  \\n"\n'
            '            "Para fachadas verticales con orientación desfavorable puede ser esperado. "\n'
            '            "Verifica la orientación, inclinación y las pérdidas del sistema."\n'
            '        )\n'
            '    elif 90 < _pr_pct <= 100:\n'
            '        st.warning(\n'
            '            f"⚠️ **PR = {_pr_pct:.1f}% — alto (> 90%).**  \\n"\n'
            '            "Verifica que la potencia nominal del sistema y la POA de referencia sean correctas. "\n'
            '            "PR > 90 % es inusual en zonas tropicales — si no estás en clima frío de altitud, revisa los datos."\n'
            '        )\n'
            '    # PR > 100%: ya se maneja abajo con contexto de sobre-rendimiento en climas fríos\n'
            '\n'
            '    # ── Gráfica mensual ───────────────────────────────────────────────────────\n'
            '    st.subheader("📅 Producción mensual")'
        ),
        desc="tooltip PR + alertas rango"
    )

    patch(
        _prod,
        buscar=(
            '| **PR convencional** | E_real ÷ (P_STC × HSP) | PR estándar IEC 61724 — incluye **todas** las pérdidas (temperatura + eléctricas + ópticas) |\n'
            '| **% Pérdidas T°** | (1 − factor_T) × 100 | Cuánto pierde el sistema **solo por calor** = γ × (T_cell − 25°C) |\n'
            '| **PR corregido T°** | PR_conv ÷ factor_T | PR sin efecto temperatura — revela las **pérdidas reales** (suciedad, sombras, degradación, cableado) |\n'
            '\n'
            '*factor_T = 1 + γ × (T_cell_media − 25°C)   ·   γ = coeficiente de temperatura de Pmax del panel*\n'
            '\n'
            '**Regla de diagnóstico:**\n'
            '- Si PR_corr ≈ PR_conv → temperatura no es el problema principal; buscar fallas mecánicas/eléctricas\n'
            '- Si PR_corr >> PR_conv → temperatura está consumiendo una fracción importante de la producción (común en BIPV fachada)\n'
            '- Si PR_corr < 0.85 → existen pérdidas no térmicas significativas (suciedad, sombras, degradación, strings)\n'
            '        """)'
        ),
        reemplazar=(
            '| **PR convencional** | E_real ÷ (P_STC × HSP) | PR estándar IEC 61724 — incluye **todas** las pérdidas (temperatura + eléctricas + ópticas) |\n'
            '| **% Pérdidas T°** | (1 − factor_T) × 100 | Cuánto pierde el sistema **solo por calor** = γ × (T_cell − 25°C) |\n'
            '| **PR corregido T°** | PR_conv ÷ factor_T | PR sin efecto temperatura — revela las **pérdidas reales** (suciedad, sombras, degradación, cableado) |\n'
            '\n'
            '*factor_T = 1 + γ × (T_cell_media − 25°C)   ·   γ = coeficiente de temperatura de Pmax del panel*\n'
            '\n'
            '**Regla de diagnóstico:**\n'
            '- Si PR_corr ≈ PR_conv → temperatura no es el problema principal; buscar fallas mecánicas/eléctricas\n'
            '- Si PR_corr >> PR_conv → temperatura está consumiendo una fracción importante de la producción (común en BIPV fachada)\n'
            '- Si PR_corr < 0.85 → existen pérdidas no térmicas significativas (suciedad, sombras, degradación, strings)\n'
            '\n'
            '---\n'
            '**Referencia IEC 61724 — rangos Colombia BIPV:**\n'
            '\n'
            '| Tipo de sistema | PR típico | Nota |\n'
            '|---|---|---|\n'
            '| Fachada vertical (Sur/Occidente) | 55–65 % | Ángulo de incidencia alto → menor captura |\n'
            '| Fachada vertical (Norte/Oriente) | 60–70 % | Mejor orientación para Colombia |\n'
            '| Techo inclinado 15–25° | 70–80 % | Óptimo para la latitud colombiana |\n'
            '| Pérgola / sombreadero | 65–75 % | Depende de la inclinación |\n'
            '| PR < 50 % | ⚠️ Revisar | Posible error de datos o pérdidas anómalas |\n'
            '| PR > 90 % | ⚠️ Verificar | Inusual en zonas tropicales |\n'
            '| PR > 100 % | ✅ Normal frío | Climas Andinos > 2 000 m (Bogotá, Manizales, Pasto) |\n'
            '\n'
            '*Fuente: UPME / CREG, proyectos BIPV Colombia 2022–2025.*\n'
            '        """)'
        ),
        desc="tabla Colombia BIPV en expander"
    )

# ══════════════════════════════════════════════════════════════════════════════
# 2. tests/test_validacion_vba.py — tests Isc(T) + pendiente alpha_sc
# ══════════════════════════════════════════════════════════════════════════════
print("\n[2] tests/test_validacion_vba.py — tests temperatura campo")

_test_file = TESTS / "test_validacion_vba.py"
if not _test_file.exists():
    print("  ❌  test_validacion_vba.py no encontrado"); errors.append("tests no encontrado")
else:
    patch(
        _test_file,
        buscar=(
            'def test_vmp_n8_vs_xlsm():\n'
            '    """Vmp realista con N=8 debe ser 666.0V ± 2V (hoja Resultado_Dim_String del XLSM)."""\n'
            '    from calculos.dimensionamiento import calcular_vmp_string\n'
            '    Vmp = calcular_vmp_string(8, ASP_ST1_T40["Vmp_stc"], ASP_ST1_T40["Tk_gamma"], 36.35)\n'
            '    assert abs(Vmp - 666.0) < 2.0, f"Vmp={Vmp:.1f}V vs VBA=666.0V"'
        ),
        reemplazar=(
            'def test_vmp_n8_vs_xlsm():\n'
            '    """Vmp realista con N=8 debe ser 666.0V ± 2V (hoja Resultado_Dim_String del XLSM)."""\n'
            '    from calculos.dimensionamiento import calcular_vmp_string\n'
            '    Vmp = calcular_vmp_string(8, ASP_ST1_T40["Vmp_stc"], ASP_ST1_T40["Tk_gamma"], 36.35)\n'
            '    assert abs(Vmp - 666.0) < 2.0, f"Vmp={Vmp:.1f}V vs VBA=666.0V"\n'
            '\n'
            '\n'
            '# ── Tests anti-regresión: curva IV a temperaturas de campo ────────────────────\n'
            '#\n'
            '# El bug histórico (agosto 2026) calculaba alpha_sc = Tk_alfa/100 (%/°C)\n'
            '# en lugar de alpha_sc = Tk_alfa/100 × Isc_stc (A/°C).\n'
            '# Para CdTe con Isc_stc=0.80: error = 25 % en alpha_sc, ~ 0.5 % en Isc a 60 °C.\n'
            '# Para Si con Isc_stc≈10 A:   error = ~10× en alpha_sc, ~10 % en Isc a 60 °C.\n'
            '#\n'
            '# Valores de referencia (alpha_sc_correcto = 0.060/100 × 0.80 = 0.000480 A/°C):\n'
            '#   T=45°C (ΔT=20): Isc_ref = 0.8000 + 0.000480×20 = 0.80960 A\n'
            '#   T=60°C (ΔT=35): Isc_ref = 0.8000 + 0.000480×35 = 0.81680 A\n'
            '\n'
            '@pytest.mark.parametrize("T_cel_C, Isc_ref", [\n'
            '    (25.0, 0.80000),   # STC — sin ΔT, validación baseline\n'
            '    (45.0, 0.80960),   # ΔT = +20 °C\n'
            '    (60.0, 0.81680),   # ΔT = +35 °C  ← error bug = 0.53 % > tolerancia 0.5 %\n'
            '])\n'
            'def test_isc_temperatura_campo(T_cel_C, Isc_ref):\n'
            '    """Isc a temperatura de campo debe seguir alpha_sc = Tk_alfa/100 × Isc_stc (A/°C).\n'
            '\n'
            '    Con el bug histórico alpha_sc sería Tk_alfa/100 = 0.000600 A/°C en lugar de\n'
            '    0.000480 A/°C, dando a T=60°C: Isc=0.8210 A en vez de 0.8168 A (error 0.53 %).\n'
            '    """\n'
            '    res = resolver_curva_iv(1000.0, T_cel_C, ASP_ST1_T40, n_puntos=0)\n'
            '    err_pct = abs(res["Isc"] - Isc_ref) / ASP_ST1_T40["Isc_stc"] * 100\n'
            '    assert err_pct < 0.5, (\n'
            '        f"T={T_cel_C}°C: Isc={res[\'Isc\']:.5f} A  ref={Isc_ref:.5f} A  "\n'
            '        f"error={err_pct:.3f}% > 0.5 % de Isc_stc.  "\n'
            '        f"Causa probable: alpha_sc usa Tk_alfa/100 en lugar de Tk_alfa/100 × Isc_stc."\n'
            '    )\n'
            '\n'
            '\n'
            'def test_alpha_sc_pendiente():\n'
            '    """La pendiente dIsc/dT debe coincidir con alpha_sc = Tk_alfa/100 × Isc_stc.\n'
            '\n'
            '    Con el bug, la pendiente sería Tk_alfa/100 = 0.000600 A/°C (25 % mayor que el\n'
            '    valor correcto 0.000480 A/°C). Tolerancia del test: 5 % relativo sobre la pendiente.\n'
            '    """\n'
            '    res_25 = resolver_curva_iv(1000.0, 25.0, ASP_ST1_T40, n_puntos=0)\n'
            '    res_60 = resolver_curva_iv(1000.0, 60.0, ASP_ST1_T40, n_puntos=0)\n'
            '    pendiente_medida  = (res_60["Isc"] - res_25["Isc"]) / (60.0 - 25.0)   # A/°C\n'
            '    alpha_sc_correcto = ASP_ST1_T40["Tk_alfa"] / 100.0 * ASP_ST1_T40["Isc_stc"]\n'
            '    error_rel_pct     = abs(pendiente_medida - alpha_sc_correcto) / alpha_sc_correcto * 100\n'
            '    assert error_rel_pct < 5.0, (\n'
            '        f"Pendiente dIsc/dT medida = {pendiente_medida:.6f} A/°C  "\n'
            '        f"vs alpha_sc correcto = {alpha_sc_correcto:.6f} A/°C  "\n'
            '        f"(error relativo = {error_rel_pct:.1f}% > 5%).  "\n'
            '        f"Con el bug histórico el error sería ~25 %."\n'
            '    )'
        ),
        desc="tests temperatura campo alpha_sc"
    )

# ══════════════════════════════════════════════════════════════════════════════
# 3. calculos/modelo_iv.py — fix numpy 2.x (rsh.item() en lugar de float(rsh))
# ══════════════════════════════════════════════════════════════════════════════
print("\n[3] calculos/modelo_iv.py — fix numpy 2.x compatibilidad")

patch(
    CALC / "modelo_iv.py",
    buscar='    return float(rsh) if rsh.size == 1 else rsh',
    reemplazar='    return rsh.item() if rsh.size == 1 else rsh   # .item() compatible numpy 1.x y 2.x',
    desc="numpy 2.x rsh.item()"
)

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
if errors:
    print(f"⚠  {len(errors)} parche(s) omitidos (ya aplicados o fragmento no encontrado):")
    for e in errors: print(f"   · {e}")
else:
    print("✅ Todos los parches aplicados correctamente.")
print("Próximo paso: pm2 restart streamlit-bipv")
