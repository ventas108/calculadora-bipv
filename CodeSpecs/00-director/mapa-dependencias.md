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
- Solo se consumen contratos publicados por módulos cuyo `diseno.md` esté aprobado.
- Toda dependencia nueva exige validación de integración antes de archivar la Spec.
- Dos módulos no pueden calcular la misma magnitud de forma distinta: deben consumir
      una fuente común o declarar y aprobar explícitamente modelos diferentes.
- `02-recurso-solar` se divide en dos Specs verticales independientes (app React
      en producción y app Streamlit hermana) — ver `CodeSpecs/02-recurso-solar/vision.md`.
- El motor óptico (IAM/soiling) es alcance de `04-produccion-energia` /
      `05-perdidas-y-temperatura`, no de `02-recurso-solar` (decisión 2026-09-15).

## Dependencias transversales de los comparadores Streamlit

```text
02-recurso-solar ───────────────┐
03-dimensionamiento ────────────┼─> comparadores de paneles/orientación
04-produccion-energia ──────────┤
05-perdidas-y-temperatura ──────┘

03-dimensionamiento ────────────┐
04-produccion-energia ──────────┼─> comparador de inversores
06-analisis-financiero ─────────┘

adoptar panel ────────────────────> conserva POA solar base; invalida POA efectiva y 04 -> 06 -> 07
adoptar orientación ──────────────> recalcula POA solar base; invalida POA efectiva y 04 -> 06 -> 07
adoptar inversor ─────────────────> conserva POA solar base; invalida 04 -> 06 -> 07
```

- Los comparadores consumen el motor físico vigente; no mantienen una segunda
  implementación de energía, PR, POA o compatibilidad.
- El Asistente general consume documentación y estado resumido. Los Analistas locales
  consumen la tabla actual de su comparador. Ninguno participa en la cadena de cálculo
  ni puede adoptar alternativas.
- Estas dependencias pertenecen a Streamlit. React solo las incorpora mediante una
  Spec propia que defina contrato, implementación y validación de integración.
- Las desviaciones activas de adopción de inversor, orientación multi-superficie y
  vigencia de tablas están registradas en
  [contratos-entre-modulos.md](contratos-entre-modulos.md). Toda Spec que toque esos
  flujos debe tratarlas como riesgos de integración, no como comportamiento resuelto.
