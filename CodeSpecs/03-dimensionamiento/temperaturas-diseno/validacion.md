# Validación — Temperaturas de diseño estables en 📐 Dimensionamiento

**Estado:** validación

## Checklist de validación del módulo

- [x] 14 pruebas nuevas en `tests/test_temperaturas_diseno_estables.py`: en
  `main` el archivo no se puede cargar (no existen las funciones); con el
  cambio pasan.
- [x] Prueba de humo de 📐 Dimensionamiento (AppTest, catálogo real):
  sin TMY → valores de la ciudad (20.0 / 55.0 / 64.0) con aviso; con TMY →
  los del TMY; editada a mano → se respeta; página nueva solo con los datos
  (salir y volver) → se conserva; otro TMY → se recalcula; las tres en 0 →
  se recalculan.
- [x] `tests/test_invalidacion_ciudad.py` sigue pasando. `tests/test_pagina_dimensionamiento_temperaturas_ciudad.py` revisaba el texto del mecanismo anterior (`setdefault`); ahora revisa lo mismo (defectos de la ciudad activa) con `campo_persistente`.
- [x] Suite completa: 1972 pasan; la única que falló era esa prueba de texto.
- [x] Compilación con `-W error::SyntaxWarning`.
- [x] Suite completa de `bipv_python`.

## Resultado

Criterios 1 a 7 cumplidos. En espera de la revisión del PR y de la prueba en
producción con el proyecto de Apartadó.
