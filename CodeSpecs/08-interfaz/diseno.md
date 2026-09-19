# Diseño — Interfaz

**Estado:** completado

## Entradas

- `session_state` ya poblado por módulos previos (`nombre_proyecto`, `ciudad`,
  banderas `_ok`, `auth_email`).
- Sesión autenticada (`calculos/auth.py::requerir_login()`).

## Salidas

- Bloqueo de traducción automática del navegador (evita que Chrome rompa el
  DOM de Streamlit).
- Banner de proyecto activo en la barra lateral, con el nombre escapado
  (`html.escape()`) antes de interpolarlo en Markdown con HTML permitido.

## Unidades

- No aplica (capa puramente presentacional).

## Tipos de datos

- Lectura directa de `session_state` (dict); sin estructuras propias de
  Interfaz.

## Errores posibles

- Prerequisito ausente (p.ej. `recurso_solar_ok=False`): la página muestra
  una advertencia y hace `st.stop()`, nunca renderiza con datos parciales.
- Fallo del script de bloqueo de traducción (sin permisos del navegador): se
  captura la excepción en JS y no rompe la página.

## Dependencias

- Módulos previos: `07-informes`
- Módulos dependientes: `09-despliegue`

## Criterios de aceptación

- Toda página sigue el mismo orden: `requerir_login()` →
  `bloquear_traduccion()` + `mostrar_proyecto_activo()` → verificación de
  prerequisitos con `st.stop()` antes de renderizar contenido dependiente.
- `utils/ui.py` no restaura ni invalida datos de `session_state`; la vigencia
  de lo que muestra se garantiza en los módulos que lo escriben (`03`–`06`).
- Cualquier texto de usuario interpolado en HTML (`mostrar_proyecto_activo()`)
  queda escapado antes de renderizarse.

## Pruebas requeridas

- Ninguna nueva identificada: no hay cambio de código en esta ronda. Si se
  agrega lógica de restauración o vigencia propia a `utils/ui.py`, esta Spec
  debe reabrirse con el mismo rigor que `06`.

