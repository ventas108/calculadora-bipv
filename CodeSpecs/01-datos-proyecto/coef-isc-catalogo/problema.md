# Spec — Coeficiente de temperatura de Isc (α) en el catálogo de paneles

**Estado:** validación

## Alcance de la fase

Lectura y edición de α Isc en 📋 Catálogo de Paneles y su uso en 🔬 Motor IV.

## Problema a resolver

El usuario (1-oct-2026), con el JAM66D46-720/LB: «esa columna "coeficiente de
temperatura de Isc" no existe… debería existir desde que importé el Excel
real». 🔬 Motor IV avisaba «Coef. Temp. Isc (α) no definido — se usará
default por tecnología» para todos los paneles del Excel.

## Contexto

- El Excel real del catálogo (26 columnas) nunca tuvo α Isc; tiene β Voc
  (`CoefVoc_C`) y γ Pmax (`CoefT_C`).
- «Agregar desde PDF» sí guarda α en `CoefIsc_C` (crea la columna), pero
  `cargar_catalogo_paneles` lo descartaba: dejaba `alpha_sc = None` y nunca
  llenaba `Tk_alfa`, que es la clave que leen Motor IV y el modelo IV.
- La tabla «Editar / Eliminar» no tenía la columna.
