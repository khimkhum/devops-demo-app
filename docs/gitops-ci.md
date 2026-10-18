# Automatic staging deployment

The application pipeline has three stages:

1. `test`: run pytest and upload the JUnit report.
2. `build`: build the non-root runtime with Kaniko, push to Harbor and export
   `IMAGE_REPOSITORY`, `IMAGE_DIGEST` and `IMAGE_REF` as a dotenv artifact.
3. `gitops`: update only `overlays/staging/kustomization.yaml` in the GitOps
   repository and push a normal Git commit.

Argo CD reads that commit and automatically reconciles staging. Production keeps
its existing digest and requires a separate promotion commit plus manual Argo CD
Sync. CI does not receive Kubernetes credentials.

## Required GitLab settings

In the **target** project `levankhiem0000/devops-demo-gitops`:

- Open Settings > CI/CD > Job token permissions.
- Enable Allow Git push requests to the repository.
- Enable Allow cross-project Git push requests from allowlisted projects.
- Add `levankhiem0000/devops-demo-app` to the CI/CD job token allowlist.
- Give that entry Repositories: Read and write (`ADMIN_REPOSITORIES`), or
  leave its default permissions without fine-grained restrictions.
- Ensure the user starting the application pipeline can push to protected
  `main` in the target project.

This uses the temporary `CI_JOB_TOKEN` automatically supplied by GitLab.
No extra personal access token or new CI secret variable is required. Cross-project
job-token push requires GitLab 19.1 or newer.

## Deployment controls

- Only the application's default-branch pipeline can run the update job.
- A resource group serializes staging updates from this project.
- An older pipeline is skipped if the application default branch has moved.
- Invalid digests or ambiguous manifest entries fail without changing the file.
- An identical digest produces no extra commit.
- A normal push rejects a concurrent conflicting GitOps update; it never force pushes.
  If this happens, rerun the latest pipeline's update job after reviewing the remote.
- The token is passed through an ephemeral askpass helper, not embedded in a URL.
- The script modifies staging only. Production promotion remains explicit.

After CI updates the remote GitOps repository, refresh your local checkout before
editing it:

```bash
git pull --ff-only origin main
```

## Validation status

Local tests cover valid and invalid digest handling, staging/prod separation,
a real commit and push to disposable Git repositories, idempotence and stale
pipeline rejection. The cross-project GitLab permission settings and full
three-stage pipeline still require a live run.
