# Runbook — vận hành, promotion và rollback

**Phase 6. Nơi chạy:** Ubuntu WSL; các thao tác Sync ghi rõ chạy trong trình duyệt
Argo CD. Checkout ứng dụng là `/mnt/f/devops-intern-lab/devops-demo-app`;
checkout GitOps là `/mnt/f/devops-intern-lab/devops-demo-gitops`.
Các lệnh dưới đây thao tác cluster `k3d-intern-lab`.

## 1. Kiểm tra đầu buổi

Mở Docker Desktop trên Windows và chờ engine sẵn sàng. Sau đó trong WSL:

```bash
docker version
k3d cluster list
kubectl --context k3d-intern-lab get nodes
kubectl --context k3d-intern-lab -n argocd get applications
kubectl --context k3d-intern-lab -n staging get pods,pvc
kubectl --context k3d-intern-lab -n prod get pods,pvc
```

Nếu cluster đang Stopped, dùng `k3d cluster start intern-lab`.
Harbor nằm ngoài repo; nếu đã dừng, chạy tại thư mục installer:

```bash
cd ~/devops-intern-lab/infra/harbor
sudo docker compose up -d
sudo docker compose ps
```

Các file env do Harbor sinh được bảo vệ quyền truy cập. Dùng sudo cho Compose
tại đây; không sửa cả cây thành chmod 777 để né lỗi permission.

Runner:

```bash
cd /mnt/f/devops-intern-lab/devops-demo-app
docker compose -f infra/gitlab-runner/compose.yaml up -d
docker compose -f infra/gitlab-runner/compose.yaml exec runner gitlab-runner verify
```

Nếu Docker chỉ in Client hoặc thiếu socket, kiểm tra Docker Desktop và Ubuntu WSL
Integration trước. Không cài thêm một Docker daemon Ubuntu để xử lý nhầm engine.

## 2. Kiểm tra dịch vụ và đúng môi trường

```bash
curl -fsS --max-time 10 http://127.0.0.1:8088/health
curl -fsS --max-time 10 http://127.0.0.1:8088/ready
curl -fsS --max-time 10 http://127.0.0.1:8088/version

curl -fsS --max-time 10 \
  --resolve prod.devops.test:8088:127.0.0.1 \
  http://prod.devops.test:8088/ready

curl -fsS --max-time 10 \
  --resolve prod.devops.test:8088:127.0.0.1 \
  http://prod.devops.test:8088/version
```

Staging phải trả environment=staging, prod phải trả environment=prod.
Nếu Ingress prod bị thiếu, host prod có thể rơi vào route staging không khai báo
host và vẫn trả HTTP 200. Vì vậy HTTP 200 riêng lẻ chưa chứng minh đúng môi trường.

Đọc image thực tế mà không in Secret:

```bash
kubectl --context k3d-intern-lab -n staging get deployment devops-demo \
  -o jsonpath='{.spec.template.spec.containers[0].image}'
echo
kubectl --context k3d-intern-lab -n prod get deployment devops-demo \
  -o jsonpath='{.spec.template.spec.containers[0].image}'
echo
```

## 3. Chờ đúng commit, không chỉ chờ Healthy

Tại checkout GitOps, sau khi CI update thành công:

```bash
git status --short
git pull --ff-only origin main
GITOPS_REVISION=$(git rev-parse HEAD)

kubectl --context k3d-intern-lab -n argocd annotate \
  application devops-demo-staging \
  argocd.argoproj.io/refresh=hard --overwrite

kubectl --context k3d-intern-lab -n argocd wait \
  --for=jsonpath='{.status.sync.revision}'="$GITOPS_REVISION" \
  application/devops-demo-staging --timeout=180s

kubectl --context k3d-intern-lab -n argocd wait \
  --for=jsonpath='{.status.sync.status}'=Synced \
  application/devops-demo-staging --timeout=180s

kubectl --context k3d-intern-lab -n staging rollout status \
  deployment/devops-demo --timeout=180s

kubectl --context k3d-intern-lab -n argocd get applications
```

Nếu local có thay đổi chưa commit, xử lý chúng trước khi pull; không reset --hard.
Đối chiếu image digest thực tế với overlay và gọi /ready.
Healthy có thể mô tả tài nguyên cũ khi revision mới chưa được triển khai.
Synced mô tả độ khớp cấu hình; Healthy mô tả sức khỏe tài nguyên.

## 4. Promote chính image staging sang prod

**Phase 6 — Release. Checkout GitOps.**

1. Đợi pipeline mới nhất pass, staging đúng digest và /ready=200.
2. `git pull --ff-only origin main`; mở hai overlay bằng Vim.
3. Sao chép **digest đã kiểm tra ở staging** vào entry image của prod.
   Không rebuild một image khác cho prod.
4. Review diff: chỉ thay digest prod; không sửa staging, Secret hoặc database.

```bash
vim overlays/staging/kustomization.yaml overlays/prod/kustomization.yaml
kubectl kustomize overlays/prod > /tmp/devops-prod.yaml
kubectl --context k3d-intern-lab apply --dry-run=server -k overlays/prod

git diff -- overlays/prod/kustomization.yaml
git add overlays/prod/kustomization.yaml
git diff --cached --check &&
git commit -m "Promote validated staging image to production" &&
git push origin main
```

**Trình duyệt Argo CD:** mở devops-demo-prod, Refresh, kiểm tra Diff, chọn Sync
toàn bộ tài nguyên cần triển khai. Để **Force, Replace và Prune tắt**.
Kiểm tra revision đích rồi Synchronize.

