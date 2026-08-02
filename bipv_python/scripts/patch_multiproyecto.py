"""
Parche #63 — Guardar y cambiar entre varios proyectos sin perder datos
======================================================================
Crea dos archivos nuevos y modifica páginas/1_🏠_Proyecto.py:

A) NUEVO: calculos/proyectos_manager.py
   Módulo con API de persistencia multi-proyecto:
     • listar_proyectos()          → lista de metadata de proyectos en datos/proyectos/
     • guardar_proyecto_actual()   → snapshot del session_state a JSON
     • cargar_proyecto(slug)       → restore del JSON a session_state
     • eliminar_proyecto(slug)     → eliminar archivo

B) MODIFICADO: pages/1_🏠_Proyecto.py
   • Añade import del nuevo módulo.
   • Inserta expander "📁 Mis Proyectos" debajo de st.title(), con:
       – Input de nombre + botón "💾 Guardar"
       – Lista de proyectos guardados con "📂 Cargar" y "🗑️ Eliminar"

Qué se guarda / qué no:
  ✅ Datos de entrada: ciudad, área, equipos, coordenadas, tarifa, presupuesto...
  ✅ Scalares de resultado: E_ac_anual_kWh, capex_total_usd, métricas financieras...
  ❌ DataFrames grandes (tmy_df, df_mensual_produccion, etc.) — se regeneran al re-ejecutar
  ❌ Resultados de cómputo pesado (bypass_result, res_produccion, etc.)
"""
import sys, pathlib, shutil, datetime, textwrap

BASE  = pathlib.Path("/var/www/bipv/calculadora-bipv/bipv_python")
PROY1 = BASE / "pages" / "1_🏠_Proyecto.py"
MGR   = BASE / "calculos" / "proyectos_manager.py"

def backup(p: pathlib.Path, tag: str):
    ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = p.with_suffix(f".py.bak_{tag}_{ts}")
    shutil.copy2(p, bak)
    print(f"  [backup] {bak.name}")

# ── Verificar archivos base ────────────────────────────────────────────────────
if not PROY1.exists():
    print(f"[ERROR] No encontrado: {PROY1}")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
# PARTE A — Crear calculos/proyectos_manager.py
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[A] Creando calculos/proyectos_manager.py")

if MGR.exists():
    print("  [OK] Ya existe proyectos_manager.py — se sobreescribe con versión actualizada.")
    backup(MGR, "63A")

