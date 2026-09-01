# AI Payroll Guardian — Frontend Multi-Stage Dockerfile (Phase 9)

# Stage 1: Build React/Vite Application
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency manifests
COPY package.json package-lock.json* ./
RUN npm ci

# Copy application source code
COPY . .

# Run build bundle (tsc && vite build)
RUN npm run build

# Stage 2: Serve via Nginx
FROM nginx:alpine

# Copy compiled static assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
