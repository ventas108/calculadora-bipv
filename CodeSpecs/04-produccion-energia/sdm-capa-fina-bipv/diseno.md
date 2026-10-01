# Diseño — Modelo IV de paneles BIPV de capa fina (CIGS) sin parámetros de laboratorio

**Estado:** validación

## Entradas

Panel del catálogo: Voc, Isc, Vmp, Imp, `tecnologia`, `N_s` (opcional),
coeficientes (opcionales), `eficiencia_rel_200` (opcional, % relativo a
STC, p. ej. 97).

## Salidas

`estimar_sdm_desde_ficha` agrega:
- `_tec_norm` real (CIGS para CIS/CIGS) y `_tecnologia_supuesta` (bool);
- `_ns_estimado` (bool) cuando las celdas salen de Voc;
- `_ajuste_200` (`"ficha"`, `"defecto"` o `None`), `_calibrado_200`
  (bool), `_rel_200_modelo` (%), `_metodo` = `pvsyst_v6_calibrado_200`
  cuando se ajusta.

## Tipos de datos

`dict`, `float`, `bool`.

## Errores posibles

- N_s inválido explícito («0», texto) → `None`, como antes.
- Objetivo de 200 W/m² fuera de lo alcanzable → se usa el valor más cercano
  (`_rel_200_modelo` lo muestra).
- Si ningún factor de idealidad da un modelo físico → sin ajuste
  (`_error_ajuste_200` guarda el motivo).

## Dependencias

pvlib (`calcparams_pvsyst`), las constantes existentes.

## Criterios de aceptación

1. MiaSolé FLEX-03 90N (CIS, sin N_s) se estima como CIGS con N_s estimado
   y reproduce la ficha en STC (≤ 6 %).
2. Con `eficiencia_rel_200` el modelo reproduce el valor (± 0,3 puntos) y
   sigue reproduciendo STC; CIGS sin el dato queda en 97 %.
3. Paneles de silicio y el ASP quedan igual.
4. «Thin Film»/«Otro» quedan como supuestos y Motor IV lo avisa.
5. Catálogo: columna editable «η rel. 200 W/m² (%)».
6. Manual del Asistente, sección 112.
7. El catálogo ofrece y lee «CIGS» y «Poli-Si»; «CIS»/«Poly-Si» viejos se
   muestran con el nombre nuevo.
