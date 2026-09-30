# Contratos entre módulos

Cada módulo publica su contrato completo (entradas, salidas, unidades, tipos de datos,
errores posibles) en su propio `diseno.md`. Este archivo resume únicamente los
contratos **vigentes** (diseño aprobado) que otros módulos consumen.

## Formato de referencia

```text
Entrada:
- variable_1

Salida:
- variable_2

Unidades:
- ...
```

## Contratos publicados

### 01-datos-proyecto
_(pendiente — ver [../01-datos-proyecto/diseno.md](../01-datos-proyecto/diseno.md))_

### 02-recurso-solar
Ver [../02-recurso-solar/diseno.md](../02-recurso-solar/diseno.md). Versión
de PVGIS (Spec [pvgis-5-3](../02-recurso-solar/pvgis-5-3/diseno.md)):

- `pvgis_version` (`"5.2"` o `"5.3"`) se guarda con el proyecto. Proyecto nuevo
  → 5.3; proyecto guardado sin la clave → 5.2 (`cargar_proyecto`).
- `tmy_df` es el TMY de esa versión; `tmy_df.attrs["pvgis"]` trae versión, base
  de radiación, periodo y año escogido para cada mes (puede faltar si el TMY
  viene de una caché anterior).
- Cambiar la versión invalida `tmy_df`, la POA y todos sus derivados, igual
  que cambiar las coordenadas (`_solar_pvgis_guardada`).

### 03-dimensionamiento

Entrada:
- Catálogo eléctrico, temperaturas de diseño, área y configuración de strings.

Salida:
- Diseño confirmado (`N_serie`, `N_strings_tracker`), compatibilidad y vigencia.

Regla de consumo:
- Los módulos downstream usan exclusivamente
	`diseno_electrico_confirmado(session_state)`. Un diseño no vigente no puede
	producir resultados persistibles.
- Excepción declarada y aprobada (2026-09-25, Spec
	`03-dimensionamiento/diseno-electrico-multisuperficie`): en multi-superficie,
	el diseño eléctrico es por superficie y lo valida
	`calculos/diseno_electrico_multisup.validar_diseno_electrico`. No es un
	segundo modelo: usa las mismas funciones (`evaluar_compatibilidad_string`,
	`calcular_voc_string`, `calcular_vmp_string`, `evaluar_relacion_dc_ac`) y las
	mismas temperaturas de diseño (`T_min_diseno`, `T_cel_realista`,
	`T_cel_extremo`). El inversor del proyecto de este módulo es la ficha por
	defecto de cada inversor multi-superficie.
- Corriente por grupo (26-sep-2026): la compatibilidad de cada grupo de strings
	usa solo sus strings en paralelo (`n_paralelo`); la corriente del MPPT completo
	la suma su propio chequeo de la tabla de MPPT. Ningún chequeo cuenta strings de
	otro grupo con el Isc de un panel ajeno.
- Potencia AC nominal (26-sep-2026, Spec `03-dimensionamiento/catalogo-inversores-potencia-ac`):
	`P_ac_nom_W` sale solo de la ficha del catálogo (`calculos/potencia_ac_inversor.py`);
	no se estima con `P_dc_max_W`. Sin el dato, la relación DC/AC es «no evaluable»
	y la página explica dónde completarlo.
- Proyecto completo (29-sep-2026, Spec `03-dimensionamiento/proyecto-completo`):
	`calculos/dimensionamiento.proyecto_completo` cuenta strings completos (los
	declarados en «N total de cadenas» o ⌊área útil ÷ (N_serie × área del
	módulo)⌋), inversores = ⌈strings ÷ (MPPT × strings por MPPT)⌉ y reparto
	parejo. Publica `N_inv_total`, `N_paneles_granja`, `P_dc_total_kWp` y
	`reparto_strings_inversores`; nunca más módulos de los que caben sin
	cadenas declaradas. La relación DC/AC se evalúa con el sistema real.
