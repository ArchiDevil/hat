FROM node:20-slim AS build
RUN npm install -g pnpm
COPY ./frontend/package.json /app/package.json
COPY ./frontend/pnpm-lock.yaml /app/pnpm-lock.yaml
WORKDIR /app
RUN pnpm install
COPY ./frontend /app
RUN pnpm run build:prod

FROM caddy:2.7-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /usr/share/caddy
EXPOSE 6916