Sau Sync, tại WSL:

```bash
kubectl --context k3d-intern-lab -n prod rollout status \
  deployment/devops-demo --timeout=180s
kubectl --context k3d-intern-lab -n argocd get applications
```

Đối chiếu revision prod với commit promotion, digest Deployment với overlay,
và lặp lại /ready, /version cùng kiểm tra nội dung giao diện.
Không kết luận chỉ từ operationState=Succeeded vì đó có thể là operation cũ.

## 5. Rollback có lịch sử Git

Chọn đúng commit đưa image lỗi vào môi trường, xem diff trước khi revert.
Ví dụ thao tác, thay placeholder bằng SHA thực tế đã review:

```bash
git pull --ff-only origin main
git log --oneline -8
git show <bad-release-commit>
git revert <bad-release-commit>
git diff --check
git push origin main
```

Trong Vim khi Git mở commit message: giữ message phù hợp, Esc rồi :wq.
Revert tạo commit mới, giữ lịch sử; không xóa commit cũ và không force push.
Nếu có conflict, xử lý từng hunk và review overlay sau cùng.

Staging auto-sync; prod cần manual Sync sau rollback commit. Đợi đúng revision,
đúng digest, rollout hoàn tất và /ready=200 như trên.
Không chỉ dùng `kubectl rollout undo` trên tài nguyên Argo quản lý:
self-heal có thể khôi phục lại image đang ghi trong Git.

Image rollback không tự rollback schema hay dữ liệu PostgreSQL.
Project chưa triển khai migration hoặc kiểm thử khôi phục database backup.

## 6. Khi rollout lỗi

Bắt đầu từ tài nguyên thật, không sửa ngẫu nhiên:

```bash
kubectl --context k3d-intern-lab -n staging get pods -o wide
kubectl --context k3d-intern-lab -n staging describe deployment devops-demo
kubectl --context k3d-intern-lab -n staging get events \
  --sort-by=.metadata.creationTimestamp
kubectl --context k3d-intern-lab -n staging logs \
  -l app=devops-demo --all-containers=true --tail=80 --prefix=true
```

Với Pod lỗi cụ thể: `kubectl ... describe pod POD_NAME`,
`kubectl ... logs POD_NAME --previous`.
Thay POD_NAME bằng tên trong get pods; không gõ dấu ngoặc placeholder nguyên xi.

| Triệu chứng | Kiểm tra tiếp |
|---|---|
| Pending | Events: quota, requests, node capacity, PVC |
| ImagePullBackOff | Digest tồn tại, registry reachable, CA, harbor-pull cùng namespace |
| CrashLoopBackOff | Logs/previous, command, dependency import, file permissions |
| Running nhưng 0/1 Ready | Readiness, database, Secret key, Service/DNS |
| 502 khi rollout | EndpointSlice, readiness, termination/drain, Ingress logs |
| Argo OutOfSync | Diff và revision; prod có thể đang chờ manual Sync |
| Argo Degraded | Resource gây lỗi; build pass không đủ chứng minh runtime đúng |

Không in Secret YAML/data, toàn bộ env container hay Runner config khi thu thập log.

### Incident đã gặp: umask 077

Kaniko build thành công nhưng package Gunicorn có thư mục root mode 700.
Runtime appuser UID 10001 không import được gunicorn.app. Pod mới crash,
Deployment vượt progress deadline; hai replica cũ vẫn phục vụ.

- Khoanh vùng: so sánh import bằng root và bằng appuser; kiểm tra quyền package.
- Khôi phục: revert commit GitOps trỏ image lỗi, Argo về image tốt.
- Sửa: credentials giữ umask 077; đổi lại 022 trước build; tạo venv và pip
  với quyền đọc bình thường; Dockerfile kiểm tra import sau USER appuser.
- Xác minh: Kaniko build, chạy Gunicorn thật với user 10001, HTTP health=200,
  CI xanh và rollout staging/prod thành công.

Một thử nghiệm drain sau sửa đã ghi 60/60 request thành công. Đây là quan sát
giới hạn của bài lab, không phải bảo đảm không gián đoạn trong mọi điều kiện.

## 7. Lỗi thường gặp tại máy

- curl exit 7: chưa kết nối được; kiểm tra process/port/địa chỉ.
- curl exit 28: hết timeout; xem logs và thời gian xử lý, không kết luận ngay sai token.
- HTTP 404: đã tới HTTP server nhưng sai route; curl chỉ exit 22 khi có --fail/-f.
- x509 unknown authority: CA chưa được client đó tin cậy.
- Certificate IP mismatch: SAN chưa chứa IP đang dùng.
- Harbor IP đổi: xử lý đồng bộ theo SETUP, không tắt TLS để vượt lỗi.
- Git push HTTPS hỏi password: nhập PAT ở prompt; GitHub/GitLab dùng token riêng,
  không dùng password tài khoản và không đặt token vào remote URL.
- Cache "No URL provided": Runner đang giữ cache cục bộ, không phải job failure.
- Artifacts 201 Created: coordinator đã nhận report/artifact.
- ^M/trailing whitespace: Vim dùng :set fileformat=unix rồi :wq,
  git add lại và git diff --cached --check. .gitattributes quy định LF.
- App local port occupied: kiểm tra ss -ltnp trước; không kill process chưa xác định.

Dừng Compose không thêm -v nếu muốn giữ database. Không xóa namespace,
PVC hoặc cluster để sửa một rollout ứng dụng.