- 🌾 Granja FV, fase 1 (30-sep-2026, Spec `03-dimensionamiento/granja-fv-campo`):
	`granja_fv` (geometría del campo) se guarda con el proyecto;
	`calculos/granja_fv.calcular_campo` es el único cálculo del campo y lo
	usan 🌾 Granja FV y la rama de granja de 🗺️ Vista 3D. Módulos a ubicar:
	`N_paneles_final` (Producción) o `N_paneles_granja`. Inclinación y azimut
	vienen de 🏠 Proyecto. En esta fase no escribe `bifacial_cfg` ni cambia
	la energía: `coherencia_campo` avisa si el GCR o la altura no coinciden.
- 🌾 Granja FV, fase 2 (30-sep-2026, Spec `05-perdidas-y-temperatura/sombra-entre-filas`):
	el botón «⚡ Usar la geometría del campo en la energía»
	(`granja_fv.aplicar_geometria_a_energia`) escribe `filas_energia`
	(`gcr`, `altura_m`, `ancho_colector_m`) y, con el modelo bifacial activo,
	los mismos tres datos en `bifacial_cfg`. ☀️ Recurso Solar pasa
	`filas=filas_energia` a `solar.calcular_poa` solo con paneles monofaciales
	(con bifacial la cara frontal de `infinite_sheds` ya incluye la sombra) y
	publica `poa_geometria_filas`; `coherencia_campo` la compara (`poa_filas`).
	`bifacial_cfg` suma `ancho_colector_m` (antes 2,0 fijo), `sombra_trasera_pct`
	y `mismatch_trasero_pct` (0 = sin cambio) que multiplican el aporte trasero.
- 🌾 Granja FV, fase 3 — agrivoltaica (30-sep-2026, Spec `03-dimensionamiento/granja-agrivoltaica`):
	`calculos/agrivoltaica.luz_en_el_suelo` usa el resultado de
	`granja_fv.calcular_campo` y el TMY (`G_h`, `Gd_h`); guarda
	`granja_luz_suelo` con la firma de la geometría (se oculta si cambia).
	`paso_maquinaria` lee `granja_altura_maquinaria_m` y
	`granja_ancho_maquinaria_m`. No cambia la energía.
- 🌾 Granja FV, fase 4 — seguidor de un eje (30-sep-2026, Spec `05-perdidas-y-temperatura/seguidor-un-eje`):
	`calculos/seguidor.comparar_seguidor_fijo` compara la luz frontal del
	campo fijo (`granja_fv.calcular_campo`) con un seguidor Norte–Sur con y
	sin backtracking; lee `granja_seg_*` y guarda `granja_seguidor` con su
	firma. Solo compara: 📊 Producción sigue con la estructura fija;
	`energia_estimada` usa `E_ac_anual_kWh` como estimación de primer orden.
- NOCT y γ del Motor Óptico frente a la ficha (30-sep-2026, Spec `05-perdidas-y-temperatura/motor-optico-ficha-termica`):
	`motor_optico_noct` sigue siendo la fuente de la temperatura de celda en
	Producción; `calculos/motor_optico_ficha.diferencias_ficha` lo compara con
	la ficha (`NOCT`, `Tk_gamma`/`gamma_mp`/`beta_mp`) y Motor Óptico y
	Producción avisan en 🟠; «Usar los de la ficha» los repone.
- Recorte por inversor en Vista 3D (29-sep-2026, Spec `05-perdidas-y-temperatura/recorte-inversor-multisuperficie`):
	`cadena_superficie` devuelve `perfil_ac` (forma horaria de la AC, suma 1);
	`cadena_superficies_estado`, después del cruce, aplica
	`recorte_inversores_multisup.factores_recorte`: por inversor con
	`P_ac_nom_W`, suma horaria de sus grupos (módulos donde están), recorte a
	la potencia AC y reparto por aporte horario; `pr` × `f_recorte`,
	`recorte_kWh` y `recorte_inversores` por superficie. `firma_cadena` incluye
	potencias AC y grupos solo si hay inversores con potencia AC y grupos.
