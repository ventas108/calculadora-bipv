
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

# ─────────────────────────────────────────────
#  PARTE 3 — HORAS DE SOL PICO E IRRADIANCIA
# ─────────────────────────────────────────────
add_seccion_titulo('PARTE 3 — HORAS DE SOL PICO (HSP) E IRRADIANCIA SOLAR')

p_def = doc.add_paragraph()
r_def = p_def.add_run('Conceptos clave antes de programar:')
r_def.bold = True
r_def.font.size = Pt(11)
r_def.font.color.rgb = RGBColor(0x6E, 0x27, 0x94)
doc.add_paragraph('')

# Definición HSP
h_hsp = doc.add_heading('¿Qué es la Hora de Sol Pico (HSP)?', level=2)
h_hsp.runs[0].font.size = Pt(11)
h_hsp.runs[0].font.color.rgb = RGBColor(0x6E, 0x27, 0x94)

p_hsp = doc.add_paragraph(
    'Una HSP equivale a 1 hora de irradiancia constante a 1 000 W/m² (condición estándar). '
    'Es decir, si tu zona recibe 5 HSP al día, significa que la energía solar acumulada '
    'de ese día es equivalente a tener el sol al máximo durante 5 horas seguidas. '
    'Se obtiene de bases de datos como NASA POWER, PVGIS o SolarGIS, ingresando la '
    'latitud/longitud del proyecto.'
)
p_hsp.runs[0].font.size = Pt(10)
doc.add_paragraph('')

# Definición Irradiancia
h_irr = doc.add_heading('¿Qué es la Irradiancia?', level=2)
h_irr.runs[0].font.size = Pt(11)
h_irr.runs[0].font.color.rgb = RGBColor(0x6E, 0x27, 0x94)

p_irr = doc.add_paragraph(
    'La irradiancia es la potencia del sol que llega a 1 m² de superficie en un instante, '
    'medida en W/m². La irradiación es la energía acumulada en un período (Wh/m² o kWh/m²). '
    'La relación fundamental es: Irradiación (kWh/m²) = HSP × 1 kW/m².'
)
p_irr.runs[0].font.size = Pt(10)
doc.add_paragraph('')

add_seccion_titulo('  E) Cálculos y Conversiones de HSP e Irradiancia')

# ── Conversión 31: kWh/m²/día → HSP
add_conversion(31,
    'Irradiación diaria (kWh/m²/día)', 'HSP del lugar',
    'HSP = kWh/m²/día  (son numéricamente iguales, solo cambia la interpretación)',
    'hsp = irradiacion_kwh_m2',
    'El atlas solar indica 5.2 kWh/m²/día para tu ciudad — ese valor ES las HSP:',
    'irradiacion_kwh_m2 = 5.2   # dato de NASA POWER o PVGIS\n'
    'hsp = irradiacion_kwh_m2\n'
    'print("HSP del lugar:", hsp, "h/día")   # → 5.2 h/día')

# ── Conversión 32: Wh/m²/día → HSP
add_conversion(32,
    'Irradiación en Wh/m²/día', 'HSP',
    'HSP = Wh/m²/día ÷ 1 000',
    'hsp = irradiacion_wh_m2 / 1000',
    'Un sensor registró 5 200 Wh/m²/día. Convertir a HSP:',
    'irradiacion_wh_m2 = 5200\n'
    'hsp = irradiacion_wh_m2 / 1000\n'
    'print("HSP:", hsp, "h/día")   # → 5.2 h/día')

# ── Conversión 33: HSP → Energía generada (Wh)
add_conversion(33,
    'HSP + Potencia del sistema (W)', 'Energía diaria generada (Wh)',
    'Energía (Wh) = Potencia_pico (W) × HSP',
    'energia_wh = potencia_pico_w * hsp',
    'Sistema de 2 000 W en zona con 5.2 HSP. ¿Cuánto genera al día?',
    'potencia_pico_w = 2000   # 5 paneles × 400 W\n'
    'hsp = 5.2\n'
    'energia_wh = potencia_pico_w * hsp\n'
    'print("Energía diaria:", energia_wh, "Wh")   # → 10400 Wh → 10.4 kWh')

