# Plan — Cierre de persistencia y adopción multi-superficie

**Estado:** pendiente de implementación coherente
**Fecha:** 2026-09-21
**Base desplegada:** `c0caa2136`

## Objetivo

Cerrar las dos brechas que permanecen después de la integración multi-superficie:

1. impedir que una adopción global de orientación sobrescriba un proyecto multi-superficie;
2. persistir y restaurar resultados físicos multi-superficie con verificación completa de vigencia.

El modelo simplificado continúa siendo el comportamiento por defecto y el modo físico permanece opt-in.

## Fase 1 — Bloquear adopción global

- Localizar el comparador global de orientación y su acción de adopción.
- Permitir la comparación exploratoria cuando `multisup_activo=True`.
- Bloquear la adopción global si existe un proyecto multi-superficie activo.
- Mostrar un mensaje que dirija a Vista 3D / Multi-Superficie.
- Confirmar que los proyectos de una sola superficie mantienen el comportamiento actual.
- Verificar que la comparación bloqueada no modifica geometría, POA, sombra ni claves `multisup_*`.

Mensaje propuesto:

> Este proyecto tiene varias superficies. Configure y adopte la orientación desde Vista 3D, superficie por superficie.

## Fase 2 — Nueva Spec de persistencia

Crear una Spec vertical separada para definir:

- payload canónico;
- superficies y geometrías;
- puntos y malla de sombra;
- `p_shade` y `firma_sombra`;
- POA y `firma_poa`;
- inversores y asignaciones;
- `n_serie` y `n_paralelo`;
- TMY y fuente solar;
- resultados DC/AC;
- versión de esquema;
- migración y rechazo de versiones no soportadas;
- rollback completo.

## Fase 3 — Payload y firmas

Diseñar funciones puras equivalentes a:

```python
construir_payload_multisuperficie(...)
firmar_payload_multisuperficie(...)
validar_payload_multisuperficie(...)
restaurar_multisuperficie(...)
```

El payload debe separar claramente:

- entradas persistidas;
- resultados calculados;
- firmas de vigencia;
- metadatos del proveedor y algoritmo.

No se deben serializar DataFrames u objetos no serializables sin una representación canónica definida.

## Fase 4 — Restauración segura

Flujo obligatorio:

```text
cargar proyecto
  -> validar schema
  -> validar payload
  -> validar firma global
  -> validar TMY
  -> validar geometría
  -> validar firma_sombra
  -> validar firma_poa
  -> validar configuración eléctrica
  -> restaurar todo o rechazar todo
```

Si falla una superficie o una firma:

- no restaurar resultados físicos parciales;
- no escribir `multisup_*`;
- no alimentar Finanzas, Presupuesto, CO2, Baterías ni Reporte;
- informar la causa concreta.

## Pruebas obligatorias

- Persistencia y restauración válidas.
- Payload alterado.
- Firma global alterada.
- Firma de sombra alterada.
- Firma de POA alterada.
- TMY cambiado.
- Geometría, tilt o azimuth cambiados.
- Inversor o `N_serie` cambiados.
- Superficie eliminada.
- Inversor inexistente.
- Payload incompleto.
- Schema no soportado.
- Rollback si falla una superficie.
- Ninguna escritura parcial durante restauración.
- Rechazo de adopción global con `multisup_activo=True`.
- Proyectos de una superficie sin regresión.
- Modelo simplificado sin regresión.

## Validación operativa

1. Crear dos superficies.
2. Calcular sombra y POA.
3. Configurar inversores.
4. Adoptar el resultado físico.
5. Guardar el proyecto.
6. Cerrar y abrir una sesión nueva.
7. Restaurar y verificar firmas.
8. Alterar una firma y confirmar rechazo.
9. Confirmar que no llegan datos obsoletos a consumidores downstream.

## Gates

No se declara esta fase completada hasta que:

- la adopción global quede bloqueada o sea por superficie;
- exista persistencia canónica validada;
- exista restauración todo-o-nada;
- pasen las pruebas de consumidores downstream;
- se actualicen Director, contratos y base de conocimiento del Asistente;
- se haga revisión humana del diff;
- GitHub y DigitalOcean queden en el mismo commit después del despliegue.

## Fuera de alcance inicial

- Editor gráfico de puntos sobre la malla.
- Motor Óptico independiente por superficie.
- Activar el modo físico como default.
- Migrar consumidores downstream a otro contrato.
