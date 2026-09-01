# Hueco #2: la compatibilidad batería↔inversor en el Diagrama Unifilar quedaba obsoleta

**Fecha**: 1 de septiembre de 2026
**Disparador**: el usuario pidió aclarar el emparentamiento entre el catálogo de inversores
híbridos y el de baterías, "principalmente en cuanto al módulo de Dimensionamiento al diseño
final del diagrama unifilar" — solo como solicitud de aclaración, no de corrección. La auditoría
encontró 3 huecos reales; el usuario pidió corregir el más serio (staleness del diagrama).

## Qué se encontró (verificado leyendo el código real, no supuesto)

1. **📐 Dimensionamiento no sabe nada de baterías**: `pages/4_📐_Dimensionamiento.py` no tiene
   ninguna referencia a "batería"/"híbrido" (0 resultados). Se puede elegir libremente cualquier
   inversor ahí sin ninguna alerta, aunque el proyecto ya tenga batería configurada.
2. **El bug corregido en este cambio**: `session_state["bateria_ok"]` es una foto fija del momento
   en que se hizo clic en "▶️ Dimensionar batería" en 🔋 Baterías y Balance
   (`pages/11_🔋_Baterias_y_Balance.py:687-690`), validada contra el inversor que estaba
   seleccionado **en ese instante** (`inversor_dict_dim` leído en la línea 522 de esa misma
   página). Si después el usuario vuelve a 📐 Dimensionamiento y cambia de inversor, ese flag no
   se invalida solo — nada en Dimensionamiento lo toca. ⚡ Diagrama Unifilar
   (`pages/20_⚡_Diagrama_Unifilar.py`) confiaba ciegamente en `bateria_ok` para pre-marcar
   "Incluir batería" y para escribir en el diagrama una leyenda fija afirmando
   *"conectada al mismo inversor híbrido... verificado por rango de voltaje"* — sin volver a
   comprobar nada contra el inversor realmente vigente.
3. **Menor, no corregido en este cambio (no afecta producción)**: `datos/catalogo_baterias_excel.py`
   tiene el path del Excel hardcodeado solo a `/var/www/...`, sin el mismo fallback relativo que
   `catalogo_inversores_excel.py` ya tiene desde el 28-ago. En cualquier entorno local, el catálogo
   de baterías carga vacío en silencio (verificado en vivo: `cargar_catalogo_baterias()` → `{}`,
   0 baterías, aquí mismo).

## Corrección aplicada

`calculos/compatibilidad_bateria.py::check_compatibilidad()` ya existía como función pura (sin
Streamlit, testeable) usada por la página 11. `pages/20_⚡_Diagrama_Unifilar.py` ahora la vuelve a
llamar **en vivo, justo antes de dibujar**, con los valores YA recalculados en esa misma página
(`bateria_dict`, `inversor_dict`, `inversor_nombre` — los mismos que terminan en el diagrama, no
una copia vieja de session_state) en vez de confiar en el flag `bateria_ok`.

El resultado (`"ok"` / `"warning"` / `"error"`) decide qué se muestra:
- `"ok"`: `st.success()` con el mensaje real de `check_compatibilidad()` (incluye los voltajes
  exactos verificados ahora, no una frase genérica).
- `"warning"`: `st.warning()` (ej. inversor no identificable, batería sin voltaje en el catálogo).
- `"error"`: `st.error()` + aviso explícito de que el diagrama se generará igual si el usuario
  continúa, pero la conexión **no está verificada** — corregir antes de usar el diagrama para
  RETIE.

No bloquea la generación del diagrama — mismo principio de toda la app (alertar, no impedir),
consistente con `diseno_electrico_confirmado()` y el resto de las alertas de vigencia ya
existentes.

## Verificación

- Sintaxis de la página verificada con `ast.parse()`.
- 2 tests nuevos en `tests/test_pagina_diagrama_unifilar.py` (mismo patrón AST/substring que el
  resto de esa suite — no requiere sesión Streamlit autenticada):
  `test_pagina_unifilar_reverifica_compatibilidad_bateria_en_vivo` (confirma el import y la
  llamada real a `check_compatibilidad()` contra `inversor_dict`/`inversor_nombre` actuales, y que
  ya no queda la leyenda vieja que citaba la verificación de la página 11 como si siguiera
  vigente) y `test_pagina_unifilar_advierte_si_bateria_actual_no_es_compatible` (confirma la rama
  de error con el aviso explícito de "no verificada").
- Suite completa: **894/894 passed** (892 previos + 2 nuevos), corrida con `PYTHONUTF8=1
  python -m pytest tests/ -q` (mismo entorno que usa el gate de CI).
- Retrieval del asistente 🧭 verificado contra el mecanismo real (`BaseConocimiento.cargar().buscar()`,
  no en teoría): 3 preguntas realistas sobre este tema devuelven la sección nueva
  (`## 25n.` en `datos/base_conocimiento_asistente.md`) en primer lugar. Longitud de la sección:
  2.658 caracteres, dentro del límite de truncamiento de 4.000.
