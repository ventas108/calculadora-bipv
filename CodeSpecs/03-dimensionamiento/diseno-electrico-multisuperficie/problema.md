# Spec A — Diseño eléctrico multi-superficie: inversores, MPPT y grupos de strings

**Estado:** implementación

## Alcance de la fase

App hermana Streamlit (`bipv_python/`): ⚙️ Superficies BIPV › 🔌 Inversores
por superficie y secciones 5 (bypass) y 6 (MPPT) de
`pages/9_🗺️_Vista_3D.py`, modo físico (`calculos/adaptador_multisuperficie.py`,
`calculos/transicion_multisuperficie.py`), validación
(`calculos/inversores_multisuperficie.py`) y persistencia
(`calculos/persistencia_multisuperficie.py`). Topologías string y central.
Microinversores y optimizadores quedan para la Spec B, que se apoya en la
estructura de grupos de esta. Evidencia verificada contra `main` `235d65dc`.

## Problema a resolver

Desde `05/panel-por-superficie` cada superficie puede llevar su propio panel,
pero el diseño eléctrico sigue sin validarse contra ese panel ni contra el
inversor:

1. **Inversor sin ficha.** En 🔌 Inversores por superficie el inversor se
   escribe a mano (ID, η, P AC); `ficha` queda `{}`. No hay Vdc máximo, ventana
   MPPT, corriente por tracker ni número de MPPT, y no se puede elegir del
   catálogo que ya usa 📐 Dimensionamiento (`cargar_catalogo_inversores`).
2. **Strings sin validar.** N serie y N paralelo solo se revisan como enteros
   ≥ 1 (`validar_inversores_y_asignaciones`). El modo físico llama a
   `evaluar_compatibilidad_string` con la ficha vacía, así que siempre queda
   «no evaluable». Además usa temperaturas fijas (−5 / 36,35 / 41,94 °C) en
   lugar de las del proyecto (`T_min_diseno`, `T_cel_realista`,
   `T_cel_extremo`), y el resultado no se muestra en ninguna parte.
3. **Un solo inversor por superficie.** Cada superficie tiene un solo
   `inversor_id`, `n_serie` y `n_paralelo`. Una fachada grande que necesita
   varios inversores o varios MPPT obliga a partirla a mano en superficies
   ficticias, con riesgo de sumar mal las áreas.
4. **MPPT invisible.** El inversor «compartido» se modela como una barra DC
   común. No se sabe a qué MPPT va cada superficie, ni si el inversor tiene
   suficientes MPPT, ni si un MPPT mezcla paneles distintos, que es un error de
   diseño.
5. **Relación DC/AC sin mostrar.** `evaluar_relacion_dc_ac` se calcula por
   superficie, cuando lo que importa es el total de cada inversor, y no
   aparece en pantalla.
6. **Dos fuentes de verdad para el MPPT.** La sección 6 toma el número de MPPT
   del inversor de Dimensionamiento (`inversor_dict_dim`) y tiene su propia
   asignación de superficie a MPPT, distinta de la de 🔌 Inversores por
   superficie.
7. **Área y módulos desconectados.** La energía simplificada usa el área de la
   superficie; el modo físico usa N serie × N paralelo módulos. Nada compara
   las dos cifras, y el grupo puede tener más módulos de los que caben.

## Ejemplo del impacto

Inversor típico (Vdc máx. 1000 V, MPPT 200–800 V, Isc máx. 20 A por MPPT),
5 °C mínima y 60 °C de celda, con las funciones de
`calculos/dimensionamiento.py` y el factor 1,25 sobre Isc:

| | ASP-ST1-T40 (fachada) | SPR-E20-327 (techo) |
|---|---|---|
| Voc en frío / Vmp en calor por módulo | 123,4 V / 76,7 V | 68,4 V / 49,5 V |
| N serie válido | 3 a 8 | 5 a 14 |
| Isc por string | 0,8 A | 6,46 A |
| Strings por MPPT de 20 A | 20 | 2 |

Hoy un N serie de 20 con SPR-E20-327 (Voc en frío ≈ 1.370 V) pasa sin aviso
y el modo físico publica su energía.

## Contexto

- Relacionadas: `05/panel-por-superficie` (panel por superficie),
  `05/publicacion-energia-multisuperficie` (origen único),
  `05/persistencia-multisuperficie`, `08-interfaz/panel-proyecto-bypass-mppt`.
- Funciones ya validadas que se reutilizan sin cambiar su física:
  `evaluar_compatibilidad_string`, `optimizar_n_serie`, `calcular_voc_string`,
  `calcular_vmp_string`, `evaluar_relacion_dc_ac` (`calculos/dimensionamiento.py`),
  `simular_bypass_horario`, `recalcular_etapa_inversor_bus`.
- Fuera de esta Spec (registrados): microinversores y optimizadores (Spec B),
  PR fijo 0,78 (H2) y Presupuesto sin superficies de Vista 3D (H3).
