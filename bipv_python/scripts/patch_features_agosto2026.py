#!/usr/bin/env python3
"""
Parche: 4 nuevas funciones — agosto 2026
Aplicar en el servidor:
    cd /var/www/bipv/calculadora-bipv
    python3 bipv_python/scripts/patch_features_agosto2026.py
    pm2 restart streamlit-bipv

Funciones agregadas:
  1. ciudades_colombia.py  — Apartadó/Urabá como ciudad propia + FECHA_VALIDACION_TARIFAS
  2. 1_Proyecto.py         — Aviso cuando tarifas llevan >6 meses sin actualizar
  3. 2_Recurso_Solar.py    — Caché de disco TMY+POA (sobrevive reinicios PM2)
  4. 8_Presupuesto.py      — Zona geográfica Estimación Rápida se sincroniza con
                             lat/lon del proyecto sin requerir ejecutar Recurso Solar
"""
import sys
from pathlib import Path

BASE    = Path(__file__).resolve().parent.parent   # bipv_python/
DATOS   = BASE / "datos"
PAGES   = BASE / "pages"
SCRIPTS = BASE / "scripts"

def patch(ruta: Path, buscar: str, reemplazar: str, desc: str) -> bool:
    txt = ruta.read_text(encoding="utf-8")
    if buscar not in txt:
        print(f"  ⚠  '{desc}' — fragmento NOT found in {ruta.name} (already applied?)")
        return False
    ruta.write_text(txt.replace(buscar, reemplazar, 1), encoding="utf-8")
    print(f"  ✅  '{desc}' → {ruta.name}")
    return True

errors = []

# ══════════════════════════════════════════════════════════════════════════════
# 1. ciudades_colombia.py — FECHA_VALIDACION_TARIFAS + Apartadó (Urabá)
# ══════════════════════════════════════════════════════════════════════════════
print("\n[1] ciudades_colombia.py — Apartadó + FECHA_VALIDACION_TARIFAS")
ok = patch(
    DATOS / "ciudades_colombia.py",
    buscar=
        '"""\n'
        '\n'
        'CIUDADES = {',
    reemplazar=
        '"""\n'
        '\n'
        '# Fecha de la última validación de tarifas — avisa en Proyecto si llevan >6 meses\n'
        'FECHA_VALIDACION_TARIFAS = "2025-01-01"\n'
        '\n'
        'CIUDADES = {',
    desc="FECHA_VALIDACION_TARIFAS"
)
if not ok: errors.append("FECHA_VALIDACION_TARIFAS ya presente o fragmento no encontrado")

ok2 = patch(
    DATOS / "ciudades_colombia.py",
    buscar=
        '    "Quibdó": {\n'
        '        "lat": 5.694, "lon": -76.658, "alt_m": 54,\n'
        '        "GHI_kWh_m2_dia": 4.3, "HSP": 4.3,\n'
        '        "T_amb_media": 28.0, "T_min_diseno": 20.0,\n'
        '        "T_cel_realista": 53.0, "T_cel_extremo": 62.0,\n'
        '        "region": "Pacífico", "CREG_zona": "Chocó",\n'
        '        "operador": "DISPAC",\n'
        '        "tarifa_comercial_cop_kwh": 1000,\n'
        '    },\n'
        '}',
    reemplazar=
        '    "Quibdó": {\n'
        '        "lat": 5.694, "lon": -76.658, "alt_m": 54,\n'
        '        "GHI_kWh_m2_dia": 4.3, "HSP": 4.3,\n'
        '        "T_amb_media": 28.0, "T_min_diseno": 20.0,\n'
        '        "T_cel_realista": 53.0, "T_cel_extremo": 62.0,\n'
        '        "region": "Pacífico", "CREG_zona": "Chocó",\n'
        '        "operador": "DISPAC",\n'
        '        "tarifa_comercial_cop_kwh": 1000,\n'
        '    },\n'
        '    "Apartadó (Urabá)": {\n'
        '        "lat": 7.884, "lon": -76.635, "alt_m": 30,\n'
        '        "GHI_kWh_m2_dia": 5.3, "HSP": 5.3,\n'
        '        "T_amb_media": 28.0, "T_min_diseno": 20.0,\n'
        '        "T_cel_realista": 55.0, "T_cel_extremo": 64.0,\n'
        '        "region": "Caribe/Tropical", "CREG_zona": "Antioquia",\n'
        '        "operador": "EPM",\n'
        '        "tarifa_comercial_cop_kwh": 950,\n'
        '    },\n'
        '}',
    desc="Apartadó (Urabá) ciudad"
)
if not ok2: errors.append("Apartadó ya presente o fragmento no encontrado")

