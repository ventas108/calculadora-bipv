# Mockup UI — Multi-superficie BIPV

**Estado:** propuesta pendiente de aprobacion humana
**Alcance:** definir la interfaz antes de implementar widgets en Vista 3D.

## Objetivo

Permitir que el usuario complete, revise y adopte el modo fisico multi-superficie sin inventar datos y sin publicar resultados parciales.

La UI se integra en la subpestana `Superficies BIPV` de `pages/9_🗺️_Vista_3D.py` y reutiliza el TMY, la malla y los puntos ya cargados por la aplicacion.

## Flujo visible

```text
1. Definir superficie
2. Asignar puntos y malla
3. Calcular sombra por superficie
4. Configurar inversores
5. Revisar estado y comparacion
6. Adoptar explicitamente
```

El modelo simplificado permanece activo por defecto. Activar el modo fisico no escribe ninguna clave `multisup_*`.

## Seccion A — Sombra por superficie

Cada superficie activa muestra un expander con:

```text
[Nombre] [Tipo] [Activa]
Tilt: ... deg    Azimuth: ... deg    Area: ... m2

Geometria de sombra
  Malla: [selector de malla disponible]
  Puntos de analisis: [selector/cargador por superficie]
  Resolucion: [N puntos] / [N serie]
  Transparencia: [0.0 - 1.0]

[Calcular sombra de esta superficie]

Estado: [sin calcular | calculado completo | sombra cero calculada |
         calculo incompleto | error geometrico | resolucion insuficiente]
Cobertura solar: ... %
Advertencias: ...
Firma: ...
[Ver detalle de firma]
```

### Reglas de la seccion A

- La malla seleccionada debe existir y tener un identificador estable.
- Los puntos deben pertenecer a la superficie activa y conservar coordenadas 3D.
- El calculo usa el TMY vigente y guarda su huella real.
- Un cambio de tilt, azimuth, area, `n_serie`, puntos, malla o transparencia retira `p_shade` y `firma_sombra`.
- `sombra cero calculada` solo es valida si todas las horas solares aplicables fueron evaluadas.
- `calculo incompleto`, `error geometrico` y `resolucion insuficiente` bloquean la comparacion.
- `resolucion insuficiente` solo puede continuar con una aprobacion explicita visible y registrada.
- No se presenta un cero numerico como sustituto de un calculo pendiente.

### Accion de lote

```text
[Calcular sombras de todas las superficies activas]
```

La accion es transaccional: si una superficie falla, no se publica ninguna sombra nueva. El panel muestra la lista de superficies bloqueadas y la accion requerida para cada una.

## Seccion B — Inversores

En la misma subpestana, despues de la seccion de sombra:

```text
Inversores del proyecto

[+ Agregar inversor]

ID: INV-1
Ficha: [selector del catalogo]
Eficiencia: ... %
Potencia AC nominal: ... W
Superficies asignadas: [0]
Tipo derivado: [bloqueado hasta asignar]
[Eliminar]
```

Cada superficie activa muestra un selector:

```text
Superficie: Fachada Sur
Inversor asignado: [INV-1 | INV-2 | Sin asignar]
N serie: [...]
N paralelo: [...]
```

El tipo no es editable:

- una superficie asignada: `dedicado`;
- dos o mas superficies asignadas: `compartido`;
- cero superficies asignadas: error bloqueante.

### Reglas de la seccion B

- Una superficie activa sin inversor bloquea el modo fisico.
- Un inversor sin superficies bloquea el modo fisico.
- IDs duplicados bloquean el modo fisico.
- `n_serie`, `n_paralelo`, eficiencia y potencia nominal deben ser validos.
- El tipo se deriva siempre mediante `validar_inversores_y_asignaciones()` y `aplicar_tipos_derivados()`.
- La UI nunca escribe un tipo declarado manualmente como fuente de verdad.
- Eliminar un inversor exige reasignar sus superficies o deja el modo fisico bloqueado.

## Estado de preparacion

Antes de los botones de calculo se muestra una tabla:

```text
Superficie       Sombra       POA       Inversor       Estado
Fachada Sur      Completa     Lista     INV-1          Lista
Techo            Incompleta   Lista     INV-2          Bloqueada
Marquesina       Completa     Falta     Sin asignar    Bloqueada
```

El boton fisico queda deshabilitado si existe al menos una fila bloqueada:

```text
[Calcular comparacion fisica]
```

El mensaje debe nombrar superficie, campo/estado y accion requerida.

## Comparacion y adopcion

Cuando todas las superficies estan listas:

```text
Modelo simplificado       Modelo fisico
E_ac: ... kWh/año          E_ac: ... kWh/año
Diferencia: ... %

[Calcular comparacion fisica]
```

La comparacion guarda solo un candidato temporal y no escribe `multisup_*`.

La adopcion se muestra separada:

```text
[Adoptar calculo fisico]
```

Al pulsarla, la aplicacion debe reconstruir y validar el proyecto desde el `session_state` actual. Nunca debe confiar solo en el candidato guardado de un rerun anterior.

Si la revalidacion falla:

- eliminar el candidato temporal;
- conservar intactas las claves `multisup_*` anteriores;
- mostrar el error concreto;
- no hacer `rerun` hasta que el usuario pueda corregirlo.

Si pasa, `aplicar_proyecto_a_session_state()` es el unico escritor de las cinco claves productivas.

## Persistencia de estado UI

Claves propuestas, no productivas:

- `multisup_malla_id_por_superficie`;
- `multisup_puntos_por_superficie`;
- `multisup_transparencia_por_superficie`;
- `multisup_inversores`;
- `multisup_proyecto_fisico_candidato`;
- `multisup_usar_fisico`.

Los datos calculados deben incluir firma y estado. Las claves productivas solo se escriben tras adopcion valida.

## Criterios de aprobacion del mockup

- [ ] La ubicacion en `Superficies BIPV` es aceptada.
- [ ] La seccion de sombra permite una malla y puntos por superficie.
- [ ] Los estados de sombra y bloqueos son visibles.
- [ ] La resolucion insuficiente requiere aprobacion explicita.
- [ ] La seccion de inversores no permite editar el tipo derivado.
- [ ] El estado de preparacion bloquea si una sola superficie falla.
- [ ] Comparar y adoptar son acciones separadas.
- [ ] Adoptar revalida contra el estado actual.
- [ ] No se modifican consumidores `multisup_*` ni `calculos/invalidacion.py`.
- [ ] Existe prueba de pagina para cada bloqueo y para adopcion valida.

## Fuera de alcance

- Implementar widgets antes de aprobar este mockup.
- Cambiar el modelo simplificado.
- Ejecutar Motor Optico por superficie.
- Cambiar consumidores downstream.
- Activar el modo fisico por defecto.
