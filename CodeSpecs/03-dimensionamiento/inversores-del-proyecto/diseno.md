# Diseño — Cantidad de inversores del proyecto elegida por el diseñador

**Estado:** validación

## Entradas

- `N_inversores_proyecto` (int, 0 = automática), `N_inversores_proyecto_ref`.
- Strings del proyecto, capacidad de un inversor (MPPT × strings por MPPT),
  `P_ac_nom_W` de una unidad, kWp.

## Salidas

- `resolver_inversores(strings, capacidad, fijado=0, minimo=None) -> dict`
  (`n`, `minimo`, `maximo`, `fuente` «calculado»|«fijado», `ajustado`).
- `inversores_para_dcac(p_dc_kwp, p_ac_w_unidad, minimo, maximo,
  objetivo=1.3) -> int | None`.
- `inversores_fijados_vigentes(estado, inversor_nombre) -> int`.
- `proyecto_completo(..., N_inversores_fijado=0)`: agrega
  `fuente_inversores`, `inversores_ajustado`, `N_inversores_minimo`,
  `N_inversores_dcac`.
- `escalar_p_ac_nom_por_inversores(..., n_inversores_fijado=0)`: mínimo
  hacia arriba; agrega `fuente`, `ajustado`, `minimo`.

## Tipos de datos

`int`, `float`, `dict`.

## Errores posibles

- Cantidad fijada imposible: se ajusta al rango y se avisa (🟠 en
  Dimensionamiento, texto en Producción).
- Sin potencia AC en la ficha: no hay sugerencia por DC/AC (igual que hoy).
- Cantidad fijada para otro modelo: se ignora (vuelve a 0 en
  Dimensionamiento; Producción usa la automática).

## Dependencias

`calculos/dimensionamiento.py`; páginas 4, 6 y 8.

## Criterios de aceptación

1. Sin fijar, Dimensionamiento y Producción dan la misma cantidad (hacia
   arriba): Apartadó con 1 string por MPPT → 2 en las dos.
2. Con 2 fijados y 2 strings por MPPT, Apartadó usa 2 inversores, reparto
   6 + 5 y DC/AC 1,11 en Dimensionamiento y en Producción.
3. Una cantidad fuera de [mínimo, strings] se ajusta y se avisa.
4. 💡 sugiere 2 inversores para Apartadó con 2 strings por MPPT sin fijar.
5. La cantidad fijada solo vale para el mismo modelo de inversor.
6. Producción recorta con la potencia AC de todos los inversores.
7. Presupuesto cotiza `N_inv_total` inversores.
8. Sin fijar y con cantidades exactas, el resultado no cambia (840 ÷ 280 = 3).
9. El manual del Asistente lo explica con el caso Apartadó.
