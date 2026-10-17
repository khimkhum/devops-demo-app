# Khiem Lab

Ứng dụng Flask dùng cho project DevOps internship.
Giao diện chuyển thể từ [Tooplate Neon Carbon](https://www.tooplate.com/view/2165-neon-carbon).
[Điều khoản sử dụng Tooplate](https://www.tooplate.com/about).

## Chạy trong Ubuntu WSL

```bash
cd /mnt/f/devops-intern-lab/devops-demo-app
source ~/.venvs/devops-demo/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Mở http://localhost:8000. Dừng bằng Ctrl+C.

## Thay cấu hình

```bash
APP_VERSION=v2 APP_ENV=staging python app.py
```

`/` trả HTML; `/health` và `/version` trả JSON.
Nút kiểm tra API gọi `/health` thật. Lịch sử chỉ lưu trong phiên trình duyệt.
Các phần Docker, CI, Kubernetes và GitOps chưa được triển khai.
Khi triển khai container sẽ dùng Gunicorn thay development server.

## Health check

Run: `bash scripts/check-health.sh http://127.0.0.1:8000`

## Database failure and recovery

- Database running: /health = 200, /ready = 200.
- Database stopped: /health = 200, /ready = 503.
- Database restarted: /ready returns 200 without restarting the app.
- Commands: docker compose stop db; docker compose start db.

## Run with Docker Compose

Prerequisites: Docker Engine and Docker Compose.

1. Copy `.env.example` to `.env`.
2. Replace the sample database password with a local password.
3. Run:

```bash
docker compose up -d --build
```

Open http://localhost:8084.

Endpoints:
- `/health`: HTTP application health.
- `/ready`: PostgreSQL connection and SQL query check.
- `/version`: application version and environment.

## Verified behavior

- The app runs as a non-root user.
- The Dockerfile uses a multi-stage build.
- With PostgreSQL stopped, `/health` returns 200 and `/ready` returns 503.
- After PostgreSQL restarts, `/ready` returns 200 without restarting the app.
- A database record survives `docker compose down` followed by `docker compose up -d`.

## Stop the environment

```bash
docker compose down
```

Named volumes are retained. Adding `-v` deletes the Compose named volumes.

## Deploy from Harbor

The application image is stored in a private Harbor project.
The deployment configuration pins the image by digest.

Prerequisites:
- Docker and Docker Compose.
- A running Harbor registry reachable at the configured address.
- The Harbor CA trusted by Docker Engine.
- Registry credentials with pull permission.
- A local `.env` file based on `.env.example`.

Authenticate interactively with a Harbor robot account:

```bash
docker login 192.168.1.31:8443 -u 'robot$intern+deploy-pull'
```

Pull and deploy the application:

```bash
docker compose -f compose.yaml -f compose.harbor.yaml pull app
docker compose -f compose.yaml -f compose.harbor.yaml up -d --no-build app
```

Verify:

```bash
bash scripts/check-health.sh http://127.0.0.1:8084
curl -i http://127.0.0.1:8084/ready
curl http://127.0.0.1:8084/version
```

Verified results:
- The application container references the Harbor image by digest.
- `/health` returns 200.
- `/ready` returns 200 after querying PostgreSQL.
- `/version` reports version `v4` and environment `harbor-lab`.

## Lab limitations

This is a local lab. The registry uses a private LAN IP and a private CA.
Other machines must have network access and trust the CA before pulling images.
Registry credentials and private keys are not included in this repository.

Kubernetes, GitLab CI and Argo CD are not implemented yet.
