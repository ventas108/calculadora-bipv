# JRC/Huld como motor primario de energía para CdTe (reemplaza al SDM, solo en Producción)

**Fecha**: 2 de septiembre de 2026
**Disparador**: cierre de la investigación del vacío mensual de PR para CdTe (ver
`DIAGNOSTICO_RECOMBINACION_CDTE.md`) — tras descartar corrección espectral, V_bi genérico,
sesgo de Pnom y agotar el ajuste de parámetros del SDM (Rs, Rsh, Gamma, recombinación d²/µτ),
se encontró la causa raíz estructural: el modelo de un solo diodo con Rsh exponencial produce
una "joroba" de eficiencia relativa por encima del 100% entre G=100-300 W/m² que ni una corrida
real de PVsyst 8.1.5 ni el modelo empírico JRC/Huld (ya en el repo como "segunda opinión" desde
el 31-ago-2026) reproducen.

## Evidencia real que sustenta el cambio

Comparación estadística rigurosa, mismo panel (ASP-ST1-T40), mismo sitio real (Teusaquillo,
fachada vertical), contra el patrón mensual de PR de una corrida real y válida de PVsyst 8.1.5:

| | Correlación (forma mensual) | RMSE | MAE |
|---|---|---|---|
| SDM (motor anterior) | **r = -0,142** (sin relación, incluso inversa) | 16,19 pts | 15,64 pts |
| **JRC/Huld** | **r = 0,545** (correlación positiva real) | **13,17 pts** | **12,21 pts** |

Curva de eficiencia relativa punto a punto (T=25°C) — el porqué estructural:

| G (W/m²) | SDM (Rsh exponencial) | JRC/Huld (empírico, ESTI) |
|---|---|---|
| 1000 (STC) | 96,0% | 100,0% |
| 300 | **105,5%** | 95,1% |
| 200 | **106,1% (pico)** | 88,6% |
| 100 | **102,9%** | 72,1% |
| 50 | 94,7% | 48,6% |

El SDM predice que CdTe se vuelve MÁS eficiente que en STC entre G=100-300 W/m² (por el Rsh
exponencial, calibrado contra un único punto real de laboratorio, Batzner et al. 2001). El
modelo JRC/Huld (ajustado directamente contra mediciones reales de módulos CdTe en el ESTI
europeo, Huld et al. 2011) muestra una caída monótona desde STC, sin joroba. Como una fachada
vertical pasa la mayoría de sus horas productivas justo en ese rango 50-300 W/m², la joroba del
SDM se acumula mes tras mes en una ganancia artificial de energía.

## Decisión: NO reemplazo total, reemplazo acotado a energía

`calculos/modelo_jrc_huld.py` (creado 31-ago-2026) documentaba explícitamente "NO reemplaza al
motor principal — es una verificación cruzada puntual". Esa decisión se revisita hoy porque la
evidencia disponible entonces era solo literatura (rangos, sin serie mensual real); hoy hay una
corrida real de PVsyst comparada mes a mes, evidencia cualitativamente distinta.

**Pero la razón estructural para NO reemplazar todo sigue siendo válida**: JRC/Huld solo predice
Pmax (W) — no calcula Voc, Isc, Vmp, Imp por separado, ni una curva I-V. Tres módulos de la app
necesitan esa curva completa y NO pueden usar JRC/Huld:

- `mismatch_bypass.py` — necesita Isc individual por módulo para diodos de bypass bajo sombra.
- `mppt_combinado.py` — necesita la curva I-V completa para combinar strings en un MPPT compartido.
- Compatibilidad eléctrica / dimensionamiento — necesita Vmp/Voc reales para la ventana MPPT del
  inversor y el máximo voltaje del array.

**Alcance final**: `calculos/produccion.py::_calcular_pmax_vectorizado()` usa JRC/Huld como motor
primario para CdTe. `produccion_iv.py` (Motor IV, curva real), `mismatch_bypass.py` y
`mppt_combinado.py` siguen exclusivamente en el SDM, sin cambios.

## Implementación

