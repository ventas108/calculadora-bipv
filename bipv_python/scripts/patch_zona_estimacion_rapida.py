#!/usr/bin/env python3
"""
Parche: Task #79 — Sincronizar zona geográfica de Estimación Rápida
                   con la ciudad detectada del Recurso Solar
Aplicar en el servidor:
    cd /var/www/bipv/calculadora-bipv
    python3 bipv_python/scripts/patch_zona_estimacion_rapida.py
    pm2 restart streamlit-bipv

Problema:
  El auto-update de Estimación Rápida (se activa cuando kWp cambia >5%)
  usaba _er_cfg_prev.get("zona") — la zona de la última ejecución — en vez
  de la zona fresca calculada desde zona_geo_coords / lat_proyecto / tmy_ciudad.
  Si el usuario movía el proyecto a otra ciudad, el auto-update seguía
  calculando con la zona antigua.

Solución:
  1. Mover el bloque de detección de zona (predio → coords → TMY) a ANTES
     del bloque de auto-actualización, para que éste siempre use la zona vigente.
  2. En el auto-update, usar _zona_opts[_zona_idx] (fresco) en vez de la
     zona cacheada en est_rapida_config.
  3. El st.info del auto-update ahora menciona el cambio de zona cuando ocurre.
  4. Eliminar el bloque de detección duplicado que quedaba en la posición original.
"""
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent.parent
PRES = BASE / "pages" / "8_💼_Presupuesto.py"
errors = []

def patch(buscar: str, reemplazar: str, desc: str):
    txt = PRES.read_text(encoding="utf-8")
    if buscar not in txt:
        print(f"  ⚠  '{desc}' — fragmento NOT found (already applied?)")
        errors.append(desc); return
    PRES.write_text(txt.replace(buscar, reemplazar, 1), encoding="utf-8")
    print(f"  ✅  '{desc}'")

print(f"\nParchando {PRES.name}...")

# ── 1. Insertar detección de zona fresca + corregir auto-update ───────────
patch(
    buscar=(
        '    # ── Auto-actualización silenciosa cuando el kWp del sistema cambió ────────\n'
        '    # Si la estimación ya fue aplicada y el sistema cambió >5% de potencia,\n'
        '    # recalcula y re-aplica automáticamente con el mismo tipo/escenario/zona.\n'
        '    _er_cfg_prev = st.session_state.get("est_rapida_config", {})\n'
        '    if st.session_state.get("est_rapida_aplicada") and _er_cfg_prev and p_stc > 0:\n'
        '        _kwp_prev_er = float(_er_cfg_prev.get("kwp", 0))\n'
        '        if _kwp_prev_er > 0 and abs(p_stc - _kwp_prev_er) / _kwp_prev_er > 0.05:\n'
        '            _tipo_auto = _er_cfg_prev.get("tipo", list(_BENCH.keys())[0])\n'
        '            _esc_auto  = _er_cfg_prev.get("escenario", "Base")\n'
        '            _zona_auto = _er_cfg_prev.get("zona", list(_ZONA_FACTOR.keys())[0])\n'
    ),
    reemplazar=(
        '    # ── #79 — Detectar zona fresca ANTES del auto-update ────────────────────────\n'
        '    _zona_opts  = list(_ZONA_FACTOR.keys())\n'
        '    _municipio_predio = str(st.session_state.get("municipio_predio", "")).lower()\n'
        '    _ciudad_tmy       = str(st.session_state.get("tmy_ciudad", "")).lower()\n'
        '    _zona_geo_coords  = st.session_state.get("zona_geo_coords", "")\n'
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
        '            st.session_state["zona_geo_coords"] = _zona_geo_coords\n'
        '    _zona_map = {\n'
        '        "villavicencio": 5, "vichada": 5, "orinoquia": 5,\n'
        '        "leticia": 5, "amazona": 5, "llano": 5,\n'
        '        "urab": 4, "apartad": 4, "turbo": 4,\n'
        '        "necoclí": 4, "necocli": 4, "chigorodo": 4, "chigorodó": 4,\n'
        '        "mutata": 4, "mutatá": 4, "carepa": 4, "arboletes": 4,\n'
        '        "choc": 4, "quibd": 4,\n'
        '        "barranq": 3, "santa marta": 3, "cartagena": 3,\n'
        '        "monteria": 3, "sincelejo": 3, "valledup": 3,\n'
        '        "cordoba": 3, "sucre": 3, "cesar": 3, "magdalena": 3, "costa": 3,\n'
        '        "cali": 2, "palmira": 2, "buenaven": 2, "popayan": 2,\n'
        '        "valle": 2, "cauca": 2,\n'
        '        "medell": 1, "rionegro": 1, "manizal": 1,\n'
        '        "pereira": 1, "armenia": 1, "risaral": 1, "quindio": 1, "caldas": 1,\n'
        '        "antioq": 1,\n'
        '        "bogot": 0, "saban": 0, "tunja": 0, "cundinam": 0,\n'
        '    }\n'
        '    _zona_idx = 0; _zona_fuente = None\n'
        '    for kw, idx in _zona_map.items():\n'
        '        if kw in _municipio_predio:\n'
        '            _zona_idx = idx; _zona_fuente = "predio"; break\n'
        '    if not _zona_fuente and _zona_geo_coords in _zona_opts:\n'
        '        _zona_idx = _zona_opts.index(_zona_geo_coords); _zona_fuente = "coords"\n'
        '    if not _zona_fuente:\n'
        '        for kw, idx in _zona_map.items():\n'
        '            if kw in _ciudad_tmy:\n'
        '                _zona_idx = idx; _zona_fuente = "TMY"; break\n'
        '\n'
        '    # ── Auto-actualización silenciosa cuando el kWp del sistema cambió ────────\n'
        '    # Si la estimación ya fue aplicada y el sistema cambió >5% de potencia,\n'
        '    # recalcula y re-aplica automáticamente con el mismo tipo/escenario/zona.\n'
        '    _er_cfg_prev = st.session_state.get("est_rapida_config", {})\n'
        '    if st.session_state.get("est_rapida_aplicada") and _er_cfg_prev and p_stc > 0:\n'
        '        _kwp_prev_er = float(_er_cfg_prev.get("kwp", 0))\n'
        '        if _kwp_prev_er > 0 and abs(p_stc - _kwp_prev_er) / _kwp_prev_er > 0.05:\n'
        '            _tipo_auto = _er_cfg_prev.get("tipo", list(_BENCH.keys())[0])\n'
        '            _esc_auto  = _er_cfg_prev.get("escenario", "Base")\n'
        '            # #79 — zona fresca desde coords/predio/TMY; stale-config solo como fallback\n'
        '            _zona_auto = _zona_opts[_zona_idx] if _zona_fuente else _er_cfg_prev.get("zona", _zona_opts[0])\n'
    ),
    desc="insertar detección de zona fresca antes del auto-update"
)

