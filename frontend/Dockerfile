# Stage 1: Build static assets
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY package*.json ./
RUN npm install

# Copy application source
COPY . .

# Accept API base URL as a build argument
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Compile production bundle
RUN npm run build

# Stage 2: Serve with lightweight Nginx web server
FROM nginx:alpine

# Copy compiled assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
