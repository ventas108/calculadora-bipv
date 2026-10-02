# Diseño — Caché del catálogo de paneles

**Estado:** validación

## Entradas

El Excel `paneles_catalogo.xlsx` (hoja `Catalogo_Paneles_FV`).

## Salidas

`cargar_catalogo_paneles() -> dict[str, dict]`, igual que antes. El contenido
es idéntico: 0 diferencias en 3.128 paneles.

## Tipos de datos

`_CACHE_CATALOGO = {"clave": (ruta, mtime_ns, tamaño), "datos": dict}`.

## Errores posibles

- Excel inexistente: la clave lleva `None` y la lectura falla igual que antes.
- Excel modificado fuera de la app (por ejemplo, `git pull`): cambia el mtime
  y se relee.

## Dependencias

`pandas.read_excel`, `os.stat`.

## Criterios de aceptación

1. `cargar_catalogo_paneles` tiene `.clear` y `_texto_celda` no.
2. La segunda carga tarda menos de 0,5 s (medido: 0,003 s; antes 5 a 9 s).
3. Todo `cargar_catalogo*` de `datos/` tiene caché (guardia).
4. Mismo catálogo que con `iterrows` (0 diferencias).
