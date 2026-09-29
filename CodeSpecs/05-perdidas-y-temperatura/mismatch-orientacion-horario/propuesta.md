# Propuesta — Mismatch por orientación hora a hora

**Estado:** validación

## Objetivo

Que la pérdida por mezclar orientaciones en un string sea la de cada hora, con
el efecto de los diodos de bypass, y que llegue a 📊 Producción hora a hora,
una sola vez.

## Alternativa recomendada

Aprobada por el usuario el 29-sep-2026 («luego la Spec B de forma coherente y
sin errores que afecten cálculos futuros en el módulo de producción»).

- **Modelo de string con diodos de bypass (primer orden):** en cada hora la
  corriente de un módulo es proporcional a su irradiancia y su voltaje es
  constante. El string trabaja a la corriente que da más potencia: con la
  corriente de un grupo, aportan los grupos que la alcanzan y los demás quedan
  puenteados por sus diodos. Potencia del string = máx sobre los grupos j de
  G_j × (suma de fracciones de los grupos con G ≥ G_j). Pérdida de la hora =
  1 − potencia del string ÷ potencia ideal (Σ fracción × G).
- La pérdida anual que se muestra es la **ponderada por energía**; también se
  muestra la aproximación anual anterior como referencia.
- La POA de cada orientación usa el **albedo y la configuración bifacial** del
  proyecto (☀️ Recurso Solar).
- **Producción:** el factor de cada hora entra a la POA junto con el horizonte
  (`factores_mismatch_produccion`); el factor escalar ya no lleva la
  orientación cuando el resultado es horario (`mismatch_or_horario = True`).
  Un resultado anterior (sin esa marca) se usa como antes.
- El resultado se recalcula solo si cambian las orientaciones, el albedo, la
  configuración bifacial o el año típico.
- Manual del Asistente con el caso Este/Oeste.

## Alternativas descartadas

- σ²/(2μ²) hora a hora: es una aproximación para diferencias pequeñas; con
  Este/Oeste da 24.1 %, más que el límite físico con diodos (14.9 %).
- Curva I-V completa de cada módulo con el SDM: más exacta, pero mucho más
  costosa; el modelo de primer orden captura el efecto dominante (la corriente
  la marca el grupo más débil o los diodos lo sacan).

## Fuera de alcance

- Strings de distinta orientación en paralelo en el mismo MPPT (pérdida por
  voltaje, pequeña).
- La POA base de Producción sigue siendo la de la orientación principal del
  proyecto; para superficies con su propia POA se usa 🗺️ Vista 3D.
