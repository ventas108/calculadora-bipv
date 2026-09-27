# Propuesta — Lectura de resultados de Financiero

**Estado:** validación

## Objetivo

Que el umbral, la tabla de flujo y la lectura del LCOE digan al cliente lo
mismo que TIR y VPN.

## Alternativas consideradas

1. **Subir el tope fijo de la búsqueda** (p. ej. a 5.000 COP/kWh). Descartada:
   vuelve a fallar con otro proyecto.
2. **Ampliar el rango hasta encontrar VPN positivo** y decir «sin umbral» si
   no se alcanza. Recomendada.
3. **Comparar el LCOE con la tarifa promedio sin descontar.** Descartada: el
   LCOE está descontado; la comparación justa es con el valor de la energía
   descontado igual.

## Alternativa recomendada

Nuevo `calculos/lectura_financiera.py`:

- `umbral_vpn_cero`: búsqueda binaria que duplica el tope mientras el VPN siga
  negativo (hasta 100.000 COP/kWh); `None` si no hay umbral.
- `valor_nivelado_energia`: Σ ingreso descontado ÷ Σ producción descontada.
  LCOE < valor nivelado ⇔ VPN sin Ley 1715 > 0.

En la página: umbral ordenado en la tabla y leyenda corregida; formato sin
decimales; nota «Cómo leer el LCOE» bajo el comparativo; el resumen y la
métrica comparan el LCOE con el valor nivelado.

## Fuera de alcance

- Cambiar la fórmula del LCOE o los escenarios de la sensibilidad.
