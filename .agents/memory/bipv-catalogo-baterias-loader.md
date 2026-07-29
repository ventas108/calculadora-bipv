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
