# Primer ejercicio con Claude y Copilot en la Calculadora BIPV

## Objetivo

Aprender a usar las dos herramientas sobre este proyecto real:

- **Claude Code**, desde la terminal: exploración profunda, análisis de arquitectura, seguimiento de la ruta del cálculo, ejecución de comandos, validación y revisión de cambios.
- **GitHub Copilot**, desde este cuadro de VS Code: explicación rápida, autocompletado, edición guiada, comentarios puntuales, refactorización y revisión del código mientras trabajas.
- **Agente SDD**, como gatekeeper de preparación y control: auditoría determinista de Specs, revisión de contratos, dependencias, riesgos y validaciones antes de crear tareas o tocar código.

La regla más importante es simple: **una herramienta debe terminar su edición antes de que la otra edite el mismo archivo**.

El agente SDD no reemplaza a Claude ni a Copilot y no ejecuta cambios autónomos.
Su función es preparar y detener el flujo cuando falten datos:

```text
problema -> propuesta -> diseño -> aprobación -> agente SDD -> tareas -> implementación -> validación -> completado -> archivado
```

## Qué puede hacer Claude en la terminal

Claude sirve especialmente para trabajos que necesitan recorrer varios archivos o ejecutar una secuencia completa:

1. **Reconocimiento del proyecto**: localizar páginas, componentes, routers, motores matemáticos, tipos y configuraciones.
2. **Análisis de la ruta del cálculo**: seguir un dato desde el formulario hasta el resultado, por ejemplo área, irradiancia, PR, potencia y energía anual.
3. **OpenSpec**: convertir una idea en una especificación de trabajo con objetivo, alcance, archivos afectados, criterios de aceptación y casos límite.
4. **Implementación amplia**: modificar frontend, backend y tipos compartidos manteniendo coherencia entre capas.
5. **Validación**: ejecutar `pnpm check`, `pnpm build`, pruebas, linters y comandos de diagnóstico.
6. **Depuración con evidencia**: leer logs, comparar entradas y salidas, reproducir errores y proponer la causa raíz.
7. **Revisión de cambios**: inspeccionar `git diff`, detectar regresiones, archivos olvidados y riesgos en cálculos o datos.
8. **Documentación técnica**: actualizar manuales, notas de operación y decisiones de diseño.
9. **Automatización**: preparar scripts para repetir verificaciones o generar informes.
10. **Preparación de commits o PR**: resumir cambios y dejar una lista de validaciones realizadas. El commit solo se crea si tú lo pides.

Claude no sustituye tu criterio de ingeniería: en cálculos fotovoltaicos debes revisar unidades, supuestos, fuente climática, PR, orientación, temperatura y límites eléctricos.

## Qué hace el agente SDD implementado

El agente está documentado en `CodeSpecs/00-director/agente-sdd.md` y se ejecuta
con `scripts/sdd-agent.ts`. Su auditoría objetiva comprueba:

- los seis documentos de una Spec: problema, propuesta, diseño, tareas, implementación y validación;
- secciones técnicas obligatorias: entradas, salidas, tipos, errores, dependencias y criterios de aceptación;
- documentos incompletos, estados inválidos y aprobación humana;
- capas y archivos probablemente afectados;
- riesgos de integración y comandos de validación;
- condiciones especiales de `09-despliegue`, como migraciones, variables de entorno, artefactos y rollback.

Cuando la Spec está completa y aprobada, puede enviar a Claude el contexto de la
Spec junto con el director central. Claude devuelve un informe estructurado con
hallazgos, contratos, dependencias, tareas propuestas, archivos afectados,
riesgos y validaciones faltantes.

El contrato es estricto: el agente no modifica código ni Specs, no cambia
contratos, no decide arquitectura, no ejecuta validaciones reales, no aprueba
Specs y no las marca como válidas. La revisión humana y los comandos reales
siguen siendo obligatorios.

## Qué puede hacer Copilot aquí en VS Code

Copilot es más cómodo para la interacción inmediata mientras tienes un archivo abierto:

- Explicar una función o un bloque seleccionado.
- Completar código a partir del contexto cercano.
- Crear una función pequeña siguiendo el estilo existente.
- Añadir validaciones, mensajes de error o tipos.
- Comentar una línea o una decisión concreta.
- Encontrar referencias y usos de una función.
- Revisar un diff y señalar riesgos.
- Convertir una necesidad en tareas pequeñas.
- Ejecutar comandos y comprobar el resultado cuando actúa como agente.
- Mantener la conversación contigo mientras decides qué cambiar.

