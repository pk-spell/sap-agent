# Multi-stage build für React + Vite
# Stage 1: Build
FROM node:20-alpine AS build

WORKDIR /app

# API URL als Build Argument (wird zur Build-Zeit gesetzt)
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

# Kopiere package files
COPY package.json package-lock.json* ./

# Installiere Dependencies
RUN npm install

# Kopiere Source Code
COPY . .

# Build für Production
RUN npm run build

# Stage 2: Serve mit nginx
FROM nginx:alpine

# Kopiere built files
COPY --from=build /app/dist /usr/share/nginx/html

# Kopiere nginx config (falls vorhanden, sonst Default)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Erstelle nginx config für SPA (Single Page Application)
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
