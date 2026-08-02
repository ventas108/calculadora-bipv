#!/usr/bin/env python3
"""Parche #24 — Detectar columnas del catálogo de baterías automáticamente.

Distingue entre:
  (a) columna presente en el Excel pero celda vacía para un modelo
  (b) ningún alias de esa columna existe en el Excel — todos los modelos la pierden silenciosamente

Cambios:
  - datos/catalogo_baterias_excel.py:
      + _CAMPO_ALIASES_SUGERIDOS, _CAMPOS_CRITICOS, _CAMPOS_IMPORTANTES
      + diagnostico_catalogo() agrega "campos_sin_columna_excel"
  - pages/11_🔋_Baterias_y_Balance.py:
      + st.error para columnas críticas totalmente ausentes del Excel
      + st.warning para columnas importantes totalmente ausentes
      + Expander reorganizado en ①②③ con tabla accionable

Aplica desde /var/www/bipv/calculadora-bipv/:
    python3 bipv_python/scripts/patch_detectar_columnas_baterias.py
"""
import pathlib, sys

BASE = pathlib.Path(__file__).resolve().parents[1]  # bipv_python/
ROOT = BASE.parent                                   # calculadora-bipv/


def patch(path: pathlib.Path, old: str, new: str, tag: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        first_line = new.strip().splitlines()[0].strip()
        if first_line in text:
            print(f"[SKIP] {tag} — parece ya aplicado en {path.name}")
        else:
            print(f"[WARN] {tag} — patrón no encontrado en {path.name}. Revisa manualmente.")
        return False
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"[OK]   {tag}")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 1. datos/catalogo_baterias_excel.py — constantes + lógica en diagnostico
# ─────────────────────────────────────────────────────────────────────────────
CAT = ROOT / "datos" / "catalogo_baterias_excel.py"
if not CAT.exists():
    CAT = BASE / "datos" / "catalogo_baterias_excel.py"

# 1-a. Agregar constantes después de _NUM_KEYS
patch(
    CAT,
    "# Claves numéricas internas\n"
    "_NUM_KEYS = {\"capacidad_kWh\", \"potencia_kW\", \"voltaje_V\",\n"
    "             \"dod_pct\", \"ciclos_vida\", \"eta_rte_pct\",\n"
    "             \"costo_usd\", \"garantia_anos\"}",
    "# Claves numéricas internas\n"
    "_NUM_KEYS = {\"capacidad_kWh\", \"potencia_kW\", \"voltaje_V\",\n"
    "             \"dod_pct\", \"ciclos_vida\", \"eta_rte_pct\",\n"
    "             \"costo_usd\", \"garantia_anos\"}\n"
    "\n"
    "# ── #24 — Aliases canónicos por campo (para mensajes de acción en UI) ─────────\n"
    "# Lista de nombres de columna sugeridos para agregar al Excel si el campo falta.\n"
    "_CAMPO_ALIASES_SUGERIDOS: dict = {\n"
    "    \"capacidad_kWh\": [\"Capacidad (kWh)\", \"Energía Nominal (kWh)\", \"Energy (kWh)\"],\n"
    "    \"potencia_kW\":   [\"Potencia Continua (kW)\", \"Potencia Max (kW)\", \"Continuous Power (kW)\"],\n"
    "    \"voltaje_V\":     [\"Voltaje Nominal (V)\", \"Tensión Nominal (V)\", \"Nominal Voltage (V)\"],\n"
    "    \"dod_pct\":       [\"DoD Máximo (%)\", \"Profundidad Descarga (%)\", \"Depth of Discharge (%)\"],\n"
    "    \"ciclos_vida\":   [\"Ciclos de Vida\", \"Cycle Life\", \"Cycles\"],\n"
    "    \"eta_rte_pct\":   [\"Eficiencia RTE (%)\", \"Round-trip Efficiency (%)\", \"RTE (%)\"],\n"
    "    \"tipo\":          [\"Tecnología\", \"Química\", \"Chemistry\"],\n"
    "    \"costo_usd\":     [\"Costo (USD)\", \"Precio (USD)\", \"Price (USD)\"],\n"
    "    \"garantia_anos\": [\"Garantía (años)\", \"Warranty (years)\"],\n"
    "    \"fabricante\":    [\"Fabricante\", \"Manufacturer\"],\n"
    "}\n"
    "\n"
    "# Campos que bloquean el dimensionamiento si no se encuentran en el Excel\n"
    "_CAMPOS_CRITICOS    = {\"capacidad_kWh\", \"potencia_kW\"}\n"
    "# Campos que afectan precisión pero tienen defaults seguros\n"
    "_CAMPOS_IMPORTANTES = {\"dod_pct\", \"eta_rte_pct\", \"ciclos_vida\"}",
    "catalogo_baterias_excel.py — agregar _CAMPO_ALIASES_SUGERIDOS",
)

