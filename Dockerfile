# syntax=docker/dockerfile:1
ARG PY_VERSION=3.11

##
# Build stage: build and install dependencies
##
FROM python:${PY_VERSION} AS builder

ARG VERSION=0.dev
ENV PDM_BUILD_SCM_VERSION=${VERSION}

WORKDIR /project

# install PDM
RUN pip install -U pip setuptools wheel
RUN pip install pdm pdm-dockerize

RUN --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=pdm.lock,target=pdm.lock \
    --mount=type=cache,target=$HOME/.cache \
    pdm dockerize --prod -v

##
# Run stage: create the final runtime container
##
FROM python:${PY_VERSION} AS runtime

WORKDIR /app

# Fetch built dependencies
COPY --from=builder /project/dist/docker /app
# Copy needed files from your project (filter using `.dockerignore`)
COPY  . /app

ENTRYPOINT ["/app/entrypoint"]
CMD ["your-default-command"]