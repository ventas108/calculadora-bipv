# Diseño — Catálogos editables y potencia AC nominal de los inversores

**Estado:** implementación

## Entradas

- Fila del Excel `inversores_catalogo.xlsx` (columna «Potencia AC nominal (kW)»).
- Texto de la ficha PDF («Rated AC output power», «Potencia nominal CA»…).
- Formulario ➕: arquitectura y «Potencia AC nominal (kW)».
- Tabla ✏️: filas originales y editadas del `st.data_editor`.

## Tipos de datos

- `potencia_ac_w(p_ac_kw) -> float | None`: W desde kW; `None` si falta, es 0,
  negativo o no finito.
- `error_potencia_ac(arquitectura, p_ac_kw) -> str | None`.
- `inversores_sin_potencia_ac(catalogo) -> list[str]`.
- `COLUMNAS_EDICION: dict[clave, (etiqueta, columna Excel)]`.
- `parches_edicion(original, editada) -> list[(modelo, {columna Excel: valor})]`.
- `_extraer_potencia_ac_kw(texto) -> float | None` (kW, 0,5–5.000).

## Salidas

- Catálogo: `P_ac_nom_W` solo de ficha; `P_ac_nom_kW` igual que antes.
- Extractor: nueva clave `P_ac_nom_kW`.
- Excel: el formulario escribe «Potencia AC nominal (kW)»; la tabla la actualiza.
- Mensaje `MENSAJE_SIN_POTENCIA_AC` en Vista 3D (aviso 🟡 de DC/AC),
  Dimensionamiento y Producción.

## Reglas

- La potencia AC nunca se estima a partir de la potencia FV máxima.
- Obligatoria en el formulario salvo «Cargador off-grid puro».
- Una celda vaciada se guarda como vacía (`None`), nunca como NaN.
- La estimación de P FV máx. desde la potencia AC (×1,5, con aviso) no cambia.

## Errores posibles

- Guardar un inversor de red sin potencia AC: «No se guardó» con el motivo.
- `actualizar_inversor_excel` falla en una fila: se muestra el error de esa
  fila y las demás se guardan.

## Dependencias

`datos/catalogo_inversores_excel.py`, `calculos/pdf_inversor_extractor.py`,
`calculos/diseno_electrico_multisup.py`, `calculos/dimensionamiento.py`
(`evaluar_relacion_dc_ac`, sin cambios), páginas 4, 6, 14 y 15.

## Criterios de aceptación

1. Sin PDF subido, la pestaña ✏️ de los dos catálogos muestra la tabla y sus
   botones; ninguna pestaña que no sea la última usa `st.stop()`.
2. «💾 Guardar cambios» guarda las celdas cambiadas del catálogo de inversores
   (Growatt MID15KTL3-X corregido con su ficha oficial).
3. Un inversor sin «Potencia AC nominal (kW)» tiene `P_ac_nom_W = None`.
4. El extractor devuelve `P_ac_nom_kW` aunque la ficha traiga la P FV máx.
5. El formulario no guarda un inversor de red sin potencia AC.
6. La tabla muestra y guarda «P AC nominal (kW)», cuenta los inversores sin
   ella y permite filtrarlos.
7. Vista 3D, Dimensionamiento y Producción explican dónde completar el dato
   cuando falta.

## Pruebas requeridas

`test_catalogo_inversores_pestana_editar.py`, `test_potencia_ac_inversor.py`,
`test_edicion_catalogo_inversores.py`.
