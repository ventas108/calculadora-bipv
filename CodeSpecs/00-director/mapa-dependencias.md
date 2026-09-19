# Mapa de dependencias

```text
01-datos-proyecto
      ↓
02-recurso-solar
      ↓
03-dimensionamiento
      ↓
04-produccion-energia
      ↓
05-perdidas-y-temperatura
      ↓
06-analisis-financiero
      ↓
07-informes
      ↓
08-interfaz
      ↓
09-despliegue
```

## Reglas

 - El orden de fases no sustituye las dependencias de datos en ejecución: aunque
       `04-produccion-energia` antecede a `05-perdidas-y-temperatura` en la hoja de
       ruta, el Motor Óptico de `05` publica POA sin térmico que `04` consume para
       su simulación. Esa dependencia de runtime es `05 → 04`.
  tienen `diseno.md` en estado `aprobado`.
  antes de archivar la Spec.
  calculen la misma magnitud de forma distinta.
- `02-recurso-solar` se divide en dos Specs verticales independientes (app React
      en producción y app Streamlit hermana) — ver `CodeSpecs/02-recurso-solar/vision.md`.
- El motor óptico (IAM/soiling) es alcance de `04-produccion-energia` /
      `05-perdidas-y-temperatura`, no de `02-recurso-solar` (decisión 2026-09-15).
