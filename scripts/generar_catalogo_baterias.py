"""
Genera Catalogo_Baterias_BIPV.xlsx con los 4 modelos reales BR172R/186R/200R/215R.
Usa zipfile puro (sin openpyxl) para compatibilidad con entorno Replit Nix.
"""
import zipfile, io, os

# ── Colores ────────────────────────────────────────────────────────────────
C_VERDE    = "FF2E7D32"   # verde oscuro — obligatorio
C_NARANJA  = "FFE65100"   # naranja     — importante
C_GRIS     = "FF616161"   # gris        — opcional
C_HEADER   = "FF1565C0"   # azul        — encabezado
C_AMBAR    = "FFF57F17"   # ámbar       — advertencia
C_FILA1    = "FFE3F2FD"   # azul muy claro — fila par
C_FILA2    = "FFFFFFFF"   # blanco       — fila impar

# ── Datos de baterías ──────────────────────────────────────────────────────
HEADERS = [
    ("Modelo",              C_VERDE),
    ("Fabricante",          C_NARANJA),
    ("Datos completos\n(Si/No)", C_VERDE),
    ("Tecnología",          C_VERDE),
    ("Capacidad\n(kWh)",    C_VERDE),
    ("DoD\n(%)",            C_VERDE),
    ("Eficiencia RTE\n(%)", C_VERDE),
    ("Ciclos de Vida",      C_VERDE),
    ("Potencia Continua\n(kW)", C_VERDE),
    ("Potencia Pico\n(kW)", C_NARANJA),
    ("Voltaje Nominal\n(V)",C_NARANJA),
    ("Voltaje Mín\n(V)",    C_NARANJA),
    ("Voltaje Máx\n(V)",    C_NARANJA),
    ("Temperatura Mín\n(°C)", C_GRIS),
    ("Temperatura Máx\n(°C)", C_GRIS),
    ("Peso\n(kg)",          C_GRIS),
    ("IP",                  C_GRIS),
    ("Montaje",             C_GRIS),
    ("Garantía\n(años)",    C_NARANJA),
    ("Costo\n(USD)",        C_NARANJA),
    ("Notas",               C_GRIS),
]

