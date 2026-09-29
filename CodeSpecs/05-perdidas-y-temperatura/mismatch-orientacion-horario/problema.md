# Spec — Mismatch por orientación hora a hora (con diodos de bypass)

**Estado:** validación

## Alcance de la fase

`calculos/mismatch.calcular_mismatch_orientacion`, la sección «🧭 2. Mismatch
por orientación múltiple» de 🔀 Mismatch, lo que se publica para 📊 Producción
(`factores_mismatch_produccion`) y la cascada de 🔀 Mismatch. No cambia las
fórmulas del SDM ni la energía multi-superficie de 🗺️ Vista 3D (cada
superficie con su propia POA).

## Problema a resolver

Cuando módulos de distinta orientación van **en el mismo string**, la app
calcula la pérdida con los **totales anuales** de cada orientación
(σ²/(2μ²) de la POA anual). Dos fachadas Este y Oeste reciben casi la misma
energía en el año, así que la app da **0.00 %**, aunque en la mañana el Este
recibe mucho sol y el Oeste poco, y en la tarde al revés. Medido con el motor
de `main` + Spec A (Apartadó, TMY sintético):

| Mezcla en el mismo string | App (anual) | Hora a hora con diodos de bypass |
|---|---|---|
| Fachadas Este/Oeste 50/50 | 0.00 % | 14.9 % |
| Fachadas Sur/Este 70/30 | 0.62 % | 15.9 % |
| Techo 10° Sur / 10° Norte 50/50 | 0.02 % | 5.7 % |
| Techo 10° Sur / fachada Sur 80/20 | 4.10 % | 7.9 % |

Además la pérdida llega a Producción como un factor anual en todas las horas,
y la POA de cada orientación se calcula siempre monofacial y con albedo 0.20,
aunque el proyecto tenga otro albedo o panel bifacial.

## Contexto

La Spec A (`05/mismatch-horizonte-coherente`) ya lleva el horizonte hora a
hora hasta Producción; esta Spec usa el mismo camino para la orientación.
