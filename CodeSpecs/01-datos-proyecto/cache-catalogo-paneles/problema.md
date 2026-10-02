# Spec — Caché del catálogo de paneles

**Estado:** validación

## Alcance de la fase

Lectura del catálogo de paneles (`datos/catalogo_paneles_excel.py`). No
cambia ningún cálculo ni dato del catálogo.

## Problema a resolver

El usuario reportó que la app se puso «muy lenta» (2-oct-2026, proyecto
Urabá). Causa:
- El PR #107 insertó la función `_texto_celda` justo debajo del
  `@st.cache_data` de `cargar_catalogo_paneles`. La caché quedó en la función
  pequeña.
- Desde entonces, el catálogo (3.128 paneles) se releía del Excel en cada
  clic: de 5 a 9 s en 🔬 Motor IV, 📐 Dimensionamiento, ⚡ Producción y 💰
  Financiero.
- Aun con la caché original, `st.cache_data` entrega una copia serializada:
  ~2 s por llamada.

## Contexto

El catálogo de inversores (111 equipos) sí tiene caché con el mtime del
archivo.
