"""
Página 10 — Reporte Técnico PDF / HTML
Genera un reporte descargable con todos los resultados del proyecto.
Incluye notas explicativas en cada sección para comprensión del usuario.
"""
import streamlit as st
import datetime

st.set_page_config(page_title="Reporte PDF — BIPV", page_icon="📄", layout="wide")

from calculos.auth import requerir_login
requerir_login()

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()   # #63 — proyecto activo visible en cada página
st.title("📄 Reporte Técnico del Proyecto")
st.caption(
    "Genera un informe completo descargable con resultados, parámetros y notas explicativas. "
    "Incluye todas las secciones completadas hasta el momento."
)

# ── Estado de completitud ──────────────────────────────────────────────────────
proyecto_ok    = bool(st.session_state.get("ciudad"))
recurso_ok     = st.session_state.get("recurso_solar_ok", False)
motor_optico   = st.session_state.get("motor_optico_ok", False)
dimensionam_ok = bool(st.session_state.get("N_serie"))
produccion_ok  = st.session_state.get("produccion_ok", False)
financiero_ok  = st.session_state.get("financiero_ok", False)
co2_ok         = st.session_state.get("impacto_co2_ok", False)

st.markdown("### Estado del proyecto")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("🏠 Proyecto",       "✅" if proyecto_ok  else "⬜")
c2.metric("☀️ Recurso Solar",  "✅" if recurso_ok   else "⬜")
c3.metric("🔆 Motor Óptico",   "✅" if motor_optico else "⬜")
c4.metric("📊 Producción",     "✅" if produccion_ok else "⬜")
c5.metric("💰 Financiero",     "✅" if financiero_ok else "⬜")
c6.metric("🌿 Huella CO₂",     "✅" if co2_ok       else "⬜")

if not recurso_ok:
    st.warning("⚠️ Ejecuta al menos ☀️ Recurso Solar para generar un reporte útil.")

st.markdown("---")

# ── Opciones del reporte ───────────────────────────────────────────────────────
st.subheader("⚙️ Opciones del reporte")
col_op1, col_op2 = st.columns(2)
with col_op1:
    nombre_empresa = st.text_input(
        "Nombre de la empresa",
        value=st.session_state.get("nombre_empresa", "Innovación Química"),
        key="rep_empresa",
    )
    nombre_proyecto = st.text_input(
        "Nombre del proyecto",
        value=st.session_state.get("nombre_proyecto", "Proyecto BIPV"),
        key="rep_proyecto",
    )
    # ── #5 — Logo y datos de contacto de la empresa ──────────────────────────
    contacto_empresa = st.text_input(
        "Datos de contacto (opcional)",
        value=st.session_state.get("empresa_contacto", ""),
        key="rep_contacto",
        placeholder="Ej: contacto@miempresa.com · +57 300 000 0000 · NIT 900.000.000",
        help="Aparece bajo el nombre de la empresa en el encabezado del reporte.",
    )
    st.session_state["empresa_contacto"] = contacto_empresa
    _logo_up = st.file_uploader(
        "Logo de la empresa (PNG/JPG, opcional)", type=["png", "jpg", "jpeg"],
        key="rep_logo_up",
        help="Se muestra en el encabezado del reporte en lugar del ícono ☀️. "
             "Recomendado: fondo transparente, máx. ~1 MB.",
    )
    if _logo_up is not None:
        _logo_bytes = _logo_up.getvalue()
        if len(_logo_bytes) > 2_000_000:
            st.warning("⚠️ El logo pesa más de 2 MB — usa una versión más liviana "
                       "para que el PDF no quede gigante.")
        else:
            import base64 as _b64
            _mime = "image/png" if _logo_up.name.lower().endswith(".png") else "image/jpeg"
            st.session_state["empresa_logo_b64"] = (
                f"data:{_mime};base64,{_b64.b64encode(_logo_bytes).decode()}"
            )
            st.caption(f"✅ Logo cargado: {_logo_up.name}")
    if st.session_state.get("empresa_logo_b64"):
        if st.button("🗑️ Quitar logo", key="rep_logo_clear"):
            st.session_state.pop("empresa_logo_b64", None)
            st.rerun()
with col_op2:
    balance_ok_ui   = st.session_state.get("balance_ok", False)
    incluir_motor   = st.checkbox("Incluir sección Motor Óptico",    value=motor_optico,   key="rep_inc_motor")
    incluir_dim     = st.checkbox("Incluir sección Dimensionamiento", value=dimensionam_ok, key="rep_inc_dim")
    incluir_prod    = st.checkbox("Incluir sección Producción",      value=produccion_ok,  key="rep_inc_prod")
    _bypass_ok_rep  = st.session_state.get("bypass_ok", False)
    incluir_bypass  = st.checkbox("Incluir pérdidas bypass diodes",  value=_bypass_ok_rep, key="rep_inc_bypass")
    incluir_fin     = st.checkbox("Incluir sección Financiero",      value=financiero_ok,  key="rep_inc_fin")
    st.checkbox("Incluir Balance Energético + Clasificación A+/A/B/C/D",
                value=balance_ok_ui, key="rep_inc_balance")
    st.checkbox("🌿 Incluir Huella de Carbono Evitada",
                value=co2_ok, key="rep_inc_co2",
                help="Incluye emisiones CO₂ evitadas, equivalencias IDEAM (árboles, hogares), "
                     "valor en bonos de carbono y contribución al NDC Colombia 2030. "
                     "Ejecuta 🌿 Huella CO₂ primero para activar.")
    _multisup_ui = bool(st.session_state.get("multisup_activo", False))
    st.checkbox("🏗️ Incluir desglose Multi-Superficie",
                value=_multisup_ui, key="rep_inc_multisup",
                help="Tabla de producción y bypass por superficie. "
                     "Activa en 🗺️ Vista 3D › ⚙️ Superficies BIPV primero.")
    _ppto_ui = float(st.session_state.get("presupuesto_capex_usd", 0)) > 0
    st.checkbox("💼 Incluir Resumen de Costos del Presupuesto",
                value=_ppto_ui, key="rep_inc_presupuesto",
                help="CAPEX, OPEX y desglose del Presupuesto. "
                     "Completa 💼 Presupuesto primero.")
    _er_activa_ui = bool(st.session_state.get("est_rapida_aplicada", False))
    st.checkbox(
        "🧮 Incluir Estimación Rápida — Fundamentación del Presupuesto",
        value=_er_activa_ui,
        key="rep_inc_est_rapida",
        help=(
            "Desglose CAPEX/OPEX paramétrico con benchmarks colombianos, "
            "comparativo de 3 escenarios y nota metodológica persuasiva-honesta. "
            "Aplica la Estimación Rápida en 💼 Presupuesto primero."
        ),
    )

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN GENERADORA DE HTML
# ══════════════════════════════════════════════════════════════════════════════

def _fmt(val, decimals=1, suffix="", fallback="—"):
    try:
        return f"{float(val):,.{decimals}f}{suffix}"
    except Exception:
        return fallback


def _waterfall_cascada_svg(bruta, p_iam, p_soil, p_term, efectiva,
                            color_verde="#1e8449", color_prim="#1a5276"):
    """
    Genera un gráfico SVG de cascada óptico-térmica (waterfall).
    No requiere librerías externas — solo string formatting.
    """
    W, H = 680, 300
    ml, mr, mt, mb = 62, 14, 46, 54
    chart_w = W - ml - mr
    chart_h = H - mt - mb

    y_max = bruta * 1.14

    def ypx(v):
        return mt + chart_h * (1.0 - max(float(v), 0) / y_max)

    n_bars = 5
    spacing = chart_w / n_bars
    bw = spacing * 0.52

    def cxi(i):
        return ml + spacing * i + spacing / 2

    level_after_iam  = bruta - p_iam
    level_after_soil = level_after_iam - p_soil

    # (bottom, height, color, [label lines], value_str)
    bars = [
        (0,               bruta,   color_prim,   ["POA bruta"],          f"{bruta:,.0f}"),
        (level_after_iam, p_iam,   "#e74c3c",    ["① IAM", "(dir+dif)"], f"−{p_iam:,.0f}"),
        (level_after_soil, p_soil, "#e74c3c",    ["② Soiling", "(suci.)"], f"−{p_soil:,.0f}"),
        (efectiva,        p_term,  "#c0392b",    ["③ Térmico", "(BIPV)"],  f"−{p_term:,.1f}"),
        (0,               efectiva, color_verde, ["POA efectiva", "→ Prod."], f"{efectiva:,.0f}"),
    ]
    # Connector landing levels (end of each bar, going left → right)
    conn_levels = [bruta, level_after_iam, level_after_soil, efectiva]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" style="font-family:Arial,sans-serif;">',
        f'<rect width="{W}" height="{H}" fill="white" rx="6"/>',
        f'<text x="{W//2}" y="24" text-anchor="middle" font-size="13" '
        f'font-weight="bold" fill="{color_prim}">'
        f'Cascada óptico-térmica BIPV (kWh/m²/año)</text>',
    ]

    # Grid lines + Y-axis labels
    for gi in range(6):
        gv = y_max / 5 * gi
        gy = ypx(gv)
        parts.append(
            f'<line x1="{ml}" y1="{gy:.0f}" x2="{W - mr}" y2="{gy:.0f}" '
            f'stroke="#ebebeb" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{ml - 4}" y="{gy + 4:.0f}" text-anchor="end" '
            f'font-size="9" fill="#888">{gv:,.0f}</text>'
        )

    # Axis lines
    parts.append(
        f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt + chart_h}" stroke="#ccc" stroke-width="1"/>'
    )
    parts.append(
        f'<line x1="{ml}" y1="{mt + chart_h}" x2="{W - mr}" y2="{mt + chart_h}" '
        f'stroke="#ccc" stroke-width="1"/>'
    )

    # Bars
    for i, (bot, ht, color, label_lines, vstr) in enumerate(bars):
        x1    = cxi(i) - bw / 2
        top_y = ypx(bot + ht)
        bot_y = ypx(bot)
        bar_h = bot_y - top_y

        # Drop shadow
        parts.append(
            f'<rect x="{x1 + 2:.0f}" y="{top_y + 2:.0f}" width="{bw:.0f}" '
            f'height="{bar_h:.0f}" fill="rgba(0,0,0,0.07)" rx="3"/>'
        )
        # Bar body
        parts.append(
            f'<rect x="{x1:.0f}" y="{top_y:.0f}" width="{bw:.0f}" '
            f'height="{bar_h:.0f}" fill="{color}" rx="3"/>'
        )

        # Value label (above bar; fall inside if too close to top)
        lbl_y = top_y - 7
        if lbl_y < mt + 12:
            lbl_y = top_y + 14
        parts.append(
            f'<text x="{cxi(i):.0f}" y="{lbl_y:.0f}" text-anchor="middle" '
            f'font-size="10" font-weight="bold" fill="{color}">{vstr}</text>'
        )

        # X-axis labels (multi-line)
        for li, line in enumerate(label_lines):
            ly = mt + chart_h + 16 + li * 13
            parts.append(
                f'<text x="{cxi(i):.0f}" y="{ly:.0f}" text-anchor="middle" '
                f'font-size="10" fill="#333">{line}</text>'
            )

    # Dashed connectors between bars
    for i, lv in enumerate(conn_levels):
        x_from = cxi(i) + bw / 2
        x_to   = cxi(i + 1) - bw / 2
        ly = ypx(lv)
        parts.append(
            f'<line x1="{x_from:.0f}" y1="{ly:.0f}" x2="{x_to:.0f}" y2="{ly:.0f}" '
            f'stroke="#aaa" stroke-width="1" stroke-dasharray="5,3"/>'
        )

    parts.append('</svg>')
    return ''.join(parts)


def _bloque_grafica(svg: str, pie: str) -> str:
    """Envuelve una gráfica SVG + pie en un bloque no divisible al imprimir."""
    return (
        '<div style="margin:14px 0 4px 0;break-inside:avoid;page-break-inside:avoid;">'
        f'{svg}'
        f'<div style="color:#888;font-size:0.85em;">{pie}</div>'
        '</div>'
    )


def _esc_html(s) -> str:
    """Escapa texto libre del usuario antes de interpolarlo en el HTML del reporte."""
    import html as _html_mod
    return _html_mod.escape(str(s or ""))


def _barras_mensuales_svg(vals, titulo="Producción mensual E_ac (kWh)",
                          color="#1f77b4", W=680, H=240):
    """#4/#108 — Barras mensuales en SVG puro (imprime perfecto en PDF)."""
    _MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
              "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    vals = [max(float(v or 0), 0.0) for v in vals][:12]
    if not vals or max(vals) <= 0:
        return ""
    ml, mr, mt, mb = 52, 10, 26, 30
    cw, ch = W - ml - mr, H - mt - mb
    y_max = max(vals) * 1.12
    n = len(vals)
    slot = cw / n
    bw = slot * 0.62
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'style="max-width:100%;height:auto;font-family:Arial,sans-serif;">',
         f'<text x="{ml}" y="15" font-size="12" font-weight="bold" fill="#333">{titulo}</text>']
    # Grid horizontal (4 líneas) con etiqueta
    for gi in range(1, 5):
        gy = mt + ch * (1 - gi / 4)
        gv = y_max * gi / 4
        p.append(f'<line x1="{ml}" y1="{gy:.1f}" x2="{W-mr}" y2="{gy:.1f}" '
                 f'stroke="#eee" stroke-width="1"/>')
        p.append(f'<text x="{ml-4}" y="{gy+3:.1f}" font-size="9" fill="#999" '
                 f'text-anchor="end">{gv:,.0f}</text>')
    for i, v in enumerate(vals):
        x = ml + i * slot + (slot - bw) / 2
        h = ch * v / y_max
        y = mt + ch - h
        p.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" '
                 f'fill="{color}" rx="2"/>')
        p.append(f'<text x="{x + bw/2:.1f}" y="{mt + ch + 13}" font-size="9" '
                 f'fill="#666" text-anchor="middle">{_MESES[i] if i < 12 else i+1}</text>')
    p.append(f'<line x1="{ml}" y1="{mt+ch}" x2="{W-mr}" y2="{mt+ch}" '
             f'stroke="#ccc" stroke-width="1"/>')
    p.append('</svg>')
    return "".join(p)


