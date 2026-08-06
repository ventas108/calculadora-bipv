# -*- coding: utf-8 -*-
"""
Genera la Ficha Técnica comercial de la Calculadora BIPV.
Salida: entregables/FICHA_TECNICA_CALCULADORA_BIPV_agosto2026.docx
Ejecutar:  python3 scripts/generar_ficha_tecnica.py
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = "entregables/FICHA_TECNICA_CALCULADORA_BIPV_agosto2026.docx"

C_VERDE_OSC = RGBColor(0x1B, 0x5E, 0x20)
C_VERDE_CLR = RGBColor(0xE8, 0xF5, 0xE9)
C_AZUL      = RGBColor(0x0D, 0x47, 0xA1)
C_AZUL_CLR  = RGBColor(0xE3, 0xF2, 0xFD)
C_NARANJA   = RGBColor(0xE6, 0x51, 0x00)
C_GRIS      = RGBColor(0x37, 0x47, 0x4F)
C_GRIS_CLR  = RGBColor(0xEC, 0xEF, 0xF1)
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)

doc = Document()
for s in doc.sections:
    s.top_margin = s.bottom_margin = Cm(1.6)
    s.left_margin = s.right_margin = Cm(1.8)

st = doc.styles["Normal"]
st.font.name = "Calibri"; st.font.size = Pt(10.5)

def hexs(rgb): return f"{int(rgb[0]):02X}{int(rgb[1]):02X}{int(rgb[2]):02X}"

def cell_bg(cell, rgb):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexs(rgb))
    cell._tc.get_or_add_tcPr().append(shd)

def para(text="", size=10.5, bold=False, color=None, align=None, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    if align: p.alignment = align
    r = p.add_run(text)
    r.font.size = Pt(size); r.bold = bold
    if color: r.font.color.rgb = color
    return p

def h(text, color=C_AZUL, size=13):
    para(text, size=size, bold=True, color=color, space_after=4)

def box(text, bg, fg, bold_first=None):
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]; cell_bg(c, bg)
    p = c.paragraphs[0]
    if bold_first:
        r = p.add_run(bold_first + " "); r.bold = True; r.font.color.rgb = fg; r.font.size = Pt(10.5)
    r = p.add_run(text); r.font.color.rgb = fg; r.font.size = Pt(10.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def tabla(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, htxt in enumerate(headers):
        c = t.rows[0].cells[j]; cell_bg(c, C_VERDE_OSC)
        r = c.paragraphs[0].add_run(htxt); r.bold = True
        r.font.color.rgb = WHITE; r.font.size = Pt(10)
    for i, row in enumerate(rows):
        cells = t.add_row().cells
        for j, val in enumerate(row):
            if i % 2 == 1: cell_bg(cells[j], C_VERDE_CLR)
            r = cells[j].paragraphs[0].add_run(val); r.font.size = Pt(9.5)
            if j == 0: r.bold = True
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t

# ══ Portada / encabezado ═══════════════════════════════════════════════════
para("FICHA TÉCNICA", size=22, bold=True, color=C_VERDE_OSC,
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0)
para("Calculadora BIPV — Simulación fotovoltaica integrada en edificios y agrivoltaica",
     size=13, bold=True, color=C_GRIS, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0)
para("Innovación Química  ·  calc.innovacionquimica.com.co  ·  Versión agosto 2026",
     size=9.5, color=C_GRIS, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

box("La única herramienta en Colombia que simula fachadas BIPV, cubiertas, pérgolas y "
    "granjas agrivoltaicas con física de nivel bancable: 8 760 horas de simulación real, "
    "curva IV completa del panel, sombras con diodos de bypass y análisis financiero en "
    "COP con TRM en línea. No es una regla de tres: es un laboratorio solar.",
    C_AZUL_CLR, C_AZUL, "¿Por qué es diferente?")

# ══ 1. Motores de cálculo ═════════════════════════════════════════════════
h("1. Motores de cálculo — el corazón de la herramienta")

para("☀️ Recurso solar hora a hora (8 760 h/año)", bold=True, color=C_VERDE_OSC, space_after=2)
para("Consume archivos climáticos TMY/EPW reales de la ubicación y calcula la irradiancia "
     "en el plano exacto de instalación (POA) con el modelo de transposición Hay-Davies, "
     "incluyendo heatmap horario y diagrama de trayectoria solar. Para sistemas bifaciales "
     "y agrivoltaicos aplica el modelo infinite_sheds (pvlib), que captura la luz que llega "
     "a la cara trasera del panel según la separación real entre filas (GCR).")

para("⚡ Motor IV — curva corriente-voltaje real del panel", bold=True, color=C_VERDE_OSC, space_after=2)
para("Mientras otras herramientas multiplican Wp × horas de sol, la Calculadora resuelve el "
     "modelo de diodo único del panel en cada condición de irradiancia y temperatura: Voc, "
     "Isc, punto de máxima potencia y coeficientes térmicos reales de la ficha técnica. "
     "Se activa automáticamente cuando el panel tiene ficha completa e incluye defensa "
     "contra el error más común del mercado: el conteo de celdas en paneles half-cut "
     "(verificación Ns ≈ Voc/0.74).")

para("🌗 Sombras con diodos de bypass — el diferencial técnico", bold=True, color=C_VERDE_OSC, space_after=2)
para("En BIPV urbano la sombra parcial es la regla, no la excepción. El motor de mismatch "
     "simula el comportamiento eléctrico real del string bajo sombra: qué diodos de bypass "
     "se activan, cuánta potencia se recupera y cuánta se pierde de verdad — no un "
     "descuento porcentual arbitrario. Se alimenta de la Calculadora de Sombreado 3D "
     "(factor de sombra horario por punto de análisis).")

para("🔬 Motor Óptico BIPV", bold=True, color=C_VERDE_OSC, space_after=2)
para("Pérdidas que solo existen en integración arquitectónica y que las herramientas "
     "genéricas ignoran: reflexión por ángulo de incidencia (IAM), suciedad (soiling) y "
     "el efecto térmico del confinamiento en fachada, donde el panel opera más caliente "
     "que en un rack ventilado.")

para("🌱 Agrivoltaica — cultivo y energía en el mismo terreno", bold=True, color=C_VERDE_OSC, space_after=2)
para("Factor de ocupación configurable (5–100%): la herramienta dimensiona paneles, "
     "presupuesto y USD/m² sobre el área útil, sincroniza la separación entre filas (GCR) "
     "con ese factor y lo muestra en una Vista 3D con las filas elevadas a 3 m sobre el "
     "cultivo. Diseñada y validada con proyectos reales de cultivo bajo paneles en Colombia.")

# ══ 2. Cadena de simulación ═══════════════════════════════════════════════
h("2. Cadena de simulación completa")
tabla(["Etapa", "Modelo / método", "Lo que garantiza"],
[
 ("Recurso solar", "TMY/EPW + Hay-Davies + infinite_sheds (pvlib)", "Irradiancia real del sitio, no promedios nacionales"),
 ("Óptica BIPV", "IAM + soiling + térmica confinada", "Pérdidas de fachada que otros ignoran"),
 ("Eléctrica", "Diodo único (curva IV) + mismatch con bypass", "Producción creíble bajo sombra parcial"),
 ("Dimensionamiento", "Emparejamiento automático panel-inversor (catálogo Growatt/Deye)", "Ventanas MPPT y ratios DC/AC verificados"),
 ("Producción", "8 760 h con PR resultante, no asumido", "E_ac anual defendible ante un banco"),
 ("Baterías", "Balance horario consumo vs generación", "Autoconsumo y respaldo con catálogo real"),
 ("Financiero", "Flujo de caja en COP, TRM en línea, precio real del inversor", "TIR, VPN, payback y LCOE bancables"),
 ("Entregables", "Presupuesto bancable + Reporte PDF automático", "Documento listo para cliente y banco"),
])

box("El PR (performance ratio) no se asume: se obtiene. La cadena óptica-eléctrica-térmica "
    "produce el PR como resultado físico del sitio y la tecnología — el número que un "
    "evaluador técnico puede auditar capa por capa.",
    C_VERDE_CLR, C_VERDE_OSC, "🎯 Argumento clave:")

# ══ 3. Catálogos inteligentes ═════════════════════════════════════════════
h("3. Catálogos inteligentes — cero digitación manual")
para("Los catálogos de paneles, inversores y baterías se alimentan directamente desde la "
     "ficha técnica PDF del fabricante: un extractor con banco de regresión de 84 casos "
     "reales lee Voc, Isc, coeficientes térmicos, número de celdas, bifacialidad y "
     "ventanas MPPT, y un validador físico rechaza valores imposibles antes de que "
     "contaminen la simulación. Soporta fichas multi-modelo (un PDF, varios equipos).")

# ══ 4. Especificaciones ═══════════════════════════════════════════════════
h("4. Especificaciones generales")
tabla(["Característica", "Detalle"],
[
 ("Tipos de instalación", "Fachada BIPV, techo inclinado, techo plano, pérgola, marquesina, granja fotovoltaica/agrivoltaica"),
 ("Resolución temporal", "Horaria — 8 760 horas por año típico meteorológico"),
 ("Multi-superficie", "Combina fachada + techo + pérgola en un solo sistema (Vista 3D)"),
 ("Moneda y mercado", "COP con TRM en línea; costos de referencia del mercado colombiano"),
 ("Entregables", "Reporte PDF ejecutivo, presupuesto bancable, cotización exportable"),
 ("Acceso", "Aplicación web — sin instalación (calc.innovacionquimica.com.co)"),
 ("Base científica", "pvlib (estándar de la industria fotovoltaica, NREL) + modelos propios BIPV"),
])

box("Ideal para: desarrolladores inmobiliarios, arquitectos, EPCs, evaluadores de banca "
    "verde y proyectos agrivoltaicos que necesitan cifras defendibles — no promesas.",
    C_GRIS_CLR, C_GRIS, "👥")

para("Ficha técnica — agosto de 2026 · Innovación Química",
     size=8.5, color=C_GRIS, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0)

doc.save(OUT)
print("OK —", OUT)
