# -*- coding: utf-8 -*-
"""Ficha Técnica Preliminar — Proyecto agrivoltaico Urabá (v2, config eléctrica optimizada)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

AZUL, VERDE, GRIS = "#1B4F72", "#1E8449", "#555555"

def pagina(pdf, titulo, bloques):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.text(0.06, 0.965, "FICHA TÉCNICA PRELIMINAR — v2 (config. eléctrica optimizada)",
             fontsize=9, color=GRIS)
    fig.text(0.06, 0.935, titulo, fontsize=16, fontweight="bold", color=AZUL)
    fig.text(0.94, 0.965, "Proyecto Agrivoltaico Urabá · agosto 2026", fontsize=9,
             color=GRIS, ha="right")
    y = 0.90
    for tipo, contenido in bloques:
        if tipo == "h":
            y -= 0.012
            fig.text(0.06, y, contenido, fontsize=12, fontweight="bold", color=VERDE)
            y -= 0.022
        elif tipo == "t":
            for fila in contenido:
                fig.text(0.07, y, fila[0], fontsize=9.3, color="#222222")
                fig.text(0.47, y, fila[1], fontsize=9.3, fontweight="bold", color="#111111",
                         wrap=True)
                y -= 0.0185
            y -= 0.008
        elif tipo == "p":
            for linea in contenido:
                fig.text(0.07, y, linea, fontsize=8.6, color="#333333")
                y -= 0.0165
            y -= 0.008
    fig.text(0.5, 0.03, "Documento preliminar para cotización — no constituye ingeniería de detalle · "
             "Innovación Química", fontsize=8, color=GRIS, ha="center")
    pdf.savefig(fig); plt.close(fig)

with PdfPages("entregables/Ficha_Tecnica_Preliminar_Agrivoltaico_Uraba.pdf") as pdf:

    pagina(pdf, "1. Sitio, generador FV y estructura", [
        ("h", "Emplazamiento"),
        ("t", [
            ("Ubicación", "Apartadó, Urabá antioqueño, Colombia"),
            ("Coordenadas / altitud", "7.884° N, −76.635° O · 30 m s.n.m."),
            ("Terreno", "3.200 m² (32 m N-S × 100 m E-O)"),
            ("Uso del suelo", "Agrivoltaico — cultivo bajo y entre paneles"),
            ("Viento / nieve de diseño", "30 m/s (por confirmar NSR-10) · 0 kN/m²"),
        ]),
        ("h", "Generador fotovoltaico"),
        ("t", [
            ("Módulo", "JA Solar JAM66D46-720/LB · bifacial n-type"),
            ("Potencia / cantidad", "720 Wp × 306 módulos = 220,32 kWp DC"),
            ("Dimensiones / peso", "2384 × 1303 × 33 mm · ~38,5 kg"),
            ("Degradación garantizada", "≤1% año 1 · ≤0,4%/año · ~87,8% a 30 años"),
        ]),
        ("h", "Configuración eléctrica preliminar (optimizada por simulación)"),
        ("t", [
            ("Arreglo DC", "17 strings de 18 módulos (1 por matriz)"),
            ("Tensión de string", "Voc ≈ 882 V · Vmp ≈ 738 V (límite equipo 1.100–1.500 V)"),
            ("Corriente por string", "Imp ≈ 17,6 A → entradas MPPT ≥18 A, 1 string por tracker"),
            ("Inversores", "2 × 80–90 kW AC (clase string, 1.500 V)"),
            ("Ratio DC/AC", "1,22–1,38 · clipping simulado ≤0,24%"),
            ("Candidatos verificados ~100 kW", "Huawei 100KTL-M1 · Sungrow SG110CX · Growatt MAX 100 (penalización <1%)"),
        ]),
        ("p", ["El barrido horario de ratio DC/AC mostró que el pico real del campo es ~192 kW AC;",
               "2×80–90 kW maximiza TIR y minimiza LCOE sin pérdida apreciable de energía.",
               "La redundancia de 2 equipos conserva ~50% de producción ante falla de uno."]),
        ("h", "Estructura y disposición agrivoltaica"),
        ("t", [
            ("Matrices", "17 matrices de 2×9 módulos apaisados"),
            ("Altura libre bajo panel", "3,0 m (maquinaria y cultivo)"),
            ("Inclinación / orientación", "10° · azimut Sur"),
            ("Factor de ocupación", "30% — corredores de cultivo ~4 m, pasillos 2,8 m"),
            ("Cimentación", "Tornillo de tierra + acero ZAM (requiere estudio de suelo)"),
        ]),
    ])

    pagina(pdf, "2. Producción estimada (simulación horaria)", [
        ("h", "Método"),
        ("p", ["Simulación horaria de 8.760 h con año meteorológico típico PVGIS para el punto exacto",
               "(7.884, −76.635): transposición Hay-Davies al plano 10° Sur, temperatura de celda por",
               "modelo Faiman, coeficiente −0,30%/°C, ganancia bifacial +8%, pérdidas DC combinadas 8%",
               "(soiling, mismatch, cableado), eficiencia de inversor 98,2–98,4% y clipping AC real.",
               "Reemplaza la estimación anterior por método HSP×PR (368 MWh/año), que resultaba optimista",
               "para la nubosidad real del Urabá. Esta cifra es la defendible ante banca."]),
        ("h", "Resultados anuales"),
        ("t", [
            ("Energía AC año 1", "≈ 278.600 kWh/año"),
            ("Yield específico", "≈ 1.265 kWh/kWp·año"),
            ("Pico AC real del campo", "≈ 192 kW (nunca alcanza los 220 kWp nominales)"),
            ("Clipping con 2×80 kW", "0,24% (≈670 kWh/año)"),
            ("Producción año 25 (degradación)", "≈ 253.000 kWh/año"),
            ("Energía acumulada 25 años", "≈ 6,65 GWh"),
        ]),
        ("h", "Sinergia agrivoltaica"),
        ("t", [
            ("Suelo libre para cultivo", "≈ 2.250 m² (70% del terreno)"),
            ("Ganancia bifacial", "+8% por albedo del cultivo y altura de 3,0 m"),
        ]),
        ("p", ["Nota: la cifra contractual definitiva debe salir de la Calculadora BIPV (Motor IV con la",
               "curva del módulo + bypass diodes si hay sombras) una vez cerrado el layout final."]),
    ])

    pagina(pdf, "3. Estimación financiera preliminar", [
        ("h", "Supuestos declarados"),
        ("t", [
            ("TRM / tarifa", "COP 4.000/USD · 950 COP/kWh (EPM, 100% autoconsumo)"),
            ("Vida útil / degradación", "25 años · 0,4%/año"),
            ("OPEX", "10 USD/kWp·año"),
            ("Precios de inversor", "Referencia de mercado — pendiente cotización local"),
        ]),
        ("h", "Inversión (sin BOM oficial — rangos de mercado)"),
        ("t", [
            ("Costos duros", "≈ 0,68 USD/Wp (módulos, estructura elevada 3 m, 2 inversores 80–90 kW, BOS, montaje)"),
            ("Costos blandos (17%)", "Ingeniería, trámites UPME/RETIE, interventoría, imprevistos"),
            ("CAPEX central", "≈ USD 176.300 ≈ 0,80 USD/Wp ≈ COP 705 M"),
            ("Rango (±16%)", "USD 148.000 – 205.000"),
        ]),
        ("h", "Indicadores (simulación horaria + flujo de caja 25 años)"),
        ("t", [
            ("Ahorro año 1", "≈ COP 264,7 M (278.600 kWh × 950 COP)"),
            ("TIR", "≈ 35,8%"),
            ("VPN (tasa 10%)", "≈ USD 385.000"),
            ("Payback simple", "≈ 2,8 años"),
            ("LCOE", "≈ 0,080 USD/kWh ≈ 321 COP/kWh (vs tarifa 950)"),
        ]),
        ("h", "Beneficios Ley 1715/2014 (no incluidos arriba — mejoran los indicadores)"),
        ("t", [
            ("Art. 11", "Deducción del 50% de la inversión en renta (hasta 15 años)"),
            ("Art. 12 / 13", "Exclusión de IVA y exención arancelaria de equipos"),
            ("Art. 14", "Depreciación acelerada hasta 33,3% anual"),
        ]),
        ("p", ["Los indicadores asumen 100% de autoconsumo; si parte de la energía se exporta como",
               "excedentes (Res. CREG 174/2021), el retorno se reduce según la tarifa de venta.",
               "Pendientes para pasar a ingeniería: estudio de suelo (tornillo), confirmación de viento",
               "NSR-10, cotizaciones reales de inversores 80–90 kW y del BOM completo."]),
    ])

print("OK")
