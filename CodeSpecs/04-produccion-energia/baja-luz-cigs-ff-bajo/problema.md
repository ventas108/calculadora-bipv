# Spec — Baja luz de CIGS con factor de forma bajo y «Origen del modelo» en el selector

**Estado:** validación

## Alcance de la fase

Ajuste de baja luz (200 W/m²) del SDM estimado desde ficha y aviso en 🔬 Motor IV.
No cambia el silicio sin dato de 200 W/m² ni los paneles con SDM calibrado.

## Problema a resolver

El usuario eligió el **MiaSolé FLEX-03-70N** (CIGS, 70 W) en el selector «Panel
del catálogo interno» de 🔬 Motor IV y no vio «Origen del modelo». Al revisar
se encontraron tres fallas:

1. «Origen del modelo» solo salía con el panel que llega de 📐 Dimensionamiento,
   no con el elegido en el selector de la página.
2. El ajuste de baja luz solo podía **bajar** el factor de idealidad. Con N_s en
   el catálogo, el factor de partida es 1,0. Con una ficha de factor de forma
   bajo (FF ≈ 0,64), el modelo daba **~110 % a 200 W/m²**: mejor con poca luz
   que en STC, algo que no es físico.
3. No había aviso. El modelo quedaba marcado como «ajustado» aunque estuviera
   13 puntos por encima del objetivo, lo que sobrestima la energía en fachadas
   con mucha luz difusa.

4. **El panel elegido en el selector no se mantenía.** «Usar este panel» solo
   valía en la recarga en que se pulsaba. Al pulsar otro botón, como «Generar
   comparación FF vs G», la página volvía al ASP-ST1-T40 por defecto. El usuario
   lo vio en la gráfica FF vs G (1-oct-2026).

5. **El NOCT arrancaba en 45 °C.** El SDM estimado no traía el NOCT de la
   ficha (48 °C en el 70N), así que la temperatura de celda de Motor IV salía
   3,75 °C más baja: 51,2 °C en vez de 55 °C a 1.000 W/m² y 20 °C de ambiente.

## Contexto

Viene de la Spec `04/sdm-capa-fina-bipv`, que se probó con el FLEX-03 90N: sin
N_s y con FF ≈ 0,78, el ajuste bajaba el factor de 1,35 a 1,05. El 70N es el
caso contrario: hay que subir el factor.