# ── 2. Actualizar est_rapida_config con la zona nueva + info con cambio ───
patch(
    buscar=(
        '            st.session_state["est_rapida_config"] = {**_er_cfg_prev, "kwp": p_stc}\n'
        '            st.info(\n'
        '                f"🔄 **Estimación Rápida auto-actualizada** — el sistema cambió de "\n'
        '                f"**{_kwp_prev_er:.1f} → {p_stc:.1f} kWp**. "\n'
        '                f"CAPEX actualizado a **USD {_r_auto[\'capex_total\']:,.0f}** "\n'
        '                f"({_tipo_auto} · {_esc_auto} · {_zona_auto}). "\n'
        '                f"💰 Financiero refleja el nuevo valor automáticamente."\n'
        '            )'
    ),
    reemplazar=(
        '            _zona_prev_er = _er_cfg_prev.get("zona", _zona_opts[0])\n'
        '            st.session_state["est_rapida_config"] = {**_er_cfg_prev, "kwp": p_stc, "zona": _zona_auto}\n'
        '            _zona_cambio_txt = (\n'
        '                f" · zona actualizada de **{_zona_prev_er}** → **{_zona_auto}**"\n'
        '                if _zona_auto != _zona_prev_er else ""\n'
        '            )\n'
        '            st.info(\n'
        '                f"🔄 **Estimación Rápida auto-actualizada** — el sistema cambió de "\n'
        '                f"**{_kwp_prev_er:.1f} → {p_stc:.1f} kWp**{_zona_cambio_txt}. "\n'
        '                f"CAPEX actualizado a **USD {_r_auto[\'capex_total\']:,.0f}** "\n'
        '                f"({_tipo_auto} · {_esc_auto} · {_zona_auto}). "\n'
        '                f"💰 Financiero refleja el nuevo valor automáticamente."\n'
        '            )'
    ),
    desc="guardar zona actualizada en config + mostrar cambio en info"
)

# ── 3. Eliminar bloque de detección duplicado en posición original ────────
patch(
    buscar=(
        '    # Auto-detectar zona — prioridad:\n'
        '    #   1. municipio_predio  (nombre real del predio, keyword matching)\n'
        '    #   2. zona_geo_coords   (lat/lon del proyecto → calculada en Recurso Solar, nombre exacto)\n'
        '    #   3. tmy_ciudad        (ciudad de referencia TMY, keyword matching — menos fiable)\n'
        '    _municipio_predio = str(st.session_state.get("municipio_predio", "")).lower()\n'
        '    _ciudad_tmy       = str(st.session_state.get("tmy_ciudad", "")).lower()\n'
        '    _zona_geo_coords  = st.session_state.get("zona_geo_coords", "")   # set en Recurso Solar\n'
        '    _zona_opts  = list(_ZONA_FACTOR.keys())\n'
    ),
    reemplazar=(
        '    # Auto-detectar zona — ya computado antes del auto-update (#79).\n'
    ),
    desc="eliminar duplicado: cabecera del bloque de detección"
)