MGR.write_text(
    textwrap.dedent('''\
    """
    proyectos_manager.py — Gestión de múltiples proyectos BIPV
    ===========================================================
    Permite guardar, cargar, listar y eliminar proyectos.
    Cada proyecto se almacena como un archivo JSON en datos/proyectos/.
    """
    from __future__ import annotations
    import json
    import os
    import re
    import datetime
    from typing import Any

    import streamlit as st

    _DIR_BASE     = os.path.join(os.path.dirname(__file__), "..", "datos")
    DIR_PROYECTOS = os.path.join(_DIR_BASE, "proyectos")

    _CLAVES_EXCLUIR: set = {
        "tmy_df", "poa_df", "poa_efectiva_df", "df_mensual_produccion",
        "df_diagnostico_real", "df_fs_raw", "horizonte_df", "balance_mensual_df",
        "poa_directa_df", "poa_difusa_df",
        "res_produccion", "res_sombra", "res_mismatch_or",
        "cascada_mismatch", "bypass_result", "motor_optico_summary",
        "res_motor_optico",
        "bateria_dim",
        "proyecto_cargado_desde_disco",
        "ss_materiales_df", "ss_mano_df", "ss_fv_df",
        "ss_inversor_df", "ss_blando_df", "ss_opex_df",
        "insumos_df", "insumos_template_df",
    }
    _PREFIJOS_TEMP = ("_", "FormSubmitter:", "btn_")


    class _SafeEncoder(json.JSONEncoder):
        def default(self, obj: Any):
            try:
                import numpy as np
                if isinstance(obj, np.integer):
                    return int(obj)
                if isinstance(obj, np.floating):
                    return float(obj)
                if isinstance(obj, np.bool_):
                    return bool(obj)
                if isinstance(obj, np.ndarray):
                    return obj.tolist() if obj.size <= 100 else None
            except ImportError:
                pass
            try:
                import pandas as pd
                if isinstance(obj, (pd.DataFrame, pd.Series)):
                    return None
            except ImportError:
                pass
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()
            return None


    def _es_serializable(v: Any) -> bool:
        try:
            import pandas as pd
            if isinstance(v, (pd.DataFrame, pd.Series)):
                return False
        except ImportError:
            pass
        try:
            import numpy as np
            if isinstance(v, np.ndarray) and v.size > 100:
                return False
        except ImportError:
            pass
        try:
            json.dumps(v, cls=_SafeEncoder)
            return True
        except Exception:
            return False


    def nombre_a_slug(nombre: str) -> str:
        s = nombre.lower().strip()
        for src, dst in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),
                         ("ñ","n"),("ü","u")]:
            s = s.replace(src, dst)
        s = re.sub(r"[^a-z0-9]+", "_", s)
        return s.strip("_") or "proyecto"


    def _ruta_proyecto(slug: str) -> str:
        return os.path.join(DIR_PROYECTOS, f"{slug}.json")


    def listar_proyectos() -> list:
        os.makedirs(DIR_PROYECTOS, exist_ok=True)
        proyectos = []
        for fname in os.listdir(DIR_PROYECTOS):
            if not fname.endswith(".json"):
                continue
            ruta = os.path.join(DIR_PROYECTOS, fname)
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    data = json.load(f)
                meta = data.get("_meta", {})
                proyectos.append({
                    "slug":     fname[:-5],
                    "nombre":   meta.get("nombre", fname[:-5]),
                    "guardado": meta.get("guardado", ""),
                    "ciudad":   meta.get("ciudad", "—"),
                    "area_m2":  meta.get("area_m2", 0.0),
                    "e_ac_kWh": meta.get("e_ac_kWh", 0.0),
                    "archivo":  ruta,
                })
            except Exception:
                pass
        proyectos.sort(key=lambda x: x["guardado"], reverse=True)
        return proyectos


    def guardar_proyecto_actual(nombre=None) -> str:
        nombre = nombre or st.session_state.get("nombre_proyecto", "Proyecto BIPV")
        slug   = nombre_a_slug(nombre)
        os.makedirs(DIR_PROYECTOS, exist_ok=True)

        estado = {}
        for k, v in st.session_state.items():
            if k in _CLAVES_EXCLUIR:
                continue
            if any(k.startswith(p) for p in _PREFIJOS_TEMP):
                continue
            if not _es_serializable(v):
                continue
            try:
                json.dumps(v, cls=_SafeEncoder)
                estado[k] = v
            except Exception:
                pass

        estado_limpio = json.loads(json.dumps(estado, cls=_SafeEncoder))
        meta = {
            "nombre":   nombre,
            "guardado": datetime.datetime.now().isoformat(timespec="seconds"),
            "ciudad":   st.session_state.get("tmy_ciudad",
                            st.session_state.get("ciudad", "—")),
            "area_m2":  float(st.session_state.get("area_fachada_m2", 0.0)),
            "e_ac_kWh": float(st.session_state.get("E_ac_anual_kWh", 0.0)),
        }
        payload = {"_meta": meta, "estado": estado_limpio}
        ruta = _ruta_proyecto(slug)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return slug


    def cargar_proyecto(slug: str) -> str:
        ruta = _ruta_proyecto(slug)
        if not os.path.exists(ruta):
            raise FileNotFoundError(f"Proyecto no encontrado: {ruta}")

        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)

        estado = data.get("estado", {})
        meta   = data.get("_meta", {})

        _claves_reset = {
            "produccion_ok", "financiero_ok", "bypass_ok",
            "motor_optico_ok", "mismatch_ok", "balance_ok", "bateria_ok",
            "df_mensual_produccion", "df_diagnostico_real", "df_fs_raw",
            "horizonte_df", "balance_mensual_df", "tmy_df", "poa_df",
            "res_produccion", "res_sombra", "bypass_result",
            "cascada_mismatch", "motor_optico_summary",
        }
        for k in _claves_reset:
            st.session_state.pop(k, None)

        st.session_state["proyecto_cargado_desde_disco"] = True
        for k, v in estado.items():
            st.session_state[k] = v

        return meta.get("nombre", slug)


    def eliminar_proyecto(slug: str) -> bool:
        ruta = _ruta_proyecto(slug)
        if os.path.exists(ruta):
            os.remove(ruta)
            return True
        return False
    '''),
    encoding="utf-8",
)
print("  [✓] proyectos_manager.py creado.")

