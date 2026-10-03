# Diseño — Proveedor de sombra opcional `pybdshadow`

**Estado:** propuesta — NO aprobada. Borrador de diseño, no un contrato vigente.

## Contrato `ShadowResult` (borrador)

Ver esquema completo y tabla campo-por-campo en
`references/informe-verificacion-pybdshadow-p-shade.md` ("Contrato universal
`ShadowProvider`/`ShadowResult`"). Resumen de las decisiones de diseño que esta Spec fijaría:

- `p_shade` es y sigue siendo **geométrico** (idéntico contrato numérico a `FS_geometrico`,
  0=sin sombra, 1=sombra total). Ningún proveedor escribe ahí una magnitud eléctrica.
- `capacidades_declaradas` es obligatorio en todo `ShadowResult` — el consumidor (adaptador de
  entrada de `transicion_multisuperficie`) debe rechazar una superficie no horizontal si el
  proveedor declara `soporta_inclinada=False`/`soporta_vertical=False`, en vez de aceptar un
  resultado numérico que el proveedor no puede garantizar.
- `sombra_cero_calculada` vs. `no_calculado` es un campo explícito, nunca inferido de un `p_shade`
  en cero — mismo criterio que ya exige el proyecto contra los "defaults silenciosos".

## Función propuesta

```python
def calcular_p_shade_pybdshadow_horizontal(
    superficie: dict,          # nombre, tilt_deg, azimuth_deg, area_m2, footprint (lon/lat)
    edificios_vecinos: "geopandas.GeoDataFrame",  # polígono + columna height
    lat: float, lon: float,
    indice_tmy: "pandas.DatetimeIndex",   # 8760 horas
    tolerancia_horizontal_deg: float = 5.0,
) -> dict:
    """Devuelve un ShadowResult. Lanza ValueError explícito si
    abs(superficie['tilt_deg']) > tolerancia_horizontal_deg -- nunca aproxima
    una superficie inclinada con este proveedor."""
```

Ubicación propuesta: `calculos/proveedores_sombra/pybdshadow_horizontal.py` (paquete nuevo, no
toca `calculos/sombras_3d.py` ni `calculos/transicion_multisuperficie.py`).

## Integración (solo si se aprueba una fase posterior)

```text
pybdshadow_horizontal.calcular_p_shade_pybdshadow_horizontal()
  -> ShadowResult (p_shade geométrico + firma_sombra-compatible)
  -> mismo punto de entrada que ya usa sombras_3d.calcular_fs_horario_por_superficie
  -> adaptador_multisuperficie.construir_proyecto_desde_session_state (sin cambios)
  -> transicion_multisuperficie.py (sin cambios)
```

La integración NO requiere modificar `transicion_multisuperficie.py` ni
`adaptador_multisuperficie.py`: ambos ya consumen `p_shade` + `firma_sombra` como datos de
entrada, sin importar el proveedor que los produjo — es la misma propiedad que hace este diseño
viable como *opcional* sin tocar código productivo existente.

## Rendimiento

`bdshadow_sunlight` no está vectorizado por hora (una llamada Python por timestamp). Para 8760
horas, este proveedor debe:

- Filtrar primero por `ALTURA_SOLAR_MIN_DEG` (igual que `sombras_3d.py`) para no llamar en horas
  sin sol (~4400 llamadas típicas, no 8760).
- Cachear el `GeoDataFrame` de edificios preprocesado (`pybdshadow.bd_preprocess`) fuera del
  bucle horario.
- Documentar explícitamente en la UI que este proveedor es más lento que el ray-casting propio
  (orden de minutos, no segundos, para un año completo) — no prometer paridad de rendimiento.

## Dependencia opcional

```python
try:
    import pybdshadow
except ImportError:
    pybdshadow = None

def calcular_p_shade_pybdshadow_horizontal(...):
    if pybdshadow is None:
        raise ImportError(
            "pybdshadow no está instalado -- proveedor opcional, "
            "pip install pybdshadow para habilitarlo."
        )
    ...
```

`pybdshadow` NO entra a `bipv_python/requirements.txt`. Se documenta como dependencia opcional
en un `requirements-opcional.txt` o similar, decisión de la fase de implementación.

## Pendiente de decisión del Director antes de tareas.md real

- ¿Vale la pena esta Spec ahora, frente a la prioridad ya registrada de completar sombra por
  superficie inclinada en `sombras_3d.py` (bloqueo real de `transicion-multisuperficie`)? Esta
  Spec NO resuelve ese bloqueo.
- ¿Quién mantiene el parche de compatibilidad si `pybdshadow` sigue sin actualizarse para
  versiones futuras de Python?
