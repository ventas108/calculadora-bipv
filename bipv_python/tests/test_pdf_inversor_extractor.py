"""
Regresión: motor de extracción de fichas técnicas de inversores.

Bugs reales encontrados el 30-ago-2026 auditando las 3 fichas reales pedidas
por el usuario (MUST PV3500/PV3600 TLV Series, distribuidas por Solis
Colombia): `C:\\Users\\Mauricio\\Desktop\\TODO FICHAS TECNICAS BIPV\\TODO
INVERSORES\\INVERORES SOLIS COLOMBIA\\HIBRIDOS  MARCA MUST DE SOLIS`.

Ver DIAGNOSTICO_EXTRACCION_INVERSORES_MUST.md para el detalle completo,
incluido el hallazgo más importante (no es un bug de código): el archivo
"Inversor-Hibrido-12000W-...-PV35-...-Must.pdf" contiene en realidad la
ficha de la serie PV3600 (PV36-8048/10048/12048 TLV), no PV35-12048 TLV --
un problema de archivo mal nombrado en el escritorio del usuario, no del
extractor.
"""
import calculos.pdf_inversor_extractor as ext

# Extracto real de la ficha MUST PV3500 TLV Series (texto tal como lo
# devuelve pdfplumber, incluido el typo real del fabricante "Maximim").
TEXTO_MUST_PV3500 = """
Low Frequency Solar Inverter
PV3500 TLV Series (8KW-12KW)
Specification
Features MODEL PV35-8048 TLV PV35-10048 TLV PV35-12048 TLV
Nominal Battery System Voltage 48VDC 48VDC 48VDC
Rated power 8.0KW 10.0KW 12.0KW
INVERTER
Maximum PV charge current 100A
DC voltage 48V
Maximim PV array power 5000W(10000W for 200A optional)
MPPT range @ operating voltage(VDC) 64~145VDC
Maximum PV array open circuit voltage 145VDC
"""


def test_extrae_p_dc_max_con_typo_maximim_del_fabricante():
    # Bug real: la ficha MUST trae "Maximim" (no "Maximum") -- ningún patrón
    # "Max(?:imum)?" existente lo cubría, dejando P_dc_max_W en None pese a
    # que el valor (5000W) está impreso con claridad.
    valor = ext._find(ext._PAT_PDCMAX, TEXTO_MUST_PV3500)
    assert valor == 5000.0


def test_extrae_p_dc_max_con_maximum_correcto_sigue_funcionando():
    # El patrón nuevo no debe romper el caso normal (ortografía correcta).
    texto = "Maximum PV array power 6000W"
    valor = ext._find(ext._PAT_PDCMAX, texto)
    assert valor == 6000.0


def test_modelo_no_confunde_encabezado_inverter_con_codigo_de_modelo():
    # Bug real: "INVERTER" es un encabezado de sección de tabla que aparece
    # como línea aislada tras la extracción de pdfplumber -- se confundía
    # con un código de modelo real (cumple la forma "todo mayúsculas,
    # 5-35 caracteres").
    modelo = ext._extract_model(TEXTO_MUST_PV3500, "")
    assert modelo != "INVERTER"


def test_modelo_generico_no_incluye_encabezados_de_seccion_comunes():
    for header in ("OUTPUT", "BATTERY", "SPECIFICATIONS", "MECHANICAL"):
        texto = f"Datasheet\n{header}\nAlgo de contenido\n"
        modelo = ext._extract_model(texto, "")
        assert modelo != header


def test_multimodelo_detecta_los_3_modelos_reales_pv35():
    resultado = ext._extraer_multimodelo(TEXTO_MUST_PV3500)
    assert resultado["modelos"] == ["PV35-8048", "PV35-10048", "PV35-12048"]


# Extracto real de la ficha MUST PV3300 TLV Series -- la sección de entrada
# AC (red/generador) trae "Max input voltage 270Vac MAX", un voltaje de
# CORRIENTE ALTERNA, en una línea con la misma forma "Max ... input voltage"
# que usan las fichas DC reales -- root cause del bug real de Vdc_max=270.
TEXTO_MUST_PV3300_SECCION_AC = """
AC Input Nominal input voltage 200Vac / 220Vac / 240Vac
Max input voltage 270Vac MAX
Input frequency 50Hz / 60Hz (auto sensing)
Maximum Solar Input Voltage 100±2Vdc / 145±2Vdc 145±2Vdc 145±2Vdc
Solar MPPT Range @ Operating Voltage 16~95VDC @ 12V / 30~130VDC @ 24V
"""


def test_vdc_max_no_confunde_voltaje_ac_de_red_con_voltaje_dc_fv():
    # Bug real (ficha MUST PV3300): "Max input voltage 270Vac MAX" es la
    # tensión AC máxima de red/generador -- NO debe leerse como Vdc_max. El
    # patrón anterior no distinguía "Input voltage" AC de DC y devolvía 270.
    valor = ext._find(ext._PAT_VDCMAX, TEXTO_MUST_PV3300_SECCION_AC)
    assert valor != 270.0
    assert valor is None or valor != 270


def test_campos_extraidos_completos_para_ficha_must_pv3500():
    campos = ext._extraer_campos(TEXTO_MUST_PV3500)
    assert campos["Vdc_max"] == 145.0
    assert campos["Vmppt_min"] == 64.0
    assert campos["Vmppt_max"] == 145.0
    assert campos["I_max_tracker"] == 100.0
    assert campos["P_dc_max_W"] == 5000.0