- Cantidad de inversores (29-sep-2026, Spec `03-dimensionamiento/inversores-del-proyecto`):
	`N_inversores_proyecto` (0 = automática) y `N_inversores_proyecto_ref`
	(modelo para el que se fijó) son claves de datos. `resolver_inversores`
	usa la cantidad fijada entre el mínimo ⌈strings ÷ capacidad⌉ y un string
	por inversor; `N_inv_total` publica la cantidad efectiva. 📊 Producción
	(`escalar_p_ac_nom_por_inversores`) redondea hacia arriba igual que
	Dimensionamiento y usa la fijada vía `inversores_fijados_vigentes` (solo
	si es del mismo modelo). Unifilar, RETIE y Presupuesto toman `N_inv_total`.
- Temperaturas de diseño (29-sep-2026, Spec `03-dimensionamiento/temperaturas-diseno`):
	`T_min_diseno`, `T_cel_realista` y `T_cel_extremo` son claves de datos (se
	guardan con el proyecto); sus campos usan `campo_persistente`. Se recalculan
	desde el TMY solo si cambia `dim_temps_tmy_firma` (T2m del TMY + NOCT), si
	falta alguna o si las tres están en 0. «Guardar configuración» de
	🏠 Proyecto no las pisa si hay firma; el cambio de ciudad borra la firma.

### 04-produccion-energia

Entrada:
- Recurso solar, diseño eléctrico confirmado y, cuando aplique, POA sin térmico
	del Motor Óptico.

Salida:
- Energía AC/DC, PR, pérdidas, resultados persistidos y firma
	`produccion_run_signature_v1`.

Regla de consumo:
- Producción valida la vigencia reconstruyendo la firma en vivo desde su propia
	configuración visible. Consumidores que no tienen esos insumos en sesión
	(Finanzas/Presupuesto, ver `06-analisis-financiero`) no reconstruyen la firma:
	verifican la integridad del payload canónico persistido junto a ella. Sin esa
	verificación exitosa, ningún agregado de Producción se restaura.

### 05-perdidas-y-temperatura

Entrada:
- TMY/POA bruta y parámetros ópticos/térmicos.

Salida:
- `poa_sin_termico_df`, `poa_efectiva_df`, `k_BIPV`, resumen óptico y estado
	de vigencia.

Regla de consumo:
- Con Motor Óptico activo, Producción y bypass consumen solo
	`poa_sin_termico_df`; el término térmico se calcula una única vez dentro del
	SDM. Recalcular la cascada invalida resultados dependientes de su POA.
- Pérdidas de módulo (29-sep-2026, Spec `05-perdidas-y-temperatura/calidad-y-mismatch`):
	`pct_calidad_modulo` («Module quality loss», −2 a 5 %, por defecto 0) y
	`pct_mismatch_fab` («Mismatch loss, modules and strings», 0 a 4 %). Los dos
	motores de Producción las aplican en cadena sobre Pmax
	(`(1 − calidad)(1 − mismatch)`); consumidores sin motor propio (cadena
	multi-superficie, comparadores, 🤖 Análisis IA) usan
	`calculos.mismatch.pct_perdida_modulos`. La calidad entra en la firma de
	Producción solo si se aplica.
- Equivalencia térmica con PVsyst (29-sep-2026): para igualar un informe con
	Uc/Uv, k_BIPV = α(1 − η)/(Uc + Uv·v) ÷ ((NOCT − 20)/800); la tabla de
	presets por tipo de montaje del Asistente es solo orientativa (ver sección 83
	de la base de conocimiento).
- Cascada bifacial (29-sep-2026, Spec `05-perdidas-y-temperatura/motor-optico-bifacial`):
	con POA bifacial (`poa_front`, `poa_rear`), `cascada_optica` aplica el IAM a
	`poa_front` y solo la IAM difusa al aporte trasero (`poa_global − poa_front`),
	sin suciedad; se cumple POA bruta − IAM − suciedad = `poa_post_soil`. La POA
	publicada (`motor_optico.poa_publicable`) mantiene `poa_global − poa_front` =
	aporte trasero óptico. Los factores promedio del resumen son ponderados por
	energía (su producto es `factor_global`). Monofacial sin cambios.
