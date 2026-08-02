#!/usr/bin/env python3
"""Parche #93 — Sincronizar tarifa eléctrica Proyecto ↔ Financiero en tiempo real.

Réplica del patrón TRM:
  - Crea calculos/tarifa_utils.py (módulo de sincronización)
  - Proyecto: city-change llama set_tarifa_from_ciudad(), widget reemplaza number_input
  - Financiero: widget reemplaza number_input; init_tarifa() al inicio de página

Aplica desde /var/www/bipv/calculadora-bipv/:
    python3 bipv_python/scripts/patch_tarifa_sync.py
"""
import pathlib, sys, shutil, textwrap

BASE = pathlib.Path(__file__).resolve().parents[1]  # bipv_python/
ROOT = BASE.parent                                   # calculadora-bipv/

# ─────────────────────────────────────────────────────────────────────────────
# 0. Crear tarifa_utils.py en calculos/
# ─────────────────────────────────────────────────────────────────────────────
TARIFA_UTILS_SRC = pathlib.Path(__file__).parent.parent / "calculos" / "tarifa_utils.py"

if not TARIFA_UTILS_SRC.exists():
    # El archivo debería haber llegado con el git pull / rsync.
    # Si no existe, lo creamos inline.
    TARIFA_UTILS_CODE = textwrap.dedent('''\
        """Tarifa eléctrica local \\u2014 sincronizaci\\u00f3n entre Proyecto y Financiero.

        R\\u00e9plica del patr\\u00f3n TRM: fuente de verdad global en session_state,
        widget editable con provenance (ciudad, operador, fuente).

        Keys de session_state:
          tarifa_cop_kwh          \\u2014 valor COP/kWh (clave can\\u00f3nica)
          tarifa_cop_kWh          \\u2014 alias legacy
          tarifa_ciudad_origen    \\u2014 ciudad donde se pre-carg\\u00f3 la tarifa
          tarifa_operador         \\u2014 operador local (EPM, Codensa, EDEQ\\u2026)
          tarifa_fuente           \\u2014 "cat\\u00e1logo", "Proyecto", "Financiero", "valor por defecto"
        """
        from __future__ import annotations
        import streamlit as st

        TARIFA_DEFAULT    = 850.0
        _KEY_VALOR        = "tarifa_cop_kwh"
        _KEY_VALOR_LEGACY = "tarifa_cop_kWh"
        _KEY_CIUDAD       = "tarifa_ciudad_origen"
        _KEY_OPERADOR     = "tarifa_operador"
        _KEY_FUENTE       = "tarifa_fuente"

        _ALERTA_MUY_BAJA  = 300.0
        _ALERTA_BAJA      = 500.0
        _ALERTA_ALTA      = 1_800.0
        _LABELS_FUENTE    = {"proy": "Proyecto", "fin": "Financiero"}


        def init_tarifa(ciudad: str = "", ciudades_dict: dict | None = None) -> None:
            if _KEY_VALOR in st.session_state:
                return
            valor = TARIFA_DEFAULT; operador = ""; fuente = "valor por defecto"
            if ciudad and ciudades_dict:
                c = ciudades_dict.get(ciudad, {})
                if "tarifa_comercial_cop_kwh" in c:
                    valor = float(c["tarifa_comercial_cop_kwh"]); fuente = "cat\\u00e1logo"
                operador = c.get("operador", "")
            st.session_state[_KEY_VALOR]        = valor
            st.session_state[_KEY_VALOR_LEGACY] = valor
            st.session_state[_KEY_CIUDAD]       = ciudad or "\\u2014"
            st.session_state[_KEY_OPERADOR]     = operador
            st.session_state[_KEY_FUENTE]       = fuente


        def set_tarifa_from_ciudad(ciudad: str, ciudades_dict: dict) -> None:
            c = ciudades_dict.get(ciudad, {}); operador = c.get("operador", "")
            if "tarifa_comercial_cop_kwh" in c:
                valor = float(c["tarifa_comercial_cop_kwh"])
                st.session_state[_KEY_VALOR]        = valor
                st.session_state[_KEY_VALOR_LEGACY] = valor
            st.session_state[_KEY_CIUDAD]   = ciudad
            st.session_state[_KEY_OPERADOR] = operador
            st.session_state[_KEY_FUENTE]   = "cat\\u00e1logo"


        def tarifa_widget(page_key: str = "default") -> float:
            _val      = float(st.session_state.get(_KEY_VALOR, TARIFA_DEFAULT))
            _ciudad   = st.session_state.get(_KEY_CIUDAD, "")
            _operador = st.session_state.get(_KEY_OPERADOR, "")
            _fuente   = st.session_state.get(_KEY_FUENTE, "valor por defecto")

            _ciudad_info = ""
            if _ciudad and _ciudad not in ("", "\\u2014"):
                _ciudad_info = f"\\ud83d\\udccd **{_ciudad}**" + (f" ({_operador})" if _operador else "")

            _help = (
                "Tarifa comercial/industrial sin subsidio.  \\n"
                "Bogot\\u00e1 2024: ~550\\u2013750 COP/kWh \\u00b7 Residencial est. 4\\u20136: ~600\\u2013850 COP/kWh.  \\n"
                + (_ciudad_info + "  \\n" if _ciudad_info else "")
                + f"\\ud83d\\udd01 Fuente actual: *{_fuente}*  \\n"
                "Edita el valor aqu\\u00ed y se propagar\\u00e1 autom\\u00e1ticamente a la otra secci\\u00f3n."
            )
            nuevo = st.number_input(
                "Tarifa electricidad (COP/kWh)",
                min_value=100.0, max_value=2_000.0,
                value=_val, step=25.0,
                key=f"_tarifa_num_{page_key}",
                help=_help,
            )
            if _ciudad and _ciudad not in ("", "\\u2014"):
                _icono = "\\ud83d\\udccd" if _fuente == "cat\\u00e1logo" else "\\u270f\\ufe0f"
                _op_txt = f" \\u00b7 {_operador}" if _operador else ""
                st.caption(f"{_icono} **{_ciudad}{_op_txt}** \\u00b7 Fuente: {_fuente} \\u00b7 {nuevo:,.0f} COP/kWh")
            else:
                st.caption(f"\\u270f\\ufe0f {_fuente} \\u00b7 {nuevo:,.0f} COP/kWh")

            if nuevo < _ALERTA_MUY_BAJA:
                st.error(f"\\u26a0\\ufe0f Tarifa {nuevo:,.0f} COP/kWh parece muy baja (m\\u00ednimo ~300 COP/kWh). Revisa el valor.")
            elif nuevo < _ALERTA_BAJA:
                st.warning(f"\\u26a0\\ufe0f Tarifa {nuevo:,.0f} COP/kWh es baja \\u2014 t\\u00edpica de residencial subsidiado. Verifica con la factura real.")
            elif nuevo > _ALERTA_ALTA:
                st.warning(f"\\u26a0\\ufe0f Tarifa {nuevo:,.0f} COP/kWh parece alta (ref. m\\u00e1x. ~1.800 COP/kWh). Confirma con la factura del cliente.")

            st.session_state[_KEY_VALOR]        = nuevo
            st.session_state[_KEY_VALOR_LEGACY] = nuevo
            if nuevo != _val:
                st.session_state[_KEY_FUENTE] = _LABELS_FUENTE.get(page_key, page_key)
            return nuevo
    ''')
    TARIFA_UTILS_SRC.write_text(TARIFA_UTILS_CODE, encoding="utf-8")
    print(f"[OK] calculos/tarifa_utils.py creado inline (no venía en el repo).")
