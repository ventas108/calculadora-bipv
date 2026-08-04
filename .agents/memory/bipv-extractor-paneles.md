---
name: BIPV - extractor de fichas de paneles blindado
description: Banco de regresión + validador físico del extractor PDF de paneles; cómo agregar fichas nuevas que fallen
---

## Regla
Cualquier fix al extractor de fichas de paneles (`bipv_python/calculos/pdf_panel_extractor.py`) debe correr `python bipv_python/scripts/test_pdf_panel_extractor.py` (banco de regresión, fixtures OCR reales en `scripts/fixtures_fichas/`). Cada ficha nueva que falle se agrega al banco con sus valores esperados — nunca parchar regex sin fixture.

**Why:** fallos silenciosos recurrentes (JA Solar ago-2026: coefs 0, Ns=2384 desde "Dimensions", modelo desde "Version No."); arreglar una ficha rompía otras.

**How to apply:**
- Validador de coherencia física: `calculos/validador_panel.py` (`validar_panel`) — bloquea guardado en Catálogo PDF si hay errores (Vmp<Voc, Imp<Isc, Pmax≈Vmp×Imp ±8%, Voc/Ns 0.55–0.95 V/celda con sugerencia half-cut, eficiencia >25% imposible). Es sensible a tecnología: thin-film (CdTe/CIS/a-Si) degrada Voc/Ns y eficiencia baja a aviso — no volver a endurecerlo.
- Campo irrecuperable por OCR → devolver None, nunca un valor plausible falso.
- Cada importación guarda el texto OCR crudo en `bipv_python/datos/fichas_ocr/<modelo>.txt` para auditar sin pedir la ficha de nuevo.
- El usuario suele probar con paneles half-cut: Ns efectivo = medias celdas / 2 (ej. JAM66D46: 132 → 66).
