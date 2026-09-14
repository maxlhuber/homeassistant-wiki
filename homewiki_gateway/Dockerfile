FROM ghcr.io/home-assistant/base-python:3.13-alpine3.24

ARG BUILD_VERSION=dev
ARG BUILD_ARCH=amd64
ARG CODEX_VERSION=0.154.0
ARG CLAUDE_CODE_VERSION=2.1.270

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}" \
  org.opencontainers.image.source="https://github.com/maxlhuber/homeassistant-wiki" \
  org.opencontainers.image.description="Vollautomatisches lokales Home-Assistant-Wiki"

RUN apk add --no-cache nodejs npm git curl libffi libsodium \
  && NPM_CONFIG_CACHE=/tmp/npm-cache npm install -g "@openai/codex@${CODEX_VERSION}" \
  && NPM_CONFIG_CACHE=/tmp/npm-cache npm install -g "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" \
  && rm -rf /tmp/npm-cache

WORKDIR /app
COPY homewiki_gateway/requirements-addon.txt /app/requirements-addon.txt
RUN pip install --no-cache-dir -r /app/requirements-addon.txt
COPY homewiki_gateway/app /app/homewiki
COPY homewiki_gateway/config.yaml /app/homewiki-config.yaml
COPY scripts/*.py scripts/wiki_ai_prompt.txt /app/project/scripts/
# Keep runtime modules on the interpreter's default module path as well.  The
# Supervisor/s6 environment can intentionally omit PYTHONPATH during startup;
# the gateway must still import every pipeline module in that case.
COPY scripts/*.py /app/
# The ingress server imports the redaction patterns directly. Keep this
# module beside the app as a packaging-safe fallback in case the Supervisor
# runtime does not preserve PYTHONPATH for the service process.
COPY scripts/wiki_snapshot.py /app/homewiki/wiki_snapshot.py
COPY homewiki_gateway/runtime/wiki_overrides.yaml /app/project/scripts/wiki_overrides.yaml
COPY homewiki_gateway/runtime/mkdocs.yml /app/project/mkdocs.yml
COPY homewiki_gateway/runtime/docs /app/project/docs
RUN mkdir -p /app/project/docs/manuell \
  && python3 -m mkdocs build --clean --strict --config-file /app/project/mkdocs.yml --site-dir /app/bootstrap-site

ENV PYTHONUNBUFFERED=1 \
    CODEX_HOME=/data/codex-home \
    CLAUDE_CONFIG_DIR=/data/claude-home \
    PYTHONPATH=/app/homewiki:/app/project/scripts \
    HOMEWIKI_VERSION=${BUILD_VERSION}

# s6-overlay v3 starts Docker CMD with a minimal environment. Restore the
# Supervisor-provided environment (especially SUPERVISOR_TOKEN) before Python.
CMD ["/command/with-contenv", "python3", "-m", "homewiki"]
