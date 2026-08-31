# Auditoría de la alerta de vigencia: 3 huecos reales encontrados aguas abajo

**Fecha**: 31 de agosto de 2026
**Disparador**: el usuario preguntó explícitamente por el módulo ⚡ Diagrama Unifilar — *"varias
métricas antes del módulo dimensionamiento influyen en esta función y no las hemos ni revisado, ni
auditado ni prevenido antes de cualquier incoherencia en la elaboración del diagrama unifilar"*.
Pedía una auditoría real, no una respuesta del manual.

## Auditoría: ¿quién más lee `N_serie`/`inversor_nombre_dim` en la app?

`grep` de todos los sitios que LEEN `N_serie` (9 páginas) y todos los que ESCRIBEN
`N_serie`/`inversor_nombre_dim`/`panel_nombre_dim` (los puntos de confirmación reales). De las 9
páginas lectoras, 2 nunca habían sido auditadas cuando se construyó la alerta de vigencia original
(`DIAGNOSTICO_ALERTA_VIGENCIA_DISENO.md`, 31-ago-2026):

### Hueco 1 y 2 — ⚡ Diagrama Unifilar y 📋 Ficha de Validación RETIE (páginas 20 y 21)

Ambas son "generadores universales" con el mismo patrón: auto-llenan `N_serie` y
`N_paneles_granja` desde el último diseño confirmado en Dimensionamiento, en campos que el usuario
puede editar libremente. Ninguna de las 2 llamaba a `diseno_electrico_confirmado()` ni mostraba la
alerta de vigencia — a diferencia de las otras 5 páginas que sí quedaron cubiertas en el trabajo
original. Riesgo real: cambiar de panel/inversor en Dimensionamiento sin re-confirmar, ir directo a
cualquiera de estas 2 páginas, y sellar en el Ledger de Auditoría un diagrama/ficha con un `N_serie`
que ya no corresponde al panel/inversor mostrado — sin ningún aviso.

Además, ambas auto-llenan "Número total de módulos" desde `N_paneles_granja`, que Dimensionamiento
ya protege internamente con su propia firma `N_paneles_granja_inversor_ref` (bug real del
29-ago-2026, ver el propio comentario en `pages/4_📐_Dimensionamiento.py` línea 260) — pero esa
protección solo se aplicaba DENTRO de Dimensionamiento, nunca se extendió a estas 2 páginas
consumidoras.

**Corregido** en ambas con el mismo patrón: `diseno_electrico_confirmado()` + `st.warning(aviso)`
justo después del bloque de prerrequisitos, más una segunda alerta específica que compara
`N_paneles_granja_inversor_ref` contra `inversor_nombre_dim` (mismo principio anti-falso-positivo:
solo avisa si hay una referencia guardada que ya no coincide, nunca por la sola ausencia del dato).

### Hueco 3 — ⚖️ Comparador de Inversores (página 4b): riesgo de FALSO POSITIVO

Auditando quién más ESCRIBE `N_serie`/`inversor_nombre_dim` (no solo quién lee), se encontró un
tercer punto de confirmación real que no se conocía al construir la alerta original: el botón
"✅ Adoptar esta configuración" de 4b escribe `N_serie` e `inversor_nombre_dim` directamente (un
mecanismo de adopción paralelo a los 2 botones de Dimensionamiento), pero **nunca actualizaba**
`N_serie_panel_ref`/`N_serie_inversor_ref`.

Consecuencia real: un usuario que confirma un diseño en Dimensionamiento con el Inversor A, luego
usa 4b para explorar y adopta el Inversor B (`N_serie` e `inversor_nombre_dim` quedan correctamente
actualizados para B), habría visto la alerta de vigencia dispararse en **falso** en las 7 páginas
que la muestran — la referencia guardada seguiría señalando al Inversor A como "el confirmado",
aunque el valor ya adoptado (B) es perfectamente válido y fresco. Esto viola directamente la
garantía de diseño de la alerta original ("nunca un falso positivo").

**Corregido**: el botón "Adoptar esta configuración" ahora también escribe
`N_serie_panel_ref`/`N_serie_inversor_ref` en el mismo punto donde adopta la configuración —
tercer punto de confirmación, misma disciplina que los otros 2.

### Verificado como correcto (sin bug, sin cambios)

- **🧩 Comparador de Paneles, botón "Adoptar este panel"**: cambia `panel_nombre_dim` pero
  deliberadamente NO toca `N_serie_panel_ref` — esto es correcto por omisión: al no actualizar la
  referencia, `diseno_electrico_confirmado()` detecta el desfase real (el panel cambió, N_serie
  sigue siendo el del panel anterior) y dispara la alerta como debe — un verdadero positivo, no
  requiere corrección.
- **📊 Producción, selector de inversor propio**: permite re-seleccionar el inversor directamente en
  esa página (para explorar el efecto en producción) y reescribe `inversor_nombre_dim` en vivo — la
  llamada a `diseno_electrico_confirmado()` ocurre DESPUÉS de esa reasignación en el mismo render,
  así que la alerta se dispara correctamente si el usuario explora un inversor distinto al
  confirmado en Dimensionamiento, sin ningún cambio necesario.
- **🔋 Baterías y Balance**: `bateria_dict`/`bateria_dim`/`bateria_nombre` se escriben todos
  atómicamente en un solo punto — no hay una versión "en vivo" separada de una "confirmada" como
  con panel/inversor, así que no existe el mismo riesgo de desalineación.

## Verificación

Sintaxis de los 3 archivos verificada con `ast.parse()`. Suite completa: **821/821** sin cambios
(estos son fixes de página con lectura de `session_state`, igual que
`DIAGNOSTICO_NSTRTR_PRODUCCION_DESALINEADO.md` — no unit-testeables directamente sin un harness de
Streamlit; verificados por auditoría exhaustiva de `grep` de todos los sitios de lectura/escritura
de las claves involucradas, no solo los 2 puntos ya conocidos).

## Alcance final de la alerta de vigencia (actualizado)

Ahora cubre **8 páginas de lectura** (Dimensionamiento, Producción, Reporte PDF, Análisis IA,
Comparador de Paneles, Comparador de Orientación, Diagrama Unifilar, Ficha de Validación RETIE) y
**3 puntos de confirmación** que la mantienen vigente (los 2 botones de Dimensionamiento + el botón
"Adoptar" de Comparador de Inversores).
