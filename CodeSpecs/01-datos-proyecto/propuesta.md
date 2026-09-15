# Propuesta — Datos del proyecto

**Estado:** completado

## Objetivo

Documentar como contrato formal las reglas de negocio ya implementadas en el módulo
de entrada del proyecto (rangos por tipo de instalación, invalidación en cascada al
cambiar de ciudad, sincronización de tarifa) y corregir el único defecto real
identificado: `set_tarifa_from_ciudad()` sobreescribe la tarifa eléctrica sin
verificar si el usuario ya la había corregido manualmente con su factura real,
perdiendo esa corrección de forma silenciosa.

## Alternativas consideradas

1. **No tocar el código, solo documentar el comportamiento actual.** Deja el defecto
   de pérdida silenciosa de la tarifa sin corregir.
2. **Eliminar la precarga automática por ciudad** y dejar la tarifa siempre en blanco
   hasta que el usuario la ingrese. Simplifica la regla pero elimina una ayuda útil
   (el valor aproximado por operador regional) para usuarios que aún no tienen la
   factura a mano.
3. **Añadir una regla de precedencia explícita**: `set_tarifa_from_ciudad()` solo
   sobreescribe el valor si `tarifa_fuente` actual es `"catálogo"` o `"valor por
   defecto"`. Si la fuente ya es `"Proyecto"` o `"Financiero"` (edición manual), se
   conserva el valor del usuario y se muestra un aviso informando que existe un valor
   de referencia distinto para la nueva ciudad, sin sobreescribir automáticamente.

## Alternativa recomendada

La alternativa 3: mantiene la ayuda de precarga por región/operador para el caso
común (usuario sin factura a mano todavía), pero deja de descartar silenciosamente
una corrección manual ya hecha con la factura real. Es el cambio de menor alcance
que resuelve el defecto sin quitar funcionalidad existente. Se detalla en
`diseno.md` como parte del contrato de `01-datos-proyecto`.
