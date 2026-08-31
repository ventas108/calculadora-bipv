# Blindaje: fuente única para el "diseño confirmado" entre módulos

**Fecha**: 31 de agosto de 2026
**Disparador**: tras corregir el bug de `N_strings/tracker` desalineado en 📊 Producción
(`DIAGNOSTICO_NSTRTR_PRODUCCION_DESALINEADO.md`), el usuario pidió explícitamente: *"busca como
blindar las alineaciones entre los módulos y confirma el paso a paso coherente entre módulos aguas
abajo de tal forma que el usuario evite encontrar cálculos con valores fantasmas diferentes a los
confirmados en la sección inmediatamente anterior... siempre imponer coherencia"*.

## Auditoría: ¿había más casos del mismo patrón?

Se buscaron todas las claves `_usado` (la convención ya establecida en este proyecto para "valor
CONFIRMADO por el usuario", distinto del valor en vivo de un widget) y se revisó cada consumidor:

- `N_str_tr_usado` — el caso real ya corregido. 5 consumidores: 📊 Producción (corregido hoy),
  📄 Reporte PDF, 🤖 Análisis IA, 🧩 Comparador Paneles, 🧭 Comparador Orientación (estos 4 ya
  usaban la clave correcta).
- `_N_s_usado`, `bypass_*_usado` — de alcance interno a una sola página, sin el mismo riesgo de
  desalineación entre módulos.

**Un caso revisado a fondo y descartado como bug**: `calculos/escenarios_fase4.py::
capturar_base_comparacion()` lee `N_str_tr` (en vivo) ANTES que `N_str_tr_usado` — a primera vista
parece el mismo error, pero su propósito es distinto: esa función existe específicamente para
*congelar una nueva base de comparación de escenarios* con lo que el usuario tiene configurado en
ese momento (🔒 "Fase 2 — Base única de comparación" en 🔀 Mismatch) — ahí "capturar lo que hay
ahora mismo" es el propósito declarado, no un descuido. Se dejó sin tocar, documentado.

## El blindaje real: una función, no 5 copias

Antes de este cambio, cada una de las 5 páginas consumidoras repetía a mano
`session_state.get("N_str_tr_usado", 1)` (o la clave equivocada, en el caso ya corregido de
Producción) — cinco oportunidades independientes de volver a equivocar la clave, sin que nada lo
detectara hasta que alguien comparara capturas de pantalla de dos páginas distintas.

Nueva función pura `calculos/dimensionamiento.py::diseno_electrico_confirmado(session_state)`:
única fuente de verdad para `N_serie` y `N_strings_tracker` **confirmados** (no en vivo). Las 5
páginas ahora llaman a esta función en vez de repetir la clave a mano:

- `pages/6_📊_Produccion.py`
- `pages/10_📄_Reporte_PDF.py`
- `pages/18_🤖_Análisis_IA.py`
- `pages/4c_🧩_Comparador_Paneles.py`
- `pages/4d_🧭_Comparador_Orientación.py`

Si en el futuro se necesita cambiar CÓMO se resuelve el diseño confirmado (por ejemplo, agregar un
nuevo mecanismo de confirmación), hay un solo lugar que tocar — y un typo de clave en una página ya
no puede pasar desapercibido en silencio: todas comparten la misma implementación, así que o
funcionan las 5, o falla de forma visible en los tests de la única función.

## Verificación

3 tests nuevos en `tests/test_compatibilidad_string.py`, anclados al caso real de Teusaquillo:

1. `test_diseno_confirmado_usa_n_str_tr_usado_no_el_widget_en_vivo` — con `N_str_tr=1` (el decoy
   real observado) y `N_str_tr_usado=8` (el confirmado real), debe devolver 8.
2. `test_diseno_confirmado_default_1_sin_diseno_confirmado_todavia` — sesión nueva, sin diseño
   confirmado: no debe inventar nada.
3. `test_diseno_confirmado_ignora_n_str_tr_aunque_no_haya_usado` — solo existe el widget en vivo,
   sin confirmación: debe caer al default (1), nunca tomar el valor del widget.

Suite completa: **809/809**. Sintaxis de los 6 archivos de página/cálculo verificada con
`ast.parse()`. Confirmado por grep que ya no queda ninguna lectura directa de `"N_str_tr_usado"`
fuera de los 2 puntos de escritura legítimos (dentro de los botones de confirmación en
📐 Dimensionamiento) y de la nueva función centralizada.
