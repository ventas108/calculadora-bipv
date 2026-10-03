# Candidato alternativo de validación BIPV — NIST 2003

**Estado:** candidato prioritario para revisión del PDF; no aprobado para implementación
**Fecha:** 2026-09-22
**Caso:** *Measured Versus Predicted Performance of Building Integrated Photovoltaics*
**DOI:** [10.1115/1.1532006](https://doi.org/10.1115/1.1532006)

## Motivo de selección

Este artículo es más adecuado que NIST Round 2 para una comparación cuantitativa porque su objetivo explícito es comparar datos experimentales de 12 meses con predicciones de un modelo fotovoltaico desarrollado por Maui Solar Software y Sandia National Laboratories.

El abstract confirma:

- banco experimental BIPV del NIST;
- 12 meses de datos de rendimiento;
- cuatro tecnologías de célula;
- dos paneles por tecnología;
- un panel aislado y otro sin aislamiento posterior;
- datos meteorológicos asociados;
- comparación contra predicciones del modelo IV Curve Tracer/SNL.

## Clasificación arquitectónica

No es un caso multi-fachada. Es un conjunto de paneles multi-tecnología instalado en una configuración experimental de fachada/superficie común. No debe forzarse dentro del contrato de `superficies_bipv` con orientaciones independientes.

Su posible función en la APP sería un benchmark de:

- rendimiento eléctrico DC;
- modelo térmico y efecto del aislamiento posterior;
- respuesta mensual/anual;
- diferencia entre medición y predicción;
- incertidumbre de la simulación.

East2 sigue siendo el caso complementario para geometría y sombra por superficie.

## Datos que el PDF debe confirmar antes de simular

No se debe asumir que el abstract basta. Extraer con página, tabla o figura:

- ubicación, coordenadas y altitud;
- orientación y tilt;
- dimensiones, área activa y área de cobertura;
- marca/modelo y ficha eléctrica de cada tecnología;
- `Voc`, `Isc`, `Vmp`, `Imp`, `Pmax` y coeficientes térmicos;
- configuración de módulos y strings;
- aislamiento posterior y construcción física;
- irradiancia, temperatura, viento y periodo de las series;
- si las series meteorológicas se publican numéricamente o solo en gráficas;
- energía medida y predicha mensual/anual;
- PR, RMSE, MBE, bias u otras métricas;
- modelo de temperatura y parámetros del IV Curve Tracer;
- tablas suplementarias o datos descargables.

## Criterio de aceptación del candidato

Solo se puede construir un escenario de la APP si el PDF aporta como mínimo:

1. ficha eléctrica suficiente para el SDM, o una ficha citada accesible y verificable;
2. datos meteorológicos utilizables o una serie reconstruible sin inventar valores;
3. al menos una métrica final absoluta o una tabla de medición/predicción comparable;
4. geometría y configuración eléctrica suficientemente definidas.

Si falta cualquiera de los cuatro, el resultado será **parcialmente reproducible** o **no reproducible**, y no se añadirá un escenario artificial con defaults.

## Comparación esperada

| Magnitud | Medición NIST | Predicción publicada | APP | Estado |
|---|---:|---:|---:|---|
| POA/irradiancia | Extraer | Extraer si existe | Calcular | Pendiente |
| Energía DC mensual/anual | Extraer | Extraer | Calcular | Pendiente |
| Temperatura de módulo | Extraer | Extraer/calcular | Calcular | Pendiente |
| Efecto del aislamiento | Extraer | Extraer | Calcular si el modelo lo permite | Pendiente |
| RMSE/MBE/bias | Extraer | Publicado o derivar | Calcular | Pendiente |
| Energía AC | Solo si existe inversor | Solo si existe | Probablemente no aplica | Pendiente |

## Riesgos conocidos

- Puede ser el mismo banco experimental que Round 2, pero el artículo de 2003 parece contener la comparación medida-predicha que Round 2 no contiene.
- Puede que los parámetros eléctricos completos estén en tablas o referencias externas; deben verificarse, no inferirse.
- Si el modelo publicado usa datos propietarios del IV Curve Tracer, la APP no podrá reproducirlo exactamente.
- El sistema puede ser DC y no tener inversor; en tal caso la comparación será DC, no AC.
- No valida multi-fachada, sombra 3D ni asignación de inversores por superficie.

## Veredicto provisional

**Candidato prioritario, pendiente de lectura completa del PDF.**

No debe llamarse reproducible hasta comprobar las cuatro condiciones de aceptación y generar una tabla medición-versus-predicción-versus-APP.