else:
    print(f"[OK] calculos/tarifa_utils.py ya existe — sin cambios.")


def patch(path: pathlib.Path, old: str, new: str, tag: str) -> bool:
    """Reemplaza `old` por `new` en `path`. Devuelve True si aplicó."""
    text = path.read_text(encoding="utf-8")
    if old not in text:
        if new.strip() in text or new.strip().splitlines()[0].strip() in text:
            print(f"[SKIP] {tag} — parece ya aplicado en {path.name}")
        else:
            print(f"[WARN] {tag} — patrón no encontrado en {path.name}. Revisa manualmente.")
        return False
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"[OK]   {tag}")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 1. pages/1_🏠_Proyecto.py
# ─────────────────────────────────────────────────────────────────────────────
PROY = ROOT / "pages" / "1_🏠_Proyecto.py"
if not PROY.exists():
    PROY = BASE / "pages" / "1_🏠_Proyecto.py"

# 1-a. Agregar import de tarifa_utils
patch(
    PROY,
    "from calculos.tz_utils import utc_offset_latam, tz_label",
    "from calculos.tz_utils import utc_offset_latam, tz_label\n"
    "from calculos.tarifa_utils import init_tarifa, set_tarifa_from_ciudad, tarifa_widget",
    "Proyecto — import tarifa_utils",
)

