---
name: Panel multi-model extractor
description: Extractor PDF de paneles con soporte multi-columna — estructura, campos y limitaciones conocidas
---

# Panel multi-model extractor

## Regla
`_extract_multimodel_panel(text)` en `bipv_python/calculos/pdf_panel_extractor.py` detecta fichas con ≥2 variantes en columnas y extrae Pmax/Voc/Isc/Vmp/Imp por modelo.

**Why:** Fichas reales (Canadian Solar, Trina, NCL BIPV) presentan 4-12 variantes en columnas paralelas. Sin esto, _find_first captura solo el primer valor y lo asigna a todos.

## How to apply
- Búsqueda de cabecera de modelos: `_MODEL_CODE_RE = [A-Z][A-Z0-9]{1,7}[-][A-Z0-9][-A-Z0-9-\.]{3,40}` + filtro `re.search(r'\d', code)`.
- Busca en **todo el documento** (sin límite de líneas) — la tabla de specs puede estar en cualquier página.
- Maneja unidades embebidas en valores: `327.8W`, `124.2V`, `3.74A` via `re.findall(r'([0-9]+(?:\.[0-9]+)?)', line[from_pos:])`.
- Campos **compartidos** (CoefVoc/CoefIsc/CoefPmax/NOCT/Ns/dimensiones/tecnología) se siguen extrayendo con `_apply_patterns()` — no cambian entre variantes.
- Sanity checks ampliados: Voc≤300V (CdTe puede tener >120V), Isc≤60A, Pmax≤2000W.

## Limitaciones conocidas
- El servidor usa pdfplumber (no pdftotext): el texto puede diferir en layout.  Verificado solo con pdftotext localmente; la estructura de texto plano del PDF NCL funciona, pero datasheets con tablas muy fragmentadas por pdfplumber pueden necesitar ajuste.
- Campos compartidos CoefVoc/CoefIsc/CoefPmax/NOCT no se detectaron en la ficha NCL — el PDF los pone en formato `%/ºC` sin un label exacto que coincida con los patrones actuales. Pendiente afinar patrones para ese formato.
- Si hay múltiples tablas de specs (grupos de productos distintos, como en NCL), solo se toma la PRIMERA tabla encontrada.
- N_s (celdas en serie) no aparece en fichas CdTe — el usuario debe llenarlo manualmente.
