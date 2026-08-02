#!/usr/bin/env python3
"""
Parche: Task #64 — Invalidar recurso solar automáticamente cuando cambian las coordenadas
Aplicar en el servidor:
    cd /var/www/bipv/calculadora-bipv
    python3 bipv_python/scripts/patch_invalidar_recurso_solar_coords.py
    pm2 restart streamlit-bipv

Cambios:
  1. pages/1_Proyecto.py — cambio de ciudad: limpiar también recurso solar
     (antes solo borraba lat/lon/alt_proyecto; tmy_df y poa_df quedaban con datos viejos)

  2. pages/2_Recurso_Solar.py — constante _SOLAR_SS_KEYS con todas las keys del recurso

  3. pages/2_Recurso_Solar.py — check de invalidación al cargar la página:
     compara lat/lon/alt actuales con _solar_lat/lon/alt_guardada; si difieren
     limpia el recurso y muestra st.warning con las coords anteriores y actuales

  4. pages/2_Recurso_Solar.py — auto-restaurar desde disco: guarda
     _solar_lat/lon/alt_guardada junto al resultado para rastrear de qué coords viene

  5. pages/2_Recurso_Solar.py — ejecución exitosa de descarga: igual

  6. pages/2_Recurso_Solar.py — botón Limpiar caché: borra _solar_*_guardada
     para que la próxima ejecución las reescriba limpiamente
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
errors = []

def patch(ruta: Path, buscar: str, reemplazar: str, desc: str):
    txt = ruta.read_text(encoding="utf-8")
    if buscar not in txt:
        print(f"  ⚠  '{desc}' — fragmento NOT found (already applied?)")
        errors.append(desc); return
    ruta.write_text(txt.replace(buscar, reemplazar, 1), encoding="utf-8")
    print(f"  ✅  '{desc}'")

# ─── 1. Proyecto.py — cambio de ciudad limpia recurso solar ──────────────────
_proy = BASE / "pages" / "1_🏠_Proyecto.py"
print(f"\n[1] {_proy.name} — cambio de ciudad: limpiar recurso solar")
patch(
    _proy,
    buscar=(
        '        for _k in ("lat_proyecto", "lon_proyecto", "alt_proyecto",\n'
        '                   "densidad_Wm2", "PR", "tilt_default"):\n'
        '            st.session_state.pop(_k, None)\n'
        '        st.rerun()  # Re-render limpio para evitar DOM error al cambiar ciudad'
    ),
    reemplazar=(
        '        _KEYS_LIMPIAR_CIUDAD = (\n'
        '            "lat_proyecto", "lon_proyecto", "alt_proyecto",\n'
        '            "densidad_Wm2", "PR", "tilt_default",\n'
        '            "recurso_solar_ok", "tmy_df", "poa_df", "tmy_ciudad",\n'
        '            "tilt_fachada", "azimuth_fachada", "orientacion_label",\n'
        '            "poa_anual_kWh_m2", "ghi_anual_kWh_m2", "t_media_anual",\n'
        '            "zona_geo_coords", "poa_efectiva_df",\n'
        '            "_solar_lat_guardada", "_solar_lon_guardada", "_solar_alt_guardada",\n'
        '        )\n'
        '        for _k in _KEYS_LIMPIAR_CIUDAD:\n'
        '            st.session_state.pop(_k, None)\n'
        '        st.rerun()  # Re-render limpio para evitar DOM error al cambiar ciudad'
    ),
    desc="cambio de ciudad: limpiar recurso solar"
)

# ─── 2-3. Recurso_Solar.py — check invalidación al cargar ────────────────────
_sol = BASE / "pages" / "2_☀️_Recurso_Solar.py"
print(f"\n[2] {_sol.name} — check invalidación por coordenadas al cargar")
patch(
    _sol,
    buscar=(
        'st.markdown("---")\n'
        '\n'
        '# ── Auto-restaurar desde caché de disco (sobrevive reinicios de PM2) ─────────\n'
        '# Si los parámetros actuales coinciden con un caché en disco y la sesión aún no\n'
        '# tiene datos, restaurar silenciosamente para evitar la descarga de PVGIS.\n'
        'if not st.session_state.get("recurso_solar_ok"):'
    ),
    reemplazar=(
        'st.markdown("---")\n'
        '\n'
        '# ── #64 — Invalidar recurso solar si las coordenadas cambiaron ───────────────\n'
        '_SOLAR_SS_KEYS = (\n'
        '    "recurso_solar_ok", "tmy_df", "poa_df", "tmy_ciudad",\n'
        '    "tilt_fachada", "tilt_default", "azimuth_fachada", "orientacion_label",\n'
        '    "poa_anual_kWh_m2", "ghi_anual_kWh_m2", "t_media_anual",\n'
        '    "zona_geo_coords", "poa_efectiva_df",\n'
        ')\n'
        '_s_lat = st.session_state.get("_solar_lat_guardada")\n'
        '_s_lon = st.session_state.get("_solar_lon_guardada")\n'
        '_s_alt = st.session_state.get("_solar_alt_guardada")\n'
        'if st.session_state.get("recurso_solar_ok") and _s_lat is not None:\n'
        '    _drift = (\n'
        '        abs(lat - float(_s_lat)) > 0.0001 or\n'
        '        abs(lon - float(_s_lon)) > 0.0001 or\n'
        '        abs(alt_m - int(_s_alt))  > 10\n'
        '    )\n'
        '    if _drift:\n'
        '        for _k in _SOLAR_SS_KEYS:\n'
        '            st.session_state.pop(_k, None)\n'
        '        for _k in ("_solar_lat_guardada", "_solar_lon_guardada", "_solar_alt_guardada"):\n'
        '            st.session_state.pop(_k, None)\n'
        '        st.warning(\n'
        '            f"⚠️ **Recurso solar invalidado** — las coordenadas del proyecto cambiaron.  \\n"\n'
        '            f"Recurso calculado para: **{float(_s_lat):.5f}°**, **{float(_s_lon):.5f}°**, "\n'
        '            f"**{int(_s_alt)} m**  \\n"\n'
        '            f"Coordenadas actuales: **{lat:.5f}°**, **{lon:.5f}°**, **{alt_m} m**  \\n"\n'
        '            "Presiona **🌐 Descargar TMY de PVGIS** para recalcular con las coordenadas actuales."\n'
        '        )\n'
        '\n'
        '# ── Auto-restaurar desde caché de disco (sobrevive reinicios de PM2) ─────────\n'
        '# Si los parámetros actuales coinciden con un caché en disco y la sesión aún no\n'
        '# tiene datos, restaurar silenciosamente para evitar la descarga de PVGIS.\n'
        'if not st.session_state.get("recurso_solar_ok"):'
    ),
    desc="check invalidación por coordenadas"
)

print(f"\n[3] {_sol.name} — auto-restaurar: guardar _solar_*_guardada")
patch(
    _sol,
    buscar=(
        '            "zona_geo_coords":     _zona_por_coords_rs(lat, lon),\n'
        '            "recurso_solar_ok":    True,\n'
        '        })'
    ),
    reemplazar=(
        '            "zona_geo_coords":     _zona_por_coords_rs(lat, lon),\n'
        '            "recurso_solar_ok":    True,\n'
        '            "_solar_lat_guardada": lat,\n'
        '            "_solar_lon_guardada": lon,\n'
        '            "_solar_alt_guardada": alt_m,\n'
        '        })'
    ),
    desc="auto-restaurar: guardar _solar_*_guardada"
)

print(f"\n[4] {_sol.name} — ejecución exitosa: guardar _solar_*_guardada")
patch(
    _sol,
    buscar=(
        '    st.session_state["recurso_solar_ok"]  = True\n'
        '    # ── #64 — Guardar coords usadas para detectar drift futuro ───────────────\n'
        '    st.session_state["_solar_lat_guardada"] = lat\n'
        '    st.session_state["_solar_lon_guardada"] = lon\n'
        '    st.session_state["_solar_alt_guardada"] = alt_m'
    ),
    reemplazar=(
        '    st.session_state["recurso_solar_ok"]    = True\n'
        '    st.session_state["_solar_lat_guardada"] = lat\n'
        '    st.session_state["_solar_lon_guardada"] = lon\n'
        '    st.session_state["_solar_alt_guardada"] = alt_m'
    ),
    desc="ejecución exitosa: guardar _solar_*_guardada"
)

print(f"\n[5] {_sol.name} — botón Limpiar caché: borrar _solar_*_guardada")
patch(
    _sol,
    buscar=(
        '    st.session_state["recurso_solar_ok"] = False\n'
        '    # ── #64 — Limpiar coords guardadas para que la próxima ejecución las reescriba\n'
        '    for _k in ("_solar_lat_guardada", "_solar_lon_guardada", "_solar_alt_guardada"):\n'
        '        st.session_state.pop(_k, None)\n'
        '    st.success("✅ Caché limpiada — presiona **Descargar TMY** para obtener datos frescos.")'
    ),
    reemplazar=(
        '    st.session_state["recurso_solar_ok"] = False\n'
        '    for _k in ("_solar_lat_guardada", "_solar_lon_guardada", "_solar_alt_guardada"):\n'
        '        st.session_state.pop(_k, None)\n'
        '    st.success("✅ Caché limpiada — presiona **Descargar TMY** para obtener datos frescos.")'
    ),
    desc="botón limpiar caché: borrar _solar_*_guardada"
)

print("\n" + "="*60)
if errors:
    print(f"⚠  {len(errors)} parche(s) omitidos:"); [print(f"   · {e}") for e in errors]
else:
    print("✅ Todos los parches aplicados correctamente.")
print("Próximo paso: pm2 restart streamlit-bipv")
