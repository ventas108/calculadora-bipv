"""
generador_reporte.py
====================
Genera un reporte técnico PDF de un proyecto BIPV a partir de los datos
de session_state de Streamlit.

Dependencias: fpdf2 >= 2.7
"""
from __future__ import annotations

import io
from datetime import date
from typing import Any

from fpdf import FPDF, XPos, YPos


# --- Paleta de colores ---------------------------------------------------------
VERDE_OSCURO  = (30, 100, 50)    # títulos de sección
VERDE_CLARO   = (220, 240, 225)  # fondo alternado de filas
GRIS_OSCURO   = (60, 60, 60)     # texto principal
GRIS_MEDIO    = (120, 120, 120)  # texto secundario / notas
AZUL_OSCURO   = (20, 60, 100)    # encabezado superior
BLANCO        = (255, 255, 255)
NEGRO         = (0, 0, 0)
AMARILLO_LEY  = (255, 248, 220)  # fondo tabla Ley 1715


# --- Clase principal -----------------------------------------------------------

class ReporteBIPV(FPDF):
    """FPDF subclaseada con encabezado y pie de página corporativos."""

    def __init__(self, nombre_proyecto: str = "Proyecto BIPV"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.nombre_proyecto = nombre_proyecto
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(left=18, top=28, right=18)

    # -- Encabezado --------------------------------------------------------------
    def header(self):
        # Barra superior
        self.set_fill_color(*AZUL_OSCURO)
        self.rect(0, 0, 210, 16, style="F")

        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*BLANCO)
        self.set_xy(10, 4)
        self.cell(100, 7, "CALCULADORA BIPV - Reporte Técnico", new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font("Helvetica", "", 8)
        self.set_xy(130, 4)
        self.cell(70, 7, f"{self.nombre_proyecto}", align="R",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_text_color(*NEGRO)
        self.ln(2)

    # -- Pie de página -----------------------------------------------------------
    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*GRIS_MEDIO)
        self.cell(0, 5,
                  "Generado por Calculadora BIPV · Los resultados son estimativos y no "
                  "reemplazan una ingeniería de detalle certificada.",
                  align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(0, 4, f"Página {self.page_no()}", align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*NEGRO)

    # -- Helpers visuales -------------------------------------------------------
    def titulo_seccion(self, texto: str):
        """Barra de título de sección con fondo verde oscuro."""
        self.set_fill_color(*VERDE_OSCURO)
        self.set_text_color(*BLANCO)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 8, f"  {texto}", fill=True,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*NEGRO)
        self.ln(1)

    def fila_kv(self, clave: str, valor: str, fila_par: bool = False):
        """Fila clave-valor con fondo alternado."""
        if fila_par:
            self.set_fill_color(*VERDE_CLARO)
        else:
            self.set_fill_color(*BLANCO)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*GRIS_OSCURO)
        ancho_total = 174
        self.cell(70, 6, f"  {clave}", fill=True,
                  border="B", new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font("Helvetica", "B", 9)
        self.cell(ancho_total - 70, 6, valor, fill=True,
                  border="B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*NEGRO)

    def fila_tabla(self, cols: list[tuple[str, float]], fila_par: bool = False,
                   bold: bool = False, bg: tuple | None = None):
        """Fila genérica para tablas con N columnas [(texto, ancho), ...]."""
        fill_color = bg or (VERDE_CLARO if fila_par else BLANCO)
        self.set_fill_color(*fill_color)
        style = "B" if bold else ""
        self.set_font("Helvetica", style, 8)
        self.set_text_color(*GRIS_OSCURO)
        for texto, ancho in cols:
            self.cell(ancho, 6, str(texto), fill=True,
                      border="B", new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.ln(6)
        self.set_text_color(*NEGRO)

    def encabezado_tabla(self, cols: list[tuple[str, float]]):
        """Encabezado de tabla con fondo verde oscuro."""
        self.set_fill_color(*VERDE_OSCURO)
        self.set_text_color(*BLANCO)
        self.set_font("Helvetica", "B", 8)
        for texto, ancho in cols:
            self.cell(ancho, 7, f" {texto}", fill=True,
                      border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.ln(7)
        self.set_text_color(*NEGRO)

    def nota(self, texto: str):
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(*GRIS_MEDIO)
        self.multi_cell(0, 5, texto, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*NEGRO)
        self.ln(1)


# --- Función pública -----------------------------------------------------------

def generar_pdf(ss: dict[str, Any]) -> bytes:
    """
    Genera el reporte PDF y devuelve los bytes del archivo.

    Parameters
    ----------
    ss : dict
        Copia de st.session_state (o un dict equivalente) con todas las claves
        almacenadas por las páginas de la calculadora.

    Returns
    -------
    bytes
        Contenido del PDF listo para `st.download_button`.
    """
    # -- Leer datos disponibles -------------------------------------------------
    nombre  = ss.get("nombre_proyecto", "Proyecto BIPV")
    ciudad  = ss.get("tmy_ciudad") or ss.get("ciudad", "-")
    area    = ss.get("area_fachada_m2", 0.0)
    poa_b   = ss.get("poa_anual_kWh_m2", 0.0)
    poa_ef  = ss.get("poa_efectiva_kWh_m2", poa_b)
    alt_m   = ss.get("alt_m", "-")
    t_media = ss.get("t_media_anual", None)

    panel_nombre   = ss.get("panel_nombre_final", "-")
    n_paneles      = ss.get("N_paneles_final", ss.get("N_paneles_dim", 0))
    p_stc_kw       = ss.get("P_stc_kW_sistema", ss.get("P_dc_stc_kW_dim", 0.0))
    eta_inv        = ss.get("eta_inversor", None)

    e_ac            = ss.get("E_ac_anual_kWh", 0.0)
    e_dc            = ss.get("E_dc_anual_kWh", 0.0)
    pr              = ss.get("PR_sistema", None)
    yf              = ss.get("Y_f_kWh_kWp", None)
    res             = ss.get("res_produccion", {})
    cf_pct          = res.get("CF_pct", None)
    yr              = res.get("Y_r", None)
    df_mensual      = res.get("df_mensual", None)

    fin_ok          = ss.get("financiero_ok", False)
    capex           = ss.get("capex_total_usd", 0.0)
    ben             = ss.get("ben_1715", {})
    met             = ss.get("metricas_financiero", {})
    tarifa_cop      = ss.get("tarifa_cop_kWh", 0.0)
    tipo_cambio     = float(ss.get("tipo_cambio", 4200.0))

    # -- Inicializar PDF --------------------------------------------------------
    pdf = ReporteBIPV(nombre_proyecto=nombre)
    pdf.add_page()

    # -- Portada / título -------------------------------------------------------
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*VERDE_OSCURO)
    pdf.ln(2)
    pdf.cell(0, 12, "Reporte Técnico - Sistema BIPV", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*GRIS_OSCURO)
    pdf.cell(0, 7, nombre, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS_MEDIO)
    pdf.cell(0, 6, f"Generado el {date.today().strftime('%d de %B de %Y')}",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*NEGRO)
    pdf.ln(4)

    # -------------------------------------------------------------------------
    # SECCIÓN 1 - DATOS DEL PROYECTO
    # -------------------------------------------------------------------------
    pdf.titulo_seccion("1. Datos del Proyecto")

    filas_proyecto = [
        ("Ciudad / ubicación",        ciudad),
        ("Altitud",                   f"{alt_m} m s.n.m." if alt_m != "-" else "-"),
        ("T° ambiente media anual",   f"{t_media:.1f} °C" if t_media is not None else "-"),
        ("Área de fachada disponible",f"{area:,.1f} m²"),
        ("POA bruta (TMY)",           f"{poa_b:,.0f} kWh/m²/año"),
        ("POA efectiva (con mismatch)",f"{poa_ef:,.0f} kWh/m²/año"),
    ]
    for i, (k, v) in enumerate(filas_proyecto):
        pdf.fila_kv(k, v, fila_par=(i % 2 == 0))
    pdf.ln(4)

    # -------------------------------------------------------------------------
    # SECCIÓN 2 - CONFIGURACIÓN DEL SISTEMA
    # -------------------------------------------------------------------------
    pdf.titulo_seccion("2. Configuración del Sistema Fotovoltaico")

    area_modulos = n_paneles * _panel_area(panel_nombre)
    eta_str = f"{eta_inv*100:.1f}%" if eta_inv is not None else "-"

    filas_sistema = [
        ("Módulo BIPV",               panel_nombre),
        ("Número de módulos",         str(int(n_paneles))),
        ("Área total de módulos",     f"{area_modulos:.1f} m²"),
        ("Potencia instalada (STC)",  f"{p_stc_kw:.3f} kWp"),
        ("Eficiencia del inversor",   eta_str),
    ]
    for i, (k, v) in enumerate(filas_sistema):
        pdf.fila_kv(k, v, fila_par=(i % 2 == 0))
    pdf.ln(4)

    # -------------------------------------------------------------------------
    # SECCIÓN 3 - RESULTADOS DE PRODUCCIÓN (IEC 61724)
    # -------------------------------------------------------------------------
    pdf.titulo_seccion("3. Producción Anual - IEC 61724")

    pr_str  = f"{pr*100:.1f}%" if pr is not None else "-"
    yf_str  = f"{yf:,.0f} kWh/kWp" if yf is not None else "-"
    yr_str  = f"{yr:,.0f} h" if yr is not None else "-"
    cf_str  = f"{cf_pct:.1f}%" if cf_pct is not None else "-"

    filas_prod = [
        ("Energía AC anual (E_ac)",   f"{e_ac:,.0f} kWh/año"),
        ("Energía DC anual (E_dc)",   f"{e_dc:,.0f} kWh/año"),
        ("Performance Ratio (PR)",    pr_str),
        ("Final Yield (Y_f)",         yf_str),
        ("Reference Yield (Y_r)",     yr_str),
        ("Factor de Planta (CF)",      cf_str),
    ]
    for i, (k, v) in enumerate(filas_prod):
        pdf.fila_kv(k, v, fila_par=(i % 2 == 0))
    pdf.ln(2)

    # Tabla mensual si disponible
    if df_mensual is not None and not df_mensual.empty:
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*VERDE_OSCURO)
        pdf.cell(0, 6, "  Producción mensual (kWh)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*NEGRO)

        meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        col_w = 174 / (len(meses) + 1)
        pdf.encabezado_tabla([("Mes", col_w)] + [(m, col_w) for m in meses])

        row_eac = [("E_ac (kWh)", col_w)]
        row_edc = [("E_dc (kWh)", col_w)]
        for mes in meses:
            if mes in df_mensual.index:
                row_eac.append((f"{df_mensual.loc[mes,'E_ac (kWh)']:,.0f}", col_w))
                row_edc.append((f"{df_mensual.loc[mes,'E_dc (kWh)']:,.0f}", col_w))
            else:
                row_eac.append(("-", col_w))
                row_edc.append(("-", col_w))

        pdf.fila_tabla(row_eac, fila_par=False)
        pdf.fila_tabla(row_edc, fila_par=True)
        pdf.ln(2)

    pdf.nota(
        "Motor SDM De Soto 2006 · Temperatura NOCT · Datos TMY hora a hora. "
        "PR > 100% es válido para climas fríos de alta altitud (IEC 61724-1:2017)."
    )
    pdf.ln(2)

    # -------------------------------------------------------------------------
    # SECCIÓN 4 - INDICADORES FINANCIEROS (solo si financiero_ok)
    # -------------------------------------------------------------------------
    if fin_ok and met:
        pdf.titulo_seccion("4. Análisis Financiero - Ley 1715 de 2014")

        capex_neto = ben.get("capex_neto_usd", capex)
        tir    = met.get("tir_pct", None)
        vpn    = met.get("vpn_usd", None)
        pb     = met.get("payback_simple", None)
        lcoe   = met.get("lcoe_cop_kWh", None)

        tir_str  = f"{tir:.1f}%" if tir is not None else "-"
        vpn_str  = (f"USD {vpn:,.0f}  /  $ {vpn*tipo_cambio/1e6:.2f} M COP"
                    if vpn is not None else "-")
        pb_str   = f"{pb:.1f} años" if pb is not None else "-"
        lcoe_str = f"{lcoe:,.0f} COP/kWh" if lcoe is not None else "-"
        tarifa_str = f"{tarifa_cop:,.0f} COP/kWh"

        filas_fin = [
            ("CAPEX total",            f"USD {capex:,.0f}  /  $ {capex*tipo_cambio/1e6:.2f} M COP"),
            ("CAPEX neto (con Ley 1715)", f"USD {capex_neto:,.0f}  /  $ {capex_neto*tipo_cambio/1e6:.2f} M COP"),
            ("TIR (Tasa Interna de Retorno)", tir_str),
            ("VPN (Valor Presente Neto)",     vpn_str),
            ("Payback simple",               pb_str),
            ("LCOE",                         lcoe_str),
            ("Tarifa de referencia",          tarifa_str),
        ]
        for i, (k, v) in enumerate(filas_fin):
            pdf.fila_kv(k, v, fila_par=(i % 2 == 0))
        pdf.ln(3)

        # Sub-tabla Ley 1715
        if ben:
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_text_color(*VERDE_OSCURO)
            pdf.cell(0, 6, "  Beneficios Ley 1715 de 2014", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(*NEGRO)

            w = [70, 52, 52]
            pdf.encabezado_tabla([
                ("Artículo / Beneficio", w[0]),
                ("Valor (USD)", w[1]),
                ("Valor (M COP)", w[2]),
            ])

            ben_rows = [
                ("Art. 11 - Deducción renta",
                 f"{ben.get('ahorro_renta_usd', 0):,.0f}",
                 f"$ {ben.get('ahorro_renta_usd', 0)*tipo_cambio/1e6:.2f}"),
                ("Art. 12 - Exclusión IVA",
                 f"{ben.get('ahorro_iva_usd', 0):,.0f}",
                 f"$ {ben.get('ahorro_iva_usd', 0)*tipo_cambio/1e6:.2f}"),
                ("Art. 14 - Dep. acelerada (VPN)",
                 f"{ben.get('ahorro_dep_vpn_usd', 0):,.0f}",
                 f"$ {ben.get('ahorro_dep_vpn_usd', 0)*tipo_cambio/1e6:.2f}"),
                ("Total Ley 1715",
                 f"{ben.get('total_usd', 0):,.0f}",
                 f"$ {ben.get('total_usd', 0)*tipo_cambio/1e6:.2f}"),
            ]
            for i, row in enumerate(ben_rows):
                bold = (i == len(ben_rows) - 1)
                bg   = AMARILLO_LEY if bold else None
                pdf.fila_tabla(
                    [(row[0], w[0]), (row[1], w[1]), (row[2], w[2])],
                    fila_par=(i % 2 == 0),
                    bold=bold,
                    bg=bg,
                )
            pdf.ln(2)

        pdf.nota(
            "TIR y VPN calculados sobre flujo de caja proyectado 25 años con degradación anual "
            "y O&M. Los beneficios Ley 1715 (Art. 11 y 14) requieren renta gravable suficiente "
            "y certificación UPME previa. LCOE calculado en COP corrientes."
        )

    # -------------------------------------------------------------------------
    # SECCIÓN 5 - RESUMEN EJECUTIVO
    # -------------------------------------------------------------------------
    pdf.titulo_seccion("5. Resumen Ejecutivo")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS_OSCURO)

    lineas = [
        f"El proyecto \"{nombre}\" contempla la instalación de un sistema BIPV de "
        f"{p_stc_kw:.2f} kWp ({int(n_paneles)} módulos {panel_nombre}) "
        f"en {ciudad}.",

        f"La simulación hora a hora (Motor SDM De Soto 2006) sobre datos TMY estima "
        f"una producción anual de {e_ac:,.0f} kWh/año (E_ac), "
        f"equivalente a un Final Yield de {yf:,.0f} kWh/kWp "
        f"y un Performance Ratio de {pr*100:.1f}%."
        if (yf is not None and pr is not None) else
        f"La producción AC anual estimada es {e_ac:,.0f} kWh/año.",
    ]

    if fin_ok and met:
        tir_v  = met.get("tir_pct", 0)
        vpn_v  = met.get("vpn_usd", 0)
        pb_v   = met.get("payback_simple", 0)
        lcoe_v = met.get("lcoe_cop_kWh", 0)
        signo  = ">" if (tir_v or 0) > 0 else "<"
        lineas.append(
            f"El análisis financiero arroja una TIR de {tir_v:.1f}%, "
            f"VPN de USD {vpn_v:,.0f}, payback de {pb_v:.1f} años y "
            f"LCOE de {lcoe_v:,.0f} COP/kWh "
            f"({'menor' if lcoe_v < tarifa_cop else 'mayor'} a la tarifa de referencia "
            f"de {tarifa_cop:,.0f} COP/kWh)."
        )
        cap_neto = ben.get("capex_neto_usd", capex)
        lineas.append(
            f"Los incentivos de la Ley 1715 de 2014 reducen el CAPEX de "
            f"USD {capex:,.0f} a USD {cap_neto:,.0f} neto."
        )

    for linea in lineas:
        pdf.multi_cell(0, 5.5, linea, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)

    pdf.set_text_color(*NEGRO)

    # -- Serializar a bytes -----------------------------------------------------
    buf = io.BytesIO()
    pdf_bytes = pdf.output()
    return bytes(pdf_bytes)


# --- Helpers internos ---------------------------------------------------------

def _panel_area(panel_nombre: str) -> float:
    """Devuelve el área unitaria del módulo (m²). Fallback 0.72 m²."""
    try:
        from datos.tecnologias_bipv import MODULOS_BIPV
        return MODULOS_BIPV.get(panel_nombre, {}).get("area_m2", 0.72)
    except Exception:
        return 0.72


def nombre_archivo(ss: dict[str, Any]) -> str:
    """Sugiere un nombre de archivo para el PDF descargado."""
    nombre  = ss.get("nombre_proyecto", "BIPV").replace(" ", "_")
    ciudad  = (ss.get("tmy_ciudad") or ss.get("ciudad", "ciudad")).replace(" ", "_")
    hoy     = date.today().strftime("%Y%m%d")
    return f"Reporte_BIPV_{nombre}_{ciudad}_{hoy}.pdf"