BATERIAS = [
    # BR172R — 12 módulos, 172 kWh, 614.4V
    {
        "Modelo":               "BR172R",
        "Fabricante":           "",               # no indicado en ficha
        "Datos completos":      "No",             # faltan DoD, RTE, garantía, fabricante
        "Tecnología":           "LiFePO4 (16S1P)",
        "Capacidad (kWh)":      172.032,
        "DoD (%)":              "",               # no especificado en ficha
        "Eficiencia RTE (%)":   "",               # no especificado en ficha
        "Ciclos de Vida":       6000,
        "Potencia Continua (kW)": 86.0,           # 0.5C × 172 kWh
        "Potencia Pico (kW)":   172.0,            # 1C opcional
        "Voltaje Nominal (V)":  614.4,
        "Voltaje Mín (V)":      537.6,
        "Voltaje Máx (V)":      691.2,
        "Temperatura Mín (°C)": "",
        "Temperatura Máx (°C)": "",
        "Peso (kg)":            1511,
        "IP":                   "IP20",
        "Montaje":              "Rack interior",
        "Garantía (años)":      "",
        "Costo (USD)":          "",
        "Notas": "ALTA TENSIÓN 614V — incompatible con inversores 48V. "
                 "Requiere inversor HV comercial/industrial. "
                 "12 módulos × 14.336 kWh. BMS CAN incluido. Pantalla táctil 7\".",
    },
    # BR186R — 13 módulos, 186 kWh, 665.6V
    {
        "Modelo":               "BR186R",
        "Fabricante":           "",
        "Datos completos":      "No",
        "Tecnología":           "LiFePO4 (16S1P)",
        "Capacidad (kWh)":      186.368,
        "DoD (%)":              "",
        "Eficiencia RTE (%)":   "",
        "Ciclos de Vida":       6000,
        "Potencia Continua (kW)": 93.2,
        "Potencia Pico (kW)":   186.4,
        "Voltaje Nominal (V)":  665.6,
        "Voltaje Mín (V)":      582.4,
        "Voltaje Máx (V)":      748.8,
        "Temperatura Mín (°C)": "",
        "Temperatura Máx (°C)": "",
        "Peso (kg)":            1624,
        "IP":                   "IP20",
        "Montaje":              "Rack interior",
        "Garantía (años)":      "",
        "Costo (USD)":          "",
        "Notas": "ALTA TENSIÓN 665V — incompatible con inversores 48V. "
                 "13 módulos × 14.336 kWh. BMS CAN incluido.",
    },
    # BR200R — 14 módulos, 200 kWh, 716.8V
    {
        "Modelo":               "BR200R",
        "Fabricante":           "",
        "Datos completos":      "No",
        "Tecnología":           "LiFePO4 (16S1P)",
        "Capacidad (kWh)":      200.704,
        "DoD (%)":              "",
        "Eficiencia RTE (%)":   "",
        "Ciclos de Vida":       6000,
        "Potencia Continua (kW)": 100.4,
        "Potencia Pico (kW)":   200.7,
        "Voltaje Nominal (V)":  716.8,
        "Voltaje Mín (V)":      627.2,
        "Voltaje Máx (V)":      806.4,
        "Temperatura Mín (°C)": "",
        "Temperatura Máx (°C)": "",
        "Peso (kg)":            1737,
        "IP":                   "IP20",
        "Montaje":              "Rack interior",
        "Garantía (años)":      "",
        "Costo (USD)":          "",
        "Notas": "ALTA TENSIÓN 716V — incompatible con inversores 48V. "
                 "14 módulos × 14.336 kWh. BMS CAN incluido.",
    },
    # BR215R — 15 módulos, 215 kWh, 768V
    {
        "Modelo":               "BR215R",
        "Fabricante":           "",
        "Datos completos":      "No",
        "Tecnología":           "LiFePO4 (16S1P)",
        "Capacidad (kWh)":      215.040,
        "DoD (%)":              "",
        "Eficiencia RTE (%)":   "",
        "Ciclos de Vida":       6000,
        "Potencia Continua (kW)": 107.5,
        "Potencia Pico (kW)":   215.0,
        "Voltaje Nominal (V)":  768.0,
        "Voltaje Mín (V)":      672.0,
        "Voltaje Máx (V)":      864.0,
        "Temperatura Mín (°C)": "",
        "Temperatura Máx (°C)": "",
        "Peso (kg)":            1850,
        "IP":                   "IP20",
        "Montaje":              "Rack interior",
        "Garantía (años)":      "",
        "Costo (USD)":          "",
        "Notas": "ALTA TENSIÓN 768V — incompatible con inversores 48V. "
                 "15 módulos × 14.336 kWh. BMS CAN incluido.",
    },
]

# ── Helpers XML ────────────────────────────────────────────────────────────
def _esc(v):
    return str(v).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def _cell(col, row, value, style_id=0):
    cr = f"{col}{row}"
    if value == "" or value is None:
        return f'<c r="{cr}" s="{style_id}"><v></v></c>'
    if isinstance(value, (int, float)):
        return f'<c r="{cr}" t="n" s="{style_id}"><v>{value}</v></c>'
    return f'<c r="{cr}" t="inlineStr" s="{style_id}"><is><t xml:space="preserve">{_esc(str(value))}</t></is></c>'

COL_LETTERS = [
    "A","B","C","D","E","F","G","H","I","J","K","L","M",
    "N","O","P","Q","R","S","T","U"
]

