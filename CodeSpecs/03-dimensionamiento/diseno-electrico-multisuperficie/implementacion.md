# Implementación — Diseño eléctrico multi-superficie: inversores, MPPT y grupos de strings

**Estado:** implementación

## Fase A1 — Cambios realizados

- Nuevo `calculos/diseno_electrico_multisup.py` (puro, sin Streamlit):
  - `normalizar_ficha_inversor`: contrato único para fichas del Excel
    (`n_trackers`, `n_strings_tracker`, `V_mppt_activo`) y del catálogo
    interno (`N_mppt`, `N_strings_nativo`, `eficiencia_max`). Sin MPPT mínimo
    activo usa el mínimo del MPPT.
  - `inversor_normalizado`: `clase` `string` y `origen_ficha` `manual` para
    inversores anteriores.
  - `grupos_de_superficie` (migración a G1) y `campos_legacy_desde_grupos`.
  - `temperaturas_diseno`: `T_min_diseno`, `T_cel_realista`, `T_cel_extremo`
    o, si faltan, −5 / 36,35 / 41,94 °C con origen `por_defecto`.
  - `rango_n_serie`: N que cumplen las mismas condiciones de tensión que
    `evaluar_compatibilidad_string`.
  - `validar_diseno_electrico`: diagnóstico por grupo, MPPT, inversor y
    superficie. Cada comprobación trae valor, límite, unidad, fórmula, fuente
    y estado; además devuelve bloqueos, avisos y estado global.
- `pages/9_🗺️_Vista_3D.py`, 🔌 Inversores por superficie:
  - Selector «Ficha del inversor»: del proyecto, del catálogo (Excel o
    interno) o manual; resumen de la ficha. La P AC sale de la ficha, salvo
    en manual.
  - Por superficie: Inversor, MPPT, N serie y N paralelo del grupo G1, y
    «Rango válido de N serie con <panel>: a–b».
  - Los campos siguen el patrón del editor de superficies (sin
    `value=`/`index=`), así que ya no pueden revertir el valor escrito.
  - Tabla «⚡ Diseño eléctrico — 🟢/🟡/🔴» (grupos, MPPT, inversores,
    superficies) con bloqueos, avisos y «🔎 Cómo se calcula cada valor». Una
    nota indica que todavía es informativa.
- Base de conocimiento del Asistente.

Desviaciones del diseño, con motivo:

- **Un solo grupo por superficie en el editor de A1.** El modelo, la
  migración y la validación ya aceptan varios grupos, pero el modo físico,
  el bypass y el MPPT siguen leyendo los campos de superficie hasta A2.
  Permitir varios grupos antes dejaría cálculos sin respaldo. Si una
  superficie ya tiene varios grupos, el editor lo dice y no los toca.
- **`rango_n_serie` recorre los N con `calcular_voc_string` y
  `calcular_vmp_string`** en lugar de llamar a `optimizar_n_serie`. Esa
  función exige `Vmppt_activo_min` y un N_min/N_max fijos (6–12). Las
  condiciones son las mismas de `evaluar_compatibilidad_string`.
- **El Asistente se actualiza ya en A1** y no esperó a A3, porque la
  pantalla cambia en esta fase.

## Archivos modificados (fase A1)

- `bipv_python/calculos/diseno_electrico_multisup.py` (nuevo)
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/tests/test_diseno_electrico_multisup.py` (nuevo),
  `bipv_python/tests/test_asistente_retrieval.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/03-dimensionamiento/diseno-electrico-multisuperficie/`
- `CodeSpecs/00-director/registro-de-decisiones.md`

## Impacto en despliegue (fase A1)

- Solo Streamlit (`pm2 restart streamlit-bipv`).
- Ninguna energía cambia. Un inversor que el usuario pase a «del proyecto» o
  «del catálogo» toma la P AC de la ficha, que es el límite de recorte del
  modo físico: es una elección explícita del usuario, no un cambio de
  fórmula.
