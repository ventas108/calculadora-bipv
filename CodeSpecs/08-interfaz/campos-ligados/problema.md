# Spec — Campos ligados a su dato en Dimensionamiento, Mismatch y Producción

**Estado:** validación

## Alcance de la fase

📐 Dimensionamiento (`N_str_tr`), 🔀 Mismatch (`bypass_n_series`,
`bypass_n_parallel`, `bypass_panel`) y 📊 Producción
(`produccion_usar_iv`), más una guarda para toda la app.

## Problema a resolver

Auditoría tras la Spec `05/motor-optico-campos-persistentes` (NOCT y γ que
volvían a su mínimo): el mismo patrón —la clave del dato usada como clave del
widget— estaba en tres páginas más. Streamlit borra la clave de un widget al
abrir otra página o recargar:

- 📐 Dimensionamiento: «N_strings por tracker» volvía a **1** (su mínimo) y
  así entraba al diseño y a los escenarios.
- 🔀 Mismatch: módulos en serie, strings en paralelo y panel del bypass
  volvían al valor por defecto (8 o 400 ÷ Voc, reparto, ASP-ST1-T40).
- 📊 Producción: el modo «Usar curva IV real (Motor IV)» se **apagaba** solo,
  y la firma de vigencia lo notaba como un cambio.

## Contexto

El usuario pidió «prepara otra Spec con su PR para arreglar esos tres de la
misma forma» (30-sep-2026).
