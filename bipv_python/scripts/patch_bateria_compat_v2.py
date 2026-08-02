#!/usr/bin/env python3
"""
Parche: Task #25 — Alertar cuando la batería es incompatible con el inversor (v2)
Aplicar en el servidor:
    cd /var/www/bipv/calculadora-bipv
    python3 bipv_python/scripts/patch_bateria_compat_v2.py
    pm2 restart streamlit-bipv

Mejoras sobre el check original:
  4. Batería LV (≤80 V) con híbrido que solo acepta HV (SPH/SPA/SUN2000/Sungrow)
  5. Inversor híbrido pero batería sin voltaje definido en el catálogo → aviso claro
  6. Mensajes mejorados con instrucciones concretas
  7. Check POST-dimensionamiento: N_baterias × potencia_kW vs P_ac_nom inversor
"""
import glob
from pathlib import Path

BASE  = Path(__file__).resolve().parent.parent
PAGES = BASE / "pages"
errors = []

def patch(ruta: Path, buscar: str, reemplazar: str, desc: str):
    txt = ruta.read_text(encoding="utf-8")
    if buscar not in txt:
        print(f"  ⚠  '{desc}' — fragmento NOT found (already applied?)")
        errors.append(desc); return
    ruta.write_text(txt.replace(buscar, reemplazar, 1), encoding="utf-8")
    print(f"  ✅  '{desc}'")

_bat_files = glob.glob(str(PAGES / "*Baterias*Balance*.py"))
if not _bat_files:
    print("❌  11_Baterias_y_Balance.py no encontrado"); raise SystemExit(1)
_bat = Path(_bat_files[0])

print(f"\n[1] {_bat.name} — ampliar _check_compatibilidad (checks 4, 5 + mensajes mejorados)")
patch(
    _bat,
    buscar=(
        '            # 3. HV check: si no hay info de rango pero la batería es HV y el inversor no parece híbrido\n'
        '            if not tipo_inv and not es_string and bat_v and bat_v > 150:\n'
        '                motivos.append(\n'
        '                    f"La batería es **alta tensión ({bat_v:.0f} V)**. "\n'
        '                    "Confirme que el inversor seleccionado es híbrido y soporta ese rango de voltaje."\n'
        '                )\n'
        '\n'
        '            if motivos:\n'
        '                return "error", "🔴 **Incompatibilidad detectada:**\\n" + "\\n".join(f"- {m}" for m in motivos)\n'
        '            elif tipo_inv and bat_v:\n'
        '                if bat_v_min and bat_v_max:\n'
        '                    return "ok", (\n'
        '                        f"✅ Inversor híbrido · Voltaje batería {bat_v:.0f} V ✓ "\n'
        '                        f"dentro del rango {bat_v_min:.0f}–{bat_v_max:.0f} V"\n'
        '                    )\n'
        '                return "ok", f"✅ Inversor híbrido compatible con baterías ({inv_nom})"\n'
        '            elif not _inv_dim and not inv_nom:\n'
        '                return "warning", (\n'
        '                    "ℹ️ Selecciona el inversor en Página 4 para verificar la compatibilidad."\n'
        '                )\n'
        '            else:\n'
        '                return "warning", (\n'
        '                    f"⚠️ No se puede verificar la compatibilidad automáticamente para **{inv_nom}**. "\n'
        '                    + (f"Voltaje de batería: **{bat_v:.0f} V**. " if bat_v else "")\n'
        '                    + "Confirme con el fabricante del inversor que acepta batería externa."\n'
        '                )'
    ),
    reemplazar=(
        '            # 3. Batería HV con inversor no identificado como híbrido\n'
        '            if not tipo_inv and not es_string and bat_v and bat_v > 150:\n'
        '                motivos.append(\n'
        '                    f"La batería es **alta tensión ({bat_v:.0f} V)**. "\n'
        '                    "Confirme que el inversor seleccionado es **híbrido** y soporta ese rango de voltaje."\n'
        '                )\n'
        '\n'
        '            # 4. Batería LV (≤ 80 V) con híbrido que normalmente requiere HV\n'
        '            _hv_only_heuristic = any(x in inv_lower for x in\n'
        '                                     ["sph", "spa", "sun2000", "sungrow", "sh-", "x-hybrid", "solax"])\n'
        '            if tipo_inv and bat_v and bat_v <= 80 and not bat_v_min and _hv_only_heuristic:\n'
        '                motivos.append(\n'
        '                    f"La batería es de **baja tensión ({bat_v:.0f} V)** y **`{inv_nom}`** "\n'
        '                    "normalmente requiere bancos de **alta tensión (100–550 V)**. "\n'
        '                    "Verifique el rango de tensión DC de batería en la ficha técnica del inversor."\n'
        '                )\n'
        '\n'
        '            # 5. Inversor híbrido pero la batería no tiene voltaje definido en el catálogo\n'
        '            if tipo_inv and not bat_v and not motivos:\n'
        '                return "warning", (\n'
        '                    f"⚠️ **Inversor híbrido detectado ({inv_nom})** pero la batería no tiene "\n'
        '                    "**voltaje definido** en el catálogo.  \\n"\n'
        '                    "- Agregue `Voltaje Nominal (V)` en la hoja `Catalogo_Baterias` del Excel "\n'
        '                    "para verificar compatibilidad de tensión automáticamente."\n'
        '                )\n'
        '\n'
        '            if motivos:\n'
        '                return "error", "🔴 **Incompatibilidad detectada:**\\n" + "\\n".join(f"- {m}" for m in motivos)\n'
        '            elif tipo_inv and bat_v:\n'
        '                if bat_v_min and bat_v_max:\n'
        '                    return "ok", (\n'
        '                        f"✅ Inversor híbrido · Voltaje batería **{bat_v:.0f} V** ✓ "\n'
        '                        f"dentro del rango admitido **{bat_v_min:.0f}–{bat_v_max:.0f} V**"\n'
        '                    )\n'
        '                return "ok", (\n'
        '                    f"✅ Inversor híbrido detectado (**{inv_nom}**) · Voltaje batería {bat_v:.0f} V  \\n"\n'
        '                    "*(Rango DC de batería no definido en el catálogo — verifique la ficha del inversor.)*"\n'
        '                )\n'
        '            elif not _inv_dim and not inv_nom:\n'
        '                return "warning", (\n'
        '                    "ℹ️ Selecciona el inversor en **Página 4 › Dimensionamiento** para "\n'
        '                    "verificar la compatibilidad antes de dimensionar."\n'
        '                )\n'
        '            else:\n'
        '                return "warning", (\n'
        '                    f"⚠️ No se pudo determinar el tipo de **`{inv_nom}`** automáticamente.  \\n"\n'
        '                    + (f"Voltaje de batería: **{bat_v:.0f} V**.  \\n" if bat_v else "")\n'
        '                    + "Confirme en la ficha del inversor que tiene **puerto DC para batería** "\n'
        '                    "y que el rango de tensión es compatible."\n'
        '                )'
    ),
    desc="checks 4+5 + mensajes mejorados"
)

