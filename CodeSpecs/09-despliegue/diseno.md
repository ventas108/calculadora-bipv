# Diseño — Despliegue

**Estado:** en validación

## Entradas

- Commit ya validado y subido a `main`/GitHub.
- Configuración real del servidor: ruta `/var/www/bipv/calculadora-bipv`,
  proceso PM2 `streamlit-bipv` (Python) y `calculadora-bipv` (Node),
  separados según `00-director/separacion-apps.md`.

## Salidas

- Servidor de producción en el mismo commit que `main`/GitHub
  (`git rev-parse --short HEAD` coincide en ambos lados — regla permanente
  registrada en memoria del repositorio, 19-sep-2026).
- Un único `ecosystem.config.cjs` por app, sin duplicados divergentes.

## Unidades

- No aplica.

## Tipos de datos

- Scripts bash y configuración PM2 (`.cjs`); no hay estructuras de datos
  propias de este módulo.

## Errores posibles

- Ruta o nombre de proceso desactualizado en un script: falla silenciosa
  (`cd` a un directorio inexistente, o `pm2 restart` sin encontrar el
  proceso) — causa raíz de esta Spec.
- Mezclar despliegues entre la app web (Node) y la app hermana (Streamlit):
  prohibido explícitamente en `separacion-apps.md`.

## Dependencias

- Módulos previos: `08-interfaz`
- Módulos dependientes: (ninguno, es el módulo final)

## Criterios de aceptación

- `actualizar_en_servidor.sh`, `instalar_servidor.sh` y
  `ecosystem.config.cjs` de `bipv_python/` coinciden exactamente con la
  configuración confirmada en producción.
- Existe una única fuente de verdad de `ecosystem.config` por app; el
  archivo `.js` redirige explícitamente al `.cjs`, no lo duplica.
- Ningún despliegue de código se da por terminado sin verificar
  `git rev-parse --short HEAD` idéntico en GitHub y en el servidor.

## Pruebas requeridas

- No aplica prueba automatizada (son scripts de infraestructura, no lógica
  de la app); la verificación es la revisión manual del diff contra la
  configuración real confirmada por SSH.


- 

## Pruebas requeridas

- 

## Procedimiento de rollback

_(Pendiente)_
