# ==============================================================
# Expense Splitter — Frontend Dockerfile
# Multi-stage build: development (Vite HMR) & production (Nginx)
# ==============================================================

# ── Stage 1: Development ──────────────────────────────────────
FROM node:22-alpine AS development

WORKDIR /app

# Copy package files first for optimal layer caching
COPY package*.json ./
RUN npm ci

# Copy application source
COPY . .

EXPOSE 3007

# Vite dev server listening on 0.0.0.0:3007
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3007"]

# ── Stage 2: Production Build ──────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ── Stage 3: Production Nginx Runtime ──────────────────────────
FROM nginx:alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