- 🔀 Mismatch → 📊 Producción (29-sep-2026, Spec
	`05-perdidas-y-temperatura/mismatch-horizonte-coherente`, `mismatch_version = 2`):
	- `factor_global_mismatch` (orientación + suciedad) y
		`factor_mismatch_sin_soiling` (orientación) ya **no** incluyen el horizonte.
	- El horizonte entra solo por `calculos.mismatch.factores_mismatch_produccion`:
		factor hora a hora = 1 − luz directa frontal ÷ POA en las horas bloqueadas,
		aplicado a la POA base con `aplicar_factor_horario` antes de la firma de
		vigencia y de la simulación (en bifacial baja `poa_front`, el aporte trasero
		no cambia). Sin Motor Óptico y en bifacial, la suciedad solo sobre la cara
		frontal que queda tras el horizonte.
	- Bypass: FS 3D = 0 en las horas de horizonte (`excluir_horas_horizonte`); cada
		sombra se resta una sola vez.
	- Estado sin `mismatch_version` (versión anterior): se usa su escalar tal cual
		(ya trae el horizonte), sin factor horario, con aviso de recalcular.
	- Con Motor Óptico activo la suciedad es la del Motor Óptico; el control de
		🔀 Mismatch queda deshabilitado.
	- Valores por defecto: `calculos.mismatch.DEFAULTS_MISMATCH`; Producción no los
		aplica si la página no se abrió (aplica 0 % y avisa).
	- Producción guarda `factor_mismatch_aplicado` (el factor escalar de su
		corrida), que muestra 📄 Reporte PDF.
	- Mismatch por orientación (29-sep-2026, Spec
		`05-perdidas-y-temperatura/mismatch-orientacion-horario`):
		`calcular_mismatch_orientacion` calcula la pérdida hora a hora con diodos de
		bypass (`perdida_string_bypass`) y la POA de cada orientación con
		`albedo_suelo` y `bifacial_cfg` del proyecto; publica `factor_horario`,
		`factor_mismatch_pct` (ponderado por energía) y `firma`. Con resultado
		horario, `mismatch_or_horario = True`: el escalar no lleva la orientación
		y `factores_mismatch_produccion` la aplica hora a hora junto con el
		horizonte. Un resultado sin `factor_horario` va en el escalar, como antes.

#### Energía multi-superficie (Vista 3D)

Entrada:
- Por superficie: geometría, POA firmada (`05/vigencia-poa-superficie`), sombra
	3D con su estado, panel propio (`05/panel-por-superficie`) y diseño eléctrico
	(grupos de strings con inversor y MPPT,
	`03-dimensionamiento/diseno-electrico-multisuperficie`).

Salida:
- Publicación única: `E_ac_anual_kWh_multisup`, `multisup_desglose`,
	`area_total_multisup`, `poa_df_multisup`, `multisup_activo` y
	`multisup_origen` (`simplificado`, `bypass_csv` o `fisico`) y
	`multisup_estado_electrico` (`{estado, n_bloqueos, n_avisos, texto}`, fase
	A2) y `multisup_sistema` (potencia, módulos por panel, reparto mensual y
	`completo`; Spec `06-analisis-financiero/sistema-multisuperficie`); en origen físico, además `_multisup_proyecto_fisico` y
	`multisup_perdida_bus_kWh`.

Reglas de consumo:
- Toda publicación pasa por `publicar_energia_multisuperficie`. Reemplazar un
	origen distinto pide confirmación; nunca «gana el último».
- Solo se publica con POA vigente en todas las superficies activas.
- Modelos declarados (regla de `mapa-dependencias.md`): el simplificado es
	POA × área × η del panel de cada superficie × PR; η = Pmax / (área del módulo
	× 1000), nunca un valor fijo. Con grupos de strings el área es la instalada
	(módulos × área del módulo, sin pasar del área de la superficie); sin grupos,
	el área de la superficie como estimación (`superficies_para_energia`). El
	bypass aplica a esa energía la pérdida del modelo de bypass de cada grupo,
	ponderada por módulos. El físico es SDM + bypass + etapa de inversor, con una
	unidad por grupo y las temperaturas de diseño del proyecto. Los tres se
	muestran con su origen.
