---
name: BIPV POA hierarchy and Motor Óptico session keys
description: Jerarquía de fuentes POA en la página Producción y claves de session_state del Motor Óptico
---

# Jerarquía de POA en Producción

La página `6_📊_Produccion.py` sigue esta prioridad para `poa_base`:
1. **Motor Óptico** (`motor_optico_ok=True`) → usa `poa_efectiva_df` (hora a hora, IAM+Soiling+Térmico)
2. **Mismatch** (`mismatch_ok=True`) → usa `poa_df` + `factor_global_mismatch`
3. **POA bruta** → usa `poa_df` directamente

**Why:** El Motor Óptico corrige la irradiancia hora a hora (más preciso que factor anual), por lo que
debe tener prioridad. El factor Mismatch se aplica encima como pérdida adicional en ambos casos.

## Claves session_state del Motor Óptico (página 5b)

| Clave | Tipo | Contenido |
|---|---|---|
| `motor_optico_ok` | bool | True cuando se calculó la cascada |
| `motor_optico_summary` | dict | b0, k_bipv, noct, coef_temp, factor_global, f_iam_prom, f_soil_prom, f_term_prom, perdida_iam/soil/term_kWh_m2, poa_bruta/efectiva_anual_kWh_m2, monthly |
| `poa_efectiva_df` | DataFrame | poa_df con columna poa_global reemplazada por POA corregida |
| `poa_efectiva_anual_kWh_m2` | float | Suma anual de la POA efectiva |
| `motor_optico_b0/tau/k_bipv/noct/coef_temp` | float | Parámetros usados |
| `mo_panel_ref` | str | Nombre del panel al momento del auto-fill (para detectar cambios) |

## Auto-fill en Motor Óptico (página 5b)

Mapa tecnología → b₀:
- CdTe → 0.12 ("Vidrio CdTe laminado")
- CIGS / a-Si → 0.10 ("Vidrio BIPV semi-transparente")
- Mono-Si / Poli-Si / HJT / TopCon → 0.05 ("Vidrio estándar templado")

Fuente de cada parámetro auto-llenado:
- b₀: inferido de `panel_dict["tecnologia"]`
- τ: `panel_dict["transparencia_pct"]` (clampeado a 70%)
- NOCT: `panel_dict["NOCT"]`
- γ: `panel_dict["gamma_mp"]` o `panel_dict["beta_mp"]`
- k_BIPV: NO auto-llenado (depende de arquitectura, no del panel)

**How to apply:** Siempre verificar `motor_optico_ok` antes de usar `poa_efectiva_df`.
Si no está, usar `poa_df` como fallback. Nunca asumir que existe.
