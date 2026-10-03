# Encargo para Claude: verificación pybdshadow como proveedor de `p_shade` eléctrico

Necesito realizar una verificación técnica y arquitectónica, todavía SIN modificar el código productivo.

Repositorio externo:
- https://github.com/ni1o1/pybdshadow

Repositorio de la aplicación:
- `/workspaces/calculadora-bipv`
- App Streamlit principal en `bipv_python/`

## Hipótesis que debes verificar

La hipótesis no es solamente que `pybdshadow` genere polígonos de sombra.

Quiero comprobar si su salida geométrica y/o su análisis de cobertura sobre cubierta puede transformarse de forma directa, reproducible y físicamente defendible en un factor eléctrico horario `p_shade` por superficie BIPV, y si esa capacidad puede quedar detrás de un contrato universal de proveedores de sombreado.

La pregunta central es:

> ¿Puede `pybdshadow`, quizá mediante una transformación pequeña y explícita, producir directamente el `p_shade[t]` que necesita el motor BIPV, o únicamente produce una medida geométrica que todavía requiere un modelo óptico/eléctrico adicional?

No des por cierta ninguna de las dos respuestas. Demuéstrala con código, ecuaciones, casos sintéticos y lectura del código real.

## Contexto local que debes leer antes de concluir

Lee estos archivos:

- `CodeSpecs/00-director/vision.md`
- `CodeSpecs/00-director/arquitectura-global.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
- `CodeSpecs/05-perdidas-y-temperatura/transicion-multisuperficie/problema.md`
- `CodeSpecs/05-perdidas-y-temperatura/transicion-multisuperficie/diseno.md`
- `CodeSpecs/05-perdidas-y-temperatura/transicion-multisuperficie/validacion.md`
- `bipv_python/calculos/sombras_3d.py`
- `bipv_python/calculos/transicion_multisuperficie.py`
- `bipv_python/calculos/adaptador_multisuperficie.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- pruebas existentes de sombras por superficie y multi-superficie.

Lee también directamente el código del repositorio externo, en particular:

- `src/pybdshadow/pybdshadow.py`
- `src/pybdshadow/analysis.py`
- `src/pybdshadow/preprocess.py`
- `src/pybdshadow/utils.py`
- pruebas y README.

## Verificación física obligatoria

Determina exactamente qué representan estas salidas de `pybdshadow`:

- geometrías `ground` y `roof`;
- intersecciones de sombra sobre cubiertas;
- `time`;
- `Hour`;
- cualquier conteo de cobertura temporal.

Después responde con evidencia si pueden producir un `p_shade` horario definido, por ejemplo:

```text
p_shade[t] = fracción de irradiancia efectiva perdida por sombra
```

Debes distinguir explícitamente entre:

1. fracción de área geométrica sombreada;
2. fracción de irradiancia directa bloqueada;
3. fracción de irradiancia global perdida;
4. factor de potencia DC perdido en el módulo/string;
5. factor agregado de energía AC perdida.

Si propones una conversión directa, escribe la ecuación, todas sus entradas y sus unidades. Evalúa como mínimo si requiere:

- irradiancia directa normal o sobre plano (`DNI`, `poa_direct`);
- irradiancia difusa (`DHI`, `poa_diffuse`);
- posición solar y ángulo de incidencia;
- orientación, inclinación y geometría real de la superficie BIPV;
- fracción de superficie sombreada;
- pérdidas por mismatch y bypass diodes;
- configuración de strings;
- temperatura y modelo eléctrico.

No aceptes como `p_shade` eléctrico una simple cuenta de horas de sol ni una fracción de área, salvo que se demuestre que el contrato actual de la app define `p_shade` exactamente así.

Verifica también si el análisis de `roof` de pybdshadow trabaja con cubiertas horizontales/extrusiones y qué ocurre con:

- superficies inclinadas;
- fachadas verticales;
- varias superficies con distinto tilt/azimuth;
- geometrías no planas o malladas;
- sombras parciales sobre módulos.

## Prototipo experimental obligatorio

Construye un prototipo desechable, fuera del código productivo, que use geometrías sintéticas y compare:

1. un obstáculo conocido y una superficie BIPV conocida;
2. la geometría de sombra de `pybdshadow`;
3. la intersección con la superficie;
4. la fracción geométrica sombreada;
5. el valor candidato de `p_shade` horario;
6. una referencia independiente calculada con geometría/ray-casting o una solución analítica simple.

El prototipo debe responder si la transformación es:

