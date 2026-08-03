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
        score_ok = score_total = n_nones = 0
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
                if ex is None:           # campo esperado que quedó vacío
                    n_nones += 1
        fila["_nones"] = n_nones
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

# ── Alerta de extracción probablemente rota ──────────────────────────────────
# Si un caso deja > 3 campos esperados en None, casi seguro el extractor falló
# en silencio con ese formato (no es un campo suelto, es el formato completo)
_rotos = [r for r in resultados if r["_nones"] > 3]
if _rotos:
    st.error(
        "🚨 **Posible fallo de extracción** — estos casos tienen más de 3 campos "
        "esperados vacíos (None), señal de que el extractor no reconoce el formato:\n\n"
        + "\n".join(f"- **{r['_fab']} — {r['_model']}**: {r['_nones']} campos vacíos"
                    for r in _rotos)
    )

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

# Etiqueta única "fabricante — modelo": hay fabricantes con varios casos
# (SolaX, Growatt, SAJ...) y con solo el fabricante siempre se mostraba el 1º
_opciones = [f"{r['_fab']} — {r['_model']}" for r in resultados]
op_sel = st.selectbox(
    "Selecciona un caso para ver el desglose completo",
    _opciones,
    key="fab_detail",
)
_idx_sel = _opciones.index(op_sel)
r_sel = resultados[_idx_sel]
caso_sel = CASOS[_idx_sel]

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

    # ── Botón explícito: evita problemas con el rerun automático del uploader ──
    btn_extraer = st.button(
        "🔍 Extraer métricas del PDF",
        type="primary",
        disabled=(up is None),
        key="btn_extraer_pdf",
    )

    # Limpiar resultado previo si se sube un archivo nuevo
    if up is None:
        st.session_state.pop("pdf_extraccion_result", None)

    # Ejecutar extracción SOLO al presionar el botón
    if btn_extraer and up is not None:
        _placeholder = st.empty()
        _placeholder.info("⏳ Extrayendo texto y métricas del PDF…")
        try:
            _raw_bytes = up.read()
            res_real   = extraer_parametros_inversor(_raw_bytes)
        except Exception as _exc:
            import traceback
            res_real = {"error": f"Excepción inesperada: {_exc}\n{traceback.format_exc()}"}
        st.session_state["pdf_extraccion_result"] = res_real
        _placeholder.empty()

    # Mostrar resultado almacenado (persiste tras el rerun del botón)
    res_real = st.session_state.get("pdf_extraccion_result")

    if res_real is not None:
        if "error" in res_real:
            st.error(f"❌ {res_real['error']}")
        else:
            fab_real    = res_real.get("marca", "")
            modelo_real = res_real.get("modelo", "")
            n_pages     = res_real.get("n_pages_total", "?")
            n_chars     = res_real.get("n_chars_extraidos", 0)
            escaneado   = res_real.get("es_escaneado", False)
            uso_ocr     = res_real.get("uso_ocr", False)

            # ── Diagnóstico de calidad ─────────────────────────────────────────
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Páginas en el PDF",     n_pages)
            d2.metric("Caracteres extraídos",  f"{n_chars:,}")
            d3.metric("¿PDF escaneado?",        "Sí ⚠️" if escaneado else "No ✅")
            d4.metric("OCR usado",             "Sí" if uso_ocr else "No")

            if escaneado and not uso_ocr:
                st.error(
                    "🔴 **PDF escaneado sin OCR disponible** — el PDF contiene imágenes "
                    "en lugar de texto seleccionable. Instala `pdf2image` + `tesseract` "
                    "para el fallback OCR, o usa un PDF con texto seleccionable."
                )
            elif n_chars < 200:
                st.warning(
                    f"⚠️ **Texto muy corto ({n_chars} chars)** — PDF posiblemente escaneado, "
                    "protegido, o especificaciones en páginas > 8. Revisa el texto crudo abajo."
                )
            elif not fab_real:
                st.warning(
                    "⚠️ **Marca no detectada** — texto extraído pero fabricante no identificado. "
                    "Revisa el texto crudo para ver qué llegó."
                )
            else:
                st.success(
                    f"✅ **{fab_real} — {modelo_real or '(modelo no detectado)'}** · "
                    f"{n_pages} págs · {n_chars:,} chars"
                    + (" · OCR" if uso_ocr else "")
                )

            # ── Selector de modelo (ficha técnica multi-modelo) ───────────────
            # Contenedor SIEMPRE presente: estabiliza el árbol React entre reruns
            # (misma lección de la página Catálogo PDF — evita NotFoundError
            # insertBefore/removeChild cuando el bloque aparece/desaparece).
            _slot_multi = st.container()
            modelos_det = res_real.get("modelos_detectados", [])
            modelo_seleccionado = None
            if modelos_det:
                with _slot_multi:
                    st.info(
                        f"📋 **Ficha técnica multi-modelo** — se detectaron {len(modelos_det)} modelos "
                        f"en columnas separadas: `{'`, `'.join(modelos_det)}`  \n"
                        "Selecciona el modelo que deseas agregar al catálogo para ver sus valores específicos."
                    )
                    modelo_seleccionado = st.selectbox(
                        "Modelo a utilizar",
                        modelos_det,
                        key="sel_modelo_pdf",
                    )
                # Sobreescribir campos variables con los del modelo elegido
                vals_mod = res_real.get("valores_por_modelo", {}).get(modelo_seleccionado, {})
                res_real_view = {**res_real}        # copia shallow para no mutar session_state
                for campo, val in vals_mod.items():
                    if val is not None:
                        res_real_view[campo] = val
            else:
                res_real_view = res_real

            # ── Tabla de métricas ──────────────────────────────────────────────
            campos_extraidos = sum(
                1 for c in CAMPOS_CRITICOS if res_real_view.get(c) is not None
            )
            st.markdown(f"**Campos extraídos: {campos_extraidos} / {len(CAMPOS_CRITICOS)}**")

            # Buscar caso sintético del mismo fabricante Y modelo (si hay modelo seleccionado)
            caso_match = None
            if fab_real:
                for c in CASOS:
                    fab_ok   = fab_real.lower() in c["fabricante"].lower()
                    model_ok = (
                        not modelo_seleccionado
                        or modelo_seleccionado.lower() in c["modelo"].lower()
                        or c["modelo"].lower() in (modelo_seleccionado.lower() if modelo_seleccionado else "")
                    )
                    if fab_ok and model_ok:
                        caso_match = c
                        break
                # Fallback: sólo por fabricante
                if caso_match is None:
                    caso_match = next(
                        (c for c in CASOS if fab_real.lower() in c["fabricante"].lower()), None
                    )

            if caso_match:
                mod_ref = modelo_seleccionado or caso_match['modelo']
                st.markdown(f"**Comparación vs caso sintético — {caso_match['fabricante']} {mod_ref}:**")
                comp_rows = []
                for campo in CAMPOS_CRITICOS:
                    esp = caso_match["esperado"].get(campo)
                    ex  = res_real_view.get(campo)
                    emoji, detalle = _comparar(ex, esp)
                    comp_rows.append({
                        "Campo":           CAMPO_LABELS[campo],
                        "Estado":          emoji,
                        "PDF real":        str(ex) if ex is not None else "None",
                        "Sintético (esp)": str(esp) if esp is not None else "N/D",
                    })
                st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)
            else:
                label = f"No hay caso sintético para **{fab_real}**." if fab_real else "Marca no detectada."
                st.info(f"{label} Valores extraídos:")
                raw_rows = [
                    {"Campo": CAMPO_LABELS.get(c, c), "Valor": str(res_real_view.get(c))}
                    for c in CAMPOS_CRITICOS
                ]
                st.dataframe(pd.DataFrame(raw_rows), use_container_width=True, hide_index=True)

            # Texto crudo — auto-abierto si hay problemas
            _auto_open = (escaneado or n_chars < 500 or campos_extraidos < 4 or not fab_real)
            with st.expander("🔍 Texto crudo extraído del PDF", expanded=_auto_open):
                texto_crudo = res_real.get("texto_crudo", "")
                if texto_crudo.strip():
                    st.text(texto_crudo)
                else:
                    st.warning(
                        "Sin texto extraído — PDF posiblemente escaneado "
                        "(imágenes sin texto seleccionable)."
                    )

# ══════════════════════════════════════════════════════════════════════════════
# Forzar re-ejecución
# ══════════════════════════════════════════════════════════════════════════════

if st.button("🔄 Re-ejecutar todos los casos"):
    _run_all_cases.clear()
    st.rerun()