- Strings que cruzan a otra superficie (29-sep-2026, Spec
	`05-perdidas-y-temperatura/string-cruza-superficies`): un grupo puede
	declarar `cruce = {uid, modulos}` (k de sus N serie módulos en otra
	superficie). Los módulos se cuentan donde están
	(`cruce_superficies.modulos_fisicos_por_superficie`, usado por
	`superficies_para_energia`); `cadena_superficies_estado` multiplica el PR de
	cada superficie por `f_cruce` = 1 − Σ L × módulos del string en ella ÷
	módulos de la superficie, con L la pérdida hora a hora con diodos de bypass
	(`perdida_string_bypass`). El simplificado y el bypass la usan; el físico no
	se prepara con cruces (error explicado). `validar_diseno_electrico` agrega
	🔴/🟡 al grupo. `firma_cadena` incluye los cruces solo si existen.
- Corriente DC de diseño con panel bifacial (29-sep-2026, Spec
	`07-informes/unifilar-retie-bifacial-cruce`): `calculos.corriente_bifacial`
	(`factor_isc_bifacial(φ) = 1 + 0,135 φ`, BNPI). φ: modelo bifacial activo →
	bifacialidad × vista trasera de la superficie (`config_bifacial_superficie`);
	modelo apagado → bifacialidad de la ficha del panel (lado seguro, aviso);
	monofacial → 0. Lo usan `validar_diseno_electrico(..., bifacial=)` (límite de
	corriente del MPPT y caja combinadora), `topologia_electrica` (`isc_stc_A` en
	BNPI, `isc_frontal_A`, `factor_bifacial`, `cruce_texto`, superficies con
	`modulos_fisicos`), `calcular_perdida_ohmica(..., factor_bifacial=)`
	(ampacidad; la resistencia no cambia) y `construir_config_retie(...,
	factor_bifacial=)` (`isc_bnpi_a`, Isc de diseño y fusible gPV). Voc y Vmp no
	cambian. La energía no usa este factor (la luz trasera ya está en la POA).
- Cambiar el panel de una superficie (o el del proyecto, para las que lo siguen)
	retira la publicación y los resultados de bypass, MPPT y físico; la POA y la
	sombra se conservan. Agregar, eliminar, desactivar o renombrar superficies no
	cuenta como cambio de panel.
- Diseño eléctrico (fase A2): con 🔴 el modo físico no publica
	(`aplicar_proyecto_a_session_state` lanza `ValueError`); el simplificado y
	el bypass publican con `multisup_estado_electrico`, y Vista 3D, Financiero,
	Baterías y CO₂ lo muestran con `aviso_estado_electrico`. Con 🔴,
	Financiero no calcula (`problemas_financieros`). Cambiar grupos,
	inversor o ficha de una superficie existente retira la publicación y los
	resultados de bypass, MPPT y físico (`invalidar_por_cambio_electrico`).
- Hasta la fase A3, la sección 6 deja fuera, con aviso, las superficies con
	varios grupos.
- Financiero, Baterías y CO₂ (Spec `06-analisis-financiero/sistema-multisuperficie`):
	con `multisup_activo` no exigen `produccion_ok` y toman energía, kWp, módulos
	y reparto mensual solo de la publicación (`estado_sistema_publicado`); nunca
	los mezclan con `P_stc_kW_sistema`/`N_paneles_final` de superficie única.
	Sistema incompleto, publicación sin `multisup_sistema` o diseño eléctrico 🔴
	⇒ 🔴 y Financiero no calcula. Si la energía se retiró por un cambio,
	Financiero, Baterías y CO₂ lo dicen (`aviso_retiro_para_consumidores`).
- La sección «Strings de distinta orientación en un mismo MPPT» es informativa y
	no cambia la energía publicada.

#### Persistencia física multi-superficie

Entrada:
- `session_state` con superficies (geometría, panel propio y asignaciones
	eléctricas), inversores con su ficha, TMY y snapshot físico adoptado.

