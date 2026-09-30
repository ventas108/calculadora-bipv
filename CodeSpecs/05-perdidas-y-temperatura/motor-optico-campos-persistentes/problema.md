# Spec — Motor Óptico: los campos no vuelven a su mínimo al cambiar de página

**Estado:** validación

## Alcance de la fase

Los 8 campos de 🔆 Motor Óptico (NOCT, γ, tipo de vidrio, b₀ personalizado,
transparencia, montaje, soiling personalizado, auto-limpieza vertical, IAM
difusa).

## Problema a resolver

Urabá (30-sep-2026), después de la Spec `05/motor-optico-ficha-termica`: el
usuario puso NOCT 45 °C y γ −0,29 %/°C con «Usar los de la ficha», guardó y
al volver vio **NOCT 35 °C y γ −0,70 %/°C**, los **mínimos** de los campos.

Causa: cada campo usaba la misma clave para el dato y para el widget
(`key="mo_noct"`). Streamlit borra la clave de un widget al abrir otra
página o recargar; al volver, el campo arrancaba en su mínimo, y al guardar
el proyecto desde 🏠 Proyecto se guardaba ese mínimo. El auto-llenado desde
la ficha no lo corregía porque solo corre al cambiar de panel. 📊 Producción
usa el NOCT del Motor Óptico: la energía salía más alta en silencio.

## Contexto

Mismo defecto que se corrigió en 💰 Financiero (Spec
`06-analisis-financiero/parametros-persistentes`). El usuario pidió
«solucionalo para que no vuelva a suceder».
