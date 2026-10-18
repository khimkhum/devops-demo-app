# Setup and prerequisites

All shell commands below run in **Ubuntu WSL**, unless marked otherwise.
The verified installation uses Docker Desktop with Ubuntu WSL integration.
The Compose quickstart in the root README is the shortest reproducible application demo.
Reproducing the entire CI/CD lab additionally requires the external services below.

## 1. Tools and directories

Observed versions on 2026-10-18, recorded for reproducibility rather than as
a recommendation to install the newest release:

| Tool | Observed version |
|---|---|
| Docker Desktop / Engine | 4.95.0 / 29.8.2 |
| Compose / WSL | 5.6.0 / 2.7.3 |
| Python | 3.14 |
| k3d / K3s / kubectl | 5.9.0 / 1.35.5-k3s1 / 1.35.5 |
| Harbor / GitLab Runner | 2.15.4 / 19.5.0 |
| Argo CD | 3.5.5 |
| Kaniko community fork | 1.28.6-debug, pinned by digest in CI |

On this machine, application files are at
`F:\devops-intern-lab\devops-demo-app` in Windows and
`/mnt/f/devops-intern-lab/devops-demo-app` in WSL.
The GitOps checkout is its sibling `devops-demo-gitops`.
Private infrastructure files live under
`~/devops-intern-lab/infra/` in the Ubuntu filesystem.

Check prerequisites:

```bash
docker version
docker compose version
k3d version
kubectl version --client
```

Match kubectl to a supported server version. This lab explicitly selected
`~/.local/bin/kubectl` 1.35.5 via PATH. The Windows named-pipe
Docker context is not usable from Linux; WSL uses the Unix socket integration.

## 2. External Harbor registry

Install Harbor separately using its versioned official installer. This repository
does not contain Harbor's generated configuration, data, passwords or certificates.

For the recorded lab:

- HTTPS registry: `192.168.1.32:8443`; private project: `intern`.
- Server certificate SAN must contain that IP; its issuing private CA is trusted.
- Private CA certificate:
  `~/devops-intern-lab/infra/harbor-certs/ca.crt`.
- Push robot: `robot$intern+ci-push`; deployment robot:
  `robot$intern+deploy-pull` with pull permission only.
- Runner and Kubernetes node must reach this address.

Verify the server before configuring CI:

```bash
curl --cacert "$HOME/devops-intern-lab/infra/harbor-certs/ca.crt" \
  --connect-timeout 3 --max-time 10 \
  https://192.168.1.32:8443/api/v2.0/ping

docker login 192.168.1.32:8443 -u 'robot$intern+deploy-pull'
```

Expected: Pong and Login Succeeded. A 401 from an unauthenticated
`/v2/` is the normal registry authentication challenge.

Trust the CA separately in the Docker Desktop engine, K3s/containerd node and
Kaniko job. Trust in one client does not automatically configure the others.
Do not replace verification with an insecure-registry setting.

Use a DHCP reservation or stable address. If the IP changes, update the server
certificate SAN, Harbor hostname, clients, CI variable, cluster registry config,
image references and image-pull credentials together.

