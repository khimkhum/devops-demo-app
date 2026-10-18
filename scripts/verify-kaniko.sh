#!/usr/bin/env bash
set -euo pipefail
umask 077

PROJECT_DIR="$(git rev-parse --show-toplevel)"
cd "$PROJECT_DIR"

REGISTRY="192.168.1.31:8443"
IMAGE_REPOSITORY="$REGISTRY/intern/devops-demo"
COMMIT_SHA="$(git rev-parse HEAD)"
IMAGE_TAG="kaniko-$COMMIT_SHA"

KANIKO_IMAGE="ghcr.io/osscontainertools/kaniko:v1.28.6-debug@sha256:7ab44d0131c3051b6dea128067e258c7afb5c4815082a93b9cf6c624f2140bf0"
CA_FILE="$HOME/devops-intern-lab/infra/harbor-certs/ca.crt"

test -r "$CA_FILE"

mkdir -p "$HOME/devops-intern-lab/infra/kaniko-runs"
LAB_DIR="$(mktemp -d "$HOME/devops-intern-lab/infra/kaniko-runs/run.XXXXXX")"
trap 'rm -rf -- "$LAB_DIR"' EXIT

mkdir -p "$LAB_DIR/context" "$LAB_DIR/auth" "$LAB_DIR/output"

# Build exactly the files stored in the current commit.
git archive HEAD | tar -x -C "$LAB_DIR/context"

read -rsp 'Nhap token Harbor robot ci-push: ' HARBOR_TOKEN
printf '\n'
: "${HARBOR_TOKEN:?Token must not be empty}"

AUTH="$(printf '%s:%s' 'robot$intern+ci-push' "$HARBOR_TOKEN" |
  base64 | tr -d '\n')"

printf '{"auths":{"%s":{"auth":"%s"}}}\n' \
  "$REGISTRY" "$AUTH" \
  > "$LAB_DIR/auth/config.json"

unset AUTH HARBOR_TOKEN

printf 'Building commit: %s\n' "$COMMIT_SHA"
printf 'Destination: %s:%s\n' "$IMAGE_REPOSITORY" "$IMAGE_TAG"

docker run --rm \
  --volume "$LAB_DIR/context:/workspace:ro" \
  --volume "$LAB_DIR/auth:/kaniko/.docker:ro" \
  --volume "$CA_FILE:/certs/harbor-ca.crt:ro" \
  --volume "$LAB_DIR/output:/out" \
  "$KANIKO_IMAGE" \
  --context dir:///workspace \
  --dockerfile /workspace/Dockerfile \
  --destination "$IMAGE_REPOSITORY:$IMAGE_TAG" \
  --registry-certificate "$REGISTRY=/certs/harbor-ca.crt" \
  --cache=true \
  --cache-repo "$REGISTRY/intern/devops-demo-cache" \
  --cache-ttl=168h \
  --compressed-caching=false \
  --label "org.opencontainers.image.revision=$COMMIT_SHA" \
  --digest-file /out/image.digest \
  --push-retry=3

mkdir -p "$PROJECT_DIR/reports"
cp "$LAB_DIR/output/image.digest" \
  "$PROJECT_DIR/reports/kaniko-local.digest"

printf '%s@%s\n' \
  "$IMAGE_REPOSITORY" \
  "$(cat "$LAB_DIR/output/image.digest")" \
  > "$PROJECT_DIR/reports/kaniko-local.image"

printf 'PASS: Kaniko build and push completed.\n'
cat "$PROJECT_DIR/reports/kaniko-local.image"
