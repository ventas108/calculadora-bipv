"""
Página 16 — Harness de cobertura del extractor de inversores.

Muestra una tabla fabricante × campo con semáforos:
  🟢 OK     — valor extraído coincide con esperado (±5 %)
  🟡 CERCA  — error entre 5 % y 20 %
  🔴 FALLA  — valor muy diferente o None cuando se esperaba un número
  🔵 N/D    — campo legítimamente ausente (esperado = None)

Permite subir un PDF real para compararlo contra el patrón sintético
del mismo fabricante, o para añadirlo como nuevo caso de prueba.
"""

import streamlit as st
import pandas as pd
import sys, os

# Asegurar que el módulo scripts/ sea importable
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

from calculos.extractor_inversor_core import extraer_desde_texto
from scripts.casos_test_inversores import CASOS, CAMPOS_CRITICOS, CAMPO_LABELS

st.set_page_config(page_title="Test Extractor Inversores", page_icon="🧪", layout="wide")
st.title("🧪 Harness — Cobertura del Extractor de Inversores")
st.caption(
    "Valida los patrones regex del extractor contra casos sintéticos reales "
    "de cada fabricante. Usa esta página para detectar regresiones antes de "
    "subir fichas técnicas reales a producción."
)

# ══════════════════════════════════════════════════════════════════════════════
# Lógica de comparación
# ══════════════════════════════════════════════════════════════════════════════

def _comparar(extraido, esperado, tol=0.05) -> tuple[str, str]:
    """
    Retorna (emoji, detalle) comparando valor extraído vs esperado.
    tol = tolerancia relativa para valores numéricos.
    """
    if esperado is None:
        if extraido is None:
            return "🔵", "N/D"
        else:
            return "🔵", f"N/D (extraído: {extraido})"

    if extraido is None:
        return "🔴", f"None (esperado: {esperado})"

    try:
        e = float(esperado)
        x = float(extraido)
        if e == 0:
            return ("🟢", f"{x}") if x == 0 else ("🔴", f"{x} ≠ 0")
        err = abs(x - e) / abs(e)
        if err <= tol:
            return "🟢", f"{x}"
        elif err <= 0.20:
            return "🟡", f"{x} (esp: {e}, err: {err*100:.0f}%)"
        else:
            return "🔴", f"{x} (esp: {e}, err: {err*100:.0f}%)"
    except (TypeError, ValueError):
        return ("🟢", str(extraido)) if str(extraido) == str(esperado) else ("🔴", f"{extraido} ≠ {esperado}")


# ══════════════════════════════════════════════════════════════════════════════
# Ejecutar todos los casos
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def _run_all_cases():
    resultados = []
    for caso in CASOS:
        ext = extraer_desde_texto(caso["texto"])
        fila = {
            "_fab":   caso["fabricante"],
            "_model": caso["modelo"],
            "_arch":  caso["arquitectura"],
        }
        score_ok = score_total = 0
        for campo in CAMPOS_CRITICOS:
            esp = caso["esperado"].get(campo)  # None si no está en esperado → N/D
            ex  = ext.get(campo)
            emoji, detalle = _comparar(ex, esp)
            fila[campo] = emoji
            fila[f"{campo}_detalle"] = detalle
            if esp is not None:          # solo cuenta campos con valor esperado
                score_total += 1
                if emoji == "🟢":
                    score_ok += 1
        fila["_score"] = f"{score_ok}/{score_total}"
        fila["_pct"]   = score_ok / score_total * 100 if score_total else 0
        resultados.append(fila)
    return resultados

with st.spinner("Ejecutando casos de prueba…"):
    resultados = _run_all_cases()

# ══════════════════════════════════════════════════════════════════════════════
# Métricas globales
# ══════════════════════════════════════════════════════════════════════════════

total_ok    = sum(1 for r in resultados for c in CAMPOS_CRITICOS
                  if r[c] == "🟢" and r[f"{c}_detalle"] != "N/D")
total_fail  = sum(1 for r in resultados for c in CAMPOS_CRITICOS
                  if r[c] == "🔴")
