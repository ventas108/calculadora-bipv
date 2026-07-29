"""
Página 10 — Reporte Técnico PDF / HTML
Genera un reporte descargable con todos los resultados del proyecto.
Incluye notas explicativas en cada sección para comprensión del usuario.
"""
import streamlit as st
import datetime

st.set_page_config(page_title="Reporte PDF — BIPV", page_icon="📄", layout="wide")
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

st.markdown("### Estado del proyecto")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🏠 Proyecto",       "✅" if proyecto_ok  else "⬜")
c2.metric("☀️ Recurso Solar",  "✅" if recurso_ok   else "⬜")
c3.metric("🔆 Motor Óptico",   "✅" if motor_optico else "⬜")
c4.metric("📊 Producción",     "✅" if produccion_ok else "⬜")
c5.metric("💰 Financiero",     "✅" if financiero_ok else "⬜")

if not recurso_ok:
    st.warning("⚠️ Ejecuta al menos ☀️ Recurso Solar para generar un reporte útil.")

st.markdown("---")

# ── Opciones del reporte ───────────────────────────────────────────────────────
st.subheader("⚙️ Opciones del reporte")
col_op1, col_op2 = st.columns(2)
with col_op1:
    nombre_empresa = st.text_input(
        "Nombre de la empresa",
        value=st.session_state.get("nombre_empresa", "Innovación Química / SolTech Energy"),
        key="rep_empresa",
    )
    nombre_proyecto = st.text_input(
        "Nombre del proyecto",
        value=st.session_state.get("nombre_proyecto", "Proyecto BIPV"),
        key="rep_proyecto",
    )
with col_op2:
    incluir_motor   = st.checkbox("Incluir sección Motor Óptico",  value=motor_optico,   key="rep_inc_motor")
    incluir_dim     = st.checkbox("Incluir sección Dimensionamiento", value=dimensionam_ok, key="rep_inc_dim")
    incluir_prod    = st.checkbox("Incluir sección Producción",    value=produccion_ok,  key="rep_inc_prod")
    incluir_fin     = st.checkbox("Incluir sección Financiero",    value=financiero_ok,  key="rep_inc_fin")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN GENERADORA DE HTML
# ══════════════════════════════════════════════════════════════════════════════

def _fmt(val, decimals=1, suffix="", fallback="—"):
    try:
        return f"{float(val):,.{decimals}f}{suffix}"
    except Exception:
        return fallback


def generar_html_reporte() -> str:
    # Colectar datos de session_state
    ciudad          = st.session_state.get("tmy_ciudad", st.session_state.get("ciudad", "—"))
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

    # Financiero
    fin          = st.session_state.get("metricas_financiero", {})
    ben          = st.session_state.get("ben_1715", {})
    capex        = st.session_state.get("capex_total_usd", "—")
    tarifa       = st.session_state.get("tarifa_cop_kWh", st.session_state.get("tarifa_cop_kwh", 850))

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
      <h1>{nombre_empresa}</h1>
      <div style="font-size:1.15em;font-weight:bold;color:{COLOR_TEXTO};">
        REPORTE TÉCNICO — SISTEMA BIPV
        <span class="badge badge-borrador">BORRADOR</span>
      </div>
      <div style="color:#888;margin-top:4px;font-size:0.92em;">
        Versión 2026 · Generado el {fecha_hoy} · Calculadora BIPV Colombia
      </div>
    </div>
    <div style="text-align:right;color:{COLOR_PRIMARIO};font-size:1.8em;line-height:1;">☀️</div>
  </div>

  <div class="aviso-borrador">
    ⚠️ <strong>BORRADOR:</strong> Este reporte es preliminar y fue generado automáticamente
    por la Calculadora BIPV Colombia. Verifique los datos de entrada antes de presentarlo al cliente.
  </div>
