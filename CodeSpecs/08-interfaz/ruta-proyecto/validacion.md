# Validación — 🧭 Ruta del proyecto

**Estado:** validación

## Checklist de validación del módulo

- [x] 9 pruebas en `tests/test_ruta_proyecto.py`: rojas sin el módulo.
- [x] Humo con AppTest de 🏠 Proyecto: sin excepciones; «1 de 11 pasos
  listos · siguiente: ☀️ Recurso Solar»; con Granja, 15 estaciones.
- [x] Sin cambios de cálculo: la guardia de física no aplica.

- [x] Corrección tras el despliegue del PR #112: al volver de ☀️ Recurso
  Solar a 🏠 Proyecto salía «ValueError: The truth value of a DataFrame is
  ambiguous». La comprobación de «listo» comparaba las tablas de pandas con
  `{}` y `[]`. Prueba con tablas reales: roja antes, verde después. Humo con
  AppTest y sesión real: sin excepciones.

## Resultado

Criterios 1 a 7 cumplidos. En espera de la revisión del PR.
