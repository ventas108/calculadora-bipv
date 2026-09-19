# Módulo 08 — Interfaz

**Estado:** completado

## Alcance de la fase

Presentación al usuario, componentes de interfaz, interacción y estado de la aplicación.

## Problema a resolver

El contrato de página de la app (login, bloqueo de traducción, banner de
proyecto activo, verificación de prerequisitos) nunca quedó formalizado en
CodeSpecs, aunque se repite idéntico en las ~20 páginas de `bipv_python/pages/`.
La exploración no encontró un gap de coherencia nuevo: `utils/ui.py` es
puramente presentacional (no restaura ni invalida datos de `session_state`) y
el riesgo real de sesiones/pestañas obsoletas ya lo cierran los gates de
`03`–`06` (diseño vencido, firmas de Producción/bypass, verificación de
payload).

## Contexto

Regularización documental, no correctiva: fijar el contrato de página
compartido (`requerir_login()` → `bloquear_traduccion()` +
`mostrar_proyecto_activo()` → prerequisitos con `st.stop()`) y dejar
constancia explícita de que la vigencia de datos se garantiza aguas arriba,
no en la capa de interfaz.

