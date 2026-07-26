
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

for section in doc.sections:
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

# Título
title = doc.add_heading('ADENDA: Reglas Principales de Python', 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.runs[0].font.color.rgb = RGBColor(0x1A, 0x5C, 0x8A)

subtitle = doc.add_paragraph('Aplicadas a Cálculos Fotovoltaicos')
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
subtitle.runs[0].font.size = Pt(13)
subtitle.runs[0].font.bold = True
subtitle.runs[0].font.color.rgb = RGBColor(0x2E, 0x86, 0xC1)

doc.add_paragraph('')


def add_regla(numero, titulo, descripcion, sintaxis, ejemplo_desc, ejemplo_codigo):
    h = doc.add_heading(f'{numero}. {titulo}', level=1)
    h.runs[0].font.size = Pt(13)
    h.runs[0].font.color.rgb = RGBColor(0x1A, 0x5C, 0x8A)

    p = doc.add_paragraph()
    r = p.add_run('¿Qué hace? ')
    r.bold = True
    p.add_run(descripcion)

    p2 = doc.add_paragraph()
    r2 = p2.add_run('Sintaxis:  ')
    r2.bold = True
    cr = p2.add_run(sintaxis)
    cr.font.name = 'Courier New'
    cr.font.size = Pt(10)
    cr.font.color.rgb = RGBColor(0x17, 0x6B, 0x17)

    p3 = doc.add_paragraph()
    r3 = p3.add_run('Ejemplo FV:  ')
    r3.bold = True
    p3.add_run(ejemplo_desc + '  ')
    er = p3.add_run(ejemplo_codigo)
    er.font.name = 'Courier New'
    er.font.size = Pt(10)
    er.font.color.rgb = RGBColor(0xC0, 0x39, 0x2B)

    doc.add_paragraph('')


def add_seccion_titulo(texto):
    doc.add_paragraph('')
    h = doc.add_heading(texto, level=2)
    h.runs[0].font.size = Pt(12)
    h.runs[0].font.color.rgb = RGBColor(0x1A, 0x6B, 0x3C)
    doc.add_paragraph('')


def add_conversion(numero, nombre_from, nombre_to, formula_explicada, formula_codigo, ejemplo_desc, ejemplo_codigo):
    """Bloque especial para conversiones de métricas."""
    h = doc.add_heading(f'{numero}. Conversión: {nombre_from}  →  {nombre_to}', level=1)
    h.runs[0].font.size = Pt(13)
    h.runs[0].font.color.rgb = RGBColor(0x6E, 0x27, 0x94)  # morado para conversiones

    p = doc.add_paragraph()
    r = p.add_run('Fórmula:  ')
    r.bold = True
    p.add_run(formula_explicada)

    p2 = doc.add_paragraph()
    r2 = p2.add_run('En Python:  ')
    r2.bold = True
    cr = p2.add_run(formula_codigo)
    cr.font.name = 'Courier New'
    cr.font.size = Pt(10)
    cr.font.color.rgb = RGBColor(0x17, 0x6B, 0x17)

    p3 = doc.add_paragraph()
    r3 = p3.add_run('Ejemplo FV:  ')
    r3.bold = True
    p3.add_run(ejemplo_desc + '  ')
    er = p3.add_run(ejemplo_codigo)
    er.font.name = 'Courier New'
    er.font.size = Pt(10)
    er.font.color.rgb = RGBColor(0xC0, 0x39, 0x2B)

    doc.add_paragraph('')


# ─────────────────────────────────────────────
#  PARTE 1 — REGLAS BÁSICAS DE PYTHON
# ─────────────────────────────────────────────
add_seccion_titulo('PARTE 1 — REGLAS BÁSICAS DE PYTHON')

add_regla(1, 'Variable — Guardar un dato',
    'Almacena un valor en memoria con un nombre para usarlo después.',
    'nombre = valor',
    'Guardar la potencia de un panel solar:',
    'potencia_panel = 400   # watts')

add_regla(2, 'print() — Mostrar resultado',
    'Muestra un mensaje o resultado en la consola.',
    'print("texto", variable)',
    'Mostrar energía diaria generada:',
    'print("Energía diaria:", energia, "Wh")')

add_regla(3, 'input() — Pedir dato al usuario',
    'Pausa el programa y espera que el usuario escriba un valor.',
    'variable = input("mensaje")',
    'Pedir horas de sol del lugar:',
    'horas = input("Horas de sol al día: ")')

add_regla(4, 'float() — Convertir a número decimal',
    'Convierte texto a número decimal para realizar cálculos.',
    'variable = float(variable)',
    'Convertir horas de sol ingresadas para calcular:',
    'horas = float(horas)')

add_regla(5, 'int() — Convertir a número entero',
    'Convierte texto o decimal a número entero sin decimales.',
    'variable = int(variable)',
    'Convertir cantidad de paneles del usuario:',
    'paneles = int(input("Cantidad de paneles: "))')

add_regla(6, 'Operaciones aritméticas ( + - * / )',
    'Realiza suma, resta, multiplicación y división entre valores.',
    'resultado = valor1 * valor2 / valor3',
    'Calcular energía total del sistema solar:',
    'energia = potencia * horas * num_paneles')

add_regla(7, 'round() — Redondear decimales',
    'Redondea un número a la cantidad de decimales que indiques.',
    'round(numero, decimales)',
    'Redondear kWh mensuales generados:',
    'kwh_mes = round(energia * 30 / 1000, 2)')

add_regla(8, 'if / else — Condición',
    'Ejecuta acciones diferentes según si se cumple o no una condición.',
    'if condicion:\n      accion1\nelse:\n      accion2',
    'Verificar si el sistema cubre el consumo del hogar:',
    'if energia >= consumo:\n      print("Sistema suficiente")\nelse:\n      print("Faltan paneles")')

add_regla(9, 'for — Bucle (repetición)',
    'Repite un bloque de código para cada elemento de una lista o rango.',
    'for item in lista:\n      accion',
    'Calcular energía de varios modelos de paneles:',
    'for p in [300, 400, 500]:\n      print("Panel", p, "W →", p*5, "Wh/día")')

add_regla(10, 'range() — Generar secuencia de números',
    'Crea una secuencia de números desde un inicio hasta un fin.',
    'range(inicio, fin)',
    'Simular producción mensual durante 12 meses:',
    'for mes in range(1, 13):\n      print("Mes", mes, "→", kwh, "kWh")')

add_regla(11, 'Lista — Guardar varios valores',
    'Almacena múltiples valores en una sola variable.',
    'lista = [valor1, valor2, valor3]',
    'Guardar potencias de paneles disponibles:',
    'paneles = [300, 370, 400, 450, 550]')

add_regla(12, 'len() — Contar elementos de una lista',
    'Devuelve cuántos elementos tiene una lista.',
    'len(lista)',
    'Contar cuántos modelos de paneles hay:',
    'print("Modelos disponibles:", len(paneles))')

add_regla(13, 'Comentario con #',
    'Agrega una nota explicativa que Python ignora al ejecutar el código.',
    '# texto explicativo',
    'Documentar la fórmula usada:',
    '# Energía(Wh) = Potencia(W) x Horas_sol x N_paneles')

add_regla(14, 'type() — Ver tipo de dato',
    'Muestra si un dato es texto (str), entero (int) o decimal (float).',
    'print(type(variable))',
    'Verificar que horas_sol es número antes de calcular:',
    'print(type(horas_sol))   # debe ser <class float>')

add_regla(15, 'Fórmula con paréntesis — Control de orden',
    'Usa paréntesis para controlar el orden de las operaciones matemáticas.',
    'resultado = (a - b) * c / d',
    'Calcular retorno de inversión del sistema solar:',
    'roi = costo_sistema / (ahorro_anual)')


# ─────────────────────────────────────────────
#  PARTE 2 — CONVERSIONES DE MÉTRICAS
# ─────────────────────────────────────────────
add_seccion_titulo('PARTE 2 — CONVERSIONES DE MÉTRICAS EN PYTHON')

p_intro = doc.add_paragraph(
    'En ingeniería fotovoltaica es frecuente recibir datos en una unidad '
    'y necesitar calcular en otra. Esta sección muestra cómo escribir esas '
    'conversiones directamente en Python, con la fórmula, el código y un ejemplo aplicado.'
)
p_intro.runs[0].italic = True
doc.add_paragraph('')

# ── TEMPERATURA ──
add_seccion_titulo('  A) Conversiones de Temperatura')

add_conversion(16,
    'Celsius (°C)', 'Fahrenheit (°F)',
    '°F = (°C × 9/5) + 32',
    'tf = (tc * 9/5) + 32',
    'Convertir temperatura de operación del panel (25 °C estándar):',
    'tc = 25\ntf = (tc * 9/5) + 32\nprint("Temperatura:", tf, "°F")   # → 77.0 °F')

add_conversion(17,
    'Fahrenheit (°F)', 'Celsius (°C)',
    '°C = (°F − 32) × 5/9',
    'tc = (tf - 32) * 5/9',
    'Convertir dato climático de estación en °F a °C para calcular pérdida:',
    'tf = 95\ntc = (tf - 32) * 5/9\nprint("Temperatura:", round(tc,1), "°C")   # → 35.0 °C')

add_conversion(18,
    'Celsius (°C)', 'Kelvin (K)',
    'K = °C + 273.15',
    'tk = tc + 273.15',
    'Calcular eficiencia real del panel con temperatura en Kelvin:',
    'tc = 45\ntk = tc + 273.15\nprint("Temperatura en Kelvin:", tk, "K")   # → 318.15 K')

# ── POTENCIA ──
add_seccion_titulo('  B) Conversiones de Potencia')

add_conversion(19,
    'Watts (W)', 'Kilowatts (kW)',
    'kW = W ÷ 1 000',
    'kw = w / 1000',
    'Convertir potencia total de sistema de 3 200 W a kW:',
    'w = 3200\nkw = w / 1000\nprint("Potencia:", kw, "kW")   # → 3.2 kW')

add_conversion(20,
    'Kilowatts (kW)', 'Watts (W)',
    'W = kW × 1 000',
    'w = kw * 1000',
    'Expresar en W un panel nominado en 0.40 kW:',
    'kw = 0.40\nw = kw * 1000\nprint("Potencia:", w, "W")   # → 400.0 W')

add_conversion(21,
    'Watts (W)', 'Horsepower — HP (CV)',
    '1 HP = 745.7 W  →  HP = W ÷ 745.7',
    'hp = w / 745.7',
    'Comparar potencia de inversor (1 500 W) en HP:',
    'w = 1500\nhp = round(w / 745.7, 2)\nprint("Potencia:", hp, "HP")   # → 2.01 HP')

add_conversion(22,
    'Horsepower (HP)', 'Watts (W)',
    'W = HP × 745.7',
    'w = hp * 745.7',
    'Calcular carga en vatios de bomba de 2 HP alimentada por panel:',
    'hp = 2\nw = hp * 745.7\nprint("Carga bomba:", w, "W")   # → 1491.4 W')

# ── ENERGÍA ──
add_seccion_titulo('  C) Conversiones de Energía')

add_conversion(23,
    'Watt-hora (Wh)', 'Kilowatt-hora (kWh)',
    'kWh = Wh ÷ 1 000',
    'kwh = wh / 1000',
    'Convertir producción diaria de 4 800 Wh a kWh para factura:',
    'wh = 4800\nkwh = wh / 1000\nprint("Producción:", kwh, "kWh")   # → 4.8 kWh')

add_conversion(24,
    'Kilowatt-hora (kWh)', 'Watt-hora (Wh)',
    'Wh = kWh × 1 000',
    'wh = kwh * 1000',
    'Expresar en Wh el consumo mensual de 180 kWh para dimensionar banco de baterías:',
    'kwh = 180\nwh = kwh * 1000\nprint("Consumo:", wh, "Wh")   # → 180000 Wh')

add_conversion(25,
    'Kilowatt-hora (kWh)', 'Megawatt-hora (MWh)',
    'MWh = kWh ÷ 1 000',
    'mwh = kwh / 1000',
    'Calcular producción anual de un parque solar en MWh:',
    'kwh_anual = 52000\nmwh = kwh_anual / 1000\nprint("Producción anual:", mwh, "MWh")   # → 52.0 MWh')

add_conversion(26,
    'Watt-hora (Wh)', 'Joules (J)',
    '1 Wh = 3 600 J  →  J = Wh × 3 600',
    'j = wh * 3600',
    'Convertir energía de batería de 100 Wh a Joules:',
    'wh = 100\nj = wh * 3600\nprint("Energía:", j, "J")   # → 360000 J')

# ── ÁREA / SUPERFICIE ──
add_seccion_titulo('  D) Conversiones de Área')

add_conversion(27,
    'Metros cuadrados (m²)', 'Pies cuadrados (ft²)',
    '1 m² = 10.764 ft²  →  ft² = m² × 10.764',
    'ft2 = m2 * 10.764',
    'Calcular área de techo en ft² para clientes que usan sistema imperial:',
    'm2 = 30\nft2 = round(m2 * 10.764, 2)\nprint("Área:", ft2, "ft²")   # → 322.92 ft²')

add_conversion(28,
    'Pies cuadrados (ft²)', 'Metros cuadrados (m²)',
    '1 ft² = 0.0929 m²  →  m² = ft² × 0.0929',
    'm2 = ft2 * 0.0929',
    'Convertir techo de 400 ft² a m² para calcular cuántos paneles caben:',
    'ft2 = 400\nm2 = round(ft2 * 0.0929, 2)\nprint("Área:", m2, "m²")   # → 37.16 m²')

add_conversion(29,
    'Metros cuadrados (m²)', 'Hectáreas (ha)',
    '1 ha = 10 000 m²  →  ha = m² ÷ 10 000',
    'ha = m2 / 10000',
    'Expresar superficie de un parque solar de 25 000 m² en hectáreas:',
    'm2 = 25000\nha = m2 / 10000\nprint("Superficie:", ha, "ha")   # → 2.5 ha')

add_conversion(30,
    'Kilómetros cuadrados (km²)', 'Metros cuadrados (m²)',
    '1 km² = 1 000 000 m²  →  m² = km² × 1 000 000',
    'm2 = km2 * 1000000',
    'Convertir irradiación global en km² a m² para proyectar potencia instalable:',
    'km2 = 0.05\nm2 = km2 * 1000000\nprint("Área disponible:", m2, "m²")   # → 50000.0 m²')

# ── EJEMPLO INTEGRADOR ──
add_seccion_titulo('EJEMPLO INTEGRADOR — Uso combinado de conversiones')

p_ej = doc.add_paragraph()
r_titulo = p_ej.add_run('Caso: Calcular producción y verificar suficiencia de un sistema solar')
r_titulo.bold = True
r_titulo.font.size = Pt(11)
r_titulo.font.color.rgb = RGBColor(0x1A, 0x5C, 0x8A)

codigo_integrador = (
    '# Datos de entrada\n'
    'potencia_w     = 400          # potencia de cada panel en W\n'
    'num_paneles    = 8            # cantidad de paneles\n'
    'horas_sol      = 5.5          # horas de sol pico (HSP) del lugar\n'
    'consumo_kwh    = 20           # consumo diario del hogar en kWh\n'
    'temp_f         = 95           # temperatura ambiente en °F\n\n'
    '# Conversión de temperatura\n'
    'temp_c = (temp_f - 32) * 5/9\n'
    'print("Temperatura de operación:", round(temp_c,1), "°C")\n\n'
    '# Energía generada en Wh y kWh\n'
    'energia_wh  = potencia_w * num_paneles * horas_sol\n'
    'energia_kwh = energia_wh / 1000\n'
    'print("Energía generada:", energia_kwh, "kWh/día")\n\n'
    '# ¿Cubre el consumo?\n'
    'if energia_kwh >= consumo_kwh:\n'
    '    print("Sistema suficiente")\n'
    'else:\n'
    '    faltante = consumo_kwh - energia_kwh\n'
    '    print("Faltan", faltante, "kWh — se necesitan más paneles")\n'
)

p_code = doc.add_paragraph()
cr = p_code.add_run(codigo_integrador)
cr.font.name = 'Courier New'
cr.font.size = Pt(9.5)
cr.font.color.rgb = RGBColor(0x10, 0x10, 0x60)

doc.add_paragraph('')

# Pie de página
footer = doc.add_paragraph('Elaborado para curso de Python aplicado a Energía Solar Fotovoltaica — 2026')
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer.runs[0].font.size = Pt(9)
footer.runs[0].font.color.rgb = RGBColor(0x7F, 0x7F, 0x7F)
footer.runs[0].italic = True

doc.save('Adenda_Python_Fotovoltaico.docx')
print("Documento creado correctamente.")