# ══════════════════════════════════════════════════════════════════════════════
# 2. 1_Proyecto.py — import FECHA + aviso >6 meses
# ══════════════════════════════════════════════════════════════════════════════
print("\n[2] 1_Proyecto.py — aviso tarifas desactualizadas")

_proyecto_file = None
for _p in PAGES.iterdir():
    if "Proyecto" in _p.name and _p.suffix == ".py":
        _proyecto_file = _p
        break

if _proyecto_file is None:
    print("  ❌  No se encontró 1_Proyecto.py")
    errors.append("Proyecto.py no encontrado")
else:
    patch(
        _proyecto_file,
        buscar="from datos.ciudades_colombia import CIUDADES, LISTA_CIUDADES",
        reemplazar="from datetime import date\nfrom datos.ciudades_colombia import CIUDADES, LISTA_CIUDADES, FECHA_VALIDACION_TARIFAS",
        desc="import FECHA_VALIDACION_TARIFAS"
    )
    patch(
        _proyecto_file,
        buscar=
            '    if modo_key == "consumo":\n'
            '        st.subheader("Consumo / Factura")',
        reemplazar=
            '    # ── Aviso si las tarifas del catálogo llevan más de 6 meses sin actualizar ─\n'
            '    try:\n'
            '        _fv = date.fromisoformat(FECHA_VALIDACION_TARIFAS)\n'
            '        _meses_sin_actualizar = (date.today() - _fv).days / 30.44\n'
            '        if _meses_sin_actualizar > 6:\n'
            '            st.warning(\n'
            '                f"⚠️ **Tarifas del catálogo desactualizadas** — la última validación fue el "\n'
            '                f"**{_fv.strftime(\'%d/%m/%Y\')}** "\n'
            '                f"({int(_meses_sin_actualizar)} meses). "\n'
            '                f"Las tarifas de CREG/operadores pueden haber variado. "\n'
            '                f"Confirma con la factura real del cliente o la circular CREG más reciente "\n'
            '                f"y ajusta el valor arriba. "\n'
            '                f"*(Para actualizar el catálogo: `bipv_python/datos/ciudades_colombia.py` → "\n'
            '                f"campo `tarifa_comercial_cop_kwh` + actualizar `FECHA_VALIDACION_TARIFAS`.)*"\n'
            '            )\n'
            '    except Exception:\n'
            '        pass\n'
            '\n'
            '    if modo_key == "consumo":\n'
            '        st.subheader("Consumo / Factura")',
        desc="aviso tarifas >6 meses"
    )

# ══════════════════════════════════════════════════════════════════════════════
# 3. 2_Recurso_Solar.py — caché de disco TMY+POA
# ══════════════════════════════════════════════════════════════════════════════
print("\n[3] 2_Recurso_Solar.py — caché de disco")

_solar_file = None
for _p in PAGES.iterdir():
    if "Recurso_Solar" in _p.name or "Recurso Solar" in _p.name:
        _solar_file = _p
        break

if _solar_file is None:
    print("  ❌  No se encontró 2_Recurso_Solar.py")
    errors.append("Recurso_Solar.py no encontrado")
