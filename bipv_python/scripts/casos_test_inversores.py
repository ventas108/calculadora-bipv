"""
casos_test_inversores.py
Casos de prueba sintéticos para el harness del extractor de inversores.

Cada caso replica el formato EXACTO de la ficha técnica real del fabricante,
basado en el Mapa de Alias INNOVAQ/EINNOVA 2026.

Estructura de cada caso:
    {
        "fabricante": str,       # nombre del fabricante / familia
        "modelo":     str,       # modelo representativo
        "arquitectura": str,     # tipo de inversor
        "texto":      str,       # texto sintético que imita el datasheet real
        "esperado":   dict,      # valores esperados para comparar
    }

Convención para esperado:
    None  → campo legítimamente ausente (N/D) — no se penaliza si extractor retorna None
    valor → se compara con tolerancia ±5%
"""

CASOS = [

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Growatt MID-25KTL3-X — Inversor de red trifásico, 1100 V
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "Growatt",
        "modelo":     "MID-25KTL3-X",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
Growatt MID-25KTL3-X
Three Phase String Inverter

DC INPUT
Maximum PV Input Voltage: 1100V
MPPT Voltage Range: 200V ~ 1000V
Startup Voltage: 200V
Number of MPP trackers: 3
Strings per MPP tracker: 2
Max. PV input current per MPPT: 22A
Max. PV short-circuit current input per MPPT: 27.5A
Max. PV array power: 37500W

AC OUTPUT
Rated Output Power: 25000W
""",
        "esperado": {
            "Vdc_max":           1100,
            "Vmppt_min":         200,
            "Vmppt_max":         1000,
            "V_arranque":        200,
            "n_trackers":        3,
            "n_strings_tracker": 2,
            "I_max_tracker":     22,
            "Isc_max_tracker":   27.5,
            "P_dc_max_W":        37500,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Solis 60K — Inversor de red comercial trifásico, 1100 V
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "Solis",
        "modelo":     "Solis-60K-5G",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
Solis 60K-5G High Power String Inverter

DC Input Data
Max. DC input voltage: 1100V
MPPT voltage range: 200V ~ 1000V
Start-up Voltage: 250V
Number of MPP trackers: 4
Strings per MPP tracker: 3
Max. input current [A]: 40
Max. short circuit current [A]: 50
Max. DC Input Power (W): 78000
""",
        "esperado": {
            "Vdc_max":           1100,
            "Vmppt_min":         200,
            "Vmppt_max":         1000,
            "V_arranque":        250,
            "n_trackers":        4,
            "n_strings_tracker": 3,
            "I_max_tracker":     40,
            "Isc_max_tracker":   50,
            "P_dc_max_W":        78000,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Deye SUN-5K-SG01LP1 — Híbrido residencial (EE.UU.), 500 V
    #    ALIAS ESPECIAL: Full Load DC Voltage Range = V_mppt_activo exacto
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "Deye",
        "modelo":     "SUN-5K-SG01LP1-US",
        "arquitectura": "Híbrido / Off-grid",
        "texto": """\
Deye Hybrid Inverter SUN-5K-SG01LP1-US

PV Input
Max. PV input voltage: 500V
Full Load DC Voltage Range: 300 ~ 430V
MPPT Voltage Range: 120 ~ 430V
Start-up Voltage (V): 125
Number of MPPT inputs: 2
Strings per MPP tracker: 1
Max. PV input current: 15A
Max. PV short-circuit current: 18.75A
Max. PV array power: 7200W

Battery
Battery Voltage Range: 40 ~ 60V
""",
        "esperado": {
            "Vdc_max":           500,
            "Vmppt_min":         120,
            "Vmppt_max":         430,
            "V_mppt_activo":     300,
            "V_arranque":        125,
            "n_trackers":        2,
            "n_strings_tracker": 1,
            "I_max_tracker":     15,
            "Isc_max_tracker":   18.75,
            "P_dc_max_W":        7200,
            "bat_voltaje_min":   40,
            "bat_voltaje_max":   60,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 4. MUST PV3600 TLV — Cargador off-grid puro, 250 V
    #    ALIAS ESPECIAL: V_arranque = N/D legítimo (solo existe voltaje de batería)
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "MUST",
        "modelo":     "PV3600 TLV",
        "arquitectura": "Cargador off-grid puro",
        "texto": """\
MUST PV3600 TLV Solar Inverter/Charger

PV Input
Maximum PV array open circuit voltage: 250 V
MPPT Range @ Operating Voltage: 30-115 V
No. of MPP trackers: 1
Maximum PV Charge Current: 60A
Max. PV array power (W): 3600

Battery
Minimum start voltage: 48 V
""",
        "esperado": {
            "Vdc_max":           250,
            "Vmppt_min":         30,
            "Vmppt_max":         115,
            "V_arranque":        None,   # N/D legítimo — no existe campo PV arranque
            "n_trackers":        1,
            "n_strings_tracker": None,
            "I_max_tracker":     60,
            "Isc_max_tracker":   None,   # N/D — MUST no lo reporta
            "P_dc_max_W":        3600,
            "bat_voltaje_min":   None,   # el "minimum start voltage" es batería, no debe mapearse
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 5. POWEST UPS Híbrida 3.6kW — Cargador off-grid puro, 145 V
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "POWEST",
        "modelo":     "POWEST-UPS-3600",
        "arquitectura": "Cargador off-grid puro",
        "texto": """\
POWEST UPS Híbrida Solar

Entradas FV
Max PV VOC: 145 V
Rango de Operación PV MPPT: 30 ~ 115 V
Maximum PV Charge Current: 30A
Max. PV array power (W): 3600
""",
        "esperado": {
            "Vdc_max":           145,
            "Vmppt_min":         30,
            "Vmppt_max":         115,
            "V_arranque":        None,   # N/D legítimo
            "n_trackers":        None,
            "n_strings_tracker": None,
            "I_max_tracker":     30,
            "Isc_max_tracker":   None,
            "P_dc_max_W":        3600,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 6. SolaX X3-PRO-30K-G2-LV — Inversor de red comercial, 800 V
    #    ALIAS ESPECIAL: P en kWp (no W), trackers en formato N/(S:S:S)
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "SolaX",
        "modelo":     "X3-PRO-30K-G2-LV",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
SolaX X3-PRO-30K-G2-LV Three Phase Inverter

DC Input
Max. PV input voltage [V]: 800
MPP tracker voltage range [V]: 160 ~ 800
Startup voltage: 200V
No. of MPP trackers: 3/(1:1:1)
Max. PV input current [A]: 32
Max. short circuit current [A]: 40
Max. PV array input power [kWp]: 36
""",
        "esperado": {
            "Vdc_max":           800,
            "Vmppt_min":         160,
            "Vmppt_max":         800,
            "V_arranque":        200,
            "n_trackers":        3,
            "n_strings_tracker": 1,
            "I_max_tracker":     32,
            "Isc_max_tracker":   40,
            "P_dc_max_W":        36000,  # 36 kWp × 1000
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 7. LuxPower LXP-LB-US-12K — Híbrido residencial, 600 V
    #    ALIAS ESPECIAL: formato "2 x (2:2)" (Gap 3 corregido)
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "LuxPower",
        "modelo":     "LXP-LB-US-12K",
        "arquitectura": "Híbrido / Off-grid",
        "texto": """\
LuxPower LXP-LB-US-12K Hybrid Inverter

DC Input
Max. PV input voltage (V): 600
MPPT voltage range (V): 80 ~ 550
Start-up Voltage (V): 140
No. of MPP trackers: 3
Strings per MPP tracker: 2 x (2:2)
Max. input current [A]: 25
Max. PV array power (W): 18000

Battery
Battery Voltage Range: 40 ~ 60V
""",
        "esperado": {
            "Vdc_max":           600,
            "Vmppt_min":         80,
            "Vmppt_max":         550,
            "V_arranque":        140,
            "n_trackers":        3,
            "n_strings_tracker": 2,
            "I_max_tracker":     25,
            "Isc_max_tracker":   None,
            "P_dc_max_W":        18000,
            "bat_voltaje_min":   40,
            "bat_voltaje_max":   60,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 8. LuxPower SNA-5000 — Híbrido residencial, 500 V
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "LuxPower SNA",
        "modelo":     "SNA-5000",
        "arquitectura": "Híbrido / Off-grid",
        "texto": """\
LuxPower SNA-5000 Hybrid Inverter

DC Input
Max. PV input voltage (V): 500
MPPT voltage range (V): 80 ~ 450
Start-up Voltage (V): 100
No. of MPP trackers: 2
Strings per MPP tracker: 2/(2:2)
Max. input current [A]: 25
Max. PV array power (W): 7500

Battery
Battery Voltage Range: 40 ~ 60V
""",
        "esperado": {
            "Vdc_max":           500,
            "Vmppt_min":         80,
            "Vmppt_max":         450,
            "V_arranque":        100,
            "n_trackers":        2,
            "n_strings_tracker": 2,
            "I_max_tracker":     25,
            "Isc_max_tracker":   None,
            "P_dc_max_W":        7500,
            "bat_voltaje_min":   40,
            "bat_voltaje_max":   60,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 9. SMA SUNNY BOY 5.0 — Gap 2: min/max DC en líneas separadas
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "SMA",
        "modelo":     "SUNNY BOY 5.0",
        "arquitectura": "Inversor de red monofásico",
        "texto": """\
SMA SUNNY BOY 5.0

DC Input
Maximum input voltage: 850 V
DC voltage range, min.: 125 V
DC voltage range, max.: 750 V
Minimum input voltage (start): 150 V
Number of independent MPPT inputs: 2
Max. input current [A]: 15
DC power, max.: 5400 W
""",
        "esperado": {
            "Vdc_max":           850,
            "Vmppt_min":         125,
            "Vmppt_max":         750,
            "V_arranque":        150,
            "n_trackers":        2,
            "n_strings_tracker": None,
            "I_max_tracker":     15,
            "Isc_max_tracker":   None,
            "P_dc_max_W":        5400,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 10. Fronius SYMO 25.0 — Gap 1: separador "..." en rango MPPT
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "Fronius",
        "modelo":     "SYMO 25.0-3-M",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
Fronius SYMO 25.0-3-M

Technical data
Maximum DC voltage: 1000 V
MPP voltage range: 200...800 V
Start Voltage: 200 V
Number of MPP trackers: 2
Max. input current [A]: 27
Max. DC Input Power (W): 27000
""",
        "esperado": {
            "Vdc_max":           1000,
            "Vmppt_min":         200,
            "Vmppt_max":         800,
            "V_arranque":        200,
            "n_trackers":        2,
            "n_strings_tracker": None,
            "I_max_tracker":     27,
            "Isc_max_tracker":   None,
            "P_dc_max_W":        27000,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 11. Sungrow SG30CX — Gap 4: potencia en kW sin 'p'
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "Sungrow",
        "modelo":     "SG30CX",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
Sungrow SG30CX Multi-MPPT String Inverter

DC Input
Max. DC Input Voltage: 1100 V
MPPT Voltage Range: 200 ~ 1000 V
Startup Voltage: 200 V
Number of MPPT: 3
Max. input current [A]: 25
Recommended maximum PV power: 30 kW
""",
        "esperado": {
            "Vdc_max":           1100,
            "Vmppt_min":         200,
            "Vmppt_max":         1000,
            "V_arranque":        200,
            "n_trackers":        3,
            "n_strings_tracker": None,
            "I_max_tracker":     25,
            "Isc_max_tracker":   None,
            "P_dc_max_W":        30000,  # 30 kW × 1000
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 12–17. SolaX X3-FORTH (familia C&I trifásico, 1100 V)
    #
    # Ficha técnica real: tabla multi-columna con 6 modelos.
    # Campos comunes a todos los modelos:
    #   Vdc_max=1100 V, Vmppt=180~1000 V, V_arranque=200 V,
    #   I_max=32 A, Isc=46 A, n_strings=2
    # Campos que VARÍAN por modelo:
    #   n_trackers: 75K/80K=9, 100K/110K=9 (opt 12), 120K/125K=12
    #   P_dc_max: 120/120/150/165/180/188 kWp
    #
    # Formato del texto sintético: misma línea (real PDF es layout pdftotext)
    #   "Max. PV input voltage   ①\n   1100 d.c. V"  ← nota ① antes del salto
    #   "Max. recommended PV array power   150 kWp"   ← valor en la misma línea
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "SolaX",
        "modelo":     "X3-FTH-75K",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
Three-phase C&I On-grid Inverter

X3-FORTH
75kW / 80kW / 100kW / 110kW / 120kW / 125kW

Max. 12 MPPTs, 2 strings per MPP tracker
32A per MPP tracker
180~1000Vdc MPPT voltage range

solaxpower

PV INPUT
Max. recommended PV array power   120 kWp
Max. PV input voltage   ①
   1100 d.c. V

MPPT voltage range   180 ~ 1000 d.c. V
Start-up voltage   200 d.c. V
No. of MPP trackers / strings per MPP tracker   9 / 2
Max. input current per MPPT   32 d.c. A
Max. input short circuit current per MPPT   46 d.c. A
""",
        "esperado": {
            "Vdc_max":           1100,
            "Vmppt_min":          180,
            "Vmppt_max":         1000,
            "V_arranque":         200,
            "n_trackers":           9,
            "n_strings_tracker":    2,
            "I_max_tracker":       32,
            "Isc_max_tracker":     46,
            "P_dc_max_W":       120000,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },
    {
        "fabricante": "SolaX",
        "modelo":     "X3-FTH-80K",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
Three-phase C&I On-grid Inverter

X3-FORTH
75kW / 80kW / 100kW / 110kW / 120kW / 125kW

Max. 12 MPPTs, 2 strings per MPP tracker
32A per MPP tracker
180~1000Vdc MPPT voltage range

solaxpower

PV INPUT
Max. recommended PV array power   120 kWp
Max. PV input voltage   ①
   1100 d.c. V

MPPT voltage range   180 ~ 1000 d.c. V
Start-up voltage   200 d.c. V
No. of MPP trackers / strings per MPP tracker   9 / 2
Max. input current per MPPT   32 d.c. A
Max. input short circuit current per MPPT   46 d.c. A
""",
        "esperado": {
            "Vdc_max":           1100,
            "Vmppt_min":          180,
            "Vmppt_max":         1000,
            "V_arranque":         200,
            "n_trackers":           9,
            "n_strings_tracker":    2,
            "I_max_tracker":       32,
            "Isc_max_tracker":     46,
            "P_dc_max_W":       120000,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },
    {
        "fabricante": "SolaX",
        "modelo":     "X3-FTH-100K",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
Three-phase C&I On-grid Inverter

X3-FORTH
75kW / 80kW / 100kW / 110kW / 120kW / 125kW

Max. 12 MPPTs, 2 strings per MPP tracker
32A per MPP tracker
180~1000Vdc MPPT voltage range

solaxpower

PV INPUT
Max. recommended PV array power   150 kWp
Max. PV input voltage   ①
   1100 d.c. V

MPPT voltage range   180 ~ 1000 d.c. V
Start-up voltage   200 d.c. V
No. of MPP trackers / strings per MPP tracker   9 / 2
Max. input current per MPPT   32 d.c. A
Max. input short circuit current per MPPT   46 d.c. A
""",
        "esperado": {
            "Vdc_max":           1100,
            "Vmppt_min":          180,
            "Vmppt_max":         1000,
            "V_arranque":         200,
            "n_trackers":           9,
            "n_strings_tracker":    2,
            "I_max_tracker":       32,
            "Isc_max_tracker":     46,
            "P_dc_max_W":       150000,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },
    {
        "fabricante": "SolaX",
        "modelo":     "X3-FTH-110K",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
Three-phase C&I On-grid Inverter

X3-FORTH
75kW / 80kW / 100kW / 110kW / 120kW / 125kW

Max. 12 MPPTs, 2 strings per MPP tracker
32A per MPP tracker
180~1000Vdc MPPT voltage range

solaxpower

PV INPUT
Max. recommended PV array power   165 kWp
Max. PV input voltage   ①
   1100 d.c. V

MPPT voltage range   180 ~ 1000 d.c. V
Start-up voltage   200 d.c. V
No. of MPP trackers / strings per MPP tracker   12 / 2
Max. input current per MPPT   32 d.c. A
Max. input short circuit current per MPPT   46 d.c. A
""",
        "esperado": {
            "Vdc_max":           1100,
            "Vmppt_min":          180,
            "Vmppt_max":         1000,
            "V_arranque":         200,
            "n_trackers":          12,
            "n_strings_tracker":    2,
            "I_max_tracker":       32,
            "Isc_max_tracker":     46,
            "P_dc_max_W":       165000,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },
    {
        "fabricante": "SolaX",
        "modelo":     "X3-FTH-120K",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
Three-phase C&I On-grid Inverter

X3-FORTH
75kW / 80kW / 100kW / 110kW / 120kW / 125kW

Max. 12 MPPTs, 2 strings per MPP tracker
32A per MPP tracker
180~1000Vdc MPPT voltage range

solaxpower

PV INPUT
Max. recommended PV array power   180 kWp
Max. PV input voltage   ①
   1100 d.c. V

MPPT voltage range   180 ~ 1000 d.c. V
Start-up voltage   200 d.c. V
No. of MPP trackers / strings per MPP tracker   12 / 2
Max. input current per MPPT   32 d.c. A
Max. input short circuit current per MPPT   46 d.c. A
""",
        "esperado": {
            "Vdc_max":           1100,
            "Vmppt_min":          180,
            "Vmppt_max":         1000,
            "V_arranque":         200,
            "n_trackers":          12,
            "n_strings_tracker":    2,
            "I_max_tracker":       32,
            "Isc_max_tracker":     46,
            "P_dc_max_W":       180000,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },
    {
        "fabricante": "SolaX",
        "modelo":     "X3-FTH-125K",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
Three-phase C&I On-grid Inverter

X3-FORTH
75kW / 80kW / 100kW / 110kW / 120kW / 125kW

Max. 12 MPPTs, 2 strings per MPP tracker
32A per MPP tracker
180~1000Vdc MPPT voltage range

solaxpower

PV INPUT
Max. recommended PV array power   188 kWp
Max. PV input voltage   ①
   1100 d.c. V

MPPT voltage range   180 ~ 1000 d.c. V
Start-up voltage   200 d.c. V
No. of MPP trackers / strings per MPP tracker   12 / 2
Max. input current per MPPT   32 d.c. A
Max. input short circuit current per MPPT   46 d.c. A
""",
        "esperado": {
            "Vdc_max":           1100,
            "Vmppt_min":          180,
            "Vmppt_max":         1000,
            "V_arranque":         200,
            "n_trackers":          12,
            "n_strings_tracker":    2,
            "I_max_tracker":       32,
            "Isc_max_tracker":     46,
            "P_dc_max_W":       188000,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # SAJ R6 — etiquetas en español con unidad entre corchetes [V]/[A]/[Wp]@STC
    # (valores por modelo en columnas y listas con "/")
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "SAJ",
        "modelo":     "R6-20K-T3-32-LV",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
SAJ R6 Series
Model R6-20K-T3-32-LV R6-25K-T4-32-LV R6-30K-T4-32-LV
Potencia máxima FV [Wp]@STC 30000 37500 45000
Tensión máxima de entrada [V] 1100
Rango de tensión MPPT [V] 180~1000
Tensión nominal de entrada [V] 370
Tensión de arranque [V] 200
Corriente máxima de entrada [A] 32/32/32 32/32/32/32
Corriente máxima de cortocircuito CC [A] 38.4/38.4/38.4 38.4/38.4/38.4/38.4
No. de cadenas por MPPT 2/2/2 2/2/2/2
No. de MPPT 3 4 4
Corriente de salida CA nominal [A] a 230 VCA 52.5 65.6 78.7
""",
        "esperado": {
            "Vdc_max":           1100,
            "Vmppt_min":          180,
            "Vmppt_max":         1000,
            "V_mppt_activo":      370,
            "V_arranque":         200,
            "n_trackers":           3,
            "n_strings_tracker":    2,
            "I_max_tracker":       32,
            "Isc_max_tracker":   38.4,
            "P_dc_max_W":       30000,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # Growatt MID 15-25KTL3-X — "Normal Voltage" como rango MPPT (con línea CA
    # adversarial cerca), rango de un solo valor → MPPT activo, pseudo-rango
    # "27A 27A" que no debe tomarse como rango, e Isc con etiqueta partida
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "Growatt",
        "modelo":     "MID-25KTL3-X (formato Normal Voltage)",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
Growatt MID 15-25KTL3-X
Max. DC voltage 1100V
Start Voltage 250V
Normal Voltage 200V-1000V
MPPT voltage range 580V
No. of MPP trackers/strings per
MPP tracker 2/2 2/2 2/2 2/2 2/3
Max.input current per MPP tracker 27A 27A 27A 27A 27A/40.5A
Max. short-circuit current per
MPP tracker 33.8A 33.8A 33.8A 33.8A 33.8A/50.6A
AC output
Normal Voltage 230/400VAC
Max. AC apparent power 16600VA 18800VA 22000VA 24400VA 27700VA
""",
        "esperado": {
            "Vdc_max":           1100,
            "Vmppt_min":          200,
            "Vmppt_max":         1000,
            "V_mppt_activo":      580,
            "V_arranque":         250,
            "n_trackers":           2,
            "n_strings_tracker": None,  # etiqueta partida "trackers/strings per\\nMPP tracker 2/2" — no soportada aún
            "I_max_tracker":       27,
            "Isc_max_tracker":   33.8,
            "P_dc_max_W":        None,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # Deye TriP2-LB-3P — nombres de modelo partidos en dos líneas, unidad en la
    # etiqueta "(V) 690", corrientes por MPPT con listas "/" y P_dc por columna
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "Deye",
        "modelo":     "TriP2-LB-3P 5K",
        "arquitectura": "Inversor híbrido trifásico",
        "texto": """\
HYBRID SERIES
Three Phase Hybrid Inverter
Model TriP2-LB- TriP2-LB- TriP2-LB- TriP2-LB- TriP2-LB- TriP2-LB- TriP2-LB-
3P 5K 3P 6K 3P 8K 3P 10K 3P 12K 3P 15K 3P 20K
Max. PV input power (W) 7500 9000 12000 15000 18000 22500 30000
Rated PV input voltage (V) 690
Max. PV input voltage (V) 1000
MPPT voltage range (V) 200 ~ 900
Start-up voltage (V) 100
Number of independent MPPT inputs 3 / (1:1:1)
Max. PV input current per MPPT (A) 20 / 20 / 20
Max. PV short-circuit current input per MPPT 25 / 25 / 25
Battery voltage range (V) 40 - 60
""",
        "esperado": {
            "Vdc_max":           1000,
            "Vmppt_min":          200,
            "Vmppt_max":          900,
            "V_mppt_activo":      690,
            "V_arranque":         100,
            "n_trackers":           3,
            "n_strings_tracker":    1,
            "I_max_tracker":       20,
            "Isc_max_tracker":     25,
            "P_dc_max_W":        None,   # global ausente; por modelo 7500-30000
            "bat_voltaje_min":     40,
            "bat_voltaje_max":     60,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # Voltronic InfiniSolar — folleto de familia con secciones "MODEL <nombre>"
    # y etiquetas dobles con "/" (Nominal/Max, Start-up/Initial, Trackers/Imax)
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "Voltronic",
        "modelo":     "InfiniSolar 2KW",
        "arquitectura": "Inversor híbrido",
        "texto": """\
InfiniSolar Hybrid Inverter
MODEL InfiniSolar 2KW
Maximum PV Input Power 2250W
Nominal DC Voltage / Maximum DC Voltage 300 VDC / 350 VDC
Start-up Voltage / Initial Feeding Voltage 80 VDC / 120 VDC
MPP Voltage Range 150 VDC ~ 320 VDC
Number of MPP Trackers / Maximum Input Current 1 / 1 x 15 A
Output Voltage Range 88 - 127 VAC*
""",
        "esperado": {
            "Vdc_max":            350,
            "Vmppt_min":          150,
            "Vmppt_max":          320,
            "V_arranque":          80,
            "n_trackers":           1,
            "I_max_tracker":       15,
            "Isc_max_tracker":   None,
            "P_dc_max_W":        2250,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CASO LÍMITE: tabla de 2 columnas — cada etiqueta en una línea y el valor
    # (con su unidad) en la línea siguiente. Típico de pdfplumber al leer tablas
    # con celdas combinadas.
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "Genérico (tabla 2 columnas)",
        "modelo":     "GenericSun 30K",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
Inversor Trifásico GenericSun 30K
DC Input
Max. DC voltage
1100 V
MPPT voltage range
180 - 1000 V
Start-up voltage
195 V
Number of MPP trackers
3
Strings per MPP tracker
2
Max. input current per MPPT
32 A
Max. short-circuit current per MPPT
40 A
Max. PV array power
45000 W
""",
        "esperado": {
            "Vdc_max":           1100,
            "Vmppt_min":          180,
            "Vmppt_max":         1000,
            "V_arranque":         195,
            "n_trackers":           3,
            "n_strings_tracker":    2,
            "I_max_tracker":       32,
            "Isc_max_tracker":     40,
            "P_dc_max_W":       45000,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CASO LÍMITE: número de trackers opcional "9 or 12" (X3-FTH-100K).
    # El extractor debe tomar el valor conservador (9), nunca fallar en None.
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "Genérico (trackers opcionales)",
        "modelo":     "X3-FTH-100K (9 or 12)",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
SolarMax X3-FTH-100K
Max. DC input voltage 1100V
MPPT voltage range 180V-1000V
Start-up voltage 200V
No. of MPP trackers 9 or 12
Strings per MPP tracker 2
Max. input current per MPPT 32A
Max. short circuit current per MPPT 46A
Max. recommended PV array power 150 kWp
""",
        "esperado": {
            "Vdc_max":           1100,
            "Vmppt_min":          180,
            "Vmppt_max":         1000,
            "V_arranque":         200,
            "n_trackers":           9,    # conservador: el menor de "9 or 12"
            "n_strings_tracker":    2,
            "I_max_tracker":       32,
            "Isc_max_tracker":     46,
            "P_dc_max_W":      150000,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CASO LÍMITE: fila combinada "trackers / strings per MPP tracker 3 / 2" —
    # el primer número es el conteo de trackers, NO las cadenas. El patrón sin
    # separador de n_strings no debe capturar el 3.
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "Genérico (fila combinada)",
        "modelo":     "ComboRow 25K",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
ComboRow 25K Three Phase Inverter
Max. DC voltage 1100V
MPPT voltage range 200V-1000V
Start-up voltage 250V
No. of MPP trackers / strings per MPP tracker 3 / 2
Max. input current per MPPT 26A
Max. short-circuit current per MPPT 33A
Max. PV array power 37500W
""",
        "esperado": {
            "Vdc_max":           1100,
            "Vmppt_min":          200,
            "Vmppt_max":         1000,
            "V_arranque":         250,
            "n_trackers":           3,
            "n_strings_tracker":    2,
            "I_max_tracker":       26,
            "Isc_max_tracker":     33,
            "P_dc_max_W":       37500,
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CASO LÍMITE: la ficha NO publica potencia FV máxima — solo potencia AC
    # nominal. El extractor debe estimarla (AC × 1.5) y marcarla como estimada,
    # nunca dejar el campo vacío en silencio.
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "Genérico (sin P_dc publicada)",
        "modelo":     "PowerInv 20K",
        "arquitectura": "Inversor de red trifásico",
        "texto": """\
PowerInv 20K Three Phase Inverter
Max. DC voltage 1100V
MPPT voltage range 200V-1000V
Start Voltage 250V
No. of MPP trackers 2
Strings per MPP tracker 2
Max. input current per MPPT 27A
Max. short-circuit current 34A
AC OUTPUT
Rated AC output power 20000 W
Nominal output voltage 400V
""",
        "esperado": {
            "Vdc_max":           1100,
            "Vmppt_min":          200,
            "Vmppt_max":         1000,
            "V_arranque":         250,
            "n_trackers":           2,
            "n_strings_tracker":    2,
            "I_max_tracker":       27,
            "Isc_max_tracker":     34,
            "P_dc_max_W":       30000,   # estimada: 20000 AC × 1.5
            "bat_voltaje_min":   None,
            "bat_voltaje_max":   None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 26. ECO HYBRID SNA2-EU-LT 10-14K — híbrido monofásico. Formato crítico:
    # los 3 modelos comparten el nombre base y el diferenciador (10K/12K/14K)
    # es un token que empieza con dígito en la MISMA línea del encabezado.
    # Además la potencia FV trae el desglose por MPPT entre paréntesis, que
    # NO debe confundirse con la potencia total del modelo.
    # ─────────────────────────────────────────────────────────────────────────
    {
        "fabricante": "ECO HYBRID (SNA2)",
        "modelo":     "SNA2-EU-LT 10K",
        "arquitectura": "Híbrido monofásico",
        "texto": """\
ECO HYBRID
SNA2-EU-LT 10-14K
(Single-Phase)
Model SNA2-EU-LT 10K SNA2-EU-LT 12K SNA2-EU-LT 14K
Input (PV DC)
Max. PV input power (W) 18000 (9000/9000) 24000 (12000/12000)
Rated PV input voltage (V) 320
Number of independent MPPT inputs 2 / (2:2)
Max. PV input voltage (V) 480
MPPT voltage range (V) 120 ~ 440
Start-up voltage (V) 100
Max. PV input current per MPPT (A) 26 / 26 35 / 35
Max. PV short-circuit current input per MPPT (A) 32.5 / 32.5 44 / 44
Battery
Rated battery voltage (V) 48 / 51.2
Battery voltage range (V) 46.4 ~ 60 / 38.4 ~ 60
""",
        "esperado": {
            "Vdc_max":           480,
            "Vmppt_min":         120,
            "Vmppt_max":         440,
            "V_mppt_activo":     320,
            "V_arranque":        100,
            "n_trackers":          2,
            "n_strings_tracker":   2,
            "I_max_tracker":      26,
            "Isc_max_tracker":  32.5,
            "P_dc_max_W":       None,   # va por modelo (valores_por_modelo)
            "bat_voltaje_min":  46.4,
            "bat_voltaje_max":    60,
        },
    },

]

# Campos que se comparan (ordenados para la tabla de cobertura)
CAMPOS_CRITICOS = [
    "Vdc_max", "Vmppt_min", "Vmppt_max", "V_mppt_activo",
    "V_arranque", "n_trackers", "n_strings_tracker",
    "I_max_tracker", "Isc_max_tracker", "P_dc_max_W",
    "bat_voltaje_min", "bat_voltaje_max",
]

# Etiquetas legibles para la UI
CAMPO_LABELS = {
    "Vdc_max":           "Vdc máx (V)",
    "Vmppt_min":         "MPPT mín (V)",
    "Vmppt_max":         "MPPT máx (V)",
    "V_mppt_activo":     "MPPT activo (V)",
    "V_arranque":        "V arranque (V)",
    "n_trackers":        "N trackers",
    "n_strings_tracker": "Strings/tracker",
    "I_max_tracker":     "I máx (A)",
    "Isc_max_tracker":   "Isc máx (A)",
    "P_dc_max_W":        "P FV máx (W)",
    "bat_voltaje_min":   "Bat mín (V)",
    "bat_voltaje_max":   "Bat máx (V)",
}
