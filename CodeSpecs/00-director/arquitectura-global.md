# Arquitectura global

## Capas del sistema

- **Frontend**: `client/` (React/TypeScript)
- **Backend**: `server/` (routers, procedimientos)
- **Motor Python de referencia**: `bipv_python/`
- **Tipos compartidos**: `shared/`

## Fuente de verdad por magnitud

Se completa durante la Fase 0 (arquitectura y contratos), antes de modificar fórmulas.

| Magnitud | Fuente de verdad | Ubicación |
|---|---|---|
| POA / irradiancia | _(pendiente de confirmar)_ | |
| Energía mensual/anual | _(pendiente de confirmar)_ | |
| Performance Ratio (PR) | _(pendiente de confirmar)_ | |
| Dimensionamiento eléctrico | _(pendiente de confirmar)_ | |
| Finanzas | _(pendiente de confirmar)_ | |

## Flujo funcional entre módulos

```text
Recurso solar
      ↓
Dimensionamiento
      ↓
Producción energética
      ↓
Pérdidas y temperatura
      ↓
Finanzas e informes
```

## Reglas de cambio

- Ningún módulo cambia unidades, nombres de variables o contratos sin registrar la
  decisión en [registro-de-decisiones.md](registro-de-decisiones.md).
- Los contratos vigentes que otros módulos consumen se resumen en
  [contratos-entre-modulos.md](contratos-entre-modulos.md).

## Propiedad de comparadores y asistentes

- Los comparadores de paneles, inversores y orientación, el Asistente general y
      los Analistas locales pertenecen hoy a la app Streamlit (`bipv_python/`).
- Los comparadores consumen los motores Python vigentes; no constituyen fuentes
      de verdad adicionales para POA, energía, PR, compatibilidad o finanzas.
- React y Streamlit son aplicaciones independientes. Compartir una magnitud exige
      un contrato aprobado; no autoriza copiar fórmulas ni asumir paridad funcional.
- La frontera operativa y de despliegue obligatoria está en
      [separacion-apps.md](separacion-apps.md) y forma parte del contexto del agente SDD.