total_warn  = sum(1 for r in resultados for c in CAMPOS_CRITICOS
                  if r[c] == "🟡")
avg_cov     = sum(r["_pct"] for r in resultados) / len(resultados) if resultados else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Fabricantes probados", len(resultados))
m2.metric("Campos OK 🟢",        total_ok,   delta=None)
m3.metric("Campos FALLA 🔴",     total_fail, delta=None, delta_color="inverse")
m4.metric("Cobertura promedio",  f"{avg_cov:.0f}%")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# Tabla de cobertura fabricante × campo
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("📊 Tabla de cobertura")

_df_rows = []
for r in resultados:
    row = {
        "Fabricante":   r["_fab"],
        "Modelo":       r["_model"],
        "Score":        r["_score"],
    }
    for campo in CAMPOS_CRITICOS:
        row[CAMPO_LABELS[campo]] = r[campo]
    _df_rows.append(row)

df_cob = pd.DataFrame(_df_rows)
st.dataframe(df_cob, use_container_width=True, hide_index=True, height=430)

# Leyenda
st.caption("🟢 OK (±5%)  ·  🟡 Cerca (5–20%)  ·  🔴 Falla o None inesperado  ·  🔵 N/D legítimo")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# Detalle por fabricante
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("🔍 Detalle por fabricante")

fab_sel = st.selectbox(
    "Selecciona un fabricante para ver el desglose completo",
    [r["_fab"] for r in resultados],
    key="fab_detail",
)

r_sel = next(r for r in resultados if r["_fab"] == fab_sel)
caso_sel = next(c for c in CASOS if c["fabricante"] == fab_sel)

col_det, col_txt = st.columns([1, 1])

with col_det:
    st.markdown(f"**{r_sel['_fab']} — {r_sel['_model']}**")
    st.caption(f"Arquitectura: {r_sel['_arch']}  ·  Score: {r_sel['_score']}")

    det_rows = []
    for campo in CAMPOS_CRITICOS:
        esp = caso_sel["esperado"].get(campo)
        det_rows.append({
            "Campo":    CAMPO_LABELS[campo],
            "Estado":   r_sel[campo],
            "Extraído": r_sel[f"{campo}_detalle"],
            "Esperado": str(esp) if esp is not None else "N/D",
        })
    st.dataframe(pd.DataFrame(det_rows), use_container_width=True, hide_index=True)

with col_txt:
    st.markdown("**Texto sintético del caso:**")
    st.code(caso_sel["texto"], language="text")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# Probar con PDF real
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("📄 Probar con PDF real")
st.caption(
    "Sube un PDF real para ver qué extrae el motor. "
    "Si el fabricante ya tiene caso sintético, se muestra la comparación directa."
)

try:
    from calculos.pdf_inversor_extractor import extraer_parametros_inversor, pdf_disponible
    _pdf_ok = pdf_disponible()
except ImportError:
    _pdf_ok = False

if not _pdf_ok:
    st.warning("pdfplumber no disponible — solo se pueden probar los casos sintéticos.")
