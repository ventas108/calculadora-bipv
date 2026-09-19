# Guía paso a paso: SDD y OpenSpec en la calculadora BIPV

## Para qué sirve esta guía

Esta guía explica, con palabras sencillas, cómo iniciar y completar un cambio en la calculadora BIPV usando SDD y OpenSpec.

- **SDD** significa Specification-Driven Development: desarrollo guiado por una especificación.
- **OpenSpec** es la estructura de archivos que permite escribir, revisar y conservar esa especificación.

La regla principal es:

> Primero describimos y entendemos el cambio. Después escribimos código.

---

## El flujo completo en una frase

```text
Problema -> Propuesta -> Diseño -> Tareas -> Implementación -> Validación -> Archivo
```

En este repositorio se representa así:

```text
/opsx:propose -> /opsx:apply -> /opsx:validate -> /opsx:archive
```

No es necesario memorizar los comandos. Lo importante es entender qué resultado debe producir cada etapa.

---

## Antes de empezar: qué debe tener claro el usuario

Antes de pedir cambios a Claude Code o a VS Agent, escriba una descripción sencilla:

- ¿Qué está ocurriendo?
- ¿Qué esperaba que ocurriera?
- ¿En qué pantalla, cálculo o informe se observa?
- ¿Tiene un ejemplo con valores?
- ¿Qué resultado considera correcto?

### Ejemplo

```text
En el caso de Urabá, la producción mensual parece desalineada con la irradiancia.
Espero que la producción use la misma región, temperatura y serie meteorológica
que utiliza el cálculo principal. Necesito revisar primero shared y server antes
de cambiar la pantalla.
```

No hace falta conocer todavía el nombre del archivo. El agente debe localizarlo, pero usted debe describir el comportamiento esperado.

---

## Paso 1: comprobar el estado del proyecto

Antes de trabajar, el agente debe revisar:

- la rama actual
- los cambios pendientes
- si hay archivos modificados por otro trabajo
- el alcance de la tarea

Puede pedirlo así:

```text
Revisa el estado actual del repositorio y dime en qué rama estamos,
qué cambios pendientes existen y si hay algún riesgo de mezclar trabajos.
Todavía no edites archivos.
```

### Qué debe recibir como respuesta

Una respuesta clara que indique:

- rama actual
- archivos modificados o sin seguimiento
- si el trabajo puede comenzar sin interferir con otra tarea

---

## Paso 2: localizar la ruta real del cálculo

La calculadora está dividida en capas. Para una tarea de cálculo, el orden recomendado es:

1. `shared/`: contratos, tipos, regiones y lógica común
2. `server/`: validación, orquestación y cálculo
3. `client/`: formularios, llamadas y presentación

Los archivos críticos que siempre deben considerarse cuando correspondan son:

- `shared/shading-engine-contract.ts`
- `shared/colombianRegions.ts`

Pida al agente:

```text
Localiza la ruta completa de este cálculo desde la entrada hasta el resultado.
Revisa primero shared y server. Después revisa client solo para confirmar cómo
se envían y muestran los datos. No cambies nada todavía.
```

### Resultado esperado

El agente debe explicar:

- dónde entra el dato
- qué validaciones se aplican
- qué funciones calculan el resultado
- dónde se transforma el resultado
- dónde se muestra

Si no puede explicar ese recorrido, todavía no se debe implementar.

---

## Paso 3: crear la propuesta OpenSpec

La propuesta es la descripción formal del trabajo. Se crea dentro de:

```text
.openspec/proposals/<nombre-del-caso>/
```

Por ejemplo:

```text
.openspec/proposals/uraba-produccion-alineada/
```

La carpeta debe contener:

```text
proposal.md
 design.md
tasks.md
spec.yaml
```

No importa si al principio la propuesta es corta. Debe ser concreta y comprobable.

### Prompt recomendado

```text
Crea una propuesta OpenSpec para este problema: [describa el problema].
Incluye objetivo, estado actual, módulos afectados, restricciones,
comportamiento esperado, validación y riesgos. No implementes código todavía.
```

---

## Paso 4: revisar la propuesta antes del código

Lea la propuesta y compruebe estas preguntas:

- ¿El objetivo describe el problema real?
- ¿Aparecen `shared/` y `server/` cuando el cambio afecta cálculos?
- ¿Las restricciones protegen los contratos existentes?
- ¿El comportamiento esperado se puede comprobar?
- ¿La validación indica comandos o pruebas concretas?
- ¿Los riesgos están escritos?

Si algo no está claro, pida corregir la propuesta. Esta es la etapa más barata para cambiar de dirección.

Prompt útil:

```text
Revisa la propuesta como si fueras un revisor técnico.
Busca supuestos no demostrados, módulos omitidos, riesgos de compatibilidad
y criterios de validación incompletos. Corrige solo la propuesta, todavía no
modifiques código.
```

---

## Paso 5: completar el diseño técnico

`design.md` explica cómo debería funcionar la solución.

Debe responder:

- ¿Qué módulo es dueño del comportamiento?
- ¿Qué datos entran y salen?
- ¿Qué contrato se conserva?
- ¿Qué casos límite existen?
- ¿Qué parte no se va a modificar?

