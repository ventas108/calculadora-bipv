# Validación — 🌾 Granja FV, fase 3: agrivoltaica — luz para el cultivo, mapa de sombra y maquinaria

**Estado:** validación

## Checklist de validación del módulo

- [x] 15 pruebas nuevas en `tests/test_granja_agrivoltaica.py`: en `main` el
  archivo no se puede cargar (no existe `calculos.agrivoltaica`); con el
  motor y sin la página ni el manual fallan 2; con el cambio completo pasan.
- [x] Contra pvlib: fracción de cielo del suelo a ±0,001 de
  `vf_ground_sky_2d` (inclinación 0°, 10° y 30°); fracción de suelo con sol
  igual a `_unshaded_ground_fraction`.
- [x] Prueba con la página real (AppTest, Apartadó, JAM66D46-720/LB del
  catálogo, TMY sintético de cielo claro sin red):
  - Avisos: 🟢 categoría I (2,40 m ≥ 2,10 m), 🟠 tractor de 2,50 m no pasa
    por debajo (necesita 2,80 m), 🟢 pasa por el corredor de 4,01 m.
  - «🌱 Calcular la luz en el suelo»: luz media 60 %, 1,442 kWh/m², bajo
    las mesas 39 %, entre filas 74 %, homogeneidad 0,27; perfil y mapa de
    sombra mensual dibujados.
  - Máquina de 2,0 m: 🟢 pasa por debajo con 0,40 m de holgura.
  - Altura libre 4,0 m: el resultado viejo se oculta; recalculado, luz media
    60 % y homogeneidad 0,67.
- [x] Guardia de física: sin cambios en fórmulas del SDM.
- [x] Suite completa de `bipv_python`: 2221 pruebas pasan.

## Resultado

Criterios 1 a 7 cumplidos. En espera de la revisión del PR.
