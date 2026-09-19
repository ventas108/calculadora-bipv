# Plantilla OpenSpec para calculadora BIPV

> Copie este archivo dentro de `.openspec/proposals/<nombre-del-caso>/` y complete cada sección antes de implementar código.

---

# 1. Identificación

- **ID del caso:** `nombre-corto-del-caso`
- **Título:** [título claro]
- **Fecha:** [AAAA-MM-DD]
- **Responsable:** [nombre]
- **Estado:** `draft | review | approved | implemented | validated | archived`
- **Rama:** [nombre de la rama]

---

# 2. Problema

## Qué ocurre actualmente

[Describa el comportamiento observado con palabras sencillas.]

## Qué debería ocurrir

[Describa el comportamiento esperado.]

## Evidencia

- Documento, reporte o caso: [ruta o referencia]
- Pasos para observarlo: [pasos]
- Valores de entrada: [valores y unidades]
- Resultado observado: [resultado]
- Resultado esperado: [resultado]

---

# 3. Objetivo

[Escriba un objetivo concreto y comprobable. Evite objetivos generales como “mejorar todo el cálculo”.]

Ejemplo:

> Alinear la selección de la serie meteorológica y la región usada por el cálculo de producción para que el caso de Urabá utilice las mismas entradas validadas en todo el flujo.

---

# 4. Alcance

## Incluido

- [ ] [módulo o comportamiento incluido]
- [ ] [módulo o comportamiento incluido]

## No incluido

- [ ] [refactor no necesario]
- [ ] [cambio visual fuera del objetivo]
- [ ] [funcionalidad futura]

---

# 5. Módulos afectados

## Shared

- [ ] `shared/shading-engine-contract.ts`
- [ ] `shared/colombianRegions.ts`
- [ ] [otro archivo]

## Server

- [ ] [archivo o ruta]
- [ ] [orquestador o procedimiento]

## Client

- [ ] [componente o formulario]
- [ ] [mapeo de datos o presentación]

## Documentación o configuración

- [ ] [archivo]

> Si una sección no aplica, escriba “No aplica” y explique brevemente por qué.

---

# 6. Ruta actual del cálculo

Describa el recorrido real del dato:

```text
Entrada -> validación -> shared -> server -> resultado -> client
```

## Entrada

- Nombre del dato: [nombre]
- Tipo y unidad: [tipo/unidad]
- Origen: [formulario, API, archivo, región, etc.]

## Transformaciones

1. [transformación y archivo]
2. [transformación y archivo]
3. [transformación y archivo]

## Salida

- Nombre del resultado: [nombre]
- Tipo y unidad: [tipo/unidad]
- Consumidores: [módulos o pantalla]

---

# 7. Restricciones y contratos

- El contrato `shared/shading-engine-contract.ts` debe [describir protección].
- La lógica de `shared/colombianRegions.ts` debe [describir protección].
- Las unidades de entrada y salida deben mantenerse en [unidades].
- No se deben cambiar APIs públicas salvo que [razón].
- No se deben añadir dependencias salvo que [justificación].
- Debe mantenerse compatibilidad con [flujo o consumidor].

---

# 8. Hipótesis de causa raíz

## Hipótesis

[Explique por qué cree que ocurre el problema. Debe ser verificable.]

## Evidencia que la apoya

- [archivo, función, prueba o documento]
- [archivo, función, prueba o documento]

## Prueba que puede refutarla

[Describa una comprobación que demostraría que la hipótesis es incorrecta.]

---

# 9. Comportamiento esperado

## Escenario principal

**Dado que:** [condición inicial]

**Cuando:** [acción]

**Entonces:** [resultado verificable]

## Casos límite

- [caso límite y resultado esperado]
- [caso límite y resultado esperado]

## Errores esperados

- [entrada inválida y respuesta esperada]
- [dato ausente y respuesta esperada]

---

# 10. Diseño técnico

## Decisión principal

[Describa qué módulo es dueño del comportamiento y por qué.]

## Cambios previstos

1. [cambio en shared]
2. [cambio en server]
3. [cambio en client, si aplica]

## Cambios explícitamente evitados

- [cambio no necesario]
- [refactor no relacionado]

## Compatibilidad

[Explique qué consumidores existentes deben seguir funcionando.]

---

# 11. Plan de tareas

- [ ] Revisar estado de git y rama.
- [ ] Confirmar la ruta real del cálculo.
- [ ] Revisar contratos y tipos compartidos.
- [ ] Revisar validación y orquestación del servidor.
- [ ] Añadir o actualizar prueba específica.
- [ ] Implementar el cambio mínimo.
- [ ] Ejecutar la prueba específica.
- [ ] Ejecutar typecheck, lint o build según corresponda.
- [ ] Revisar el mapeo y la presentación en client.
- [ ] Documentar resultados y riesgos.
- [ ] Archivar la propuesta.

---

# 12. Plan de validación

## Prueba principal

- **Comando:** `[comando]`
- **Qué demuestra:** [comportamiento comprobado]
- **Resultado esperado:** [resultado]

## Validaciones adicionales

- **Comando:** `[comando]`
- **Qué demuestra:** [comportamiento comprobado]
- **Resultado esperado:** [resultado]

## Validación manual

1. [paso]
2. [paso]
3. [resultado esperado]

---

# 13. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---:|---:|---|
| [riesgo] | baja/media/alta | bajo/medio/alto | [acción] |

---

# 14. Registro de implementación

- **Fecha de inicio:** [AAAA-MM-DD]
- **Archivos modificados:** [rutas]
- **Decisiones tomadas:** [resumen]
- **Cambios descartados:** [resumen]

---

# 15. Registro de validación

- **Fecha:** [AAAA-MM-DD]
- **Comandos ejecutados:** [comandos]
- **Resultado:** `pass | fail | partial`
- **Evidencia:** [salida o referencia]
- **Riesgos restantes:** [riesgos]

---

# 16. Aprobación y cierre

- [ ] Propuesta revisada.
- [ ] Diseño revisado.
- [ ] Tareas completadas.
- [ ] Validación ejecutada.
- [ ] Riesgos documentados.
- [ ] Documentación actualizada.
- [ ] Propuesta archivada.

**Observaciones finales:**

[Escriba aquí la conclusión técnica.]
