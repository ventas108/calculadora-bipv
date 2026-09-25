# Spec — Panel por superficie en Vista 3D multi-superficie

**Estado:** diseño

## Alcance de la fase

App hermana Streamlit (`bipv_python/`): ⚙️ Superficies BIPV, Producción por
superficie y secciones 5 (bypass) y 6 (MPPT) de `pages/9_🗺️_Vista_3D.py`,
modo físico (`calculos/adaptador_multisuperficie.py`) y persistencia
(`calculos/persistencia_multisuperficie.py`). Evidencia verificada contra
`main` `db7e96a6`.

## Problema a resolver

1. **Todas las superficies usan una sola referencia de panel.** Un proyecto
   real puede llevar vidrio BIPV semitransparente en fachada y módulo opaco
   en cubierta, pero no hay dónde indicarlo:
   - bypass y MPPT: un solo selector de panel para todas las superficies
     (líneas 2157 y 2365);
   - modo físico: `construir_proyecto_desde_session_state` pasa el mismo
     `panel_dict` global a cada superficie (líneas 19–21 y 44), aunque
     `superficie_nueva` y `simular_mppt_compartido` ya aceptan un panel por
     superficie o grupo;
   - persistencia: un solo `electrical.panel` (línea 191).
2. **La energía simplificada no usa el panel: usa η = 16 % fijo.** Las
   cuatro lecturas de `st.session_state.get("eta_panel", 0.16)` (líneas
   1476, 1561, 1986 y 1955) leen una clave que **ninguna página escribe**, así
   que siempre valen 0,16. Esa energía alimenta el resumen POA, «🔗 Usar
   sistema multi-superficie en Financiero» (origen `simplificado`),
   Producción por superficie y el bypass (línea 2249: energía simplificada ×
   factor de bypass). Solo el modo físico usa el panel real.
3. **Strings estimados con el módulo equivocado.** `strings_superficie`
   estima el paralelo con el área del panel elegido en el selector común,
   no con la del módulo de cada superficie, y toma el N serie de
   Dimensionamiento, dimensionado para el panel del proyecto.

## Impacto medido

Prueba en producción del 24-sep-2026, «Fachada principal», panel del
proyecto `ASP-ST1-T40` (CdTe 40 % transparente, 63 W en 0,72 m²):

| Dato | Hoy | Con la η del panel |
|---|---|---|
| η usada | 16 % (fija) | 63 / (0,72 × 1000) = **8,75 %** |
| Fachada, 97,3 m², POA 1004 kWh/m², PR 0,78 | 12.191 kWh/año | **6.667 kWh/año** |

La energía publicada en Financiero, Baterías y CO₂ con origen `simplificado`
o `bypass_csv` está sobrestimada un 83 % para este panel. Con un panel más
eficiente que 16 % quedaría subestimada.

## Contexto

- Relacionadas: `08-interfaz/panel-proyecto-bypass-mppt` (panel del
  proyecto por defecto), `05/publicacion-energia-multisuperficie` (origen
  único), `05/persistencia-multisuperficie`.
- Hallazgos vistos en la misma revisión, **fuera de esta Spec**:
  - H2: el PR de la energía simplificada lee `pr_sistema` (minúscula),
    clave que tampoco se escribe; 📊 Producción escribe `PR_sistema`. Hoy
    siempre vale 0,78.
  - H3: 💼 Presupuesto no lee las superficies de Vista 3D; cuenta módulos
    con `N_paneles_final` de Dimensionamiento.
