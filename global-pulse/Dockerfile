# Global Pulse — imagen de despliegue (Railway u otro PaaS con Docker).
# Etapa 1: build de la PWA. Etapa 2: nginx sirviendo el estatico.

FROM node:22-alpine AS build
WORKDIR /build
COPY app/package.json app/package-lock.json ./
RUN npm ci
COPY app/ ./
RUN npm run build

FROM nginx:alpine
# Railway inyecta PORT; nginx lo toma via template + envsubst (soporte nativo
# de la imagen oficial con /etc/nginx/templates/*.template)
ENV PORT=8080
COPY deploy/nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /build/dist /usr/share/nginx/html
EXPOSE 8080