# ═══════════════════════════════════════════════════════════════════════════════
# PARTE B — Modificar pages/1_🏠_Proyecto.py
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[B] Modificando pages/1_🏠_Proyecto.py")

src = PROY1.read_text(encoding="utf-8")

# Idempotencia
if "proyectos_manager" in src:
    print("  [OK] Ya contiene proyectos_manager — sin cambios.")
else:
    backup(PROY1, "63B")

    # ── B1: Añadir import ────────────────────────────────────────────────────
    OLD_IMPORT = "from calculos.tarifa_utils import init_tarifa, set_tarifa_from_ciudad, tarifa_widget\n"
    NEW_IMPORT = (
        "from calculos.tarifa_utils import init_tarifa, set_tarifa_from_ciudad, tarifa_widget\n"
        "from calculos.proyectos_manager import (\n"
        "    listar_proyectos, guardar_proyecto_actual,\n"
        "    cargar_proyecto, eliminar_proyecto,\n"
        ")\n"
    )

    if OLD_IMPORT in src:
        src = src.replace(OLD_IMPORT, NEW_IMPORT, 1)
        print("  [✓] B1: import añadido.")
    else:
        # Fallback: añadir después de los imports de calculos que existan
        import re
        m = re.search(r"(from calculos\.[^\n]+\n)(?!from calculos\.)", src)
        if m:
            pos = m.end()
            src = (
                src[:pos]
                + "from calculos.proyectos_manager import (\n"
                "    listar_proyectos, guardar_proyecto_actual,\n"
                "    cargar_proyecto, eliminar_proyecto,\n"
                ")\n"
                + src[pos:]
            )
            print("  [✓] B1: import añadido (fallback).")
        else:
            print("  [ADVERTENCIA] B1: no se pudo añadir import automáticamente.")

    # ── B2: Insertar expander "📁 Mis Proyectos" después de st.title() ───────
    OLD_TITLE_BLOCK = (
        'st.set_page_config(page_title="Proyecto — BIPV", page_icon="🏠", layout="wide")\n'
        'st.title("🏠 Datos del Proyecto")\n'
        '\n'
        '# ── Tipos de instalación con defaults técnicos'
    )
    NEW_TITLE_BLOCK = (
        'st.set_page_config(page_title="Proyecto — BIPV", page_icon="🏠", layout="wide")\n'
        'st.title("🏠 Datos del Proyecto")\n'
        '\n'
        '# ── 📁 Gestión de múltiples proyectos (tarea #63) ────────────────────────────\n'
        'with st.expander("📁 Mis Proyectos — guardar / cambiar proyecto", expanded=False):\n'
        '    _proyectos = listar_proyectos()\n'
        '    _nombre_actual = st.session_state.get("nombre_proyecto", "Proyecto BIPV")\n'
        '    st.markdown("**💾 Guardar proyecto actual**")\n'
        '    _col_nombre, _col_btn = st.columns([3, 1])\n'
        '    _nombre_guardar = _col_nombre.text_input(\n'
        '        "Nombre del proyecto a guardar",\n'
        '        value=_nombre_actual,\n'
        '        key="_pm_nombre_guardar",\n'
        '        label_visibility="collapsed",\n'
        '        placeholder="Nombre del proyecto",\n'
        '    )\n'
        '    if _col_btn.button("💾 Guardar", key="_pm_btn_guardar", use_container_width=True):\n'
        '        try:\n'
        '            st.session_state["nombre_proyecto"] = _nombre_guardar\n'
        '            _slug_guardado = guardar_proyecto_actual(_nombre_guardar)\n'
        '            st.success(f"✅ Proyecto «{_nombre_guardar}» guardado correctamente.")\n'
        '            st.rerun()\n'
        '        except Exception as _e_pm:\n'
        '            st.error(f"Error al guardar: {_e_pm}")\n'
        '    st.divider()\n'
        '    if not _proyectos:\n'
        '        st.info(\n'
        '            "No hay proyectos guardados todavía. "\n'
        '            "Ingresa los datos del proyecto y pulsa **💾 Guardar** para crear el primero."\n'
        '        )\n'
        '    else:\n'
        '        st.markdown(f"**📂 Proyectos guardados** ({len(_proyectos)})")\n'
        '        for _p in _proyectos:\n'
        '            _es_actual = _p["nombre"].strip().lower() == _nombre_actual.strip().lower()\n'
        '            _fecha_corta = _p["guardado"][:16].replace("T", " ") if _p["guardado"] else "—"\n'
        '            _e_ac_label  = f\'{_p["e_ac_kWh"]:,.0f} kWh/año\' if _p["e_ac_kWh"] > 0 else "sin E_ac"\n'
        '            _area_label  = f\'{_p["area_m2"]:.0f} m²\' if _p["area_m2"] > 0 else "—"\n'
        '            _tag = " 🔵 **(actual)**" if _es_actual else ""\n'
        '            _pc1, _pc2, _pc3 = st.columns([4, 1, 1])\n'
        '            _pc1.markdown(\n'
        '                f"**{_p[\'nombre\']}**{_tag}  \\n"\n'
        '                f"<span style=\'color:#888;font-size:0.85em\'>"\n'
        '                f"{_p[\'ciudad\']} · {_area_label} · {_e_ac_label} · {_fecha_corta}"\n'
        '                f"</span>",\n'
        '                unsafe_allow_html=True,\n'
        '            )\n'
        '            if _pc2.button("📂 Cargar", key=f"_pm_cargar_{_p[\'slug\']}", use_container_width=True):\n'
        '                try:\n'
        '                    _nombre_cargado = cargar_proyecto(_p["slug"])\n'
        '                    st.success(f"✅ Proyecto «{_nombre_cargado}» cargado. Revisa los datos abajo.")\n'
        '                    st.rerun()\n'
        '                except Exception as _e_carga:\n'
        '                    st.error(f"Error al cargar: {_e_carga}")\n'
        '            if _pc3.button("🗑️", key=f"_pm_del_{_p[\'slug\']}", help="Eliminar proyecto", use_container_width=True):\n'
        '                eliminar_proyecto(_p["slug"])\n'
        '                st.rerun()\n'
        '    st.caption(\n'
        '        "💡 Los resultados de simulación (Producción, Bypass, Motor IV) "\n'
        '        "no se guardan — deberás volver a ejecutarlos tras cargar un proyecto. "\n'
        '        "Los datos de entrada (ciudad, área, equipos, presupuesto) sí se preservan."\n'
        '    )\n'
        '\n'
        '# ── Tipos de instalación con defaults técnicos'
    )

    if OLD_TITLE_BLOCK in src:
        src = src.replace(OLD_TITLE_BLOCK, NEW_TITLE_BLOCK, 1)
        print("  [✓] B2: expander 'Mis Proyectos' insertado.")
    else:
        print("  [ADVERTENCIA] B2: no se encontró bloque ancla exacto.")
        print("    Asegúrate de que el archivo del servidor tenga exactamente:")
        print('      st.title("🏠 Datos del Proyecto")')
        print('    seguido de una línea en blanco y:')
        print('      # ── Tipos de instalación con defaults técnicos')

    PROY1.write_text(src, encoding="utf-8")
    print(f"  [✓] {PROY1.name} actualizado.")

# ── Crear directorio de proyectos si no existe ────────────────────────────────
import os
_dir_proy = BASE / "datos" / "proyectos"
os.makedirs(_dir_proy, exist_ok=True)
print(f"\n[✓] Directorio de proyectos listo: {_dir_proy}")

# ── Resumen ───────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("[✓] Parche #63 aplicado.")
print("\nPróximo paso:")
print("  pm2 restart streamlit-bipv")
print("\nVerificación:")
print("  1. Abre Página 1 — aparece expander '📁 Mis Proyectos'")
print("  2. Escribe nombre → 💾 Guardar → aparece en la lista")
print("  3. Cambia proyecto → 📂 Cargar → datos se actualizan")
print("  4. Archivos en: bipv_python/datos/proyectos/*.json")
