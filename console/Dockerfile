# Stage 1: Build
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

# Stage 2: Serve with nginx
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# SPA fallback: all routes -> index.html
RUN echo 'server { \
    listen 3000; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { try_files $uri $uri/ /index.html; } \
    location /api/ { proxy_pass http://api:8000; } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
