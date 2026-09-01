# -*- coding: utf-8 -*-
"""Matriz real de compatibilidad regional BIPV, portada 1:1 (31-ago-2026,
pedido explicito del usuario) desde `client/src/lib/panelTechnologies.ts`,
la funcion ya viva en produccion en https://bipv.innovacionquimica.com.co/
(otra app del mismo repositorio, stack TypeScript/React -- no se reinventa
el juicio experto, se extrae del que ya existe).

21 familias reales de 3 marcas (HIITIO, EINNOVA, SOLTECH -- esta ultima es
la MISMA marca del panel ASP-ST1-T40 ya usado en el proyecto real Teusaquillo
de esta app), cada una con su score 1-2-3 (no recomendado/aceptable/optimo)
por region climatica de Colombia + nota tecnica real (estructural, estetica,
salinidad, logistica, patrimonio -- no solo energia).

Extraccion verificada programaticamente (node.js evaluando el array real de
panelTechnologies.ts, no transcripcion manual) -- 63 productos reales se
reducen a estas 21 familias porque dentro de cada familia todas las variantes
(distintas potencias/transparencias) comparten la misma compatibilidad regional.
"""

# 1=no recomendado (rojo), 2=aceptable (amarillo), 3=optimo (verde)
COMPATIBILIDAD_REGIONAL_BIPV: dict[str, dict] = {
    "topcon_flex": {
        "tecnologia_jrc": "Crystalline",
        "marca": "hiitio",
        "regional": {"caribe": 3, "andina": 1, "pacifica": 3, "orinoquia": 3, "amazonia": 3, "insular": 3},
        "notas": "23.5% eficiencia, 3 kg/m², coef -0.26%/°C; el todoterreno",
    },
    "hjt_curtain": {
        "tecnologia_jrc": "Crystalline",
        "marca": "hiitio",
        "regional": {"caribe": 3, "andina": 3, "pacifica": 2, "orinoquia": 3, "amazonia": 1, "insular": 3},
        "notas": "Fachadas vidriadas premium; 5400 Pa carga frontal",
    },
    "hjt_tile": {
        "tecnologia_jrc": "Crystalline",
        "marca": "hiitio",
        "regional": {"caribe": 2, "andina": 3, "pacifica": 3, "orinoquia": 2, "amazonia": 1, "insular": 2},
        "notas": "Marco AL estructural; modular; respuesta a difusa",
    },
    "cdte_semit": {
        "tecnologia_jrc": "CdTe",
        "marca": "hiitio",
        "regional": {"caribe": 3, "andina": 3, "pacifica": 2, "orinoquia": 2, "amazonia": 1, "insular": 3},
        "notas": "Lucernarios; Voc 125V cadenas cortas; control térmico",
    },
    "cdte_bipv": {
        "tecnologia_jrc": "CdTe",
        "marca": "hiitio",
        "regional": {"caribe": 3, "andina": 3, "pacifica": 2, "orinoquia": 2, "amazonia": 1, "insular": 3},
        "notas": "Vidrio estructural 5-22 mm; granizo Nivel IV",
    },
    "cigs": {
        "tecnologia_jrc": "CIS",
        "marca": "hiitio",
        "regional": {"caribe": 2, "andina": 3, "pacifica": 2, "orinoquia": 1, "amazonia": 2, "insular": 2},
        "notas": "Patrimonial; ligera 6.5 kg/pieza; baja eficiencia ~10%",
    },
    "einnova_antirreflejo": {
        "tecnologia_jrc": "Crystalline",
        "marca": "einnova",
        "regional": {"caribe": 3, "andina": 3, "pacifica": 3, "orinoquia": 3, "amazonia": 2, "insular": 3},
        "notas": "Mejor captación de difusa; tropicalizado salt-spray",
    },
    "einnova_bifacial": {
        "tecnologia_jrc": "Crystalline",
        "marca": "einnova",
        "regional": {"caribe": 3, "andina": 1, "pacifica": 1, "orinoquia": 3, "amazonia": 1, "insular": 2},
        "notas": "Cubiertas planas, agrovoltaico",
    },
    "einnova_teja_bc": {
        "tecnologia_jrc": "Crystalline",
        "marca": "einnova",
        "regional": {"caribe": 3, "andina": 3, "pacifica": 2, "orinoquia": 1, "amazonia": 1, "insular": 3},
        "notas": "Estética premium; integración patrimonial",
    },
    "einnova_teja_plana": {
        "tecnologia_jrc": "Crystalline",
        "marca": "einnova",
        "regional": {"caribe": 2, "andina": 3, "pacifica": 2, "orinoquia": 1, "amazonia": 1, "insular": 2},
        "notas": "Tejados a dos aguas residenciales",
    },
    "einnova_color_panel": {
        "tecnologia_jrc": "Crystalline",
        "marca": "einnova",
        "regional": {"caribe": 2, "andina": 3, "pacifica": 2, "orinoquia": 2, "amazonia": 1, "insular": 2},
        "notas": "Estética industrial; cubierta+fachada",
    },
    "einnova_fachada": {
        "tecnologia_jrc": "Crystalline",
        "marca": "einnova",
        "regional": {"caribe": 2, "andina": 3, "pacifica": 2, "orinoquia": 1, "amazonia": 1, "insular": 3},
        "notas": "Edificios oficinas/hoteles; varios colores",
    },
    "einnova_flexible": {
        "tecnologia_jrc": "Crystalline",
        "marca": "einnova",
        "regional": {"caribe": 2, "andina": 1, "pacifica": 3, "orinoquia": 1, "amazonia": 3, "insular": 2},
        "notas": "Baja capacidad portante; off-grid amazónico",
    },
    "einnova_agripv": {
        "tecnologia_jrc": "Crystalline",
        "marca": "einnova",
        "regional": {"caribe": 2, "andina": 1, "pacifica": 1, "orinoquia": 3, "amazonia": 2, "insular": 1},
        "notas": "Invernaderos, palma, ganadería",
    },
    "einnova_pavimento": {
        "tecnologia_jrc": "Crystalline",
        "marca": "einnova",
        "regional": {"caribe": 2, "andina": 2, "pacifica": 1, "orinoquia": 2, "amazonia": 1, "insular": 2},
        "notas": "Plazas, estaciones servicio, urbanismo",
    },
    "einnova_vidrio": {
        "tecnologia_jrc": "CdTe",
        "marca": "einnova",
        "regional": {"caribe": 3, "andina": 3, "pacifica": 2, "orinoquia": 2, "amazonia": 1, "insular": 3},
        "notas": "Claraboyas, curtain wall LEED/EDGE",
    },
    "soltech_laminado": {
        "tecnologia_jrc": "CdTe",
        "marca": "soltech",
        "regional": {"caribe": 3, "andina": 2, "pacifica": 3, "orinoquia": 3, "amazonia": 3, "insular": 3},
        "notas": "Tecnología CdTe de película delgada. Coeficiente de temperatura excepcional y excelente respuesta a radiación difusa, óptimo para regiones cálidas y nubladas de Colombia.",
    },
    "soltech_dvh": {
        "tecnologia_jrc": "CdTe",
        "marca": "soltech",
        "regional": {"caribe": 3, "andina": 2, "pacifica": 3, "orinoquia": 3, "amazonia": 3, "insular": 3},
        "notas": "Unidad de Doble Vidrio Hermético (DVH) con CdTe. Ofrece excelente aislamiento térmico (U = 4.89) y alto control solar (factor g = 0.25 a 0.54).",
    },
    "soltech_opaco": {
        "tecnologia_jrc": "CdTe",
        "marca": "soltech",
        "regional": {"caribe": 3, "andina": 2, "pacifica": 3, "orinoquia": 3, "amazonia": 3, "insular": 3},
        "notas": "Módulo de CdTe opaco premium para revestimientos ciegos y antepechos.",
    },
    "soltech_transparente": {
        "tecnologia_jrc": "CdTe",
        "marca": "soltech",
        "regional": {"caribe": 3, "andina": 2, "pacifica": 3, "orinoquia": 3, "amazonia": 3, "insular": 3},
        "notas": "Transparencia equilibrada con captación de energía CdTe.",
    },
    "soltech_teja": {
        "tecnologia_jrc": "CIS",
        "marca": "soltech",
        "regional": {"caribe": 2, "andina": 3, "pacifica": 2, "orinoquia": 1, "amazonia": 2, "insular": 2},
        "notas": "Estética premium colonial. Excelente para la región Andina y zonas patrimoniales.",
    },
}
