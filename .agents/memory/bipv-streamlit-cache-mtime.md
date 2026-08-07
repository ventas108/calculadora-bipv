---
name: BIPV - cachés st.cache_data y mtime
description: Invalidación de cachés de catálogos Excel por mtime; trampa de los parámetros con guion bajo
---

**Regla:** Todo loader de catálogo Excel cacheado con `@st.cache_data` debe recibir el mtime del archivo como parámetro **sin guion bajo inicial** (`mtime`, nunca `_mtime`), inyectado por un wrapper público sin argumentos.

**Why:** `st.cache_data` EXCLUYE del hashing los parámetros que empiezan con `_` (comportamiento documentado de Streamlit). Un `_mtime` compila y "parece" funcionar, pero la caché nunca se invalida al editar el Excel en el servidor — bug silencioso hasta 1h de TTL. Nos pasó con el catálogo de inversores (tarea #205); lo atrapó la auditoría, no las pruebas.

**How to apply:**
- Patrón: `def cargar_x(): return _cargar_x_cached(excel_mtime_x())` + `@st.cache_data(ttl=3600) def _cargar_x_cached(mtime): ...` + `cargar_x.clear = _cargar_x_cached.clear` (los guardadores/botones llaman `.clear()` sobre la pública).
- Hay test de regresión AST en `bipv_python/tests/test_cache_mtime_inversores.py` — replicar para nuevos catálogos.
- Baterías usa el mismo patrón (#26); si se agrega otro catálogo (p.ej. estructuras), copiarlo.
