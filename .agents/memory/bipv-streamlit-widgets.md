---
name: BIPV - sincronización de widgets keyed en Streamlit
description: Cómo auto-sincronizar selectbox/number_input con detección automática sin pisar el override manual del usuario
---

**Regla:** para widgets con `key` que se auto-poblan desde una detección (zona geográfica, ciudad, etc.), escribir `session_state[key]` SOLO cuando el valor detectado CAMBIA respecto al último detectado (guardado en una clave `_<key>_auto_prev`). Escribirlo en cada rerun revierte silenciosamente la selección manual del usuario — el widget queda de facto de solo lectura.

**Why:** en Estimación Rápida (página 8, tarea #79) la sincronización forzada por rerun impedía elegir zona manualmente; el fix agregó `_est_zona_auto_prev` + aviso de divergencia.

**How to apply:**
- La re-sincronización debe ocurrir ANTES de cualquier bloque que consuma el valor en el mismo rerun (ej. auto-update de CAPEX corre antes de renderizar el widget; si se sincroniza junto al widget, el auto-update calcula con el valor viejo mientras el dropdown muestra el nuevo).
- Si el usuario diverge de la detección, mostrar warning explícito indicando cuál valor usa el cálculo; el cálculo siempre debe usar el valor del widget.
- Patrón similar: fuente de TRM "valor por defecto" vs "valor manual" (trm_utils) — la edición manual solo se detecta si el número cambia.
