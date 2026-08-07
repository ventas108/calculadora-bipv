---
name: BIPV — persistencia por usuario
description: Cómo persistir estado a disco en la app multiusuario sin mezclar datos entre cuentas
---

# Persistencia por usuario (tareas 89/94/114 + auditoría)

**Regla:** todo estado del usuario que se persista a disco debe ir a un archivo PRIVADO por cuenta: `calculos/persistencia_resultados.py → ruta_datos_usuario(nombre_base, auth_email)` → `datos/persistencia/<sha256[:12]>__<nombre>.json`. Nunca archivos globales en `datos/` (varios clientes comparten el servidor).

**Why:** auditoría architect marcó FAIL por aislamiento roto: archivos globales (`proyecto_actual.json`, `consumo_cache.json`) dejaban que un cliente viera/pisara el proyecto de otro.

**How to apply:**
- Cargar estado desde disco SIEMPRE después de `requerir_login()` (se necesita `auth_email`).
- Escritura atómica con tmp único por proceso: `f"{ruta}.{os.getpid()}.tmp"` + `os.replace`.
- Resultados de Producción llevan huella (ciudad/lat/lon); no restaurar si la sesión trabaja otro proyecto, y `limpiar_resultados_produccion()` al cambiar ciudad/coords/proyecto (Página 1 y `proyectos_manager.cargar_proyecto`).
- Restaurar solo claves AUSENTES y nunca marcar `produccion_ok=True`.
- Tablas del Presupuesto: validar esquema (`presupuesto_store.cargar_seccion`) — esquema viejo → plantilla, no KeyError.
- OJO: `datos/proyectos/` (Mis Proyectos) sigue global — tarea pendiente #203.
- Se eliminó `calculos/persistencia.py` (módulo global duplicado de un merge previo, sin consumidores): no revivirlo.
