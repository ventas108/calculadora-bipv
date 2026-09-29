# Spec — «Proyecto completo» de 📐 Dimensionamiento cabe en el área y respeta el total de cadenas

**Estado:** validación

## Alcance de la fase

Las dos secciones «🏭 Proyecto completo» de `pages/4_📐_Dimensionamiento.py`
(prorrateo preliminar y resultado de «▶️ Optimizar N paneles/string») y los
totales que publican: `N_inv_total`, `N_paneles_granja`, `P_dc_total_kWp`.

## Problema a resolver

La página arma un inversor con todos sus MPPT llenos y redondea hacia arriba
cuántos caben en el área útil:
`inversores = ⌈área útil ÷ área de un inversor lleno⌉`,
`módulos = inversores × módulos de un inversor lleno`.

En la comparación con PVsyst del proyecto agrivoltaico de Apartadó
(29-sep-2026): área útil 957 m² (2,393 m² × 40 %), JA Solar JAM66D46-720/LB,
28 en serie, Growatt MAX 100KTL3 LV con 10 MPPT y 1 string por MPPT.

- Un inversor lleno: 280 módulos, 869.8 m².
- La app: ⌈957 ÷ 869.8⌉ = **2 inversores, 560 módulos, 403.2 kWp, 1,740 m²**,
  y «Cobertura 100 %» (el valor tiene tope y esconde el exceso).
- PVsyst: **308 módulos (11 strings), 222 kWp, 2 inversores, DC/AC 1.11**.

Esos totales llegan a 📊 Producción (número de módulos), ⚡ Diagrama Unifilar,
📋 Ficha RETIE y los comparadores. Además, el «N total de cadenas» que declara
el usuario solo cambia los strings por MPPT; no fija el total del proyecto.

## Contexto

La relación DC/AC de la página se evalúa con un inversor lleno (201.6 kWp
sobre 100 kW = 2.02), no con el diseño real.