Para cálculos BIPV, incluya cuando aplique:

- irradiancia
- temperatura
- región colombiana
- sombreado
- geometría
- pérdidas
- producción
- unidades y conversiones

El diseño no debe inventar valores. Cuando un dato no esté confirmado, debe marcarse como pendiente de verificación.

---

## Paso 6: dividir el trabajo en tareas

`tasks.md` convierte el diseño en acciones pequeñas.

Una tarea buena indica:

- qué revisar o cambiar
- en qué módulo
- cómo comprobarlo
- si depende de otra tarea

Ejemplo:

```text
- [ ] Confirmar el contrato de entrada en shared.
- [ ] Confirmar la fuente regional usada por server.
- [ ] Añadir o ajustar la prueba del cálculo.
- [ ] Implementar el cambio mínimo en el módulo dueño.
- [ ] Ejecutar typecheck y la prueba específica.
- [ ] Revisar la presentación en client.
```

No marque una tarea como terminada solo porque el archivo fue editado. Debe existir una comprobación.

---

## Paso 7: implementar con `/opsx:apply`

Cuando la propuesta, el diseño y las tareas estén revisados, se puede implementar.

Prompt recomendado:

```text
Aplica únicamente las tareas aprobadas de esta propuesta OpenSpec.
Respeta shared/shading-engine-contract.ts y shared/colombianRegions.ts.
No hagas refactors no relacionados. Antes de editar, resume la hipótesis
sobre la causa raíz y la prueba que puede confirmarla.
```

Durante la implementación:

- cambie primero el módulo que controla el comportamiento
- conserve las APIs públicas si no es necesario modificarlas
- no corrija problemas ajenos a la propuesta
- mantenga los cambios pequeños

---

## Paso 8: validar con `/opsx:validate`

La validación debe demostrar que el cambio funciona y que no rompe el proyecto.

Use la prueba más pequeña que pueda detectar el problema:

- prueba específica del cálculo
- typecheck
- lint
- build
- validación del flujo completo, si corresponde

Prompt recomendado:

```text
Valida esta implementación según la propuesta OpenSpec.
Ejecuta primero la prueba más específica. Después ejecuta typecheck o build
si el cambio lo requiere. Informa los comandos ejecutados, el resultado y
cualquier riesgo restante. No afirmes éxito sin evidencia.
```

Una validación fallida no significa que el proceso fracasó. Significa que se encontró información útil. Se corrige la causa y se repite la misma comprobación.

---

## Paso 9: revisar la interfaz al final

Solo después de confirmar la lógica compartida y del servidor se revisa la UI.

Compruebe:

- que los valores se envían con las unidades correctas
- que el resultado mostrado corresponde al resultado calculado
- que no se redondea demasiado pronto
- que los mensajes de error siguen la validación real
- que la pantalla no oculta una diferencia entre datos de entrada y salida

Una modificación visual no debe usarse para ocultar un error de cálculo.

---

## Paso 10: archivar el trabajo

Cuando el cambio esté validado:

- actualice las tareas completadas
- registre las pruebas ejecutadas
- documente decisiones importantes
- anote riesgos pendientes
- archive la propuesta según el flujo OpenSpec del proyecto

El resultado final debe permitir que otra persona entienda qué cambió y por qué.

---

## Cómo pedir ayuda a Claude Code sin ser experto

Use prompts con cuatro partes:

1. **Contexto:** qué módulo o caso está trabajando
2. **Objetivo:** qué comportamiento necesita
3. **Restricciones:** qué no se debe romper
4. **Salida esperada:** análisis, propuesta, código o validación

### Plantilla de prompt

```text
Contexto: estoy trabajando en [caso o módulo] de la calculadora BIPV.
Objetivo: necesito [comportamiento esperado].
Restricciones: respeta los contratos compartidos, la lógica regional colombiana
y la arquitectura shared/server/client. No hagas cambios no relacionados.
Salida: [analiza / crea propuesta / implementa / valida] y explica la evidencia.
```

---

## Señales de que debe detenerse y revisar

Detenga la implementación y vuelva a la propuesta si:

- el agente quiere cambiar la UI sin revisar shared/server
- aparece un supuesto sin fuente en el código o la documentación
- se propone cambiar un contrato sin revisar sus consumidores
- no existe una prueba o criterio que demuestre el resultado
- se quieren añadir dependencias sin una razón documentada
- el cambio empieza a incluir archivos ajenos al objetivo

---

## Primera práctica recomendada

Para comenzar de forma segura, use el caso de Urabá agrivoltaica y pida únicamente un diagnóstico:

```text
Usa el caso de Urabá agrivoltaica como ejercicio SDD.
No edites código. Revisa la documentación y localiza la ruta del cálculo
relacionada con temperatura, región, irradiancia y producción.
Entrega un diagnóstico con archivos implicados, hipótesis verificables,
riesgos y propuesta de validación.
```

Después de revisar ese diagnóstico, se crea la propuesta OpenSpec concreta.

---

## Regla final

Si no puede explicar qué dato entra, qué módulo lo transforma y cómo se comprobará el resultado, todavía no es momento de implementar.
