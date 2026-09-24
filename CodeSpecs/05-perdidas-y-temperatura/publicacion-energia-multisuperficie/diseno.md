# Diseño — Publicación única de la energía multi-superficie

**Estado:** validación

## Entradas

- `origen`: `"simplificado" | "bypass_csv" | "fisico"`.
- `e_ac_total` (kWh/año), `desglose` (lista por superficie: nombre, tipo,
  área, `e_ac_kWh`, `poa_kWh_m2`), `poa_ponderada` (DataFrame 8760 h),
  `area_total` (m²), `proyecto_fisico` (solo si `origen == "fisico"`).
- Confirmación del usuario cuando el origen vigente es distinto.

## Salidas

- Claves escritas juntas: `E_ac_anual_kWh_multisup`, `multisup_desglose`,
  `poa_df_multisup`, `area_total_multisup`, `multisup_activo=True`,
  `multisup_origen`, y solo para `fisico`: `_multisup_proyecto_fisico` y
  `multisup_perdida_bus_kWh`.
- Invariantes: `sum(área) == area_total` en los tres orígenes. Para
  `simplificado` y `bypass_csv`, `sum(d["e_ac_kWh"]) == e_ac_total`
  (tolerancia 0,1 kWh). Para `fisico` el total es la suma de los buses de
  inversor (`recalcular_agregados_proyecto`), que incluye el recorte de
  inversores compartidos; la diferencia con la suma del desglose se publica
  en la clave `multisup_perdida_bus_kWh` y no se trata como error.

## Tipos de datos

- `multisup_origen`: `str` del conjunto cerrado; cualquier otro valor →
  `ValueError`.
- Desglose: `list[dict]` con las mismas claves que produce hoy
  `aplicar_proyecto_a_session_state`.

## Errores posibles

- En `simplificado` o `bypass_csv`, desglose que no suma el total →
  `ValueError`, sin escribir nada (publicación atómica).
- `origen="fisico"` sin `proyecto_fisico` → `ValueError`.
- Sesiones antiguas sin `multisup_origen` con energía activa → se muestran
  como «origen desconocido» y se pide volver a publicar antes de guardar.

## Dependencias

- Módulos previos: la Spec `vigencia-poa-superficie`,
  `05/transicion-multisuperficie`, `05/persistencia-multisuperficie`.
- Módulos dependientes: `06-analisis-financiero`, `07-informes`, Baterías,
  CO₂, Diagrama Unifilar (consumen las mismas claves; no cambian su lectura).
- Capas: cálculo (`calculos/adaptador_multisuperficie.py` o módulo nuevo),
  estado (`invalidacion.py`, `proyectos_manager.py`), interfaz (Vista 3D).

## Criterios de aceptación

- Los tres botones publican solo a través de la función central.
- Tras cualquier publicación, total, desglose, área y POA ponderada son
  coherentes (invariantes de la sección Salidas).
- Reemplazar un origen distinto exige confirmación y el banner muestra el
  origen vigente.
- «✖ Desactivar» y cualquier publicación no física dejan
  `_multisup_proyecto_fisico` fuera de la sesión; un proyecto guardado
  nunca combina proyecto físico con energía de otro origen.
- Financiero, Baterías, CO₂, Reporte y Unifilar leen las mismas claves sin
  cambios.

## Pruebas requeridas

- Publicación por cada origen: claves completas e invariantes; en `fisico`,
  `multisup_perdida_bus_kWh` = suma del desglose − total de buses.
- Publicación atómica ante desglose incoherente.
- Reemplazo de origen: sin confirmación no escribe.
- Desactivar borra `_multisup_proyecto_fisico`, `multisup_perdida_bus_kWh`
  y `multisup_origen`.
- Guardado de proyecto tras reemplazar físico por simplificado: sin
  `proyecto_fisico` en el payload.
- Prueba de página: ningún botón escribe las claves directamente (AST).
- Regresión: persistencia, Financiero, Baterías, CO₂, Reporte, Unifilar.
