# Spec — Temperaturas de diseño estables en 📐 Dimensionamiento

**Estado:** validación

## Alcance de la fase

Las tres temperaturas de diseño de 📐 Dimensionamiento (`T_min_diseno`,
`T_cel_realista`, `T_cel_extremo`), su cálculo desde el año típico (TMY) y
«💾 Guardar configuración» de 🏠 Proyecto.

## Problema a resolver

Reportado por el usuario el 29-sep-2026 en la comparación con PVsyst de
Apartadó: las temperaturas salieron en 0 y, tras reiniciar, en
20.0 / 55.0 / 64.0 (los valores fijos de la ciudad) en vez de
20.9 / 54.2 / 63.6 (los del TMY de PVGIS 5.3). Con 20.0 °C el Voc en frío
sube a 1,389 V, el margen baja a 7.4 % y N = 28 sale en ALERTA («Ningún N
válido»). Tres causas:

1. Los tres campos usan la misma clave para el dato y para el campo:
   Streamlit borra esa clave al abrir otra página y, al volver, la página la
   vuelve a llenar con los valores de la ciudad.
2. «💾 Guardar configuración» de 🏠 Proyecto escribe siempre los valores de
   la ciudad encima de los del TMY.
3. El recálculo desde el TMY solo ocurre cuando cambia el nombre de la
   ciudad. Otra versión de PVGIS, otras coordenadas o otro panel (NOCT) no
   lo disparan.

## Contexto

Producción, Reporte PDF, Vista 3D y el Comparador de inversores leen las
mismas claves. Es el mismo defecto que se corrigió en 💰 Financiero con
`campos_persistentes.campo_persistente` (Spec 06/parametros-persistentes).
