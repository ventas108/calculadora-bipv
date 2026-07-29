"""
Genera Catalogo_Baterias_BIPV_Maestro.xlsx con todos los modelos de batería
industrial identificados hasta ahora:
  - BR172R/186R/200R/215R  (fabricante pendiente confirmar)
  - ATESS ESS: BC/BR45T/50T/60T, BC/BR75T/100T, BR138T/145T,
               BR114R/129R/143R/157R, BC55RPB (6-11 módulos)

Nota: TODOS son sistemas de alta tensión (300-870V) — incompatibles con
inversores 48V residenciales. Requieren inversores HV comerciales/industriales.

Uso: python3 scripts/generar_catalogo_baterias_maestro.py
"""
import zipfile, io, os

# ── Helpers XML ────────────────────────────────────────────────────────────
def _esc(v):
    return (str(v)
            .replace("&","&amp;").replace("<","&lt;")
            .replace(">","&gt;").replace('"',"&quot;"))

def _cell(col, row, value, sid=0):
    cr = f"{col}{row}"
    if value == "" or value is None:
        return f'<c r="{cr}" s="{sid}"/>'
    if isinstance(value, (int, float)):
        return f'<c r="{cr}" t="n" s="{sid}"><v>{value}</v></c>'
    return (f'<c r="{cr}" t="inlineStr" s="{sid}">'
            f'<is><t xml:space="preserve">{_esc(str(value))}</t></is></c>')

COLS = list("ABCDEFGHIJKLMNOPQRSTU")

def kw(kwh, c=0.5):
    return round(kwh * c, 2)

# ── Definición de columnas ─────────────────────────────────────────────────
# (nombre, color: V=verde/obligatorio, N=naranja/importante, G=gris/opcional)
HEADERS = [
    ("Modelo",                    "V"),
    ("Fabricante",                "N"),
    ("Datos completos\n(Si/No)",  "V"),
    ("Tecnología",                "V"),
    ("Capacidad\n(kWh)",          "V"),
    ("DoD\n(%)",                  "V"),
    ("Eficiencia RTE\n(%)",       "V"),
    ("Ciclos de Vida",            "V"),
    ("Potencia Continua\n(kW)",   "V"),
    ("Potencia Pico\n(kW)",       "N"),
    ("Voltaje Nominal\n(V)",      "N"),
    ("Voltaje Mín\n(V)",          "N"),
    ("Voltaje Máx\n(V)",          "N"),
    ("Temperatura Mín\n(°C)",     "G"),
    ("Temperatura Máx\n(°C)",     "G"),
    ("Peso\n(kg)",                "G"),
    ("IP",                        "G"),
    ("Montaje",                   "G"),
    ("Garantía\n(años)",          "N"),
    ("Costo\n(USD)",              "N"),
    ("Notas",                     "G"),
]

def bat(modelo, fab, kwh, vnom, vmin, vmax, config, ip, montaje,
        peso="", notas=""):
    """Crea fila con datos comunes calculados automáticamente."""
    return {
        "Modelo":           modelo,
        "Fabricante":       fab,
        "Datos completos":  "No",      # faltan DoD, RTE, garantía, temperatura
        "Tecnología":       "LiFePO4",
        "Capacidad (kWh)":  kwh,
        "DoD (%)":          "",        # no especificado en ficha
        "Eficiencia RTE (%)": "",      # no especificado en ficha
        "Ciclos de Vida":   6000,
        "Potencia Continua (kW)": kw(kwh, 0.5),
        "Potencia Pico (kW)":     kw(kwh, 1.0),
        "Voltaje Nominal (V)":    vnom,
        "Voltaje Mín (V)":        vmin,
        "Voltaje Máx (V)":        vmax,
        "Temperatura Mín (°C)":   "",
        "Temperatura Máx (°C)":   "",
        "Peso (kg)":        peso,
        "IP":               ip,
        "Montaje":          montaje,
        "Garantía (años)":  "",
        "Costo (USD)":      "",
        "Notas":            notas,
    }