else:
    up = st.file_uploader("Ficha técnica PDF", type=["pdf"], key="pdf_test_up")
    if up:
        with st.spinner("Extrayendo texto y métricas del PDF…"):
            try:
                res_real = extraer_parametros_inversor(up.read())
            except Exception as _exc:
                res_real = {"error": f"Excepción inesperada: {_exc}"}

        if "error" in res_real:
            st.error(f"❌ {res_real['error']}")
        else:
            fab_real   = res_real.get("marca", "")
            modelo_real = res_real.get("modelo", "")
            n_pages    = res_real.get("n_pages_total", "?")
            n_chars    = res_real.get("n_chars_extraidos", 0)
            escaneado  = res_real.get("es_escaneado", False)
            uso_ocr    = res_real.get("uso_ocr", False)

            # ── Diagnóstico de calidad de extracción ──────────────────────────
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Páginas en el PDF",  n_pages)
            d2.metric("Caracteres extraídos", f"{n_chars:,}")
            d3.metric("¿PDF escaneado?",    "Sí ⚠️" if escaneado else "No ✅")
            d4.metric("OCR usado",          "Sí" if uso_ocr else "No")

            # Alertas de calidad
            if escaneado and not uso_ocr:
                st.error(
                    "🔴 **PDF escaneado sin OCR disponible** — pdfplumber no pudo extraer texto "
                    "porque el PDF contiene imágenes en lugar de texto seleccionable. "
                    "Instala `pdf2image` + `tesseract` para activar el fallback OCR, "
                    "o usa un PDF con texto seleccionable (no escaneado)."
                )
            elif n_chars < 200:
                st.warning(
                    f"⚠️ **Texto muy corto extraído ({n_chars} chars)** — el PDF puede ser "
                    "escaneado, estar protegido, o tener las especificaciones en páginas > 8. "
                    "Revisa el texto crudo abajo para diagnosticar."
                )
            elif not fab_real:
                st.warning(
                    "⚠️ **Marca no detectada** — el extractor leyó texto pero no identificó "
                    "el fabricante. Puede ser un fabricante no listado o un formato inusual. "
                    "Revisa el texto crudo para ver qué se extrajo."
                )
            else:
                st.success(
                    f"✅ **{fab_real} — {modelo_real or '(modelo no detectado)'}** · "
                    f"{n_pages} páginas · {n_chars:,} chars extraídos"
                    + (" · OCR" if uso_ocr else "")
                )

            # ── Tabla de métricas extraídas ───────────────────────────────────
            # Contar cuántos campos no son None
            campos_extraidos = sum(
                1 for c in CAMPOS_CRITICOS
                if res_real.get(c) is not None
            )
            st.markdown(
                f"**Campos extraídos: {campos_extraidos} / {len(CAMPOS_CRITICOS)}**"
            )

            # ¿Existe caso sintético para este fabricante?
            caso_match = next(
                (c for c in CASOS
                 if fab_real and fab_real.lower() in c["fabricante"].lower()),
                None,
            ) if fab_real else None

            if caso_match:
                st.markdown(f"**Comparación vs caso sintético de {caso_match['fabricante']}:**")
                comp_rows = []
                for campo in CAMPOS_CRITICOS:
                    esp = caso_match["esperado"].get(campo)
                    ex  = res_real.get(campo)
                    emoji, detalle = _comparar(ex, esp)
                    comp_rows.append({
                        "Campo":              CAMPO_LABELS[campo],
                        "Estado":             emoji,
                        "PDF real":           str(ex) if ex is not None else "None",
                        "Sintético (esp)":    str(esp) if esp is not None else "N/D",
                    })
                st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)
            else:
                st.info(
                    f"{'No hay caso sintético para **' + fab_real + '**.' if fab_real else 'Marca no detectada.'} "
                    "Valores extraídos:"
                )
                raw_rows = [
                    {"Campo": CAMPO_LABELS.get(c, c), "Valor": str(res_real.get(c))}
                    for c in CAMPOS_CRITICOS
                ]
                st.dataframe(pd.DataFrame(raw_rows), use_container_width=True, hide_index=True)

            # Auto-abrir texto crudo cuando hay problemas de calidad
            _auto_open = (escaneado or n_chars < 500 or campos_extraidos < 4 or not fab_real)
            with st.expander("🔍 Texto crudo extraído del PDF", expanded=_auto_open):
                texto_crudo = res_real.get("texto_crudo", "")
                if texto_crudo.strip():
                    st.text(texto_crudo)
                else:
                    st.warning(
                        "Sin texto extraído — el PDF es probable que sea escaneado "
                        "(imágenes sin texto seleccionable)."
                    )

# ══════════════════════════════════════════════════════════════════════════════
# Forzar re-ejecución
# ══════════════════════════════════════════════════════════════════════════════

if st.button("🔄 Re-ejecutar todos los casos"):
    _run_all_cases.clear()
    st.rerun()
