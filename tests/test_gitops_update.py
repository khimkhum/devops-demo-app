from pathlib import Path
import os
import shutil
import subprocess

import pytest

from ci.update_staging_image import update_staging_image


REPOSITORY = "192.168.1.32:8443/intern/devops-demo"
OLD_DIGEST = "sha256:" + "a" * 64
NEW_DIGEST = "sha256:" + "b" * 64


def manifest(digest):
    return (
        "apiVersion: kustomize.config.k8s.io/v1beta1\n"
        "kind: Kustomization\n"
        "images:\n"
        f"  - name: {REPOSITORY}\n"
        f"    digest: {digest}\n"
    )


def prepare_overlays(root):
    for environment in ("staging", "prod"):
        path = root / "overlays" / environment / "kustomization.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(manifest(OLD_DIGEST))
    return root / "overlays/staging/kustomization.yaml"


def test_updates_staging_without_changing_prod(tmp_path):
    staging = prepare_overlays(tmp_path)
    assert update_staging_image(tmp_path, REPOSITORY, NEW_DIGEST)
    assert NEW_DIGEST in staging.read_text()
    assert OLD_DIGEST in (tmp_path / "overlays/prod/kustomization.yaml").read_text()
    assert not update_staging_image(tmp_path, REPOSITORY, NEW_DIGEST)


@pytest.mark.parametrize("digest", ["latest", "sha256:short", "sha256:" + "G" * 64])
def test_rejects_invalid_digest_without_writing(tmp_path, digest):
    staging = prepare_overlays(tmp_path)
    before = staging.read_bytes()
    with pytest.raises(ValueError):
        update_staging_image(tmp_path, REPOSITORY, digest)
    assert staging.read_bytes() == before


def test_rejects_missing_or_duplicate_image_entries(tmp_path):
    staging = prepare_overlays(tmp_path)
    for text in ("images: []\n", manifest(OLD_DIGEST) * 2):
        staging.write_text(text)
        with pytest.raises(ValueError):
            update_staging_image(tmp_path, REPOSITORY, NEW_DIGEST)
        assert staging.read_text() == text


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True, stderr=subprocess.STDOUT
    ).strip()


def init_repo(path):
    path.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main", str(path)],
        check=True, capture_output=True, text=True,
    )
    git(path, "config", "user.name", "Test")
    git(path, "config", "user.email", "test@example.invalid")


def test_gitops_job_push_is_idempotent_and_skips_stale_pipeline(tmp_path):
    # Use disposable local repositories; no GitLab credentials or network.
    seed = tmp_path / "seed"
    init_repo(seed)
    prepare_overlays(seed)
    git(seed, "add", ".")
    git(seed, "commit", "-m", "Initial overlays")
    remote = tmp_path / "gitops.git"
    subprocess.run(
        ["git", "clone", "--bare", str(seed), str(remote)],
        check=True, capture_output=True, text=True,
    )

    source = tmp_path / "source"
    init_repo(source)
    project = Path(__file__).resolve().parents[1]
    shutil.copytree(project / "ci", source / "ci", ignore=shutil.ignore_patterns("__pycache__"))
    git(source, "add", ".")
    git(source, "commit", "-m", "Application")
    source_remote = tmp_path / "source.git"
    subprocess.run(
        ["git", "clone", "--bare", str(source), str(source_remote)],
        check=True, capture_output=True, text=True,
    )
    git(source, "remote", "add", "origin", str(source_remote))
    source_sha = git(source, "rev-parse", "HEAD")

    env = os.environ.copy()
    env.update(
        CI_JOB_TOKEN="dummy-test-token",
        CI_PROJECT_DIR=str(source),
        CI_DEFAULT_BRANCH="main",
        CI_COMMIT_SHA=source_sha,
        CI_COMMIT_SHORT_SHA=source_sha[:8],
        CI_PIPELINE_URL="https://example.invalid/pipelines/1",
        GITOPS_REPO_URL=str(remote),
        IMAGE_REPOSITORY=REPOSITORY,
        IMAGE_DIGEST=NEW_DIGEST,
    )

    def run_job():
        return subprocess.run(
            ["sh", "ci/update_gitops.sh"], cwd=source, env=env,
            check=True, capture_output=True, text=True,
        )

    run_job()
    committed = git(remote, "rev-parse", "main")
    assert NEW_DIGEST in git(remote, "show", "main:overlays/staging/kustomization.yaml")
    assert OLD_DIGEST in git(remote, "show", "main:overlays/prod/kustomization.yaml")

    run_job()
    assert git(remote, "rev-parse", "main") == committed

    git(source, "commit", "--allow-empty", "-m", "Newer application commit")
    git(source, "push", "origin", "main")
    env["IMAGE_DIGEST"] = "sha256:" + "c" * 64
    assert "Skipping GitOps update" in run_job().stdout
    assert git(remote, "rev-parse", "main") == committed
