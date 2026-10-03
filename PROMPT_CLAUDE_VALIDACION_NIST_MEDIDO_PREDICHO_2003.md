# Prompt Claude — NIST 2003 medido versus predicho

```text
Evalúa con rigor si el artículo “Measured Versus Predicted Performance of Building Integrated Photovoltaics” (DOI 10.1115/1.1532006, Dougherty/Fanney/Davis, 2003) puede convertirse en un caso de comparación cuantitativa para la APP calculadora-bipv.

Importante:
- Descarta NIST Round 2 como candidato de simulación; no lo uses como base de este trabajo.
- Este candidato debe evaluarse desde cero.
- No lo fuerces como caso multi-fachada: primero confirma si es un conjunto multi-panel en una superficie/fachada común.
- El objetivo es encontrar un artículo con resultados finales comparables, no llenar huecos con supuestos.

Contexto obligatorio:
- references/candidato-validacion-bipv-nist-medido-vs-predicho-2003.md
- references/informe-validacion-nist-round2-app.md (solo para evitar repetir el caso descartado)
- references/east2-validacion-informe.md
- bipv_python/calculos/transicion_multisuperficie.py
- bipv_python/calculos/vinculador_sombra_multisuperficie.py
- bipv_python/calculos/adaptador_multisuperficie.py
- bipv_python/calculos/solar.py
- bipv_python/calculos/produccion_vigencia.py
- bipv_python/datos/tecnologias_bipv.py

Fuente:
- DOI: https://doi.org/10.1115/1.1532006
- Localiza y lee el PDF completo mediante una fuente legítima.
- La búsqueda no termina con el abstract.
- Identifica también las referencias del artículo que puedan contener fichas eléctricas o datos meteorológicos, pero no las uses sin autorización y documentación separada.

Fase 1 — Extracción exacta
Para cada una de las cuatro tecnologías y sus dos variantes (aislada/no aislada), extrae con página, tabla o figura:
- ubicación, coordenadas y altitud;
- tilt, azimuth y geometría;
- dimensiones, área activa y área de cobertura;
- marca/modelo y ficha eléctrica;
- Pmax, Voc, Isc, Vmp, Imp y coeficientes térmicos;
- número de módulos y configuración eléctrica;
- aislamiento posterior y construcción;
- irradiancia, temperatura, viento y periodo;
- si los datos son numéricos o solo gráficos;
- energía medida y predicha mensual/anual;
- PR, RMSE, MBE, bias y cualquier intervalo de incertidumbre;
- parámetros y modelo usado por IV Curve Tracer/SNL.

Clasifica cada dato como publicado, inferido, ausente o tomado de una referencia externa.

Fase 2 — Gate de reproducibilidad
No escribas código hasta decidir si se cumplen todos:
1. ficha eléctrica suficiente para construir el SDM;
2. meteorología numérica o serie reconstruible sin inventar;
3. al menos una magnitud final absoluta comparable;
4. geometría y configuración suficientemente definidas.

Si falta uno, detén la implementación y emite “no reproducible” o “parcialmente reproducible” explicando el bloqueo. No uses valores nominales inventados, TMY sintético silencioso ni ficha de otro panel.

Fase 3 — Separación arquitectónica
Confirma si el caso es una fachada/superficie vertical común con paneles lado a lado. Si es así:
- no lo representes como varias superficies con orientaciones distintas;
- no lo presentes como validación multi-fachada;
- úsalo solo como benchmark eléctrico/térmico de una fachada, si los datos lo permiten.

East2 continúa siendo el caso de geometría/sombra multi-superficie y no debe mezclarse con este artículo.

Fase 4 — Simulación, solo si pasa el gate
Si los datos pasan el gate:
- crea una prueba de escenario reproducible;
- usa el pipeline físico existente;
- no modifiques consumidores downstream;
- no actives multi-superficie por defecto;
- separa medición del artículo, predicción publicada y APP;
- calcula diferencia absoluta, porcentual, RMSE mensual, MBE y bias anual;
- compara energía DC, temperatura y efecto del aislamiento;
- AC solo si el artículo realmente tiene inversor, si no marca “no aplica”.

Si no pasa el gate, no crees un escenario artificial. Produce únicamente el informe de factibilidad.

Validación:
- ejecuta solo pruebas nuevas si existe escenario;
- ejecuta regresión física relacionada;
- muestra todos los warnings;
- no conviertas advertencias en éxitos silenciosos;
- no uses los nRMSE de East2 u otros artículos como tolerancia.

Restricciones:
- sin commit;
- sin merge;
- sin push;
- sin despliegue;
- no modificar DigitalOcean;
- no modificar código productivo si el artículo no pasa el gate.

Informe obligatorio:
- Markdown en `references/informe-validacion-nist-medido-predicho-2003.md`;
- tabla de extracción con páginas/figuras;
- tabla medición vs predicción vs APP si es posible;
- lista de datos ausentes;
- supuestos explícitos;
- limitaciones;
- clasificación arquitectónica;
- veredicto final: reproducido, reproducido con supuestos, parcialmente reproducido o no reproducible.

Publica el informe final en una web temporal accesible para revisión humana y entrega la URL.
```