# También eliminar el resto del bloque duplicado si quedó parcialmente
_bloque_dup = (
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
    '            st.session_state["zona_geo_coords"] = _zona_geo_coords\n'
)
txt = PRES.read_text(encoding="utf-8")
if _bloque_dup in txt:
    PRES.write_text(txt.replace(_bloque_dup, '', 1), encoding="utf-8")
    print("  ✅  'eliminar bloque latlon duplicado'")
else:
    print("  ⚠  'bloque latlon duplicado' — NOT found (already removed or not present)")

_zona_map_dup = (
    '    # IMPORTANTE: keywords más específicos primero. "antioq" es substring de\n'
    '    # "Antioquia" que aparece tanto en "Medellín, Antioquia" como en\n'
    '    # "Apartadó, Urabá, Antioquia" — Urabá debe ir ANTES que "antioq".\n'
    '    _zona_map   = {\n'
    '        # Zonas remotas / llanos (específico antes que nombres de depto)\n'
    '        "villavicencio": 5, "vichada": 5, "orinoquia": 5,\n'
    '        "leticia": 5, "amazona": 5, "llano": 5,\n'
    '        # Urabá / Chocó ANTES de "antioq" (evita falso match Antioquia→Medellín)\n'
    '        "urab": 4, "apartad": 4, "turbo": 4,\n'
    '        "necoclí": 4, "necocli": 4, "chigorodo": 4, "chigorodó": 4,\n'
    '        "mutata": 4, "mutatá": 4, "carepa": 4, "arboletes": 4,\n'
    '        "choc": 4, "quibd": 4,\n'
    '        # Costa Caribe (ciudades específicas antes de términos genéricos)\n'
    '        "barranq": 3, "santa marta": 3, "cartagena": 3,\n'
    '        "monteria": 3, "sincelejo": 3, "valledup": 3,\n'
    '        "cordoba": 3, "sucre": 3, "cesar": 3, "magdalena": 3, "costa": 3,\n'
    '        # Sur-Occidente\n'
    '        "cali": 2, "palmira": 2, "buenaven": 2, "popayan": 2,\n'
    '        "valle": 2, "cauca": 2,\n'
    '        # Eje Cafetero / Antioquia (genérico — al final del grupo)\n'
    '        "medell": 1, "rionegro": 1, "manizal": 1,\n'
    '        "pereira": 1, "armenia": 1, "risaral": 1, "quindio": 1, "caldas": 1,\n'
    '        "antioq": 1,   # ← genérico: solo llega aquí si ningún keyword anterior hizo match\n'
    '        # Bogotá / Sabana\n'
    '        "bogot": 0, "saban": 0, "tunja": 0, "cundinam": 0,\n'
    '    }\n'
    '\n'
    '    _zona_idx    = 0\n'
    '    _zona_fuente = None\n'
    '\n'
    '    # Fuente 1: nombre del predio (keyword matching)\n'
    '    for kw, idx in _zona_map.items():\n'
    '        if kw in _municipio_predio:\n'
    '            _zona_idx    = idx\n'
    '            _zona_fuente = "predio"\n'
    '            break\n'
    '\n'
    '    # Fuente 2: lat/lon del proyecto (nombre exacto desde Recurso Solar)\n'
    '    if not _zona_fuente and _zona_geo_coords in _zona_opts:\n'
    '        _zona_idx    = _zona_opts.index(_zona_geo_coords)\n'
    '        _zona_fuente = "coords"\n'
    '\n'
    '    # Fuente 3: ciudad TMY de referencia (keyword matching — menos precisa)\n'
    '    if not _zona_fuente:\n'
    '        for kw, idx in _zona_map.items():\n'
    '            if kw in _ciudad_tmy:\n'
    '                _zona_idx    = idx\n'
    '                _zona_fuente = "TMY"\n'
    '                break\n'
    '\n'
    '    # FIX: pre-poblar session_state para TODAS las fuentes automáticas.\n'
    '    # Sin esto, Streamlit ignora `index=` en renders sucesivos porque el key\n'
    '    # ya existe en session_state con el valor anterior.\n'
    '    if _zona_fuente:\n'
    '        st.session_state["est_zona"] = _zona_opts[_zona_idx]\n'
)
txt = PRES.read_text(encoding="utf-8")
if _zona_map_dup in txt:
    repl = (
        '    # FIX: pre-poblar session_state para TODAS las fuentes automáticas.\n'
        '    # Sin esto, Streamlit ignora `index=` en renders sucesivos porque el key\n'
        '    # ya existe en session_state con el valor anterior.\n'
        '    if _zona_fuente:\n'
        '        st.session_state["est_zona"] = _zona_opts[_zona_idx]\n'
    )
    PRES.write_text(txt.replace(_zona_map_dup, repl, 1), encoding="utf-8")
    print("  ✅  'eliminar _zona_map/_zona_idx/_zona_fuente duplicados'")
else:
    print("  ⚠  '_zona_map duplicado' — NOT found (already removed or not present)")

print("\n" + "="*60)
if errors:
    print(f"⚠  {len(errors)} parche(s) omitidos:"); [print(f"   · {e}") for e in errors]
else:
    print("✅ Todos los parches aplicados.")
print("Próximo paso: pm2 restart streamlit-bipv")
