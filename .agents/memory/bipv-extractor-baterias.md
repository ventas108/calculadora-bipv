---
name: BIPV - extractor de fichas de baterías
description: Decisiones del extractor PDF de baterías (multi-modelo por columnas, módulo vs rack)
---

- Fichas de bancos de baterías traen DOS tablas con los MISMOS labels: módulo (~14 kWh/51 V) y rack (~200 kWh/768 V). Lo que va al catálogo es el rack.
  - Multi-modelo: elegir la fila del label con MÁS valores (rack) y mapear cada código de modelo al valor por POSICIÓN de caracteres en `pdftotext -layout` (los pares "BC75T BR75T" comparten columna).
  - Single-model: recorrer TODAS las líneas del label y tomar el valor plausible más grande — nunca "la primera fila que empata" (así ganaba el módulo; corregido tras auditoría).
- El peso (kg) se descartó a propósito: la fila de pesos queda desalineada (números cortos → centros corridos) y asignaba el peso del modelo vecino. Mejor no mostrarlo que mostrarlo mal.
- C-rate nominal = el MENOR de los "X C" en líneas de carga/descarga (fichas listan "0.5C" nominal y "1C (Opcional)"). Potencia kW = c_rate × kWh, marcada `potencia_estimada`.
- Siglas técnicas que parecen modelos y hay que filtrar: IP20/IP54, UN38, RS485, IEC62619, 16S1P, CE, CB, BMS, BPU, SOC, LCD, CAN, ROHS, MSDS.
- Prefill del form CRUD: guardar en session_state y forzar `bat_mm_sel = "➕ Nueva batería…"` ANTES del rerun, o Guardar renombraría el modelo seleccionado.
- Banco: `scripts/test_pdf_bateria_extractor.py` (fixtures PDF reales en scripts/fixtures_fichas/).
