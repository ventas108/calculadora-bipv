# Diseño — Vista 3D: string que cruza dos superficies

**Estado:** validación

## Entradas

- `superficies_bipv[*].grupos[*].cruce`: `{"uid": str, "modulos": int}` o
  ausente.
- POA de cada superficie (`poas_vigentes_estado`) y paneles por superficie.

## Salidas

- `calculos/cruce_superficies.py`:
  - `cruces_del_proyecto(superficies) -> list[dict]` (origen, gid, destino,
    n_serie, n_paralelo, k).
  - `validar_cruces(superficies, paneles) -> (bloqueos, avisos)`.
  - `modulos_fisicos_por_superficie(superficies) -> {nombre: int}`.
  - `perdida_cruce(poa_origen, poa_destino, n_serie, k) -> dict`
    (`perdida_pct`, `factor_horario`).
  - `factores_cruce(superficies, poas) -> {nombre: {f_cruce, detalle}}`.
- `superficies_para_energia`: `modulos` y área con los módulos físicos.
- `cadena_superficies_estado`: `pr × f_cruce`, `f_cruce` y `cruce_detalle`
  en el resultado de cada superficie; `tabla_desglose` agrega la columna
  «String que cruza» cuando hay cruces.
- `firma_cadena`: incluye los cruces solo si existen (las firmas guardadas
  sin cruces no cambian).
- `validar_diseno_electrico`: agrega los bloqueos y avisos de los cruces.
- `construir_proyecto_desde_session_state` (modo físico): `ValueError` claro
  si hay cruces.

## Tipos de datos

`dict`, `list`, `numpy.ndarray`, `pandas.DataFrame`.

## Errores posibles

- Cruce hacia una superficie sin POA vigente: sin factor para ese grupo y
  error visible en la cadena («falta la POA de …»); no se publica.
- Cruce inválido: 🔴 en ⚡ Diseño eléctrico (bloquea el modo físico; los
  modos simplificado y bypass publican con el estado visible, como con
  cualquier 🔴 del diseño).

## Dependencias

`calculos.mismatch.perdida_string_bypass` (Spec B).

## Criterios de aceptación

1. Un grupo de A con N = 10, N paralelo = 2 y k = 4 hacia B: A cuenta 12
   módulos de ese grupo, B suma 8; el total del proyecto no cambia.
2. Este/Oeste con k = N/2: la pérdida del string es la de la Spec B (≈ 14.9 %
   en Apartadó) y se aplica a sus módulos en las dos superficies.
3. PR de cada superficie = PR de la cadena × (1 − L × módulos del string en
   ella ÷ módulos de la superficie); sin cruces, idéntico a antes.
4. La energía publicada (simplificado) baja exactamente lo que dice (3).
5. Validación: otra superficie inexistente, inactiva o la misma; k fuera de
   1..N − 1; paneles distintos → 🔴.
6. El modo físico no se prepara con cruces y lo explica; la sección «🔀 6»
   deja fuera esas superficies.
7. Sin cruces, las firmas de la cadena y del diseño eléctrico no cambian.
8. El editor de grupos permite declarar el cruce; el dato se guarda con el
   proyecto.
9. El manual del Asistente lo explica con números.
