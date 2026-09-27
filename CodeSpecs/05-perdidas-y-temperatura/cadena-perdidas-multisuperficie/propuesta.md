# Propuesta — Cadena de pérdidas multi-superficie

**Estado:** validación

## Objetivo

Que la energía multi-superficie que llega a Financiero pase por la misma
cadena física que 📊 Producción, superficie por superficie, con cada pérdida
visible y con aviso si falta un dato; nunca un PR genérico sin decirlo.

## Alternativas consideradas

1. **Escribir `pr_sistema` con el `PR_sistema` de 📊 Producción.** Descartada:
   ese PR es de la superficie única (una orientación, un panel); aplicarlo a una
   fachada vertical y a un techo a 10° mezclaría sistemas (regla de la Spec
   `06/sistema-multisuperficie`).
2. **Aplicar la POA efectiva del Motor Óptico a todas las superficies.**
   Descartada: el IAM y la suciedad dependen de la inclinación y orientación de
   cada superficie.
3. **Cadena por superficie con las funciones existentes** (recomendada): la
   cascada óptica y el factor térmico se calculan con la POA, el vidrio y el
   montaje de cada superficie; las pérdidas eléctricas usan los mismos
   parámetros que 📊 Producción.

## Alternativa recomendada

Nuevo módulo `calculos/cadena_perdidas_multisup.py` que, por superficie:

1. **Óptica:** `cascada_optica` con la POA de la superficie (`poa_direct`,
   `poa_sky_diffuse`), `b0` según el vidrio del panel, `f_iam_dif` y suciedad
   de 🔆 Motor Óptico, y `k_soiling_vert` solo si la superficie es vertical
   (inclinación ≥ 75°). Salida: POA sin térmico (IAM + suciedad) y factores.
2. **Temperatura:** `factor_termico_bipv` con NOCT y γ del panel de la
   superficie y `k_bipv` según el montaje de la superficie (por defecto
   `indice_montaje_default(tipo)`: fachada confinada 1,3, techo según tipo),
   editable en ⚙️ Superficies BIPV.
3. **Eléctricas:** mismatch de fabricación y cableado DC/AC con los valores de
   📊 Producción (mismos defaults), η de cada inversor asignado.
4. **Sombra:** en el simplificado, el factor de sombra de horizonte de
   🔀 Mismatch sin suciedad (`factor_mismatch_sin_soiling`); en bypass y físico
   la sombra ya la resuelve su propio modelo, y no se vuelve a aplicar.

Uso por origen:

- **Simplificado:** E = Σ horas [POA óptica × área instalada × η STC ×
  f_térmico] × f_mismatch × f_cables × η inversor × f_sombra. El PR resultante
  se muestra en una tabla por superficie (óptico, térmico, mismatch, cables,
  inversor, sombra) y reemplaza el 0,78.
- **Bypass con CSV:** la misma base, más la pérdida por bypass del CSV.
- **Físico:** `simular_bypass_horario` recibe la POA óptica y el `k_bipv` de la
  superficie; luego cables e inversor como hoy.

Avisos: si 🔆 Motor Óptico no se ha corrido, la cascada usa sus valores por
defecto documentados (b0 del vidrio del panel, suciedad Colombia, f_iam_dif
0,95) y la página dice «óptica con valores por defecto: corre 🔆 Motor
Óptico para ajustarla». Nunca se usa 0,78 sin decirlo.

## Ajuste tras la aprobación (27-sep-2026)

El usuario aprobó la Spec («implementa las soluciones»), con las cuatro
decisiones recomendadas. Al implementar, la cadena con temperatura lineal (γ)
se comparó con 📊 Producción para la misma geometría: el techo SPR coincidía
(0,4 %) pero la fachada vertical ASP (CdTe) salía **11 % más alta**, porque el
SDM del panel (🔬 Motor IV) capta que la película delgada rinde menos con poca
luz. Por eso la temperatura, la poca luz, el mismatch de fabricación, los
cables y el inversor se calculan con el **mismo motor de Producción**
(`produccion.simular_produccion_anual`) superficie por superficie, con la POA
óptica de la superficie. La fórmula lineal queda solo para paneles sin SDM
completo, con aviso.

## Decisiones aprobadas por el usuario

1. `k_bipv` por superficie con valor por defecto según el tipo y editable.
2. Transparencia: **no** se aplica cuando η del panel ya es η de módulo
   (Pmax / área del módulo, caso ASP-ST1-T40), para no contarla dos veces.
3. Sombra de horizonte solo en el simplificado.
4. La energía publicada cambia: los proyectos guardados con el 0,78 se marcan
   como «energía de la versión anterior» y piden volver a publicar.

## Fuera de alcance

- Espectro (CdTe), degradación inicial LID y bifacialidad nuevas.
- La sección 6 de Vista 3D (MPPT combinado, fase A3).
- 📊 Producción de superficie única (no cambia).