HV = "ALTA TENSIÓN — requiere inversor HV comercial/industrial (NO compatible con 48V)."

BATERIAS = [
    # ── Fabricante pendiente (fichas anteriores) ───────────────────────────
    bat("BR172R", "Pendiente confirmar", 172.032, 614.4, 537.6, 691.2,
        "16S1P·12 mód.", "IP20", "Rack interior", 1511,
        f"{HV} 12×14.336 kWh. BMS CAN. Pantalla 7\"."),
    bat("BR186R", "Pendiente confirmar", 186.368, 665.6, 582.4, 748.8,
        "16S1P·13 mód.", "IP20", "Rack interior", 1624,
        f"{HV} 13×14.336 kWh. BMS CAN."),
    bat("BR200R", "Pendiente confirmar", 200.704, 716.8, 627.2, 806.4,
        "16S1P·14 mód.", "IP20", "Rack interior", 1737,
        f"{HV} 14×14.336 kWh. BMS CAN."),
    bat("BR215R", "Pendiente confirmar", 215.040, 768.0, 672.0, 864.0,
        "16S1P·15 mód.", "IP20", "Rack interior", 1850,
        f"{HV} 15×14.336 kWh. BMS CAN."),

    # ── ATESS ESS — Serie BC/BR45T-60T (24S1P, 7.68 kWh/mód) ────────────
    bat("BC45T", "ATESS ESS", 46.08, 460.8, 403.2, 525.6,
        "24S1P·6 mód.", "IP54", "Gabinete exterior", 716,
        f"{HV} 6×7.68 kWh. Variante interior: BR45T. Certif. CE/UL/IEC62619."),
    bat("BR45T", "ATESS ESS", 46.08, 460.8, 403.2, 525.6,
        "24S1P·6 mód.", "IP20", "Rack interior", 539,
        f"{HV} 6×7.68 kWh. Variante exterior IP54: BC45T. Certif. CE/UL/IEC62619."),
    bat("BC50T", "ATESS ESS", 53.76, 537.6, 470.4, 613.2,
        "24S1P·7 mód.", "IP54", "Gabinete exterior", 792,
        f"{HV} 7×7.68 kWh. Variante interior: BR50T."),
    bat("BR50T", "ATESS ESS", 53.76, 537.6, 470.4, 613.2,
        "24S1P·7 mód.", "IP20", "Rack interior", 615,
        f"{HV} 7×7.68 kWh. Variante exterior IP54: BC50T."),
    bat("BC60T", "ATESS ESS", 61.44, 614.4, 537.6, 700.8,
        "24S1P·8 mód.", "IP54", "Gabinete exterior", 868,
        f"{HV} 8×7.68 kWh. Variante interior: BR60T."),
    bat("BR60T", "ATESS ESS", 61.44, 614.4, 537.6, 700.8,
        "24S1P·8 mód.", "IP20", "Rack interior", 691,
        f"{HV} 8×7.68 kWh. Variante exterior IP54: BC60T."),

    # ── ATESS ESS — Serie BC/BR75T-145T (12S2P, 7.68 kWh/mód) ───────────
    bat("BC75T", "ATESS ESS", 76.8, 384.0, 336.0, 438.0,
        "12S2P·10 mód.", "IP54", "Gabinete exterior", 1130,
        f"{HV} 10×7.68 kWh. Variante interior: BR75T."),
    bat("BR75T", "ATESS ESS", 76.8, 384.0, 336.0, 438.0,
        "12S2P·10 mód.", "IP20", "Rack interior", 877,
        f"{HV} 10×7.68 kWh. Variante exterior IP54: BC75T."),
    bat("BC100T", "ATESS ESS", 107.52, 537.6, 470.4, 613.2,
        "12S2P·14 mód.", "IP54", "Gabinete exterior", 1436,
        f"{HV} 14×7.68 kWh. Variante interior: BR100T."),
    bat("BR100T", "ATESS ESS", 107.52, 537.6, 470.4, 613.2,
        "12S2P·14 mód.", "IP20", "Rack interior", 1183,
        f"{HV} 14×7.68 kWh. Variante exterior IP54: BC100T."),
    bat("BR138T", "ATESS ESS", 138.24, 691.2, 604.8, 766.8,
        "12S2P·18 mód.", "IP20", "Rack interior", 1547,
        f"{HV} 18×7.68 kWh. Solo interior."),
    bat("BR145T", "ATESS ESS", 145.92, 729.6, 638.4, 832.2,
        "12S2P·19 mód.", "IP20", "Rack interior", 1624,
        f"{HV} 19×7.68 kWh. Solo interior."),

    # ── ATESS ESS — Serie BR114R-157R (16S1P, 14.336 kWh/mód) ───────────
    bat("BR114R", "ATESS ESS", 114.688, 409.6, 358.4, 460.8,
        "16S1P·8 mód.", "IP20", "Rack interior", 1064,
        f"{HV} 8×14.336 kWh. 166 Wh/kg. BMS CAN+RS485."),
    bat("BR129R", "ATESS ESS", 129.024, 460.8, 403.2, 518.4,
        "16S1P·9 mód.", "IP20", "Rack interior", 1157,
        f"{HV} 9×14.336 kWh. 166 Wh/kg. BMS CAN+RS485."),
    bat("BR143R", "ATESS ESS", 143.36, 512.0, 448.0, 576.0,
        "16S1P·10 mód.", "IP20", "Rack interior", 1270,
        f"{HV} 10×14.336 kWh. 166 Wh/kg. BMS CAN+RS485."),
    bat("BR157R", "ATESS ESS", 157.696, 563.2, 492.8, 633.6,
        "16S1P·11 mód.", "IP20", "Rack interior", 1383,
        f"{HV} 11×14.336 kWh. 166 Wh/kg. BMS CAN+RS485."),

    # ── ATESS ESS — BC55RPB (16S1P, 5.12 kWh/mód, IP54 exterior) ────────
    bat("BC55RPB-6M", "ATESS ESS", 30.72, 307.2, 268.8, 345.6,
        "16S1P·6 mód.", "IP54", "Gabinete exterior", 474,
        f"{HV} 6×5.12 kWh. 100Ah/mód. Equilibrado activo opcional."),
    bat("BC55RPB-7M", "ATESS ESS", 35.84, 358.4, 313.6, 403.2,
        "16S1P·7 mód.", "IP54", "Gabinete exterior", 518,
        f"{HV} 7×5.12 kWh."),
    bat("BC55RPB-8M", "ATESS ESS", 40.96, 409.6, 358.4, 460.8,
        "16S1P·8 mód.", "IP54", "Gabinete exterior", 562,
        f"{HV} 8×5.12 kWh."),
    bat("BC55RPB-9M", "ATESS ESS", 46.08, 460.8, 403.2, 518.4,
        "16S1P·9 mód.", "IP54", "Gabinete exterior", 606,
        f"{HV} 9×5.12 kWh."),
    bat("BC55RPB-10M", "ATESS ESS", 51.2,  512.0, 448.0, 576.0,
        "16S1P·10 mód.", "IP54", "Gabinete exterior", 650,
        f"{HV} 10×5.12 kWh."),
    bat("BC55RPB-11M", "ATESS ESS", 56.32, 563.2, 492.8, 642.4,
        "16S1P·11 mód.", "IP54", "Gabinete exterior", 694,
        f"{HV} 11×5.12 kWh."),
]

