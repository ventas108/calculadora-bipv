# Diseño — Cadena de pérdidas multi-superficie

**Estado:** validación

## Entradas

- Por superficie: POA horaria (`calcular_poa_superficie`, 8760 h con
  `poa_global`, `poa_direct`, `poa_sky_diffuse`), inclinación, tipo, área
  instalada, panel (η STC, NOCT, γ, vidrio), `k_bipv` (nuevo campo) e
  inversor asignado (η).
- TMY (`T2m`) de ☀️ Recurso Solar.
- 🔆 Motor Óptico, si se corrió: `motor_optico_f_iam_dif`,
  `motor_optico_soiling_config`, `motor_optico_k_soil_vert`.
- 🔀 Mismatch, si se corrió: `factor_mismatch_sin_soiling`.
- 📊 Producción / defaults: `pct_mismatch_fab`, `pct_cableado_dc`,
  `pct_cableado_ac`.

## Salidas

`cadena_superficie(...) -> dict` con:

- `poa_optica_kWh_m2`, `f_iam`, `f_soiling`, `f_termico`, `f_mismatch`,
  `f_cables`, `eta_inversor`, `f_sombra`, `pr_superficie`,
  `e_ac_anual_kWh`, reparto mensual y `origen_parametros` (Motor Óptico o
  valores por defecto; Mismatch o sin sombra de horizonte).

La publicación multi-superficie guarda el desglose por superficie y la
versión de la cadena (`cadena_perdidas_v1`) para invalidar publicaciones con
el 0,78.

Motor por superficie: `cascada_optica` (IAM + suciedad) → POA óptica →
`simular_produccion_anual` (SDM, T celda NOCT + `k_bipv`, mismatch de
fabricación, cables, η inversor y sombra de horizonte como
`factor_pr_mismatch`). PR = E_ac / (POA bruta × módulos × Pmax). Resultado
guardado en memoria por huella de entradas (`_cadena_perdidas_cache`).

## Tipos de datos

Series `numpy` de 8760 valores; factores `float` en (0, 1]; energías en
kWh/año; `k_bipv` en {1,0; 1,15; 1,3; 1,5} o valor manual 1,0–1,6.

## Errores posibles

- Superficie sin POA vigente o panel sin NOCT/γ: no entra en la energía y la
  página lo dice (mismo criterio que hoy para el panel).
- POA sin `poa_direct`: la cascada usa su respaldo documentado y se avisa.
- Factores fuera de (0, 1]: error explícito, nunca recorte silencioso.

## Dependencias

`calculos/motor_optico.py`, `calculos/produccion.py` (parámetros de
pérdidas), `calculos/mismatch_bypass.py`,
`calculos/transicion_multisuperficie.py`, `calculos/multi_superficie.py`,
`calculos/publicacion_multisuperficie.py`. `physics-guard`: toca
temperatura, óptica y energía; cada fórmula nueva lleva prueba física.

## Criterios de aceptación

1. **Sin 0,78 oculto:** ningún origen usa `pr_sistema` = 0,78 por defecto; el
   PR de cada superficie sale de la cadena y se muestra desglosado.
2. **Coherencia con Producción:** para una sola superficie con la misma
   geometría, panel, Motor Óptico y parámetros, el simplificado nuevo queda a
   ±2 % de la E_ac de 📊 Producción (sin sombra ni recorte).
3. **Motor Óptico conectado:** cambiar el vidrio (b0) o la suciedad en 🔆 Motor
   Óptico cambia la energía multi-superficie publicada (o la marca como
   vencida hasta volver a publicar).
4. **Vertical ≠ techo:** con el mismo panel, una superficie a 90° tiene
   f_iam menor que una a 10° y usa `k_soiling_vert`; su `k_bipv` por defecto
   es el de fachada.
5. **Físico sin doble conteo:** el físico recibe la POA con IAM + suciedad y
   aplica el térmico una sola vez (dentro del SDM).
6. **Sin doble transparencia** cuando η es de módulo.
7. **Caso del cliente:** se informa la energía y la TIR antes (0,78) y después
   (cadena) de la fachada ASP y del techo SPR, con el desglose de pérdidas.
8. Proyectos guardados con la versión anterior: aviso y nueva publicación, sin
   romper la carga.
