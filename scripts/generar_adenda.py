
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

# Pie de página
doc.add_paragraph('')
footer = doc.add_paragraph('Elaborado para curso de Python aplicado a Energía Solar Fotovoltaica — 2026')
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer.runs[0].font.size = Pt(9)
footer.runs[0].font.color.rgb = RGBColor(0x7F, 0x7F, 0x7F)
footer.runs[0].italic = True

doc.save('Adenda_Python_Fotovoltaico.docx')
print("Documento creado correctamente.")
