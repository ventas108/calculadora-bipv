# Spec — Curva de baja irradiancia de la ficha en 🔬 Motor IV

**Estado:** validación

## Alcance de la fase

Calibración de baja luz del SDM estimado desde ficha (paneles del catálogo
Excel) y su presentación en 🔬 Motor IV y 📋 Catálogo de Paneles. No cambia
los SDM calibrados (ASP-ST1) ni los SDM manuales.

## Problema a resolver

Motor IV solo aceptaba un dato de baja luz: la eficiencia relativa a 200 W/m²
(«η rel. 200 W/m² (%)»). Sin él, a los CIGS les aplicaba el 97 % por defecto.
Muchas fichas traen en cambio la gráfica «Performance at low irradiance» con
varios puntos, y no había dónde escribirlos.

Caso real: teja solar **Hanergy HW-MQSB-V1** (CIGS, 25 a 32 W). La ficha dice
80 % a 300 W/m², 88 % a 400, 93 % a 500 y 96 % a 600. Con el 97 % por defecto,
Motor IV daba ~99 a 100 % en todo ese rango, sobrestimando la energía en las
horas nubladas.

Además, la estimación tardaba ~12 s por panel y se repetía en cada recarga
de Motor IV.

## Contexto

Viene de las Specs `04/sdm-capa-fina-bipv` y `04/baja-luz-cigs-ff-bajo`, que
ajustan el factor de idealidad con R_s re-anclado a la Pmax de la ficha.
