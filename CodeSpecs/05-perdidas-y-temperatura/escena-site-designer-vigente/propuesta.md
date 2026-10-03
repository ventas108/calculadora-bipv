# Propuesta — Escena de Site Designer vigente

**Estado:** validación

## Objetivo

Que la sombra multi-superficie corresponda siempre a la escena del sitio y a
la que está cargada.

## Alternativa recomendada

Autorizada por el usuario el 3-oct-2026 («haz ambas»).

- `cargar_escena_sitedesigner`: huella `malla_fingerprint` =
  «externa_marsh-<sha256 de bloques, ubicación y norte>».
- Vista 3D:
  - rechaza una escena de otra ubicación;
  - firma la sombra con la huella.
- `invalidar_sombra_por_cambio_malla`:
  - retira la sombra calculada con otra escena cuando hay una escena
    cargada;
  - sin escena cargada, la conserva.
- Comentario de alcance radiativo en el bypass.
- Manual del Asistente, sección 122 (East2 y La Salle) y registro.

## Alternativas descartadas

- Cambiar la fuente de la firma a «externa_marsh» (parche original): saltaba
  la protección contra sombras del algoritmo v1.
- Invalidar también sin escena cargada (parche original): borraría la sombra
  de todo proyecto guardado al abrirlo.
- Guardar la escena con el proyecto: más grande y fuera de alcance.

## Fuera de alcance

Separar la difusa en el bypass (Sky View Factor por superficie).
