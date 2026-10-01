# Diseño — Comparador de Inversores completo

**Estado:** validación

## Entradas

- Panel (`Voc_stc`, `Vmp_stc`, `Isc_stc`, `Tk_beta`, `Pmax_stc`), catálogo de
  inversores, módulos del proyecto (`N_paneles_final` o los de
  Dimensionamiento), temperaturas de frío, trabajo y extrema.
- Serie horaria `P_ac_sin_recorte_kW` de 📊 Producción, precios cotizados
  (`comp_precios_cotizados`) y supuestos financieros.

## Salidas

- Tabla por inversor: N, rango de N, strings, sobrantes, modo, unidades,
  reparto, DC/AC, Voc en frío, margen 🟢/🟠, ficha, motivo.
- Comparación: energía, recorte, precio y su fuente; CAPEX, TIR, VPN,
  payback y LCOE solo con precio.
- Claves de adopción para 📐 Dimensionamiento.

## Tipos de datos

`pd.DataFrame`, `dict`, `list[int]`.

## Errores posibles

- Ningún N compatible: fila con el motivo (del N de referencia).
- Inversor sin potencia AC: no entra a la comparación de energía.
- Módulos que no se reparten exacto: se usan los strings completos y se
  muestran los sobrantes.

## Dependencias

`calculos/comparador_inversores.py`, `calculos/ficha_inversor.py`,
`calculos/dimensionamiento.py` (`DCAC_OBJETIVO`, `resolver_n_strings_tracker`),
`calculos/financiero.py`, `pages/4b_⚖️_Comparador_Inversores.py`.

## Criterios de aceptación

1. Un inversor con Vmp extremo fuera del MPPT queda descartado.
2. Ficha 🔴 descarta; ficha 🟠 se muestra; margen de Voc visible.
3. Urabá: Growatt (1.100 V) → 22 en serie, 14 strings, 7 + 7, 1 string por
   MPPT, 🟠; un inversor de 1.500 V → 28, 11 strings, 2 unidades por DC/AC.
4. Sin precio no hay TIR ni LCOE; con precio cotizado sí; energía escalada
   por los módulos usados.
5. Adoptar deja Dimensionamiento con 1 string por MPPT, 14 cadenas y 7 + 7.
6. La página muestra la sección nueva y la T. extrema.
7. El manual del Asistente lo explica (sección 104).
