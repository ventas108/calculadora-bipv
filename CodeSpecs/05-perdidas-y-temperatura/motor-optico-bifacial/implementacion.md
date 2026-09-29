# Implementación — Motor Óptico en modo bifacial

**Estado:** validación

## Cambios realizados

- `calculos/motor_optico.py`:
  - `cascada_optica` separa cara frontal (`poa_front`, IAM con la proporción
    directa/difusa de la hora, suciedad) y aporte trasero
    (`poa_global − poa_front`, solo IAM difusa, sin suciedad) cuando la POA es
    bifacial; monofacial sin cambios.
  - Columnas nuevas `poa_frontal_optica` y `poa_trasera_optica`; resumen con
    `bifacial`, `aporte_trasero_kWh_m2` y `aporte_trasero_optico_kWh_m2`.
  - Factores promedio ponderados por energía.
  - `poa_publicable()` y `mensaje_impacto_optico()`.
- `pages/5b_🔆_Motor_Optico.py`: publica `poa_sin_termico_df` y
  `poa_efectiva_df` con `poa_publicable`; nota «🔆 Panel bifacial»; factores
  ponderados con su explicación; aviso de la sección 5 según la inclinación;
  encabezado «Superficie» en vez de «Fachada».
- Manual del Asistente, sección 84 (y nota en la 83).
- Director: contrato de 05 y registro de decisiones.

## Archivos modificados

- `bipv_python/calculos/motor_optico.py`
- `bipv_python/pages/5b_🔆_Motor_Optico.py`
- `bipv_python/tests/test_motor_optico_bifacial.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