Salida:
- Payload canónico firmado con `inputs`, `results`, `validity` y
	`provider_metadata`, persistido atómicamente por usuario.

Reglas de consumo:
- Cargar valida schema, firma global, TMY, geometría, sombra, POA y configuración
	eléctrica antes de publicar estado físico.
- La restauración es todo-o-nada; un fallo no publica `multisup_*`, el snapshot
	físico ni resultados downstream.
- Finanzas, CO₂, Baterías, Mismatch, Reporte, Diagrama Unifilar y Comparador de
	Inversores solo consumen multi-superficie cuando `multisup_activo=True`; si no,
	conservan el fallback simplificado/bypass/base.
- Cambiar de proyecto invalida el estado físico anterior y cualquier payload
	pendiente de restauración.

#### Cadena de pérdidas multi-superficie (27-sep-2026)

- La energía que Vista 3D publica (simplificado, bypass y físico) sale de
	`calculos/cadena_perdidas_multisup`: `motor_optico.cascada_optica` con la
	POA de cada superficie (sin transparencia: η ya es de módulo) y
	`produccion.simular_produccion_anual` (SDM) con esa POA. No es un segundo
	modelo: son las mismas funciones de 🔆 Motor Óptico y 📊 Producción.
- La publicación guarda `multisup_cadena_perdidas` (versión y huella de
	parámetros); Vista 3D, Financiero, Baterías y CO₂ avisan si la energía se
	publicó con el 0,78 o si los parámetros cambiaron después.

### 06-analisis-financiero

Entrada:
- Resultados persistidos de Producción (`04-produccion-energia`): agregados
	(`E_ac_anual_kWh`, `P_stc_kW_sistema`, etc.), `produccion_run_signature_v1` y
	su payload canónico (`payload_firma`).

Salida:
- Agregados restaurados en `session_state` de Finanzas/Presupuesto, solo
	cuando el payload persistido verifica contra la firma persistida.

Regla de consumo:
- Finanzas y Presupuesto nunca reconstruyen la firma en vivo (no cargan
	panel/inversor/TMY/POA). Restauran únicamente si
	`firma_desde_payload(payload_persistido) == firma_persistida`; payload
	ausente (legacy) o alterado nunca restaura.
- Con `multisup_activo`, la energía, los kWp y los módulos salen de
	`multisup_sistema` (Spec `06-analisis-financiero/sistema-multisuperficie`);
	con diseño eléctrico 🔴 no se calculan TIR, VPN, payback ni LCOE.
- Precios (26-sep-2026): Financiero y Presupuesto leen el precio vigente de los
	catálogos de paneles, inversores y baterías (`calculos/costos_catalogo.py`,
	`sistema_multisuperficie.costo_actual_panel`). En multi-superficie el CAPEX de
	inversores es la suma de un precio por inversor del diseño. Un precio escrito
	a mano se respeta mientras la fuente no cambie (`campos_editor.sincronizar_con_fuente`).
- Vigencia del resultado (26-sep-2026): el resultado guardado de Financiero solo
	se muestra si los datos del cálculo no cambiaron
	(`calculos/vigencia_financiero.datos_cambiados`); si cambiaron, se retira y se
	pide calcular de nuevo.
- Excedentes (27-sep-2026, Spec `06-analisis-financiero/indicadores-excedentes`):
	la única fuente del reparto autoconsumo/excedentes es `frac_exportada` con
	`tarifa_excedentes_cop`. El flujo de caja (`calculos/financiero.py`) y los
	indicadores de la página (`calculos/indicadores_excedentes.py`: ahorro del año 1
	y escenario sin batería) usan ese mismo reparto.

### 07-informes

Entrada:
- Banderas `_ok` (`produccion_ok`, `financiero_ok`, `impacto_co2_ok`, etc.) y
	energía anual con prioridad `multisuperficie > bypass > base`.

Salida:
- Reporte HTML/PDF descargable y, opcionalmente, un eslabón en el Ledger de
	Auditoría con hash de insumos+resultados al momento de generación.

