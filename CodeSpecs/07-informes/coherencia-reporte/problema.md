# Spec — Coherencia del Reporte

**Estado:** validación

## Alcance de la fase

Revisión de coherencia antes de generar el 📄 Reporte. Incluye la energía
que guardan 🌿 Impacto CO₂ y 💰 Financiero, la verificación PVGIS–PVWatts
con paneles bifaciales y el texto de CO₂ en granjas. No cambia ningún cálculo
de energía.

## Problema a resolver

Informe real «Granja Solar Apartadó 3» (403,2 kWp, 2-oct-2026):
1. «3 × Growatt MAX 100KTL3 LV · AC 300 kW · DC/AC 1,34» junto a «Reparto
   7 + 7 + 7 + 7» y a los bloques INV-1 a INV-4. 📊 Producción se había
   simulado con 3 inversores y 📐 Dimensionamiento repartía en 4.
2. Sin sección de Producción.
3. CO₂ de 6,3 t/año: 🌿 Impacto CO₂ se abrió sin Producción y usó los
   50.000 kWh de ejemplo. Con los ~604 MWh de la granja son ~76 t/año.
4. «Diferencia PVGIS–PVWatts −7,1 %»: la POA de PVGIS incluía la cara trasera
   (+8,1 %) y PVWatts es monofacial. La cara frontal coincide (~0,4 %).
5. El texto final de CO₂ decía «la fachada BIPV» en una granja.

## Contexto

Cada página guarda su último cálculo en la sesión y el reporte los junta sin
comprobar que sean del mismo momento.
