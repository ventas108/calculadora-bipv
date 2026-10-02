# Propuesta — Coherencia del Reporte

**Estado:** validación

## Objetivo

Que el reporte no pueda salir para el cliente con datos contradictorios, y
que el diseñador sepa qué página volver a ejecutar.

## Alternativa recomendada

- `calculos/coherencia_reporte.py`: `revisar_coherencia_reporte(estado)`
  compara:
  - inversores de Producción frente al reparto y a la cantidad fijada en
    Dimensionamiento;
  - energía de Producción frente a la de CO₂ y Financiero (2 %) o escrita a
    mano;
  - que exista la Producción;
  - el resumen del diseño guardado al simular Producción
    (`produccion_resumen_diseno`) frente al diseño actual.
- 📄 Reporte: errores 🔴 con su acción. El botón «Generar» queda bloqueado,
  salvo «Generar de todas formas (solo para revisión interna)».
- 🌿 Impacto CO₂ y 💰 Financiero guardan la energía usada y si fue manual
  (`co2_e_ac_kWh`, `co2_e_ac_manual`, `fin_e_ac_kWh`, `fin_e_ac_manual`). Si
  falta el dato, el CO₂ deduce la energía de su factor.
- ☀️ Recurso Solar: con el modelo bifacial, compara con PVWatts la cara
  frontal.
- Texto de CO₂ según el tipo de instalación.

## Alternativas descartadas

- Recalcular todo al generar el reporte: tardaría minutos y escondería el
  problema.
- Solo avisar sin bloquear: el informe de Apartadó habría salido igual.

## Fuera de alcance

Recalcular automáticamente las páginas desactualizadas.
