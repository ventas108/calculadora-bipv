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
adoptar inversor ─────────────────> conserva Motor Óptico; invalida 04 -> 06 -> 07
```

Persistencia física multi-superficie:

```text
02-recurso-solar (TMY vigente) ──┐
03-dimensionamiento (eléctrica) ─┼─> payload firmado / restauración todo-o-nada
05-perdidas-y-temperatura ───────┘                    │
                                                     ├─> 06-analisis-financiero
                                                     ├─> 07-informes
                                                     └─> 08-interfaz
```

Energía multi-superficie (Vista 3D, Streamlit):

```text
02-recurso-solar (TMY) ───────────────> POA firmada por superficie (05)
03-dimensionamiento (panel, inversor, ─┬─> panel por superficie (05) ──> η del panel
      temperaturas de diseño)          └─> diseño eléctrico por superficie (03, Spec A)
05 sombra 3D por superficie ──────────────────────────────┐
POA + η + diseño eléctrico + sombra ──> simplificado / bypass / físico
                                         └─> publicación única con origen ──> 06, 07, 08
                                             (energía + estado eléctrico + sistema:
                                              kWp, módulos por panel, reparto mensual)

publicación multi-superficie ──> 06 Financiero, Baterías y CO₂ (sin 📊 Producción,
                                 sin mezclar kWp/módulos de superficie única)

cambio de panel o de diseño eléctrico ──> retira publicación, bypass, MPPT y físico
                                          (conserva POA y sombra; aviso fijo en
                                           «Integrar» hasta volver a publicar)
cambio de geometría o montaje ────────> invalida POA y sombra de esa superficie
```

- Con `multisup_activo`, 💰 Financiero, 🔋 Baterías y 🌿 CO₂ dependen solo de la
  publicación multi-superficie (Spec `06-analisis-financiero/sistema-multisuperficie`),
  no de 📊 Producción; 💼 Presupuesto sigue en superficie única (H3, Spec propia).

- Los comparadores consumen el motor físico vigente; no mantienen una segunda
  implementación de energía, PR, POA o compatibilidad.
- El Asistente general consume documentación y estado resumido. Los Analistas locales
  consumen la tabla actual de su comparador. Ninguno participa en la cadena de cálculo
  ni puede adoptar alternativas.
- Estas dependencias pertenecen a Streamlit. React solo las incorpora mediante una
  Spec propia que defina contrato, implementación y validación de integración.
- La adopción global de orientación está bloqueada cuando `multisup_activo=True`;
      la orientación multi-superficie pertenece a Vista 3D, superficie por superficie.
- La persistencia física no sustituye el modelo simplificado: es opt-in y su
      restauración exige firmas coincidentes antes de alimentar los consumidores.