- `calculos/produccion.py::_calcular_pmax_vectorizado(G, T_cel, panel)`: si
  `clasificar_tecnologia_jrc(panel["tecnologia"]) == "CdTe"` y el panel tiene `Pmax_stc > 0`,
  llama `potencia_jrc(G, T_cel, Pmax_stc, tecnologia="CdTe")` en vez del SDM. Si `Pmax_stc` falta
  o es 0, cae al mismo fallback lineal genérico que ya existía para paneles sin SDM completo (no
  revienta, no inventa un valor).
- **Decisión de diseño sobre temperatura**: se sigue usando el `T_cel` que ya calcula la app
  (NOCT + `k_bipv`, el factor de confinamiento térmico IEA-PVPS T15 específico de BIPV) como
  entrada a `potencia_jrc()`, **no** el modelo Faiman propio de JRC/Huld (`u0=23,37, u1=5,44`,
  ajustado contra módulos en montaje abierto/techo, sin confinamiento BIPV). Se prefirió preservar
  la física de confinamiento térmico ya validada y usada en toda la app, en vez de la pareja
  exacta temperatura+potencia del paper original — una desviación real, documentada aquí, no
  oculta.
- **Caveat real de precisión**: JRC/Huld da `Pmax = Pmax_stc` EXACTO en STC (G=1000, T=25) porque
  su fórmula se reduce a factor=1,0 (ln(1)=0) — no puede reproducir la inconsistencia real de
  ~4% entre `Vmpp×Impp` y `Pmax` nominal que sí tiene la ficha real de ASP-ST1-T40 y que el SDM
  (o una corrida real de PVsyst) sí capturan. Es una desventaja real de precisión en STC a cambio
  de mucha mejor precisión en el patrón de baja irradiancia.
- **Alcance del catálogo real**: 7/7 paneles de la familia ASP-ST1 en `MODULOS_BIPV`, y 53/76
  paneles del catálogo Excel (`datos/catalogo_paneles_excel.py`) se clasifican como CdTe vía
  `clasificar_tecnologia_jrc()` — todos cambian de motor de energía. La validación numérica
  directa contra PVsyst solo existe para ASP-ST1-T40 (el caso real de Teusaquillo); el resto se
  beneficia por extensión del mismo argumento estructural (el defecto de la joroba es de la
  ecuación del modelo, no de la calibración de un panel específico), no por validación individual.

## Interfaz y asistente actualizados

- `pages/6_📊_Produccion.py`: la sección "🔬 Segunda opinión" ya no dice "Motor principal (SDM
  De Soto)" para CdTe — ahora aclara que ambos números (motor principal y verificación cruzada)
  vienen del mismo modelo JRC/Huld, difiriendo solo en el pipeline alrededor (temperatura
  NOCT+k_BIPV vs. Faiman propio; cascada Mismatch/IAM completa vs. solo POA+temperatura).
- La nota de "PR > 100%" (que afirmaba sin contraste "resultado correcto... no es un error de
  cálculo") se suavizó: ya no declara con certeza que un PR>100% sea automáticamente real,
  reconociendo que el propio motor anterior producía ese resultado como artefacto.
- `calculos/asistente.py::contexto_sesion()`: mismo ajuste — para CdTe, ya no describe "SDM vs.
  modelo independiente", sino que aclara que ambos números comparten el mismo modelo de módulo.

## Verificación

- `tests/test_consistencia_sdm_entre_modulos.py`: actualizado — para CdTe, `produccion.py` ahora
  debe DIVERGIR intencionalmente de `modelo_iv.py` (verificado contra `potencia_jrc()` directo,
  no contra el SDM); `produccion_iv.py`/`mismatch_bypass.py` siguen exigiendo igualdad exacta con
  el SDM, sin cambios.
- `tests/test_jrc_huld_primario_cdte.py` (nuevo, 6 tests): ancla real de STC (63,0W exacto, no
  60,48W del SDM), coincidencia exacta con `potencia_jrc()` directo, ausencia de la joroba >100%
  (con margen real de +2% para el sobrepico genuino y pequeño que sí tiene JRC/Huld cerca de
  STC), Motor IV sigue en SDM sin cambios, paneles no-CdTe no cambian de motor, fallback sin
  `Pmax_stc` no revienta.
- Suite completa: **939/939** (933 previos + 6 nuevos).
