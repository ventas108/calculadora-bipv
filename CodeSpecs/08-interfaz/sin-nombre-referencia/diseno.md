# Diseño — La app no nombra el software de simulación de referencia

**Estado:** validación

## Entradas

Cualquier texto (`str`); los demás tipos pasan igual.

## Salidas

- `anonimizar_referencia(texto, *, identificadores=True) -> str`.
- `menciona_referencia(texto) -> bool`.
- `datos/catalogo_paneles_excel.py`: `notas`, `confianza`, `fuente_NsA`,
  `sdm_fuente`, `sdm_advertencia` filtrados.
- `datos/catalogo_inversores_excel.py`: `notas`, `confianza` filtrados.
- `calculos/asistente.responder`: respuesta filtrada; `PROMPT_SISTEMA` con la
  regla 6 y la regla 2 ampliada.

## Tipos de datos

`str`.

## Errores posibles

- Una frase queda menos fluida tras el reemplazo: se corrige a mano en el
  texto fuente (los cuatro casos del selector de 🔀 Mismatch y de Producción).

## Dependencias

`re` (estándar).

## Criterios de aceptación

1. El manual del Asistente no contiene el nombre.
2. Ningún texto entre comillas de `pages/`, `calculos/` ni `utils/` lo
   contiene (salvo nombres internos en minúscula).
3. Los catálogos cargados no lo muestran en notas, confianza ni fuentes.
4. La respuesta del Asistente no lo contiene aunque el modelo lo escriba.
5. «pvlib.pvsystem» no se modifica.
