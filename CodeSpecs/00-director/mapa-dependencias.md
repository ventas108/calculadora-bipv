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

  tienen `diseno.md` en estado `aprobado`.
  antes de archivar la Spec.
  calculen la misma magnitud de forma distinta.
- `02-recurso-solar` se divide en dos Specs verticales independientes (app React
      en producción y app Streamlit hermana) — ver `CodeSpecs/02-recurso-solar/vision.md`.
- El motor óptico (IAM/soiling) es alcance de `04-produccion-energia` /
      `05-perdidas-y-temperatura`, no de `02-recurso-solar` (decisión 2026-09-15).
