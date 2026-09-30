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
🔆 Motor Óptico (IAM, suciedad) + 🔀 Mismatch (fabricación, cables, horizonte)
   + 🔬 Motor IV (SDM del panel) ──> cadena de pérdidas por superficie (05)
POA + η + diseño eléctrico + sombra + cadena ──> simplificado / bypass / físico
                                         └─> publicación única con origen ──> 06, 07, 08
diseño eléctrico (grupos, diagnóstico) ──> topología eléctrica ──> 07 Unifilar y Ficha RETIE
      (+ batería de Baterías y Balance, optimizadores del proyecto)
                                             (energía + estado eléctrico + sistema:
                                              kWp, módulos por panel, reparto mensual)

publicación multi-superficie ──> 06 Financiero, Baterías y CO₂ (sin 📊 Producción,
                                 sin mezclar kWp/módulos de superficie única)

cambio de panel o de diseño eléctrico ──> retira publicación, bypass, MPPT y físico
                                          (conserva POA y sombra; aviso fijo en
                                           «Integrar» hasta volver a publicar)
cambio de geometría o montaje ────────> invalida POA y sombra de esa superficie
```

🌾 Granja FV (Streamlit, 29 y 30-sep-2026, fases 1 a 5):

```text
01 Proyecto (tipo «Granja fotovoltaica», terreno, tilt, azimut) ─┐
03 Dimensionamiento (panel, N_serie, inversores, reparto) ───────┼─> granja_fv.calcular_campo (03)
04 Producción (N_paneles_final) ─────────────────────────────────┘      │  (única geometría; también
                                                                        │   la usa 🗺️ Vista 3D)
      ├─ fase 2 ─> filas_energia / bifacial_cfg ──> 02 Recurso Solar: calcular_poa(filas=…)
      │            (sombra entre filas monofacial; infinite_sheds bifacial + cara trasera)
      │            ──> poa_df ──> 05 Motor Óptico / Mismatch ──> 04 Producción ──> 06, 07
      ├─ fase 3 ─> agrivoltaica.luz_en_el_suelo + paso_maquinaria (solo informa)
      ├─ fase 4 ─> seguidor.comparar_seguidor_fijo (solo compara; 04 sigue fija)
      └─ fase 5 ─> granja_electrico.diseno_desde_estado (recalcula siempre)
                   ├─> 07 Diagrama Unifilar: un tramo DC por string ──> perdida_ohmica_unifilar ──> 04
                   └─> 07 Ficha RETIE: checks «Granja: …» (caída de tensión ≤ 3 %, NTC 2050)
```

- Unifilar y Ficha RETIE solo usan el diseño de la granja cuando el tipo de
  instalación es «Granja fotovoltaica» y el proyecto es de superficie única.
- Las secciones 6 y 7 de 🌾 Granja FV guardan su resultado con una firma de la
  geometría y lo ocultan si cambia; la fase 5 no guarda resultado (se recalcula).

Catálogos y análisis financiero (Streamlit, 26 y 27-sep-2026):

```text
📋 Catálogo Paneles ────────┐
🔌 Catálogo Inversores ─────┼─> precio vigente ──> 06 Financiero y 💼 Presupuesto
🔋 Catálogo Baterías ───────┘   (se lee al abrir la página; nunca una copia vieja)
🔌 ficha del inversor (P AC nominal) ──> 03 relación DC/AC (sin dato: «no evaluable»)
🔋 Baterías y Balance ──> frac_exportada ──┬─> flujo de caja (TIR, VPN, payback)
Financiero: tarifa de excedentes ─────────┘   └─> ahorro año 1 y escenario sin batería
cualquier dato del cálculo cambia ──> Financiero retira el resultado guardado
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
