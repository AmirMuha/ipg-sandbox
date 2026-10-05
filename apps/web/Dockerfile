# syntax=docker/dockerfile:1
FROM node:22-alpine
# node:22 because pnpm 11 declares engines.node >= 22.13; under node:20 pnpm refuses to run.
RUN npm install -g pnpm@11.3.0
WORKDIR /repo

# Workspace manifests first: the install layer only invalidates when deps actually change.
# If packages/ ever gains a member, its package.json must be added here too — otherwise a
# frozen install succeeds locally and fails inside the image.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/
RUN pnpm install --frozen-lockfile --filter ipg-sandbox-web...

COPY apps/web apps/web
# NEXT_PUBLIC_* is inlined at BUILD time, so it must arrive as a build arg — a runtime
# compose `environment:` entry is invisible to the already-built bundle.
ARG NEXT_PUBLIC_API_URL=http://localhost:8080
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN pnpm --filter ipg-sandbox-web build

WORKDIR /repo/apps/web
EXPOSE 3000
CMD ["pnpm", "start"]