print(f"\n[2] {_bat.name} — check potencia post-dimensionamiento")
patch(
    _bat,
    buscar=(
        '    for adv in dim_res.get("advertencias", []):\n'
        '        st.warning(f"⚠️ {adv}")\n'
        '\n'
        '    with st.expander("📐 Tabla de dimensionamiento detallada"):'
    ),
    reemplazar=(
        '    for adv in dim_res.get("advertencias", []):\n'
        '        st.warning(f"⚠️ {adv}")\n'
        '\n'
        '    # ── #25 — Check potencia post-dimensionamiento ────────────────────────────\n'
        '    _n_bat       = dim_res.get("N_baterias", 1)\n'
        '    _p_bat_unit  = bat.get("potencia_kW") or 0\n'
        '    _p_bat_total = _n_bat * _p_bat_unit\n'
        '    _p_inv_w     = (_inv_dim.get("P_ac_nom_W") or _inv_dim.get("P_dc_max_W") or 0)\n'
        '    _p_inv_kw    = _p_inv_w / 1000\n'
        '    if _p_bat_total > 0 and _p_inv_kw > 0:\n'
        '        _ratio = _p_bat_total / _p_inv_kw\n'
        '        if _ratio > 1.5:\n'
        '            st.error(\n'
        '                f"🔴 **Potencia del banco sobredimensionada:** {_n_bat} × {_p_bat_unit:.1f} kW = "\n'
        '                f"**{_p_bat_total:.1f} kW** vs inversor **{_p_inv_kw:.1f} kW**.  \\n"\n'
        '                f"El inversor limitará la carga/descarga — considera reducir unidades o "\n'
        '                "usar un inversor de mayor potencia."\n'
        '            )\n'
        '        elif _ratio > 1.1:\n'
        '            st.warning(\n'
        '                f"⚠️ **Potencia del banco ({_p_bat_total:.1f} kW) supera la del inversor "\n'
        '                f"({_p_inv_kw:.1f} kW) en {(_ratio-1)*100:.0f}%.** "\n'
        '                "El inversor será el cuello de botella en picos de carga/descarga."\n'
        '            )\n'
        '        else:\n'
        '            st.info(\n'
        '                f"⚡ Potencia del banco: **{_p_bat_total:.1f} kW** "\n'
        '                f"({_n_bat} × {_p_bat_unit:.1f} kW) — "\n'
        '                f"dentro de la capacidad del inversor ({_p_inv_kw:.1f} kW)."\n'
        '            )\n'
        '\n'
        '    with st.expander("📐 Tabla de dimensionamiento detallada"):'
    ),
    desc="check potencia post-dimensionamiento"
)

print("\n" + "="*60)
if errors:
    print(f"⚠  {len(errors)} parche(s) omitidos:"); [print(f"   · {e}") for e in errors]
else:
    print("✅ Todos los parches aplicados correctamente.")
print("Próximo paso: pm2 restart streamlit-bipv")
