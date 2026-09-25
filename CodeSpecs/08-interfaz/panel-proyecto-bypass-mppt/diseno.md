# Diseño — Panel y strings del proyecto en bypass y MPPT por superficie

**Estado:** completado

## Entradas

- `panel_dict`, `panel_nombre_dim` (📐 Dimensionamiento).
- `N_serie` de Dimensionamiento.
- Por superficie activa: `n_serie`, `n_paralelo`, `area_m2`.
- Catálogo `MODULOS_BIPV` y `tiene_sdm_completo`.

## Salidas

- Opción por defecto de ambos selectores: panel del proyecto.
- `N_series`/`N_parallel` por superficie con su origen: `superficie`,
  `dimensionamiento` o `estimado_por_area`.
- Tabla de resultados con columnas nuevas: «Panel usado», «N serie ×
  paralelo», «Origen strings» y marca si difiere del proyecto.
- `bypass_multisup_resultados` guarda panel y N usados por superficie.

## Tipos de datos

- Panel: `dict` con parámetros SDM (mismo contrato de `MODULOS_BIPV`).
- `N_series`, `N_parallel`: `int` ≥ 1.
- Origen de strings: `str` del conjunto cerrado indicado arriba.

## Errores posibles

- Sin `panel_dict` (Dimensionamiento no ejecutado): se exige elegir panel
  del catálogo y se muestra aviso.
- Panel del proyecto sin ficha SDM completa (`tiene_sdm_completo`), en el
  bypass o en el MPPT: aviso y selección del catálogo obligatoria, porque ambos
  modelos resuelven el circuito con el SDM del panel.
- `n_serie`/`n_paralelo` no numéricos en una superficie: se usa el
  respaldo con aviso; nunca se inventa un valor silencioso.

## Dependencias

- Módulos previos: `03-dimensionamiento` (`panel_dict`, `N_serie`),
  `05/transicion-multisuperficie` (strings por superficie).
- Módulos dependientes: la Spec `publicacion-energia-multisuperficie`
  (energía publicada por el bypass).
- Capas: interfaz (Vista 3D); estado (`bypass_multisup_resultados`).

## Criterios de aceptación

- Sin intervención del usuario, bypass y MPPT usan el panel del proyecto.
- Un panel del proyecto ausente de `MODULOS_BIPV` se puede usar en el bypass.
- Cada superficie usa sus propios `n_serie`/`n_paralelo` si están
  configurados, y la tabla muestra el origen.
- Elegir otro panel queda marcado en los resultados.

## Pruebas requeridas

- Resolución de panel por defecto: con panel en catálogo, fuera de catálogo
  y sin panel.
- Resolución de strings por superficie: configurada, desde
  Dimensionamiento y estimada.
- Bypass y MPPT con panel sin SDM completo: aviso y bloqueo del cálculo.
- Prueba de página: los selectores ya no fijan `ASP-ST1-T40` como índice por
  defecto (AST).
- Regresión: suites de bypass y MPPT combinado.
