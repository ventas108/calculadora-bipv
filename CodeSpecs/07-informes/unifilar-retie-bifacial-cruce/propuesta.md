# Propuesta — Unifilar y RETIE coherentes con Motor Óptico, Mismatch y Vista 3D

**Estado:** validación

## Objetivo

Que el Unifilar y la ficha RETIE dimensionen con las mismas condiciones
físicas que ya usan la energía y el diseño eléctrico: cara trasera del panel
bifacial, módulos donde están y pérdidas de cableado que de verdad aplica
Producción.

## Alternativa recomendada

Aprobada por el usuario el 29-sep-2026 («implementa las correcciones
correspondientes … en el Módulo Diagrama Unifilar y ficha validación RETIE»,
«incluye lo nuevo de Vista 3D sin omitir los nuevos cálculos»).

- **Isc bifacial (BNPI):** `calculos/corriente_bifacial.py` con
  `factor_isc_bifacial(φ) = 1 + 0.135 φ`. φ efectivo:
  - con el modelo bifacial activo (☀️ Recurso Solar / 🗺️ Vista 3D):
    bifacialidad × factor de vista trasera de la superficie (fachada adosada →
    0, como en el Motor Óptico);
  - sin modelo bifacial pero con panel bifacial en el catálogo: la
    bifacialidad del panel (lado seguro), con aviso;
  - panel monofacial: 1.0 (sin cambio).
  Se aplica a: corriente de diseño DC del Unifilar (ampacidad), Isc de diseño y
  fusible gPV de la ficha RETIE (única y multi-superficie), `isc_total` del
  MPPT y el límite de corriente del string en ⚡ Diseño eléctrico. Voc y Vmp
  no cambian.
- **String que cruza:** la topología marca el cruce en el grupo («5 de 10
  módulos en «Oeste»») y las superficies del Unifilar/RETIE muestran sus
  módulos físicos (`modulos_fisicos_por_superficie`). La corriente y la rama
  eléctrica siguen siendo las del grupo (el string es uno solo).
- **Cableado:** 🔀 Mismatch indica cuándo Producción usa el cálculo real del
  Unifilar en lugar del % manual; el Unifilar multi-superficie muestra el % de
  cableado DC que de verdad aplica la cadena.
- Manual del Asistente con la cuenta del JAM66D46-720/LB.

## Alternativas descartadas

- Usar el Isc máximo con el albedo real del sitio: la norma pide la BNPI, un
  valor fijo y comparable entre fichas.
- Ignorar la bifacialidad cuando el modelo bifacial está apagado: el panel
  sigue recibiendo luz atrás en obra; se toma el lado seguro y se avisa.

## Fuera de alcance

- La compatibilidad de corriente de 📐 Dimensionamiento de superficie única
  (sigue con el Isc de la ficha; siguiente fase).
- Ampacidad por temperatura del sitio y método de instalación.
