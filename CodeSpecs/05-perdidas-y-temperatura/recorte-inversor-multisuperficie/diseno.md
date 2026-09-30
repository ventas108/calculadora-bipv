# Diseño — Vista 3D: recorte de cada inversor en los modos simplificado y bypass

**Estado:** validación

## Entradas

- `multisup_inversores[*]`: `inversor_id`, `nombre`, `P_ac_nom_W` (o
  `ficha.P_ac_nom_W`).
- Superficies de energía (`modulos`, `uid`, `grupos` con `inversor_id`,
  `n_serie`, `n_paralelo`, `cruce`).
- Resultado de la cadena por superficie (`pr`, `poa_bruta_kWh_m2`,
  `perfil_ac`) y panel (`Pmax_stc`).

## Salidas

- `cadena_superficie(...)["perfil_ac"]`: `numpy.ndarray` de 8760, suma 1.
- `factores_recorte(superficies, resultados, paneles, inversores) -> dict`:
  `superficies: {nombre: {f_recorte, recorte_kWh}}`, `inversores: [{inversor_id,
  nombre, P_ac_nom_W, e_sin_recorte_kWh, recorte_kWh, pct, horas,
  superficies}]`.
- `cadena_superficies_estado`: `pr` × `f_recorte`, `f_recorte`,
  `recorte_kWh`, `recorte_inversores` (solo si hay recorte).
- `recorte_por_inversor(resultados) -> list`, `tabla_recorte(resumen) -> list`.
- `tabla_desglose`: columna «Recorte inversor» si hay recorte.
- `firma_cadena(parametros, superficies, inversores=None)`.

## Tipos de datos

`dict`, `list`, `numpy.ndarray`, `pandas.DataFrame`.

## Errores posibles

- Inversor sin potencia AC: no recorta (el aviso existente pide el dato).
- Superficie de un inversor sin cadena (sin POA o panel): ese inversor no se
  recorta; la superficie ya aparece como error de la cadena.

## Dependencias

`calculos.cadena_perdidas_multisup`, `calculos.produccion.simular_produccion_anual`
(forma horaria SDM), Spec `05/string-cruza-superficies`.

## Criterios de aceptación

1. La cadena trae `perfil_ac` de 8760 horas que suma 1.
2. Inversor sin potencia AC o grande: PR idéntico al de antes, sin columna.
3. Inversor chico: la energía total es exactamente Σ min(AC del inversor,
   Pnom) hora a hora, y cada superficie pierde su parte.
4. Con dos inversores solo recorta el chico.
5. Un string que cruza reparte el recorte en las dos superficies.
6. El resumen por inversor cuadra con la suma de las superficies.
7. La energía publicada (simplificado) baja exactamente el recorte.
8. La firma cambia con la potencia AC; sin inversores con potencia AC, igual
   que antes.
9. Vista 3D muestra «✂️ Recorte por inversor» y el manual lo explica.
10. El mensaje DC/AC dice «1.00–1.35» y coincide con los límites: 0,97 → 🟠,
    1,00 y 1,35 → 🟢, 1,36 → 🟠; ya no aparece 0,95.
11. Con el campo de inversores en 0 aparece «🧮 La app calcula N
    inversor(es)» con la cuenta; con un número escrito no aparece.
