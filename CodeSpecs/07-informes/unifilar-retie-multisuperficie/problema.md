# Spec — Diagrama Unifilar y Ficha RETIE con el sistema multi-superficie real

**Estado:** validación

## Alcance de la fase

App Streamlit (`bipv_python/`): ⚡ Diagrama Unifilar (`pages/20_⚡_Diagrama_Unifilar.py`,
`calculos/diagrama_unifilar.py`) y 📋 Ficha de Validación RETIE
(`pages/21_📋_Ficha_Validacion_RETIE.py`, `calculos/ficha_validacion_retie.py`).
Evidencia: proyecto del cliente en Bogotá, 28-sep-2026 (fachada ASP-ST1-T40 con
8 en serie × 14 strings, techo SPR-E20-327 con 4 en serie × 1 string, un
inversor, 116 módulos), pregunta del usuario «¿mi APP cumple el RETIE?».

## Problema a resolver

1. **La Ficha RETIE no lee el diseño real.** Toma panel, inversor, N serie y
   número de módulos de 📐 Dimensionamiento (un solo panel y un solo tipo de
   string). Con el sistema multi-superficie de 🗺️ Vista 3D (dos paneles
   distintos, grupos de strings por MPPT, varios inversores) valida otro
   sistema: el Voc en frío, la ventana MPPT y el breaker no corresponden a lo
   que se va a construir.
2. **El Diagrama Unifilar pide a mano los módulos por superficie.** El texto
   de la página dice que Vista 3D «trabaja con áreas y POA, no con conteo de
   paneles», lo que dejó de ser cierto con los grupos de strings (A1–A3). El
   dibujo multi-superficie además junta todas las superficies en un solo
   inversor genérico, sin MPPT, sin inversores reales y sin cajas
   combinadoras.
3. **Faltan elementos del sistema en el diagrama.** Las cajas combinadoras
   que el diseño eléctrico ya detecta (más strings que entradas del MPPT con
   corriente dentro del límite) no aparecen; la batería se cuelga de «el»
   inversor aunque haya varios; los optimizadores (MLPE) no tienen forma de
   declararse ni de dibujarse.

## Contexto

- `calculos/diseno_electrico_multisup.validar_diseno_electrico` ya valida
  grupo, MPPT, inversor y superficie (Voc en frío, ventana MPPT, Isc del
  MPPT, entradas, relación DC/AC) y marca `caja_combinadora` por MPPT.
- La topología `optimizador` existe en el modelo (`TOPOLOGIAS_CONOCIDAS`) pero
  no tiene validación eléctrica (queda para la Spec B de topologías).
- La batería de 🔋 Baterías y Balance vive en `bateria_ok`, `bateria_dict`,
  `bateria_dim` y `bateria_nombre`; `compatibilidad_bateria.check_compatibilidad`
  revisa si el inversor la admite.
- RETIE certifica instalaciones y productos, no software: estas páginas son
  documentos de apoyo para el ingeniero que firma el diseño.