else:
    # a) Agregar imports y funciones de caché al inicio
    patch(
        _solar_file,
        buscar=
            '"""Página 2 — Recurso Solar: TMY desde PVGIS + POA para sistemas solares."""\n'
            'import streamlit as st\n'
            'import plotly.graph_objects as go\n'
            'import pandas as pd\n',
        reemplazar=
            '"""Página 2 — Recurso Solar: TMY desde PVGIS + POA para sistemas solares."""\n'
            'import os\n'
            'import pickle\n'
            'import streamlit as st\n'
            'import plotly.graph_objects as go\n'
            'import pandas as pd\n'
            '\n'
            '# ── Caché de disco para TMY+POA — sobrevive reinicios de PM2 ─────────────────\n'
            '_SOLAR_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "datos", "solar_cache")\n'
            '\n'
            'def _cache_path(lat, lon, tilt, azimuth, alt_m):\n'
            '    os.makedirs(_SOLAR_CACHE_DIR, exist_ok=True)\n'
            '    return os.path.join(\n'
            '        _SOLAR_CACHE_DIR,\n'
            '        f"solar_{lat:.4f}_{lon:.4f}_t{tilt}_a{int(azimuth)}_h{alt_m}.pkl",\n'
            '    )\n'
            '\n'
            'def _leer_cache(lat, lon, tilt, azimuth, alt_m):\n'
            '    try:\n'
            '        p = _cache_path(lat, lon, tilt, azimuth, alt_m)\n'
            '        if os.path.exists(p):\n'
            '            with open(p, "rb") as f:\n'
            '                return pickle.load(f)\n'
            '    except Exception:\n'
            '        pass\n'
            '    return None\n'
            '\n'
            'def _guardar_cache(lat, lon, tilt, azimuth, alt_m, tmy, poa):\n'
            '    try:\n'
            '        with open(_cache_path(lat, lon, tilt, azimuth, alt_m), "wb") as f:\n'
            '            pickle.dump({"tmy": tmy, "poa": poa}, f, protocol=4)\n'
            '    except Exception:\n'
            '        pass\n',
        desc="imports+funciones caché disco"
    )

    # b) Auto-restaurar + Limpiar caché borra disco + descarga usa disco primero
    patch(
        _solar_file,
        buscar=
            'st.markdown("---")\n'
            '\n'
            '# ── Función cacheada para PVGIS ──────────────────────────────────────────────\n'
            '@st.cache_data(ttl=86400, show_spinner=False)\n'
            'def cargar_tmy(lat, lon):\n'
            '    return obtener_tmy_pvgis(lat, lon)\n'
            '\n'
            '# ── Botones de acción ────────────────────────────────────────────────────────\n'
            '_btn_col1, _btn_col2 = st.columns([4, 1])\n'
            '_descarga_btn = _btn_col1.button("🌐 Descargar TMY de PVGIS y calcular POA", type="primary", use_container_width=True)\n'
            '_recalc_btn   = _btn_col2.button("🔄 Limpiar caché", use_container_width=True,\n'
            '                                  help="Fuerza nueva descarga desde PVGIS, descartando datos anteriores.")\n'
            'if _recalc_btn:\n'
            '    cargar_tmy.clear()\n'
            '    st.success("✅ Caché limpiada — presiona **Descargar TMY** para obtener datos frescos.")\n'
            '\n'
            'if _descarga_btn:\n'
            '\n'
            '    _sitio_label = (\n'
            '        f"predio en {ciudad} ({lat:.5f}°, {lon:.5f}°)"\n'
            '        if _coord_personalizada else f"{ciudad} ({lat}°, {lon}°)"\n'
            '    )\n'
            '    with st.spinner(f"Conectando a PVGIS para {_sitio_label}..."):\n'
            '        try:\n'
            '            tmy = cargar_tmy(lat, lon)\n'
            '        except Exception as e:\n'
            '            st.error(f"❌ Error conectando a PVGIS: {e}")\n'
            '            st.info("Verifica la conexión a internet del servidor. PVGIS requiere acceso a re.jrc.ec.europa.eu")\n'
            '            st.stop()\n'
            '\n'
            '    with st.spinner(f"Calculando irradiancia POA para {icono_tipo} {tipo_instalacion} ({tilt}°)..."):\n'
            '        poa = calcular_poa(tmy, lat, lon, alt_m, tilt, azimuth)\n'
            '        monthly = resumen_mensual(tmy, poa)\n',
        reemplazar=
            'st.markdown("---")\n'
            '\n'
            '# ── Auto-restaurar desde caché de disco (sobrevive reinicios de PM2) ─────────\n'
            'if not st.session_state.get("recurso_solar_ok"):\n'
            '    _auto_cached = _leer_cache(lat, lon, tilt, azimuth, alt_m)\n'
            '    if _auto_cached is not None:\n'
            '        _tmy_r = _auto_cached["tmy"]\n'
            '        _poa_r = _auto_cached["poa"]\n'
            '        _poa_anual_r = _poa_r["poa_global"].sum() / 1000.0\n'
            '        _ghi_anual_r = _tmy_r["G_h"].sum() / 1000.0\n'
            '        _t_media_r   = _tmy_r["T2m"].mean()\n'
            '        def _zona_por_coords_rs(la, lo):\n'
            '            if 4.5 <= la <= 8.5 and lo <= -76.0:              return "Urabá / Chocó (tropical)"\n'
            '            if la > 8.5 or (la > 7.5 and lo > -76.0):         return "Barranquilla / Costa"\n'
            '            if lo > -74.0:                                     return "Llanos Orientales"\n'
            '            if la < 4.5 and lo < -74.0:                        return "Cali / Valle"\n'
            '            if la < 5.5 and lo > -74.5:                        return "Bogotá / Sabana"\n'
            '            return "Medellín / Antioquia"\n'
            '        st.session_state.update({\n'
            '            "tmy_df":             _tmy_r,\n'
            '            "poa_df":             _poa_r,\n'
            '            "tmy_ciudad":         ciudad,\n'
            '            "tilt_fachada":       tilt,\n'
            '            "tilt_default":       tilt,\n'
            '            "azimuth_fachada":    azimuth,\n'
            '            "orientacion_label":  orientacion_label,\n'
            '            "poa_anual_kWh_m2":   round(_poa_anual_r, 1),\n'
            '            "ghi_anual_kWh_m2":   round(_ghi_anual_r, 1),\n'
            '            "t_media_anual":      round(_t_media_r, 1),\n'
            '            "zona_geo_coords":    _zona_por_coords_rs(lat, lon),\n'
            '            "recurso_solar_ok":   True,\n'
            '        })\n'
            '        st.info(\n'
            '            f"📂 **Recurso solar restaurado desde caché local** — "\n'
            '            f"POA: **{_poa_anual_r:,.0f} kWh/m²/año** · "\n'
            '            f"GHI: **{_ghi_anual_r:,.0f} kWh/m²/año** · "\n'
            '            f"{icono_tipo} {orientacion_label} / {tilt}°  \\n"\n'
            '            f"*(Sin descarga de PVGIS. Usa 🔄 **Limpiar caché** si necesitas datos frescos.)*"\n'
            '        )\n'
            '        st.rerun()\n'
            '\n'
            '# ── Función cacheada para PVGIS (RAM, 24 h) ──────────────────────────────────\n'
            '@st.cache_data(ttl=86400, show_spinner=False)\n'
            'def cargar_tmy(lat, lon):\n'
            '    return obtener_tmy_pvgis(lat, lon)\n'
            '\n'
            '# ── Botones de acción ────────────────────────────────────────────────────────\n'
            '_btn_col1, _btn_col2 = st.columns([4, 1])\n'
            '_descarga_btn = _btn_col1.button("🌐 Descargar TMY de PVGIS y calcular POA", type="primary", use_container_width=True)\n'
            '_recalc_btn   = _btn_col2.button("🔄 Limpiar caché", use_container_width=True,\n'
            '                                  help="Fuerza nueva descarga desde PVGIS, descartando datos anteriores.")\n'
            'if _recalc_btn:\n'
            '    cargar_tmy.clear()\n'
            '    try:\n'
            '        _p = _cache_path(lat, lon, tilt, azimuth, alt_m)\n'
            '        if os.path.exists(_p): os.remove(_p)\n'
            '    except Exception:\n'
            '        pass\n'
            '    st.session_state["recurso_solar_ok"] = False\n'
            '    st.success("✅ Caché limpiada — presiona **Descargar TMY** para obtener datos frescos.")\n'
            '\n'
            'if _descarga_btn:\n'
            '\n'
            '    _sitio_label = (\n'
            '        f"predio en {ciudad} ({lat:.5f}°, {lon:.5f}°)"\n'
            '        if _coord_personalizada else f"{ciudad} ({lat}°, {lon}°)"\n'
            '    )\n'
            '    _disco = _leer_cache(lat, lon, tilt, azimuth, alt_m)\n'
            '    if _disco is not None:\n'
            '        tmy = _disco["tmy"]\n'
            '        poa = _disco["poa"]\n'
            '        monthly = resumen_mensual(tmy, poa)\n'
            '        st.info("📂 Datos recuperados de caché local — sin conexión a PVGIS.")\n'
            '    else:\n'
            '        with st.spinner(f"Conectando a PVGIS para {_sitio_label}..."):\n'
            '            try:\n'
            '                tmy = cargar_tmy(lat, lon)\n'
            '            except Exception as e:\n'
            '                st.error(f"❌ Error conectando a PVGIS: {e}")\n'
            '                st.info("Verifica la conexión a internet del servidor. PVGIS requiere acceso a re.jrc.ec.europa.eu")\n'
            '                st.stop()\n'
            '\n'
            '        with st.spinner(f"Calculando irradiancia POA para {icono_tipo} {tipo_instalacion} ({tilt}°)..."):\n'
            '            poa = calcular_poa(tmy, lat, lon, alt_m, tilt, azimuth)\n'
            '            monthly = resumen_mensual(tmy, poa)\n'
            '            _guardar_cache(lat, lon, tilt, azimuth, alt_m, tmy, poa)\n',
        desc="auto-restore + disco en descarga"
    )

