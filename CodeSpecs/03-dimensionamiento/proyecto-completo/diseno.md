# Diseño — «Proyecto completo» cabe en el área y respeta el total de cadenas

**Estado:** validación

## Entradas

`proyecto_completo(panel, area_util_m2, N_serie, N_strings_tracker, N_mppt,
N_total_cadenas=0, P_ac_nom_W=None)` en `calculos/dimensionamiento.py`.

## Salidas

`dict` con:

- `fuente`: `"declarado"` o `"area"`.
- `strings_que_caben`: ⌊área útil ÷ (N_serie × área del módulo)⌋.
- `N_strings_total`, `N_inversores`, `reparto` (strings por inversor, de
  mayor a menor), `capacidad_strings_inversor` (MPPT × strings por MPPT).
- `N_paneles`, `P_dc_kWp`, `area_m2`, `cobertura_pct` (sin tope),
  `cabe` (`bool`), `faltan_m2`.
- `dcac` (resultado de `evaluar_relacion_dc_ac` con la potencia AC total) y
  `dcac_max_inversor` (ratio del inversor más cargado, o `None`).

La página muestra estos valores en las dos secciones y publica
`N_inv_total`, `N_paneles_granja`, `P_dc_total_kWp` y
`reparto_strings_inversores`.

## Tipos de datos

Enteros para strings, inversores y módulos; `float` para kWp, m² y %.

## Errores posibles

- Área útil menor que un string: 0 strings, 0 inversores, `cabe=False` y el
  aviso dice cuántos m² necesita un string.
- Datos del panel sin área o `N_mppt < 1`: `ValueError` (la página ya exige
  trackers válidos antes de llamar).

## Dependencias

`evaluar_relacion_dc_ac` (misma escala de colores).

## Criterios de aceptación

1. Apartadó sin declarar cadenas (957.2 m², 28 × 3.106 m², 10 MPPT × 1):
   11 strings, 2 inversores, reparto 6 + 5, 308 módulos, 221.76 kWp, DC/AC
   1.11 con 2 × 100 kW.
2. Con 11 cadenas declaradas: lo mismo.
3. Con 20 cadenas declaradas en 957 m²: 560 módulos, `cabe=False` y los m²
   que faltan.
4. Nunca más módulos que los que caben cuando no hay cadenas declaradas.
5. La página usa `proyecto_completo` en las dos secciones y ya no calcula
   `ceil(área ÷ área de un inversor)`.
6. El manual del Asistente explica el cálculo con el caso Apartadó.
