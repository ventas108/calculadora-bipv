# Validación — Interfaz

**Estado:** completado

## Checklist de validación del módulo

- [x] Evidencia estática: `utils/ui.py` (`mostrar_proyecto_activo`,
      `bloquear_traduccion`) no lee ni escribe firmas, resultados persistidos
      ni banderas de vigencia.
- [x] Evidencia estática: el texto de usuario interpolado en HTML se escapa
      con `html.escape()` antes de renderizarse.
- [x] Sin cambios de código; no aplica ejecutar pruebas nuevas.

## Resultado

Regularización documental cerrada. El módulo queda sin deuda SDD pendiente;
si una futura página o utilidad de Interfaz agrega restauración o invalidación
propia, esta Spec debe reabrirse con el mismo rigor que `06`.

