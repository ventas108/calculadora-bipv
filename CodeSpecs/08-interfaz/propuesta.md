# Propuesta — Interfaz

**Estado:** completado

## Objetivo

Formalizar el contrato de página compartido por toda la app y dejar explícito
que la capa de interfaz no es responsable de la vigencia de los datos que
muestra — esa garantía vive en `03`–`06`.

## Alternativas consideradas

1. **No documentar nada** — descartada: sin contrato publicado, un cambio
   futuro en `utils/ui.py` o en el orden del boilerplate de página podría
   romper el bloqueo de traducción o el banner de proyecto activo en alguna
   página sin que nadie lo note en el director.
2. **Agregar una verificación de vigencia dentro de `utils/ui.py`** —
   descartada: no se encontró evidencia de que la interfaz restaure o
   reutilice datos por su cuenta; agregar lógica de vigencia ahí duplicaría
   lo que ya hacen `04` y `06`.
3. **Documentar el contrato tal como existe hoy**, con el mismo enfoque usado
   en `07-informes`.

## Alternativa recomendada

La 3: regularización documental sin cambios de código.

