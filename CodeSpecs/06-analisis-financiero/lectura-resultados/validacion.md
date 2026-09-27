# Validación — Lectura de resultados de Financiero

**Estado:** validación

## Checklist de validación del módulo

- [x] `tests/test_lectura_financiera.py`: 5 pruebas. La de la página falla en
  `main` y pasa con el cambio; umbral 677 con el caso del cliente (antes 600),
  300, mínimo y sin umbral; LCOE < valor nivelado ⇔ VPN sin Ley > 0 con el
  caso del cliente (LCOE > 1.200 y aun así rentable).
- [x] Humo con AppTest de la página: sin errores; fila del umbral ordenada;
  leyenda nueva; nota del LCOE; tabla de flujo con las columnas formateadas.
- [x] Suite completa de `bipv_python`.

## Resultado

Criterios 1 a 5 cumplidos. En espera de la revisión del PR.
