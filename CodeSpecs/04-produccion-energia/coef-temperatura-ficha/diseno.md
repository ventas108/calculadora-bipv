# Diseño — Coeficientes de temperatura de la ficha en el modelo IV

**Estado:** validación

## Entradas

SDM ya estimado: I_L, I_o, R_s, R_sh, gamma_ref y N_s. Datos de la ficha:
Tk_beta (β Voc), Tk_gamma (γ Pmax), Vmp e Imp.

## Salidas

- `EgRef` (Eg efectiva) y `mu_gamma` ajustado.
- `_beta_voc_modelo`, `_gamma_pmax_modelo`, `_beta_voc_ficha`,
  `_gamma_pmax_ficha` y `_aviso_temperatura`.
- Resolutor común: `EgRef = panel.get("EgRef")`, o la nominal de la
  tecnología.
- 🔬 Motor IV: línea «Temperatura: γ … · β …» y aviso ⚠️ en «Origen del
  modelo».

## Tipos de datos

`EgRef: float` (eV); coeficientes en %/°C (`float | None`);
`_aviso_temperatura: str | None`.

## Errores posibles

- Sin β en la ficha: Eg nominal y solo se ajusta mu_gamma a γ.
- mu_gamma no converge en un Eg: se descarta ese Eg. Si no queda ninguno,
  el SDM queda como antes.
- β inalcanzable: se usa el Eg más cercano y queda el aviso.

## Dependencias

`_resolver_mu_gamma_pvsyst`, `_pmax_pvsyst_a_G` y el nuevo
`_voc_pvsyst_a_T` (`pvlib.pvsystem.v_from_i`).

## Criterios de aceptación

1. JA Solar 730 W: β −0,25 y γ −0,29 (±0,005) con el resolutor común.
2. EINNOVA ESM-550T (respaldo Batzelis): γ −0,36 ±0,01 (antes −0,88).
3. Teja 32 W, con y sin curva:
   - γ −0,40 ±0,01;
   - β a menos de 0,08 de −0,36 (antes 0,11-0,14), con aviso;
   - STC sin cambios.
4. Con la curva, R_s ≥ 1 % de Vmp/Imp (antes 0,0001 Ω).
5. FLEX 70N: β a ≤ 0,03 de la ficha, sin aviso, baja luz 97 %.
6. Los 5 motores dan lo mismo con el panel de respaldo (guardia de física).
