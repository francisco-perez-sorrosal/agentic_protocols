FROM ghcr.io/prefix-dev/pixi:0.40.3 AS install

# Install dependencies
WORKDIR /app
COPY ./pyproject.toml .
COPY ./pixi.lock .
RUN --mount=type=cache,target=/root/.cache/rattler/cache,sharing=private pixi install

# Build for production
FROM install AS build

# Create an "entrypoint.sh" script which activates the pixi environment
RUN printf '#!/bin/sh\n%s\nexec "$@"' "$(pixi shell-hook -e prod)" > /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy only the necessary source files
# COPY .. .
COPY ./src ./src
RUN ls -la

RUN echo "****************************************************"
RUN pwd
RUN ls -la

# Build then install the Python wheel
RUN pixi run build-wheel
RUN pixi run install-wheel

# Final minimal production image
# FROM ubuntu:22.04 AS production
FROM python:3.12-slim-bookworm AS production
COPY --from=ghcr.io/astral-sh/uv:0.6.16 /uv /bin/

ARG RELEASE_VERSION="alice"

# only copy the production environment into prod container
COPY --from=build /app/.pixi/envs/prod /app/.pixi/envs/prod
COPY --from=build /entrypoint.sh /entrypoint.sh
# We don't need to copy this
# COPY --from=build /app/src /app/src
# COPY --from=build /app/README.md /app/README.md
WORKDIR /app
RUN chmod +x /entrypoint.sh
EXPOSE 8000

RUN echo "****************************************************"
RUN pwd
RUN ls -la

RUN cat /entrypoint.sh
RUN ls -la /app/.pixi/envs/prod/bin

RUN echo "Agent alice will run in port 8000"

# Add the path from the pixi environment to the PATH to be accessible by uv
ENV PATH="/app/.pixi/envs/prod/bin:$PATH"
ENV PRODUCTION_MODE=False\
    RELEASE_VERSION=${RELEASE_VERSION}

RUN echo "Platform URL: ${PLATFORM_URL}"

# RUN uv lock
# RUN uv sync --no-cache --locked --link-mode copy
    

ENTRYPOINT ["/entrypoint.sh"]
CMD uv run --no-sync alice
