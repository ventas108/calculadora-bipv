---
name: BIPV - extractores de fichas blindados (paneles e inversores)
description: Bancos de regresión + validadores físicos de los extractores PDF de paneles e inversores; cómo agregar fichas nuevas que fallen
---

## Regla
Cualquier fix al extractor de fichas de paneles (`bipv_python/calculos/pdf_panel_extractor.py`) debe correr `python bipv_python/scripts/test_pdf_panel_extractor.py` (banco de regresión, fixtures OCR reales en `scripts/fixtures_fichas/`). Cada ficha nueva que falle se agrega al banco con sus valores esperados — nunca parchar regex sin fixture.

**Why:** fallos silenciosos recurrentes (JA Solar ago-2026: coefs 0, Ns=2384 desde "Dimensions", modelo desde "Version No."); arreglar una ficha rompía otras.

**How to apply:**
- Validador de coherencia física: `calculos/validador_panel.py` (`validar_panel`) — bloquea guardado en Catálogo PDF si hay errores (Vmp<Voc, Imp<Isc, Pmax≈Vmp×Imp ±8%, Voc/Ns 0.55–0.95 V/celda con sugerencia half-cut, eficiencia >25% imposible). Es sensible a tecnología: thin-film (CdTe/CIS/a-Si) degrada Voc/Ns y eficiencia baja a aviso — no volver a endurecerlo.
- Campo irrecuperable por OCR → devolver None, nunca un valor plausible falso.
- Cada importación guarda el texto OCR crudo en `bipv_python/datos/fichas_ocr/<modelo>.txt` para auditar sin pedir la ficha de nuevo.
- El usuario suele probar con paneles half-cut: Ns efectivo = medias celdas / 2 (ej. JAM66D46: 132 → 66).

## Inversores (mismo patrón)
- Validador: `calculos/validador_inversor.py`; bloquea solo invariantes universales (Vdc_max>0, MPPT mín<máx≤Vdc_max, Isc≥I_max por tracker, batería mín<máx); microinversores 60 V y off-grid sin Isc/arranque NO se bloquean.
- Runner consola: `scripts/test_pdf_inversor_extractor.py` — ejecuta el banco `CASOS` de `scripts/casos_test_inversores.py` (mismo de la página 16) en modo estricto: campo con esperado None (N/D) que aparezca con valor extraído en la salida SIN merge = fallo (atrapa basura). Los valores por modelo legítimos (Deye P_dc) viven en `valores_por_modelo` y no cuentan como basura.
- Convención de la página 16: esperado None = N/D informativo (🔵), no penaliza — no cambiarla; la estrictez vive solo en el runner.

## PDFs "mixtos" (texto digital escaso + tablas en imagen, p.ej. Hiitio CdTe)
- Algunas fichas superan el umbral de texto digital pero los coeficientes/dimensiones están solo en imágenes → complemento OCR al final de `extraer_parametros_panel`: rellena SOLO campos faltantes sin sobrescribir lo digital.
- Bifacialidad faltante NO debe disparar el OCR (falta legítimamente en monofaciales); sí se rellena si el OCR corre por otro motivo.
- `uso_ocr=True` siempre que el OCR aporte algo (incluida solo la tecnología) — la UI usa el flag para banners/confianza.
- Labels descriptivos ingleses ("Open circuit voltage temperature coefficient -0.28%°C") y espesores decimales ("1200*600*16.2mm") requieren patrones propios.

## Fichas que repiten el MISMO código de modelo en varias columnas (p.ej. HL-XWB13)
- Nunca acumular valores multi-modelo en dict keyed por nombre: columnas con código repetido se pisan en silencio. Usar lista posicional por columna y deduplicar nombres al final con sufijo de Pmax ("(135W)") o "var. N".
- La UI de catálogo debe reemplazar el nombre prellenado también cuando el extraído es la BASE de una variante deduplicada, o se guardan variantes distintas bajo el mismo nombre.
- Alias "Optimum operating voltage/current" → Vmp/Imp (fichas PV wall/tile).

## Fallback genérico de coeficientes de temperatura
- En vez de una regex por fabricante, hay fallback por línea: "temperature coefficient"/"coeficiente de temperatura" + magnitud (Voc/Isc/Pmax) en cualquier orden e idioma; solo rellena lo que los patrones específicos dejaron None.
- Rango físico obligatorio (Voc/Pmax negativos en (-1,0); Isc en (-0.2,0.2)) y descartar "±" (tolerancias) — sin esto captura ruido.
- Los patrones específicos tienen prioridad y NO validan rango: los casos negativos de test deben usar redacciones que solo alcance el fallback.

## Ns en fichas half-cut (#67)
- Fichas half-cut declaran SEMICELDAS ("28 half-piece"); el Motor IV necesita celdas en serie = mitad (dos strings paralelos). Decidir mitad vs total con Voc/celda 0.4–1.0 V.
- El guard de plausibilidad Ns 10–300 mata valores legítimos de tejas BIPV (Ns=14): eximir cuando el Ns viene del conteo de semiceldas, y propagar ese origen a través del complemento OCR.
- Exigir contexto de conteo en el regex ("half cells", no "half-cut technology") y limpiar flags internos antes de devolver a la UI.
- Motor IV ya corrige Ns al vuelo (verificar_ns_halfcut en modelo_iv.py) y el validador sugiere la mitad al guardar — las tres capas se complementan.
