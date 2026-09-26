# Spec H-D5 — Financiero, Baterías y CO₂ con el sistema multi-superficie publicado

**Estado:** implementación

## Alcance de la fase

App Streamlit (`bipv_python/`): publicación de la energía multi-superficie
(`calculos/publicacion_multisuperficie.py`, `pages/9_🗺️_Vista_3D.py`,
`calculos/adaptador_multisuperficie.py`) y sus consumidores 💰 Financiero,
🔋 Baterías y Balance, 🌿 Impacto CO₂ y 💼 Presupuesto. Evidencia verificada
contra `main` `d20d8807` y en la prueba de producción D5 de la fase A2
(25-sep-2026).

## Problema a resolver

1. **Financiero ignora la energía multi-superficie sin avisar.** Solo la usa si
   en la sesión corrió 📊 Producción (`produccion_ok`). Producción simula el
   sistema de superficie única de 📐 Dimensionamiento, que puede no existir o
   estar bloqueado («No hay N/string validado»). En la prueba D5 había
   7.552 kWh/año publicados desde Vista 3D y Financiero pasó a modo manual con
   5.695 kWh/año y «cobertura 99 %», sin mencionar la energía publicada.
2. **Financiero mezcla dos sistemas.** Aun con Producción, la energía sale de
   Vista 3D pero la potencia (`P_stc_kW_sistema`) y los módulos
   (`N_paneles_final`) salen del sistema de superficie única. El CAPEX
   (módulos × costo, kWp × costo de inversor y estructura), el OPEX y el
   umbral de la Ley 1715 se calculan con otro sistema: TIR, VPN, payback y
   LCOE quedan mal. En la prueba: 7.552 kWh/año con 8,06 kWp y 128 módulos,
   cuando el diseño de Vista 3D tiene 6,37 kWp y 34 módulos.
3. **Un solo precio por módulo.** Con paneles distintos por superficie
   (ASP-ST1-T40 en fachada, SPR-E20-327 en techo) el costo de módulos usa un
   único USD/módulo.
4. **Baterías usa la producción mensual de superficie única** (`df_mensual_produccion`)
   para el balance aunque la energía anual mostrada sea la multi-superficie.
5. **CO₂ muestra kWp y módulos de superficie única** junto a la energía
   multi-superficie.
6. **Presupuesto** arma el CAPEX con los módulos y kWp de superficie única
   (hallazgo H3) y Financiero puede vincularlo sin advertir la diferencia.

## Ejemplo del impacto

Prueba D5 (Bogotá): Vista 3D publica 7.552 kWh/año con fachada ASP-ST1-T40
(18 módulos) y techo SPR-E20-327 (16 módulos), 6,37 kWp. Financiero muestra
«Producción no detectada», 5.695 kWh/año, 8,06 kWp y 128 módulos: el análisis
parece corresponder al diseño de Vista 3D, pero no.

## Contexto

- Spec `03-dimensionamiento/diseno-electrico-multisuperficie` (A2): grupos de
  strings por superficie, área instalada y `multisup_estado_electrico`.
- Spec `05-perdidas-y-temperatura/publicacion-energia-multisuperficie`:
  publicación única y todo o nada de la energía multi-superficie.
- H3 (Presupuesto ignora las superficies) queda registrado para su propia
  Spec; aquí solo se advierte la diferencia.