# 1-b. Actualizar diagnostico_catalogo() para calcular campos_sin_columna_excel
patch(
    CAT,
    "    # Columnas del Excel que no están en _COL_MAP\n"
    "    for h in range(5):\n"
    "        try:\n"
    "            df_cand = pd.read_excel(_EXCEL, sheet_name=sheet_found,\n"
    "                                    header=h, engine=\"openpyxl\")\n"
    "            cols = [_normalizar_col(c) for c in df_cand.columns]\n"
    "            if any(c.lower() in _MODELO_ALIASES for c in cols):\n"
    "                mapeadas   = set(_COL_MAP.keys())\n"
    "                no_mapeadas = [c for c in cols if c not in mapeadas\n"
    "                               and c.lower() not in _MODELO_ALIASES\n"
    "                               and \"unnamed\" not in c.lower()]\n"
    "                info[\"columnas_no_mapeadas\"] = no_mapeadas\n"
    "                break\n"
    "        except Exception:\n"
    "            continue\n"
    "\n"
    "    return info",
    "    # Columnas del Excel que no están en _COL_MAP  +  campos sin ningún alias en Excel\n"
    "    for h in range(5):\n"
    "        try:\n"
    "            df_cand = pd.read_excel(_EXCEL, sheet_name=sheet_found,\n"
    "                                    header=h, engine=\"openpyxl\")\n"
    "            cols = [_normalizar_col(c) for c in df_cand.columns]\n"
    "            if any(c.lower() in _MODELO_ALIASES for c in cols):\n"
    "                mapeadas    = set(_COL_MAP.keys())\n"
    "                no_mapeadas = [c for c in cols if c not in mapeadas\n"
    "                               and c.lower() not in _MODELO_ALIASES\n"
    "                               and \"unnamed\" not in c.lower()]\n"
    "                info[\"columnas_no_mapeadas\"] = no_mapeadas\n"
    "\n"
    "                # ── #24 — Campos internos cuyo alias NO aparece en el Excel ────\n"
    "                cols_excel_set = set(cols)\n"
    "                campos_sin_columna = []\n"
    "                for campo_int, aliases_sug in _CAMPO_ALIASES_SUGERIDOS.items():\n"
    "                    aliases_del_campo = [k for k, v in _COL_MAP.items() if v == campo_int]\n"
    "                    if not any(a in cols_excel_set for a in aliases_del_campo):\n"
    "                        campos_sin_columna.append({\n"
    "                            \"campo\":              campo_int,\n"
    "                            \"critico\":            campo_int in _CAMPOS_CRITICOS,\n"
    "                            \"importante\":         campo_int in _CAMPOS_IMPORTANTES,\n"
    "                            \"columnas_sugeridas\": aliases_sug,\n"
    "                        })\n"
    "                info[\"campos_sin_columna_excel\"] = campos_sin_columna\n"
    "                break\n"
    "        except Exception:\n"
    "            continue\n"
    "\n"
    "    return info",
    "catalogo_baterias_excel.py — diagnostico_catalogo() agrega campos_sin_columna_excel",
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. pages/11_🔋_Baterias_y_Balance.py — nueva UI de diagnóstico
# ─────────────────────────────────────────────────────────────────────────────
BAT = ROOT / "pages" / "11_🔋_Baterias_y_Balance.py"
if not BAT.exists():
    BAT = BASE / "pages" / "11_🔋_Baterias_y_Balance.py"

OLD_UI = (
    "else:\n"
    "    _n_modelos    = _diag.get(\"modelos_cargados\", len(cat_bat))\n"
    "    _incompletos  = _diag.get(\"modelos_incompletos\", [])\n"
    "    _no_mapeadas  = _diag.get(\"columnas_no_mapeadas\", [])\n"
    "\n"
    "    if _incompletos or _no_mapeadas:\n"
    "        st.warning(\n"
    "            f\"🟡 **Catálogo parcial** — hoja `{_hoja_usada}` · \"\n"
    "            f\"**{_n_modelos} modelos** cargados · \"\n"
    "            f\"{len(_incompletos)} modelos con datos incompletos\"\n"
    "            + (f\" · {len(_no_mapeadas)} columnas no reconocidas\" if _no_mapeadas else \"\")\n"
    "        )\n"
    "    else:\n"
    "        st.success(\n"
    "            f\"✅ **Catálogo OK** — hoja `{_hoja_usada}` · **{_n_modelos} modelos** · todos los campos reconocidos\"\n"
    "        )\n"
    "\n"
    "# ── #24 — Expander de diagnóstico detallado ───────────────────────────────────\n"
    "if tiene_catalogo:\n"
    "    _incompletos = _diag.get(\"modelos_incompletos\", [])\n"
    "    _no_mapeadas = _diag.get(\"columnas_no_mapeadas\", [])\n"
    "    if _incompletos or _no_mapeadas:\n"
    "        with st.expander(\"🔍 Diagnóstico detallado del catálogo\"):\n"
    "            if _no_mapeadas:\n"
    "                st.markdown(\"**Columnas del Excel NO reconocidas por el loader:**\")\n"
    "                st.code(\", \".join(_no_mapeadas))\n"
    "                st.caption(\n"
    "                    \"Estas columnas están en el Excel pero no tienen un alias en el loader. \"\n"
    "                    \"Si contienen datos importantes (voltaje, DoD, ciclos…), agrega el nombre exacto \"\n"
    "                    \"al `_COL_MAP` en `datos/catalogo_baterias_excel.py`.\"\n"
    "                )\n"
    "            if _incompletos:\n"
    "                st.markdown(\"**Modelos con campos críticos faltantes:**\")\n"
    "                rows = []\n"
    "                for m in _incompletos:\n"
    "                    rows.append({\n"
    "                        \"Modelo\": m[\"modelo\"],\n"
    "                        \"Campos faltantes\": \", \".join(m[\"campos_faltantes\"]) if m[\"campos_faltantes\"] else \"—\",\n"
    "                        \"Ficha marcada\": \"✅ Sí\" if m.get(\"datos_completos\") else \"🟡 No\",\n"
    "                    })\n"
    "                st.dataframe(\n"
    "                    pd.DataFrame(rows), use_container_width=True, hide_index=True\n"
    "                )\n"
    "                st.caption(\n"
    "                    \"Modelos sin `capacidad_kWh` no pueden dimensionarse. \"\n"
    "                    \"Modelos sin `dod_pct`, `eta_rte_pct` o `ciclos_vida` usan valores por defecto \"\n"
    "                    \"(80% DoD · 95% RTE · 3000 ciclos).\"\n"
    "                )\n"
    "elif not tiene_catalogo:\n"
    "    with st.expander(\"📋 Columnas esperadas en la hoja Catalogo_Baterias\"):\n"
    "        st.markdown(\"\"\"\n"
    "| Columna | Descripción | Ejemplo |\n"
    "|---|---|---|\n"
    "| Modelo | Nombre del modelo | BYD Battery-Box HVM |\n"
    "| Datos completos (Si/No) | Si / No | Si |\n"
    "| Capacidad (kWh) | Capacidad nominal | 11.04 |\n"
    "| Potencia Continua (kW) | Potencia de carga/descarga | 5.0 |\n"
    "| Voltaje Nominal (V) | Tensión del bus DC | 48 |\n"
    "| DoD Máximo (%) | Profundidad de descarga máxima | 90 |\n"
    "| Ciclos de Vida | Ciclos garantizados a DoD nominal | 4000 |\n"
    "| Eficiencia RTE (%) | Rendimiento round-trip | 96 |\n"
    "| Tecnología | Química | LFP |\n"
    "| Costo (USD) | Precio unitario sin IVA | 4200 |\n"
    "| Garantía (años) | Años de garantía | 10 |\n"
    "        \"\"\")"
)

NEW_UI = (
    "else:\n"
    "    _n_modelos   = _diag.get(\"modelos_cargados\", len(cat_bat))\n"
    "    _incompletos = _diag.get(\"modelos_incompletos\", [])\n"
    "    _no_mapeadas = _diag.get(\"columnas_no_mapeadas\", [])\n"
    "    # #24 — campos cuyo alias no apareció en NINGUNA columna del Excel\n"
    "    _ausentes    = _diag.get(\"campos_sin_columna_excel\", [])\n"
    "\n"
    "    _criticos_aus    = [c for c in _ausentes if c.get(\"critico\")]\n"
    "    _importantes_aus = [c for c in _ausentes if c.get(\"importante\") and not c.get(\"critico\")]\n"
    "\n"
    "    # ── Alertas de columnas ausentes — visibles sin abrir el expander ──────────\n"
    "    if _criticos_aus:\n"
    "        st.error(\n"
    "            \"🔴 **Columnas críticas ausentes en el Excel** — sin ellas ninguna batería \"\n"
    "            \"puede dimensionarse: `\"\n"
    "            + \"`, `\".join(c[\"campo\"] for c in _criticos_aus) + \"`  \\n\"\n"
    "            \"Abre el diagnóstico ↓ para ver exactamente qué encabezados agregar al Excel.\"\n"
    "        )\n"
    "    if _importantes_aus:\n"
    "        st.warning(\n"
    "            \"⚠️ **Columnas importantes ausentes en el Excel**: `\"\n"
    "            + \"`, `\".join(c[\"campo\"] for c in _importantes_aus) + \"`  \\n\"\n"
    "            \"Se usarán valores por defecto (80 % DoD · 95 % RTE · 3 000 ciclos). \"\n"
    "            \"Abre el diagnóstico ↓ para ver qué encabezados agregar.\"\n"
    "        )\n"
    "\n"
    "    if _ausentes or _incompletos or _no_mapeadas:\n"
    "        st.warning(\n"
    "            f\"🟡 **Catálogo parcial** — hoja `{_hoja_usada}` · **{_n_modelos} modelos** cargados\"\n"
    "            + (f\" · {len(_ausentes)} columnas ausentes en Excel\" if _ausentes else \"\")\n"
    "            + (f\" · {len(_incompletos)} modelos con valores vacíos\" if _incompletos else \"\")\n"
    "            + (f\" · {len(_no_mapeadas)} columnas no reconocidas\" if _no_mapeadas else \"\")\n"
    "        )\n"
    "    else:\n"
    "        st.success(\n"
    "            f\"✅ **Catálogo OK** — hoja `{_hoja_usada}` · **{_n_modelos} modelos** · \"\n"
    "            \"todas las columnas reconocidas y sin valores vacíos\"\n"
    "        )\n"
    "\n"
    "# ── #24 — Expander de diagnóstico detallado ──────────────────────────────────\n"
    "if tiene_catalogo:\n"
    "    _incompletos = _diag.get(\"modelos_incompletos\", [])\n"
    "    _no_mapeadas = _diag.get(\"columnas_no_mapeadas\", [])\n"
    "    _ausentes    = _diag.get(\"campos_sin_columna_excel\", [])\n"
    "    if _ausentes or _incompletos or _no_mapeadas:\n"
    "        with st.expander(\"🔍 Diagnóstico detallado del catálogo\"):\n"
    "\n"
    "            # ① Columnas completamente ausentes del Excel (#24)\n"
    "            if _ausentes:\n"
    "                st.markdown(\"**① Columnas sin ningún alias en el Excel:**\")\n"
    "                st.caption(\n"
    "                    \"Estas columnas internas no tienen NINGUNA columna mapeada en tu Excel. \"\n"
    "                    \"Agrega **UNA** de las opciones sugeridas como encabezado de columna en \"\n"
    "                    f\"la hoja `{_diag.get('hoja_usada', 'Catalogo_Baterias')}`.\"\n"
    "                )\n"
    "                _rows_aus = []\n"
    "                for _c in _ausentes:\n"
    "                    _nivel = (\n"
    "                        \"🔴 Crítico\"    if _c.get(\"critico\")    else\n"
    "                        \"🟡 Importante\" if _c.get(\"importante\") else\n"
    "                        \"🔵 Opcional\"\n"
    "                    )\n"
    "                    _rows_aus.append({\n"
    "                        \"Campo interno\":  _c[\"campo\"],\n"
    "                        \"Nivel\":          _nivel,\n"
    "                        \"Agregar UNA de estas columnas al Excel\":\n"
    "                            \" | \".join(_c.get(\"columnas_sugeridas\", [])),\n"
    "                    })\n"
    "                st.dataframe(pd.DataFrame(_rows_aus), use_container_width=True, hide_index=True)\n"
    "\n"
    "            # ② Columnas del Excel no reconocidas\n"
    "            if _no_mapeadas:\n"
    "                st.markdown(\"**② Columnas del Excel NO reconocidas por el loader:**\")\n"
    "                st.code(\", \".join(_no_mapeadas))\n"
    "                st.caption(\n"
    "                    \"Estas columnas están en el Excel pero no tienen un alias en el loader. \"\n"
    "                    \"Si contienen datos importantes, agrega el nombre exacto al `_COL_MAP` \"\n"
    "                    \"en `datos/catalogo_baterias_excel.py`.\"\n"
    "                )\n"
    "\n"
    "            # ③ Modelos con valores vacíos (la columna existe pero la celda está vacía)\n"
    "            if _incompletos:\n"
    "                st.markdown(\"**③ Modelos con valores vacíos en campos críticos:**\")\n"
    "                _rows_inc = []\n"
    "                for _m in _incompletos:\n"
    "                    _rows_inc.append({\n"
    "                        \"Modelo\":                   _m[\"modelo\"],\n"
    "                        \"Campos con valor vacío\":   \", \".join(_m[\"campos_faltantes\"]) if _m[\"campos_faltantes\"] else \"—\",\n"
    "                        \"Ficha marcada completa\":   \"✅ Sí\" if _m.get(\"datos_completos\") else \"🟡 No\",\n"
    "                    })\n"
    "                st.dataframe(\n"
    "                    pd.DataFrame(_rows_inc), use_container_width=True, hide_index=True\n"
    "                )\n"
    "                st.caption(\n"
    "                    \"Modelos sin `capacidad_kWh` no pueden dimensionarse. \"\n"
    "                    \"Modelos sin `dod_pct`, `eta_rte_pct` o `ciclos_vida` usan valores por defecto \"\n"
    "                    \"(80 % DoD · 95 % RTE · 3 000 ciclos).\"\n"
    "                )\n"
    "elif not tiene_catalogo:\n"
    "    with st.expander(\"📋 Columnas esperadas en la hoja Catalogo_Baterias\"):\n"
    "        st.markdown(\"\"\"\n"
    "| Columna | Descripción | Ejemplo |\n"
    "|---|---|---|\n"
    "| Modelo | Nombre del modelo | BYD Battery-Box HVM |\n"
    "| Datos completos (Si/No) | Si / No | Si |\n"
    "| Capacidad (kWh) | Capacidad nominal | 11.04 |\n"
    "| Potencia Continua (kW) | Potencia de carga/descarga | 5.0 |\n"
    "| Voltaje Nominal (V) | Tensión del bus DC | 48 |\n"
    "| DoD Máximo (%) | Profundidad de descarga máxima | 90 |\n"
    "| Ciclos de Vida | Ciclos garantizados a DoD nominal | 4000 |\n"
    "| Eficiencia RTE (%) | Rendimiento round-trip | 96 |\n"
    "| Tecnología | Química | LFP |\n"
    "| Costo (USD) | Precio unitario sin IVA | 4200 |\n"
    "| Garantía (años) | Años de garantía | 10 |\n"
    "        \"\"\")"
)

patch(BAT, OLD_UI, NEW_UI, "Baterias_y_Balance.py — nueva UI de diagnóstico #24")

print("\n✅ Parche #24 completado. Reinicia el proceso:")
print("   pm2 restart streamlit-bipv")
