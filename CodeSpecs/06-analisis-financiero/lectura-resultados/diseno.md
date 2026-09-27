# Diseño — Lectura de resultados de Financiero

**Estado:** validación

## Entradas

- `vpn_de(t)`: VPN con Ley 1715 a la tarifa `t` (la función de la página).
- `comp["sin"]["flujos"]`, tasa de descuento y TRM.

## Salidas

- `umbral_vpn_cero` → `float` (COP/kWh) o `None`.
- `valor_nivelado_energia` → `{usd_kWh, cop_kWh}` o `None`.

## Tipos de datos

Números `float`; los flujos son los diccionarios de `calcular_flujo_caja`
(`año`, `produccion_kWh`, `ingreso_energia_usd`).

## Errores posibles

- VPN `None` (cálculo fallido): se trata como no positivo.
- VPN negativo hasta 100.000 COP/kWh: `None` y la leyenda dice «sin umbral».
- Sin producción: `valor_nivelado_energia` devuelve `None` y la página vuelve a
  la tarifa del año 1 solo como referencia.

## Dependencias

`calculos/financiero.py` (sin cambios).

## Criterios de aceptación

1. Con un umbral real mayor de 600 COP/kWh, la tabla muestra el real (~677 en
   el caso del cliente), no 600.
2. Umbral menor de 600: igual que antes; sin umbral: la leyenda lo dice.
3. La leyenda describe bien los colores.
4. Autoconsumo y Exportación del flujo sin decimales.
5. El LCOE se compara con el valor nivelado de la energía; LCOE < valor
   nivelado exactamente cuando el VPN sin Ley 1715 es positivo.