# Orden de claves para escribir celdas
KEY_ORDER = [
    "Modelo","Fabricante","Datos completos","Tecnología",
    "Capacidad (kWh)","DoD (%)","Eficiencia RTE (%)","Ciclos de Vida",
    "Potencia Continua (kW)","Potencia Pico (kW)",
    "Voltaje Nominal (V)","Voltaje Mín (V)","Voltaje Máx (V)",
    "Temperatura Mín (°C)","Temperatura Máx (°C)",
    "Peso (kg)","IP","Montaje","Garantía (años)","Costo (USD)","Notas",
]
NUM_CI = {4,5,6,7,8,9,10,11,12,15,19}  # índices 0-based con valores numéricos

# ── Styles XML ─────────────────────────────────────────────────────────────
STYLES_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="4">
    <font><sz val="9"/><name val="Calibri"/></font>
    <font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
    <font><b/><sz val="9"/><name val="Calibri"/></font>
    <font><b/><sz val="9"/><color rgb="FFB71C1C"/><name val="Calibri"/></font>
  </fonts>
  <fills count="10">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF1B5E20"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFE65100"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF37474F"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF1565C0"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFE3F2FD"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFF9C4"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFCE4EC"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFF3E5F5"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>
      <left style="thin"><color rgb="FFB0BEC5"/></left>
      <right style="thin"><color rgb="FFB0BEC5"/></right>
      <top style="thin"><color rgb="FFB0BEC5"/></top>
      <bottom style="thin"><color rgb="FFB0BEC5"/></bottom>
    </border>
  </borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="12">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0">
      <alignment wrapText="1" vertical="center" shrinkToFit="0"/>
    </xf>
    <xf numFmtId="0" fontId="1" fillId="5" borderId="1" xfId="0">
      <alignment horizontal="center" wrapText="1" vertical="center"/>
    </xf>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0">
      <alignment horizontal="center" wrapText="1" vertical="center"/>
    </xf>
    <xf numFmtId="0" fontId="1" fillId="3" borderId="1" xfId="0">
      <alignment horizontal="center" wrapText="1" vertical="center"/>
    </xf>
    <xf numFmtId="0" fontId="1" fillId="4" borderId="1" xfId="0">
      <alignment horizontal="center" wrapText="1" vertical="center"/>
    </xf>
    <xf numFmtId="2" fontId="2" fillId="6" borderId="1" xfId="0">
      <alignment horizontal="center" vertical="center"/>
    </xf>
    <xf numFmtId="2" fontId="2" fillId="0" borderId="1" xfId="0">
      <alignment horizontal="center" vertical="center"/>
    </xf>
    <xf numFmtId="0" fontId="2" fillId="6" borderId="1" xfId="0">
      <alignment wrapText="1" vertical="center"/>
    </xf>
    <xf numFmtId="0" fontId="2" fillId="0" borderId="1" xfId="0">
      <alignment wrapText="1" vertical="center"/>
    </xf>
    <xf numFmtId="0" fontId="3" fillId="7" borderId="1" xfId="0">
      <alignment wrapText="1" vertical="center"/>
    </xf>
    <xf numFmtId="0" fontId="2" fillId="8" borderId="1" xfId="0">
      <alignment wrapText="1" vertical="center"/>
    </xf>
    <xf numFmtId="0" fontId="2" fillId="9" borderId="1" xfId="0">
      <alignment wrapText="1" vertical="center"/>
    </xf>
  </cellXfs>