# ── Conversión 34: Energía real con pérdidas (PR)
add_conversion(34,
    'Energía ideal (Wh) + Factor de rendimiento (PR)', 'Energía real entregada (Wh)',
    'Energía_real = Potencia_pico × HSP × PR    (PR típico: 0.75 a 0.85)',
    'energia_real_wh = potencia_pico_w * hsp * pr',
    'Calcular energía real considerando pérdidas del sistema (PR = 0.80):',
    'potencia_pico_w = 2000\n'
    'hsp = 5.2\n'
    'pr  = 0.80   # 80% de rendimiento real (pérdidas por calor, cableado, inversor)\n'
    'energia_real_wh = potencia_pico_w * hsp * pr\n'
    'print("Energía real:", energia_real_wh, "Wh")   # → 8320 Wh')

# ── Conversión 35: Potencia pico necesaria
add_conversion(35,
    'Consumo diario (kWh) + HSP + PR', 'Potencia pico necesaria (kWp)',
    'Potencia_pico (kWp) = Consumo_diario (kWh) ÷ (HSP × PR)',
    'potencia_kWp = consumo_kwh / (hsp * pr)',
    'Hogar con 18 kWh/día de consumo, zona con 5 HSP y PR 0.78. ¿Cuántos kWp instalar?',
    'consumo_kwh = 18\n'
    'hsp = 5.0\n'
    'pr  = 0.78\n'
    'potencia_kWp = consumo_kwh / (hsp * pr)\n'
    'print("Potencia necesaria:", round(potencia_kWp, 2), "kWp")   # → 4.62 kWp')

# ── Conversión 36: Número de paneles necesarios
add_conversion(36,
    'Potencia pico (kWp) + Potencia por panel (W)', 'Número de paneles',
    'N_paneles = Potencia_pico (W) ÷ Potencia_panel (W)  → redondear hacia arriba',
    'import math\nn_paneles = math.ceil(potencia_w / potencia_panel_w)',
    'Sistema de 4.62 kWp con paneles de 400 W. ¿Cuántos paneles se necesitan?',
    'import math\n'
    'potencia_w = 4620        # 4.62 kWp convertido a W\n'
    'potencia_panel_w = 400\n'
    'n_paneles = math.ceil(potencia_w / potencia_panel_w)\n'
    'print("Paneles necesarios:", n_paneles)   # → 12 paneles')

# ── Conversión 37: Irradiancia W/m² → kW/m²
add_conversion(37,
    'Irradiancia (W/m²)', 'Irradiancia (kW/m²)',
    'kW/m² = W/m² ÷ 1 000',
    'irr_kw_m2 = irr_w_m2 / 1000',
    'Sensor registra 850 W/m² en el mediodía. Convertir a kW/m²:',
    'irr_w_m2 = 850\n'
    'irr_kw_m2 = irr_w_m2 / 1000\n'
    'print("Irradiancia:", irr_kw_m2, "kW/m²")   # → 0.85 kW/m²')

# ── Conversión 38: Eficiencia real del panel según temperatura
add_conversion(38,
    'Eficiencia nominal + temperatura real (°C)', 'Eficiencia real del panel (%)',
    'Efic_real = Efic_nom × (1 + Coef_temp × (T_real − 25))\n'
    '   Coef_temp típico: −0.0035 por °C  (pérdida del 0.35 % por cada °C sobre 25°C)',
    'efic_real = efic_nom * (1 + coef_temp * (temp_c - 25))',
    'Panel con eficiencia nominal 20 %, operando a 45 °C. ¿Cuál es su eficiencia real?',
    'efic_nom  = 0.20        # 20% de eficiencia en condición estándar\n'
    'coef_temp = -0.0035     # coeficiente de temperatura del fabricante\n'
    'temp_c    = 45          # temperatura real de operación\n'
    'efic_real = efic_nom * (1 + coef_temp * (temp_c - 25))\n'
    'print("Eficiencia real:", round(efic_real * 100, 2), "%")   # → 18.6 %')

# ── Conversión 39: Irradiación mensual → producción mensual
add_conversion(39,
    'Irradiación mensual (kWh/m²/mes) + Potencia pico + PR', 'Producción mensual (kWh)',
    'Producción_mes (kWh) = Potencia_pico (kWp) × Irradiación_mes (kWh/m²) × PR',
    'prod_mes_kwh = potencia_kWp * irradiacion_mes * pr',
    'Sistema de 3 kWp, mes con 150 kWh/m² de irradiación, PR 0.80:',
    'potencia_kWp     = 3.0\n'
    'irradiacion_mes  = 150   # kWh/m²/mes (dato de PVGIS o NASA)\n'
    'pr               = 0.80\n'
    'prod_mes_kwh = potencia_kWp * irradiacion_mes * pr\n'
    'print("Producción mensual:", prod_mes_kwh, "kWh")   # → 360.0 kWh')

