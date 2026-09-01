# Hueco #2: la compatibilidad batería↔inversor en el Diagrama Unifilar quedaba obsoleta

**Fecha**: 1 de septiembre de 2026
**Disparador**: el usuario pidió aclarar el emparentamiento entre el catálogo de inversores
híbridos y el de baterías, "principalmente en cuanto al módulo de Dimensionamiento al diseño
final del diagrama unifilar" — solo como solicitud de aclaración, no de corrección. La auditoría
encontró 3 huecos reales; el usuario pidió corregir el más serio (staleness del diagrama).

## Qué se encontró (verificado leyendo el código real, no supuesto)

1. **📐 Dimensionamiento no sabe nada de baterías (corregido en la actualización de abajo)**:
   `pages/4_📐_Dimensionamiento.py` no tenía ninguna referencia a "batería"/"híbrido"
   (0 resultados). Se podía elegir libremente cualquier inversor ahí sin ninguna alerta, aunque el
   proyecto ya tuviera batería configurada.
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
3. **Menor, corregido en la actualización de abajo (no afectaba producción)**: `datos/catalogo_baterias_excel.py`
   tenía el path del Excel hardcodeado solo a `/var/www/...`, sin el mismo fallback relativo que
   `catalogo_inversores_excel.py` ya tiene desde el 28-ago. En cualquier entorno local, el catálogo
   de baterías cargaba vacío en silencio (verificado en vivo: `cargar_catalogo_baterias()` → `{}`,
   0 baterías, aquí mismo).

## Actualización (1-sep-2026): hueco #3 corregido — path del Excel de baterías

Mismo fix que ya tenía `catalogo_inversores_excel.py` desde el 28-ago, nunca replicado en el
loader de baterías pese a leer del mismo archivo Excel: `_EXCEL` ahora se resuelve primero como
ruta relativa al propio módulo (`os.path.join(os.path.dirname(os.path.abspath(__file__)), ...)`),
cayendo al path histórico del servidor (`/var/www/bipv/calculadora-bipv/...`) solo si esa ruta
relativa no existe. En el servidor, ambas rutas resuelven al mismo archivo — **cero cambio de
comportamiento en producción**. En cualquier entorno local (incluido CI, donde
`inversores_catalogo.xlsx` sí está versionado en git), el catálogo ahora carga los datos reales
en vez de `{}`.

**Verificado en vivo**: antes del fix, `cargar_catalogo_baterias()` devolvía `{}` en este entorno;
después del fix, devuelve **26 baterías reales** (ej. `BR172R`, `BR186R`, `BC45T`).

3 tests nuevos en `tests/test_catalogo_baterias_excel_ruta.py`: la ruta resuelve a un archivo real
en este entorno, el catálogo carga datos reales anclados a un modelo conocido (`BR172R`), y el
fallback al path del servidor sigue presente en el código (por si el layout del servidor cambia
algún día). Suite completa: **897/897**.

## Actualización (1-sep-2026): hueco #1 corregido — Dimensionamiento ya conoce la batería configurada

Mismo patrón que el fix del hueco #2 (re-correr `check_compatibilidad()` en vivo, misma función
pura de `calculos/compatibilidad_bateria.py`), aplicado ahora "hacia arriba": justo después de que
`pages/4_📐_Dimensionamiento.py` fija `inversor_dict_dim`/`inversor_nombre_dim` para la sesión
(línea donde ya decía en un comentario viejo "Propagar inversor a session_state para
compatibilidad baterías (#25)" — la propagación existía, pero nunca se usaba para verificar nada),
se comprueba si el proyecto YA tiene una batería configurada (`session_state["bateria_dict"]`,
escrito por 🔋 Baterías y Balance). Si la hay, se re-verifica en vivo contra el inversor recién
seleccionado y se muestra `st.error`/`st.warning`/`st.caption` según severidad — igual que la
auditoría de compatibilidad regional que ya vive justo debajo en la misma página. Si el proyecto
no usa batería, no aparece nada — nunca inventa la alerta.

5 tests nuevos en `tests/test_pagina_dimensionamiento_compat_bateria.py` (mismo patrón
AST/substring). Suite completa: **902/902**.

Con esto quedan cubiertos los 3 huecos encontrados en la auditoría del emparentamiento inversor
híbrido ↔ batería pedida por el usuario: (1) Dimensionamiento alerta si el inversor elegido deja
de ser compatible con una batería ya configurada, (2) el diagrama unifilar re-verifica en vivo en
vez de confiar en un flag desactualizado, (3) el catálogo de baterías carga en cualquier entorno,
no solo en el servidor.

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
