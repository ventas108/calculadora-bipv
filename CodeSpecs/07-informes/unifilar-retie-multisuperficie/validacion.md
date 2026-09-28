# Validación — Diagrama Unifilar y Ficha RETIE con el sistema multi-superficie real

**Estado:** validación

## Checklist de validación del módulo

- [x] `tests/test_topologia_electrica.py` (8) y
  `tests/test_retie_unifilar_multisuperficie.py` (19): rojas en `main` (no
  existían los módulos ni los parámetros) y verdes con el cambio. Caso real
  del cliente: Voc en frío 987,6 V < 1100 V, caja combinadora en el MPPT 1
  (14 strings, 14,0 A de 18 A), fusible gPV ≥ 1,25 A, breaker del SG5.0RT
  20 A a 220 V, DC/AC 1,67 por revisar.
- [x] Páginas ejecutadas con AppTest en los dos modos y sin proyecto; en
  `main` el unifilar falla con `st.image(use_container_width)`.
- [x] Geometría del dibujo: cajas del tamaño pedido, centradas en su línea
  (una superficie) y alineadas con sus ramas (topología).
- [x] Auditoría de las pruebas por mutación: 21 cambios deliberados del código
  (caja, strings, reasignación de batería, factores del fusible y del
  breaker, colores, doble redondeo, dibujo, página, alto de la ficha); las
  21 hacen fallar al menos una prueba.
- [x] Revisión visual: PNG del unifilar (cliente; dos inversores con batería y
  optimizadores; una superficie) y de la ficha (multi y una superficie).
- [x] Asistente: 4 pruebas de recuperación (RETIE, caja combinadora,
  optimizadores, lectura del unifilar).
- [x] Suite completa de `bipv_python`, physics-guard y auditoría SDD.

## Resultado

Criterios 1 a 7 cumplidos. En espera de la revisión del PR.
