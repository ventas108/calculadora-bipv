#!/usr/bin/env python3
"""
Parche: Task #81 — Avisar cuando Costos Blandos están incompletos
                   antes de enviar el presupuesto a Financiero
Aplicar en el servidor:
    cd /var/www/bipv/calculadora-bipv
    python3 bipv_python/scripts/patch_costos_blandos_aviso.py
    pm2 restart streamlit-bipv

Cambios:
  1. pages/8_Presupuesto.py — Resumen CAPEX (cotización real):
     Después del st.success final, si sub6==0 y capex_directo>0, muestra
     st.warning con el rango de referencia 10–20% del CAPEX directo y
     enlace a la pestaña de Costos Blandos.

  2. pages/7_Financiero.py — desglose del Presupuesto:
     Después del st.success de CAPEX activo, si _ppto_blando==0 y
     _ppto_directo>0, muestra st.warning con los mismos rangos de referencia.
"""
from pathlib import Path

BASE  = Path(__file__).resolve().parent.parent
PRES  = BASE / "pages" / "8_💼_Presupuesto.py"
FIN   = BASE / "pages" / "7_💰_Financiero.py"
errors = []

def patch(ruta, buscar, reemplazar, desc):
    txt = ruta.read_text(encoding="utf-8")
    if buscar not in txt:
        print(f"  ⚠  '{desc}' — fragmento NOT found (already applied?)")
        errors.append(desc); return
    ruta.write_text(txt.replace(buscar, reemplazar, 1), encoding="utf-8")
    print(f"  ✅  '{desc}'")

# ── 1. Presupuesto — Resumen: aviso blandos vacíos ───────────────────────────
print(f"\n[1] {PRES.name} — aviso blandos vacíos en Resumen")
patch(
    PRES,
    buscar=(
        '    st.success(\n'
        '        f"✅ **CAPEX TOTAL USD {capex_total:,.0f}** ($ {capex_total*tc/1e6:.2f} M COP) "\n'
        '        f"→ 💰 Financiero lo usa automáticamente. "\n'
        '        f"Ley 1715 frac. equipos: **{_frac_eq*100:.0f}%**"\n'
        '        + (f" · **OPEX USD {sub7:,.0f}/año** enviado al flujo de caja." if sub7 > 0 else\n'
        '           " · ⚠️ OPEX = USD 0 — completa la pestaña 📅 OPEX Anual.")\n'
        '    )\n'
    ),
    reemplazar=(
        '    st.success(\n'
        '        f"✅ **CAPEX TOTAL USD {capex_total:,.0f}** ($ {capex_total*tc/1e6:.2f} M COP) "\n'
        '        f"→ 💰 Financiero lo usa automáticamente. "\n'
        '        f"Ley 1715 frac. equipos: **{_frac_eq*100:.0f}%**"\n'
        '        + (f" · **OPEX USD {sub7:,.0f}/año** enviado al flujo de caja." if sub7 > 0 else\n'
        '           " · ⚠️ OPEX = USD 0 — completa la pestaña 📅 OPEX Anual.")\n'
        '    )\n'
        '\n'
        '    # ── #81 — Avisar si Costos Blandos están vacíos en modo cotización real ────\n'
        '    if sub6 == 0 and capex_directo > 0:\n'
        '        _ref_blando_lo = capex_directo * 0.10\n'
        '        _ref_blando_hi = capex_directo * 0.20\n'
        '        st.warning(\n'
        '            f"⚠️ **Costos Blandos = USD 0** — la pestaña 🧾 Costos Blandos está vacía. "\n'
        '            f"Para un presupuesto bancable, ingeniería, permisos RETIE/UPME, PM y seguros "\n'
        '            f"representan el **10–20% del CAPEX directo** "\n'
        '            f"(≈ USD {{_ref_blando_lo:,.0f}} – USD {{_ref_blando_hi:,.0f}} para este proyecto).  \\n"\n'
        '            f"Ve a la pestaña **🧾 Costos Blandos** → **🪄 Sugerir valores conservadores** para completarlos "\n'
        '            f"antes de enviar el presupuesto a Financiero."\n'
        '        )\n'
    ),
    desc="Resumen: aviso blandos vacíos"
)

# ── 2. Financiero — desglose presupuesto: aviso blandos vacíos ───────────────
print(f"\n[2] {FIN.name} — aviso blandos vacíos en desglose presupuesto")
patch(
    FIN,
    buscar=(
        '        st.success(\n'
        '            f"✅ CAPEX activo: **USD {capex_total:,.0f}** "\n'
        '            f"($ {capex_total * _tc0 / 1e6:.2f} M COP) — desde 💼 Presupuesto detallado"\n'
        '        )\n'
    ),
    reemplazar=(
        '        st.success(\n'
        '            f"✅ CAPEX activo: **USD {capex_total:,.0f}** "\n'
        '            f"($ {capex_total * _tc0 / 1e6:.2f} M COP) — desde 💼 Presupuesto detallado"\n'
        '        )\n'
        '        # ── #81 — Avisar si Costos Blandos están vacíos en el Presupuesto ─────\n'
        '        if _ppto_blando == 0 and _ppto_directo > 0:\n'
        '            st.warning(\n'
        '                f"⚠️ **Costos Blandos = USD 0** en el Presupuesto — ingeniería, permisos "\n'
        '                f"RETIE/UPME, PM y seguros de construcción no están incluidos en el CAPEX.  \\n"\n'
        '                f"Referencia Colombia: **10–20% del CAPEX directo** "\n'
        '                f"(≈ USD {{_ppto_directo*0.10:,.0f}} – USD {{_ppto_directo*0.20:,.0f}}).  \\n"\n'
        '                f"Ve a 💼 **Presupuesto → 🧾 Costos Blandos → 🪄 Sugerir valores** para completarlos."\n'
        '            )\n'
    ),
    desc="Financiero: aviso blandos vacíos"
)

print("\n" + "="*60)
if errors:
    print(f"⚠  {len(errors)} parche(s) omitidos:"); [print(f"   · {e}") for e in errors]
else:
    print("✅ Todos los parches aplicados.")
print("Próximo paso: pm2 restart streamlit-bipv")
