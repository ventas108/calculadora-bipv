# Bug real: `fit_desoto_batzelis` no existe en la versión de pvlib fijada — CI en rojo

**Fecha**: 31 de agosto de 2026
**Disparador**: el usuario reenvió el aviso por correo de GitHub Actions ("Tests / test — Failed in
5 minutes and 29 seconds") para el commit `2ea08f9b` (el fix de retrieval del asistente, que no
tocaba código de Motor IV — el fallo real venía de un commit anterior, `984eb39f`, el de
`fit_desoto_batzelis`, que hasta ahora nunca había disparado un push a `main` con la suite en rojo
en CI).

## Causa raíz

`requirements.txt` fija **`pvlib==0.11.1`**. La función `pvlib.ivtools.sdm.fit_desoto_batzelis()`
que se agregó como respaldo cerrado para el ajuste SDM (ver
`DIAGNOSTICO_GRAFICA_COMPATIBILIDAD_ELECTRICA.md`, actualización del 30-ago) **no existe en esa
versión** — se agregó a `pvlib` en una versión posterior. Confirmado directamente:

```python
import pvlib          # instalado como pvlib==0.11.1, igual que requirements.txt
pvlib.__version__      # '0.11.1'
hasattr(pvlib.ivtools.sdm, 'fit_desoto_batzelis')   # False
```

El entorno de desarrollo local donde se implementó y probó ese fix ya tenía instalado un `pvlib`
mucho más nuevo (0.15.2, de una instalación anterior en esta misma sesión) — así que la función
existía ahí y todos los tests pasaban. La llamada real está envuelta en un `except Exception:`
(caída al heurístico tosco), así que en cualquier entorno que sí respetara el pin real —
GitHub Actions, y potencialmente el servidor de producción si su entorno no coincide exactamente
con el del desarrollo — la llamada lanzaba `AttributeError`, se capturaba en silencio, y el ajuste
SDM caía siempre al heurístico tosco. Como ese heurístico da resultados que no reproducen la ficha
STC (confirmado en la sesión anterior: Voc con hasta 96% de error), el recuento real de paneles
que activan Motor IV en un entorno con el pin real es mucho menor que el `>=65` que aseguraban los
tests nuevos — de ahí el fallo real y correcto de la suite en CI.

## Corrección aplicada

En vez de subir la versión de `pvlib` fijada (cambio de mayor alcance, arriesga romper cualquier
otra parte de la app que dependa de la API 0.11.1, y no se puede verificar por completo sin acceso
a CI), se **reimplementó localmente** el método Batzelis — es un conjunto cerrado de ecuaciones
(sin iteración, ver referencia abajo), no algo que dependa de internals de pvlib salvo la función
de Lambert W. Nueva función `calculos/modelo_iv.py::_fit_desoto_batzelis_local()`, verificada
**bit a bit idéntica** (diferencia 0.0 en las 6 salidas) contra `pvlib.ivtools.sdm.fit_desoto_batzelis()`
real (con el pvlib 0.15.2 ya disponible) para 3 paneles reales, incluido el caso límite conocido de
Rsh negativo (EINNOVA ESM-620M). Usa `scipy.special.lambertw()` (ya fijado en `requirements.txt`,
`scipy==1.13.1`) en vez del helper privado `pvlib.ivtools.utils._lambertw_pvlib` — verificado que
da el mismo valor (diferencia 0.0) para los rangos reales de esta app (Lambert W hasta ~1e13, sin
overflow con `scipy.special.lambertw`).

## Verificación contra el entorno EXACTO que usa CI

No hay acceso a los logs de GitHub Actions desde este entorno (permiso "Must have admin rights to
Repository" en la API sin token), así que se reprodujo el entorno de CI localmente instalando
`pvlib==0.11.1` en una carpeta aislada (`pip install --target`) y corriendo la suite completa con
`PYTHONPATH` apuntando ahí primero:

- Auditoría del catálogo real de 76 paneles con `pvlib==0.11.1`: **72/76 activan Motor IV** (65 vía
  `_fit_desoto_batzelis_local` + 7 precalibrados) — igual que con el pvlib más nuevo, confirmando
  que la reimplementación local es la que realmente importa, no la versión de pvlib instalada.
- Suite completa (`tests/`) con `pvlib==0.11.1`: **806/806 passed**.

## Lección para el futuro

Ningún test local corre nunca contra las versiones EXACTAS de `requirements.txt` a menos que se
verifique explícitamente (como aquí) — el entorno de desarrollo de esta sesión tiene versiones más
nuevas de `pvlib`, `numpy` y `scipy` que las fijadas. Vale la pena, antes de depender de una
función nueva de una librería externa, confirmar que existe en la versión realmente fijada del
proyecto — `python -c "import X; hasattr(X, 'funcion_nueva')"` con el paquete instalado en una
carpeta aislada, como se hizo aquí, es rápido y evita este tipo de sorpresa.