# ══════════════════════════════════════════════════════════════════════════════
# 4. 8_Presupuesto.py — zona desde lat/lon sin requerir Recurso Solar
# ══════════════════════════════════════════════════════════════════════════════
print("\n[4] 8_Presupuesto.py — zona geográfica desde lat/lon del proyecto")

_ppto_file = None
for _p in PAGES.iterdir():
    if "Presupuesto" in _p.name and _p.suffix == ".py":
        _ppto_file = _p
        break

if _ppto_file is None:
    print("  ❌  No se encontró 8_Presupuesto.py")
    errors.append("Presupuesto.py no encontrado")
else:
    patch(
        _ppto_file,
        buscar=
            '    _municipio_predio = str(st.session_state.get("municipio_predio", "")).lower()\n'
            '    _ciudad_tmy       = str(st.session_state.get("tmy_ciudad", "")).lower()\n'
            '    _zona_geo_coords  = st.session_state.get("zona_geo_coords", "")   # set en Recurso Solar\n'
            '    _zona_opts  = list(_ZONA_FACTOR.keys())\n',
        reemplazar=
            '    _municipio_predio = str(st.session_state.get("municipio_predio", "")).lower()\n'
            '    _ciudad_tmy       = str(st.session_state.get("tmy_ciudad", "")).lower()\n'
            '    _zona_geo_coords  = st.session_state.get("zona_geo_coords", "")   # set en Recurso Solar\n'
            '    _zona_opts  = list(_ZONA_FACTOR.keys())\n'
            '\n'
            '    # Si Recurso Solar aún no se ha ejecutado, calcular la zona directamente desde\n'
            '    # lat/lon del proyecto — misma lógica que _zona_por_coords() en Recurso Solar.\n'
            '    if not _zona_geo_coords:\n'
            '        _lat_p = float(st.session_state.get("lat_proyecto", 0.0))\n'
            '        _lon_p = float(st.session_state.get("lon_proyecto", 0.0))\n'
            '        if _lat_p and _lon_p:\n'
            '            if   4.5 <= _lat_p <= 8.5 and _lon_p <= -76.0:              _zona_geo_coords = "Urabá / Chocó (tropical)"\n'
            '            elif _lat_p > 8.5 or (_lat_p > 7.5 and _lon_p > -76.0):     _zona_geo_coords = "Barranquilla / Costa"\n'
            '            elif _lon_p > -74.0:                                         _zona_geo_coords = "Llanos Orientales"\n'
            '            elif _lat_p < 4.5 and _lon_p < -74.0:                       _zona_geo_coords = "Cali / Valle"\n'
            '            elif _lat_p < 5.5 and _lon_p > -74.5:                       _zona_geo_coords = "Bogotá / Sabana"\n'
            '            else:                                                         _zona_geo_coords = "Medellín / Antioquia"\n'
            '            st.session_state["zona_geo_coords"] = _zona_geo_coords\n',
        desc="zona desde lat/lon proyecto"
    )

# ══════════════════════════════════════════════════════════════════════════════
# Crear directorio de caché solar
# ══════════════════════════════════════════════════════════════════════════════
_cache_dir = DATOS / "solar_cache"
_cache_dir.mkdir(exist_ok=True)
print(f"\n[5] Directorio caché solar: {_cache_dir} ✅")

# ══════════════════════════════════════════════════════════════════════════════
# Resumen
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
if errors:
    print(f"⚠  {len(errors)} parche(s) omitidos (ya aplicados o fragmento no encontrado):")
    for e in errors: print(f"   · {e}")
else:
    print("✅ Todos los parches aplicados correctamente.")
print("Próximo paso: pm2 restart streamlit-bipv")