Usa Copilot para preguntas como: "¿qué hace esta función?", "añade una validación para PR entre 0 y 100" o "explícame este error de TypeScript".

Usa Claude cuando la pregunta sea más parecida a: "sigue el cálculo completo desde el formulario hasta el resultado, encuentra dónde se pierde la unidad kWh/m2 y valida la corrección".

## Mapa mínimo de esta calculadora BIPV

Estas son las ubicaciones que usaremos en el ejercicio:

- `client/src/pages/Home.tsx`: página principal y composición del flujo web.
- `client/src/components/EnergyProductionSimulator.tsx`: simulación y presentación de producción energética.
- `client/src/lib/bipvToEnergyBridge.ts`: puente entre el dimensionamiento BIPV y la producción de energía.
- `client/src/lib/iamSoilingEngine.ts`: cálculo relacionado con pérdidas ópticas y suciedad.
- `server/routers.ts`: procedimientos de servidor y acceso a servicios.
- `bipv_python/calculos/solar.py`: motor solar Python.
- `bipv_python/pages/2_☀️_Recurso_Solar.py`: pantalla Python del recurso solar.
- `package.json`: comandos de desarrollo, comprobación, compilación y pruebas.

Comandos principales del proyecto:

```bash
pnpm install
pnpm dev
pnpm check
pnpm build
pnpm test
```

Nota: el script actual de `pnpm test` informa que no hay pruebas unitarias JavaScript configuradas. Por eso, en este primer ejercicio `pnpm check` y `pnpm build` son las validaciones ejecutables principales.

# Ejercicio 1: seguir un cálculo real sin romperlo

## Resultado esperado

Al terminar podrás explicar y comprobar esta cadena:

```text
entrada del proyecto
  -> datos solares y orientación
  -> potencia o dimensionamiento BIPV
  -> pérdidas / PR
  -> energía estimada
  -> resultado mostrado en pantalla
```

No vamos a cambiar código en el primer paso. Primero aprenderás a obtener evidencia. Después harás un cambio pequeño y verificable.

## Paso 1. Abrir el proyecto en VS Code

1. Abre la carpeta `/workspaces/calculadora-bipv`.
2. Abre una terminal normal con el perfil `bash` o una terminal `claude`.
3. Si Claude está activo, confirma que estás en la raíz:

```bash
pwd
```

El resultado debe ser:

```text
/workspaces/calculadora-bipv
```

## Paso 2. Pedir a Claude un OpenSpec de diagnóstico

En la terminal `claude`, pega esta solicitud:

```text
Trabaja en /workspaces/calculadora-bipv. No edites archivos todavía.

Quiero un OpenSpec para seguir la ruta completa del cálculo BIPV desde la
entrada del usuario hasta la energía producida. Inspecciona Home.tsx,
EnergyProductionSimulator.tsx, bipvToEnergyBridge.ts, server/routers.ts y
bipv_python/calculos/solar.py.

Entrega:
1. La cadena de llamadas y datos, con nombres exactos de funciones.
2. Las unidades de cada entrada y salida.
3. Dónde se aplica PR, pérdidas, orientación, irradiancia y potencia.
4. Tres riesgos de cálculo o conversión de unidades.
5. Comandos concretos para validar sin modificar código.
6. Un cambio pequeño y reversible para el siguiente paso.

No inventes funciones: si algo no está confirmado en el código, márcalo como
pendiente de verificar.
```

### Qué debes observar

Claude debe devolverte rutas y símbolos reales, no una explicación genérica. Si inventa un nombre, pídele:

```text
Muestra el archivo y el fragmento exacto donde confirmas ese nombre antes de seguir.
```

Ese hábito es importante en cálculos: una respuesta convincente no reemplaza la evidencia del código.

## Paso 2A: pasar la Spec por el agente SDD

Antes de convertir el análisis en tareas, ejecuta la auditoría determinista desde
la raíz del repositorio:

```bash
pnpm exec tsx scripts/sdd-agent.ts --spec CodeSpecs/01-datos-proyecto
```

También puedes solicitarla desde VS Code con **Tasks: Run Task** -> **SDD:
auditar Spec (alertas tempranas)**. La tarea muestra las alertas en la terminal y
termina con código `2` cuando encuentra un bloqueo. No modifica la Spec.

En el estado inicial del repositorio, esta Spec está deliberadamente en `idea` y
contiene plantillas pendientes. Por tanto, el agente debe bloquearla y mostrar
motivos como documentos faltantes, secciones incompletas y falta de aprobación.
Ese bloqueo confirma que el agente está funcionando como control de preparación,
no como un generador que inventa requisitos.

