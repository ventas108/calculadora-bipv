"""Página 14 — Agregar panel al catálogo desde ficha técnica PDF (#65)."""
import streamlit as st
import pandas as pd

from calculos.pdf_panel_extractor import extraer_parametros_panel, pdf_disponible
from datos.catalogo_paneles_excel import guardar_panel_excel, cargar_catalogo_paneles

st.set_page_config(page_title="Catálogo PDF — BIPV", page_icon="📋", layout="wide")
st.title("📋 Agregar Panel desde Ficha Técnica PDF")
st.caption(
    "Sube la ficha técnica (datasheet) de un panel FV en PDF. "
    "La app extrae automáticamente los parámetros eléctricos y te permite verificarlos "
    "antes de guardarlos en el catálogo Excel."
)

# ── Verificar disponibilidad de pdfplumber ────────────────────────────────────
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

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Ficha técnica del panel (PDF)",
    type=["pdf"],
    help="Datasheets de Canadian Solar, Trina, LONGi, JA Solar, Jinko, Hanwha, REC, etc.",
)

if not uploaded:
    st.info("⬆️ Sube un PDF para comenzar. La extracción tarda menos de 2 segundos.")
    st.stop()

# ── Extraer parámetros ────────────────────────────────────────────────────────
with st.spinner("Analizando PDF…"):
    pdf_bytes = uploaded.read()
    data = extraer_parametros_panel(pdf_bytes)

if "error" in data:
    st.error(data["error"])
    st.stop()

st.success("✅ PDF analizado. Verifica y corrige los valores antes de guardar.")

# ── Formulario de verificación ────────────────────────────────────────────────
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
    n_s   = f1.number_input("Celdas en serie (Ns)", value=int(data.get("N_s") or 0), min_value=0, step=1)
    dims  = f2.text_input("Dimensiones (LxAxE mm)", value=data.get("dimensiones") or "")
    transp = f3.number_input("Transparencia (%)", value=0.0, min_value=0.0, max_value=100.0, step=1.0,
                              help="Para BIPV semitransparente. 0 = opaco.")
    costo = f4.number_input("Costo (USD/ud)", value=0.0, min_value=0.0, step=1.0, format="%.2f")

    notas = st.text_area("Notas / observaciones", placeholder="Fuente de datos, fecha de ficha, observaciones…", height=68)

    _campos_ok = modelo.strip() and Pmax > 0
    submitted = st.form_submit_button(
        "💾 Guardar en catálogo",
        disabled=not _campos_ok,
        type="primary",
        help="Requiere al menos Nombre del modelo y Pmax." if not _campos_ok else "",
    )

if submitted:
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
        "Confianza":          "PDF-auto",
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

# ── Texto extraído (debug) ────────────────────────────────────────────────────
with st.expander("🔍 Ver texto extraído del PDF (para diagnóstico)"):
    raw = data.get("texto_crudo", "")
    if raw:
        st.text_area("Texto crudo (primeros 4000 caracteres)", raw, height=300)
    else:
        st.info("No se extrajo texto del PDF (puede ser un PDF escaneado/imagen).")
    st.caption(
        "Si los valores no se detectaron correctamente, es posible que el PDF sea "
        "una imagen escaneada sin texto seleccionable. En ese caso ingresa los valores manualmente."
    )

# ── Catálogo actual ───────────────────────────────────────────────────────────
st.divider()
with st.expander("📂 Ver catálogo completo actual"):
    _cat = cargar_catalogo_paneles()
    if _cat:
        _rows = []
        for nm, p in sorted(_cat.items()):
            _rows.append({
                "Modelo":     nm,
                "Marca":      p.get("marca", ""),
                "Tecnología": p.get("tecnologia", ""),
                "Pmax (W)":   p.get("Pmax_stc"),
                "Voc (V)":    p.get("Voc"),
                "Isc (A)":    p.get("Isc"),
                "Vmp (V)":    p.get("Vmp"),
                "Imp (A)":    p.get("Imp"),
                "Ns":         p.get("N_s"),
            })
        st.dataframe(pd.DataFrame(_rows), use_container_width=True, hide_index=True)
    else:
        st.info("El catálogo está vacío o no se pudo leer.")
