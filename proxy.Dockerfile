FROM node:20-slim AS build
COPY ./frontend /app
WORKDIR /app
RUN npm install -g pnpm
RUN pnpm install && pnpm run build

FROM caddy:2.7-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /usr/share/caddy
EXPOSE 6916
