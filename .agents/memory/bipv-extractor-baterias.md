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

## Fichas escaneadas (OCR) — formato bloques verticales (Felicity FLA-EU)
- PDFs escaneados sin texto → OCR (pytesseract, disponible en el servidor). El texto OCR NO conserva columnas: labels en un bloque y luego CADA modelo en línea sola con sus valores debajo (kWh, V, rango V, A continua, A pico, W pico).
- `_parse_bloques_verticales` es el fallback cuando el mapeo por columnas no llena ningún campo per-modelo. Exige capacidad Y voltaje por modelo (solo uno = ruido OCR → omitir). Ignora líneas `Parallel(...)` (escalabilidad, no capacidad).
- Potencia continua = primera corriente A del bloque × voltaje nominal (la pico viene después). `potencia_estimada=True` puede darse con `c_rate=None` — la UI no debe formatear c_rate sin chequear None (ya causó un TypeError).
- DoD/garantía en OCR quedan en líneas sueltas lejos del label (">95%", "10Years"): solo aceptarlas si el label existe y el valor suelto es único en la ficha.
- Segundo formato OCR (según motor/versión de tesseract): tabla HORIZONTAL con la cabecera de modelos ilegible — solo quedan legibles los extremos del rango del título ("FLA48100-EU~FLA48250-EU"). Regla: con 2 modelos y >2 valores en la fila, mapear primera y última columna a los extremos (el mapeo por posición asignaría la misma columna a ambos). Limitación conocida: los modelos intermedios del rango se pierden en ese formato.
- Labels OCR vienen pegados ("NominalVoltage") y unidades en minúscula ("51.2v"): los regex de label deben usar \s* y los de unidad aceptar mayúscula/minúscula.