"""

    # ── 1. Resumen del Proyecto ───────────────────────────────────────────────
    html += seccion("Información General del Proyecto", "🏠")
    html += tabla_kv([
        ("Nombre del proyecto",  nombre_proyecto,          "",         ""),
        ("Ciudad / Localización", ciudad,                   "",         "Clima extraído de base TMY/PVGIS"),
        ("Área de fachada",      _fmt(area_m2, 1),         "m²",       "Superficie total disponible para BIPV"),
        ("Orientación",          str(orientacion),          "",         "Azimut de la fachada"),
        ("Inclinación (tilt)",   str(tilt),                "°",        "90° = fachada vertical típica"),
        ("Panel seleccionado",   panel_nombre,              "",         "Módulo BIPV"),
        ("N° de módulos",        str(n_paneles),            "módulos",  "Resultado de Dimensionamiento"),
        ("Potencia instalada",   _fmt(p_stc_kw, 2),        "kWp",      "Potencia pico DC en STC"),
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
        html += cierre()

    # ── 3. Motor Óptico ───────────────────────────────────────────────────────
    if motor_optico and incluir_motor and mo_sum:
        b0       = mo_sum.get("b0",    "—")
        k_bipv   = mo_sum.get("k_bipv","—")
        noct     = mo_sum.get("noct",  "—")
        coef_t   = mo_sum.get("coef_temp", 0) * 100
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

        html += tabla_kv([
            ("Parámetros usados", "", "", ""),
            ("— Tipo de vidrio (b₀ ASHRAE)",  _fmt(b0, 3),   "",       "Reflexión del vidrio a ángulos oblicuos"),
            ("— Montaje / confinamiento (k_BIPV)", str(k_bipv),       "",  "1.0 ventilado · 1.3 confinado · 1.5 sellado"),
            ("— NOCT",            _fmt(noct, 0),  "°C",      "Temperatura nominal de operación"),
            ("— Coef. temperatura γ",  _fmt(coef_t, 2), "%/°C",  "Caída de eficiencia por temperatura"),
        ])

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
        html += cierre()

    # ── 5. Financiero ─────────────────────────────────────────────────────────
    if financiero_ok and incluir_fin and fin:
        vpn        = fin.get("vpn_usd", 0)
        tir        = fin.get("tir_pct")
        payback    = fin.get("payback_simple")
        lcoe_cop   = fin.get("lcoe_cop_kWh", 0)
        capex_n    = ben.get("capex_neto_usd", capex) if ben else capex
        des_1715   = ben.get("descuento_ica_pct", 0) if ben else 0

        html += seccion("Análisis Financiero — Ley 1715 / 2014", "💰")
        html += tabla_kv([
            ("CAPEX total (bruto)",   _fmt(capex,    0),  "USD",      "Costo total del sistema instalado"),
            ("CAPEX neto (Ley 1715)", _fmt(capex_n,  0),  "USD",      "Después de beneficios tributarios"),
            ("Descuento ICA / IVA",   _fmt(des_1715, 1),  "%",        "Beneficio Ley 1715 de 2014 Colombia"),
            ("Tarifa de referencia",  _fmt(tarifa,   0),  "COP/kWh",  "Precio de energía del contrato o tarifa pública"),
            ("VPN (20 años)",         _fmt(vpn,      0),  "USD",      "Valor Presente Neto del proyecto"),
            ("TIR",                   _fmt(tir,      1) if tir else "N/A",   "%", "Tasa Interna de Retorno"),
            ("Payback simple",        _fmt(payback,  1) if payback else "> horizonte", "años", "Período de recuperación de la inversión"),
            ("LCOE",                  _fmt(lcoe_cop, 0),  "COP/kWh",  "Costo nivelado de la energía generada"),
        ],
        nota="VPN > 0 y TIR > WACC (costo del capital) indican proyecto viable. "
             "LCOE < tarifa de red indica que generar es más barato que comprar. "
             "Los beneficios de la Ley 1715/2014 incluyen: deducción del 50% del IVA en equipos, "
             "exención de aranceles, y depreciación acelerada.")
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
if st.button("📄 Generar Reporte", type="primary", use_container_width=True, key="btn_generar"):
    with st.spinner("Generando reporte…"):
        html_bytes = generar_html_reporte().encode("utf-8")

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
