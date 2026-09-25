# Implementación — Validación visible de los puntos 3D por superficie

**Estado:** completado

## Cambios realizados

- Nuevo `calculos/puntos_3d.py`:
  - `parsear_puntos_3d(texto, nombre)` → `(puntos, errores)`. Con `;` los
    campos se separan por `;` y la coma es decimal; sin `;` se separan por
    `,` con punto decimal. Una línea que no da exactamente 3 números finitos
    es un error `{"linea", "texto", "motivo"}`; con 4 valores separados por
    coma el motivo sugiere usar `;`. Las líneas vacías se ignoran. Los
    puntos conservan el contrato del motor (`nombre`, `fachada`, `x`, `y`,
    `z`).
  - `previsualizar_puntos(malla, puntos)`: llama a la misma
    `sombras_3d.validar_puntos` que usa el cálculo.
  - `migrar_puntos_por_uid(puntos, superficies)` y
    `puntos_por_nombre(puntos_por_uid, superficies)`.
- `pages/9_🗺️_Vista_3D.py`: `multisup_puntos_por_superficie` queda indexado
  por `uid` (migración automática con aviso). Bajo cada recuadro se muestran
  las líneas con error y los avisos de la vista previa. «🌳 Calcular sombra»
  se deshabilita con líneas con error, y un aviso dice qué falta (escena,
  TMY, líneas con error, superficies sin puntos). El motor recibe los puntos
  por el nombre actual de cada superficie activa.

Desviaciones del diseño, con motivo:

- El texto de cada recuadro se inicializa una sola vez en `session_state`
  (clave `multisup_puntos_<uid>`) en lugar de pasar `value=` en cada rerun.
  Con `value=` cambiante Streamlit reinicia el widget: la línea con error
  desaparecía en el siguiente rerun y el texto del usuario se reformateaba.
  Se detectó en la prueba de humo con `AppTest`.
- La migración también reconoce el `uid` escrito como texto (`"1"`), que es
  como vuelve la clave tras guardar y cargar un proyecto en JSON.

## Archivos modificados

- `bipv_python/calculos/puntos_3d.py` (nuevo)
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/tests/test_puntos_3d_validacion.py` (nuevo)
- `bipv_python/datos/base_conocimiento_asistente.md`
- `docs/MANUAL_VISTA_3D.md`, `entregables/MANUAL_VISTA_3D_BIPV.docx`
- `CodeSpecs/08-interfaz/puntos-3d-validacion/`
- `CodeSpecs/00-director/registro-de-decisiones.md`

## Impacto en despliegue

- Solo la app Streamlit (reinicio de `streamlit-bipv`). El motor de sombra y
  el contrato de puntos no cambian.
