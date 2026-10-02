# Diseño — Etapa del documento en el Reporte

**Estado:** validación

## Entradas

`st.session_state["reporte_etapa"]`, que guarda la elección del selector
`rep_etapa`.

## Salidas

`encabezado_etapa(clave) -> (badge_html, aviso_html)`, usados en el encabezado
de `generar_html_reporte()`.

## Tipos de datos

`ETAPAS: dict[str, dict]` con `nombre`, `etiqueta`, `icono`, `aviso` y `color`
(fondo, texto). `ETAPA_DEFECTO = "prefactibilidad"`.

## Errores posibles

Una clave desconocida o `None` usa la etapa por defecto.

## Dependencias

`html.escape`; `calculos/reporte_documentos.py` (Word y PDF desde el HTML).

## Criterios de aceptación

1. Etapa por defecto: Estudio de prefactibilidad.
2. Las etapas para el cliente no contienen «BORRADOR» ni «presentarlo al
   cliente».
3. El Borrador interno conserva el aviso al diseñador.
4. Word y PDF llevan la etiqueta elegida.
5. La página tiene el selector y no tiene «BORRADOR» fijo.
