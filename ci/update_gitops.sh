#!/bin/sh
set -eu

: "${CI_JOB_TOKEN:?Missing CI_JOB_TOKEN}"
: "${CI_PROJECT_DIR:?Missing CI_PROJECT_DIR}"
: "${CI_DEFAULT_BRANCH:?Missing CI_DEFAULT_BRANCH}"
: "${CI_COMMIT_SHA:?Missing CI_COMMIT_SHA}"
: "${CI_COMMIT_SHORT_SHA:?Missing CI_COMMIT_SHORT_SHA}"
: "${CI_PIPELINE_URL:?Missing CI_PIPELINE_URL}"
: "${GITOPS_REPO_URL:?Missing GITOPS_REPO_URL}"
: "${IMAGE_REPOSITORY:?Missing IMAGE_REPOSITORY}"
: "${IMAGE_DIGEST:?Missing IMAGE_DIGEST}"

# Ignore an older pipeline if the default branch has already moved forward.
LATEST_SOURCE_REF=$(git ls-remote origin "refs/heads/$CI_DEFAULT_BRANCH")
LATEST_SOURCE_SHA=$(printf '%s\n' "$LATEST_SOURCE_REF" | awk '{print $1}')
if [ "$LATEST_SOURCE_SHA" != "$CI_COMMIT_SHA" ]; then
    echo "Skipping GitOps update: the application branch has a newer commit."
    exit 0
fi

umask 077
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT
trap 'exit 1' HUP INT TERM
export GIT_TERMINAL_PROMPT=0
export LC_ALL=C
export GIT_ASKPASS="$WORK_DIR/askpass.sh"

# Keep the token out of the remote URL, Git configuration and command arguments.
cat > "$GIT_ASKPASS" <<'ASKPASS'
#!/bin/sh
case "$1" in
    *Username*) printf '%s\n' 'gitlab-ci-token' ;;
    *Password*) printf '%s\n' "$CI_JOB_TOKEN" ;;
    *) exit 1 ;;
esac
ASKPASS
chmod 700 "$GIT_ASKPASS"

GITOPS_DIR="$WORK_DIR/gitops"
git -c credential.helper= clone --single-branch --branch main \
    "$GITOPS_REPO_URL" "$GITOPS_DIR"

python3 "$CI_PROJECT_DIR/ci/update_staging_image.py" \
    "$GITOPS_DIR" "$IMAGE_REPOSITORY" "$IMAGE_DIGEST"

if git -C "$GITOPS_DIR" diff --quiet -- overlays/staging/kustomization.yaml; then
    echo "No deployment change needed."
    exit 0
fi

git -C "$GITOPS_DIR" config user.name "DevOps Lab CI"
git -C "$GITOPS_DIR" config user.email "devops-lab-ci@noreply.gitlab.com"
git -C "$GITOPS_DIR" add overlays/staging/kustomization.yaml
git -C "$GITOPS_DIR" commit \
    -m "Update staging image for $CI_COMMIT_SHORT_SHA" \
    -m "Source pipeline: $CI_PIPELINE_URL"

# A normal push rejects conflicting remote updates instead of overwriting them.
git -C "$GITOPS_DIR" -c credential.helper= push origin HEAD:main
