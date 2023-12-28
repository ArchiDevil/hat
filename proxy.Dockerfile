FROM node:20 AS build
COPY ./frontend /app
WORKDIR /app
RUN npm install && npm run build

FROM caddy:2.7-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /usr/share/caddy
EXPOSE 6916
