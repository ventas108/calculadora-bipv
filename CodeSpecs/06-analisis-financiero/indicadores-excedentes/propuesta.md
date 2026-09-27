# Propuesta — Indicadores de Financiero con la tarifa de excedentes

**Estado:** validación

## Objetivo

Que los indicadores de la página usen el mismo reparto autoconsumo/excedentes
que el flujo de caja, y que la comparación con/sin batería compare el mismo
sistema solar.

## Alternativas consideradas

1. **Quitar la métrica y la sección.** Descartada: son útiles para el cliente.
2. **Calcular el escenario sin batería con `balance_mensual` otra vez.**
   Descartada: el balance horario no está disponible en Financiero.
3. **Deducir el escenario sin batería de las métricas del balance**
   (autoconsumo directo = autoconsumo total − descarga de la batería).
   Recomendada: exacta para el balance mensual y el horario.

## Alternativa recomendada

Nuevo módulo `calculos/indicadores_excedentes.py`:

- `ahorro_anual_cop`: autoconsumo × tarifa + excedentes × tarifa de excedentes.
- `hay_bateria`: la sección de batería solo aparece con CAPEX de batería o
  energía descargada.
- `escenario_sin_bateria`: energía y fracción exportada del mismo sistema sin
  batería, valorada con la misma tarifa de excedentes.

Complemento (26-sep-2026):

- `aviso_sobredimension`: aviso 🟡 si, sin balance, la energía supera 1,2 ×
  el consumo anual de 🏠 Proyecto; explica por qué TIR y VPN salen altos y
  los pasos para corregirlo. No bloquea el cálculo.
- `desglose_capex`: quinta tarjeta «Imprevistos (x %)» (u «Otros
  (Presupuesto)» con el Presupuesto vinculado) para que las tarjetas sumen el
  CAPEX bruto.

## Fuera de alcance

- La tabla de sensibilidad por tarifa (cada fila supone vender toda la
  energía a esa tarifa, por diseño).
- La fracción de equipos para la Ley 1715 del escenario sin batería.
