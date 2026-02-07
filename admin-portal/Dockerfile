# ==============================================
# Behavioral Health Platform - Admin Portal
# Multi-stage production Dockerfile
# ==============================================

# --------------- Build Stage ---------------
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files first for better layer caching
COPY package.json package-lock.json ./

# Install dependencies (ci for reproducible builds)
RUN npm ci --ignore-scripts

# Copy source code and config files
COPY src/ ./src/
COPY public/ ./public/
COPY index.html ./
COPY vite.config.ts ./
COPY tsconfig.json ./
COPY tsconfig.app.json ./
COPY tsconfig.node.json ./

# Set API base URL for production (nginx proxies /api/ to backend)
ENV VITE_API_BASE_URL=/api

# Build the application (skip vue-tsc in Docker, type-checked locally)
RUN npx vite build

# --------------- Production Stage ---------------
FROM nginx:alpine AS production

# Remove default nginx static content
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create non-root user for nginx
RUN addgroup -g 1000 -S appuser && \
    adduser -u 1000 -S appuser -G appuser && \
    chown -R appuser:appuser /usr/share/nginx/html && \
    chown -R appuser:appuser /var/cache/nginx && \
    chown -R appuser:appuser /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R appuser:appuser /var/run/nginx.pid

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
