# Propuesta — Panel por superficie en Vista 3D multi-superficie

**Estado:** diseño

## Objetivo

Que cada superficie declare su referencia de panel y que todos los cálculos
de Vista 3D (simplificado, bypass, MPPT, físico, strings y guardado) usen la
de esa superficie, sin eficiencias fijas.

## Alternativas consideradas

1. **Solo corregir η con el panel del proyecto.** Arregla el 16 % fijo pero
   no permite fachada y techo con paneles distintos.
2. **Calcular cada superficie como proyecto separado.** Rompe el origen
   único de energía en Financiero y la trazabilidad.
3. **Panel por superficie, por defecto el del proyecto.** Recomendada.

## Alternativa recomendada

1. En el editor de ⚙️ Superficies BIPV, cada superficie tiene un selector
   «Panel»: primera opción «Panel del proyecto (nombre)», que sigue al panel
   de 📐 Dimensionamiento; las demás son las del catálogo. Junto al selector
   se muestran Pmax, área del módulo y η.
2. La energía simplificada usa por superficie η = Pmax_stc / (área del
   módulo × 1000 W/m²). Se elimina el 16 % fijo: si el panel no permite
   calcular η, la superficie no entra al cálculo y se dice por qué.
3. Bypass, MPPT y modo físico usan el panel de cada superficie. El selector
   común de panel de las secciones 5 y 6 desaparece; la tabla de resultados
   muestra el panel de cada superficie.
4. Los strings estimados usan el área del módulo de la superficie. Si la
   superficie usa un panel distinto al del proyecto, el N serie de
   Dimensionamiento no se toma como respaldo: hay que configurarlo en la
   superficie.
5. Cambiar el panel de una superficie retira la energía publicada y los
   resultados de bypass, MPPT y físico que dependían de él. La POA y la
   sombra siguen vigentes, porque no dependen del panel.
6. El proyecto guardado conserva el panel de cada superficie; los proyectos
   guardados antes de este cambio cargan con el panel del proyecto.

## Fuera de alcance

- H2 (PR fijo 0,78) y H3 (Presupuesto multi-superficie): Specs aparte.
- Ganancia bifacial por panel: sigue la configuración bifacial actual.
- La física del bypass, del MPPT combinado y del modo físico.
