# Prompt Claude — Validación BIPV NIST Round 2

```text
Actúa como investigador técnico y desarrollador principal para evaluar si el caso NIST Round 2 puede reproducirse honestamente en la APP calculadora-bipv.

Objetivo:
Determinar si el artículo “Measured Performance of Building Integrated Photovoltaic Panels—Round 2” (DOI 10.1115/1.1883237) ofrece un caso BIPV con entradas y resultados suficientes para compararlo contra el pipeline físico de la APP.

Clasificación que debes verificar explícitamente:
Este caso parece ser multi-panel dentro de una fachada vertical común, no un caso multi-fachada. No lo fuerces dentro del contrato multi-superficie si el PDF confirma una única orientación/plano. Evalúalo como benchmark eléctrico/térmico de fachada y separa esa conclusión de la validación geométrica multi-fachada de East2.

Regla principal:
No implementes ni declares una validación antes de extraer y verificar las entradas del artículo. Si faltan datos, documenta el bloqueo con precisión. No inventes defaults para sustituir datos ausentes.

Archivos de contexto obligatorios:
- references/candidato-validacion-bipv-nist-round2.md
- references/buildings-16-01668-east2-caso.md
- references/informe-validacion-east2-sunpower-e20327-app.md
- bipv_python/calculos/vinculador_sombra_multisuperficie.py
- bipv_python/calculos/transicion_multisuperficie.py
- bipv_python/calculos/adaptador_multisuperficie.py
- bipv_python/calculos/solar.py
- bipv_python/calculos/produccion_vigencia.py
- bipv_python/datos/tecnologias_bipv.py
- bipv_python/tests/test_flujo_fisico_multisuperficie_end_to_end.py
- bipv_python/tests/test_escenario_validacion_east2_sunpower.py

Fuente científica:
- DOI: https://doi.org/10.1115/1.1883237
- Título: Measured Performance of Building Integrated Photovoltaic Panels—Round 2
- Debes localizar y leer el PDF completo o una versión legítima accesible.
- No uses solo el abstract para afirmar reproducibilidad.

Fase 1 — Extracción bibliográfica
Extrae del PDF y documenta con página/tabla/figura:
- ubicación y coordenadas;
- altitud;
- orientación, tilt y geometría;
- marca/modelo de cada panel;
- Pmax, Voc, Isc, Vmp, Imp, área y coeficientes térmicos;
- número de módulos y configuración eléctrica;
- inversor, eficiencia y potencia AC nominal;
- aislamiento posterior, ventilación y configuración constructiva;
- fuente meteorológica, periodo y resolución;
- irradiancia, temperatura y viento;
- energía DC/AC mensual y anual medida;
- PR, pérdidas y métricas de error;
- incertidumbres experimentales;
- tablas o datos suplementarios disponibles.

Crea una tabla con:
- campo;
- valor;
- unidad;
- página/tabla/figura;
- publicado, inferido o ausente;
- si puede representarse en la APP.

Fase 2 — Decisión de reproducibilidad
Clasifica el caso antes de modificar código:
- reproducible;
- reproducible con supuestos;
- parcialmente reproducible;
- no reproducible.

Explica qué resultados finales sí pueden compararse y cuáles no.

Fase 3 — Mapeo al pipeline
Si hay datos suficientes, mapea explícitamente:
- datos del artículo → session_state;
- superficie → geometría/POA/sombra;
- panel → SDM;
- TMY → POA;
- temperatura → modelo térmico;
- inversor → etapa AC;
- medición → métrica de comparación.

Usa preferentemente:
`calculos.vinculador_multisuperficie.construir_y_recalcular_proyecto_fisico()`
según el nombre real existente en el repositorio.

No modifiques consumidores downstream ni actives multi-superficie por defecto.

Fase 4 — Implementación mínima, solo si procede
- Trabaja en una rama aislada.
- Añade primero pruebas reproducibles.
- Implementa solo el adaptador/escenario mínimo necesario.
- No modifiques código productivo si el bloqueo es la falta de datos científicos.
- No sustituyas mediciones faltantes con TMY sintético sin marcarlo como supuesto.
- No uses nRMSE de otro artículo como tolerancia de la APP.
- Mantén separados artículo, simulación original del artículo y APP.

Comparación obligatoria:
Genera una tabla con:
- magnitud;
- valor medido del artículo;
- valor simulado en el artículo, si existe;
- valor de la APP;
- diferencia absoluta;
- diferencia porcentual;
- fuente;
- incertidumbre/confianza;
- explicación.

Incluye, cuando sea posible:
- POA;
- energía DC;
- energía AC;
- PR;
- potencia instalada;
- temperatura de módulo;
- pérdidas térmicas;
- pérdidas por orientación/sombra;
- clipping;
- error mensual RMSE;
- bias anual.

Validación obligatoria:
- determinismo;
- ficha del módulo;
- configuración eléctrica;
- coherencia QCRad si se construye TMY;
- sensibilidad a TMY, geometría y sombra;
- no mezcla entre superficies;
- comparación mensual y anual;
- prueba de que un resultado inválido no se consume downstream.

Ejecuta las pruebas focales y la regresión relacionada. Reporta exactamente los comandos, conteos y warnings. No ocultes warnings.

Restricciones:
- No commit.
- No merge.
- No push.
- No despliegue.
- No modificar DigitalOcean.
- No cambiar el veredicto sin evidencia del PDF y de la ejecución.

Informe final obligatorio:
- deja Markdown en `references/informe-validacion-nist-round2-app.md`;
- incluye fuente y hash del PDF si está disponible;
- incluye extracción de tablas/figuras;
- incluye parámetros faltantes;
- incluye supuestos;
- incluye comparación numérica;
- incluye limitaciones;
- incluye veredicto final;
- indica claramente si el caso no puede ejecutarse por falta de datos.

Publica además el informe final en una web temporal accesible para revisión humana y entrega la URL.
```