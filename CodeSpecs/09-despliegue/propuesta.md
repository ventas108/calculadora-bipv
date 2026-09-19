# Propuesta — Despliegue

**Estado:** en validación

## Objetivo

Que la ruta, el nombre de proceso PM2 y el archivo `ecosystem.config` de la
app Streamlit en los scripts del repositorio coincidan exactamente con lo
que corre en producción, y que exista una única fuente de verdad (no dos
archivos `ecosystem.config.*` divergentes).

## Alternativas consideradas

1. **Dejarlo como estaba**, confiando en que nadie vuelva a ejecutar esos
   scripts — descartada: es frágil, y ya casi causó confusión hoy mismo al
   intentar `git pull`/`pm2 restart` en la ruta equivocada.
2. **Reescribir todo el flujo de despliegue desde cero** — descartada: fuera
   de alcance; el flujo real (confirmado en producción durante toda esta
   sesión) ya funciona, solo había que corregir la documentación/scripts
   para que coincidan con él.
3. **Corregir los scripts existentes y consolidar un único
   `ecosystem.config.cjs`** como fuente de verdad, dejando
   `ecosystem.config.js` como redirección explícita (no un segundo archivo
   divergente).

## Alternativa recomendada

La 3: corrección mecánica de rutas/nombres, sin cambiar el flujo real de
despliegue, aplicada directamente (sin Claude, análogo al fix de columnas de
Financiero).


_(Pendiente)_

## Alternativa recomendada

_(Pendiente)_
