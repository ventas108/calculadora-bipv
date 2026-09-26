# Implementación — Catálogos editables y potencia AC nominal de los inversores

**Estado:** implementación

## Cambios realizados

- **Pestañas ✏️ Editar / Eliminar** (páginas 14 y 15): el cuerpo de la
  pestaña ➕ Agregar desde PDF es la función `_pestana_agregar_desde_pdf()` y
  sus `st.stop()` son `return`. Sin PDF subido, la pestaña de edición se ve.
- **`calculos/edicion_catalogo_inversores.py`** (nuevo): `COLUMNAS_EDICION`
  (clave → etiqueta de la tabla → columna del Excel), `tabla_edicion` y
  `parches_edicion`, que compara por nombre de columna (antes `getattr` sobre
  `itertuples()`, con columnas renombradas a `_1`, `_2`…) y guarda una celda
  vaciada como `None`.
- **`calculos/potencia_ac_inversor.py`** (nuevo): `potencia_ac_w`,
  `potencia_ac_requerida`, `error_potencia_ac`, `inversores_sin_potencia_ac`
  y `MENSAJE_SIN_POTENCIA_AC`.
- **`datos/catalogo_inversores_excel.py`**: `P_ac_nom_W` = `potencia_ac_w`
  de «Potencia AC nominal (kW)»; se elimina el respaldo 0,96 × P FV máx.
- **`calculos/pdf_inversor_extractor.py`**: `_extraer_potencia_ac_kw` y clave
  `P_ac_nom_kW` en el resultado (antes la potencia AC solo servía para estimar
  P FV máx. y se descartaba); en fichas multi-modelo, `P_ac_nom_kW` por
  columna solo si hay exactamente un valor por modelo.
- **Página 15**: campo «Potencia AC nominal (kW)» precargado y obligatorio
  salvo «Cargador off-grid puro»; se guarda en su columna. La tabla tiene la
  columna «P AC nominal (kW)», un aviso con cuántos inversores no la tienen y
  la casilla «Mostrar solo los inversores sin potencia AC».
- **Mensajes**: Vista 3D (aviso 🟡 de DC/AC), 📐 Dimensionamiento y 📊
  Producción explican dónde completar la potencia AC; Producción aclara que
  se calcula sin recorte.
- **Asistente**: sección 73 con el procedimiento y la ficha oficial del Growatt
  MID15KTL3-X (corrige «8 strings por tracker» y «27,5 A / 33,5 A»).

## Archivos modificados

- `bipv_python/calculos/edicion_catalogo_inversores.py` (nuevo)
- `bipv_python/calculos/potencia_ac_inversor.py` (nuevo)
- `bipv_python/calculos/pdf_inversor_extractor.py`
- `bipv_python/calculos/diseno_electrico_multisup.py`
- `bipv_python/datos/catalogo_inversores_excel.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `bipv_python/pages/14_📋_Catálogo_Paneles.py`
- `bipv_python/pages/15_🔌_Catálogo_Inversores_PDF.py`
- `bipv_python/pages/4_📐_Dimensionamiento.py`
- `bipv_python/pages/6_📊_Produccion.py`
- Pruebas: `test_catalogo_inversores_pestana_editar.py`,
  `test_potencia_ac_inversor.py`, `test_edicion_catalogo_inversores.py` (nuevas),
  `test_asistente_retrieval.py`.
- `CodeSpecs/00-director/registro-de-decisiones.md`

## Impacto en despliegue

- No cambia el Excel versionado `inversores_catalogo.xlsx`: las correcciones
  hechas en el servidor desde la tabla no chocan con `git pull`.
- Tras desplegar, los inversores sin «Potencia AC nominal (kW)» muestran la
  DC/AC como «no evaluable» y quedan fuera del comparador financiero con el
  motivo «Sin potencia AC nominal». Se completan desde la tabla con su ficha.
- En 🗺️ Vista 3D cada inversor guarda su copia de la ficha: después de
  completar un dato en el catálogo hay que volver a elegir la ficha.