Regla de consumo:
- Informes no restaura resultados persistidos por su cuenta; toda vigencia se
	garantiza aguas arriba, en `04-produccion-energia` y `06-analisis-financiero`.

#### Diagrama Unifilar y Ficha RETIE con el sistema multi-superficie (28-sep-2026)

- Con `multisup_activo` y grupos de strings, ⚡ Diagrama Unifilar y 📋 Ficha
	RETIE leen UNA topología de `calculos/topologia_electrica`
	(`topologia_desde_estado`): inversor → MPPT → grupos, caja combinadora del
	diagnóstico de `diseno_electrico_multisup`, optimizadores y batería.
- Las comprobaciones de string, MPPT e inversor de la ficha son las del
	diagnóstico eléctrico (verde → OK, amarillo → PENDIENTE, rojo → ERROR); no
	se recalculan con otra fórmula.
- `sistema_optimizadores` y `bateria_inversor_id` son datos del proyecto
	compartidos por las dos páginas. Los optimizadores no cambian la energía.
- Sin multi-superficie las dos páginas conservan el modo de una superficie
	(📐 Dimensionamiento o datos manuales).

### 08-interfaz

Entrada:
- `session_state` ya poblado por módulos previos; sesión autenticada.

Salida:
- Bloqueo de traducción del navegador y banner de proyecto activo.

Regla de consumo:
- La infraestructura compartida de Interfaz no restaura ni invalida datos por su
	cuenta; toda vigencia se garantiza en `03`–`06` antes de que estas claves lleguen
	a `session_state`. Son excepción los comandos explícitos de adopción definidos en
	el contrato transversal de comparadores: mutan el proyecto y ejecutan la
	invalidación central correspondiente como una sola operación.
- Cualquier texto de usuario interpolado en HTML debe quedar escapado.
- Widgets con clave (Streamlit 1.36): no reciben `value=`; su estado se sincroniza
	con los datos mediante `calculos/campos_editor.py` (`sincronizar_campo`,
	`sincronizar_con_fuente`). Un selector cuyas opciones cambian (p. ej. la lista
	de inversores) usa `clave_con_opciones`, para que el widget se reconstruya desde
	los datos y no pierda ni cambie el valor de otros elementos (26-sep-2026).
- Un dato que el usuario escribe y que debe guardarse con el proyecto vive en
	una clave de datos (sin `_`); el campo usa una clave temporal `_w_<clave>`
	(`calculos/campos_persistentes.campo_persistente`). Un campo con `key` de
	widget como único almacén pierde su valor al abrir otra página (27-sep-2026).

### Contrato transversal — comparadores Streamlit

Este contrato pertenece exclusivamente a la app hermana Streamlit. Los comparadores
son superficies de decisión de `08-interfaz` que consumen contratos de `02`–`06`; no
son motores físicos alternativos ni autorizan duplicar fórmulas en la app React.

#### Comparador de inversores

Entrada:
- Diseño eléctrico confirmado, panel vigente y serie horaria de Producción previa al
  límite AC del inversor actualmente seleccionado (`P_ac_sin_recorte_kW`).

Salida:
- Compatibilidad eléctrica, energía con el límite propio de cada candidato, clipping
  e indicadores económicos comparables.

Invariantes:
- Cada candidato aplica su propio límite a la serie previa al recorte. La serie ya
	recortada nunca se usa para reconstruir potencia perdida.
- Un resultado legacy sin la serie previa al recorte bloquea la comparación y exige
	volver a ejecutar Producción.
- Como regla física, cambiar de inversor no cambia la POA. La adopción conserva como
  conjunto atómico el estado del Motor Óptico, incluidas `poa_efectiva_df` y
  `poa_sin_termico_df`; Producción, bypass, pérdida óhmica, Financiero, CO₂ y demás
  resultados dependientes del inversor o `N_serie` sí se invalidan.

#### Comparador de paneles

Entrada:
- Recurso solar vigente, diseño base e inversor configurado; cada candidato se evalúa
  con el motor común de simulación y con la ficha exacta del catálogo unido.

