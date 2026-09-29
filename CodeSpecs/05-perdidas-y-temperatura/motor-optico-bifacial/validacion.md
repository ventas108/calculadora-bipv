# Validación — Motor Óptico en modo bifacial

**Estado:** validación

## Checklist de validación del módulo

- [x] 22 pruebas nuevas en `tests/test_motor_optico_bifacial.py`: en `main` el
  archivo no se puede cargar (no existen `poa_publicable` ni
  `mensaje_impacto_optico`) y la cascada deja un hueco de 223.8 kWh/m² (el
  aporte trasero); con el cambio pasan.
- [x] Monofacial: la POA óptica es idéntica, hora a hora, a la fórmula de
  antes (tolerancia 1e-9).
- [x] Prueba de humo de 🔆 Motor Óptico (AppTest, granja a 10°, bifacial
  0.80): sin excepciones; 2,647.6 − 73.2 − 88.3 = 2,486.1 = POA sin térmico;
  aporte trasero 228.0 → 216.6 después de la IAM difusa, y el mismo 216.6 en
  `poa_sin_termico_df` («global − front»); aviso «superficie casi horizontal
  (granja o cubierta) (10°)».
- [x] Pruebas existentes del Motor Óptico, del Asistente y de la regla de no
  nombrar la referencia: pasan.
- [x] Suite completa de `bipv_python`: 2019 pasan.

## Resultado

Criterios 1 a 8 cumplidos. En espera de la revisión del PR.