def build_xlsx(path):
    # ── Styles XML ─────────────────────────────────────────────────────────
    # fontId: 0=normal, 1=bold-white, 2=bold-black, 3=bold-ambar
    # fillId: 0=none, 1=gray(reserved), 2=verde, 3=naranja, 4=gris, 5=header-blue,
    #         6=fila-par, 7=ambar
    styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="4">
    <font><sz val="10"/><name val="Calibri"/></font>
    <font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
    <font><b/><sz val="10"/><name val="Calibri"/></font>
    <font><b/><sz val="10"/><color rgb="FFE65100"/><name val="Calibri"/></font>
  </fonts>
  <fills count="8">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF2E7D32"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFE65100"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF616161"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF1565C0"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFE3F2FD"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFF9C4"/></patternFill></fill>
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
  <cellXfs count="10">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0">
      <alignment wrapText="1" vertical="center"/>
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
    <xf numFmtId="0" fontId="2" fillId="6" borderId="1" xfId="0">
      <alignment wrapText="1" vertical="center"/>
    </xf>
    <xf numFmtId="0" fontId="2" fillId="0" borderId="1" xfId="0">
      <alignment wrapText="1" vertical="center"/>
    </xf>
    <xf numFmtId="2" fontId="2" fillId="6" borderId="1" xfId="0">
      <alignment horizontal="center" vertical="center"/>
    </xf>
    <xf numFmtId="2" fontId="2" fillId="0" borderId="1" xfId="0">
      <alignment horizontal="center" vertical="center"/>
    </xf>
    <xf numFmtId="0" fontId="3" fillId="7" borderId="1" xfId="0">
      <alignment horizontal="center" wrapText="1" vertical="center"/>
    </xf>
  </cellXfs>
