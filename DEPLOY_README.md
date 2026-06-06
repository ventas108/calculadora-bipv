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
