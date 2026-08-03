---
name: BIPV catálogo baterías — loader y template
description: Fixes críticos al loader de baterías y estructura del catálogo Excel
---

## Regla crítica: normalización de columnas
El template Excel de baterías usa `\n` en headers (ej. `"Capacidad\n(kWh)"`) para display multilinea.
pandas los lee con el `\n` literal. El `_COL_MAP` usa espacios (`"Capacidad (kWh)"`).
**Fix aplicado**: `_normalizar_col()` reemplaza `\n` → espacio antes de matchear.

**Why:** Sin este fix, `capacidad_kWh` = None → `dimensionar_bateria()` retorna error
"Batería sin capacidad definida" aunque el Excel tenga el dato.

## Regla crítica: detección de header row
El template tiene título en fila 1 y headers en fila 3. La heurística original
(chequear si col[0] es dígito o "unnamed") no detectaba este caso.
**Fix aplicado**: prueba `header=0..4` y busca si alguna columna matchea alias de "Modelo".

**Why:** Con header=0 se leía el título como columna → catálogo retornaba `{}`.

## Defaults seguros del loader
Cuando DoD, RTE o ciclos faltan en la ficha:
- `dod_pct` = 80 %
- `eta_rte_pct` = 95 %
- `ciclos_vida` = 3000

Para ATESS ESS (6000 ciclos reales), el dato falta en las fichas actuales → vida estimada subestimada.
Pedir al proveedor: DoD, RTE, garantía, temperatura.

## Diagnóstico en servidor
Script disponible: `bipv_python/datos/diagnostico_catalogo_baterias.py`
Comando: `python bipv_python/datos/diagnostico_catalogo_baterias.py`
Reporta: hoja encontrada, columnas mapeadas, modelos completos/incompletos.

## Baterías cargadas al catálogo (26 modelos — TODOS alta tensión 300-870V)
- BR172R/186R/200R/215R — fabricante pendiente confirmar
- ATESS ESS: BC/BR45T-60T, BC/BR75T-145T, BR114R-157R, BC55RPB (6-11 mód)
- NINGUNA compatible con inversores 48V (DEYE, APsystems AHS)
- Requieren inversores HV comerciales

## Cómo agregar la hoja al servidor
El archivo maestro `Catalogo_Baterias_BIPV_Maestro.xlsx` (hoja `Catalogo_Baterias`)
debe agregarse como hoja adicional a `/var/www/bipv/.../inversores_catalogo.xlsx`.
El loader busca la hoja por nombre; si no existe, retorna `{}` sin error.

## pdfplumber pierde celdas en tablas multi-modelo (extractor de paneles)
- En filas SIN etiqueta de tablas multi-modelo, pdfplumber puede devolver None
  en la última columna aunque el valor exista en el PDF (bordes de grilla incompletos).
- Solución en el extractor: `_extract_tables_reparadas()` repara celdas None
  cropeando columna×fila; solo en filas ≥ceil(n/2) completas y texto de 1 línea ≤60 chars.
- La cabecera de modelos se elige por la fila con MÁS códigos (celdas colspan
  reparadas pueden inyectar códigos sueltos en la fila de grupo).

## Fichas PDF 100% imagen (SolTech flexible)
- Algunas fichas (ej. SolTech SMF 520J) no tienen capa de texto: pdfplumber devuelve 0 chars → se activa el fallback OCR (tesseract) en pdf_panel_extractor.py.
- **Lección OCR:** los subíndices se pierden (Vmp→"Vm") y las unidades no siguen al número — los patrones deben aceptar `Etiqueta (Símbolo) valor` sin unidad. El nombre de modelo debe tomarse de una etiqueta confiable (fila "Rendimiento a STC"), nunca del primer código suelto: el OCR genera basura tipo "MAZM-IDOO" que gana si se busca genéricamente.
- En fichas con secciones STC y NOMT, el primer match (STC) es el correcto porque STC aparece primero en el texto.

## Extractor inversores — lecciones fichas en español (ago 2026)
- Fichas Growatt en español insertan caracteres de control (\x01) DENTRO de los nombres de modelo ("MAX\x0150KTL3-XL\x012") → siempre limpiar [\x00-\x1f] del texto antes de detectar modelos multi-columna.
- Etiquetas españolas ≠ inglesas: "Rango de voltaje de MPPT", "Número de MPPTs", "Cadenas por MPPT", "Voltaje de arranque", "Rango de potencia máxima" (= rango voltaje a plena carga → V_mppt_activo).
- Etiquetas que se parten en dos líneas ("Máxima potencia FV / recomendada (STC) 100000W...") → los loops línea-a-línea no deben hacer break en la línea de la etiqueta sin valores.
- Fallbacks conservadores aceptados por el usuario: Vdc_max=Vmppt_max si no publicado; V_mppt_activo desde "Rated PV/DC input voltage" con sanity dentro del rango MPPT y ≥60 V.

## Fichas OCR (Felicity y similares)
- El OCR pega palabras ("PVIsc" sin espacio) y duplica letras en títulos ("MMAAXX5500"). Regla: en patrones de fichas OCR usar `\s*` entre tokens de etiqueta, y rechazar tokens que sean pares de letras duplicadas `(?:(.)\1)+` al detectar modelos.
- Fichas en español (Huawei/Growatt): normalizar separador de miles `(\d),(\d{3})(?!\d)` antes de extraer; ojo con superíndices de notas al pie pegados al valor ("entrada 1 1100 V") y palabras pegadas por pdfplumber ("Tensiónde funcionamientoMPPT").

## Fichas en español con unidades entre corchetes (SAJ y similares)
- Etiquetas tipo "Tensión máxima de entrada [V] 1100" requieren patrones con `\[\s*V\s*\]` explícito; los genéricos fallan por el corchete entre etiqueta y número.
- Valores por MPPT en notación slash ("32/32/32", "38.4/38.4/38.4"): el valor por tracker es el primero de la lista.
- Filas multi-modelo pueden traer números SIN unidad ("Potencia máxima FV [Wp]@STC 30000 37500 45000") → fallback de números pelados 4-7 dígitos solo en líneas cuya etiqueta ya matcheó potencia FV.
- "No. de MPPT 3 4 4" (un entero por columna, sin N/M): preferir la línea con tantos valores como modelos; si faltan, rellenar con el último.

## Pseudo-rangos por la 'A' de amperios (Growatt MID)
- _RANGE_RE acepta 'a' como separador (IGNORECASE) → "27A 27A" en tablas multicolumna matchea como rango 27–27. Regla: un rango con mín==máx nunca es real → descartarlo y probar la siguiente etiqueta.
- Growatt MID: "Normal Voltage 200V-1000V" es el rango MPPT real; "MPPT voltage range 580V" (un solo valor) es la tensión nominal a plena carga → V_mppt_activo.
- Etiquetas partidas en dos líneas por pdfplumber ("Max. short-circuit current per\nMPP tracker 33.8A", "recommended PV power\n(for module STC) 22500W...") requieren patrones (?m) multilínea o matchear la línea de valores.
