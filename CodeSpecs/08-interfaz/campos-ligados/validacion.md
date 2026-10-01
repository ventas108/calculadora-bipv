# Validación — Campos ligados a su dato en Dimensionamiento, Mismatch y Producción

**Estado:** validación

## Checklist de validación del módulo

- [x] 7 pruebas en `tests/test_campos_ligados.py`: cambio de página simulado
  con AppTest (los valores se conservan; antes: 1, valor por defecto,
  apagado), cambio del dato desde fuera, rango y opciones.
- [x] Guardas: con las páginas anteriores fallan la de los tres campos y la
  general (ninguna página usa como widget un dato que leen otros módulos);
  con el cambio pasan.
- [x] Guardia de física: sin cambios en fórmulas del SDM.
- [x] Suite completa de `bipv_python`: 2275 pruebas pasan.

## Resultado

Criterios 1 a 6 cumplidos. En espera de la revisión del PR.
