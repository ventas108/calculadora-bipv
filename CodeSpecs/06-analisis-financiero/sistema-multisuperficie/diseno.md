# Diseño — Financiero, Baterías y CO₂ con el sistema multi-superficie publicado

**Estado:** implementación

## Entradas

- Superficies activas con sus grupos (`superficies_bipv`), panel de cada
  superficie (`paneles_superficies_estado`), desglose publicado y POA horaria
  de cada superficie (Vista 3D: `poas_vigentes_estado`; físico: `poa_df` de
  las unidades del proyecto).

## Tipos de datos

`multisup_sistema` (clave nueva de la publicación):

```
{
  "P_dc_stc_kW": float,            # Σ módulos × Pmax / 1000 de las superficies publicadas
  "n_modulos": int,
  "por_panel": [{"panel": str, "modulos": int, "P_dc_stc_kW": float,
                 "costo_usd": float | None}],
  "completo": bool,                 # False si alguna superficie no tiene grupos
  "superficies_sin_grupos": [str],
  "mensual_kWh": [float] * 12,      # suma = E_ac_anual_kWh_multisup (± 0,5 kWh)
  "reparto_mensual": "poa_superficie",
}
```

## Salidas

- `multisup_sistema` publicado con el resto de claves, persistido con el
  proyecto y retirado con ellas.
- `calculos/sistema_multisuperficie.py`: `resumen_sistema_multisuperficie`,
  `estado_sistema_publicado(session_state)` →
  `{"activo", "sistema", "problemas"}` y `df_mensual_multisuperficie`.
- Financiero: energía, kWp y módulos del sistema publicado; costo de módulos
  por referencia de panel.
- Baterías: `df_mensual_produccion` sustituido por el reparto mensual publicado
  cuando el modo multi-superficie está activo.
- CO₂: kWp y módulos del sistema publicado.

## Reglas

- Con `multisup_activo`, Financiero **no** exige `produccion_ok`.
- Sin `multisup_sistema` (publicación anterior) → 🔴 «vuelve a publicar en
  🗺️ Vista 3D»; con `completo = False` → 🔴 con las superficies sin grupos.
  En ambos casos Financiero se detiene: no calcula TIR con datos mezclados.
- Presupuesto vinculado con módulos o kWp distintos a los del sistema
  multi-superficie → 🟡 con ambos valores.

## Errores posibles

- POA de una superficie publicada ausente → `ValueError`, no se publica nada.
- Reparto mensual que no suma el total (± 0,5 kWh) → `ValueError`.
- Panel sin `Pmax_stc` → `ValueError` con el nombre de la superficie.

## Dependencias

- `calculos/diseno_electrico_multisup` (`modulos_de_superficie`,
  `paneles_superficies_estado`), `calculos/multi_superficie`
  (`poa_mensual_superficie`), `calculos/publicacion_multisuperficie`.

## Invalidación

`multisup_sistema` está en las mismas listas que `multisup_estado_electrico`:
caduca con la energía publicada, con el cambio de panel o del diseño
eléctrico, y al cambiar de proyecto.

## Criterios de aceptación

1. Escenario D5: Financiero muestra 7.552 kWh/año, 6,37 kWp y 34 módulos sin
   haber corrido Producción, con el banner de la fuente.
2. CAPEX paramétrico de módulos = 18 × costo ASP + 16 × costo SPR.
3. Superficie activa sin grupos → 🔴 y Financiero no calcula.
4. Publicación anterior sin `multisup_sistema` → 🔴 «vuelve a publicar».
5. Baterías: el balance mensual suma la energía multi-superficie.
6. CO₂ muestra 6,37 kWp y 34 módulos.
7. Guardar y cargar conserva `multisup_sistema`.
8. Si un cambio de panel o de diseño eléctrico retira la energía publicada, el
   motivo y las superficies quedan visibles en «🔗 Integrar al análisis
   financiero» hasta volver a publicar (`_multisup_retiro_motivo`,
   `aviso_energia_retirada`); desactivar a mano no deja el aviso.
9. Con `multisup_estado_electrico` 🔴, Financiero no calcula
   (`problemas_financieros`) y explica que el sistema no se puede construir.
10. Si la energía se retiró por un cambio, Financiero, Baterías y CO₂ muestran
   el aviso y que sus valores no son del diseño de Vista 3D
   (`aviso_retiro_para_consumidores`).

## Pruebas requeridas

Unitarias del resumen (potencia, módulos por panel, reparto mensual, sin
grupos, errores), de la publicación y la persistencia, y de las páginas
(AppTest o AST): Financiero sin Producción, 🔴 incompleto, Baterías y CO₂.
