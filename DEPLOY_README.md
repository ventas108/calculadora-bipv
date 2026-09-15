# Solar Shading Calculator — Guía de Despliegue

## Requisitos del Servidor

- **Node.js** >= 22.x
- **pnpm** >= 9.x (o npm/yarn equivalente)
- **MySQL** o **TiDB** (base de datos relacional)
- Puerto disponible (por defecto usa la variable `PORT` o 3000)

---

## Estructura del ZIP

```
├── client/          → Código fuente del frontend (React 19 + Tailwind 4)
├── server/          → Código fuente del backend (Express + tRPC)
├── shared/          → Tipos y constantes compartidas
├── drizzle/         → Schema de base de datos y migraciones
├── dist/            → BUILD DE PRODUCCIÓN (listo para ejecutar)
│   ├── index.js     → Servidor Express compilado (ESM)
│   └── public/      → Frontend compilado (assets estáticos)
├── package.json     → Dependencias del proyecto
└── pnpm-lock.yaml   → Lockfile de dependencias
```

---

## Despliegue Rápido (usando el build incluido)

### 1. Instalar dependencias de producción

```bash
pnpm install --prod
# o con npm:
npm install --omit=dev
```

### 2. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
# Base de datos (obligatorio)
DATABASE_URL=mysql://usuario:password@host:3306/solar_calculator

# Autenticación (obligatorio)
JWT_SECRET=tu_secreto_jwt_seguro_aqui

# OAuth Manus (si aplica)
VITE_APP_ID=tu_app_id
OAUTH_SERVER_URL=https://oauth.manus.im
VITE_OAUTH_PORTAL_URL=https://id.manus.im

# API NREL (para PVWatts)
NREL_API_KEY=tu_api_key_nrel

# Puerto (opcional, default 3000)
PORT=3000
```

### 3. Ejecutar migraciones de base de datos

```bash
pnpm db:push
```

### 4. Iniciar el servidor de producción

```bash
node dist/index.js
```

El servidor servirá tanto la API (`/api/trpc`) como el frontend estático desde `dist/public/`.

---

## Despliegue con Docker (alternativa)

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --prod
COPY dist/ ./dist/
COPY drizzle/ ./drizzle/
COPY drizzle.config.ts ./
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

```bash
docker build -t solar-calculator .
docker run -d -p 3000:3000 --env-file .env solar-calculator
```

---

## Desarrollo Local (si necesitas modificar el código)

```bash
# Instalar todas las dependencias (incluyendo dev)
pnpm install

# Ejecutar en modo desarrollo (hot reload)
pnpm dev

# Ejecutar tests
pnpm test

# Generar nuevo build de producción
pnpm build
```

---

## Notas Importantes

- El build en `dist/` ya está compilado y listo para producción
- No es necesario ejecutar `pnpm build` a menos que modifiques el código fuente
- La base de datos debe existir antes de ejecutar `pnpm db:push`
- El servidor sirve el frontend automáticamente — no necesitas nginx/apache para los assets estáticos

---

## Comandos para PowerShell — actualización manual en DigitalOcean

Esta sección sirve como referencia cuando se necesite publicar un cambio
validado en el servidor de producción.

### Datos operativos confirmados

| Dato | Valor |
|---|---|
| Servidor | `198.199.75.160` |
| Usuario SSH | `root` |
| Hostname | `bipv-colombia` |
| Proyecto web | `/var/www/bipv/calculadora` |
| Rama de producción | `main` |
| Proceso PM2 web | `calculadora-bipv` |
| Entrada PM2 | `/var/www/bipv/calculadora/dist/index.js` |
| Puerto interno web | `3000` |
| Proceso PM2 Python | `streamlit-bipv` |
| Puerto interno Python | `8501` |

### 1. Conectarse desde Windows PowerShell

Usando una clave SSH:

```powershell
ssh -i "$env:USERPROFILE\.ssh\NOMBRE_DE_TU_CLAVE" root@198.199.75.160
```

Si la clave ya está configurada por defecto en OpenSSH:

```powershell
ssh root@198.199.75.160
```

### 2. Comprobar el estado antes de actualizar

Ejecutar dentro del servidor DigitalOcean:

```bash
cd /var/www/bipv/calculadora
git status --short --branch
git log -1 --oneline
pm2 status
```

No continuar si hay cambios locales importantes o si `calculadora-bipv` no
aparece como `online`.

### 3. Actualizar la aplicación web

Ejecutar dentro del servidor, después de validar el cambio localmente y subirlo
a GitHub:

```bash
cd /var/www/bipv/calculadora
git pull --ff-only origin main
pnpm build
pm2 restart calculadora-bipv
pm2 status
```

### 4. Comprobar la publicación

```bash
pm2 logs calculadora-bipv --lines 50
ss -tulpn | grep -E ':80|:443|:3000'
```

Después, abrir el dominio de producción en el navegador y comprobar la función
modificada con un caso conocido.

### 5. Actualizar Streamlit solo si el cambio le corresponde

La aplicación Streamlit es independiente de la aplicación web:

```bash
cd /var/www/bipv/calculadora-bipv
git pull --ff-only origin main
pm2 restart streamlit-bipv
pm2 status
```

No reiniciar `streamlit-bipv` al publicar únicamente cambios de la aplicación
web.

### 6. Si el despliegue falla

No repetir comandos a ciegas. Revisar primero:

```bash
pm2 status
pm2 logs calculadora-bipv --lines 100
git status --short --branch
```

Si el proceso quedó detenido y el build anterior sigue disponible, se puede
volver temporalmente a la versión anterior solo después de revisar el log y
confirmar el commit correcto.

### Seguridad

- Nunca guardar contraseñas, tokens de GitHub, claves privadas SSH, `DATABASE_URL`, `JWT_SECRET` ni `NREL_API_KEY` en este archivo.
- Nunca pegar esos secretos en el chat ni en un commit.
- La clave privada debe permanecer en el equipo local, normalmente dentro de `%USERPROFILE%\.ssh`.
- Si un token aparece dentro de `git remote -v`, revocarlo inmediatamente y reemplazar el remoto por una URL sin credenciales.
- Antes de desplegar, ejecutar `pnpm check` y `pnpm build` en el entorno local.