Pídele a Claude que use esos motivos para completar la Spec, sin editar todavía:

```text
Usa el informe del agente SDD como lista de bloqueos. Completa una propuesta de
Spec para seguir el cálculo BIPV, pero no cambies archivos ni marques la Spec
como aprobada. Para cada entrada, salida, contrato, dependencia y criterio de
aceptación indica la evidencia que falta y los supuestos que deben aprobarse.
```

Cuando una persona haya revisado y aprobado los seis documentos, vuelve a
ejecutar la auditoría. El resultado debe indicar `canRunPreparation: true`.
Solo entonces se permite solicitar la preparación de Claude:

Desde VS Code puedes usar **Tasks: Run Task** -> **SDD: preparar revisión Claude
(solo aprobada)**. Esta tarea también se detiene con código `2` si falta la
aprobación humana.

```bash
ANTHROPIC_API_KEY=... pnpm exec tsx scripts/sdd-agent.ts \
  --spec CodeSpecs/01-datos-proyecto --review
```

El informe de Claude sirve para ordenar el trabajo. No lo tomes como aprobación:
convierte las tareas propuestas en `tareas.md`, revisa los archivos afectados y
ejecuta las validaciones reales antes de implementar.

## Paso 3. Hacer la misma pregunta a Copilot

Vuelve a este chat de VS Code y escribe:

```text
Analiza la ruta del cálculo BIPV en este repositorio. Empieza por
client/src/pages/Home.tsx y sigue hasta bipvToEnergyBridge.ts y
EnergyProductionSimulator.tsx. No edites nada. Dame solo los nombres reales de
las funciones, sus entradas, salidas y unidades. Señala cualquier punto que no
puedas confirmar.
```

Compara ambas respuestas. El objetivo no es escoger un ganador: es comprobar que ambos agentes llegan al mismo código y que tú puedes verificarlo.

En este punto compara también los roles: Claude puede investigar y redactar el
contexto; Copilot puede ayudarte a inspeccionar o editar un cambio local; el
agente SDD decide determinísticamente si la Spec está suficientemente preparada
para pasar a tareas. Ninguno elimina la revisión humana.

## Paso 4. Ejecutar la validación base

Desde una terminal `bash` ejecuta:

```bash
pnpm check
pnpm build
```

Guarda mentalmente el resultado. Esta es la **línea base**: antes de tocar código sabes si el proyecto ya compilaba.

Si `pnpm install` aún no se ha ejecutado, hazlo primero. No ejecutes `pnpm db:push` en este ejercicio, porque puede modificar la base de datos y no es necesario para inspeccionar la ruta de cálculo.

## Paso 5. Ejecutar la calculadora

En una terminal `bash` ejecuta:

```bash
pnpm dev
```

Abre la URL local que muestre la terminal, normalmente `http://localhost:3000`.

Prueba un caso controlado, anotando los valores que uses. Por ejemplo:

- Área disponible: `50 m2`
- Tarifa: `650 COP/kWh`
- PR: `80 %`
- Densidad de potencia: `200 W/m2`
- Fachada sur: azimuth `180 grados`
- Fachada vertical: tilt `90 grados`
- Albedo: `0.20`

No tomes estos valores como un diseño final. Son entradas de prueba para observar la cadena y detectar cambios de orden de magnitud.

## Paso 6. Formular una hipótesis medible

Pide a Claude:

```text
Con la línea base ya validada, formula una hipótesis sobre el cálculo de
energía para el caso 50 m2, 200 W/m2, PR 80%, azimuth 180 y tilt 90.
No cambies código. Indica qué variable debería cambiar si aumento el área de
50 a 100 m2 y qué resultado debería permanecer igual. Propón una comprobación
manual y una comprobación en la interfaz.
```

La idea es separar:

- Variables que deberían escalar, como potencia instalada y energía anual.
- Variables que no deberían cambiar solo por duplicar el área, como recurso solar del sitio o rendimiento específico en kWh/kWp.

## Paso 7. Realizar un cambio pequeño con Copilot

Ahora sí, pide a Copilot un cambio acotado:

```text
En el punto exacto donde se presenta el resultado de energía anual, añade una
etiqueta clara de la unidad si falta. Antes de editar, identifica el archivo,
la función y el valor que se está mostrando. No cambies la fórmula ni el orden
de los cálculos. Haz el cambio mínimo y dime cómo validarlo.
```

