# Spec — Coeficientes de temperatura de la ficha en el modelo IV

**Estado:** validación

## Alcance de la fase

SDM estimado desde ficha (catálogo Excel): su comportamiento con la
temperatura y el R_s del ajuste de baja luz. No cambia los SDM calibrados
(ASP-ST1) ni los manuales.

## Problema a resolver

En 🔬 Motor IV, la teja Hanergy de 32 W daba un Voc de 9,92 V a 61 °C. Con
el β de la ficha (−0,36 %/°C) debía ser 9,39 V. Al revisar el catálogo
completo (3.128 paneles) aparecieron tres fallas:

1. **β Voc:** el modelo solo ajustaba γ Pmax. β salía de la física de la
   celda: silicio ±0,03 %/°C; capa fina muy lejos (teja −0,22 frente a
   −0,36; CdTe ASP-LAM3 −0,10 frente a −0,321).
2. **Método de respaldo** (12 paneles, 10 Batzelis y 2 heurísticos):
   mu_gamma = 0, con γ de hasta **−0,88 %/°C** (ficha −0,36, EINNOVA
   ESM-550T). Esto sí afecta la energía con calor.
3. **R_s = 0,0001 Ω** al ajustar la teja a su curva de baja irradiancia.

## Contexto

Pedido del usuario tras revisar Motor IV con la teja («prepara la spec»). La
ficha SolTech ASP-LAM3 1200×1800 (CdTe, β −0,321, γ −0,214) sirvió para
corroborar el caso CdTe.
