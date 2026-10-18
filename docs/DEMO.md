# Demo phỏng vấn: code → staging → prod

**Phase 6. Nơi chạy:** Ubuntu WSL và trình duyệt GitLab/Argo CD.
Dự trù 10–15 phút khi image đã cache; thời gian CI và mạng có thể dài hơn.
Chuẩn bị sẵn lab hoạt động và tài liệu dự phòng [EVIDENCE](EVIDENCE.md).

## 1. Trình bày kiến trúc trong một phút

"Em xây ứng dụng Flask với PostgreSQL. GitLab Runner chạy test, Kaniko build image
và đẩy lên Harbor. Job cuối lấy digest cập nhật repo GitOps riêng. Argo CD tự đồng
bộ staging; prod cần commit promotion và Sync thủ công. CI không có kubeconfig."

Chỉ sơ đồ README và ba job thật trên GitLab.
Giải thích hai replica cùng node giúp rollout, không tạo node-level HA.

## 2. Ghi nhận trạng thái ban đầu

Từ checkout GitOps:

```bash
cd /mnt/f/devops-intern-lab/devops-demo-gitops
git pull --ff-only origin main
kubectl --context k3d-intern-lab -n argocd get applications
kubectl --context k3d-intern-lab -n prod get deployment devops-demo \
  -o jsonpath='{.spec.template.spec.containers[0].image}'
echo
```

Lưu digest prod hiện tại trong ghi chú demo. Mở staging và prod để so sánh.
Nếu dùng trình duyệt Windows, thêm tên prod.devops.test vào hosts theo chính sách
máy; nếu chưa cấu hình, dùng curl --resolve như runbook, không cần mua domain.

## 3. Tạo thay đổi nhìn thấy được

```bash
cd /mnt/f/devops-intern-lab/devops-demo-app
vim templates/index.html
```

Đổi một dòng mô tả dễ nhận biết, ví dụ thêm "Release demo 02".
Không đổi Secret hoặc thông số database để demo phát hành.

```bash
git diff -- templates/index.html
git add templates/index.html
git diff --cached --check &&
git commit -m "Update dashboard release demo" &&
git push gitlab master
```

Trong GitLab mở pipeline cho đúng commit vừa push. Trình bày:

1. unit_test: 14 test, JUnit hiển thị trong Tests.
2. build_image: Kaniko build/push, image tag theo commit, artifact digest.
3. update_staging: commit digest vào repo GitOps bằng CI_JOB_TOKEN.

Nếu job lỗi, đọc job log và xử lý nguyên nhân; không bỏ qua để tiếp tục promotion.

## 4. Staging nhận code; prod giữ bản cũ

Tại checkout GitOps, pull rồi chạy phần "Chờ đúng commit" trong RUNBOOK.
Đối chiếu staging Deployment image với digest mới trong overlay, gọi /ready,
và kiểm tra dòng HTML mới bằng curl hoặc trình duyệt.

Kiểm tra prod vẫn giữ digest đã ghi ở bước 2 và giao diện cũ.
Điểm cần chứng minh: pipeline không tự sửa overlay prod.

## 5. Promote cùng digest

Theo RUNBOOK phần promotion: sửa đúng digest prod bằng Vim, render/dry-run,
review diff, commit và push origin main.

Trong Argo CD prod: review Diff rồi Sync thủ công; Force/Replace/Prune tắt.
Đợi đúng revision, Synced, Healthy, rollout hoàn tất, /ready=200.
Xác minh prod hiển thị nội dung mới, /version báo environment=prod.

Giải thích đây là promotion trong lab do cùng một người thao tác; project chưa
thiết lập hệ thống phê duyệt nhiều người hoặc quy trình doanh nghiệp.

## 6. Giải thích khả năng khôi phục

Trình bày incident umask/Gunicorn trong RUNBOOK: build xanh nhưng runtime user
không đọc được package; Git revert đưa cấu hình về image tốt; bổ sung kiểm tra
import dưới appuser để phát hiện sớm.

Nếu cần demo rollback trực tiếp, revert đúng commit promotion vừa tạo và manual
Sync prod. Xác minh digest cũ, /ready và giao diện. Đừng thử image hỏng trên prod
chỉ để tạo tình huống.

## Bộ bằng chứng nên mở sẵn

- README: kiến trúc và giới hạn.
- .gitlab-ci.yml: ba job và artifact dependency.
- tests/: test ứng dụng và GitOps automation.
- GitOps overlay: hai digest, policy staging/prod.
- Argo CD: revision, Sync/Health và cây tài nguyên.
- kubectl get pods,pvc: workload và storage.
- RUNBOOK: promotion, rollback và RCA.
- EVIDENCE: snapshot có ngày; ảnh CI là dữ liệu lịch sử, không giả làm live status.

Không mở màn hình chứa token, file .env, Secret data hoặc Runner config.