Revisa el diff. Debes confirmar que solo cambió presentación o rotulado, no la fórmula.

## Paso 8. Validar después del cambio

Ejecuta otra vez:

```bash
pnpm check
pnpm build
```

Después prueba en el navegador:

1. El caso de 50 m2.
2. El mismo caso con 100 m2.
3. Un valor inválido de PR, como `120`, si la interfaz permite escribirlo.
4. Una orientación distinta, por ejemplo azimuth `0`.

Registra qué cambió y qué permaneció igual. Si falla, vuelve a la hipótesis, no a una edición al azar.

# Cómo pedir ayuda de forma precisa

Una buena solicitud contiene cinco piezas:

1. **Contexto**: qué parte de la calculadora estás usando.
2. **Síntoma**: qué observas realmente.
3. **Entrada**: valores concretos y unidades.
4. **Restricción**: qué no debe cambiar.
5. **Validación**: cómo sabremos que quedó bien.

Ejemplo:

```text
En EnergyProductionSimulator.tsx, con área 50 m2 y PR 80%, la energía anual
aparece como cero. No cambies el motor solar ni la base de datos. Sigue el dato
hasta su origen, identifica la primera función que produce cero y propón un
parche mínimo. Valida con pnpm check y una prueba manual en la interfaz.
```

# Catálogo práctico de usos futuros

## Análisis y OpenSpec

```text
No edites. Convierte este requerimiento en OpenSpec con alcance, archivos,
contrato de datos, casos límite, criterios de aceptación y plan de validación.
```

## Control SDD antes de implementar

```text
Lee el informe del agente SDD para esta Spec. No edites. Comprueba que cada
tarea tenga una entrada, una salida, un archivo responsable y una validación.
Señala dependencias no declaradas, contratos incompatibles y decisiones que
requieren aprobación humana.
```

## Ruta de cálculo

```text
Sigue `energiaAnual` desde su origen hasta la pantalla. Para cada paso indica
entrada, salida, unidad y conversión. Detente si el nombre cambia o si no hay
evidencia suficiente.
```

## Validación

```text
Ejecuta pnpm check y pnpm build. Si fallan, clasifica cada error como
bloqueante, preexistente o causado por el último cambio. No arregles errores no
relacionados.
```

## Revisión

```text
Revisa el diff como ingeniero fotovoltaico y como mantenedor TypeScript.
Prioriza errores de unidades, límites, valores nulos, datos climáticos y
regresiones. Devuelve primero los hallazgos y luego un resumen.
```

## Comentario puntual

```text
Explícame solo esta función en cinco líneas: propósito, entradas, salida,
unidades y riesgo principal.
```

## Autocompletado controlado

```text
Completa esta función siguiendo el estilo del archivo. No introduzcas nuevas
dependencias, no cambies la API pública y deja explícitos los casos de entrada
vacía o inválida.
```

# Reglas de trabajo recomendadas

- Antes de editar, pide primero análisis y archivos exactos.
- Ejecuta el agente SDD después de aprobar la Spec y antes de convertirla en tareas.
- Haz un cambio pequeño por vez.
- Guarda una línea base con `pnpm check` y `pnpm build`.
- No aceptes una fórmula solo porque el resultado parece razonable.
- Revisa siempre unidades: W, kW, Wh, kWh, m2, kWh/m2 y porcentaje.
- No ejecutes migraciones de base de datos para validar una interfaz.
- No dejes a Claude y Copilot editando el mismo archivo al mismo tiempo.
- Después de cada edición, ejecuta una validación enfocada.
- Mantén los cambios relacionados con el objetivo; no mezcles refactorizaciones.
- Si el resultado es financiero o energético, conserva los valores de entrada usados para reproducirlo.
- Si el agente SDD bloquea el flujo, corrige la Spec o consigue la aprobación necesaria; no fuerces la implementación.

# Qué debe quedar al terminar el ejercicio

- Entiendes cuándo usar Claude y cuándo usar Copilot.
- Entiendes que el agente SDD prepara y controla el flujo, pero no implementa ni aprueba por ti.
- Sabes localizar la ruta de un cálculo real.
- Puedes interpretar un informe de bloqueo y convertirlo en requisitos verificables.
- Tienes una línea base de compilación.
- Ejecutaste la calculadora con entradas conocidas.
- Hiciste un cambio pequeño sin alterar la fórmula.
- Validaste antes y después.
- Puedes pedir el siguiente trabajo con contexto, restricciones y criterio de aceptación.
