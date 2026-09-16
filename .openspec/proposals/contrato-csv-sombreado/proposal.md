# Proposal: Contrato del CSV de Factor de Sombreado entre apps hermanas

## Objective

Formalizar el contrato de datos que cruza la frontera entre las dos aplicaciones hermanas del ecosistema BIPV:

- `bipv.innovacionquimica.com.co` (interfaz React + Motor Solar Python), que produce el CSV de factor de sombreado geométrico.
- `calc.innovacionquimica.com.co` (Streamlit), que lo consume en el módulo Mismatch/Bypass Diodes y propaga el resultado a Producción, Financiero y Motor Óptico.

## Current state

- El cálculo real vive en `bipv_python/calculos/contrato_sombreado.py` + `bipv_python/scripts/run_shading_contract.py` (Motor Solar Python, ray-casting oficial). Node (`server/shadingEngineProxy.ts`) es solo un proxy de proceso, no calcula física.
- Existe un contrato JSON ya formalizado y validado en dos idiomas (`bipv.shading.v1`): `bipv_python/calculos/contrato_sombreado.py` (Python) y `shared/shading-engine-contract.ts` (TypeScript), con reglas idénticas que impiden que FS climático o combinado se hagan pasar por FS geométrico.
- El consumidor real del CSV derivado es `bipv_python/calculos/mismatch_bypass.py::cargar_csv_fs()`, invocado desde `bipv_python/pages/5_🔀_Mismatch.py`.
- Existe documentación dispersa pero no centralizada: advertencias de zona horaria, de la casilla "Invertir FS", y de los dos CSV (crudo vs. promediado) están en `bipv_python/datos/base_conocimiento_asistente.md` (Anexos 56-57), no en un documento de contrato formal.
- Borrador inicial ya redactado en `CONTRATO_CSV_SOMBREADO_ENTRE_APPS.md` (raíz del repo).

## Affected modules

### Shared / contrato

- `shared/shading-engine-contract.ts`
- `bipv_python/calculos/contrato_sombreado.py`

### Server (proxy, sin física)

- `server/shadingEngineProxy.ts`

### Cálculo Python (motor + consumidor)

- `bipv_python/scripts/run_shading_contract.py`
- `bipv_python/calculos/sombras_3d.py`
- `bipv_python/calculos/mismatch_bypass.py`

### Cliente (generación de puntos de muestreo, export CSV — ubicación exacta de la conversión UTC→local pendiente de aislar)

- `client/src/lib/buildingModelImporter.ts`
- `client/src/components/CrossingModal.tsx`

### Consumidor final (Streamlit)

- `bipv_python/pages/5_🔀_Mismatch.py`
- `bipv_python/pages/6_📊_Produccion.py`
- `bipv_python/pages/7_💰_Financiero.py`
- `bipv_python/pages/5b_🔆_Motor_Optico.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`

### Documentación existente relacionada

- `bipv_python/datos/base_conocimiento_asistente.md` (Anexos 56-57)
- `CONTRATO_CSV_SOMBREADO_ENTRE_APPS.md`

## Constraints

- No modificar la lógica de rechazo ya implementada en `cargar_csv_fs()` (falta de `FS_geometrico` → rechazo total).
- No tratar el CSV como un simple archivo plano: es la materialización en disco del contrato `bipv.shading.v1` ya validado en JSON.
- Mantener la separación FS_geometrico / FS_climatico / FS combinado — nunca permitir que climático o combinado activen bypass.
- No introducir cambios de columnas sin versión explícita documentada.
- Respetar que Node/React nunca es fuente de verdad de la física solar.

## Proposed change

1. Consolidar `CONTRATO_CSV_SOMBREADO_ENTRE_APPS.md` como la fuente única de verdad del contrato CSV (actualmente ya redactado, pendiente de localizar la transformación UTC→local exacta en `client/`).
2. Evaluar agregar una columna/cabecera de versión explícita al CSV para detección de incompatibilidades futuras sin depender de heurística de nombres de columna.
3. Referenciar cruzadamente este contrato desde `shared/shading-engine-contract.ts` (comentario) para que cualquier cambio futuro al JSON oficial dispare una revisión obligatoria del CSV derivado.

## Validation path

- Revisión de `mismatch_bypass.py::cargar_csv_fs()` contra el formato documentado (ya hecha en este borrador).
- Prueba de regresión existente o nueva que confirme el rechazo cuando falta `FS_geometrico`.
- Revisión manual de que Producción/Financiero siguen leyendo `factor_sombra_anual` sin cambios de contrato.