</styleSheet>'''

COLOR_HDR = {"V": 2, "N": 3, "G": 4}
# sid: 0=normal, 1=azul header, 2=verde hdr, 3=naranja hdr, 4=gris hdr
#      5=num par, 6=num impar, 7=txt par, 8=txt impar, 9=warn amarillo
#      10=rosa (fab pendiente), 11=lila (ATESS)


def build_xlsx(path):
    rows_xml = []

    # Fila 1 — Título
    rows_xml.append(
        '<row r="1" ht="26" customHeight="1">'
        '<c r="A1" t="inlineStr" s="1">'
        '<is><t>CATÁLOGO MAESTRO DE BATERÍAS — BIPV COLOMBIA  |  '
        f'{len(BATERIAS)} modelos  |  Todos sistemas HV 300-870V</t></is></c>'
        '</row>'
    )

    # Fila 2 — Leyenda
    rows_xml.append(
        '<row r="2" ht="16" customHeight="1">'
        '<c r="A2" t="inlineStr" s="2"><is><t>🟢 OBLIGATORIO</t></is></c>'
        '<c r="E2" t="inlineStr" s="3"><is><t>🟠 IMPORTANTE — completar con datos del proveedor</t></is></c>'
        '<c r="N2" t="inlineStr" s="4"><is><t>⬜ OPCIONAL</t></is></c>'
        '</row>'
    )

    # Fila 3 — Encabezados
    hdr_cells = []
    for i, (label, color) in enumerate(HEADERS):
        sid = COLOR_HDR[color]
        hdr_cells.append(
            f'<c r="{COLS[i]}3" t="inlineStr" s="{sid}">'
            f'<is><t xml:space="preserve">{_esc(label)}</t></is></c>'
        )
    rows_xml.append(f'<row r="3" ht="40" customHeight="1">{"".join(hdr_cells)}</row>')

    # Filas de datos
    for bi, b in enumerate(BATERIAS):
        rn = 4 + bi
        par = bi % 2 == 0
        is_atess = b["Fabricante"] == "ATESS ESS"
        is_pend  = "Pendiente" in b["Fabricante"]

        cells = []
        for ci, key in enumerate(KEY_ORDER):
            col = COLS[ci]
            val = b.get(key, "")
            is_num = ci in NUM_CI and val != ""

            if ci == 20:   # Notas
                sid = 9    # amarillo advertencia
            elif is_num:
                sid = 5 if par else 6
            elif ci == 1:  # Fabricante
                sid = 11 if is_atess else (10 if is_pend else (7 if par else 8))
            else:
                sid = 7 if par else 8

            cells.append(_cell(col, rn, val, sid))

        rows_xml.append(
            f'<row r="{rn}" ht="52" customHeight="1">{"".join(cells)}</row>'
        )

    # Fila de aviso final
    warn_r = 4 + len(BATERIAS) + 1
    rows_xml.append(
        f'<row r="{warn_r}" ht="20" customHeight="1">'
        f'<c r="A{warn_r}" t="inlineStr" s="9">'
        f'<is><t>⚠ Campos pendientes para TODOS los modelos: DoD (%), Eficiencia RTE (%), '
        f'Garantía (años), Temperatura operación. Solicitar al proveedor para completar "Datos completos = Si".</t></is></c>'
        f'</row>'
    )

    # Ancho columnas
    col_widths = [16,18,10,14,10,8,11,11,14,12,12,11,11,11,11,10,7,16,10,11,55]
    col_defs = "".join(
        f'<col min="{i+1}" max="{i+1}" width="{w}" customWidth="1"/>'
        for i, w in enumerate(col_widths)
    )

    sheet1 = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
           xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheetFormatPr defaultRowHeight="15"/>
  <cols>{col_defs}</cols>
  <sheetData>{"".join(rows_xml)}</sheetData>
  <mergeCells count="3">
    <mergeCell ref="A1:U1"/>
    <mergeCell ref="A{warn_r}:U{warn_r}"/>
    <mergeCell ref="E2:M2"/>
  </mergeCells>
  <pageSetup orientation="landscape" paperSize="9"/>
</worksheet>'''

    # ── Hoja 2: Resumen ────────────────────────────────────────────────────
    series = [
        ("BR172R–215R","Pendiente confirmar","172–215","614–768","IP20","Rack interior"),
        ("ATESS BC/BR45-60T","ATESS ESS","46–61","460–614","IP54/IP20","Gab.ext / Rack int"),
        ("ATESS BC/BR75-145T","ATESS ESS","76–146","384–730","IP54/IP20","Gab.ext / Rack int"),
        ("ATESS BR114-157R","ATESS ESS","114–157","409–563","IP20","Rack interior"),
        ("ATESS BC55RPB","ATESS ESS","30–56","307–563","IP54","Gabinete exterior"),
    ]
    res_rows = []
    res_rows.append('<row r="1"><c r="A1" t="inlineStr" s="1"><is><t>RESUMEN POR SERIE</t></is></c></row>')
    res_rows.append(
        '<row r="2">'
        + "".join(f'<c r="{c}2" t="inlineStr" s="2"><is><t>{h}</t></is></c>'
                  for c,h in zip("ABCDEF",["Serie","Fabricante","Energía (kWh)","Voltaje (V)","IP","Montaje"]))
        + '</row>'
    )
    for i,(s,f,e,v,ip,m) in enumerate(series):
        r=i+3
        par2=i%2==0; sid2=7 if par2 else 8
        res_rows.append(
            f'<row r="{r}">'
            + _cell("A",r,s,sid2)+_cell("B",r,f,11 if f=="ATESS ESS" else 10)
            + _cell("C",r,e,sid2)+_cell("D",r,v,sid2)
            + _cell("E",r,ip,sid2)+_cell("F",r,m,sid2)
            + '</row>'
        )
    note_r = len(series)+4
    res_rows.append(
        f'<row r="{note_r}"><c r="A{note_r}" t="inlineStr" s="9">'
        f'<is><t>⚠ Todos los modelos son de ALTA TENSIÓN (300-870V). '
        f'Requieren inversores HV comerciales. No compatibles con DEYE/APsystems 48V.</t></is></c></row>'
    )
    res_rows.append(
        f'<row r="{note_r+1}"><c r="A{note_r+1}" t="inlineStr" s="9">'
        f'<is><t>⚠ Pendiente para todos: DoD (%), Eficiencia RTE (%), Garantía (años), '
        f'Temperatura operación, Costo (USD).</t></is></c></row>'
    )

    sheet2 = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <cols>
    <col min="1" max="1" width="28" customWidth="1"/>
    <col min="2" max="2" width="22" customWidth="1"/>
    <col min="3" max="3" width="16" customWidth="1"/>
    <col min="4" max="4" width="16" customWidth="1"/>
    <col min="5" max="5" width="14" customWidth="1"/>
    <col min="6" max="6" width="20" customWidth="1"/>
  </cols>
  <sheetData>{"".join(res_rows)}</sheetData>
  <mergeCells count="3">
    <mergeCell ref="A1:F1"/>
    <mergeCell ref="A{note_r}:F{note_r}"/>
    <mergeCell ref="A{note_r+1}:F{note_r+1}"/>
  </mergeCells>
</worksheet>'''

    # ── Empaquetar XLSX ────────────────────────────────────────────────────
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/sharedStrings.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>''')
        z.writestr("_rels/.rels", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="xl/workbook.xml"/>
</Relationships>''')
        z.writestr("xl/workbook.xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Catalogo_Baterias" sheetId="1" r:id="rId1"/>
    <sheet name="Resumen_Series"    sheetId="2" r:id="rId2"/>
  </sheets>
</workbook>''')
        z.writestr("xl/_rels/workbook.xml.rels", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
</Relationships>''')
        z.writestr("xl/styles.xml", STYLES_XML)
        z.writestr("xl/sharedStrings.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="0" uniqueCount="0"/>')
        z.writestr("xl/worksheets/sheet1.xml", sheet1)
        z.writestr("xl/worksheets/sheet2.xml", sheet2)

    with open(path, 'wb') as f:
        f.write(buf.getvalue())
    sz = os.path.getsize(path)
    print(f"✓ {path}  ({sz:,} bytes)  —  {len(BATERIAS)} modelos")


if __name__ == "__main__":
    build_xlsx("attached_assets/Catalogo_Baterias_BIPV_Maestro.xlsx")