# ── Conversión 40: Producción anual estimada
add_conversion(40,
    'Producción mensual (kWh/mes)', 'Producción anual (kWh/año)',
    'Producción_año = suma de los 12 meses  (o simplificada: promedio × 12)',
    'prod_anual = sum(producciones_por_mes)',
    'Calcular producción anual con irradiación mensual variable por estación:',
    '# Irradiación mensual típica de una ciudad (kWh/m²/mes)\n'
    'irradiacion_meses = [130, 140, 160, 170, 180, 175, 185, 178, 165, 150, 135, 125]\n'
    'potencia_kWp = 3.0\n'
    'pr = 0.80\n'
    'producciones = [potencia_kWp * irr * pr for irr in irradiacion_meses]\n'
    'prod_anual = round(sum(producciones), 1)\n'
    'print("Producción anual:", prod_anual, "kWh/año")')

# ── EJEMPLO INTEGRADOR COMPLETO HSP ──
add_seccion_titulo('EJEMPLO INTEGRADOR COMPLETO — HSP + Irradiancia + Temperatura + Dimensionado')

p_ej2 = doc.add_paragraph()
r_t2 = p_ej2.add_run('Caso: Dimensionar un sistema solar desde cero usando todos los conceptos de HSP')
r_t2.bold = True
r_t2.font.size = Pt(11)
r_t2.font.color.rgb = RGBColor(0x6E, 0x27, 0x94)

codigo_hsp = (
    'import math\n\n'
    '# ── DATOS DEL PROYECTO ──\n'
    'consumo_kwh_dia   = 20.0    # consumo diario del hogar (kWh/día)\n'
    'hsp               = 5.2     # HSP del lugar (dato de NASA POWER o PVGIS)\n'
    'pr                = 0.80    # rendimiento del sistema (80%)\n'
    'potencia_panel_w  = 400     # potencia nominal de cada panel (W)\n'
    'efic_nom          = 0.20    # eficiencia nominal del panel (20%)\n'
    'coef_temp         = -0.0035 # coeficiente de temperatura (/°C)\n'
    'temp_f            = 95      # temperatura ambiente del lugar (°F)\n\n'
    '# ── PASO 1: Convertir temperatura ──\n'
    'temp_c = (temp_f - 32) * 5/9\n'
    'print("Temperatura de operación:", round(temp_c, 1), "°C")\n\n'
    '# ── PASO 2: Eficiencia real según temperatura ──\n'
    'efic_real = efic_nom * (1 + coef_temp * (temp_c - 25))\n'
    'print("Eficiencia real del panel:", round(efic_real * 100, 2), "%")\n\n'
    '# ── PASO 3: Potencia pico necesaria ──\n'
    'potencia_kWp = consumo_kwh_dia / (hsp * pr)\n'
    'print("Potencia pico necesaria:", round(potencia_kWp, 2), "kWp")\n\n'
    '# ── PASO 4: Número de paneles ──\n'
    'potencia_w = potencia_kWp * 1000\n'
    'n_paneles  = math.ceil(potencia_w / potencia_panel_w)\n'
    'print("Paneles necesarios:", n_paneles, "unidades")\n\n'
    '# ── PASO 5: Energía real que generará el sistema ──\n'
    'potencia_real_w  = n_paneles * potencia_panel_w\n'
    'energia_real_wh  = potencia_real_w * hsp * pr\n'
    'energia_real_kwh = energia_real_wh / 1000\n'
    'print("Energía real generada:", round(energia_real_kwh, 2), "kWh/día")\n\n'
    '# ── PASO 6: ¿Cubre el consumo? ──\n'
    'if energia_real_kwh >= consumo_kwh_dia:\n'
    '    excedente = round(energia_real_kwh - consumo_kwh_dia, 2)\n'
    '    print("Sistema suficiente. Excedente:", excedente, "kWh/día")\n'
    'else:\n'
    '    faltante = round(consumo_kwh_dia - energia_real_kwh, 2)\n'
    '    print("Sistema insuficiente. Faltan:", faltante, "kWh/día")\n'
)

p_c2 = doc.add_paragraph()
cr2 = p_c2.add_run(codigo_hsp)
cr2.font.name = 'Courier New'
cr2.font.size = Pt(9.5)
cr2.font.color.rgb = RGBColor(0x10, 0x10, 0x60)

doc.add_paragraph('')

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
