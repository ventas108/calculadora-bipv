"""Página 14 — Agregar, editar y eliminar paneles del catálogo (#65 + #129 + #130)."""
import streamlit as st
import pandas as pd

from calculos.pdf_panel_extractor import (
    extraer_parametros_panel, pdf_disponible, ocr_disponible
)
from datos.catalogo_paneles_excel import (
    guardar_panel_excel, cargar_catalogo_paneles,
    eliminar_panel_excel, actualizar_panel_excel,
)

st.set_page_config(page_title="Catálogo PDF — BIPV", page_icon="📋", layout="wide")
st.title("📋 Gestión del Catálogo de Paneles")

tab_agregar, tab_editar = st.tabs(["➕ Agregar desde PDF", "✏️ Editar / Eliminar"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — AGREGAR DESDE PDF (#65 + #129)
# ══════════════════════════════════════════════════════════════════════════════
with tab_agregar:
    st.caption(
        "Sube la ficha técnica (datasheet) de un panel FV en PDF. "
        "La app extrae automáticamente los parámetros eléctricos y te permite verificarlos "
        "antes de guardarlos en el catálogo Excel."
    )

    # ── Verificar disponibilidad de pdfplumber ────────────────────────────────
    if not pdf_disponible():
        st.error(
            "❌ **pdfplumber no está instalado.**  \n"
            "Ejecuta en el servidor:  \n"
            "```bash\n"
            "source bipv_python/venv/bin/activate\n"
            "pip install pdfplumber==0.11.4\n"
            "pm2 restart streamlit-bipv\n"
            "```"
        )
        st.stop()

    # ── OCR info banner ───────────────────────────────────────────────────────
    if not ocr_disponible():
        st.info(
            "ℹ️ **Soporte OCR no disponible** — Los PDFs escaneados (imágenes) no se pueden "
            "procesar automáticamente. Puedes igualmente subir el PDF; si no tiene texto "
            "seleccionable, el formulario aparecerá vacío para ingreso manual.  \n"
            "Para activar OCR instala en el servidor: "
            "`apt install tesseract-ocr tesseract-ocr-spa poppler-utils` + "
            "`pip install pdf2image pytesseract`",
            icon="🔍",
        )

    # ── Upload ────────────────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "Ficha técnica del panel (PDF)",
        type=["pdf"],
        help="Datasheets de Canadian Solar, Trina, LONGi, JA Solar, Jinko, Hanwha, REC, etc.",
    )

    if not uploaded:
        st.info("⬆️ Sube un PDF para comenzar.")
        st.stop()

    # ── Extraer parámetros ────────────────────────────────────────────────────
    with st.spinner("Analizando PDF…"):
        pdf_bytes = uploaded.read()
        data = extraer_parametros_panel(pdf_bytes)

    if "error" in data:
        st.error(data["error"])
        st.stop()

    # ── Banners de estado del análisis ────────────────────────────────────────
    es_escaneado = data.get("es_escaneado", False)
    uso_ocr      = data.get("uso_ocr", False)

    if uso_ocr:
        st.success(
            "✅ PDF escaneado procesado con **OCR** (Tesseract). "
            "Los valores pueden tener errores de lectura — revisa todos los campos con cuidado."
        )
    elif es_escaneado and not ocr_disponible():
        st.warning(
            "⚠️ **PDF escaneado sin texto seleccionable** — La extracción automática no "
            "está disponible porque el motor OCR no está instalado en este servidor. "
            "Completa los valores manualmente en el formulario de abajo."
        )
    elif es_escaneado and not uso_ocr:
        st.warning(
            "⚠️ **OCR no extrajo texto suficiente** — El PDF parece ser una imagen de baja "
            "calidad o resolución. Ingresa los valores manualmente."
        )
    else:
        st.success("✅ PDF analizado. Verifica y corrige los valores antes de guardar.")

    # ── Selector multi-modelo ─────────────────────────────────────────────────
    _modelos_det   = data.get("modelos_detectados", [])
    _vals_por_mod  = data.get("valores_por_modelo", {})

    if len(_modelos_det) >= 2:
        st.info(
            f"📋 **Ficha técnica multi-modelo** — se detectan **{len(_modelos_det)} modelos** "
            f"en columnas separadas: {', '.join(f'`{m}`' for m in _modelos_det)}  \n"
            "Selecciona el modelo que deseas agregar al catálogo para ver sus valores específicos."
        )
        _modelo_elegido = st.selectbox(
            "Modelo a agregar al catálogo",
            options=_modelos_det,
            key="sel_modelo_panel_mm",
        )
        # Sobrescribir campos variables (Pmax, Voc, Isc, Vmp, Imp) con los del modelo elegido
        _v = _vals_por_mod.get(_modelo_elegido, {})
        for _campo in ("Pmax", "Voc", "Isc", "Vmp", "Imp"):
            if _v.get(_campo) is not None:
                data[_campo] = _v[_campo]
        # Pre-llenar nombre del modelo con el código seleccionado
        if not data.get("modelo") or data["modelo"] in _modelos_det:
            data["modelo"] = _modelo_elegido

    # ── Formulario de verificación ────────────────────────────────────────────
    with st.form("form_panel_pdf"):
        st.subheader("📝 Datos extraídos — revisa y completa")

        c1, c2, c3 = st.columns(3)

        modelo = c1.text_input(
            "Nombre del modelo *",
            value=data.get("modelo") or "",
            help="Identificador único en el catálogo. Ej: CS6R-400MS",
        )
        marca = c2.text_input("Marca / Fabricante", value=data.get("marca") or "")

        _TECHS = ["", "Mono-Si", "Poly-Si", "CIS", "CdTe", "a-Si", "Thin Film", "HJT", "TOPCon", "Otro"]
        _tech_val = data.get("tecnologia") or ""
        _tech_idx = _TECHS.index(_tech_val) if _tech_val in _TECHS else 0
        tecnologia = c3.selectbox("Tecnología", _TECHS, index=_tech_idx)

        st.divider()
        st.markdown("**⚡ Parámetros eléctricos STC** (1000 W/m², 25 °C, AM 1.5)")

        d1, d2, d3, d4, d5 = st.columns(5)
        Pmax = d1.number_input("Pmax (W) *", value=float(data.get("Pmax") or 0), min_value=0.0, step=1.0, format="%.1f")
        Voc  = d2.number_input("Voc (V) *",  value=float(data.get("Voc")  or 0), min_value=0.0, step=0.1, format="%.2f")
        Isc  = d3.number_input("Isc (A) *",  value=float(data.get("Isc")  or 0), min_value=0.0, step=0.01, format="%.3f")
        Vmp  = d4.number_input("Vmp (V) *",  value=float(data.get("Vmp")  or 0), min_value=0.0, step=0.1, format="%.2f")
        Imp  = d5.number_input("Imp (A) *",  value=float(data.get("Imp")  or 0), min_value=0.0, step=0.01, format="%.3f")

        st.divider()
        st.markdown("**🌡️ Coeficientes de temperatura** (%/°C, típicamente negativos para Voc y Pmax)")

        e1, e2, e3, e4 = st.columns(4)
        coef_voc  = e1.number_input("β Voc (%/°C)",  value=float(data.get("CoefVoc")  or 0), step=0.001, format="%.4f")
        coef_isc  = e2.number_input("α Isc (%/°C)",  value=float(data.get("CoefIsc")  or 0), step=0.001, format="%.4f")
        coef_pmax = e3.number_input("γ Pmax (%/°C)", value=float(data.get("CoefPmax") or 0), step=0.001, format="%.4f")
        noct      = e4.number_input("NOCT (°C)",      value=float(data.get("NOCT")     or 45), min_value=0.0, step=0.5, format="%.1f")

        st.divider()
        st.markdown("**📐 Construcción**")

        f1, f2, f3, f4 = st.columns(4)
        n_s    = f1.number_input("Celdas en serie (Ns)", value=int(data.get("N_s") or 0), min_value=0, step=1)
        dims   = f2.text_input("Dimensiones (LxAxE mm)", value=data.get("dimensiones") or "")
        transp = f3.number_input("Transparencia (%)", value=0.0, min_value=0.0, max_value=100.0, step=1.0)
        costo  = f4.number_input("Costo (USD/ud)", value=0.0, min_value=0.0, step=1.0, format="%.2f")

        notas = st.text_area(
            "Notas / observaciones",
            placeholder="Fuente de datos, fecha de ficha, observaciones…",
            height=68,
            value="OCR-auto" if uso_ocr else ("PDF-escaneado-manual" if es_escaneado else ""),
        )

        _campos_ok = modelo.strip() and Pmax > 0
        submitted = st.form_submit_button(
            "💾 Guardar en catálogo",
            disabled=not _campos_ok,
            type="primary",
            help="Requiere al menos Nombre del modelo y Pmax." if not _campos_ok else "",
        )

    if submitted:
        _confianza = "OCR-auto" if uso_ocr else ("PDF-auto" if not es_escaneado else "Manual")
        _row = {
            "TipoPanel":          modelo.strip(),
            "Marca":              marca.strip(),
            "Tecnologia":         tecnologia,
            "PmaxWp":             Pmax if Pmax > 0 else None,
            "Voc_STC":            Voc  if Voc  > 0 else None,
            "Isc_STC":            Isc  if Isc  > 0 else None,
            "Vmp_STC":            Vmp  if Vmp  > 0 else None,
            "Imp_STC":            Imp  if Imp  > 0 else None,
            "CoefVoc_C":          coef_voc  if coef_voc  != 0 else None,
            "CoefT_C":            coef_pmax if coef_pmax != 0 else None,
            "NOCT_C":             noct if noct > 0 else None,
            "Ns (Celdas Serie)":  n_s  if n_s  > 0 else None,
            "DimensionesMM":      dims.strip() or None,
            "TransparenciaPct":   transp if transp > 0 else None,
            "CostoUSD":           costo if costo > 0 else None,
            "Notas":              notas.strip() or None,
            "Confianza":          _confianza,
        }
        try:
            nombre_guardado = guardar_panel_excel(_row)
            st.success(
                f"✅ **{nombre_guardado}** guardado en el catálogo.  \n"
                f"Ya puedes seleccionarlo en Dimensionamiento."
            )
            st.balloons()
        except Exception as e:
            st.error(f"❌ Error al guardar: {e}")

    # ── Texto extraído (debug) ────────────────────────────────────────────────
    with st.expander("🔍 Ver texto extraído del PDF (para diagnóstico)"):
        raw = data.get("texto_crudo", "")
        if raw:
            if uso_ocr:
                st.caption("🔍 Texto obtenido mediante OCR (Tesseract).")
            st.text_area("Texto crudo (primeros 4000 caracteres)", raw, height=300)
        else:
            if es_escaneado and not ocr_disponible():
                st.warning(
                    "El PDF es una imagen escaneada y el OCR no está disponible en este servidor. "
                    "Instala `tesseract-ocr` + `poppler-utils` + `pdf2image` + `pytesseract` para activarlo."
                )
            else:
                st.info("No se extrajo texto del PDF.")
        debug_tables = data.get("_debug_tables", "")
        if debug_tables:
            st.text_area("Tablas detectadas por pdfplumber (diagnóstico)", debug_tables, height=300)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — EDITAR / ELIMINAR (#130)
# ══════════════════════════════════════════════════════════════════════════════
with tab_editar:
    st.caption("Edita los datos de un panel existente o elimínalo del catálogo.")

    _cat = cargar_catalogo_paneles()

    if not _cat:
        st.info("El catálogo está vacío o no se pudo leer.")
        st.stop()

    # ── Filtros ───────────────────────────────────────────────────────────────
    _marcas   = sorted({v.get("marca", "") for v in _cat.values() if v.get("marca")})
    _tecnos   = sorted({v.get("tecnologia", "") for v in _cat.values() if v.get("tecnologia")})

    fc1, fc2, fc3 = st.columns([2, 2, 3])
    filtro_marca = fc1.selectbox("Filtrar por marca", ["Todas"] + _marcas, key="fil_marca")
    filtro_tecno = fc2.selectbox("Filtrar por tecnología", ["Todas"] + _tecnos, key="fil_tecno")
    filtro_texto = fc3.text_input("Buscar por nombre", placeholder="Escribe parte del modelo…", key="fil_texto")

    def _aplica_filtros(nombre, panel):
        if filtro_marca != "Todas" and panel.get("marca") != filtro_marca:
            return False
        if filtro_tecno != "Todas" and panel.get("tecnologia") != filtro_tecno:
            return False
        if filtro_texto and filtro_texto.lower() not in nombre.lower():
            return False
        return True

    _cat_filtrado = {k: v for k, v in sorted(_cat.items()) if _aplica_filtros(k, v)}
    st.caption(f"Mostrando {len(_cat_filtrado)} de {len(_cat)} paneles.")

    if not _cat_filtrado:
        st.info("Ningún panel coincide con los filtros.")
        st.stop()

    # ── Tabla editable ────────────────────────────────────────────────────────
    st.markdown("**Edita directamente las celdas y presiona «Guardar cambios»:**")

    _df_rows = []
    for nm, p in _cat_filtrado.items():
        _df_rows.append({
            "Modelo":        nm,
            "Marca":         p.get("marca", "") or "",
            "Tecnología":    p.get("tecnologia", "") or "",
            "Pmax (W)":      p.get("Pmax_stc"),
            "Voc (V)":       p.get("Voc"),
            "Isc (A)":       p.get("Isc"),
            "Vmp (V)":       p.get("Vmp"),
            "Imp (A)":       p.get("Imp"),
            "Ns":            p.get("N_s"),
            "β Voc (%/°C)":  p.get("CoefVoc_C"),
            "γ Pmax (%/°C)": p.get("beta_mp"),
            "NOCT (°C)":     p.get("NOCT"),
            "Costo USD":     p.get("costo_usd"),
        })

    _df_original = pd.DataFrame(_df_rows)

    _edited = st.data_editor(
        _df_original,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="editor_catalogo",
        column_config={
            "Modelo":        st.column_config.TextColumn("Modelo", width="medium"),
            "Marca":         st.column_config.TextColumn("Marca"),
            "Tecnología":    st.column_config.SelectboxColumn(
                "Tecnología",
                options=["", "Mono-Si", "Poly-Si", "HJT", "TOPCon", "CIS", "CdTe", "a-Si", "Thin Film", "Otro"],
            ),
            "Pmax (W)":      st.column_config.NumberColumn("Pmax (W)", format="%.1f", min_value=0),
            "Voc (V)":       st.column_config.NumberColumn("Voc (V)",  format="%.2f", min_value=0),
            "Isc (A)":       st.column_config.NumberColumn("Isc (A)",  format="%.3f", min_value=0),
            "Vmp (V)":       st.column_config.NumberColumn("Vmp (V)",  format="%.2f", min_value=0),
            "Imp (A)":       st.column_config.NumberColumn("Imp (A)",  format="%.3f", min_value=0),
            "Ns":            st.column_config.NumberColumn("Ns",       format="%d",   min_value=0, step=1),
            "β Voc (%/°C)":  st.column_config.NumberColumn("β Voc",   format="%.4f"),
            "γ Pmax (%/°C)": st.column_config.NumberColumn("γ Pmax",  format="%.4f"),
            "NOCT (°C)":     st.column_config.NumberColumn("NOCT",     format="%.1f", min_value=0),
            "Costo USD":     st.column_config.NumberColumn("Costo USD",format="%.2f", min_value=0),
        },
    )

    if st.button("💾 Guardar cambios editados", type="primary", key="btn_guardar_edicion"):
        errores = []
        guardados = 0
        for i, row_ed in _edited.iterrows():
            row_orig = _df_original.iloc[i]
            # Detectar cambios comparando celda a celda
            diff = {}
            for col in _df_original.columns:
                v_orig = row_orig[col]
                v_edit = row_ed[col]
                # Comparación tolerante a NaN
                try:
                    igual = (v_orig == v_edit) or (pd.isna(v_orig) and pd.isna(v_edit))
                except Exception:
                    igual = str(v_orig) == str(v_edit)
                if not igual:
                    diff[col] = v_edit

            if not diff:
                continue

            nombre_orig = str(row_orig["Modelo"]).strip()
            datos_patch = {
                "TipoPanel":         str(row_ed["Modelo"]).strip(),
                "Marca":             str(row_ed["Marca"]).strip(),
                "Tecnologia":        str(row_ed["Tecnología"]).strip(),
                "PmaxWp":            row_ed["Pmax (W)"],
                "Voc_STC":           row_ed["Voc (V)"],
                "Isc_STC":           row_ed["Isc (A)"],
                "Vmp_STC":           row_ed["Vmp (V)"],
                "Imp_STC":           row_ed["Imp (A)"],
                "Ns (Celdas Serie)": row_ed["Ns"],
                "CoefVoc_C":         row_ed["β Voc (%/°C)"],
                "CoefT_C":           row_ed["γ Pmax (%/°C)"],
                "NOCT_C":            row_ed["NOCT (°C)"],
                "CostoUSD":          row_ed["Costo USD"],
            }
            try:
                actualizar_panel_excel(nombre_orig, datos_patch)
                guardados += 1
            except Exception as e:
                errores.append(f"{nombre_orig}: {e}")

        if guardados:
            st.success(f"✅ {guardados} panel(es) actualizado(s).")
            st.rerun()
        elif not errores:
            st.info("No se detectaron cambios.")
        if errores:
            for err in errores:
                st.error(f"❌ {err}")

    st.divider()

    # ── Eliminar panel ────────────────────────────────────────────────────────
    with st.expander("🗑️ Eliminar un panel del catálogo"):
        st.warning(
            "⚠️ Esta acción es **permanente**. El panel se borra del Excel y no se puede recuperar "
            "salvo desde una copia de seguridad.",
            icon="⚠️",
        )
        panel_borrar = st.selectbox(
            "Selecciona el panel a eliminar",
            options=[""] + list(_cat_filtrado.keys()),
            key="sel_borrar",
        )
        confirmar = st.checkbox(
            f"Confirmo que quiero eliminar **{panel_borrar}** permanentemente",
            key="chk_confirmar",
            disabled=not panel_borrar,
        )
        if st.button(
            "🗑️ Eliminar panel",
            type="primary",
            disabled=not (panel_borrar and confirmar),
            key="btn_eliminar",
        ):
            try:
                ok = eliminar_panel_excel(panel_borrar)
                if ok:
                    st.success(f"✅ **{panel_borrar}** eliminado del catálogo.")
                    st.rerun()
                else:
                    st.error(f"No se encontró '{panel_borrar}' en el Excel.")
            except Exception as e:
                st.error(f"❌ Error al eliminar: {e}")
