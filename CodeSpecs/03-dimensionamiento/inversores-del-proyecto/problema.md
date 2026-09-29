# Spec — Cantidad de inversores del proyecto elegida por el diseñador

**Estado:** validación

## Alcance de la fase

📐 Dimensionamiento («🏭 Proyecto completo»), 📊 Producción (potencia AC
total y recorte del inversor), ⚡ Diagrama Unifilar y 📋 Ficha RETIE
(«Cantidad de unidades») y 💼 Presupuesto (cantidad de inversores cotizada),
en el modo de superficie única.

## Problema a resolver

Apartadó contra el informe de la referencia estándar internacional
(29-sep-2026): 308 × JAM66D46-720/LB (11 strings de 28, 221,76 kWp) con
**2** Growatt MAX 100KTL3 LV (200 kW AC, DC/AC 1,11, recorte 0,01 %). La app
daba 282.132 kWh frente a 339.033 kWh porque simulaba **1** inversor y
recortaba ≈ 49.000 kWh/año. Dos causas:

1. 📐 Dimensionamiento cuenta los inversores hacia arriba
   (⌈11 ÷ 10⌉ = 2), pero 📊 Producción los deriva con `round`
   (308 ÷ 280 = 1,1 → 1): las dos páginas no coinciden.
2. La cantidad solo se calcula por capacidad de strings. Con 2 strings por
   MPPT a un inversor le caben 20 strings y la app no puede representar un
   diseño que reparte 11 strings en 2 inversores para bajar la relación
   DC/AC.

Además, 💼 Presupuesto cotiza siempre **1** inversor.

## Contexto

`proyecto_completo` publica `N_inv_total`, que ya usan Unifilar, RETIE y los
comparadores. Producción deriva su propia cantidad con
`escalar_p_ac_nom_por_inversores` para no usar un valor guardado que no
corresponda a su `N_paneles`.