def _flujo_caja_svg(acum, payback=None, titulo="Flujo de caja acumulado (USD)",
                    W=680, H=260):
    """#4/#108 — Curva del flujo acumulado con el cruce de payback marcado."""
    acum = [float(v) for v in acum]
    if len(acum) < 2:
        return ""
    ml, mr, mt, mb = 64, 12, 26, 30
    cw, ch = W - ml - mr, H - mt - mb
    v_min, v_max = min(acum), max(acum)
    if v_max <= v_min:
        return ""
    # Dominio vertical con acolchado simétrico — válido para series negativas,
    # mixtas o enteramente positivas (auditoría: v_min*1.04 fallaba con v_min>0)
    _pad = (v_max - v_min) * 0.04
    _lo, _hi = v_min - _pad, v_max + _pad
    def _x(i): return ml + cw * i / (len(acum) - 1)
    def _y(v): return mt + ch * (1 - (v - _lo) / (_hi - _lo))
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'style="max-width:100%;height:auto;font-family:Arial,sans-serif;">',
         f'<text x="{ml}" y="15" font-size="12" font-weight="bold" fill="#333">{titulo}</text>']
    # Eje cero
    if v_min < 0 < v_max:
        y0 = _y(0)
        p.append(f'<line x1="{ml}" y1="{y0:.1f}" x2="{W-mr}" y2="{y0:.1f}" '
                 f'stroke="#999" stroke-width="1" stroke-dasharray="4,3"/>')
        p.append(f'<text x="{ml-4}" y="{y0+3:.1f}" font-size="9" fill="#999" text-anchor="end">0</text>')
    pts = " ".join(f"{_x(i):.1f},{_y(v):.1f}" for i, v in enumerate(acum))
    p.append(f'<polyline points="{pts}" fill="none" stroke="#1E8449" stroke-width="2.5"/>')
    # Marcas de año cada 5
    for i in range(0, len(acum), 5):
        p.append(f'<text x="{_x(i):.1f}" y="{mt+ch+14}" font-size="9" fill="#666" '
                 f'text-anchor="middle">{i}</text>')
    p.append(f'<text x="{W/2:.0f}" y="{H-2}" font-size="9" fill="#999" '
             f'text-anchor="middle">Año</text>')
    # Punto de payback: primer cruce a positivo (o el valor entregado)
    _pb_idx = next((i for i, v in enumerate(acum) if v >= 0), None)
    if _pb_idx and v_min < 0:
        _px, _py = _x(_pb_idx), _y(acum[_pb_idx])
        _lbl = f"Payback ≈ año {payback:.1f}" if payback else f"Payback ≈ año {_pb_idx}"
        p.append(f'<circle cx="{_px:.1f}" cy="{_py:.1f}" r="5" fill="#F57F17"/>')
        p.append(f'<text x="{min(_px + 8, W - 150):.1f}" y="{_py - 8:.1f}" font-size="10" '
                 f'font-weight="bold" fill="#F57F17">{_lbl}</text>')
    p.append(f'<line x1="{ml}" y1="{mt+ch}" x2="{W-mr}" y2="{mt+ch}" stroke="#ccc" stroke-width="1"/>')
    p.append('</svg>')
    return "".join(p)


def _curva_electrica_svg(curva: dict, N_serie: int, T_frio: float, T_real: float,
                         T_extremo: float, W=680, H=300):
    """
    #? — Curva Voc/Vmp del string vs. temperatura + ventana MPPT del
    inversor, equivalente al gráfico "Array behavior" de PVsyst (pedido
    explícito del usuario, 30-ago-2026). Dibuja exactamente los datos que
    devuelve `calculos.dimensionamiento.curva_electrica_temperatura()` —
    esta función NO evalúa compatibilidad ni recalcula física, solo grafica.
    """
    voc_curva = curva.get("voc_curva") or []
    vmp_curva = curva.get("vmp_curva") or []
    temps = curva.get("temps") or []
    if not temps or not voc_curva or not vmp_curva:
        return ""
    vdc_max    = curva.get("vdc_max")
    vmppt_min  = curva.get("vmppt_min")
    vmppt_max  = curva.get("vmppt_max")
    ev         = curva.get("evaluacion") or {}

    ml, mr, mt, mb = 56, 14, 26, 34
    cw, ch = W - ml - mr, H - mt - mb

    t_lo, t_hi = temps[0], temps[-1]
    v_candidatos = list(voc_curva) + list(vmp_curva)
    if vdc_max:   v_candidatos.append(vdc_max)
    if vmppt_min: v_candidatos.append(vmppt_min)
    if vmppt_max: v_candidatos.append(vmppt_max)
    v_lo = min(v_candidatos) * 0.92
    v_hi = max(v_candidatos) * 1.06
    if v_hi <= v_lo:
        return ""

    def _x(t): return ml + cw * (t - t_lo) / (t_hi - t_lo) if t_hi > t_lo else ml
    def _y(v): return mt + ch * (1 - (v - v_lo) / (v_hi - v_lo))

    compatible = ev.get("compatible")
    color_estado = "#2E7D32" if compatible else ("#C62828" if compatible is False else "#999")
    titulo = f"Compatibilidad eléctrica string–inversor (N={N_serie} en serie)"

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'style="max-width:100%;height:auto;font-family:Arial,sans-serif;">',
         f'<text x="{ml}" y="15" font-size="12" font-weight="bold" fill="#333">{_esc_html(titulo)}</text>']

    # Banda MPPT (verde clara) — la ventana operativa del inversor
    if vmppt_min is not None and vmppt_max is not None:
        y_top, y_bot = _y(vmppt_max), _y(vmppt_min)
        p.append(f'<rect x="{ml}" y="{y_top:.1f}" width="{cw:.1f}" '
                 f'height="{(y_bot - y_top):.1f}" fill="#2E7D32" fill-opacity="0.08"/>')
        for v, etiqueta in ((vmppt_min, "MPPT mín"), (vmppt_max, "MPPT máx")):
            y = _y(v)
            p.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{W-mr}" y2="{y:.1f}" '
                     f'stroke="#2E7D32" stroke-width="1" stroke-dasharray="3,3"/>')
            p.append(f'<text x="{W-mr-4}" y="{y-3:.1f}" font-size="8.5" fill="#2E7D32" '
                     f'text-anchor="end">{etiqueta} {v:.0f}V</text>')

    # Límite absoluto Vdc_max (rojo)
    if vdc_max is not None:
        y = _y(vdc_max)
        p.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{W-mr}" y2="{y:.1f}" '
                 f'stroke="#C62828" stroke-width="1.4" stroke-dasharray="5,3"/>')
        p.append(f'<text x="{ml+4}" y="{y-3:.1f}" font-size="8.5" fill="#C62828">'
                 f'Vdc máx {vdc_max:.0f}V</text>')

    # Grid horizontal ligera
    for gi in range(1, 4):
        gv = v_lo + (v_hi - v_lo) * gi / 4
        gy = _y(gv)
        p.append(f'<text x="{ml-4}" y="{gy+3:.1f}" font-size="8.5" fill="#aaa" '
                 f'text-anchor="end">{gv:,.0f}</text>')

    # Curvas Voc(T) y Vmp(T)
    pts_voc = " ".join(f"{_x(t):.1f},{_y(v):.1f}" for t, v in zip(temps, voc_curva))
    pts_vmp = " ".join(f"{_x(t):.1f},{_y(v):.1f}" for t, v in zip(temps, vmp_curva))
    p.append(f'<polyline points="{pts_voc}" fill="none" stroke="#1565C0" stroke-width="2"/>')
    p.append(f'<polyline points="{pts_vmp}" fill="none" stroke="#EF6C00" stroke-width="2"/>')

    # Puntos clave evaluados (mismos que usa el gate real de compatibilidad)
    for t, v, etiqueta in (
        (T_frio, ev.get("Voc_frio"), "Voc frío"),
        (T_real, ev.get("Vmp_real"), "Vmp real"),
        (T_extremo, ev.get("Vmp_extremo"), "Vmp extremo"),
    ):
        if v is None:
            continue
        cx, cy = _x(t), _y(v)
        p.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.5" fill="{color_estado}" '
                 f'stroke="#fff" stroke-width="1"/>')

    # Eje X (temperatura)
    p.append(f'<line x1="{ml}" y1="{mt+ch}" x2="{W-mr}" y2="{mt+ch}" stroke="#ccc" stroke-width="1"/>')
    for t, etiqueta in ((T_frio, "T mín"), (T_real, "T real"), (T_extremo, "T extremo")):
        x = _x(t)
        p.append(f'<text x="{x:.1f}" y="{mt+ch+14}" font-size="8.5" fill="#666" '
                 f'text-anchor="middle">{etiqueta} {t:.0f}°C</text>')
    p.append(f'<text x="{W/2:.0f}" y="{H-4}" font-size="9" fill="#999" '
             f'text-anchor="middle">Temperatura de celda (°C)</text>')

    # Leyenda
    ly = mt + 2
    for color, etiqueta, lx in ((("#1565C0"), "Voc(T)", W - 210), (("#EF6C00"), "Vmp(T)", W - 130)):
        p.append(f'<line x1="{lx}" y1="{ly}" x2="{lx+16}" y2="{ly}" stroke="{color}" stroke-width="2.5"/>')
        p.append(f'<text x="{lx+20}" y="{ly+3}" font-size="9" fill="#555">{etiqueta}</text>')

    p.append('</svg>')
    return "".join(p)


