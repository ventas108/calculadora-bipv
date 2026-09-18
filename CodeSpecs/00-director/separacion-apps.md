# Separación de apps: web principal (calc) vs. app hermana (Streamlit)

**Estado:** política vigente, de cumplimiento obligatorio para cualquier cambio,
despliegue o documentación en este repositorio.

## 1. Por qué existe este documento

El repositorio contiene **dos aplicaciones hermanas independientes** del
ecosistema BIPV (ver también `CodeSpecs/02-recurso-solar/vision.md`, sección 1).
No comparten repo remoto de despliegue, build, proceso PM2 ni entorno de
producción, aunque corren en el mismo servidor. Mezclar comandos o cambios
entre ellas produce despliegues cruzados y sobreescrituras no intencionadas.

## 2. Las dos apps

| | App web principal (`calc`) | App hermana (`streamlit`) |
|---|---|---|
| URL pública | https://calc.innovacionquimica.com.co | https://bipv.innovacionquimica.com.co/ |
| Stack | Node/Vite/Express (`client/`, `server/`) | Python/Streamlit (`bipv_python/`) |
| Ruta en servidor | `/var/www/bipv/calculadora` | `/var/www/bipv/calculadora-bipv` |
| Proceso PM2 | `calculadora-bipv` | `streamlit-bipv` |
| Comando de actualización | `cd /var/www/bipv/calculadora`<br>`git pull --ff-only origin main`<br>`pnpm build`<br>`pm2 restart calculadora-bipv`<br>`pm2 status` | `cd /var/www/bipv/calculadora-bipv`<br>`git pull --ff-only origin main`<br>`pm2 restart streamlit-bipv`<br>`pm2 status` |

Nota: las rutas del servidor son casi idénticas (`/calculadora` vs.
`/calculadora-bipv`) — verificar dos veces antes de ejecutar cualquier comando.

## 3. Regla de oro

**No mezclar cambios, repos, builds, procesos PM2 ni despliegues entre las dos
apps.** Un cambio de la app web principal solo se despliega en la app web
principal; un cambio de la app Streamlit solo se despliega en la app
Streamlit.

## 4. Reglas de trabajo

1. Siempre identificar primero a qué aplicación pertenece el cambio, antes de
   tocar código, git, build o PM2.
2. Documentar explícitamente si el cambio afecta a la app web, a la app
   Streamlit, o a ambas — incluso si el cambio es solo documentación.
3. No ejecutar `pm2 restart` ni `git pull` sobre el entorno equivocado.
4. No reutilizar comandos de una app en la otra.
5. Si el cambio es solo documentación (CodeSpecs, manuales), sigue siendo
   obligatorio indicar a qué app afecta.
6. Si se tocan textos de UX o manuales, especificar si corresponden a `calc` o
   a la app hermana.

## 5. Si hay duda

Orden de prioridad:

1. No mezclar procesos.
2. No ejecutar despliegues sin confirmar la app correcta.
3. Cerrar la ambigüedad (preguntar al responsable) antes de tocar producción.

## 6. Objetivo

Transparencia total, separación de responsabilidades, y evitar despliegues
cruzados, confusiones de entorno y modificaciones no autorizadas.

## 7. Referencias

- Detalle técnico de ambas implementaciones de recurso solar:
  [`CodeSpecs/02-recurso-solar/vision.md`](../02-recurso-solar/vision.md)
- División de `02-recurso-solar` en dos Specs verticales:
  [`mapa-dependencias.md`](mapa-dependencias.md)
- Decisión registrada: [`registro-de-decisiones.md`](registro-de-decisiones.md)
  (2026-09-16)