References: [Harbor HTTPS](https://goharbor.io/docs/main/install-config/configure-https/),
[Docker registry certificates](https://docs.docker.com/engine/network/ca-certs/).

## 3. Fresh Kubernetes cluster

From the application checkout, review the machine-specific CA mount and registry
address in `infra/k3d/cluster.yaml` with Vim before creating a
**fresh** cluster:

```bash
vim infra/k3d/cluster.yaml
k3d cluster create --config infra/k3d/cluster.yaml
kubectl --context k3d-intern-lab wait \
  --for=condition=Ready nodes --all --timeout=180s
kubectl --context k3d-intern-lab get nodes -o wide
kubectl --context k3d-intern-lab get storageclass
```

Do not recreate an existing cluster to refresh application code. This configuration
uses one K3s server, Traefik, local-path storage, API port 6550 and Ingress port 8088.
Its default datastore is SQLite. See [K3s datastore options](https://docs.k3s.io/datastore).

## 4. Provision namespace Secrets outside Git

Clone the separate GitOps repository using an account with access, then:

```bash
cd /mnt/f/devops-intern-lab/devops-demo-gitops
kubectl --context k3d-intern-lab apply -f overlays/staging/namespace.yaml
kubectl --context k3d-intern-lab apply -f overlays/prod/namespace.yaml
```

Each namespace requires:

| Secret | Type | Required keys |
|---|---|---|
| db-credentials | Opaque | POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD |
| harbor-pull | kubernetes.io/dockerconfigjson | .dockerconfigjson |

Keep staging and prod database credentials separate. Prepare permission-600
environment files outside both repositories with Vim. For example, after preparing
`~/.config/devops-lab/staging-db.env`:

```bash
kubectl --context k3d-intern-lab -n staging create secret generic db-credentials \
  --from-env-file="$HOME/.config/devops-lab/staging-db.env" \
  --dry-run=client -o yaml |
kubectl --context k3d-intern-lab apply -f -
```

Repeat for prod with its own namespace and file. Never commit the generated YAML.

To avoid placing the robot token in a command argument, log in using a temporary
Docker config directory; type the token at Docker's password prompt:

```bash
REGISTRY_CONFIG=$(mktemp -d)
chmod 700 "$REGISTRY_CONFIG"
docker --config "$REGISTRY_CONFIG" login \
  192.168.1.32:8443 -u 'robot$intern+deploy-pull'
```

Only continue after login succeeds:

```bash
for namespace in staging prod; do
  kubectl --context k3d-intern-lab -n "$namespace" create secret generic harbor-pull \
    --type=kubernetes.io/dockerconfigjson \
    --from-file=.dockerconfigjson="$REGISTRY_CONFIG/config.json" \
    --dry-run=client -o yaml |
  kubectl --context k3d-intern-lab apply -f -
done
rm -f -- "$REGISTRY_CONFIG/config.json"
rmdir -- "$REGISTRY_CONFIG"
unset REGISTRY_CONFIG
```

This assumes the fresh temporary config contains inline registry authentication.
Do not display it. Check Secret names/types with `kubectl get secrets`.

Changing a PostgreSQL initialization password after its data directory exists does
not reset the database role password. Plan an explicit SQL password rotation and
application configuration update instead of deleting the PVC.

## 5. GitLab Runner and CI

In the **GitLab application project browser UI**, create a project Runner tagged
`intern-lab`. Protect the default branch used for publishing.
On the local trusted machine:

```bash
cd /mnt/f/devops-intern-lab/devops-demo-app
docker compose -f infra/gitlab-runner/compose.yaml up -d
docker compose -f infra/gitlab-runner/compose.yaml exec runner gitlab-runner register
```

Register interactively with GitLab.com, the Runner authentication token, Docker
executor and a default image such as python:3.14-slim. The Docker executor needs
the engine socket available to launch job containers; Kaniko builds inside its job
without mounting that socket into the build job. Do not enable privileged jobs.
The Runner configuration is stored in a named volume, outside Git.

The Runner process has Docker socket access: use it for this trusted personal lab,
not arbitrary untrusted projects.

Verify registration:

```bash
docker compose -f infra/gitlab-runner/compose.yaml exec runner gitlab-runner verify
```

In application project Settings > CI/CD > Variables:

| Variable | Value / handling |
|---|---|
| HARBOR_USERNAME | Push robot username; disable expansion because it contains $ |
| HARBOR_PASSWORD | Robot token; protected, masked/hidden; expansion disabled |
| HARBOR_CA_CRT | File variable containing the public CA certificate; protected |

Registry address and target GitOps URL are ordinary variables in CI YAML.
Protected variables require a protected publishing branch.
Set target GitOps job-token permissions as described in
[gitops-ci.md](gitops-ci.md); the existing CI job token is supplied automatically.

## 6. Argo CD bootstrap

The application repo pins the installation manifest to Argo CD 3.5.5:

```bash
kubectl --context k3d-intern-lab apply -k infra/argocd/
kubectl --context k3d-intern-lab -n argocd rollout status \
  deployment/argocd-server --timeout=180s
kubectl --context k3d-intern-lab -n argocd port-forward \
  --address 127.0.0.1 svc/argocd-server 8090:443
```

Keep port-forward running in its own terminal. Open https://localhost:8090.
The default server uses a self-signed certificate. Obtain the initial local
admin credential according to the
[official getting-started guide](https://argo-cd.readthedocs.io/en/stable/getting_started/);
do not paste it into chat or record it in Git.

In Argo CD Settings > Repositories, connect the GitOps repository using a read-only
GitLab Deploy Token with read_repository. Configure the credential in Argo CD,
not in an Application YAML file. Then, from the GitOps checkout:

```bash
kubectl kustomize overlays/staging > /tmp/devops-staging.yaml
kubectl kustomize overlays/prod > /tmp/devops-prod.yaml
kubectl --context k3d-intern-lab apply --dry-run=server -f argocd/applications.yaml
kubectl --context k3d-intern-lab apply -f argocd/applications.yaml
```

Staging syncs automatically. Deploy prod using a reviewed manual Sync with
Force, Replace and Prune disabled. Follow the
[runbook](RUNBOOK.md) for verification and later promotions.