# 1-b. city-change handler: añadir set_tarifa_from_ciudad + metadata
patch(
    PROY,
    "        # Pre-cargar tarifa del operador local de la nueva ciudad\n"
    "        if \"tarifa_comercial_cop_kwh\" in c_nueva:\n"
    "            st.session_state[\"tarifa_cop_kwh\"] = float(c_nueva[\"tarifa_comercial_cop_kwh\"])",
    "        # Pre-cargar tarifa del operador local de la nueva ciudad\n"
    "        set_tarifa_from_ciudad(ciudad, CIUDADES)",
    "Proyecto — city-change usa set_tarifa_from_ciudad()",
)

# 1-c. Antes de renderizar el widget de tarifa: llamar init_tarifa + reemplazar number_input
OLD_WIDGET_PROY = """\
    _c_actual = CIUDADES.get(ciudad, {})
    _tarifa_default = float(
        st.session_state.get(
            "tarifa_cop_kwh",
            _c_actual.get("tarifa_comercial_cop_kwh", 850.0)
        )
    )
    _operador_txt = _c_actual.get("operador", "")
    _operador_help = f" (operador: **{_operador_txt}**)" if _operador_txt else ""
    tarifa_kwh = st.number_input(
        "Tarifa local (COP/kWh)",
        min_value=100.0, max_value=2000.0,
        value=_tarifa_default,
        step=10.0,
        help=(
            f"Tarifa comercial/industrial sin subsidio{_operador_help}. "
            "Se actualiza automáticamente al cambiar ciudad. "
            "Ajusta con el valor real de la factura del cliente."
        )
    )"""

NEW_WIDGET_PROY = """\
    # ── Tarifa sincronizada con Financiero — patrón TRM ──────────────────────
    init_tarifa(ciudad, CIUDADES)   # no-op si ya fue inicializada
    tarifa_kwh = tarifa_widget("proy")"""

patch(PROY, OLD_WIDGET_PROY, NEW_WIDGET_PROY, "Proyecto — reemplazar number_input con tarifa_widget()")


# ─────────────────────────────────────────────────────────────────────────────
# 2. pages/7_💰_Financiero.py
# ─────────────────────────────────────────────────────────────────────────────
FIN = ROOT / "pages" / "7_💰_Financiero.py"
if not FIN.exists():
    FIN = BASE / "pages" / "7_💰_Financiero.py"

# 2-a. Agregar import de tarifa_widget e init_tarifa
patch(
    FIN,
    "from calculos.trm_utils import init_trm, trm_widget",
    "from calculos.trm_utils import init_trm, trm_widget\n"
    "from calculos.tarifa_utils import init_tarifa, tarifa_widget",
    "Financiero — import tarifa_utils",
)

# 2-b. Llamar init_tarifa() justo después de init_trm()
patch(
    FIN,
    "init_trm()   # fetch TRM del API en primera carga; session_state[\"tipo_cambio\"] listo antes de línea 126",
    "init_trm()   # fetch TRM del API en primera carga; session_state[\"tipo_cambio\"] listo antes de línea 126\n"
    "init_tarifa()   # garantiza tarifa_cop_kwh en session_state antes del panel preview",
    "Financiero — init_tarifa() al inicio de página",
)

# 2-c. Reemplazar number_input de tarifa en Sección 2
OLD_WIDGET_FIN = """\
with col_t1:
    # ── Tarifa sincronizada con Proyecto — fuente de verdad: tarifa_cop_kwh ──
    _tarifa_init = float(st.session_state.get(
        "tarifa_cop_kwh",                          # clave canónica (Proyecto)
        st.session_state.get("tarifa_cop_kWh", 650.0)  # fallback clave antigua
    ))
    tarifa_cop = st.number_input(
        "Tarifa electricidad (COP/kWh)",
        min_value=100.0, max_value=2000.0,
        value=_tarifa_init, step=25.0,
        help="Tarifa comercial/industrial Bogotá 2024: ~550–750 COP/kWh. "
             "Residencial estrato 4-6: ~600–850 COP/kWh. "
             "📍 Pre-cargada desde Proyecto.",
    )"""

NEW_WIDGET_FIN = """\
with col_t1:
    # ── Tarifa sincronizada con Proyecto — patrón TRM ─────────────────────────
    tarifa_cop = tarifa_widget("fin")"""

patch(FIN, OLD_WIDGET_FIN, NEW_WIDGET_FIN, "Financiero — reemplazar number_input con tarifa_widget()")

print("\n✅ Parche #93 completado. Reinicia el proceso:")
print("   pm2 restart streamlit-bipv")
