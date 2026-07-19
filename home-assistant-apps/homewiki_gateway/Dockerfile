FROM ghcr.io/home-assistant/base:latest

ARG BUILD_VERSION=dev
ARG BUILD_ARCH=amd64

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}"

RUN apk add --no-cache nginx \
  && mkdir -p /run/nginx

COPY nginx.conf /etc/nginx/nginx.conf
COPY offline.html /usr/share/nginx/html/wiki-offline.html

CMD ["nginx", "-g", "daemon off;"]
