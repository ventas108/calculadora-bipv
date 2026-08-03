"""
Página 15 — Agregar / Editar inversores al catálogo desde ficha técnica PDF.

Flujo:
  Pestaña 1 ➕ Agregar desde PDF:
    Upload PDF → extracción automática → formulario editable → guardar al Excel

  Pestaña 2 ✏️ Editar / Eliminar:
    Filtrar por marca / arquitectura / nombre → st.data_editor → guardar cambios
    Sección eliminar con confirmación obligatoria
"""

import streamlit as st
from calculos.pdf_inversor_extractor import (
    extraer_parametros_inversor,
    pdf_disponible,
    ocr_disponible,
)
from datos.catalogo_inversores_excel import (
    cargar_catalogo_inversores,
    guardar_inversor_excel,
    actualizar_inversor_excel,
    eliminar_inversor_excel,
)

st.set_page_config(page_title="Catálogo Inversores PDF", page_icon="🔌", layout="wide")
st.title("🔌 Catálogo de Inversores — Agregar / Editar desde PDF")

tab1, tab2 = st.tabs(["➕ Agregar desde PDF", "✏️ Editar / Eliminar"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Agregar desde PDF
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── Disponibilidad de dependencias ────────────────────────────────────────
    if not pdf_disponible():
        st.error(
            "❌ **pdfplumber no está instalado.** "
            "Contacta al administrador para ejecutar `pip install pdfplumber`."
        )
        st.stop()

    if ocr_disponible():
        st.info(
            "✅ OCR disponible (Tesseract) — las fichas escaneadas también serán procesadas.",
            icon="🔍",
        )
    else:
        st.warning(
            "⚠️ OCR **no disponible** — solo se procesarán PDFs con texto digital. "
            "Para fichas escaneadas instala `tesseract-ocr` y `pdf2image`.",
            icon="📷",
        )

    st.markdown("---")

    # ── Upload ────────────────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "📄 Ficha técnica del inversor (PDF)",
        type=["pdf"],
        help="Sube el datasheet del fabricante. Se reconocen: Growatt, Solis, Deye, "
             "MUST, SolaX, LuxPower, POWEST, Huawei, SMA, Fronius, GoodWe, Sofar, "
             "Sungrow, Victron, Solaredge, Delta, Chint, Kstar, Voltronic y compatibles.",
    )

    if not uploaded:
        st.info("⬆️ Sube un PDF para comenzar la extracción automática.")
        st.stop()

    pdf_bytes = uploaded.read()

    with st.spinner("🔍 Extrayendo parámetros del PDF…"):
        res = extraer_parametros_inversor(pdf_bytes)

    if "error" in res:
        st.error(f"❌ Error al procesar el PDF: {res['error']}")
        st.stop()

    # ── Banner estado ─────────────────────────────────────────────────────────
    if res.get("es_escaneado") and res.get("uso_ocr"):
        st.warning(
            "📷 **PDF escaneado detectado** — se aplicó OCR para extraer el texto. "
            "Verifica los valores antes de guardar.",
            icon="⚠️",
        )
    elif res.get("es_escaneado") and not res.get("uso_ocr"):
        st.error(
            "📷 PDF escaneado pero **OCR no disponible** — los campos estarán vacíos. "
            "Instala Tesseract o rellena el formulario manualmente.",
            icon="❌",
        )
    else:
        st.success("✅ PDF digital procesado correctamente.", icon="✅")

    # Contar campos extraídos automáticamente
    _campos_num = [
        "Vdc_max", "Vmppt_min", "Vmppt_max", "V_mppt_activo", "V_arranque",
        "n_trackers", "n_strings_tracker", "I_max_tracker", "Isc_max_tracker",
        "P_dc_max_W",
    ]
    _n_ok = sum(1 for c in _campos_num if res.get(c) is not None)
    st.caption(
        f"Marca detectada: **{res.get('marca','—')}** · "
        f"Modelo: **{res.get('modelo','—')}** · "
        f"Arquitectura: **{res.get('arquitectura','—')}** · "
        f"Campos numéricos extraídos: **{_n_ok}/{len(_campos_num)}**"
    )

    st.markdown("---")
    st.subheader("📝 Revisar y completar los datos")

    # ── Formulario editable ───────────────────────────────────────────────────
    with st.form("form_inversor_pdf"):

        col_l, col_r = st.columns(2)

        # ── Identificación ────────────────────────────────────────────────────
        with col_l:
            modelo_val = st.text_input(
                "Modelo *",
                value=res.get("modelo", ""),
                help="Nombre exacto del modelo (requerido).",
            )
            marca_val = st.text_input("Marca", value=res.get("marca", ""))

        with col_r:
            arch_opciones = [
                "Inversor de red monofásico",
                "Inversor de red trifásico",
                "Híbrido / Off-grid",
                "Cargador off-grid puro",
                "Otro",
            ]
            arch_default = res.get("arquitectura", "Inversor de red monofásico")
            arch_idx = arch_opciones.index(arch_default) if arch_default in arch_opciones else 0
            arch_val = st.selectbox("Arquitectura", arch_opciones, index=arch_idx)

            es_hibrido_val = st.checkbox(
                "¿Inversor Híbrido? (con gestión de batería)",
                value=bool(res.get("es_hibrido", False)),
            )

        st.markdown("##### ⚡ Parámetros DC / MPPT")
        c1, c2, c3 = st.columns(3)

        with c1:
            Vdc_max_val = st.number_input(
                "Tensión DC Máxima (V)",
                min_value=0.0, max_value=1500.0, step=1.0,
                value=float(res.get("Vdc_max") or 0.0),
                help="Límite físico absoluto de voltaje de entrada DC.",
            )
            Vmppt_min_val = st.number_input(
                "Rango MPPT — Mín (V)",
                min_value=0.0, max_value=1500.0, step=1.0,
                value=float(res.get("Vmppt_min") or 0.0),
            )
            Vmppt_max_val = st.number_input(
                "Rango MPPT — Máx (V)",
                min_value=0.0, max_value=1500.0, step=1.0,
                value=float(res.get("Vmppt_max") or 0.0),
            )

        with c2:
            V_mppt_activo_val = st.number_input(
                "Tensión Mínima MPPT Activo (V)",
                min_value=0.0, max_value=1500.0, step=1.0,
                value=float(res.get("V_mppt_activo") or 0.0),
                help="Voltaje mínimo con operación a carga completa (Full Load). "
                     "Deye lo llama 'Full Load DC Voltage Range'.",
            )
            V_arranque_val = st.number_input(
                "Tensión de Arranque (V)",
                min_value=0.0, max_value=1500.0, step=1.0,
                value=float(res.get("V_arranque") or 0.0),
                help="Voltaje mínimo para iniciar operación desde apagado (PV, no batería). "
                     "Puede ser N/D para cargadores off-grid puros.",
            )
            n_trackers_val = st.number_input(
                "N° Trackers MPPT",
                min_value=0, max_value=12, step=1,
                value=int(res.get("n_trackers") or 0),
            )

        with c3:
            n_strings_val = st.number_input(
                "N° Strings por Tracker",
                min_value=0, max_value=6, step=1,
                value=int(res.get("n_strings_tracker") or 0),
                help="Si hay trackers con corrientes desiguales, usa el más alto.",
            )
            I_max_val = st.number_input(
                "Corriente Máxima Tracker (A)",
                min_value=0.0, max_value=300.0, step=0.5,
                value=float(res.get("I_max_tracker") or 0.0),
            )
            Isc_max_val = st.number_input(
                "Corriente Cortocircuito Máx Tracker (A)",
                min_value=0.0, max_value=300.0, step=0.5,
                value=float(res.get("Isc_max_tracker") or 0.0),
                help="Deja en 0 si el fabricante no lo reporta (MUST, POWEST).",
            )

        P_dc_val = st.number_input(
            "Potencia FV Máxima Recomendada (W)",
            min_value=0.0, step=100.0,
            value=float(res.get("P_dc_max_W") or 0.0),
            help="Si la ficha reporta en kWp, el extractor ya convirtió ×1000.",
        )

        # ── Batería (solo si híbrido) ─────────────────────────────────────────
        if es_hibrido_val:
            st.markdown("##### 🔋 Parámetros de Batería")
            cb1, cb2 = st.columns(2)
            with cb1:
                bat_min_val = st.number_input(
                    "Voltaje Batería Mín (V)", min_value=0.0, max_value=1200.0, step=1.0,
                    value=float(res.get("bat_voltaje_min") or 0.0),
                )
            with cb2:
                bat_max_val = st.number_input(
                    "Voltaje Batería Máx (V)", min_value=0.0, max_value=1200.0, step=1.0,
                    value=float(res.get("bat_voltaje_max") or 0.0),
                )
        else:
            bat_min_val = bat_max_val = 0.0

        # ── Costo y notas ─────────────────────────────────────────────────────
        st.markdown("##### 💲 Precio y notas")
        cn1, cn2 = st.columns([1, 2])
        with cn1:
            costo_val = st.number_input(
                "Costo inversor (USD)", min_value=0.0, step=50.0, value=0.0,
            )
        with cn2:
            notas_val = st.text_area(
                "Notas (opcional)",
                placeholder="Ej: corrientes desiguales por tracker, ver nota de diseño.",
                height=80,
            )

        submitted = st.form_submit_button("💾 Guardar en catálogo", type="primary")

    # ── Procesamiento del formulario ──────────────────────────────────────────
    if submitted:
        if not modelo_val.strip():
            st.error("❌ El campo **Modelo** es obligatorio.")
        elif Vdc_max_val <= 0:
            st.error("❌ La **Tensión DC Máxima** debe ser mayor que 0.")
        else:
            _confianza = "OCR-auto" if res.get("uso_ocr") else ("PDF-auto" if _n_ok > 0 else "Manual")
            _datos_completos = "Si" if all([
                Vdc_max_val > 0, Vmppt_min_val > 0, Vmppt_max_val > 0,
                n_trackers_val > 0, I_max_val > 0,
            ]) else "No"

            _row = {
                "Modelo":                             modelo_val.strip(),
                "Datos completos (Si/No)":            _datos_completos,
                "Costo Inversor":                     costo_val if costo_val > 0 else None,
                "Tension DC Maxima (V)":              Vdc_max_val or None,
                "Tension Arranque (V)":               V_arranque_val or None,
                "Rango MPPT Min (V)":                 Vmppt_min_val or None,
                "Rango MPPT Max (V)":                 Vmppt_max_val or None,
                "Tension Minima MPPT Activo (V)":     V_mppt_activo_val or None,
                "N Trackers":                         n_trackers_val or None,
                "N Strings/Tracker":                  n_strings_val or None,
                "Corriente Maxima Tracker (A)":       I_max_val or None,
                "Corriente Cortocircuito Max Tracker (A)": Isc_max_val or None,
                "Potencia FV Max Recomendada (W)":    P_dc_val or None,
                "Inversor Híbrido (Si/No)":           "Si" if es_hibrido_val else "No",
                "Voltaje Batería Min (V)":            bat_min_val or None,
                "Voltaje Batería Max (V)":            bat_max_val or None,
                "Notas":                              notas_val.strip() or None,
                "Confianza":                          _confianza,
                "Marca":                              marca_val.strip() or None,
                "Arquitectura":                       arch_val,
            }

            try:
                nombre_guardado = guardar_inversor_excel(_row)
                st.success(f"✅ Inversor **{nombre_guardado}** guardado correctamente en el catálogo.")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")

    # ── Debug — texto extraído ────────────────────────────────────────────────
    with st.expander("🔍 Ver texto extraído del PDF (debug)"):
        st.text(res.get("texto_crudo", "(vacío)"))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Editar / Eliminar
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    import pandas as pd

    _cat = cargar_catalogo_inversores()

    if not _cat:
        st.info("El catálogo de inversores está vacío o no se pudo cargar.")
        st.stop()

    # ── Filtros ───────────────────────────────────────────────────────────────
    _marcas = sorted({str(v.get("marca", "") or "").strip() for v in _cat.values() if v.get("marca")})
    _marcas_op = ["(todas)"] + _marcas
    _f_marca = st.selectbox("Filtrar por marca", _marcas_op, key="edit_inv_marca")

    _busqueda = st.text_input("Buscar por nombre / modelo", key="edit_inv_busqueda")

    # Aplicar filtros
    _items = list(_cat.values())
    if _f_marca != "(todas)":
        _items = [x for x in _items if str(x.get("marca", "") or "").strip() == _f_marca]
    if _busqueda.strip():
        _q = _busqueda.strip().lower()
        _items = [x for x in _items if _q in x["nombre"].lower()]

    if not _items:
        st.warning("No hay inversores que coincidan con el filtro.")
    else:
        # ── Tabla editable ────────────────────────────────────────────────────
        _COLS_EDIT = {
            "nombre":            "Modelo",
            "Vdc_max":           "Vdc máx (V)",
            "Vmppt_min":         "MPPT mín (V)",
            "Vmppt_max":         "MPPT máx (V)",
            "V_mppt_activo":     "MPPT activo mín (V)",
            "V_arranque":        "V arranque (V)",
            "n_trackers":        "N Trackers",
            "n_strings_tracker": "Strings/Tracker",
            "I_max_tracker":     "I máx tracker (A)",
            "Isc_max_tracker":   "Isc máx tracker (A)",
            "P_dc_max_W":        "P FV máx (W)",
            "costo_usd":         "Costo (USD)",
        }

        _df_orig = pd.DataFrame([
            {col: x.get(k) for k, col in _COLS_EDIT.items()}
            for x in _items
        ])

        _col_config = {
            "Modelo": st.column_config.TextColumn("Modelo", disabled=False),
            **{
                col: st.column_config.NumberColumn(col, format="%.1f")
                for col in list(_COLS_EDIT.values())[1:]
            },
        }

        st.markdown("**Edita directamente en la tabla y presiona _Guardar cambios_:**")
        _df_edit = st.data_editor(
            _df_orig,
            column_config=_col_config,
            use_container_width=True,
            num_rows="fixed",
            key="edit_inv_table",
        )

        if st.button("💾 Guardar cambios", key="btn_guardar_inv"):
            _n_ok_edit = 0
            _errores = []
            for i, (orig_row, edit_row) in enumerate(
                zip(_df_orig.itertuples(index=False), _df_edit.itertuples(index=False))
            ):
                # Detectar cambios
                _patch = {}
                for col in _COLS_EDIT.values():
                    v_orig = getattr(orig_row, col.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "").replace("á","a").replace("í","i").replace("é","e").replace("ó","o"))
                    v_edit = getattr(edit_row, col.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "").replace("á","a").replace("í","i").replace("é","e").replace("ó","o"))
                    if v_orig != v_edit:
                        # Mapear nombre de columna editable → nombre Excel
                        _excel_col = {v: k for k, v in _COLS_EDIT.items()}.get(col, col)
                        _excel_map = {
                            "nombre":            "Modelo",
                            "Vdc_max":           "Tension DC Maxima (V)",
                            "Vmppt_min":         "Rango MPPT Min (V)",
                            "Vmppt_max":         "Rango MPPT Max (V)",
                            "V_mppt_activo":     "Tension Minima MPPT Activo (V)",
                            "V_arranque":        "Tension Arranque (V)",
                            "n_trackers":        "N Trackers",
                            "n_strings_tracker": "N Strings/Tracker",
                            "I_max_tracker":     "Corriente Maxima Tracker (A)",
                            "Isc_max_tracker":   "Corriente Cortocircuito Max Tracker (A)",
                            "P_dc_max_W":        "Potencia FV Max Recomendada (W)",
                            "costo_usd":         "Costo Inversor",
                        }
                        excel_key = _excel_map.get(_excel_col, col)
                        _patch[excel_key] = v_edit

                if _patch:
                    nombre_orig = getattr(orig_row, "Modelo")
                    try:
                        actualizar_inversor_excel(nombre_orig, _patch)
                        _n_ok_edit += 1
                    except Exception as e:
                        _errores.append(f"{nombre_orig}: {e}")

            if _n_ok_edit:
                st.success(f"✅ {_n_ok_edit} inversor(es) actualizado(s).")
                st.rerun()
            elif _errores:
                for err in _errores:
                    st.error(err)
            else:
                st.info("Sin cambios detectados.")

        # ── Eliminar ──────────────────────────────────────────────────────────
        with st.expander("🗑️ Eliminar un inversor del catálogo"):
            _nombres_filtrados = [x["nombre"] for x in _items]
            _inv_borrar = st.selectbox(
                "Selecciona el inversor a eliminar",
                _nombres_filtrados,
                key="sel_inv_borrar",
            )
            _confirmar = st.checkbox(
                f'Confirmo que quiero eliminar permanentemente **"{_inv_borrar}"** del catálogo.',
                key="chk_inv_borrar",
            )
            _btn_borrar = st.button(
                "🗑️ Eliminar definitivamente",
                disabled=not (_inv_borrar and _confirmar),
                key="btn_inv_borrar",
                type="primary",
            )
            if _btn_borrar:
                try:
                    ok = eliminar_inversor_excel(_inv_borrar)
                    if ok:
                        st.success(f"✅ Inversor **{_inv_borrar}** eliminado del catálogo.")
                        st.rerun()
                    else:
                        st.warning("No se encontró el inversor en el Excel.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