- directa y exacta dentro de una tolerancia definida;
- directa solo para una superficie horizontal;
- posible pero requiere una capa geométrica propia;
- imposible sin un modelo óptico/eléctrico adicional.

Conserva los comandos, entradas, salidas, ecuaciones, tolerancias y resultados reproducibles.

## Contrato universal de proveedor

Evalúa y propone una interfaz común conceptualmente equivalente a:

```python
ShadowProvider.calculate(
    surface_geometry,
    obstacles,
    solar_times,
    irradiance_context,
    electrical_context,
) -> ShadowResult
```

El contrato debe indicar si `p_shade` es:

- geométrico;
- óptico;
- eléctrico;
- o si deben existir campos separados para no mezclar significados.

Propón un `ShadowResult` que incluya, como mínimo:

- `surface_id`;
- timestamps completos y zona horaria;
- `p_shade` con definición matemática y unidades;
- fracción geométrica sombreada, si existe;
- componentes directa/difusa, si existen;
- geometría de sombra opcional;
- cobertura temporal y resolución;
- CRS, unidades y sistema de coordenadas;
- firma reproducible;
- versión del proveedor;
- capacidades declaradas;
- calidad/confianza;
- advertencias y datos faltantes;
- indicación inequívoca de “sombra cero calculada” frente a “no calculado”.

Determina qué parte puede proporcionar directamente pybdshadow y qué parte tendría que proporcionar el adaptador o el motor BIPV.

## Casos de aceptación

Diseña y ejecuta, como mínimo, estos casos:

- obstáculo al sur de una superficie horizontal;
- obstáculo al norte;
- obstáculo más bajo que la superficie;
- sombra cero;
- sombra total;
- sombra parcial;
- superficie inclinada;
- superficie vertical;
- dos superficies con orientaciones diferentes;
- timestamps nocturnos;
- TMY en zona horaria distinta de UTC;
- año bisiesto;
- comparación con el motor propio de la app;
- comparación de fracción geométrica frente a pérdida eléctrica.

Para cada caso informa:

- resultado esperado;
- resultado observado;
- error/tolerancia;
- si valida geometría, óptica, electricidad o solo integración.

## Integración con la app

Evalúa cómo alimentar:

```text
provider -> adaptador -> p_shade por superficie -> firma_sombra
         -> transicion_multisuperficie.py -> producción física
```

La integración debe preservar:

- rollback transaccional;
- bloqueo de superficies incompletas;
- ausencia de defaults silenciosos `p_shade = 0`;
- inclusión de proveedor, versión, geometría, obstáculos, TMY y configuración en `firma_sombra`;
- invalidación de producción, bypass, financiero y CO2 cuando cambie el resultado de sombra;
- activación opt-in hasta superar todos los gates;
- compatibilidad con los consumidores existentes de `multisup_*`.

No modifiques todavía:

- `session_state` productivo;
- consumidores `multisup_*`;
- `calculos/invalidacion.py`;
- modelo simplificado actual;
- contratos aprobados;
- motor productivo de sombras.

## Dependencias y riesgos

Evalúa:

- compatibilidad con la versión actual de Python;
- GeoPandas, Shapely, rtree y demás dependencias;
- rendimiento para muchas superficies y 8760 timestamps;
- cache y precálculo;
- CRS y precisión numérica;
- fallos cerca de amanecer/atardecer;
- licencia BSD-3-Clause;
- mantenimiento del repositorio;
- dependencia obligatoria frente a proveedor opcional.

## Entregables

Entrega un informe con:

1. conclusión explícita sobre si pybdshadow puede producir directamente `p_shade` eléctrico;
2. demostración y ecuaciones, no solo opinión;
3. resultados del prototipo;
4. diferencias entre `p_shade` geométrico, óptico y eléctrico;
5. contrato universal recomendado;
6. esquema de `ShadowResult`;
7. proveedor que debe ser pybdshadow y proveedor que debe seguir siendo propio;
8. riesgos y límites;
9. pruebas de aceptación;
10. cambios necesarios en la CodeSpec;
11. decisión final: proveedor universal principal, proveedor de sombras urbanas, adaptador experimental, referencia algorítmica o no recomendable.

Si hace falta una nueva Spec vertical, redacta un borrador de:

- `problema.md`;
- `propuesta.md`;
- `diseno.md`;
- `tareas.md`;
- `validacion.md`.

Déjalo como propuesta pendiente de aprobación humana. No implementes cambios productivos ni apruebes la arquitectura.

Al final, publica o entrega el informe en una web temporal para facilitar su revisión y deja también una copia local claramente identificable. Incluye todos los comandos ejecutados y sus resultados relevantes.
