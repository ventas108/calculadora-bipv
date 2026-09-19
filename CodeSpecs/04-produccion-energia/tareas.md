# Tareas — Producción de energía

**Estado:** completado

- [x] Inventariar entradas, salidas persistidas y consumidores de Producción.
- [x] Documentar el gate `03 → 04` para diseño eléctrico incompatible o vencido.
- [x] Registrar el contrato del motor anual y sus métricas IEC 61724.
- [x] Integrar firmas de vigencia de Producción y bypass, incluyendo
	  persistencia segura y prevención de doble soiling.
- [x] Ejecutar pruebas focales del motor anual y de pérdidas en el entorno actual:
	  `38 passed` (`test_produccion_perdida_ohmica.py`,
	  `test_perdidas_desglosadas_pvsyst.py`, `test_mismatch_bypass_termico.py`).
- [x] Resuelto en `06-analisis-financiero`: Finanzas y Presupuesto no
	  reconstruyen la firma en vivo (inviable); verifican la integridad del
	  payload canónico persistido junto a ella antes de restaurar.
- [x] Confirmar integración de resultados válidos con Finanzas e Informes:
	  validado funcionalmente en `06` (restauración en pestaña nueva) y por
	  contrato estático en `07` (Informes solo lee claves ya vigentes).
- [x] Contrato con Motor Ó́ptico y temperatura regularizado en
	  `05-perdidas-y-temperatura`.