</styleSheet>'''

    # Mapa color → styleId para cabecera
    color_to_hdr = {C_VERDE: 2, C_NARANJA: 3, C_GRIS: 4}

    # ── Hoja 1: Catalogo_Baterias ──────────────────────────────────────────
    rows_xml = []

    # Fila 1 — Título
    rows_xml.append(
        f'<row r="1" ht="24" customHeight="1">'
        f'<c r="A1" t="inlineStr" s="1"><is><t>CATÁLOGO DE BATERÍAS — BIPV COLOMBIA</t></is></c>'
        f'</row>'
    )

    # Fila 2 — Leyenda
    rows_xml.append(
        f'<row r="2" ht="18" customHeight="1">'
        f'<c r="A2" t="inlineStr" s="2"><is><t>🟢 OBLIGATORIO — requerido para calcular</t></is></c>'
        f'<c r="E2" t="inlineStr" s="3"><is><t>🟠 IMPORTANTE — mejora la precisión</t></is></c>'
        f'<c r="J2" t="inlineStr" s="4"><is><t>⬜ OPCIONAL — enriquecer la ficha</t></is></c>'
        f'</row>'
    )

    # Fila 3 — Encabezados
    hdr_cells = []
    for i, (label, color) in enumerate(HEADERS):
        col = COL_LETTERS[i]
        sid = color_to_hdr.get(color, 1)
        hdr_cells.append(
            f'<c r="{col}3" t="inlineStr" s="{sid}">'
            f'<is><t xml:space="preserve">{_esc(label)}</t></is></c>'
        )
    rows_xml.append(f'<row r="3" ht="36" customHeight="1">{"".join(hdr_cells)}</row>')

    # Filas de datos (4 baterías reales)
    KEYS = [h[0].replace("\n","") for h in HEADERS]
    KEY_MAP = {
        "Modelo":               "Modelo",
        "Fabricante":           "Fabricante",
        "Datos completos(Si/No)": "Datos completos",
        "Tecnología":           "Tecnología",
        "Capacidad(kWh)":       "Capacidad (kWh)",
        "DoD(%)":               "DoD (%)",
        "Eficiencia RTE(%)":    "Eficiencia RTE (%)",
        "Ciclos de Vida":       "Ciclos de Vida",
        "Potencia Continua(kW)": "Potencia Continua (kW)",
        "Potencia Pico(kW)":    "Potencia Pico (kW)",
        "Voltaje Nominal(V)":   "Voltaje Nominal (V)",
        "Voltaje Mín(V)":       "Voltaje Mín (V)",
        "Voltaje Máx(V)":       "Voltaje Máx (V)",
        "Temperatura Mín(°C)":  "Temperatura Mín (°C)",
        "Temperatura Máx(°C)":  "Temperatura Máx (°C)",
        "Peso(kg)":             "Peso (kg)",
        "IP":                   "IP",
        "Montaje":              "Montaje",
        "Garantía(años)":       "Garantía (años)",
        "Costo(USD)":           "Costo (USD)",
        "Notas":                "Notas",
    }

    # Columnas numéricas
    NUM_COLS = {4,5,6,7,8,9,10,11,12,13,14,15,16,19}  # 0-based índices

    bat_key_order = [
        "Modelo","Fabricante","Datos completos","Tecnología",
        "Capacidad (kWh)","DoD (%)","Eficiencia RTE (%)","Ciclos de Vida",
        "Potencia Continua (kW)","Potencia Pico (kW)",
        "Voltaje Nominal (V)","Voltaje Mín (V)","Voltaje Máx (V)",
        "Temperatura Mín (°C)","Temperatura Máx (°C)",
        "Peso (kg)","IP","Montaje","Garantía (años)","Costo (USD)","Notas",
    ]

    for bi, bat in enumerate(BATERIAS):
        row_num = 4 + bi
        is_even = bi % 2 == 0
        cells = []
        for ci, key in enumerate(bat_key_order):
            col = COL_LETTERS[ci]
            val = bat.get(key, "")
            is_num = ci in NUM_COLS
            # Estilo: notas usa s=5 o s=6 (par/impar), números centrados
            if ci == 20:           # Notas — texto largo, amarillo si contiene ALTA
                if "ALTA TENSIÓN" in str(val):
                    sid = 9
                else:
                    sid = 5 if is_even else 6
            elif is_num and val != "":
                sid = 7 if is_even else 8
            else:
                sid = 5 if is_even else 6
            cells.append(_cell(col, row_num, val, sid))
        rows_xml.append(
            f'<row r="{row_num}" ht="60" customHeight="1">{"".join(cells)}</row>'
        )

    # Fila de advertencia
    warn_row = 4 + len(BATERIAS) + 1
    rows_xml.append(
        f'<row r="{warn_row}" ht="18" customHeight="1">'
        f'<c r="A{warn_row}" t="inlineStr" s="9">'
        f'<is><t>⚠ Estas baterías son de ALTA TENSIÓN (600-860V). '
        f'Requieren inversores comerciales/industriales HV. '
        f'Completar: Fabricante, DoD, RTE, Garantía cuando disponga de la información.</t></is></c>'
        f'</row>'
    )

    sheet1 = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
           xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheetFormatPr defaultRowHeight="15" customHeight="1"/>
  <cols>
    <col min="1" max="1"  width="16" customWidth="1"/>
    <col min="2" max="2"  width="16" customWidth="1"/>
    <col min="3" max="3"  width="12" customWidth="1"/>
    <col min="4" max="4"  width="18" customWidth="1"/>
    <col min="5" max="5"  width="12" customWidth="1"/>
    <col min="6" max="6"  width="10" customWidth="1"/>
    <col min="7" max="7"  width="12" customWidth="1"/>
    <col min="8" max="8"  width="12" customWidth="1"/>
    <col min="9" max="9"  width="14" customWidth="1"/>
    <col min="10" max="10" width="12" customWidth="1"/>
    <col min="11" max="11" width="13" customWidth="1"/>
    <col min="12" max="12" width="12" customWidth="1"/>
    <col min="13" max="13" width="12" customWidth="1"/>
    <col min="14" max="14" width="12" customWidth="1"/>
    <col min="15" max="15" width="12" customWidth="1"/>
    <col min="16" max="16" width="10" customWidth="1"/>
    <col min="17" max="17" width="8"  customWidth="1"/>
    <col min="18" max="18" width="13" customWidth="1"/>
    <col min="19" max="19" width="11" customWidth="1"/>
    <col min="20" max="20" width="12" customWidth="1"/>
    <col min="21" max="21" width="55" customWidth="1"/>
  </cols>
  <sheetData>
    {"".join(rows_xml)}
  </sheetData>
  <mergeCells count="3">
    <mergeCell ref="A1:U1"/>
    <mergeCell ref="A{warn_row}:U{warn_row}"/>
    <mergeCell ref="E2:I2"/>
  </mergeCells>
  <pageSetup orientation="landscape"/>
</worksheet>'''

    # ── Hoja 2: Guia_Referencia ────────────────────────────────────────────
    guia_rows = [
        ('A1','GUÍA DE REFERENCIA — Cómo leer la ficha técnica de una batería',1),
        ('A3','Campo',2), ('B3','Qué buscar en la ficha técnica',2), ('C3','Valores típicos LiFePO4',2),
        ('A4','Capacidad (kWh)',0), ('B4','kWh o kWh de energía útil (usable energy)',0),
        ('C4','5 – 200 kWh por unidad',0),
        ('A5','DoD (%)',0), ('B5','Depth of Discharge / Profundidad de Descarga',0),
        ('C5','80 – 100 %',0),
        ('A6','Eficiencia RTE (%)',0), ('B6','Round-trip efficiency / Eficiencia ida y vuelta',0),
        ('C6','90 – 98 %',0),
        ('A7','Ciclos de Vida',0), ('B7','Cycle life @ 80% DoD',0),
        ('C7','3 000 – 10 000 ciclos',0),
        ('A8','Potencia Continua (kW)',0), ('B8','Continuous charge/discharge power',0),
        ('C8','0.5 × C-rate × Capacidad',0),
        ('A9','Voltaje Nominal (V)',0), ('B9','Nominal voltage del banco completo',0),
        ('C9','48V (residencial) / 600-800V (industrial)',0),
        ('A11','⚠ NOTA ALTA TENSIÓN',3),
        ('A12','Los modelos BR172R/186R/200R/215R operan entre 537V y 864V.',0),
        ('A13','Son sistemas industriales que requieren inversores de alta tensión (HV string inverters).',0),
        ('A14','NO son compatibles con inversores de 48V como DEYE SUN-7.6K o APsystems AHS.',0),
        ('A15','Para completar la ficha solicite al proveedor: marca/fabricante, DoD real, eficiencia RTE y garantía.',0),
    ]

    g_cells = []
    for ref, text, sid in guia_rows:
        g_cells.append(
            f'<c r="{ref}" t="inlineStr" s="{sid}"><is><t xml:space="preserve">{_esc(text)}</t></is></c>'
        )
        row_num = int(''.join(filter(str.isdigit, ref)))
        g_cells[-1] = f'<row r="{row_num}">{g_cells[-1]}</row>'

    # Simplify: just write each row individually
    g_rows_xml = []
    seen_rows = {}
    for ref, text, sid in guia_rows:
        row_num = int(''.join(filter(str.isdigit, ref)))
        col = ''.join(filter(str.isalpha, ref))
        cell = f'<c r="{ref}" t="inlineStr" s="{sid}"><is><t xml:space="preserve">{_esc(text)}</t></is></c>'
        if row_num not in seen_rows:
            seen_rows[row_num] = []
        seen_rows[row_num].append(cell)

    for rn in sorted(seen_rows.keys()):
        g_rows_xml.append(f'<row r="{rn}">{"".join(seen_rows[rn])}</row>')

    sheet2 = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <cols>
    <col min="1" max="1" width="28" customWidth="1"/>
    <col min="2" max="2" width="45" customWidth="1"/>
    <col min="3" max="3" width="28" customWidth="1"/>
  </cols>
  <sheetData>{"".join(g_rows_xml)}</sheetData>
  <mergeCells count="5">
    <mergeCell ref="A1:C1"/>
    <mergeCell ref="A11:C11"/>
    <mergeCell ref="A12:C12"/>
    <mergeCell ref="A13:C13"/>
    <mergeCell ref="A14:C14"/>
  </mergeCells>
</worksheet>'''

    # ── Empaquetar XLSX ────────────────────────────────────────────────────
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:

        z.writestr("[Content_Types].xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
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
    <sheet name="Guia_Referencia"   sheetId="2" r:id="rId2"/>
  </sheets>
</workbook>''')

        z.writestr("xl/_rels/workbook.xml.rels", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"
    Target="styles.xml"/>
  <Relationship Id="rId4"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings"
    Target="sharedStrings.xml"/>
</Relationships>''')

        z.writestr("xl/styles.xml", styles_xml)
        z.writestr("xl/sharedStrings.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="0" uniqueCount="0"/>')
        z.writestr("xl/worksheets/sheet1.xml", sheet1)
        z.writestr("xl/worksheets/sheet2.xml", sheet2)

    with open(path, 'wb') as f:
        f.write(buf.getvalue())
    print(f"✓ Generado: {path}  ({os.path.getsize(path):,} bytes)")


if __name__ == "__main__":
    out = "attached_assets/Catalogo_Baterias_BR_Series.xlsx"
    build_xlsx(out)
