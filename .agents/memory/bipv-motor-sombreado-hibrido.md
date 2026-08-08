---
name: BIPV - motor híbrido de sombreado
description: Decisión de arquitectura para separar interfaz React del motor solar Python
---

## Decisión

La calculadora de factores de sombreado usará una arquitectura híbrida:

- React/TypeScript: interfaz, carga de archivos, controles, interacción y visualización 3D.
- Python: motor solar oficial, reproducible y compatible con la Calculadora BIPV.

Antes de migrar cualquier cálculo hay que inventariar el código TypeScript actual. El inventario debe clasificar cada cálculo como:

1. funcionalidad que permanece en React como previsualización o interacción;
2. cálculo que debe trasladarse al motor Python;
3. lógica que debe eliminarse por duplicada o no trazable.

La única fuente oficial de resultados solares será el motor Python. Su salida principal será `FS_geometrico` con metadatos trazables, compatible con el contrato que ya consume BIPV para Mismatch, bypass, Vista 3D y producción.

**Why:** Python ofrece el ecosistema científico y solar más adecuado (`numpy`, `pandas`, `pvlib`, `scipy`, `trimesh`) y permite alinear el diagnóstico con la Calculadora BIPV sin mantener dos modelos físicos divergentes.

**How to apply:** al iniciar una modificación del módulo externo, revisar primero el cálculo TypeScript real, ejecutar la línea base y decidir por evidencia qué queda en la interfaz y qué se convierte en cálculo oficial de Python. No reescribir todo ni conectar producción antes de cerrar ese inventario.