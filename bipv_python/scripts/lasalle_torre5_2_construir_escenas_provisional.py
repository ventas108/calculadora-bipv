# -*- coding: utf-8 -*-
"""Construye las escenas Site Designer PROVISIONALES para Torre 5, Bosques de
Castilla. TODAS las magnitudes no medidas quedan marcadas explicitamente.
No se presenta ningun archivo como "exportado" -- son reconstrucciones."""
import json
import hashlib
from pathlib import Path

LAT, LON, ELEV_M = 4.634, -74.148, 2550.0
NORTH_OFFSET = 160.5  # VERIFICADO numericamente en derivar_geometria.py

ANCHO_SE_MM = 17290.5   # MEDIDO: Fig. 4 tesis (cota AutoCAD, cara sureste)
ALTO_MM = 36417.8       # MEDIDO: Fig. 4 tesis
ANCHO_SO_MM_CENTRAL = 17290.5  # ASUMIDO = ancho SE (ver informe, sensibilidad abajo)

OUT = Path("/tmp/claude-1000/-workspaces-calculadora-bipv/a911aa20-79cb-4c25-9d11-10e46335b71c/scratchpad/geom")

def escena_base(ancho_so_mm, bloques_extra=None, etiqueta=""):
    bloques = [
        {
            "min": [0, 0, 0],
            "max": [ancho_so_mm, ANCHO_SE_MM, ALTO_MM],
            "color": [0.55, 0.55, 0.6, 1],
            "majorAxis": 0, "fixedSize": 0, "isSolid": True, "group": 0,
            "blockSubclass": "TowerBlock",
            "nombre_provisional": f"Torre5_reconstruccion_provisional{etiqueta}",
        }
    ]
    if bloques_extra:
        bloques.extend(bloques_extra)
    return {
        "Location": {
            "latitude": LAT, "longitude": LON, "timezone": -5,
            "northOffset": NORTH_OFFSET, "elevation": ELEV_M,
        },
        "Blocks": bloques,
        "_metadatos_reconstruccion_provisional": {
            "clasificacion": "B - reconstruccion provisional, NO exportada de Site Designer",
            "fuente_ancho_SE": "Fig. 4 tesis La Salle 2021, p.35 (cota AutoCAD, medido)",
            "fuente_alto": "Fig. 4 tesis La Salle 2021, p.35 (cota AutoCAD, medido, consistente con 13 pisos x 2.80m)",
            "ancho_SO_mm": ancho_so_mm,
            "ancho_SO_supuesto": ancho_so_mm == ANCHO_SO_MM_CENTRAL,
            "north_offset_derivacion": "idealiza esquina real 87 grados a 90 grados exactos (reparto 1.5 grados por cara), verificado numericamente con trimesh en derivar_geometria.py",
        },
    }

def guardar(nombre, data):
    ruta = OUT / nombre
    texto = json.dumps(data, indent=2, ensure_ascii=False)
    ruta.write_text(texto, encoding="utf-8")
    sha = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    print(f"{nombre}: SHA-256={sha}")
    return ruta, sha

# Variante 1 (PRIMARIA): solo torre, footprint asumido cuadrado (SO=SE)
guardar("torre_central.json", escena_base(ANCHO_SO_MM_CENTRAL, etiqueta="_central"))

# Sensibilidad ancho SO: angosto (12 m) y ancho (25 m)
guardar("torre_so_estrecha_12m.json", escena_base(12000.0, etiqueta="_so12m"))
guardar("torre_so_ancha_25m.json", escena_base(25000.0, etiqueta="_so25m"))

# Variante secundaria: torre + arboles (SO, pisos 1-3), parametros centrales
# ASUMIDOS: retranqueo (setback) 3 m, profundidad de copa 3 m, altura 6 m
# (dentro del rango 5-7 m que SI da la tesis)
SETBACK_MM, PROFUNDIDAD_MM, ALTURA_ARBOL_MM = 3000.0, 3000.0, 6000.0
arbol = {
    "min": [ANCHO_SO_MM_CENTRAL + SETBACK_MM, 0, 0],
    "max": [ANCHO_SO_MM_CENTRAL + SETBACK_MM + PROFUNDIDAD_MM, ANCHO_SE_MM, ALTURA_ARBOL_MM],
    "color": [0.1, 0.5, 0.15, 1], "majorAxis": 0, "fixedSize": 0, "isSolid": True,
    "group": 1, "isTree": True, "blockSubclass": "TreeBlock",
    "nombre_provisional": "Arboles_SO_pisos1-3_ASUMIDO_setback3m_profundidad3m_altura6m",
}
guardar("torre_mas_arboles_central.json", escena_base(ANCHO_SO_MM_CENTRAL, [arbol], etiqueta="_con_arboles"))

print("\nListo.")
