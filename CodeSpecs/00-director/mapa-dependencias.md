# Mapa de dependencias

```text
01-datos-proyecto
      ↓
02-recurso-solar
      ↓
03-dimensionamiento
      ↓
04-produccion-energia
      ↓
05-perdidas-y-temperatura
      ↓
06-analisis-financiero
      ↓
07-informes
      ↓
08-interfaz
      ↓
09-despliegue
```

## Reglas

- Un módulo solo puede pasar a `en implementación` cuando sus dependencias directas
  tienen `diseno.md` en estado `aprobado`.
- Un cambio en el contrato de un módulo obliga a revisar los módulos dependientes
  antes de archivar la Spec.
- El director es responsable de detectar y resolver conflictos entre módulos que
  calculen la misma magnitud de forma distinta.