Salida:
- Energía AC, PR y compatibilidad eléctrica en tres estados: `✅` compatible y
  adoptable, `❌` incompatible, `—` no evaluable y no adoptable con motivo explícito.

Invariantes:
- Adoptar usa la misma ficha completa que produjo la fila comparada; nunca vuelve a
  resolverla solo por nombre contra otro catálogo.
- Un resultado de sesión legacy sin ficha exacta o motivo eléctrico se descarta y se
  vuelve a calcular; nunca se reconstruye con el estado vigente.
- Adoptar un panel conserva la POA solar base del sitio, pero invalida la POA
  efectiva/óptica dependiente del panel, Producción, Financiero, CO₂ y sus derivados.

#### Comparador de orientación

Entrada:
- TMY vigente, geometría actual y hardware confirmado. La malla debe incluir la
  orientación actual como referencia.

Salida:
- Energía AC y PR por combinación de tilt/azimuth. No publica compatibilidad eléctrica
  porque la orientación no cambia panel, string ni inversor.

Invariantes:
- Adoptar recalcula primero la POA con el TMY y la geometría elegidos; solo después
  actualiza la geometría oficial e invalida Producción, Financiero, CO₂ y derivados.
- En proyectos multi-superficie, las geometrías y POA por superficie pertenecen al
  flujo Multi-Superficie; este comparador no las reconfigura implícitamente.

#### Asistentes y autoridad sobre resultados

- El Asistente general consulta el manual y un resumen del estado de flujo; no recibe
	las tablas de comparación ni debe inventar una recomendación sobre candidatos.
- Cada Analista local recibe únicamente la tabla actual de su comparador y no conserva
	memoria de tablas anteriores ni de otros comparadores.
- Ningún asistente o analista modifica el proyecto. Solo los controles explícitos de
	adopción aplican cambios y deben cumplir las invalidaciones anteriores.

#### Desviaciones activas que bloquean declarar cumplimiento total

- **Vigencia de tablas y análisis IA:** los DataFrames y textos de los tres comparadores
	todavía no tienen una firma común de entradas. No deben tratarse como resultados
	persistidos vigentes después de cambiar sus insumos; deben recalcularse.
- **Validación operativa multi-superficie:** la prueba manual en producción con dos
	superficies (fachada y techo) se hizo el 24 y 25-sep-2026: POA vigente, origen único
	con confirmación, puntos 3D, estado de sombra, panel y strings, mapa de calor y panel
	por superficie. Siguen abiertos:
	- la corrida real del modo físico con escena completa (Torre 5, Spec
		`05/sombra-cara-trasera`);
	- la fase A3 del diseño eléctrico multi-superficie (sección 6 unificada). La
		fase A2 se probó en producción con los casos D1–D9 (25 y 26-sep-2026); los
		hallazgos de D8 y D9 se corrigieron en los PR #60 y #61.
- **PR de la energía multi-superficie (resuelto el 27-sep-2026, antes H2):**
	Vista 3D ya no usa el 0,78: cada superficie pasa por la cadena de pérdidas
	(Spec `05/cadena-perdidas-multisuperficie`): óptica de 🔆 Motor Óptico por
	superficie y el motor SDM de 📊 Producción con el `k_bipv` de su montaje.
- **Presupuesto sin superficies de Vista 3D:** 💼 Presupuesto cuenta módulos e
	inversores con `N_paneles_final` de 📐 Dimensionamiento, no con los paneles, grupos
	e inversores de cada superficie. Registrado como H3, sin Spec todavía.
	Desde el 26-sep-2026 ya usa el precio vigente del inversor y de la batería, y
	en modo multi-superficie muestra un aviso 🟡 de la diferencia.
- **Integridad externa del archivo:** la firma actual SHA-256 detecta corrupción y
	cambios sin recalcular, pero no protege contra un actor con acceso de escritura al
	JSON. HMAC queda fuera de esta versión y requiere una decisión separada.

### 09-despliegue
_(pendiente — ver [../09-despliegue/diseno.md](../09-despliegue/diseno.md))_
