# Validación — Proveedor de sombra opcional `pybdshadow`

**Estado:** no aplica todavía — no hay implementación. Esta Spec es una propuesta pendiente de
aprobación humana; este archivo describe qué se validaría SI se aprueba, no un resultado
obtenido.

## Checklist de validación (a ejecutar solo si existe implementación futura)

- [ ] Una superficie con `tilt_deg` fuera de la tolerancia de horizontalidad es rechazada con un
  mensaje explícito, no un resultado numérico aproximado.
- [ ] `p_shade` producido por este proveedor, comparado contra `sombras_3d.py` con malla 3D real
  del mismo sitio horizontal, tiene error ≤2%.
- [ ] `bipv_python` instala y arranca sin `pybdshadow` presente (import perezoso verificado).
- [ ] `ShadowResult.capacidades_declaradas` bloquea correctamente el uso de este proveedor sobre
  superficies inclinadas/verticales en el adaptador de entrada.
- [ ] Ningún archivo de `transicion_multisuperficie.py` ni `adaptador_multisuperficie.py` requirió
  cambios para consumir este proveedor (mismo contrato `p_shade`/`firma_sombra`).
- [ ] Confirmar que no se modificó el Director, ninguna Spec ajena, ni el contrato
  `docs/contratos/shading-engine-contract.v1.json`.

## Verificación de origen (ya ejecutada, no es la validación de implementación)

La verificación técnica que originó esta propuesta está documentada en
`references/informe-verificacion-pybdshadow-p-shade.md` y en el documento vivo
https://claude.ai/artifact/7fUXsNfnFGFz9kPRT74nDT — incluye prototipos ejecutados, casos de
aceptación con resultado esperado/observado/error, y comandos reproducibles. No constituye
validación de una implementación (no existe todavía) sino la evidencia que sustenta si vale la
pena aprobar `problema.md`/`propuesta.md`/`diseno.md`.
