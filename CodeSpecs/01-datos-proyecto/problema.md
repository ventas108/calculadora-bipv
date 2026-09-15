# Módulo 01 — Datos del proyecto

**Estado:** completado

## Alcance de la fase

Área, ciudad, tarifa, PR objetivo, densidad de potencia y configuración inicial del proyecto.

## Problema a resolver

El módulo de entrada del proyecto (`bipv_python/pages/1_🏠_Proyecto.py`) captura los
datos que alimentan todo el flujo de cálculo — ciudad/coordenadas, tipo de instalación,
área disponible, factor de ocupación, tarifa eléctrica, PR y densidad de potencia — pero
sus reglas de negocio viven únicamente implícitas en el código, sin contrato
documentado:

- Los rangos válidos y valores por defecto de PR y densidad de potencia dependen del
  `tipo_instalacion` seleccionado (`TIPOS_INSTALACION` en el propio archivo) y no están
  descritos en ningún lugar fuera del código.
- Cambiar de ciudad dispara una invalidación en cascada de claves de `session_state`
  (`densidad_Wm2`, `PR`, `tilt_default`, recurso solar, resultados de producción
  persistidos) que ningún otro módulo puede anticipar sin leer este archivo.
- La tarifa eléctrica se sincroniza como fuente de verdad global entre este módulo y
  `06-analisis-financiero` (`tarifa_utils.py`). Los valores por ciudad del catálogo
  (`tarifa_comercial_cop_kwh`) son intencionalmente una **aproximación por
  región/operador** (Codensa, EPM, Air-e, EMCALI, etc.) que el usuario debe corregir
  con el valor real de su factura de servicios públicos. El riesgo no documentado es
  que `set_tarifa_from_ciudad()` sobreescribe **incondicionalmente** la tarifa al
  cambiar de ciudad, sin importar si el usuario ya la había corregido manualmente con
  su factura real (`tarifa_fuente = "Proyecto"` o `"Financiero"`) — perdiendo esa
  corrección de forma silenciosa y sin aviso.

Sin una Spec, cualquier cambio en este módulo (o en los que dependen de él) corre el
riesgo de romper compatibilidad silenciosamente, porque no hay un documento de
referencia que declare entradas, salidas, invariantes y errores esperados.

## Contexto

Este es el módulo inicial de la calculadora: no depende de ningún otro, pero
`02-recurso-solar`, `03-dimensionamiento` y `06-analisis-financiero` consumen sus
salidas (coordenadas del sitio, área útil, tarifa, PR y densidad de potencia) vía
`session_state` compartido. Se aborda ahora porque es el punto de entrada natural para
adoptar SDD de forma incremental: formalizar este módulo primero permite validar el
flujo completo (`problema -> propuesta -> diseño -> aprobación -> agente SDD -> tareas
-> implementación -> validación`) sobre funcionalidad ya construida y en producción,
antes de aplicarlo a módulos con lógica de cálculo más compleja.