def generar_html_reporte() -> str:
    # Colectar datos de session_state
    ciudad          = st.session_state.get("tmy_ciudad", st.session_state.get("ciudad", "—"))
    # ── Localización real del predio (tarea #88) ──────────────────────────────
    _ciudad_ref     = st.session_state.get("ciudad", "—")
    _lat_pdf        = st.session_state.get("lat_proyecto")
    _lon_pdf        = st.session_state.get("lon_proyecto")
    _municipio_pdf  = st.session_state.get("municipio_predio", "")
    from datos.ciudades_colombia import CIUDADES as _CIUDADES_PDF
    _c_ref_data     = _CIUDADES_PDF.get(_ciudad_ref, {})
    _coord_es_predio = (
        _lat_pdf is not None and _c_ref_data and
        abs(float(_lat_pdf) - _c_ref_data.get("lat", 0)) > 0.001
    )
    if _coord_es_predio:
        if _municipio_pdf:
            _localizacion_pdf  = f"{_municipio_pdf}  ({float(_lat_pdf):.4f}°N, {abs(float(_lon_pdf)):.4f}°O)"
        else:
            _localizacion_pdf  = f"Predio: {float(_lat_pdf):.5f}°N, {float(_lon_pdf):.5f}°O"
        _localizacion_nota = f"Ciudad de referencia climática TMY: {_ciudad_ref}"
    else:
        # Sin coordenadas personalizadas: usar municipio detectado > ciudad de referencia > tmy_ciudad
        _localizacion_pdf  = _municipio_pdf if _municipio_pdf else _ciudad_ref
        _localizacion_nota = (
            f"TMY descargado para referencia climática: {ciudad}"
            if ciudad != _ciudad_ref
            else "Clima extraído de base TMY/PVGIS"
        )
    area_m2         = st.session_state.get("area_fachada_m2", "—")
    orientacion     = st.session_state.get("orientacion_label", "—")
    tilt            = st.session_state.get("tilt_fachada", "—")
    poa_bruta       = st.session_state.get("poa_anual_kWh_m2", 0.0)
    fecha_hoy       = datetime.date.today().strftime("%d/%m/%Y")

    # Motor Óptico
    mo_sum       = st.session_state.get("motor_optico_summary", {})
    poa_efectiva = st.session_state.get("poa_efectiva_anual_kWh_m2", 0.0)

    # Producción
    res_prod     = st.session_state.get("res_produccion", {})
    n_paneles    = st.session_state.get("N_paneles_final", st.session_state.get("N_paneles_dim", "—"))
    panel_nombre = st.session_state.get("panel_nombre_final", "ASP-ST1-T40")
    p_stc_kw     = st.session_state.get("P_stc_kW_sistema", "—")

    # Bypass diodes
    bypass_ok_r   = st.session_state.get("bypass_ok", False)
    bypass_res_r  = st.session_state.get("bypass_result", {})
    meta_fs_r     = st.session_state.get("meta_fs", {})
    incluir_bypass_r = st.session_state.get("rep_inc_bypass", bypass_ok_r)

    # Financiero
    fin          = st.session_state.get("metricas_financiero", {})
    fin_p90      = st.session_state.get("metricas_financiero_p90", {})
    ben          = st.session_state.get("ben_1715", {})
    capex        = st.session_state.get("capex_total_usd", "—")
    tarifa       = st.session_state.get("tarifa_cop_kWh", st.session_state.get("tarifa_cop_kwh", 850))

    # CO₂ — Huella de Carbono Evitada (Página 12)
    co2_anual_t       = float(st.session_state.get("co2_anual_t", 0.0))
    co2_total_t       = float(st.session_state.get("co2_total_t", 0.0))
    co2_prom_t        = float(st.session_state.get("co2_total_prom_t", 0.0))
    co2_marg_t        = float(st.session_state.get("co2_total_marg_t", 0.0))
    co2_arboles       = float(st.session_state.get("co2_arboles_equiv", 0.0))
    co2_hogares       = float(st.session_state.get("co2_hogares_equiv", 0.0))
    co2_km            = float(st.session_state.get("co2_km_vehiculo_equiv", 0.0))
    co2_bonos_usd     = float(st.session_state.get("co2_valor_bonos_usd", 0.0))
    co2_precio_bono   = float(st.session_state.get("co2_precio_bono_usd", 12.0))
    co2_factor_usado  = float(st.session_state.get("co2_factor_kg_kwh", 0.126))
    co2_metodologia   = str(st.session_state.get("co2_metodologia", "GHG Protocol"))
    co2_factor_fecha  = str(st.session_state.get("co2_factor_fecha", "UPME Resolución 520/2019"))
    co2_real_ok       = bool(st.session_state.get("co2_real_ok", False))
    co2_real_t        = float(st.session_state.get("co2_real_acum_t", 0.0))
    co2_cumpl_pct     = float(st.session_state.get("co2_cumplimiento_pct", 0.0))
    factor_p90_pct    = float(st.session_state.get("factor_p90_pct", 10.0))
    tipo_cambio_rep   = float(st.session_state.get("tipo_cambio", 3400.0))

    # ── Paleta de colores ─────────────────────────────────────────────────────
    COLOR_PRIMARIO  = "#1a5276"
    COLOR_ACENTO    = "#f39c12"
    COLOR_VERDE     = "#1e8449"
    COLOR_TEXTO     = "#2c3e50"
    COLOR_FONDO_SEC = "#f4f6f7"
    COLOR_BORDE     = "#d5d8dc"

    def seccion(titulo, icono, color=COLOR_PRIMARIO):
        return f"""
        <div style="background:{color};color:white;padding:10px 16px;border-radius:6px 6px 0 0;
                    margin-top:28px;margin-bottom:0;">
            <h2 style="margin:0;font-size:1.1em;">{icono} {titulo}</h2>
        </div>
        <div style="border:1px solid {COLOR_BORDE};border-top:none;border-radius:0 0 6px 6px;
                    padding:16px;background:white;margin-bottom:0;">
        """

    def cierre():
        return "</div>"

    def tabla_kv(filas, nota=None):
        """filas = [(label, valor, unidad, nota_fila)]"""
        html = "<table style='width:100%;border-collapse:collapse;font-size:0.92em;'>"
        for i, fila in enumerate(filas):
            lbl, val, uni = fila[0], fila[1], fila[2]
            nota_f = fila[3] if len(fila) > 3 else ""
            bg = "#f8f9fa" if i % 2 == 0 else "white"
            html += f"""
            <tr style="background:{bg};">
                <td style="padding:6px 10px;color:#555;width:40%;">{lbl}</td>
                <td style="padding:6px 10px;font-weight:bold;color:{COLOR_TEXTO};">{val}</td>
                <td style="padding:6px 10px;color:#888;font-size:0.85em;">{uni}</td>
                <td style="padding:6px 10px;color:#666;font-size:0.82em;font-style:italic;">{nota_f}</td>
            </tr>"""
        html += "</table>"
        if nota:
            html += f"<p style='margin:10px 0 0;padding:8px 12px;background:#eaf4fb;border-left:3px solid #2980b9;font-size:0.88em;color:#555;'>{nota}</p>"
        return html

    def caja_nota(texto, color="#eaf4fb", borde="#2980b9", icono="ℹ️"):
        return f"""
        <div style="margin:12px 0;padding:10px 14px;background:{color};
                    border-left:4px solid {borde};border-radius:4px;
                    font-size:0.88em;color:#444;">
            {icono} {texto}
        </div>"""

    # ── Encabezado ────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reporte BIPV — {nombre_proyecto}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin:0; padding:24px;
          color:{COLOR_TEXTO}; background:#f0f2f5; font-size:14px; }}
  .contenedor {{ max-width:900px; margin:0 auto; background:white;
                 padding:32px; border-radius:8px; box-shadow:0 2px 12px rgba(0,0,0,.08); }}
  h1 {{ color:{COLOR_PRIMARIO}; margin-bottom:4px; }}
  h2 {{ margin:0; }}
  .badge {{ display:inline-block; padding:3px 10px; border-radius:12px; font-size:0.78em;
            font-weight:bold; margin-left:8px; }}
  .badge-borrador {{ background:#fdebd0; color:#d35400; }}
  .aviso-borrador {{ background:#fef9e7; border:2px solid {COLOR_ACENTO}; padding:10px 16px;
                     border-radius:6px; margin:16px 0; font-size:0.9em; }}
  table {{ width:100%; }}
  @media print {{
    body {{ background:white; padding:0; }}
    .contenedor {{ box-shadow:none; padding:0; }}
    .no-print {{ display:none; }}
  }}
</style>
</head>
<body>
<div class="contenedor">

  <div style="display:flex;justify-content:space-between;align-items:flex-start;
              border-bottom:3px solid {COLOR_PRIMARIO};padding-bottom:16px;margin-bottom:16px;">
    <div>
      <h1>{_esc_html(nombre_empresa)}</h1>
      {f'<div style="color:#555;font-size:0.95em;margin-top:2px;">{_esc_html(st.session_state.get("empresa_contacto", ""))}</div>'
       if st.session_state.get("empresa_contacto") else ''}
      <div style="font-size:1.15em;font-weight:bold;color:{COLOR_TEXTO};">
        REPORTE TÉCNICO — SISTEMA BIPV
        <span class="badge badge-borrador">BORRADOR</span>
      </div>
      <div style="color:#888;margin-top:4px;font-size:0.92em;">
        Versión 2026 · Generado el {fecha_hoy} · Calculadora BIPV Colombia
      </div>
    </div>
    {f'<img src="{st.session_state.get("empresa_logo_b64")}" alt="logo" '
     f'style="max-height:72px;max-width:220px;object-fit:contain;"/>'
     if st.session_state.get("empresa_logo_b64")
     else f'<div style="text-align:right;color:{COLOR_PRIMARIO};font-size:1.8em;line-height:1;">☀️</div>'}
  </div>

  <div class="aviso-borrador">
    ⚠️ <strong>BORRADOR:</strong> Este reporte es preliminar y fue generado automáticamente
    por la Calculadora BIPV Colombia. Verifique los datos de entrada antes de presentarlo al cliente.
  </div>
"""

    # ── 1. Resumen del Proyecto ───────────────────────────────────────────────
    # ── #54 — Zona horaria del análisis (auditabilidad de gráficos horarios) ──
    try:
        from calculos.tz_utils import utc_offset_latam, tz_label
        _off_pdf = st.session_state.get("utc_offset_local")
        if _off_pdf is None and _lat_pdf is not None and _lon_pdf is not None:
            _off_pdf = utc_offset_latam(float(_lat_pdf), float(_lon_pdf))
        if _off_pdf is None:
            _c_tz = _c_ref_data or {}
            _off_pdf = utc_offset_latam(_c_tz.get("lat", 4.6), _c_tz.get("lon", -74.1))
        _tz_label_pdf = f"{tz_label(int(_off_pdf))} (hora local del sitio)"
    except Exception:
        _tz_label_pdf = "UTC-5 (hora local de Colombia)"

    html += seccion("Información General del Proyecto", "🏠")
    html += tabla_kv([
        ("Nombre del proyecto",  nombre_proyecto,          "",         ""),
        ("Ciudad / Localización", _localizacion_pdf,         "",         _localizacion_nota),
        ("Área de fachada",      _fmt(area_m2, 1),         "m²",       "Superficie total disponible para BIPV"),
        ("Orientación",          str(orientacion),          "",         "Azimut de la fachada"),
        ("Inclinación (tilt)",   str(tilt),                "°",        "90° = fachada vertical típica"),
        ("Panel seleccionado",   panel_nombre,              "",         "Módulo BIPV"),
        ("N° de módulos",        str(n_paneles),            "módulos",  "Resultado de Dimensionamiento"),
        ("Potencia instalada",   _fmt(p_stc_kw, 2),        "kWp",      "Potencia pico DC en STC"),
        # #54 — zona horaria explícita para auditabilidad de gráficos horarios
        ("Zona horaria del análisis", _tz_label_pdf, "",
         "Todas las horas de los gráficos y tablas horarias del informe están en hora local del sitio"),
    ],
    nota="STC: condiciones estándar de prueba (1000 W/m², 25°C, AM 1.5G). "
         "kWp = kilovatios pico instalados.")
    html += cierre()

    # ── 2. Recurso Solar ──────────────────────────────────────────────────────
    if recurso_ok:
        html += seccion("Recurso Solar y POA del Sitio", "☀️")
        tmy_fuente = st.session_state.get("tmy_fuente", "PVGIS ERA-5")
        alt_m      = st.session_state.get("alt_m", "—")
        ghi_anual  = st.session_state.get("ghi_anual_kWh_m2", "—")
        t_media    = st.session_state.get("t_media_anual", "—")
        html += tabla_kv([
            ("Fuente TMY",           str(tmy_fuente),         "",             "Año Meteorológico Típico"),
            ("Altitud",              _fmt(alt_m, 0),           "m s.n.m.",     "Afecta presión atmosférica y temperatura"),
            ("GHI anual",            _fmt(ghi_anual, 0),       "kWh/m²/año",  "Irradiación global horizontal en plano"),
            ("T° ambiente media",    _fmt(t_media, 1),         "°C",           "Media anual del año típico"),
            ("POA bruta (fachada)",  _fmt(poa_bruta, 0),       "kWh/m²/año",  "Irradiación en el plano de la fachada sin correcciones"),
        ],
        nota="POA (Plane Of Array): irradiación sobre el plano inclinado del panel. "
             "Para fachadas verticales, POA es menor que GHI porque los rayos llegan con mayor ángulo. "
             "Esta es la energía disponible ANTES de descontar reflexión, suciedad y temperatura.")

        # ── Ganancia bifacial (solo si el modelo está activo) ─────────────────
        if st.session_state.get("bifacial_activo", False):
            _bif_cfg   = st.session_state.get("bifacial_cfg", {}) or {}
            _bif_gan   = st.session_state.get("ganancia_bifacial_pct", 0.0)
            _bif_bfrac = _bif_cfg.get("bifacialidad", None)
            _bif_alt   = _bif_cfg.get("altura_m", None)
            _bif_alb   = _bif_cfg.get("albedo_trasero", None)
            html += tabla_kv([
                ("Modelo bifacial",        "Activo (pvlib infinite_sheds)", "",  "Captura irradiación en la cara trasera"),
                ("Bifacialidad",           _fmt(_bif_bfrac * 100 if _bif_bfrac is not None else None, 0),
                                           "%",          "Fracción de la eficiencia frontal aprovechada por la cara trasera"),
                ("Altura de montaje",      _fmt(_bif_alt, 2),   "m",   "Separación al plano del suelo/fachada"),
                ("Albedo trasero (suelo)", _fmt(_bif_alb, 2),   "",    "Reflectividad de la superficie tras el módulo"),
                ("Ganancia bifacial anual", _fmt(_bif_gan, 1),  "%",   "Incremento de POA por el aporte de la cara trasera"),
            ],
            nota="Con el modelo bifacial activo, la POA global ya integra el aporte de la cara trasera "
                 "calculado por pvlib (infinite_sheds). La ganancia anual mostrada indica cuánta "
                 "irradiación adicional aporta la cara posterior respecto a un módulo monofacial.")
        html += cierre()

    # ── 2b. Compatibilidad Eléctrica String–Inversor ──────────────────────────
    # Pedido explícito del usuario (30-ago-2026): equivalente al gráfico
    # "Array behavior" de PVsyst. NO reimplementa la verificación eléctrica --
    # llama a la misma curva_electrica_temperatura() que envuelve
    # evaluar_compatibilidad_string(), el gate real ya usado en
    # Dimensionamiento y Producción, así que el veredicto del gráfico nunca
    # puede contradecir al resto de la app.
    from calculos.dimensionamiento import diseno_electrico_confirmado
    _diseno_pdf = diseno_electrico_confirmado(st.session_state)
    _N_serie_pdf = _diseno_pdf["N_serie"]
    _panel_dim_pdf = st.session_state.get("panel_dict")
    _inv_dim_pdf = st.session_state.get("inversor_dict_dim")
    if _N_serie_pdf and _panel_dim_pdf and _inv_dim_pdf:
        try:
            from calculos.dimensionamiento import curva_electrica_temperatura
            _T_frio_pdf = st.session_state.get("T_min_diseno", -5.0)
            _T_real_pdf = st.session_state.get("T_cel_realista", 36.35)
            _T_extr_pdf = st.session_state.get("T_cel_extremo", 41.94)
            _n_str_tr_pdf = _diseno_pdf["N_strings_tracker"]
            _curva_pdf = curva_electrica_temperatura(
                _panel_dim_pdf, _inv_dim_pdf, int(_N_serie_pdf),
                _T_frio_pdf, _T_real_pdf, _T_extr_pdf,
                N_strings_tracker=_n_str_tr_pdf,
            )
            _svg_curva = _curva_electrica_svg(
                _curva_pdf, int(_N_serie_pdf), _T_frio_pdf, _T_real_pdf, _T_extr_pdf
            )
        except Exception:
            _svg_curva = ""
        if _svg_curva:
            _ev_pdf = _curva_pdf["evaluacion"]
            _compat_pdf = _ev_pdf.get("compatible")
            _estado_pdf = (
                "🟢 Compatible" if _compat_pdf
                else ("🔴 Incompatible" if _compat_pdf is False else "⚪ No evaluable")
            )
            html += seccion("Compatibilidad Eléctrica String–Inversor", "⚡")
            html += _bloque_grafica(
                _svg_curva,
                "Voc(T) y Vmp(T) del string frente a la ventana MPPT y el límite Vdc máximo "
                "del inversor, en las 3 temperaturas de diseño del sitio. Los puntos marcados "
                "son los mismos valores que evalúa el gate de compatibilidad de Dimensionamiento "
                "y Producción — este gráfico no verifica nada distinto, solo lo visualiza."
            )
            html += tabla_kv([
                ("Estado", _estado_pdf, "", "Veredicto real del gate de compatibilidad eléctrica"),
                ("N° módulos en serie", str(int(_N_serie_pdf)), "", ""),
                ("Voc en frío", _fmt(_ev_pdf.get("Voc_frio"), 0), "V", f"a T mín {_T_frio_pdf:.1f}°C"),
                ("Vmp en condición real", _fmt(_ev_pdf.get("Vmp_real"), 0), "V", f"a T real {_T_real_pdf:.1f}°C"),
                ("Vmp en condición extrema", _fmt(_ev_pdf.get("Vmp_extremo"), 0), "V", f"a T extremo {_T_extr_pdf:.1f}°C"),
            ] + ([("Observaciones", "; ".join(_ev_pdf.get("mensajes", [])), "", "")]
                 if _ev_pdf.get("mensajes") else []),
            nota="Voc y Vmp son funciones lineales de la temperatura de celda: verificar los "
                 "3 puntos de diseño (frío, real, extremo) cubre con certeza matemática toda la "
                 "curva continua entre ellos — el gráfico es para verificación visual, no agrega "
                 "precisión sobre el cálculo ya validado."
                 + (f" ⚠️ {_diseno_pdf['aviso']}" if _diseno_pdf["aviso"] else ""))
            html += cierre()

    # ── 3. Motor Óptico ───────────────────────────────────────────────────────
    if motor_optico and incluir_motor and mo_sum:
        b0       = mo_sum.get("b0",    "—")
        k_bipv   = mo_sum.get("k_bipv","—")
        noct     = mo_sum.get("noct",  "—")
        coef_t   = mo_sum.get("coef_temp", 0) * 100
        tau_pct  = mo_sum.get("transparencia", 0.0) * 100
        f_global = mo_sum.get("factor_global", 1.0)
        p_iam    = mo_sum.get("perdida_iam_kWh_m2",  0)
        p_soil   = mo_sum.get("perdida_soil_kWh_m2", 0)
        p_term   = mo_sum.get("perdida_term_kWh_m2", 0)
        f_iam    = mo_sum.get("f_iam_prom",  1.0)
        f_soil   = mo_sum.get("f_soil_prom", 1.0)
        f_term   = mo_sum.get("f_term_prom", 1.0)

        html += seccion("Correcciones Óptico-Térmicas — Motor Óptico BIPV", "🔆", COLOR_VERDE)
        html += f"""
        <p style="margin:0 0 12px;color:#555;font-size:0.92em;">
            Las calculadoras convencionales usan la POA bruta directamente. El Motor Óptico
            aplica tres correcciones físicas reales que reducen la energía efectivamente disponible
            para el semiconductor BIPV.
        </p>"""

        _tau_row = [("— Transparencia τ", _fmt(tau_pct, 0), "%",
                     "Fracción de luz que atraviesa el vidrio; 0% = panel opaco. "
                     "Informacional: ya está incluida en el Isc_stc del catálogo.")]
        html += tabla_kv([
            ("Parámetros usados", "", "", ""),
            ("— Tipo de vidrio (b₀ ASHRAE)",      _fmt(b0, 3),      "",      "Reflexión del vidrio a ángulos oblicuos"),
            ("— Montaje / confinamiento (k_BIPV)", str(k_bipv),      "",      "1.0 ventilado · 1.3 confinado · 1.5 sellado"),
            ("— NOCT",                             _fmt(noct, 0),   "°C",    "Temperatura nominal de operación"),
            ("— Coef. temperatura γ",              _fmt(coef_t, 2), "%/°C",  "Caída de eficiencia por temperatura"),
        ] + (_tau_row if tau_pct > 0 else []))

        html += f"""
        <div style="margin:16px 0;overflow:auto;">
        <table style="width:100%;border-collapse:collapse;font-size:0.9em;">
          <thead>
            <tr style="background:{COLOR_PRIMARIO};color:white;">
              <th style="padding:8px 12px;text-align:left;">Etapa de corrección</th>
              <th style="padding:8px 12px;text-align:right;">Factor promedio</th>
              <th style="padding:8px 12px;text-align:right;">Pérdida anual</th>
              <th style="padding:8px 12px;text-align:right;">Pérdida (%)</th>
              <th style="padding:8px 12px;text-align:left;">Qué representa</th>
            </tr>
          </thead>
          <tbody>
            <tr style="background:#f8f9fa;">
              <td style="padding:7px 12px;">POA bruta (entrada)</td>
              <td style="padding:7px 12px;text-align:right;">1.000</td>
              <td style="padding:7px 12px;text-align:right;font-weight:bold;">{poa_bruta:,.0f} kWh/m²/año</td>
              <td style="padding:7px 12px;text-align:right;">—</td>
              <td style="padding:7px 12px;color:#888;">Irradiación del sitio sin correcciones</td>
            </tr>
            <tr>
              <td style="padding:7px 12px;">① IAM — Reflexión del vidrio</td>
              <td style="padding:7px 12px;text-align:right;">{f_iam:.4f}</td>
              <td style="padding:7px 12px;text-align:right;color:#c0392b;">−{p_iam:,.0f} kWh/m²/año</td>
              <td style="padding:7px 12px;text-align:right;color:#c0392b;">−{(1-f_iam)*100:.1f}%</td>
              <td style="padding:7px 12px;color:#888;">
                El vidrio refleja parte de la luz solar cuando el ángulo de incidencia es alto
                (mañanas, tardes, invierno). En fachadas verticales esta pérdida es la mayor
                de las tres porque los ángulos son siempre oblicuos.
              </td>
            </tr>
            <tr style="background:#f8f9fa;">
              <td style="padding:7px 12px;">② Soiling — Suciedad estacional</td>
              <td style="padding:7px 12px;text-align:right;">{f_soil:.4f}</td>
              <td style="padding:7px 12px;text-align:right;color:#c0392b;">−{p_soil:,.0f} kWh/m²/año</td>
              <td style="padding:7px 12px;text-align:right;color:#c0392b;">−{(1-f_soil)*100:.1f}%</td>
              <td style="padding:7px 12px;color:#888;">
                Polvo, smog y material particulado acumulado en el vidrio. En Colombia varía
                según temporadas: mayor en época seca (Ene-Feb, Jul-Ago), menor en temporadas
                de lluvia (Abr-May, Oct-Nov) por autolavado natural.
              </td>
            </tr>
            <tr>
              <td style="padding:7px 12px;">③ Térmico — Temperatura de celda</td>
              <td style="padding:7px 12px;text-align:right;">{f_term:.4f}</td>
              <td style="padding:7px 12px;text-align:right;color:#c0392b;">−{p_term:,.1f} kWh/m²/año</td>
              <td style="padding:7px 12px;text-align:right;color:#c0392b;">−{(1-f_term)*100:.1f}%</td>
              <td style="padding:7px 12px;color:#888;">
                La celda fotovoltaica pierde eficiencia cuando supera 25°C. En BIPV de fachada,
                la cámara trasera restringida eleva la temperatura (k_BIPV={k_bipv}). La pérdida
                neta depende del clima local (Bogotá es favorecida por su temperatura fresca).
              </td>
            </tr>
            <tr style="background:{COLOR_VERDE};color:white;font-weight:bold;">
              <td style="padding:8px 12px;">POA efectiva (resultado)</td>
              <td style="padding:8px 12px;text-align:right;">{f_global:.4f}</td>
              <td style="padding:8px 12px;text-align:right;">{poa_efectiva:,.0f} kWh/m²/año</td>
              <td style="padding:8px 12px;text-align:right;">{f_global*100:.1f}% de la bruta</td>
              <td style="padding:8px 12px;">Energía real disponible para la celda</td>
            </tr>
          </tbody>
        </table>
        </div>"""

        # ── Gráfico waterfall de la cascada (SVG inline, sin librerías externas) ──
        html += f"""
        <div style="margin:20px 0 8px;text-align:center;">
        {_waterfall_cascada_svg(
            poa_bruta, p_iam, p_soil, p_term, poa_efectiva,
            COLOR_VERDE, COLOR_PRIMARIO
        )}
        </div>"""

        html += caja_nota(
            f"<strong>¿Por qué importa?</strong> Sin el Motor Óptico, la calculadora usa la POA bruta "
            f"({poa_bruta:,.0f} kWh/m²/año) y sobreestima la producción en "
            f"<strong>{(poa_bruta - poa_efectiva):,.0f} kWh/m²/año ({(1-f_global)*100:.1f}%)</strong>. "
            f"Para un proyecto de 100 m², esto representa ~{(poa_bruta-poa_efectiva)*100*0.12:.0f} kWh/año "
            f"de diferencia en la predicción. El Motor Óptico da el número correcto.",
            color="#e9f7ef", borde=COLOR_VERDE, icono="💡"
        )
        html += cierre()

    # ── 4. Producción ─────────────────────────────────────────────────────────
    if produccion_ok and incluir_prod and res_prod:
        E_ac  = res_prod.get("E_ac_anual_kWh", 0)
        E_dc  = res_prod.get("E_dc_anual_kWh", 0)
        PR    = res_prod.get("PR", 0) * 100
        Yf    = res_prod.get("Y_f", 0)
        Yr    = res_prod.get("Y_r", 0)
        CF    = res_prod.get("CF_pct", 0)
        eta   = st.session_state.get("eta_inversor", 0.975) * 100
        mismatch_f = st.session_state.get("factor_global_mismatch", 1.0)
        fuente_poa = "Motor Óptico (IAM+Soiling+Térmico)" if motor_optico else "POA bruta"

        html += seccion("Producción Anual — Simulación IEC 61724", "📊")
        html += tabla_kv([
            ("Fuente de irradiación usada",  fuente_poa,          "",         "POA aplicada en la simulación"),
            ("Factor Mismatch aplicado",     _fmt(mismatch_f*100, 1), "%",   "Pérdida por desajuste de strings"),
            ("Eficiencia del inversor",      _fmt(eta, 1),         "%",        "Eficiencia CEC weighted"),
            ("E_dc anual (generación DC)",   _fmt(E_dc, 0),        "kWh/año", "Energía generada por los módulos"),
            ("E_ac anual (entrega a red)",   _fmt(E_ac, 0),        "kWh/año", "Energía AC neta entregada al edificio"),
            ("Performance Ratio (PR)",       _fmt(PR, 1),          "%",        "IEC 61724: PR = Y_f / Y_r · Bueno: >75%"),
            ("Y_f — Final yield",            _fmt(Yf, 0),          "kWh/kWp", "Horas equivalentes a plena carga AC"),
            ("Y_r — Reference yield",        _fmt(Yr, 0),          "h",        "Horas sol pico equivalentes en el sitio"),
            ("Factor de Planta",             _fmt(CF, 2),          "%",        "E_ac / (P_STC × 8 760 h)"),
        ],
        nota="Performance Ratio > 100%: posible en climas fríos de alta altitud (Bogotá, Medellín) "
             "donde los módulos CdTe operan por debajo de 25°C muchas horas, ganando eficiencia "
             "respecto a las condiciones STC. IEC 61724 permite PR > 100% — es un resultado físicamente correcto.")
        # ── #4/#108 — Gráfica de barras de producción mensual ────────────────
        _df_m_pdf = st.session_state.get("df_mensual_produccion")
        if _df_m_pdf is not None and "E_ac (kWh)" in getattr(_df_m_pdf, "columns", []):
            _svg_mes = _barras_mensuales_svg(list(_df_m_pdf["E_ac (kWh)"]))
            if _svg_mes:
                html += _bloque_grafica(
                    _svg_mes, "Energía AC neta entregada por mes (kWh).")
        html += cierre()

    # ── 4b. Diagnóstico PR real vs esperado ──────────────────────────────────
    df_diag_real = st.session_state.get("df_diagnostico_real")
    meses_rojo_d = st.session_state.get("diag_meses_rojo", [])
    meses_amar_d = st.session_state.get("diag_meses_amarillo", [])
    total_real_d = st.session_state.get("diag_total_real_kwh", 0)
    total_sim_d  = st.session_state.get("diag_total_sim_kwh", 0)

    if df_diag_real is not None and total_real_d > 0:
        pr_conv_g_d  = st.session_state.get("diag_pr_conv_global",  0.0)
        pr_corr_g_d  = st.session_state.get("diag_pr_corr_global",  0.0)
        perd_t_pct_d = st.session_state.get("diag_perdida_t_pct",   0.0)
        perd_t_kwh_d = st.session_state.get("diag_perdida_t_kwh",   0.0)
        total_stc_d  = st.session_state.get("diag_total_stc_kwh",   0.0)
        gamma_d      = st.session_state.get("diag_gamma_pct",       -0.45)

        html += seccion("Diagnóstico BIPV: PR convencional · PR corregido T° · Pérdidas temperatura", "🔍")

        # Métricas globales
        html += tabla_kv([
            ("PR convencional global",
             _fmt(pr_conv_g_d*100, 1), "%",
             "E_real ÷ (P_STC × HSP) — incluye todas las pérdidas incluida temperatura"),
            ("PR corregido por temperatura",
             _fmt(pr_corr_g_d*100, 1), "%",
             "PR_conv ÷ factor_T — elimina efecto térmico → muestra pérdidas reales no-térmicas"),
            ("% Pérdidas por temperatura (promedio)",
             _fmt(perd_t_pct_d, 1), "%",
             f"γ × (T_cell_media − 25°C) · γ = {gamma_d:+.3f}%/°C · Normal en BIPV fachada: 8–15%"),
            ("Energía perdida por temperatura",
             _fmt(perd_t_kwh_d, 0), "kWh",
             "kWh que la temperatura 'consumió' en los meses con dato"),
            ("E_real acumulada (inversor)",
             _fmt(total_real_d, 0), "kWh", "Suma kWh reales ingresados"),
            ("E_simulada con T° real",
             _fmt(total_sim_d,  0), "kWh", "Lo que el modelo predijo con temperatura real del TMY"),
            ("E_STC (T=25°C, sin pérd. T°)",
             _fmt(total_stc_d,  0), "kWh", "Producción si T_cell fuera siempre 25°C — límite térmico"),
            ("Diferencia real vs simulado",
             f"{total_real_d - total_sim_d:+,.0f}", "kWh",
             f"{(total_real_d-total_sim_d)/total_sim_d*100:+.1f}% · positivo = supera la simulación"),
            ("Meses PR_corr < 80% (problema)",
             ", ".join(meses_rojo_d) if meses_rojo_d else "Ninguno", "",
             "Pérdidas no-térmicas significativas — inspección urgente"),
            ("Meses PR_corr 80–90% (revisar)",
             ", ".join(meses_amar_d) if meses_amar_d else "Ninguno", "",
             "Suciedad, sombreado leve o degradación moderada"),
        ],
        nota="PR convencional = E_real ÷ (P_STC × HSP) — estándar IEC 61724, incluye pérdidas temperatura. "
             "PR corregido = PR_conv ÷ (1 + γ×ΔT) — elimina efecto térmico; revela pérdidas reales "
             "(suciedad, sombras, degradación, cableado). "
             "🟢 PR_corr ≥ 90%: excelente (pérdidas son principalmente térmicas, normales en BIPV). "
             "🟡 80–90%: revisar limpieza y strings. "
             "🔴 < 80%: problema real no térmico — inspección de campo urgente.")

        # Tabla mes a mes
        cols_pdf = ["Mes","HSP (h)","T_cell (°C)","% Pérd. T°",
                    "E_sim (kWh)","E_real (kWh)",
                    "PR_conv (%)","PR_corr_T (%)","Δ kWh","Estado"]
        filas_diag = df_diag_real[df_diag_real["E_real (kWh)"] != "—"]
        if not filas_diag.empty:
            html += """
            <table style="width:100%;border-collapse:collapse;font-size:0.82em;margin-bottom:14px;">
            <thead><tr style="background:#1A569A;color:#fff;">"""
            for col in cols_pdf:
                align = "left" if col == "Mes" else "right" if col not in ["Estado"] else "center"
                html += f'<th style="padding:5px 6px;text-align:{align};">{col}</th>'
            html += "</tr></thead><tbody>"
            for ri, (_, row) in enumerate(filas_diag.iterrows()):
                bg = "#fff" if ri % 2 == 0 else "#f4f7fb"
                estado_str = str(row.get("Estado","—"))
                color_est = "#c62828" if "🔴" in estado_str else "#f9a825" if "🟡" in estado_str else "#2e7d32"
                html += f'<tr style="background:{bg};">'
                for col in cols_pdf:
                    val = row.get(col,"—")
                    align = "left" if col == "Mes" else "center" if col == "Estado" else "right"
                    weight = "700" if col in ["E_real (kWh)","PR_conv (%)","PR_corr_T (%)"] else "400"
                    color  = color_est if col == "Estado" else "inherit"
                    html += f'<td style="padding:4px 6px;text-align:{align};font-weight:{weight};color:{color};">{val}</td>'
                html += "</tr>"
            html += "</tbody></table>"
        html += cierre()

    # ── 4c. Pérdidas por bypass diodes ────────────────────────────────────────
    if bypass_ok_r and incluir_bypass_r and bypass_res_r:
        kwh_bp   = bypass_res_r.get("kwh_bypass_anual", 0)
        pct_bp   = bypass_res_r.get("pct_bypass_anual", 0)
        h_bp     = bypass_res_r.get("horas_bypass", 0)
        h_somb   = bypass_res_r.get("horas_sombra", 0)
        e_dc_uni = bypass_res_r.get("kwh_dc_uniforme", 0)
        e_ac_bp  = st.session_state.get("E_ac_anual_kWh_bypass", 0)
        col_fs_r = meta_fs_r.get("col_original", "FS")
        from calculos.contrato_sombreado import etiqueta_fuente_fs as _etq_fs_pdf
        # Preferir la fuente registrada en la base congelada (sobrevive F5);
        # respaldo: la de la sesión viva.
        _fs_fuente_r = None
        _f4_r = st.session_state.get("escenarios_fase4") or {}
        _base_r = _f4_r.get("base_comparacion") or {}
        try:
            _fs_fuente_r = (_base_r.get("componentes", {})
                            .get("fachadas_y_puntos", {})
                            .get("valor", {}).get("fs_fuente"))
        except AttributeError:
            _fs_fuente_r = None
        if not _fs_fuente_r:
            _fs_fuente_r = st.session_state.get("fs_fuente")
        _etiqueta_fuente_fs_r = _etq_fs_pdf(_fs_fuente_r)
        tipo_fsr = meta_fs_r.get("tipo", "combinado")
        modo_uso = st.session_state.get("bypass_modo_usado", "mensual")
        df_m_bp  = bypass_res_r.get("df_mensual_bypass")

        html += seccion("Pérdidas por Bypass Diodes — Sombra Parcial en Strings", "⚡")
        html += tabla_kv([
            ("Pérdida anual por bypass diodes",
             _fmt(kwh_bp, 0), "kWh DC/año",
             "Energía DC adicional perdida cuando los bypass diodes se activan por sombra de obstáculos"),
            ("% sobre producción DC",
             _fmt(pct_bp, 2), "%",
             "Fracción de la producción DC base perdida por activación de bypass diodes"),
            ("Horas con bypass activo",
             f"{h_bp:,}", "h/año",
             "Horas al año donde al menos un bypass diode en el array se activa"),
            ("Horas con sombra geométrica",
             f"{h_somb:,}", "h/año",
             "Horas con Factor de Sombreado > 5% según el modelo 3D"),
            ("E_ac corregida (con bypass)",
             _fmt(e_ac_bp, 0) if e_ac_bp else "—", "kWh AC/año",
             "Producción AC real = E_ac simulada − pérdida_bypass × η_inversor"),
            ("Fuente de datos FS",
             col_fs_r, "",
             "Geometrico = solo obstáculos físicos · Combinado = geom + nubes (sobreestima)"),
            ("Fuente del sombreado",
             _etiqueta_fuente_fs_r, "",
             "Herramienta que generó la geometría de sombras: SketchUp (interno), "
             "Site Designer + TMY (externo) o CSV externo"),
            ("Modo cobertura temporal",
             "Patrón mensual" if modo_uso == "mensual" else "Días críticos exactos", "",
             "Mensual replica el patrón del día crítico a todos los días del mes"),
        ],
        nota=(
            "Los bypass diodes se activan cuando un obstáculo físico (edificio vecino, voladizo) "
            "sombrea parte de un string, reduciendo Isc por debajo del punto de operación del "
            "resto de módulos. A diferencia de la reducción escalar de irradiancia, el bypass "
            "elimina toda la tensión de los módulos sombreados → pérdida mayor. "
            f"{'🟢 Bajo impacto (<2%)' if pct_bp < 2 else '🟡 Impacto moderado (2–5%)' if pct_bp < 5 else '🔴 Impacto alto (>5%)'}"
            " — Ref: Deline et al. 2013."
        ))

        # Tabla mensual de bypass
        if df_m_bp is not None:
            try:
                html += """
                <table style="width:100%;border-collapse:collapse;font-size:0.82em;margin-bottom:14px;">
                <thead><tr style="background:#B71C1C;color:#fff;">
                <th style="padding:5px 8px;text-align:left;">Mes</th>
                <th style="padding:5px 8px;text-align:right;">E_dc con bypass (kWh)</th>
                <th style="padding:5px 8px;text-align:right;">Pérdida bypass (kWh)</th>
                <th style="padding:5px 8px;text-align:right;">FS medio</th>
                <th style="padding:5px 8px;text-align:right;">Horas bypass</th>
                </tr></thead><tbody>"""
                for ri, (mes, row) in enumerate(df_m_bp.iterrows()):
                    bg = "#fff" if ri % 2 == 0 else "#fdf2f2"
                    p_loss = float(row.get("Pérdida bypass (kWh)", 0))
                    color_p = "#c62828" if p_loss > 50 else "#e53935" if p_loss > 20 else "inherit"
                    html += f"""<tr style="background:{bg};">
                    <td style="padding:4px 8px;font-weight:600;">{mes}</td>
                    <td style="padding:4px 8px;text-align:right;">{float(row.get('E_dc con bypass (kWh)',0)):,.0f}</td>
                    <td style="padding:4px 8px;text-align:right;color:{color_p};font-weight:700;">{p_loss:,.1f}</td>
                    <td style="padding:4px 8px;text-align:right;">{float(row.get('FS medio mensual',0)):.3f}</td>
                    <td style="padding:4px 8px;text-align:right;">{float(row.get('Horas bypass activo',0)):.0f}</td>
                    </tr>"""
                html += "</tbody></table>"
            except Exception:
                pass
        html += cierre()

    # ── 4d. Desglose Multi-Superficie (#45) ──────────────────────────────────
    _inc_ms = st.session_state.get("rep_inc_multisup", False)
    _ms_activo    = bool(st.session_state.get("multisup_activo", False))
    _ms_desglose  = st.session_state.get("multisup_desglose", [])
    _ms_e_ac      = float(st.session_state.get("E_ac_anual_kWh_multisup", 0.0))
    _ms_area      = float(st.session_state.get("area_total_multisup", 0.0))
    _ms_bp_ok     = bool(st.session_state.get("bypass_multisup_ok", False))
    _ms_bp_rows   = st.session_state.get("bypass_multisup_resultados", [])

    if _inc_ms and _ms_activo and _ms_desglose and _ms_e_ac > 0:
        html += seccion("Producción Multi-Superficie — Desglose por Superficie BIPV", "🏗️", "#6c3483")

        # Tabla de desglose
        html += """
        <table style="width:100%;border-collapse:collapse;font-size:0.88em;margin-bottom:14px;">
        <thead><tr style="background:#6c3483;color:#fff;">
          <th style="padding:6px 10px;text-align:left;">Superficie</th>
          <th style="padding:6px 10px;text-align:left;">Tipo</th>
          <th style="padding:6px 10px;text-align:right;">Área (m²)</th>
          <th style="padding:6px 10px;text-align:right;">% área</th>
          <th style="padding:6px 10px;text-align:right;">POA (kWh/m²/año)</th>
          <th style="padding:6px 10px;text-align:right;">E_ac (kWh/año)</th>
          <th style="padding:6px 10px;text-align:right;">% E_ac</th>
        </tr></thead><tbody>"""
        for _ri, _s in enumerate(_ms_desglose):
            _bg = "#f4f6f7" if _ri % 2 == 0 else "white"
            _pct_a = _s.get("area_m2", 0) / max(1.0, _ms_area) * 100
            _pct_e = _s.get("e_ac_kWh", 0) / max(1.0, _ms_e_ac) * 100
            html += f"""
            <tr style="background:{_bg};">
              <td style="padding:5px 10px;font-weight:600;">{_s.get('nombre','—')}</td>
              <td style="padding:5px 10px;color:#666;">{_s.get('tipo','—')}</td>
              <td style="padding:5px 10px;text-align:right;">{_s.get('area_m2',0):.1f}</td>
              <td style="padding:5px 10px;text-align:right;color:#888;">{_pct_a:.1f}%</td>
              <td style="padding:5px 10px;text-align:right;">{_s.get('poa_kWh_m2',0):,.0f}</td>
              <td style="padding:5px 10px;text-align:right;font-weight:700;">{_s.get('e_ac_kWh',0):,.0f}</td>
              <td style="padding:5px 10px;text-align:right;color:#6c3483;">{_pct_e:.1f}%</td>
            </tr>"""
        html += f"""
            <tr style="background:#6c3483;color:white;font-weight:bold;">
              <td style="padding:6px 10px;" colspan="2">TOTAL SISTEMA</td>
              <td style="padding:6px 10px;text-align:right;">{_ms_area:.1f}</td>
              <td style="padding:6px 10px;text-align:right;">100%</td>
              <td style="padding:6px 10px;text-align:right;">—</td>
              <td style="padding:6px 10px;text-align:right;">{_ms_e_ac:,.0f}</td>
              <td style="padding:6px 10px;text-align:right;">100%</td>
            </tr>
        </tbody></table>"""

        # Tabla bypass por superficie (si está disponible)
        if _ms_bp_ok and _ms_bp_rows:
            html += """
            <p style="margin:16px 0 8px;font-weight:600;color:#6c3483;">
              ⚡ Pérdidas por bypass diodes — por superficie
            </p>
            <table style="width:100%;border-collapse:collapse;font-size:0.85em;margin-bottom:14px;">
            <thead><tr style="background:#922b21;color:#fff;">
              <th style="padding:5px 8px;text-align:left;">Superficie</th>
              <th style="padding:5px 8px;text-align:left;">Fachada CSV</th>
              <th style="padding:5px 8px;text-align:right;">E_ac base (kWh/año)</th>
              <th style="padding:5px 8px;text-align:right;">Pérdida bypass (%)</th>
              <th style="padding:5px 8px;text-align:right;">Horas bypass/año</th>
              <th style="padding:5px 8px;text-align:right;">E_ac con bypass (kWh/año)</th>
            </tr></thead><tbody>"""
            for _bi, _br in enumerate(_ms_bp_rows):
                _bg = "#fff" if _bi % 2 == 0 else "#fdf2f2"
                html += f"""
                <tr style="background:{_bg};">
                  <td style="padding:4px 8px;font-weight:600;">{_br.get('Superficie','—')}</td>
                  <td style="padding:4px 8px;color:#888;">{_br.get('Fachada CSV','—')}</td>
                  <td style="padding:4px 8px;text-align:right;">{_br.get('E_ac base (kWh/año)','—')}</td>
                  <td style="padding:4px 8px;text-align:right;color:#c62828;font-weight:700;">{_br.get('Pérdida bypass (%)','—')}</td>
                  <td style="padding:4px 8px;text-align:right;">{_br.get('Horas bypass/año','—')}</td>
                  <td style="padding:4px 8px;text-align:right;font-weight:700;">{_br.get('E_ac bypass (kWh/año)','—')}</td>
                </tr>"""
            html += f"""
                <tr style="background:#922b21;color:white;font-weight:bold;">
                  <td colspan="5" style="padding:5px 8px;">E_ac TOTAL CON BYPASS</td>
                  <td style="padding:5px 8px;text-align:right;">{_ms_e_ac:,.0f} kWh/año</td>
                </tr>
            </tbody></table>"""

        html += caja_nota(
            f"Sistema con <strong>{len(_ms_desglose)} superficies activas</strong> — "
            f"área total <strong>{_ms_area:.1f} m²</strong> · "
            f"E_ac total <strong>{_ms_e_ac:,.0f} kWh/año</strong> · "
            f"densidad <strong>{_ms_e_ac / max(1.0, _ms_area):.0f} kWh/m²·año</strong>."
            + (" Los valores de E_ac ya incluyen la corrección por bypass diodes."
               if _ms_bp_ok else ""),
            color="#f5eef8", borde="#6c3483", icono="🏗️"
        )
        html += cierre()

    # ── 5. Financiero ─────────────────────────────────────────────────────────
    if financiero_ok and incluir_fin and fin:
        vpn        = fin.get("vpn_usd", 0)
        tir        = fin.get("tir_pct")
        payback    = fin.get("payback_simple")
        lcoe_cop   = fin.get("lcoe_cop_kWh", 0)
        capex_n    = ben.get("capex_neto_usd", capex) if ben else capex
        des_1715   = ben.get("descuento_ica_pct", 0) if ben else 0

        # Trazabilidad E_ac (#38): multi-sup > bypass > base
        _e_ac_base_pdf     = res_prod.get("E_ac_anual_kWh", 0)
        _e_ac_bypass_pdf   = st.session_state.get("E_ac_anual_kWh_bypass", 0)
        _e_ac_multisup_pdf = float(st.session_state.get("E_ac_anual_kWh_multisup", 0.0))
        _multisup_ok_pdf   = bool(st.session_state.get("multisup_activo", False))
        _n_sups_pdf        = len(st.session_state.get("multisup_desglose", []))
        _kwh_bp_pdf        = bypass_res_r.get("kwh_bypass_anual", 0) if bypass_ok_r else 0
        _e_ac_fin_label    = (
            f"{_e_ac_multisup_pdf:,.0f} kWh/año "
            f"(multi-superficie — {_n_sups_pdf} superficies{'  + bypass' if st.session_state.get('bypass_multisup_ok') else ''})"
            if (_multisup_ok_pdf and _e_ac_multisup_pdf > 0)
            else (
                f"{_e_ac_bypass_pdf:,.0f} kWh/año (corregida por bypass diodes)"
                if (bypass_ok_r and _e_ac_bypass_pdf > 0)
                else f"{_e_ac_base_pdf:,.0f} kWh/año (simulación estándar superficie única)"
            )
        )

        html += seccion("Análisis Financiero — Ley 1715 / 2014", "💰")
        html += tabla_kv([
            ("CAPEX total (bruto)",   _fmt(capex,    0),  "USD",      "Costo total del sistema instalado"),
            ("CAPEX neto (Ley 1715)", _fmt(capex_n,  0),  "USD",      "Después de beneficios tributarios"),
            ("Descuento ICA / IVA",   _fmt(des_1715, 1),  "%",        "Beneficio Ley 1715 de 2014 Colombia"),
            ("E_ac usada en el análisis", _e_ac_fin_label, "",
             "La E_ac corregida por bypass ya descuenta las pérdidas por sombra parcial en strings — "
             "estimación conservadora y realista para proyectos BIPV urbanos"),
            *([(
                "Pérdida bypass descontada",
                f"{_kwh_bp_pdf:,.0f} kWh/año  ({_kwh_bp_pdf / _e_ac_base_pdf * 100:.1f}% de E_ac base)",
                "",
                "Energía DC perdida por activación de bypass diodes × η_inversor"
            )] if (bypass_ok_r and _e_ac_bypass_pdf > 0 and _e_ac_base_pdf > 0) else []),
            ("Tarifa de referencia",  _fmt(tarifa,   0),  "COP/kWh",  "Precio de energía del contrato o tarifa pública"),
            ("VPN (20 años)",         _fmt(vpn,      0),  "USD",      "Valor Presente Neto del proyecto"),
            ("TIR",                   _fmt(tir,      1) if tir else "N/A",   "%", "Tasa Interna de Retorno"),
            ("Payback simple",        _fmt(payback,  1) if payback else "> horizonte", "años", "Período de recuperación de la inversión"),
            ("LCOE",                  _fmt(lcoe_cop, 0),  "COP/kWh",  "Costo nivelado de la energía generada"),
            # #52 — trazabilidad de la degradación usada en el flujo de caja
            *([(
                "Tasa de degradación",
                f"{float(st.session_state.get('tasa_degradacion_usada', 0)):.2f} %/año "
                f"({st.session_state.get('fuente_degradacion', '')})",
                "",
                "Con degradación medida del historial PR real, la TIR refleja el "
                "comportamiento verificado del sistema — mayor rigor para banca/UPME"
            )] if st.session_state.get("tasa_degradacion_usada") else []),
        ],
        nota="VPN > 0 y TIR > WACC (costo del capital) indican proyecto viable. "
             "LCOE < tarifa de red indica que generar es más barato que comprar. "
             "Los beneficios de la Ley 1715/2014 incluyen: deducción del 50% del IVA en equipos, "
             "exención de aranceles, y depreciación acelerada.")
        # ── #4/#108 — Curva del flujo de caja acumulado con payback ──────────
        _comp_pdf = st.session_state.get("comp_financiero") or {}
        _flujos_pdf = (_comp_pdf.get("con") or {}).get("flujos") or []
        _acum_pdf = [f.get("flujo_acum_usd", 0) for f in _flujos_pdf]
        if len(_acum_pdf) >= 2:
            _svg_fc = _flujo_caja_svg(_acum_pdf, payback=payback)
            if _svg_fc:
                html += _bloque_grafica(
                    _svg_fc,
                    "Flujo de caja acumulado con beneficios Ley 1715 (escenario P50). "
                    "El punto naranja marca el año en que la inversión se recupera.")
        html += cierre()

    # ── 5b. Resumen de Costos del Presupuesto (#8) ────────────────────────────
    _inc_ppto     = st.session_state.get("rep_inc_presupuesto", False)
    _capex_ppto   = float(st.session_state.get("presupuesto_capex_usd", 0.0))
    _directo_ppto = float(st.session_state.get("presupuesto_capex_directo", 0.0))
    _blando_ppto  = float(st.session_state.get("presupuesto_capex_blando", 0.0))
    _opex_ppto    = float(st.session_state.get("presupuesto_opex_anual_usd", 0.0))
    _frac_eq_ppto = float(st.session_state.get("presupuesto_fraccion_equipos", 0.65))

    if _inc_ppto and _capex_ppto > 0:
        # USD/m² sobre el área útil de paneles (agrivoltaica), no el terreno bruto
        _area_pp       = float(st.session_state.get("area_util_m2")
                               or st.session_state.get("area_fachada_m2", 0) or 0)
        _potencia_pp   = float(st.session_state.get("P_stc_kW_sistema", 0) or 0)
        _tc_pp         = tipo_cambio_rep
        # Per-section subtotals (saved by Presupuesto page in cotización-real mode)
        _sub_pref      = float(st.session_state.get("presupuesto_sub_perfileria", 0.0))
        _sub_mo        = float(st.session_state.get("presupuesto_sub_mano_obra", 0.0))
        _sub_sfv       = float(st.session_state.get("presupuesto_sub_sistema_fv", 0.0))
        _sub_inv       = float(st.session_state.get("presupuesto_sub_inversor", 0.0))
        _sub_cat       = float(st.session_state.get("presupuesto_sub_catalogo", 0.0))
        _indirectos    = float(st.session_state.get("presupuesto_capex_indirectos", 0.0))
        _cont          = float(st.session_state.get("presupuesto_capex_cont", 0.0))
        _ind_pct       = float(st.session_state.get("presupuesto_ind_pct", 0.0))
        _cont_pct      = float(st.session_state.get("presupuesto_cont_pct", 0.0))
        _has_secciones = (_sub_pref + _sub_mo + _sub_sfv + _sub_inv + _sub_cat) > 50
        _capex_base    = _directo_ppto + _blando_ppto

        html += seccion("Presupuesto Detallado — CAPEX del Proyecto", "💼", "#1a5276")

        # ── Métricas resumen ──────────────────────────────────────────────────
        html += f"""
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px;">
          <div style="background:#eaf4fb;border-radius:8px;padding:12px 14px;text-align:center;">
            <div style="font-size:0.78em;color:#555;margin-bottom:4px;">CAPEX TOTAL</div>
            <div style="font-size:1.3em;font-weight:bold;color:#1a5276;">USD {_capex_ppto:,.0f}</div>
            <div style="font-size:0.8em;color:#888;">$ {_capex_ppto*_tc_pp/1e6:.2f} M COP</div>
          </div>
          {"" if _potencia_pp <= 0 else f'''
          <div style="background:#eaf4fb;border-radius:8px;padding:12px 14px;text-align:center;">
            <div style="font-size:0.78em;color:#555;margin-bottom:4px;">COSTO / Wp</div>
            <div style="font-size:1.3em;font-weight:bold;color:#1a5276;">USD {_capex_ppto/_potencia_pp/1000:.3f}</div>
            <div style="font-size:0.8em;color:#888;">Ref. BIPV: 0.85–4.50 USD/Wp</div>
          </div>'''}
          {"" if _area_pp <= 0 else f'''
          <div style="background:#eaf4fb;border-radius:8px;padding:12px 14px;text-align:center;">
            <div style="font-size:0.78em;color:#555;margin-bottom:4px;">COSTO / m²</div>
            <div style="font-size:1.3em;font-weight:bold;color:#1a5276;">USD {_capex_ppto/_area_pp:,.0f}</div>
            <div style="font-size:0.8em;color:#888;">Ref. BIPV: USD 180–350/m²</div>
          </div>'''}
          {"" if _opex_ppto <= 0 else f'''
          <div style="background:#e9f7ef;border-radius:8px;padding:12px 14px;text-align:center;">
            <div style="font-size:0.78em;color:#555;margin-bottom:4px;">OPEX ANUAL</div>
            <div style="font-size:1.3em;font-weight:bold;color:#1e8449;">USD {_opex_ppto:,.0f}</div>
            <div style="font-size:0.8em;color:#888;">$ {_opex_ppto*_tc_pp/1e6:.3f} M COP/año</div>
          </div>'''}
        </div>"""

        # ── Tabla desglose por sección (cotización real) ──────────────────────
        if _has_secciones:
            _capex_directo_secs = _sub_pref + _sub_mo + _sub_sfv + _sub_inv + _sub_cat
            html += f"""
            <p style="margin:14px 0 6px;font-weight:600;color:#1a5276;font-size:0.95em;">
                📋 Desglose por sección (cotización real)
            </p>
            <table style="width:100%;border-collapse:collapse;font-size:0.88em;margin-bottom:14px;">
            <thead><tr style="background:#1a5276;color:#fff;">
              <th style="padding:7px 10px;text-align:left;">Sección</th>
              <th style="padding:7px 10px;text-align:right;">USD</th>
              <th style="padding:7px 10px;text-align:right;">COP (M)</th>
              <th style="padding:7px 10px;text-align:right;">% CAPEX total</th>
            </tr></thead><tbody>"""
            _secs_data = [
                ("🔩 Perfilería y Estructura",           _sub_pref),
                ("👷 Mano de Obra y Servicios",          _sub_mo),
                ("⚡ Sistema FV (cables, protecciones)",  _sub_sfv),
                ("🔌 Inversor y Equipos Eléctricos",      _sub_inv),
                ("📦 Módulos + Inversor + Baterías (catálogo)", _sub_cat),
            ]
            for _ri, (_lbl, _val) in enumerate(_secs_data):
                if _val <= 0:
                    continue
                _bg = "#f8f9fa" if _ri % 2 == 0 else "white"
                html += f"""
                <tr style="background:{_bg};">
                  <td style="padding:6px 10px;">{_lbl}</td>
                  <td style="padding:6px 10px;text-align:right;font-weight:600;">{_val:,.0f}</td>
                  <td style="padding:6px 10px;text-align:right;color:#888;">{_val*_tc_pp/1e6:.2f}</td>
                  <td style="padding:6px 10px;text-align:right;color:#555;">{_val/_capex_ppto*100:.1f}%</td>
                </tr>"""
            # Subtotal directo
            html += f"""
                <tr style="background:#eaf4fb;font-weight:bold;">
                  <td style="padding:7px 10px;">Subtotal CAPEX directo</td>
                  <td style="padding:7px 10px;text-align:right;">{_capex_directo_secs:,.0f}</td>
                  <td style="padding:7px 10px;text-align:right;color:#888;">{_capex_directo_secs*_tc_pp/1e6:.2f}</td>
                  <td style="padding:7px 10px;text-align:right;">{_capex_directo_secs/_capex_ppto*100:.1f}%</td>
                </tr>"""
            # Costos blandos
            if _blando_ppto > 0:
                html += f"""
                <tr style="background:#f8f9fa;">
                  <td style="padding:6px 10px;">🧾 Costos Blandos (ingeniería, trámites, PM)</td>
                  <td style="padding:6px 10px;text-align:right;font-weight:600;">{_blando_ppto:,.0f}</td>
                  <td style="padding:6px 10px;text-align:right;color:#888;">{_blando_ppto*_tc_pp/1e6:.2f}</td>
                  <td style="padding:6px 10px;text-align:right;color:#555;">{_blando_ppto/_capex_ppto*100:.1f}%</td>
                </tr>"""
            # Costos indirectos
            if _indirectos > 0:
                html += f"""
                <tr style="background:white;">
                  <td style="padding:6px 10px;">⚙️ Costos Indirectos — AUI ({_ind_pct*100:.0f}%)</td>
                  <td style="padding:6px 10px;text-align:right;font-weight:600;">{_indirectos:,.0f}</td>
                  <td style="padding:6px 10px;text-align:right;color:#888;">{_indirectos*_tc_pp/1e6:.2f}</td>
                  <td style="padding:6px 10px;text-align:right;color:#555;">{_indirectos/_capex_ppto*100:.1f}%</td>
                </tr>"""
            # Contingencias
            if _cont > 0:
                html += f"""
                <tr style="background:#f8f9fa;">
                  <td style="padding:6px 10px;">🛡️ Contingencias ({_cont_pct*100:.0f}%)</td>
                  <td style="padding:6px 10px;text-align:right;font-weight:600;">{_cont:,.0f}</td>
                  <td style="padding:6px 10px;text-align:right;color:#888;">{_cont*_tc_pp/1e6:.2f}</td>
                  <td style="padding:6px 10px;text-align:right;color:#555;">{_cont/_capex_ppto*100:.1f}%</td>
                </tr>"""
            # CAPEX TOTAL
            html += f"""
                <tr style="background:#1a5276;color:white;font-weight:bold;">
                  <td style="padding:8px 10px;">✅ CAPEX TOTAL</td>
                  <td style="padding:8px 10px;text-align:right;">{_capex_ppto:,.0f}</td>
                  <td style="padding:8px 10px;text-align:right;">{_capex_ppto*_tc_pp/1e6:.2f}</td>
                  <td style="padding:8px 10px;text-align:right;">100.0%</td>
                </tr>
            </tbody></table>"""

        else:
            # Estimación rápida / sin desglose por sección
            _otros_ppto = max(0.0, _capex_ppto - _directo_ppto - _blando_ppto)
            html += tabla_kv([
                ("CAPEX directo (equipos + obra)",
                 f"USD {_directo_ppto:,.0f}",
                 f"$ {_directo_ppto*_tc_pp/1e6:.2f} M COP",
                 f"{_directo_ppto/_capex_ppto*100:.1f}% del CAPEX total — módulos, inversor, estructura, instalación"),
                ("Costos blandos (ingeniería + permisos)",
                 f"USD {_blando_ppto:,.0f}",
                 f"$ {_blando_ppto*_tc_pp/1e6:.2f} M COP",
                 f"{_blando_ppto/_capex_ppto*100:.1f}% del CAPEX — diseño, licencias, interventoría"),
                *([(
                    "Contingencias + imprevistos",
                    f"USD {_otros_ppto:,.0f}",
                    f"$ {_otros_ppto*_tc_pp/1e6:.2f} M COP",
                    f"{_otros_ppto/_capex_ppto*100:.1f}% del CAPEX"
                )] if _otros_ppto > 50 else []),
                ("CAPEX TOTAL",
                 f"USD {_capex_ppto:,.0f}",
                 f"$ {_capex_ppto*_tc_pp/1e6:.2f} M COP",
                 "Inversión inicial total del proyecto"),
            ])

        # ── Tabla KPIs + TRM ──────────────────────────────────────────────────
        html += tabla_kv([
            ("TRM aplicada",
             f"$ {_tc_pp:,.0f} COP/USD",
             "",
             "Tasa de cambio usada para conversiones COP ↔ USD en este reporte"),
            ("Fracción equipos (Ley 1715)",
             f"{_frac_eq_ppto*100:.1f}% del CAPEX",
             "",
             "Base para Art. 12 exclusión IVA · Art. 11 deducción renta · Art. 14 depreciación acelerada"),
            *([(
                "OPEX anual (O&M proyectado)",
                f"USD {_opex_ppto:,.0f}/año",
                f"$ {_opex_ppto*_tc_pp/1e6:.3f} M COP/año",
                f"{_opex_ppto/_capex_ppto*100:.2f}% del CAPEX anual — limpieza, revisión, seguros, monitoreo"
            )] if _opex_ppto > 0 else []),
        ])
        html += caja_nota(
            "CAPEX directo = módulos BIPV + inversor + estructura + instalación. "
            "Costos blandos = diseño técnico, trámites RETIE/UPME, interventoría, gastos bancables. "
            "Costos indirectos (AUI) = administración, utilidad e imprevistos del contratista. "
            "La <strong>fracción de equipos</strong> determina el monto base para los beneficios "
            "tributarios de la <strong>Ley 1715/2014</strong> (IVA, renta, depreciación acelerada).",
            color="#eaf4fb", borde="#1a5276", icono="ℹ️"
        )
        html += cierre()

    # ── 5c. Estimación Rápida — Fundamentación del Presupuesto ───────────────
    _inc_er_r    = st.session_state.get("rep_inc_est_rapida", False)
    _er_activa_r = st.session_state.get("est_rapida_aplicada", False)
    _er_cfg_r    = st.session_state.get("est_rapida_config", {})
    _er_cap_r    = float(st.session_state.get("presupuesto_capex_usd", 0.0))

    if _inc_er_r and _er_activa_r and _er_cfg_r and _er_cap_r > 0:
        _er_tipo_r  = _er_cfg_r.get("tipo", "—")
        _er_esc_r   = _er_cfg_r.get("escenario", "Base")
        _er_zona_r  = _er_cfg_r.get("zona", "—")
        _er_kwp_r   = float(_er_cfg_r.get("kwp", 0))
        _er_wp_r    = max(_er_kwp_r * 1000, 1)
        _er_dir_r   = float(st.session_state.get("presupuesto_capex_directo", 0))
        _er_bla_r   = float(st.session_state.get("presupuesto_capex_blando", 0))
        _er_cont_r  = max(0.0, _er_cap_r - _er_dir_r - _er_bla_r)
        _er_opex_r  = float(st.session_state.get("presupuesto_opex_anual_usd", 0))
        _er_feq_r   = float(st.session_state.get("presupuesto_fraccion_equipos", 0.65))
        _er_equip_r = _er_feq_r * _er_dir_r
        _er_epc_r   = max(0.0, _er_dir_r - _er_equip_r)
        _tc_er_r    = tipo_cambio_rep
        # Referencia USD/Wp ajustada por tipo Y escala del proyecto
        # Los costos fijos (permisos, scada, conexión) dominan en proyectos pequeños
        # y elevan el USD/Wp — es economía de escala normal, no un error del modelo.
        if "Granja" in _er_tipo_r:
            _ref_wp = "0.70–1.20 USD/Wp"
        elif "Techo" in _er_tipo_r:
            _ref_wp = "0.85–1.60 USD/Wp"
        else:  # BIPV fachada / pérgola: rango varía con escala (costos fijos)
            if _er_kwp_r < 50:
                _ref_wp = "1.20–4.50+ USD/Wp (costos fijos dominan a escala pequeña)"
            elif _er_kwp_r < 200:
                _ref_wp = "0.85–2.80 USD/Wp"
            else:
                _ref_wp = "0.75–2.00 USD/Wp"

        html += seccion(
            "Fundamentación del Presupuesto — Estimación Rápida Paramétrica",
            "🧮", "#1a5276"
        )
        html += f"""
        <div style="background:#eaf4fb;border-left:4px solid #2980b9;padding:13px 16px;
                    margin-bottom:18px;border-radius:0 4px 4px 0;font-size:0.93em;
                    line-height:1.55;">
            <strong>¿Por qué este presupuesto es técnicamente sólido?</strong><br>
            El CAPEX presentado fue estimado con benchmarks de mercado colombiano
            (UPME 2026, IRENA <em>Renewable Power Generation Costs 2023</em>, CCSE,
            datos de campo Urabá–Antioquia–Valle del Cauca) calibrados por
            <em>tipo de instalación</em>, <em>escenario económico</em> y
            <em>zona geográfica</em>.
            La metodología replica el análisis de <em>Prefactibilidad Etapa 1</em>
            según la guía DNDE del Ministerio de Minas y Energía de Colombia.<br><br>
            <strong>Precisión declarada: ±25–35 %</strong> sobre el valor de
            cotización EPC formal — suficiente para establecer la viabilidad del
            proyecto, comparar entre oportunidades y estructurar los escenarios
            financieros presentados en este informe.
            Los beneficios Ley 1715/2014 ya están calculados sobre esta base de CAPEX.
        </div>"""

        html += tabla_kv([
            ("Configuración aplicada",
             f"{_er_tipo_r}  ·  {_er_esc_r}",
             _er_zona_r,
             f"{_er_kwp_r:.1f} kWp · benchmarks julio 2026"),
            ("🔩 Equipos (módulos, inversores, estructura, cableado, SCADA)",
             f"USD {_er_equip_r:,.0f}",
             f"$ {_er_equip_r*_tc_er_r/1e6:.2f} M COP",
             f"{_er_equip_r/_er_cap_r*100:.1f}% del CAPEX total"),
            ("🏗️ Construcción y EPC (obra civil, montaje, instalación eléctrica)",
             f"USD {_er_epc_r:,.0f}",
             f"$ {_er_epc_r*_tc_er_r/1e6:.2f} M COP",
             f"{_er_epc_r/_er_cap_r*100:.1f}% del CAPEX total"),
            ("🧾 Costos blandos (ingeniería, RETIE/UPME, PM, conexión a red)",
             f"USD {_er_bla_r:,.0f}",
             f"$ {_er_bla_r*_tc_er_r/1e6:.2f} M COP",
             f"{_er_bla_r/_er_cap_r*100:.1f}% del CAPEX total"),
            ("⚙️ Contingencias y reservas de ejecución",
             f"USD {_er_cont_r:,.0f}",
             f"$ {_er_cont_r*_tc_er_r/1e6:.2f} M COP",
             f"{_er_cont_r/_er_cap_r*100:.1f}% del CAPEX total"),
            ("✅ CAPEX TOTAL",
             f"USD {_er_cap_r:,.0f}",
             f"$ {_er_cap_r*_tc_er_r/1e6:.2f} M COP",
             f"{_er_cap_r/_er_wp_r:.3f} USD/Wp · Referencia {_er_tipo_r}: {_ref_wp}"),
            *([(
                "OPEX anual proyectado a 25 años",
                f"USD {_er_opex_r:,.0f}/año",
                f"$ {_er_opex_r*_tc_er_r/1e6:.2f} M COP/año",
                f"{_er_opex_r/_er_cap_r*100:.2f}% CAPEX/año — O&M, limpieza, "
                "seguros, monitoreo, fondo reposición inversor"
            )] if _er_opex_r > 0 else []),
        ], nota=(
            "Fuente: benchmarks UPME / IRENA 2026 calibrados para Colombia. "
            "La fracción de equipos determina la base de los beneficios tributarios "
            "Ley 1715/2014 (Art. 11 deducción renta, Art. 12 exclusión IVA, "
            "Art. 14 depreciación acelerada). "
            "Para bancabilidad formal, reemplazar con cotización EPC firmada "
            "con fuente y vigencia de precios."
        ))

        html += f"""
        <div style="margin-top:16px;padding:14px 16px;background:#fffde7;
                    border:1px solid #f9a825;border-radius:6px;">
            <strong style="font-size:0.94em;color:#5d4037;">
                📊 Rango de escenarios — misma instalación · {_er_zona_r}
            </strong>
            <table style="width:100%;border-collapse:collapse;margin-top:10px;
                          font-size:0.90em;">
                <tr style="background:#f9a825;color:white;">
                    <th style="padding:6px 10px;text-align:left;">Escenario</th>
                    <th style="padding:6px 10px;text-align:right;">CAPEX / Wp</th>
                    <th style="padding:6px 10px;text-align:left;">Descripción</th>
                </tr>
                <tr style="background:#e8f5e9;">
                    <td style="padding:5px 10px;font-weight:bold;color:#2e7d32;">
                        Optimista</td>
                    <td style="padding:5px 10px;text-align:right;">
                        Extremo inferior del rango</td>
                    <td style="padding:5px 10px;color:#555;">
                        Proveedores negociados, acceso fácil, sin imprevistos de obra</td>
                </tr>
                <tr style="background:#e3f2fd;">
                    <td style="padding:5px 10px;font-weight:bold;color:#1565c0;">
                        ⭐ {_er_esc_r} — <em>este reporte</em></td>
                    <td style="padding:5px 10px;text-align:right;font-weight:bold;">
                        {_er_cap_r/_er_wp_r:.3f} USD/Wp</td>
                    <td style="padding:5px 10px;color:#555;">
                        Mediana del mercado colombiano julio 2026</td>
                </tr>
                <tr style="background:#fce4ec;">
                    <td style="padding:5px 10px;font-weight:bold;color:#b71c1c;">
                        Conservador</td>
                    <td style="padding:5px 10px;text-align:right;">
                        Extremo superior del rango</td>
                    <td style="padding:5px 10px;color:#555;">
                        Zona remota, alta contingencia, contratista sin experiencia BIPV</td>
                </tr>
            </table>
            <p style="margin:8px 0 0;font-size:0.83em;color:#777;font-style:italic;">
                El análisis financiero (TIR / VPN / Payback) usa el escenario
                <strong>{_er_esc_r}</strong>.
                Para due diligence bancario formal, solicitar cotización EPC
                firmada con fuente y vigencia de precios.
            </p>
        </div>"""
        html += cierre()

    # ── 6. Balance Energético y Clasificación ────────────────────────────────
    balance_ok = st.session_state.get("balance_ok", False)
    metr_bal   = st.session_state.get("balance_metricas", {})
    clase_e    = st.session_state.get("clasificacion_energetica", {})
    bal_df     = st.session_state.get("balance_mensual_df")
    incluir_bal = st.session_state.get("rep_inc_balance", balance_ok)

    if balance_ok and incluir_bal and metr_bal and clase_e:
        clase_letra = clase_e.get("clase", "—")
        clase_desc  = clase_e.get("descripcion", "—")
        frac        = metr_bal.get("fraccion_solar_pct", 0)
        e_sol       = metr_bal.get("E_solar_anual_kWh", 0)
        e_cons      = metr_bal.get("E_consumo_anual_kWh", 0)
        e_ac_total  = metr_bal.get("E_autoconsumo_anual_kWh", 0)
        e_exp       = metr_bal.get("E_exportacion_anual_kWh", 0)
        e_def       = metr_bal.get("E_deficit_anual_kWh", 0)
        e_bat       = metr_bal.get("E_bateria_total_kWh", 0)
        ac_rate     = metr_bal.get("tasa_autoconsumo_pct", 0)
        ratio       = metr_bal.get("ratio_solar_consumo", 0)
        bat_nom     = st.session_state.get("bateria_nombre", "—")
        bat_dim     = st.session_state.get("bateria_dim", {})

        color_clase = clase_e.get("color_hex", "#27ae60")

        html += seccion("Balance Energético y Clasificación del Edificio", "🔋")

        # Insignia de clasificación
        html += f"""
        <div style="display:flex;align-items:center;gap:24px;margin-bottom:20px;
                    border:2px solid {color_clase};border-radius:12px;padding:16px;
                    background:{color_clase}15;">
            <div style="font-size:64px;font-weight:900;color:{color_clase};
                        min-width:80px;text-align:center;">{clase_letra}</div>
            <div>
                <div style="font-size:18px;font-weight:700;color:{color_clase};">
                    Clase Energética {clase_letra} — {clase_desc}
                </div>
                <div style="font-size:14px;color:#555;margin-top:4px;">
                    Fracción solar: <strong>{frac:.1f}%</strong> del consumo anual cubierto
                    por generación fotovoltaica (autoconsumo directo{' + batería' if e_bat > 0 else ''})
                </div>
                <div style="font-size:12px;color:#888;margin-top:4px;">
                    Criterio: A+ ≥ 90% · A 75–89% · B 50–74% · C 25–49% · D &lt; 25%
                </div>
            </div>
        </div>"""

        html += tabla_kv([
            ("Producción solar anual (E_ac)",      _fmt(e_sol,    0), "kWh/año", "Energía AC entregada por el sistema BIPV"),
            ("Consumo edificio anual",              _fmt(e_cons,   0), "kWh/año", "Demanda eléctrica total del edificio"),
            ("Autoconsumo solar directo",           _fmt(e_ac_total - e_bat, 0), "kWh/año", "Solar consumida en tiempo real sin pasar por batería"),
        ] + ([
            ("Energía aportada por batería",        _fmt(e_bat,    0), "kWh/año", f"{bat_dim.get('N_baterias','—')} und. {bat_nom} — descarga nocturna/pico"),
        ] if e_bat > 0 else []) + [
            ("Autoconsumo total (directo + bat.)",  _fmt(e_ac_total, 0), "kWh/año", "kWh del sol que evitan comprar a la red"),
            ("Excedente exportado a red",           _fmt(e_exp,    0), "kWh/año", "Solar no consumida ni almacenada → red / facturación excedentes"),
            ("Déficit residual (de la red)",        _fmt(e_def,    0), "kWh/año", "Energía que aún debe comprarse a la distribuidora"),
            ("Fracción solar (autosuficiencia)",    _fmt(frac,     1), "%",        "% del consumo cubierto por solar — base de la clasificación"),
            ("Tasa de autoconsumo solar",            _fmt(ac_rate,  1), "%",        "% de la producción solar que se consume en el edificio"),
            ("Ratio producción/consumo",             _fmt(ratio,    2), "x",        "Solar generada ÷ consumo total"),
        ],
        nota="La clasificación energética A+/A/B/C/D mide la autosuficiencia del edificio "
             "frente a su demanda real. Una clase A+ significa que el sistema BIPV cubre el 90% "
             "o más del consumo sin depender de la red. El autoconsumo directo es energía solar "
             "usada instantáneamente; la batería captura el excedente para uso diferido (nocturno). "
             "Los proyectos con clase B o superior tienen payback acelerado por menor dependencia tarifaria.")
        html += cierre()

    # ── 7. Huella de Carbono Evitada ─────────────────────────────────────────
    incluir_co2_rep = st.session_state.get("rep_inc_co2", False)
    if co2_ok and incluir_co2_rep and co2_total_t > 0:
        COLOR_VERDE_CO2  = "#1e8449"
        COLOR_AZUL_CO2   = "#1a5276"
        COLOR_TIERRA     = "#784212"

        html += seccion("Huella de Carbono Evitada — Impacto Ambiental Real", "🌿", COLOR_VERDE_CO2)

        # Banner de impacto persuasivo
        html += f"""
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;
                    margin-bottom:20px;">
            <div style="background:linear-gradient(135deg,{COLOR_VERDE_CO2},{COLOR_VERDE_CO2}cc);
                        color:white;border-radius:10px;padding:16px;text-align:center;">
                <div style="font-size:2.2em;font-weight:900;">{co2_anual_t:.1f}</div>
                <div style="font-size:0.85em;opacity:0.9;">tCO₂ evitadas / año</div>
                <div style="font-size:0.72em;opacity:0.75;margin-top:4px;">año 1 de operación</div>
            </div>
            <div style="background:linear-gradient(135deg,#145a32,{COLOR_VERDE_CO2});
                        color:white;border-radius:10px;padding:16px;text-align:center;">
                <div style="font-size:2.2em;font-weight:900;">{co2_total_t:,.0f}</div>
                <div style="font-size:0.85em;opacity:0.9;">tCO₂ totales en 25 años</div>
                <div style="font-size:0.72em;opacity:0.75;margin-top:4px;">vida útil del sistema</div>
            </div>
            <div style="background:linear-gradient(135deg,#1a5276,#2e86c1);
                        color:white;border-radius:10px;padding:16px;text-align:center;">
                <div style="font-size:2.2em;font-weight:900;">{co2_arboles:,.0f}</div>
                <div style="font-size:0.85em;opacity:0.9;">árboles equivalentes</div>
                <div style="font-size:0.72em;opacity:0.75;margin-top:4px;">IDEAM 22 kg CO₂/árbol/año</div>
            </div>
            <div style="background:linear-gradient(135deg,#784212,#b7770d);
                        color:white;border-radius:10px;padding:16px;text-align:center;">
                <div style="font-size:2.2em;font-weight:900;">USD {co2_bonos_usd:,.0f}</div>
                <div style="font-size:0.85em;opacity:0.9;">valor en bonos carbono</div>
                <div style="font-size:0.72em;opacity:0.75;margin-top:4px;">a USD {co2_precio_bono:.0f}/tCO₂ · VCS</div>
            </div>
        </div>"""

        html += tabla_kv([
            ("Metodología",
             co2_metodologia,
             "",
             "GHG Protocol Scope 2 (inventario corporativo) · CDM AMS-I.D (bonos de carbono)"),
            ("Factor de emisión SIN Colombia",
             f"{co2_factor_usado*1000:.1f} gCO₂/kWh  ({co2_factor_usado:.3f} kg/kWh)",
             "",
             f"Fuente: {co2_factor_fecha} — Sistema Interconectado Nacional"),
            ("CO₂ evitado — año 1",
             f"{co2_anual_t:.2f} tCO₂/año",
             "",
             "Equivale a sacar un vehículo de circulación durante 1 año completo"),
            ("CO₂ evitado — 25 años (factor promedio SIN)",
             f"{co2_prom_t:,.1f} tCO₂",
             "",
             f"Factor 0.126 kg/kWh — GHG Protocol · Ley 1931/2018 · RETC"),
            ("CO₂ evitado — 25 años (factor marginal CDM)",
             f"{co2_marg_t:,.1f} tCO₂",
             "",
             "Factor 0.300 kg/kWh — UNFCCC Tool 07 — base para créditos VCS/Gold Standard"),
            ("Árboles nativos colombianos equivalentes",
             f"{co2_arboles:,.0f} árboles",
             "permanentes",
             "Bosque Húmedo Tropical · IDEAM 2010 · 22 kgCO₂/árbol/año"),
            ("Hogares colombianos abastecidos",
             f"{co2_hogares:,.1f} hogares",
             "× 1 año",
             f"o {co2_hogares/25:.1f} hogares durante 25 años · UPME 2022 · 130 kWh/mes"),
            ("Km en vehículo a gasolina",
             f"{co2_km:,.0f} mil km",
             "no recorridos",
             "IDEAM FECOC 2022 · 0.162 kgCO₂/km · equivale a múltiples vueltas al país"),
            ("Valor en bonos de carbono (VCS)",
             f"USD {co2_bonos_usd:,.0f}",
             f"({co2_total_t:,.1f} t × USD {co2_precio_bono:.0f}/t)",
             "Mercado voluntario Verra VCS · referencia 2024 · sujeto a verificación"),
        ])

        # P90 financial note
        if fin_p90 and factor_p90_pct > 0:
            tir_p90 = fin_p90.get("tir_pct")
            vpn_p90 = fin_p90.get("vpn_usd", 0)
            html += caja_nota(
                f"<strong>🏦 Sensibilidad P90 confirmada:</strong> incluso con producción "
                f"{factor_p90_pct:.0f}% menor al P50 (escenario conservador exigido por bancos), "
                f"el proyecto evita <strong>{co2_total_t*(1-factor_p90_pct/100):,.1f} tCO₂</strong> en 25 años "
                + (f"· TIR P90 = <strong>{tir_p90:.1f}%</strong> · VPN P90 = USD <strong>{vpn_p90:,.0f}</strong>"
                   if tir_p90 else ""),
                color="#e8f5e9", borde=COLOR_VERDE_CO2, icono="🏦"
            )

        # CO₂ real vs proyectado (si existe)
        if co2_real_ok and co2_real_t > 0:
            html += caja_nota(
                f"<strong>📡 Seguimiento en tiempo real:</strong> producción mensual ingresada → "
                f"CO₂ real acumulado = <strong>{co2_real_t:.2f} tCO₂</strong> · "
                f"Cumplimiento vs proyectado: <strong>{co2_cumpl_pct:.1f}%</strong>.",
                color="#e3f2fd", borde="#1565c0", icono="📡"
            )

        # Marco regulatorio compacto
        html += f"""
        <div style="margin-top:14px;padding:12px 16px;background:#f0f9f4;
                    border:1px solid #a9dfbf;border-radius:6px;font-size:0.86em;">
            <strong>📜 Marco regulatorio aplicado:</strong>
            <span style="color:#555;">
            GHG Protocol Corporate Standard (Scope 2 · Location-based) ·
            ISO 14064-1:2018 · UNFCCC CDM AMS-I.D · IPCC AR6 WG III ·
            Ley 1931/2018 (gestión cambio climático Colombia) ·
            NDC Colombia 2030 (meta 51% reducción GEI) ·
            UPME Resolución 520/2019 (factor SIN oficial).
            </span>
        </div>"""

        html += caja_nota(
            "<strong>Este proyecto no es solo una inversión financiera — es una declaración de liderazgo climático.</strong> "
            "Cada kWh generado por la fachada BIPV desplaza energía de una red que aún depende de combustibles fósiles "
            "en épocas de sequía. Al instalar este sistema, la organización puede reportar emisiones evitadas ante el "
            "RETC, acreditar ante la ANLA y posicionarse como empresa carbono-comprometida frente a clientes, "
            "inversionistas y entidades financiadoras.",
            color="#fef9e7", borde="#f39c12", icono="💡"
        )
        html += cierre()

    # ── Pie de página ─────────────────────────────────────────────────────────
    html += f"""
    <div style="margin-top:32px;border-top:1px solid {COLOR_BORDE};padding-top:16px;
                color:#aaa;font-size:0.82em;display:flex;justify-content:space-between;">
        <span>Calculadora BIPV Colombia v2026 · Motor SDM De Soto 2006 + pvlib + PVGIS</span>
        <span>Generado: {fecha_hoy} · {nombre_empresa}</span>
    </div>
    <div style="margin-top:8px;font-size:0.78em;color:#bbb;">
        Los resultados son estimaciones técnicas basadas en datos climáticos históricos (TMY).
        La producción real puede variar ±10–15% por condiciones locales no modeladas.
        Este documento no constituye garantía de desempeño.
    </div>

</div><!-- fin contenedor -->
</body>
</html>"""

    return html


# ── Botón de generación ────────────────────────────────────────────────────────
# #174 — misma guardia TRM que la cotización (#171): no generar un reporte al
# cliente con TRM en cero o sin confirmar (API caída → "valor por defecto").
# La página ofrece su propio widget TRM cuando está sin confirmar, para no
# obligar a navegar a Presupuesto/Financiero solo para desbloquear (auditoría).
from calculos.trm_utils import init_trm, trm_widget, trm_confirmada as _trm_confirmada, trm_error_msg as _trm_error_msg
init_trm()   # garantiza tipo_cambio en session_state aunque sea la primera página visitada
_trm_ok_rep, _tc_rep, _ = _trm_confirmada()
if not _trm_ok_rep:
    st.error(_trm_error_msg(_tc_rep))
    trm_widget("rep")   # 🔄 refrescar, editar o ✔️ confirmar aquí mismo
    _trm_ok_rep, _tc_rep, _ = _trm_confirmada()   # re-evaluar en el mismo rerun

# ── 🔒 Ledger de Auditoría — sellar este resultado al generar el reporte ──────
# Res. CREG 174/2021 Art. 6 exige trazabilidad de los cálculos. Sellar es
# opcional y explícito -- no cada corrida de prueba, solo la que se entrega.
from calculos import ledger_auditoria as _ledger

_sellar_rep = st.checkbox(
    "🔒 Sellar este resultado en el Ledger de Auditoría",
    value=True, key="chk_sellar_reporte",
    help="Registra un eslabón con hash encadenado (insumos + resultados de este "
         "reporte) en el Ledger de Auditoría del proyecto -- verificable después "
         "en 🔒 Ledger de Auditoría. No modifica ni bloquea la generación del reporte.",
)
_tipo_sello_rep = st.selectbox(
    "Tipo de resultado",
    options=["presupuesto_bancable", "presupuesto_informativo"],
    format_func=lambda k: _ledger.TIPO_LABELS.get(k, k),
    key="sel_tipo_sello_reporte", disabled=not _sellar_rep,
)
_nota_sello_rep = st.text_input(
    "Nota (opcional)", key="nota_sello_reporte", disabled=not _sellar_rep,
    placeholder="Ej.: Versión final entregada al cliente",
)

if st.button("📄 Generar Reporte", type="primary", use_container_width=True,
             key="btn_generar", disabled=not _trm_ok_rep,
             help="La TRM debe estar confirmada antes de generar el reporte."
                  if not _trm_ok_rep else None):
    with st.spinner("Generando reporte…"):
        html_str = generar_html_reporte()

    if _sellar_rep:
        _usr_rep = st.session_state.get("auth_email", "")
        _eslabon_rep = _ledger.sellar_resultado(
            nombre_proyecto, _usr_rep, _tipo_sello_rep,
            _ledger.construir_snapshot_insumos(st.session_state),
            _ledger.construir_snapshot_resultados(st.session_state),
            nota=_nota_sello_rep,
        ) if _usr_rep else {}
        if _eslabon_rep:
            _id_corto = _eslabon_rep["hash_propio"][:16]
            _pie_ledger = (
                '<div style="margin-top:2em;padding:0.8em;border-top:2px solid #ccc;'
                'font-size:0.8em;color:#555;">🔒 ID de verificación del Ledger de '
                f'Auditoría: <code>{_id_corto}</code> — sellado {_eslabon_rep["timestamp"]} '
                f'({_ledger.TIPO_LABELS.get(_tipo_sello_rep, _tipo_sello_rep)}) — '
                'verificable en la página 🔒 Ledger de Auditoría del proyecto.</div>'
            )
            html_str = (html_str.replace("</body>", _pie_ledger + "</body>")
                        if "</body>" in html_str else html_str + _pie_ledger)
            st.success(f"🔒 Resultado sellado en el Ledger — ID {_id_corto}")
        else:
            st.warning(
                "⚠️ No se pudo sellar en el Ledger de Auditoría (revisa que haya "
                "sesión activa, permisos/espacio en el servidor) — el reporte se "
                "generó igual, sin ID de verificación."
            )

    html_bytes = html_str.encode("utf-8")
    st.session_state["reporte_generado"] = True  # lo lee el 🧭 Asistente

    st.download_button(
        label="⬇️ Descargar reporte (.html → imprimir como PDF)",
        data=html_bytes,
        file_name=f"Reporte_BIPV_{st.session_state.get('nombre_proyecto','proyecto').replace(' ','_')}.html",
        mime="text/html",
        use_container_width=True,
        key="btn_download",
    )
    st.success(
        "✅ Reporte generado. Haz clic en **Descargar** para guardarlo. "
        "Para obtener un PDF: abre el archivo en tu navegador y usa **Archivo → Imprimir → Guardar como PDF**."
    )

st.markdown("---")
st.markdown("""
### ℹ️ Instrucciones para obtener el PDF

1. **Haz clic en "Generar Reporte"** para crear el archivo HTML con todos tus resultados.
2. **Descarga el archivo .html** usando el botón que aparece.
3. **Abre el archivo** en Chrome, Edge o Firefox.
4. Presiona **Ctrl+P** (Windows) o **⌘+P** (Mac) para abrir el diálogo de impresión.
5. Selecciona **"Guardar como PDF"** como destino de impresión.
6. Ajusta márgenes y escala si es necesario → **Guardar**.

> 💡 El reporte está diseñado para impresión en formato A4 con márgenes normales.
> En Chrome, elige "Sin márgenes" o "Mínimo" para aprovechar mejor el espacio.
""")

with st.expander("📋 Vista previa del reporte (HTML en pantalla)", expanded=False):
    if not recurso_ok:
        st.info("Ejecuta al menos ☀️ Recurso Solar para previsualizar el reporte.")
    else:
        html_preview = generar_html_reporte()
        st.components.v1.html(html_preview, height=800, scrolling=True)
