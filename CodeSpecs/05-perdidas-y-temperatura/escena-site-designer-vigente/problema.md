# Spec — Escena de Site Designer vigente

**Estado:** validación

## Alcance de la fase

🗺️ Vista 3D, sombra multi-superficie con escenas de Site Designer.
Integra en main los parches de la auditoría del 22-sep que quedaron sin
integrar en el Codespace (rama `borrador/validacion-lasalle`, c007c0ba).

## Problema a resolver

1. Una escena de Site Designer de otra ubicación solo mostraba un aviso y se
   usaba igual: sombras de otro sitio en el proyecto.
2. Si se cargaba una escena nueva y no se volvía a pulsar «Calcular sombra»,
   la sombra de la escena anterior seguía aplicada en silencio. La firma de
   sombra guardaba solo «externa_marsh», igual para todas las escenas.
3. El bypass aplica la fracción de sombra (haz directo) a la irradiancia
   total sin decirlo.
4. El Manual del Asistente no decía cómo presentar los casos East2 y La Salle.

## Contexto

Revisión del 3-oct-2026: de los 7 parches del respaldo, la validación de los
puntos 3D ya la resolvió main (Spec `08/puntos-3d-validacion`). El parche
original además cambiaba la fuente de la firma a «externa_marsh», lo que
desactivaba `invalidar_sombra_por_version_algoritmo` (solo reconoce firmas
de `sombras_3d`), e invalidaba la sombra al abrir un proyecto guardado
(la escena no se guarda con el proyecto).
