# Propuesta — Diseño eléctrico multi-superficie: inversores, MPPT y grupos de strings

**Estado:** diseño

## Objetivo

Que cada superficie tenga un diseño eléctrico explícito y validado:

- panel → grupos de strings → inversor y MPPT → validación con las
  temperaturas del proyecto → energía;
- cada cifra se muestra con su fórmula y su fuente;
- ninguna energía física se publica con un diseño eléctricamente imposible.

Sirve igual para una casa (un grupo por superficie) que para una torre (varios
grupos e inversores en la misma fachada).

## Alternativas consideradas

1. **Solo llenar la ficha del inversor y validar un string por superficie.**
   Cierra las brechas 1, 2 y 5, pero no las 3, 4 y 6: los proyectos grandes
   siguen partiendo superficies a mano.
2. **Superficies «eléctricas» separadas de las geométricas.** Duplica la
   geometría, la POA y la sombra, y rompe la vigencia ya validada.
3. **Grupos de strings dentro de cada superficie.** Recomendada. La
   superficie conserva geometría, POA, sombra y panel; los grupos llevan la
   parte eléctrica. El motor físico ya calcula la potencia DC con
   N serie × N paralelo, así que cada grupo entra como una unidad física más,
   sin tocar sus fórmulas.

## Alternativa recomendada

1. **Inversor con ficha.** Por defecto «Inversor del proyecto» (el de 📐
   Dimensionamiento); también uno del catálogo o uno manual marcado «sin
   ficha: no validado». El catálogo no trae eficiencia, así que η se escribe
   siempre y se muestra su origen.
2. **Grupos de strings.** Cada superficie tiene uno o más grupos
   `{topología, inversor, MPPT, N serie, N paralelo}`. La topología de esta
   Spec es `string`; la Spec B agrega `microinversor` y `optimizador` sobre la
   misma estructura. Un proyecto antiguo se migra a un grupo por superficie
   sin pérdida.
3. **Validación explícita por grupo, MPPT e inversor.** Mismas funciones y
   temperaturas que 📐 Dimensionamiento:
   - por grupo: Voc en frío, Vmp en calor y en frío contra la ventana
     MPPT; junto al N serie se muestra el rango válido;
   - por MPPT: corriente total, strings por entrada y un solo panel por MPPT;
   - por inversor: MPPT usados, relación DC/AC y recorte;
   - por superficie: módulos que caben en el área.
4. **Tabla de diseño eléctrico** con cada valor, su límite, la fórmula, la
   fuente y un semáforo 🟢/🟡/🔴.
5. **Energía coherente con los módulos.** Con grupos definidos, la energía
   simplificada usa el área instalada (módulos × área del módulo), la misma
   base que el modo físico, y lo indica. El bypass se calcula por grupo, con
   los strings del grupo.
6. **Reglas hacia Financiero:**
   - 🔴 en cualquier grupo, MPPT o inversor → el modo físico no publica;
   - el simplificado y el bypass publican con «diseño eléctrico: 🔴 con
     fallas» o «🟡 no verificado» visible en el banner y guardado con la
     publicación;
   - 🟢 → sin aviso.
7. **Sección 6 unificada.** Usa los grupos, su MPPT y el inversor asignado;
   sus selectores propios desaparecen.
8. **Invalidación y guardado.** Cambiar grupos o inversores retira la energía
   publicada y los resultados de bypass, MPPT y físico; la POA y la sombra se
   conservan. Guardar y cargar conserva inversores con ficha y grupos.

## Orden de implementación (cada fase validada antes de la siguiente)

- **Fase A1 — Modelo y validación, sin cambiar la energía:** inversor con
  ficha, grupos con migración, validación pura, tabla de diseño eléctrico.
  Un PR, prueba en producción.
- **Fase A2 — Cálculos:** modo físico por grupos con las temperaturas del
  proyecto, área instalada, bypass por grupo, reglas hacia Financiero,
  invalidación y persistencia. Un PR, prueba en producción.
- **Fase A3 — Sección 6 unificada**, manual y Asistente. Un PR, prueba en
  producción y cierre de la Spec.

## Fuera de alcance

- Microinversores y optimizadores (Spec B): esta Spec deja el campo
  `topología` y la clase de inversor preparados, sin lógica.
- Cajas combinadoras, cableado, protecciones y caída de tensión.
- Pérdida de desajuste entre orientaciones dentro de un MPPT en la energía
  oficial: sigue siendo informativa en la sección 6, como hoy.
- H2 (PR fijo 0,78) y H3 (Presupuesto multi-superficie).
