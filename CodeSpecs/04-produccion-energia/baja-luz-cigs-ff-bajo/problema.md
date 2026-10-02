# Problema — Baja luz de CIGS con factor de forma bajo y «Origen del modelo» en el selector

**Estado:** validación

## Caso real (1-oct-2026)

El usuario eligió el **MiaSolé FLEX-03-70N** (CIGS, 70 W) en el selector «Panel
del catálogo interno» de 🔬 Motor IV, después del despliegue de la Spec
`04/sdm-capa-fina-bipv`. Esperaba ver «Origen del modelo» con CIGS, celdas y
97 % a 200 W/m², y no salió.

## Causas

1. **«Origen del modelo» solo salía con el panel de 📐 Dimensionamiento.** Con el
   panel elegido en el selector de la página no se mostraba.
2. **El ajuste de baja luz solo podía bajar el factor de idealidad.** Con N_s en
   el catálogo, el factor de partida es 1,0. Con una ficha de factor de forma
   bajo (FF ≈ 0,64), el modelo daba **~110 % a 200 W/m²**, es decir, mejor
   eficiencia con poca luz que en STC, algo que no es físico. Para llegar al
   97 % había que subir el factor, pero la búsqueda llegaba solo hasta 1,0.
3. **No había aviso.** El modelo quedaba marcado como «ajustado» aunque estuviera
   13 puntos por encima del objetivo. En fachadas, donde hay mucha luz difusa,
   eso sobrestima la energía.
