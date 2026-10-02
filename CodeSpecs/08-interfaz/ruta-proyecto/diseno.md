# Diseño — 🧭 Ruta del proyecto

**Estado:** validación

## Entradas

`tipo_instalacion` y el estado de la sesión. Cada paso define qué clave
indica «listo»:

| Paso | Clave |
|---|---|
| Recurso Solar | `poa_df` |
| Recurso Solar 1.ª | `tmy_df` |
| Recurso Solar 2.ª | `poa_geometria_filas` = `filas_energia` |
| Dimensionamiento | `inversor_dict_dim` y `N_serie` |
| Granja FV | `filas_energia` |
| Motor Óptico | `motor_optico_ok` |
| Mismatch | `pct_mismatch_fab` |
| Unifilar | `perdida_ohmica_unifilar` |
| Producción | `res_produccion` |
| Presupuesto | `presupuesto_capex_usd` |
| Financiero | `financiero_ok` |
| Impacto CO₂ | `co2_anual_t` |
| Reporte | `reporte_generado` |

## Salidas

- `estado_ruta(tipo, estado) -> list[{clave, icono, nombre, pagina, consejo, opcional, estado, motivo}]`
- `siguiente(pasos)`
- `html_ruta(pasos)`
- `resumen(pasos)`

## Tipos de datos

`estado` ∈ listo / desactualizado / siguiente / por_hacer / opcional /
verificacion.

## Errores posibles

- 📋 Ficha RETIE no guarda resultado: se muestra 🔎 y nunca es «siguiente».
- `st.page_link` fuera de la app multipágina: se omite el botón.

## Dependencias

`calculos/coherencia_reporte.py` y `calculos/granja_fv.py`.

## Criterios de aceptación

1. Rutas en el orden de la sección 119: Unifilar antes de Producción,
   Presupuesto antes de Financiero, Granja FV entre las dos pasadas.
2. Las páginas de la ruta existen.
3. Proyecto nuevo: ▶️ Recurso Solar; opcionales en ⚪; RETIE en 🔎.
4. Granja con la geometría enviada sin POA nueva: 🟠 en la 2.ª pasada; con la
   POA recalculada: ✅ y sigue el Motor Óptico.
5. Inversores distintos: Producción 🟠.
6. Cables manuales en granja: Producción 🟠, CO₂ 🟠 aguas abajo y ▶️ Unifilar.
7. HTML con una estación por paso; 🏠 Proyecto la muestra debajo del tipo.
