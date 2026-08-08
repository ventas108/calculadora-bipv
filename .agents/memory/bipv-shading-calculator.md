---
name: BIPV - Calculadora de Sombreado
description: App separada en bipv.innovacionquimica.com.co que exporta FS horario por punto de análisis, base de datos para el modelo bypass diodes
---

## Calculadora de Factor de Sombreado

**URL:** `bipv.innovacionquimica.com.co`
**Stack:** React/TypeScript — `client/src/components/ShadingCalculator.tsx` + `client/src/lib/shadingMaskCrossing.ts`

## Qué hace

1. Carga modelo 3D del edificio vecino/obstáculo (OBJ, gLTF, DXF, FBX, STL, DAE, WRL, 3DS)
2. Carga modelo 3D del edificio propio a evaluar
3. Define "Puntos de Análisis" en la fachada — cada punto = una posición en la fachada (fila de módulos)
4. Botón naranja **"Cruzar Máscara + EPW"** → cruza la máscara geométrica de sombras con datos climáticos EPW → genera FS climático hora a hora

## Formato CSV exportado (post-cruce)

Columnas: `Evento, Mes, Dia, Hora, Altura Solar (deg), Acimut Solar (deg), Obstaculo, FS_geometrico, FS_climatico, FS, Situacion`

- `FS_geometrico`: sombra dura de obstáculos 3D (0=sin sombra, 1=sombra total)
- `FS_climatico`: `1 - POA_actual / POA_clearsky` (Hottel 1976 + isotropic sky)
- `FS`: `Math.max(FS_geometrico, FS_climatico)` — valor final combinado
- Un "Punto de Análisis" = timestamp por orientación/fila de fachada

## Integración con modelo bypass diodes (Tarea #29)

`FS` del CSV = `p_shade` [0–1] directo para el modelo de bypass diodes:
- Un Punto de Análisis por FILA de módulos → mapeo a filas del string
- `G_shade = G_eff × (1 - FS)` para módulos en esa fila
- `G_clear = G_eff` para módulos fuera de la sombra
- Elimina el paso de estimar p_shade desde geometría solar

**Why:** Evita reimplementar la geometría de sombras 3D en la calculadora Streamlit — reutiliza el cálculo ya certificado de la herramienta de sombreado existente.

**How to apply:** En Página 5 (Mismatch), añadir uploader del CSV. Parsear con pandas, indexar por timestamp (Mes+Dia+Hora → alinear con TMY). Guardar como `st.session_state["df_fs_por_fila"]`.

## Dirección de producto acordada (agosto de 2026)

La calculadora web de sombreado se convertirá en el **“Módulo de diagnóstico solar y
optimización económica para proyectos BIPV”**: debe decidir qué alternativa reduce
demostrablemente la pérdida solar, no calcular CAPEX, OPEX, TIR, VPN, payback ni precios.

**Regla:** la palabra “económica” significa optimización de energía perdida/recuperada y
apoyo a una decisión de diseño; la conversión a COP y rentabilidad ocurre únicamente en
la Calculadora BIPV — Colombia, después de importar el escenario elegido.

**Por qué:** los cálculos financieros aislados del módulo no tienen suficientes datos ni
rigor; mantenerlos daría una apariencia de precisión y debilitaría la confianza comercial.

**Cómo aplicar:** priorizar rigor solar, escenarios actual vs. alternativas, pérdida
geométrica separada de nubosidad, informe técnico reproducible, integración autorizada
con BIPV y una auditoría de pruebas mínimas antes de anunciar la nueva versión.

## Relación con el Motor Óptico de BIPV

El módulo externo puede calcular IAM Ashrae, soiling y POA para su diagnóstico comparativo,
pero esos factores no se transfieren como pérdidas acumulables a la Calculadora BIPV.

**Regla:** el intercambio principal es `FS_geometrico` por fachada/punto/hora más los
metadatos del escenario; BIPV vuelve a calcular IAM, soiling, temperatura, mismatch,
bypass y producción final. La pérdida atribuible al obstáculo se mide comparando dos
corridas BIPV idénticas: sin máscara geométrica vs. con máscara geométrica.

**Why:** aplicar POA/IAM/soiling en ambas aplicaciones y sumar porcentajes produciría
doble conteo; además, nubosidad (`FS_climatico`) no debe activar bypass físico.

**How to apply:** el informe externo muestra pérdidas ópticas como contexto y pérdidas
geométricas como diagnóstico; solo BIPV publica producción final, energía perdida del
sistema y efecto económico.
