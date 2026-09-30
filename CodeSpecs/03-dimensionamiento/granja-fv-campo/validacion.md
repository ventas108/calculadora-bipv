# Validación — 🌾 Granja FV, fase 1: campo de filas coherente con el proyecto

**Estado:** validación

## Checklist de validación del módulo

- [x] 22 pruebas nuevas en `tests/test_granja_fv.py`: en `main` el archivo
  no se puede cargar (no existe `calculos.granja_fv`); con el cambio pasan.
  Cubren la mesa de Apartadó contra la referencia (2,626 m; GCR 39,8 %;
  6,5°), el conteo de 308 módulos, terreno chico, filas que se tocan,
  orientación vertical, varias mesas por fila, sugerencia, datos del
  proyecto, coherencia (verde, bifacial, fuentes, no cabe, multi-superficie),
  3D, páginas y manual.
- [x] Prueba con las páginas reales (AppTest, JAM66D46-720/LB del catálogo,
  Apartadó 308 módulos, 10°, 2.393 m², ocupación 40 %, bifacial GCR 0,40 y
  altura 1,0 m):
  - 🌾 Granja FV al abrir: 308 / 308, 221,76 kWp, GCR 40,0 %, 6,5°, todo 🟢.
  - «Sugerir distribución» en el terreno cuadrado: 20 módulos por mesa,
    308 / 308.
  - Geometría de la referencia (80 × 30 m, 31 por mesa, separación 6,60 m,
    altura libre 2,4 m): 308 / 308 en 5 filas, GCR 39,8 %, 6,5°, corredor
    4,01 m; 🟠 altura del modelo bifacial 1,00 m frente a 2,63 m del campo.
  - 🗺️ Vista 3D con esa geometría: «308 de 308 módulos en 5 filas · GCR
    39.8 %», métrica «Paneles visualizados» 308 (antes 288).
- [x] Suite completa de `bipv_python`: 2185 pruebas pasan.

## Resultado

Criterios 1 a 9 cumplidos. En espera de la revisión del PR.
